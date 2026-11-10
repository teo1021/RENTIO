"""
Tests unitarios y de integración para el microservicio de IA Marketing.
"""

from fastapi.testclient import TestClient

from app.config import settings
from app.extractor import ExtractorInmueble
from app.main import app
from app.recomendador import RecomendadorPrecio

client = TestClient(app)
settings.INTERNAL_API_KEY = "test-internal-key"
settings.AI_API_KEY = ""
AUTH_HEADERS = {"X-Internal-API-Key": settings.INTERNAL_API_KEY}


def test_health():
    """Verifica que el endpoint de salud responda 200 y reporte barrios indexados."""
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["service"] == "rentio-ai-marketing"
    assert data["barrios_indexados"] >= 400


def test_seguridad_llave_interna():
    """Verifica que las rutas protegidas exijan la llave interna."""
    # Sin llave -> 403
    res_sin_llave = client.post(
        "/api/v1/ia/conversar",
        json={"mensaje_usuario": "Hola"},
    )
    assert res_sin_llave.status_code == 403

    # Con llave errónea -> 403
    res_llave_mala = client.post(
        "/api/v1/ia/conversar",
        headers={"X-Internal-API-Key": "clave_incorrecta"},
        json={"mensaje_usuario": "Hola"},
    )
    assert res_llave_mala.status_code == 403


def test_extractor_atributos():
    """Verifica la extracción de entidades desde texto en lenguaje natural."""
    rec = RecomendadorPrecio()
    ext = ExtractorInmueble(recomendador=rec)

    texto = "Arriendo hermoso apartamento en Laureles de 3 alcobas y 2 baños, con balcón y parqueadero."
    datos = ext.extraer(texto)
    assert datos.get("tipo") == "apartamento"
    assert datos.get("barrio") == "Laureles"
    assert datos.get("habitaciones") == 3
    assert datos.get("banos") == 2
    assert datos.get("parqueadero") is True
    assert "Balcón" in datos.get("caracteristicas", [])


def test_extractor_distingue_tipo_de_inmueble_y_numero_de_habitaciones():
    extractor = ExtractorInmueble(recomendador=RecomendadorPrecio())
    casos = [
        ("Tengo un apartamento en Laureles con 3 habitaciones", "apartamento", 3),
        ("Tengo una casa en Laureles con 2 habitaciones", "casa", 2),
        ("Ofrezco una habitación en Laureles", "habitacion", None),
    ]
    for texto, tipo_esperado, habitaciones_esperadas in casos:
        datos = extractor.extraer(texto)
        assert datos["tipo"] == tipo_esperado
        if habitaciones_esperadas is not None:
            assert datos["habitaciones"] == habitaciones_esperadas

    datos_previos = {"tipo": "apartamento"}
    respuesta = extractor.extraer("Tiene 4 habitaciones", datos_previos)
    assert "tipo" not in respuesta
    assert ExtractorInmueble.combinar_y_validar(datos_previos, respuesta)["tipo"] == "apartamento"


def test_extractor_reconoce_barrios_con_puntuacion_y_ubicaciones_escritas():
    extractor = ExtractorInmueble(recomendador=RecomendadorPrecio())

    catalogo = extractor.extraer(
        "Tengo un apartamento en El Nogal Los Almendros",
        barrios_disponibles=["El Nogal-Los Almendros"],
    )
    assert catalogo["barrio"] == "El Nogal-Los Almendros"

    escrito = extractor.extraer(
        "Tengo un apartamento en el barrio La Arboleda con dos habitaciones",
        barrios_disponibles=["Laureles"],
    )
    assert escrito["barrio"] == "La Arboleda"

    respuesta = extractor.extraer(
        "La Arboleda",
        historial=[{"rol": "asistente", "contenido": "¿En qué barrio está el inmueble?"}],
    )
    assert respuesta["barrio"] == "La Arboleda"


def test_extractor_reconoce_comuna_del_catalogo():
    extractor = ExtractorInmueble(recomendador=RecomendadorPrecio())
    datos = extractor.extraer(
        "Apartamento en la comuna 11",
        barrios_disponibles=["Comuna 11 - Laureles-Estadio"],
    )
    assert datos["barrio"] == "Comuna 11 - Laureles-Estadio"
    assert datos["barrio_comuna"] == "Comuna 11"


def test_registro_solicita_confirmacion_de_canon_sugerido_o_manual():
    extractor = ExtractorInmueble(recomendador=RecomendadorPrecio())
    datos_previos = {
        "barrio": "Laureles",
        "tipo": "apartamento",
        "habitaciones": 2,
        "banos": 1,
        "direccion": "Calle 30 # 80-25",
        "estrato": 4,
        "canon_sugerido": 3_400_000,
    }

    aceptacion = extractor.extraer("Acepto el canon sugerido", datos_previos)
    aceptados = extractor.combinar_y_validar(datos_previos, aceptacion)
    assert aceptados["precio_mensual"] == 3_400_000
    assert aceptados["canon_confirmado"] is True

    rechazo = extractor.extraer("Rechazo la sugerencia de canon", datos_previos)
    rechazados = extractor.combinar_y_validar(datos_previos, rechazo)
    assert rechazados["canon_confirmado"] is False
    assert rechazados["canon_rechazado"] is True

    ingreso_manual = extractor.extraer(
        "El canon mensual que decido cobrar es $2.100.000",
        rechazados,
    )
    confirmados = extractor.combinar_y_validar(rechazados, ingreso_manual)
    assert confirmados["precio_mensual"] == 2_100_000
    assert confirmados["canon_confirmado"] is True
    assert confirmados["canon_rechazado"] is False


def test_chat_flujo_incompleto_a_completo():
    """Verifica la detección de campos faltantes y la posterior completitud con generación."""
    # Turno 1: Faltan baños
    payload_1 = {
        "mensaje_usuario": "Tengo un apartamento en Laureles con 2 habitaciones, dirección Calle 30 # 80-25 y estrato 4",
        "datos_previos": {},
    }
    res_1 = client.post("/api/v1/ia/conversar", headers=AUTH_HEADERS, json=payload_1)
    assert res_1.status_code == 200
    data_1 = res_1.json()
    assert data_1["es_completo"] is False
    assert "banos" in data_1["datos_faltantes"]
    assert "baño" in data_1["respuesta_asistente"].lower()
    assert data_1["resultado_generado"] is None

    # Turno 2: Provee los baños
    datos_previos_2 = data_1["datos_actualizados"]
    payload_2 = {
        "mensaje_usuario": "Cuenta con 2 baños, parqueadero privado y el canon es de $1.800.000 mensuales",
        "datos_previos": datos_previos_2,
    }
    res_2 = client.post("/api/v1/ia/conversar", headers=AUTH_HEADERS, json=payload_2)
    assert res_2.status_code == 200
    data_2 = res_2.json()
    assert data_2["es_completo"] is True
    assert len(data_2["datos_faltantes"]) == 0
    assert data_2["resultado_generado"] is not None

    resultado = data_2["resultado_generado"]
    assert resultado["precio_estimado"] > 0
    assert resultado["precio_minimo"] <= resultado["precio_estimado"] <= resultado["precio_maximo"]
    assert "Laureles" in resultado["descripcion_sugerida"]
    assert len(resultado["metadatos_calculo"]["limitaciones"]) >= 2


def test_extractor_reconoce_canon_en_pesos_y_respuesta_corta_contextual():
    extractor = ExtractorInmueble(recomendador=RecomendadorPrecio())

    datos = extractor.extraer(
        "Apartamento en Laureles, 3 habitaciones, 2 baños, canon de 2.000.000 mensuales",
    )
    assert datos["precio_mensual"] == 2_000_000

    respuesta = extractor.extraer(
        "75",
        datos,
        [{"rol": "asistente", "contenido": "¿Cuántos metros cuadrados tiene?"}],
    )
    assert respuesta["area_m2"] == 75

    precio = extractor.extraer(
        "1.800.000",
        datos,
        [{"rol": "asistente", "contenido": "¿Cuál es el canon mensual que quieres cobrar?"}],
    )
    assert precio["precio_mensual"] == 1_800_000
    assert precio["canon_confirmado"] is True
    assert precio["canon_rechazado"] is False


def test_canon_es_obligatorio_para_completar_registro():
    extractor = ExtractorInmueble(recomendador=RecomendadorPrecio())
    datos = {
        "barrio": "Laureles",
        "tipo": "apartamento",
        "habitaciones": 2,
        "banos": 1,
        "direccion": "Calle 30 # 80-25",
        "estrato": 4,
    }
    assert extractor.obtener_campos_faltantes(datos) == []
    respuesta = client.post(
        "/api/v1/ia/conversar",
        headers=AUTH_HEADERS,
        json={"mensaje_usuario": "Listo", "datos_previos": datos},
    )
    assert respuesta.status_code == 200
    assert respuesta.json()["es_completo"] is False
    assert respuesta.json()["datos_actualizados"].get("canon_confirmado") is not True
    assert respuesta.json()["resultado_generado"]["precio_estimado"] > 0


def test_analisis_mercado_no_inventa_demanda_ni_vacancia():
    respuesta = client.post(
        "/api/v1/ia/analisis-mercado",
        headers=AUTH_HEADERS,
        json={"barrio": "Laureles"},
    )
    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert "no disponible" in datos["nivel_demanda"].lower()
    assert datos["tiempo_promedio_vacancia_dias"] is None
    assert "no disponible" in datos["tendencia_mercado"].lower()


def test_titulos_de_marketing_no_inventan_caracteristicas():
    respuesta = client.post(
        "/api/v1/ia/mejorar-titulo",
        headers=AUTH_HEADERS,
        json={
            "titulo_actual": "Apartamento en Laureles",
            "barrio": "Laureles",
            "tipo": "apartamento",
        },
    )
    assert respuesta.status_code == 200
    titulos = respuesta.json()["titulos_sugeridos"]
    assert len(titulos) >= 2
    assert all("hermoso" not in titulo.lower() for titulo in titulos)
    assert all("iluminación" not in titulo.lower() for titulo in titulos)


def test_error_del_proveedor_ia_no_se_presenta_como_resultado_valido(monkeypatch):
    monkeypatch.setattr(settings, "AI_API_KEY", "test-key")

    def fallar(*_args):
        raise RuntimeError("Proveedor no disponible.")

    monkeypatch.setattr("app.generador_descripcion.GeneradorDescripcion._invocar_llm", fallar)
    respuesta = client.post(
        "/api/v1/ia/generar-descripcion",
        headers=AUTH_HEADERS,
        json={"barrio": "Laureles", "tipo": "apartamento"},
    )
    assert respuesta.status_code == 503
    assert "Proveedor no disponible" in respuesta.json()["detail"]


def test_chat_permite_corregir_un_dato_previamente_proporcionado():
    datos_iniciales = client.post(
        "/api/v1/ia/conversar",
        headers=AUTH_HEADERS,
        json={
            "mensaje_usuario": (
                "Apartamento en Laureles, 3 habitaciones, 2 baños, "
                "dirección Calle 30 # 80-25, estrato 4 y canon "
                "$1.800.000 mensuales"
            ),
            "datos_previos": {},
        },
    )
    assert datos_iniciales.status_code == 200
    datos_previos = datos_iniciales.json()["datos_actualizados"]
    assert datos_previos["habitaciones"] == 3

    correccion = client.post(
        "/api/v1/ia/conversar",
        headers=AUTH_HEADERS,
        json={
            "mensaje_usuario": "Me equivoqué, son 4 habitaciones",
            "datos_previos": datos_previos,
        },
    )
    assert correccion.status_code == 200
    datos_corregidos = correccion.json()["datos_actualizados"]
    assert datos_corregidos["habitaciones"] == 4
    assert correccion.json()["es_completo"] is True


def test_estimacion_precio_laureles():
    """Verifica la estimación empírica en Laureles utilizando el dataset de mercado."""
    payload = {
        "barrio": "Laureles",
        "habitaciones": 2,
        "parqueadero": True,
        "tipo": "apartamento",
    }
    res = client.post("/api/v1/ia/estimar-precio", headers=AUTH_HEADERS, json=payload)
    assert res.status_code == 200
    datos = res.json()
    assert datos["precio_sugerido"] == 3400000.0  # Mediana exacta en dataset para Laureles 2 alcobas
    assert datos["metadatos_calculo"]["metodo"] == "mediana_barrio_por_habitaciones"
    assert datos["metadatos_calculo"]["avisos_muestra"] == 1385
    assert datos["metadatos_calculo"]["fecha_datos"] == "2026-10-05"


def test_estimacion_precio_barrio_desconocido_fallback():
    """Verifica que barrios sin muestra directa apliquen el fallback a nivel de ciudad documentado."""
    payload = {
        "barrio": "BarrioInexistenteXYZ",
        "habitaciones": 1,
    }
    res = client.post("/api/v1/ia/estimar-precio", headers=AUTH_HEADERS, json=payload)
    assert res.status_code == 200
    datos = res.json()
    assert datos["precio_sugerido"] == 3200000.0  # Mediana de 1 alcoba global Medellín
    assert datos["metadatos_calculo"]["metodo"] == "referencia_ciudad_por_habitaciones"
    assert any("no cuenta con registros comparables" in lim for lim in datos["metadatos_calculo"]["limitaciones"])
