
"""
Controladores del dominio de IA Marketing.

Incluye conversaciones con IA, herramientas de marketing
y creación de propiedades desde el asistente conversacional.
"""

import unicodedata

from flask import Blueprint, jsonify, request
from marshmallow import ValidationError

from app import db
from app.dominios.ia_marketing.cliente import (
    ServicioIAError,
    conversar as conversar_con_ia,
    solicitar as solicitar_a_ia,
)
from app.dominios.ia_marketing.dtos import (
    AnalisisMercadoDTO,
    GenerarDescripcionDTO,
    MejorarTituloDTO,
    SugerirPrecioDTO,
)
from app.dominios.ia_marketing.modelos import (
    ConversacionMarketing,
    MensajeMarketing,
    ResultadoMarketing,
)
from app.dominios.propiedades.modelos import Propiedad
from app.dominios.propiedades.dtos import CrearPropiedadDTO
from app.dominios.propiedades.servicios import PropiedadServicio
from app.dominios.barrios.repositorios import BarrioRepositorio
from app.dominios.caracteristicas.repositorios import CaracteristicaRepositorio
from app.seguridad import requiere_propietario


# ============================================================
# BLUEPRINT
# ============================================================

ia_bp = Blueprint("ia", __name__)


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def _llamar_servicio_ai(endpoint, datos):
    try:
        return solicitar_a_ia(endpoint, datos), None
    except ServicioIAError as exc:
        return None, (
            jsonify({
                "success": False,
                "error": {"message": str(exc)}
            }),
            502
        )


def _normalizar_texto(valor):
    """Normaliza textos para comparar nombres sin distinguir tildes."""
    if not isinstance(valor, str):
        return ""

    texto = unicodedata.normalize("NFD", valor.strip().lower())

    return "".join(
        caracter
        for caracter in texto
        if unicodedata.category(caracter) != "Mn"
    )


def _buscar_barrio(nombre):
    """Busca un barrio por nombre sin asumir coincidencias ambiguas."""
    if not nombre:
        return None, False

    barrios = BarrioRepositorio.obtener_todos()

    coincidencias = [
        barrio
        for barrio in barrios
        if _normalizar_texto(barrio.nombre) == _normalizar_texto(nombre)
    ]

    if len(coincidencias) == 1:
        return coincidencias[0], False

    return None, len(coincidencias) > 1


def _mensaje_dict(mensaje):
    return {
        "id": mensaje.id,
        "rol": mensaje.rol,
        "contenido": mensaje.contenido,
        "datos_extraidos": mensaje.datos_extraidos,
        "fecha_creacion": mensaje.fecha_creacion.isoformat(),
    }


def _resultado_dict(resultado):
    return {
        "id": resultado.id,
        "descripcion": resultado.descripcion,
        "precio_sugerido": (
            float(resultado.precio_sugerido)
            if resultado.precio_sugerido is not None else None
        ),
        "precio_minimo": (
            float(resultado.precio_minimo)
            if resultado.precio_minimo is not None else None
        ),
        "precio_maximo": (
            float(resultado.precio_maximo)
            if resultado.precio_maximo is not None else None
        ),
        "moneda": resultado.moneda,
        "datos_usados": resultado.datos_usados,
        "metadatos_calculo": resultado.metadatos_calculo,
        "fecha_creacion": resultado.fecha_creacion.isoformat(),
    }


def _conversacion_dict(conversacion):
    return {
        "id": conversacion.id,
        "propiedad_id": conversacion.propiedad_id,
        "estado": conversacion.estado,
        "datos_recopilados": conversacion.datos_recopilados,
        "mensajes": [
            _mensaje_dict(mensaje)
            for mensaje in conversacion.mensajes
        ],
        "resultados": [
            _resultado_dict(resultado)
            for resultado in conversacion.resultados
        ],
        "fecha_creacion": conversacion.fecha_creacion.isoformat(),
        "fecha_actualizacion": conversacion.fecha_actualizacion.isoformat(),
    }


# ============================================================
# CONVERSACIONES
# ============================================================

@ia_bp.route("/conversaciones", methods=["POST"])
@requiere_propietario
def crear_conversacion(usuario_id=None):

    datos = request.get_json(silent=True) or {}
    propiedad_id = datos.get("propiedad_id")
    prellenado = {}

    if propiedad_id is not None:
        propiedad = Propiedad.query.filter_by(
            id=propiedad_id,
            propietario_id=usuario_id
        ).first()

        if propiedad is None:
            return jsonify({
                "success": False,
                "error": {"message": "Propiedad no encontrada."}
            }), 404

        prellenado = {
            "tipo": propiedad.tipo,
            "barrio": propiedad.barrio.nombre if propiedad.barrio else None,
            "habitaciones": propiedad.habitaciones,
            "banos": propiedad.banos,
            "area_m2": (
                float(propiedad.area_m2)
                if propiedad.area_m2 else None
            ),
            "estrato": propiedad.estrato,
            "caracteristicas": [
                caracteristica.nombre
                for caracteristica in propiedad.caracteristicas
            ],
        }

        prellenado = {
            clave: valor
            for clave, valor in prellenado.items()
            if valor is not None
        }

    conversacion = ConversacionMarketing(
        propietario_id=usuario_id,
        propiedad_id=propiedad_id,
        datos_recopilados=prellenado,
    )

    db.session.add(conversacion)
    db.session.commit()

    return jsonify({
        "success": True,
        "data": _conversacion_dict(conversacion)
    }), 201


@ia_bp.route("/conversaciones", methods=["GET"])
@requiere_propietario
def listar_conversaciones(usuario_id=None):

    items = ConversacionMarketing.query.filter_by(
        propietario_id=usuario_id
    ).order_by(
        ConversacionMarketing.fecha_actualizacion.desc()
    ).all()

    return jsonify({
        "success": True,
        "data": [_conversacion_dict(conversacion) for conversacion in items]
    }), 200


@ia_bp.route("/conversaciones/<int:conversacion_id>", methods=["GET"])
@requiere_propietario
def obtener_conversacion(conversacion_id, usuario_id=None):

    conversacion = ConversacionMarketing.query.filter_by(
        id=conversacion_id,
        propietario_id=usuario_id
    ).first()

    if conversacion is None:
        return jsonify({
            "success": False,
            "error": {"message": "Conversación no encontrada."}
        }), 404

    return jsonify({
        "success": True,
        "data": _conversacion_dict(conversacion)
    }), 200


@ia_bp.route(
    "/conversaciones/<int:conversacion_id>/mensajes",
    methods=["POST"]
)
@requiere_propietario
def enviar_mensaje(conversacion_id, usuario_id=None):

    conversacion = ConversacionMarketing.query.filter_by(
        id=conversacion_id,
        propietario_id=usuario_id
    ).first()

    if conversacion is None:
        return jsonify({
            "success": False,
            "error": {"message": "Conversación no encontrada."}
        }), 404

    datos = request.get_json(silent=True) or {}
    mensaje = datos.get("mensaje", "")

    if (
        not isinstance(mensaje, str)
        or not mensaje.strip()
        or len(mensaje) > 4000
    ):
        return jsonify({
            "success": False,
            "error": {
                "message": "El mensaje debe tener entre 1 y 4000 caracteres."
            }
        }), 400

    try:
        respuesta = conversar_con_ia(
            mensaje.strip(),
            conversacion.datos_recopilados or {}
        )
    except ServicioIAError as exc:
        return jsonify({
            "success": False,
            "error": {"message": str(exc)}
        }), 502

    conversacion.datos_recopilados = respuesta["datos_actualizados"]

    conversacion.estado = (
        "lista" if respuesta["es_completo"] else "recopilando"
    )

    db.session.add(
        MensajeMarketing(
            conversacion_id=conversacion.id,
            rol="usuario",
            contenido=mensaje.strip()
        )
    )

    db.session.add(
        MensajeMarketing(
            conversacion_id=conversacion.id,
            rol="asistente",
            contenido=respuesta["respuesta_asistente"],
            datos_extraidos=respuesta.get("datos_extraidos", {}),
        )
    )

    resultado = respuesta.get("resultado_generado")

    if resultado:
        db.session.add(
            ResultadoMarketing(
                conversacion_id=conversacion.id,
                propiedad_id=conversacion.propiedad_id,
                descripcion=resultado["descripcion_sugerida"],
                precio_sugerido=resultado["precio_estimado"],
                precio_minimo=resultado["precio_minimo"],
                precio_maximo=resultado["precio_maximo"],
                moneda=resultado["moneda"],
                datos_usados=respuesta["datos_actualizados"],
                fuente_datos="datasets de avisos de arriendo Medellín",
                version_datos=resultado["metadatos_calculo"]["version_fuente"],
                metadatos_calculo=resultado["metadatos_calculo"],
            )
        )

    db.session.commit()

    return jsonify({
        "success": True,
        "data": {
            "conversacion_id": conversacion.id,
            "datos_actualizados": respuesta["datos_actualizados"],
            "datos_faltantes": respuesta["datos_faltantes"],
            "es_completo": respuesta["es_completo"],
            "respuesta_asistente": respuesta["respuesta_asistente"],
            "resultado_generado": resultado,
        }
    }), 200


# ============================================================
# APLICAR RESULTADO A UNA PROPIEDAD EXISTENTE
# ============================================================

@ia_bp.route(
    "/conversaciones/<int:conversacion_id>/aplicar",
    methods=["POST"]
)
@requiere_propietario
def aplicar_resultado(conversacion_id, usuario_id=None):

    conversacion = ConversacionMarketing.query.filter_by(
        id=conversacion_id,
        propietario_id=usuario_id
    ).first()

    if conversacion is None:
        return jsonify({
            "success": False,
            "error": {"message": "Conversación no encontrada."}
        }), 404

    if not conversacion.propiedad_id:
        return jsonify({
            "success": False,
            "error": {
                "message": "La conversación no está asociada a una propiedad."
            }
        }), 400

    propiedad = Propiedad.query.filter_by(
        id=conversacion.propiedad_id,
        propietario_id=usuario_id
    ).first()

    resultado = ResultadoMarketing.query.filter_by(
        conversacion_id=conversacion.id
    ).order_by(
        ResultadoMarketing.fecha_creacion.desc(),
        ResultadoMarketing.id.desc()
    ).first()

    if propiedad is None or resultado is None:
        return jsonify({
            "success": False,
            "error": {"message": "No hay un resultado aplicable."}
        }), 400

    propiedad.descripcion = resultado.descripcion

    if resultado.precio_sugerido is not None:
        propiedad.precio_mensual = resultado.precio_sugerido

    conversacion.estado = "generada"

    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Descripción y precio aplicados a la propiedad."
    }), 200


# ============================================================
# NUEVO: CREAR PROPIEDAD DESDE EL ASISTENTE DE IA
# ============================================================

@ia_bp.route(
    "/conversaciones/<int:conversacion_id>/crear-propiedad",
    methods=["POST"]
)
@requiere_propietario
def crear_propiedad_desde_conversacion(
    conversacion_id,
    usuario_id=None
):

    conversacion = ConversacionMarketing.query.filter_by(
        id=conversacion_id,
        propietario_id=usuario_id
    ).first()

    if conversacion is None:
        return jsonify({
            "success": False,
            "error": {"message": "Conversación no encontrada."}
        }), 404

    if conversacion.propiedad_id is not None:
        return jsonify({
            "success": False,
            "error": {
                "message": "Esta conversación ya está asociada a una propiedad."
            }
        }), 400

    datos = request.get_json(silent=True) or {}
    datos_confirmados = datos.get("datos")

    if not isinstance(datos_confirmados, dict):
        return jsonify({
            "success": False,
            "error": {
                "message": "Debes enviar los datos confirmados de la propiedad."
            }
        }), 400

    datos_ia = conversacion.datos_recopilados or {}

    # Resolver el barrio.
    barrio_id = datos_confirmados.get("barrio_id")

    if barrio_id is None:

        nombre_barrio = (
            datos_confirmados.get("barrio")
            or datos_ia.get("barrio")
        )

        barrio, ambiguo = _buscar_barrio(nombre_barrio)

        if ambiguo:
            return jsonify({
                "success": False,
                "error": {
                    "message": (
                        "Hay varios barrios con ese nombre. "
                        "Selecciona el barrio correcto."
                    )
                }
            }), 400

        if nombre_barrio and barrio is None:
            return jsonify({
                "success": False,
                "error": {
                    "message": "El barrio indicado no existe en el catálogo."
                }
            }), 400

        barrio_id = barrio.id if barrio else None

    # Resolver características.
    caracteristicas_ids = datos_confirmados.get("caracteristicas_ids")

    if caracteristicas_ids is None:

        nombres = datos_confirmados.get(
            "caracteristicas",
            datos_ia.get("caracteristicas", [])
        )

        caracteristicas_ids = []

        if isinstance(nombres, list):

            caracteristicas = CaracteristicaRepositorio.obtener_todos()

            for nombre in nombres:

                nombre_normalizado = _normalizar_texto(nombre)

                coincidencia = next(
                    (
                        caracteristica
                        for caracteristica in caracteristicas
                        if _normalizar_texto(caracteristica.nombre)
                        == nombre_normalizado
                    ),
                    None
                )

                if (
                    coincidencia
                    and coincidencia.id not in caracteristicas_ids
                ):
                    caracteristicas_ids.append(coincidencia.id)

    # Preparar datos para el DTO.
    datos_propiedad = {
        "titulo": datos_confirmados.get("titulo"),
        "descripcion": datos_confirmados.get("descripcion"),
        "precio_mensual": datos_confirmados.get("precio_mensual"),
        "direccion": datos_confirmados.get("direccion"),
        "estrato": datos_confirmados.get("estrato"),
        "area_m2": datos_confirmados.get(
            "area_m2",
            datos_ia.get("area_m2")
        ),
        "habitaciones": datos_confirmados.get(
            "habitaciones",
            datos_ia.get("habitaciones", 1)
        ),
        "banos": datos_confirmados.get(
            "banos",
            datos_ia.get("banos", 1)
        ),
        "tipo": datos_confirmados.get(
            "tipo",
            datos_ia.get("tipo", "apartamento")
        ),
        "barrio_id": barrio_id,
        "caracteristicas_ids": caracteristicas_ids,
    }

    # Validar todos los campos con el DTO existente.
    try:
        datos_validados = CrearPropiedadDTO().load(datos_propiedad)

    except ValidationError as err:
        return jsonify({
            "success": False,
            "error": {
                "message": "Revisa los datos de la propiedad.",
                "details": err.messages
            }
        }), 400

    try:

        propiedad = PropiedadServicio.crear(
            dict(datos_validados),
            usuario_id,
            commit=False
        )

        conversacion.propiedad_id = propiedad.id
        conversacion.estado = "generada"

        resultado = ResultadoMarketing.query.filter_by(
            conversacion_id=conversacion.id
        ).order_by(
            ResultadoMarketing.fecha_creacion.desc(),
            ResultadoMarketing.id.desc()
        ).first()

        if resultado:
            resultado.propiedad_id = propiedad.id

        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Propiedad creada correctamente.",
            "data": propiedad.to_dict()
        }), 201

    except Exception:
        db.session.rollback()

        return jsonify({
            "success": False,
            "error": {
                "message": (
                    "No fue posible crear la propiedad. "
                    "Inténtalo nuevamente."
                )
            }
        }), 500


# ============================================================
# HERRAMIENTAS DE MARKETING IA
# ============================================================

@ia_bp.route("/generar-descripcion", methods=["POST"])
@requiere_propietario
def generar_descripcion(usuario_id=None):

    """Genera una descripción atractiva para la propiedad con IA."""

    try:
        datos = GenerarDescripcionDTO().load(request.get_json() or {})

    except ValidationError as err:
        return jsonify({
            "success": False,
            "error": {
                "message": "Datos de entrada inválidos.",
                "details": err.messages,
            },
        }), 400

    resultado, error = _llamar_servicio_ai(
        "/api/v1/ia/generar-descripcion",
        datos
    )

    if error:
        return error

    return jsonify({
        "success": True,
        "message": "Descripción generada con éxito.",
        "data": resultado,
    }), 200


@ia_bp.route("/sugerir-precio", methods=["POST"])
@requiere_propietario
def sugerir_precio(usuario_id=None):

    """Estima y sugiere rangos de precios de mercado con IA."""

    try:
        datos = SugerirPrecioDTO().load(request.get_json() or {})

    except ValidationError as err:
        return jsonify({
            "success": False,
            "error": {
                "message": "Datos de entrada inválidos.",
                "details": err.messages,
            },
        }), 400

    resultado, error = _llamar_servicio_ai(
        "/api/v1/ia/estimar-precio",
        datos
    )

    if error:
        return error

    return jsonify({
        "success": True,
        "message": "Sugerencia de precio calculada con éxito.",
        "data": resultado,
    }), 200


@ia_bp.route("/analisis-mercado", methods=["POST"])
@requiere_propietario
def analisis_mercado(usuario_id=None):

    """Genera un análisis de mercado y demanda para la zona."""

    try:
        datos = AnalisisMercadoDTO().load(request.get_json() or {})

    except ValidationError as err:
        return jsonify({
            "success": False,
            "error": {
                "message": "Datos de entrada inválidos.",
                "details": err.messages,
            },
        }), 400

    resultado, error = _llamar_servicio_ai(
        "/api/v1/ia/analisis-mercado",
        datos
    )

    if error:
        return error

    return jsonify({
        "success": True,
        "message": "Análisis de mercado generado con éxito.",
        "data": resultado,
    }), 200


@ia_bp.route("/mejorar-titulo", methods=["POST"])
@requiere_propietario
def mejorar_titulo(usuario_id=None):

    """Propone mejoras llamativas para el título del anuncio."""

    try:
        datos = MejorarTituloDTO().load(request.get_json() or {})

    except ValidationError as err:
        return jsonify({
            "success": False,
            "error": {
                "message": "Datos de entrada inválidos.",
                "details": err.messages,
            },
        }), 400

    resultado, error = _llamar_servicio_ai(
        "/api/v1/ia/mejorar-titulo",
        datos
    )

    if error:
        return error

    return jsonify({
        "success": True,
        "message": "Títulos mejorados generados con éxito.",
        "data": resultado,
    }), 200
