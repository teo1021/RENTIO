"""
Controladores del dominio de IA Marketing.

Define el blueprint `ia_bp` con endpoints especializados para propietarios.
"""

from flask import Blueprint, jsonify, request
from marshmallow import ValidationError

from app import db
from app.dominios.ia_marketing.cliente import (
    ServicioIAError,
)
from app.dominios.ia_marketing.cliente import (
    conversar as conversar_con_ia,
)
from app.dominios.ia_marketing.cliente import (
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
from app.seguridad import requiere_propietario

# ── Blueprint ──────────────────────────────────────────────────────────
ia_bp = Blueprint("ia", __name__)


def _llamar_servicio_ai(endpoint, datos):
    try:
        return solicitar_a_ia(endpoint, datos), None
    except ServicioIAError as exc:
        return None, (jsonify({"success": False, "error": {"message": str(exc)}}), 502)


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
        "precio_sugerido": float(resultado.precio_sugerido) if resultado.precio_sugerido is not None else None,
        "precio_minimo": float(resultado.precio_minimo) if resultado.precio_minimo is not None else None,
        "precio_maximo": float(resultado.precio_maximo) if resultado.precio_maximo is not None else None,
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
        "mensajes": [_mensaje_dict(m) for m in conversacion.mensajes],
        "resultados": [_resultado_dict(r) for r in conversacion.resultados],
        "fecha_creacion": conversacion.fecha_creacion.isoformat(),
        "fecha_actualizacion": conversacion.fecha_actualizacion.isoformat(),
    }


@ia_bp.route("/conversaciones", methods=["POST"])
@requiere_propietario
def crear_conversacion(usuario_id=None):
    datos = request.get_json(silent=True) or {}
    propiedad_id = datos.get("propiedad_id")
    prellenado = {}
    if propiedad_id is not None:
        propiedad = Propiedad.query.filter_by(id=propiedad_id, propietario_id=usuario_id).first()
        if propiedad is None:
            return jsonify({"success": False, "error": {"message": "Propiedad no encontrada."}}), 404
        prellenado = {
            "tipo": propiedad.tipo,
            "barrio": propiedad.barrio.nombre if propiedad.barrio else None,
            "habitaciones": propiedad.habitaciones,
            "banos": propiedad.banos,
            "area_m2": float(propiedad.area_m2) if propiedad.area_m2 else None,
            "estrato": propiedad.estrato,
            "caracteristicas": [c.nombre for c in propiedad.caracteristicas],
        }
        prellenado = {k: v for k, v in prellenado.items() if v is not None}
    conversacion = ConversacionMarketing(
        propietario_id=usuario_id,
        propiedad_id=propiedad_id,
        datos_recopilados=prellenado,
    )
    db.session.add(conversacion)
    db.session.commit()
    return jsonify({"success": True, "data": _conversacion_dict(conversacion)}), 201


@ia_bp.route("/conversaciones", methods=["GET"])
@requiere_propietario
def listar_conversaciones(usuario_id=None):
    items = ConversacionMarketing.query.filter_by(propietario_id=usuario_id).order_by(
        ConversacionMarketing.fecha_actualizacion.desc()
    ).all()
    return jsonify({"success": True, "data": [_conversacion_dict(c) for c in items]}), 200


@ia_bp.route("/conversaciones/<int:conversacion_id>", methods=["GET"])
@requiere_propietario
def obtener_conversacion(conversacion_id, usuario_id=None):
    conversacion = ConversacionMarketing.query.filter_by(
        id=conversacion_id, propietario_id=usuario_id
    ).first()
    if conversacion is None:
        return jsonify({"success": False, "error": {"message": "Conversación no encontrada."}}), 404
    return jsonify({"success": True, "data": _conversacion_dict(conversacion)}), 200


@ia_bp.route("/conversaciones/<int:conversacion_id>/mensajes", methods=["POST"])
@requiere_propietario
def enviar_mensaje(conversacion_id, usuario_id=None):
    conversacion = ConversacionMarketing.query.filter_by(
        id=conversacion_id, propietario_id=usuario_id
    ).first()
    if conversacion is None:
        return jsonify({"success": False, "error": {"message": "Conversación no encontrada."}}), 404
    datos = request.get_json(silent=True) or {}
    mensaje = datos.get("mensaje", "")
    if not isinstance(mensaje, str) or not mensaje.strip() or len(mensaje) > 4000:
        return jsonify({"success": False, "error": {"message": "El mensaje debe tener entre 1 y 4000 caracteres."}}), 400
    try:
        respuesta = conversar_con_ia(mensaje.strip(), conversacion.datos_recopilados or {})
    except ServicioIAError as exc:
        return jsonify({"success": False, "error": {"message": str(exc)}}), 502

    conversacion.datos_recopilados = respuesta["datos_actualizados"]
    conversacion.estado = "lista" if respuesta["es_completo"] else "recopilando"
    db.session.add(MensajeMarketing(conversacion_id=conversacion.id, rol="usuario", contenido=mensaje.strip()))
    db.session.add(MensajeMarketing(
        conversacion_id=conversacion.id,
        rol="asistente",
        contenido=respuesta["respuesta_asistente"],
        datos_extraidos=respuesta.get("datos_extraidos", {}),
    ))
    resultado = respuesta.get("resultado_generado")
    if resultado:
        db.session.add(ResultadoMarketing(
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
        ))
    db.session.commit()
    return jsonify({"success": True, "data": {
        "conversacion_id": conversacion.id,
        "datos_actualizados": respuesta["datos_actualizados"],
        "datos_faltantes": respuesta["datos_faltantes"],
        "es_completo": respuesta["es_completo"],
        "respuesta_asistente": respuesta["respuesta_asistente"],
        "resultado_generado": resultado,
    }}), 200


@ia_bp.route("/conversaciones/<int:conversacion_id>/aplicar", methods=["POST"])
@requiere_propietario
def aplicar_resultado(conversacion_id, usuario_id=None):
    conversacion = ConversacionMarketing.query.filter_by(
        id=conversacion_id, propietario_id=usuario_id
    ).first()
    if conversacion is None:
        return jsonify({"success": False, "error": {"message": "Conversación no encontrada."}}), 404
    if not conversacion.propiedad_id:
        return jsonify({"success": False, "error": {"message": "La conversación no está asociada a una propiedad."}}), 400
    propiedad = Propiedad.query.filter_by(id=conversacion.propiedad_id, propietario_id=usuario_id).first()
    resultado = ResultadoMarketing.query.filter_by(conversacion_id=conversacion.id).order_by(
        ResultadoMarketing.fecha_creacion.desc(), ResultadoMarketing.id.desc()
    ).first()
    if propiedad is None or resultado is None:
        return jsonify({"success": False, "error": {"message": "No hay un resultado aplicable."}}), 400
    propiedad.descripcion = resultado.descripcion
    if resultado.precio_sugerido is not None:
        propiedad.precio_mensual = resultado.precio_sugerido
    conversacion.estado = "generada"
    db.session.commit()
    return jsonify({"success": True, "message": "Descripción y precio aplicados a la propiedad."}), 200


@ia_bp.route("/generar-descripcion", methods=["POST"])
@requiere_propietario
def generar_descripcion(usuario_id=None):
    """Genera una descripción atractiva para la propiedad con IA."""
    try:
        datos = GenerarDescripcionDTO().load(request.get_json() or {})
    except ValidationError as err:
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "message": "Datos de entrada inválidos.",
                        "details": err.messages,
                    },
                }
            ),
            400,
        )

    resultado, error = _llamar_servicio_ai("/api/v1/ia/generar-descripcion", datos)
    if error:
        return error
    return (
        jsonify(
            {
                "success": True,
                "message": "Descripción generada con éxito.",
                "data": resultado,
            }
        ),
        200,
    )


@ia_bp.route("/sugerir-precio", methods=["POST"])
@requiere_propietario
def sugerir_precio(usuario_id=None):
    """Estima y sugiere rangos de precios de mercado con IA."""
    try:
        datos = SugerirPrecioDTO().load(request.get_json() or {})
    except ValidationError as err:
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "message": "Datos de entrada inválidos.",
                        "details": err.messages,
                    },
                }
            ),
            400,
        )

    resultado, error = _llamar_servicio_ai("/api/v1/ia/estimar-precio", datos)
    if error:
        return error
    return (
        jsonify(
            {
                "success": True,
                "message": "Sugerencia de precio calculada con éxito.",
                "data": resultado,
            }
        ),
        200,
    )


@ia_bp.route("/analisis-mercado", methods=["POST"])
@requiere_propietario
def analisis_mercado(usuario_id=None):
    """Genera un análisis de mercado y demanda para la zona."""
    try:
        datos = AnalisisMercadoDTO().load(request.get_json() or {})
    except ValidationError as err:
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "message": "Datos de entrada inválidos.",
                        "details": err.messages,
                    },
                }
            ),
            400,
        )

    resultado, error = _llamar_servicio_ai("/api/v1/ia/analisis-mercado", datos)
    if error:
        return error
    return (
        jsonify(
            {
                "success": True,
                "message": "Análisis de mercado generado con éxito.",
                "data": resultado,
            }
        ),
        200,
    )


@ia_bp.route("/mejorar-titulo", methods=["POST"])
@requiere_propietario
def mejorar_titulo(usuario_id=None):
    """Propone mejoras llamativas para el título del anuncio."""
    try:
        datos = MejorarTituloDTO().load(request.get_json() or {})
    except ValidationError as err:
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "message": "Datos de entrada inválidos.",
                        "details": err.messages,
                    },
                }
            ),
            400,
        )

    resultado, error = _llamar_servicio_ai("/api/v1/ia/mejorar-titulo", datos)
    if error:
        return error
    return (
        jsonify(
            {
                "success": True,
                "message": "Títulos mejorados generados con éxito.",
                "data": resultado,
            }
        ),
        200,
    )
