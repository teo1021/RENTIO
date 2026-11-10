"""
API principal de FastAPI para el servicio independiente de IA Marketing — RENTIO.
"""

from typing import Optional

from fastapi import Depends, FastAPI, Header, HTTPException, status
from openai import APIError, OpenAI

from app.config import settings
from app.extractor import ExtractorInmueble
from app.generador_descripcion import GeneradorDescripcion
from app.recomendador import RecomendadorPrecio
from app.schemas import (
    AnalisisMercadoRequest,
    AnalisisMercadoResponse,
    ConversarRequest,
    ConversarResponse,
    EstimarPrecioRequest,
    EstimarPrecioResponse,
    GenerarContratoRequest,
    GenerarContratoResponse,
    GenerarDescripcionRequest,
    GenerarDescripcionResponse,
    MejorarTituloRequest,
    MejorarTituloResponse,
    MetadatosCalculo,
    ResultadoGeneradoItem,
)

app = FastAPI(
    title="RENTIO AI Marketing Service",
    description="Microservicio especializado en recolección conversacional, recomendación de canon con datos de mercado y marketing inmobiliario en Medellín.",
    version="1.0.0",
)

# ── Instancias de motores de dominio ───────────────────────────────────────
recomendador = RecomendadorPrecio()
extractor = ExtractorInmueble(recomendador=recomendador)
generador = GeneradorDescripcion()


def verificar_llave_interna(x_internal_api_key: Optional[str] = Header(None)):
    """Verifica la cabecera compartida para llamadas internas seguras desde el backend."""
    esperada = settings.INTERNAL_API_KEY
    if not esperada:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="El acceso interno al servicio de IA no está configurado.",
        )
    if not x_internal_api_key or x_internal_api_key != esperada:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso no autorizado al servicio interno de IA.",
        )


@app.get("/health", tags=["Salud"])
def salud():
    """Endpoint público para comprobación de estado y salud en Docker Compose."""
    return {
        "status": "ok",
        "service": "rentio-ai-marketing",
        "version": "1.0.0",
        "barrios_indexados": len(recomendador.barrios_db),
        "comunas_indexadas": len(recomendador.comunas_db),
    }


@app.post(
    "/api/v1/ia/conversar",
    response_model=ConversarResponse,
    dependencies=[Depends(verificar_llave_interna)],
    tags=["Chat de Recopilación"],
)
def conversar(solicitud: ConversarRequest):
    """
    Procesa un turno del chat con el propietario:
    1. Extrae entidades y características del mensaje actual.
    2. Combina y valida con los datos acumulados previos.
    3. Detecta campos faltantes para la descripción y la estimación.
    4. Si está completo, genera descripción comercial y recomendación de canon.
    5. Retorna la respuesta guiada del asistente.
    """
    try:
        datos_extraidos = extractor.extraer(
            solicitud.mensaje_usuario,
            solicitud.datos_previos,
            solicitud.historial,
            solicitud.barrios_disponibles,
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    datos_actualizados = extractor.combinar_y_validar(solicitud.datos_previos, datos_extraidos)
    datos_faltantes = extractor.obtener_campos_faltantes(datos_actualizados)
    datos_basicos_completos = len(datos_faltantes) == 0

    resultado_generado = None
    if datos_basicos_completos:
        # 1. Recomendación empírica de precio
        try:
            estimacion = recomendador.estimar_precio(
                barrio=datos_actualizados["barrio"],
                habitaciones=datos_actualizados["habitaciones"],
                parqueadero=datos_actualizados.get("parqueadero"),
                tipo=datos_actualizados.get("tipo", "apartamento"),
                estrato=datos_actualizados.get("estrato"),
                area_m2=datos_actualizados.get("area_m2"),
            )
        except ValueError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        datos_actualizados["canon_sugerido"] = estimacion["precio_sugerido"]

        # 2. Descripción comercial publicable
        desc_resultado = generador.generar(datos_actualizados)

        resultado_generado = ResultadoGeneradoItem(
            descripcion_sugerida=desc_resultado["descripcion"],
            puntos_destacados=desc_resultado["puntos_destacados"],
            precio_estimado=estimacion["precio_sugerido"],
            precio_minimo=estimacion["precio_minimo"],
            precio_maximo=estimacion["precio_maximo"],
            moneda=estimacion["moneda"],
            metadatos_calculo=MetadatosCalculo(**estimacion["metadatos_calculo"]),
            analisis_resumido=estimacion["analisis"],
        )

    es_completo = (
        datos_basicos_completos
        and datos_actualizados.get("canon_confirmado") is True
        and bool(datos_actualizados.get("precio_mensual"))
    )
    respuesta_asistente = extractor.construir_respuesta_asistente(
        datos_actualizados=datos_actualizados,
        datos_nuevos=datos_extraidos,
        faltantes=datos_faltantes,
        es_completo=datos_basicos_completos,
    )

    return ConversarResponse(
        datos_extraidos=datos_extraidos,
        datos_actualizados=datos_actualizados,
        datos_faltantes=datos_faltantes,
        es_completo=es_completo,
        respuesta_asistente=respuesta_asistente,
        resultado_generado=resultado_generado,
    )


@app.post(
    "/api/v1/ia/generar-contrato",
    response_model=GenerarContratoResponse,
    dependencies=[Depends(verificar_llave_interna)],
    tags=["Contratos"],
)
def generar_contrato(solicitud: GenerarContratoRequest):
    """Genera una plantilla sin datos personales ni económicos del arrendamiento."""
    if settings.AI_PROVIDER != "openai" or not settings.AI_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="La generación de contratos requiere un proveedor de IA configurado.",
        )

    marcadores = (
        "{{ARRENDADOR_NOMBRE}}, {{ARRENDATARIO_NOMBRE}}, "
        "{{ARRENDATARIO_CEDULA}}, {{ARRENDATARIO_TELEFONO}}, "
        "{{INMUEBLE_DIRECCION}}, {{INMUEBLE_BARRIO}}, "
        "{{FECHA_INICIO}}, {{FECHA_FIN}}, {{CANON_MENSUAL}}"
    )
    try:
        respuesta = OpenAI(api_key=settings.AI_API_KEY).chat.completions.create(
            model=settings.AI_MODEL,
            temperature=0.2,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Redacta en español colombiano una plantilla clara de borrador "
                        "para un contrato de arrendamiento de vivienda urbana en Colombia. "
                        "No cites leyes ni inventes requisitos legales. Incluye identificación "
                        "de las partes, inmueble, plazo, canon y condiciones generales de pago, "
                        "obligaciones, terminación y firmas. Conserva literalmente todos estos "
                        f"marcadores para sustitución local: {marcadores}. "
                        "No agregues nombres, cifras, fechas ni cláusulas punitivas no provistas. "
                        "Aclara que es un borrador sujeto a revisión jurídica."
                    ),
                },
                {
                    "role": "user",
                    "content": "Genera únicamente la plantilla solicitada. No recibes datos personales.",
                },
            ],
        )
        plantilla = (respuesta.choices[0].message.content or "").strip()
    except APIError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No fue posible generar la plantilla de contrato. Inténtalo de nuevo.",
        ) from exc

    if not plantilla:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="El proveedor de IA no devolvió una plantilla de contrato.",
        )
    if any(marcador not in plantilla for marcador in marcadores.split(", ")):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="La plantilla generada no conservó todos los campos contractuales. Inténtalo de nuevo.",
        )
    return GenerarContratoResponse(plantilla=plantilla)


@app.post(
    "/api/v1/ia/estimar-precio",
    response_model=EstimarPrecioResponse,
    dependencies=[Depends(verificar_llave_interna)],
    tags=["Precios de Mercado"],
)
def estimar_precio(solicitud: EstimarPrecioRequest):
    """Estima rangos de precio con base en medianas y percentiles reales de avisos en Medellín."""
    try:
        resultado = recomendador.estimar_precio(
            barrio=solicitud.barrio,
            habitaciones=solicitud.habitaciones,
            parqueadero=solicitud.parqueadero,
            tipo=solicitud.tipo or "apartamento",
            estrato=solicitud.estrato,
            area_m2=solicitud.area_m2,
        )
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return EstimarPrecioResponse(
        precio_sugerido=resultado["precio_sugerido"],
        precio_minimo=resultado["precio_minimo"],
        precio_maximo=resultado["precio_maximo"],
        moneda=resultado["moneda"],
        metadatos_calculo=MetadatosCalculo(**resultado["metadatos_calculo"]),
        analisis=resultado["analisis"],
    )


@app.post(
    "/api/v1/ia/generar-descripcion",
    response_model=GenerarDescripcionResponse,
    dependencies=[Depends(verificar_llave_interna)],
    tags=["Marketing"],
)
def generar_descripcion(solicitud: GenerarDescripcionRequest):
    """Genera una descripción publicable para un inmueble."""
    try:
        res = generador.generar(solicitud.model_dump())
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    return GenerarDescripcionResponse(
        descripcion=res["descripcion"],
        puntos_destacados=res["puntos_destacados"],
    )


@app.post(
    "/api/v1/ia/analisis-mercado",
    response_model=AnalisisMercadoResponse,
    dependencies=[Depends(verificar_llave_interna)],
    tags=["Mercado"],
)
def analisis_mercado(solicitud: AnalisisMercadoRequest):
    """Reporta con claridad las métricas de mercado que no están disponibles."""
    return AnalisisMercadoResponse(
        zona=f"{solicitud.barrio}, Medellín",
        estrato_predominante=solicitud.estrato,
        tipo_inmueble=solicitud.tipo or "apartamento",
        nivel_demanda="No disponible: las fuentes actuales contienen avisos, no mediciones de demanda.",
        tiempo_promedio_vacancia_dias=None,
        tendencia_mercado="No disponible: las fuentes actuales no contienen una serie histórica.",
        recomendacion=(
            "Consulta la referencia de canon, que se calcula con los avisos de arriendo "
            "disponibles y sus limitaciones documentadas."
        ),
    )


@app.post(
    "/api/v1/ia/mejorar-titulo",
    response_model=MejorarTituloResponse,
    dependencies=[Depends(verificar_llave_interna)],
    tags=["Marketing"],
)
def mejorar_titulo(solicitud: MejorarTituloRequest):
    """Propone variantes fieles a los datos del inmueble, sin atributos supuestos."""
    tipo = (solicitud.tipo or "inmueble").replace("_", " ")
    barrio = solicitud.barrio.strip()
    titulos = [
        f"Arriendo de {tipo} en {barrio}",
        f"{tipo.title()} disponible para arriendo en {barrio}",
    ]
    if solicitud.titulo_actual.strip():
        titulos.append(
            f"{solicitud.titulo_actual.strip()} | {tipo.title()} en {barrio}"
        )
    return MejorarTituloResponse(
        titulo_original=solicitud.titulo_actual,
        titulos_sugeridos=titulos,
    )
