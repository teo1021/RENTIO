"""
Controladores del dominio de arriendos.

Define el blueprint `arriendos_bp` para solicitudes y contratos.
"""

from flask import Blueprint, jsonify, request
from marshmallow import ValidationError

from app import db
from app.dominios.arriendos.modelos import SolicitudArriendo
from app.dominios.ia_marketing.cliente import ServicioIAError, generar_plantilla_contrato
from app.dominios.arriendos.dtos import ResponderSolicitudDTO, SolicitarArriendoDTO
from app.dominios.usuarios.repositorios import UsuarioRepositorio
from app.seguridad import requiere_propietario, requiere_token

# ── Servicio inyectado por el factory ──────────────────────────────────
servicio = None

# ── Blueprint ──────────────────────────────────────────────────────────
arriendos_bp = Blueprint("arriendos", __name__)


@arriendos_bp.route("/solicitar", methods=["POST"])
@requiere_token
def solicitar(usuario_id=None):
    """Crea una nueva solicitud de arriendo."""
    try:
        datos = SolicitarArriendoDTO().load(request.get_json() or {})
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

    solicitud = servicio.solicitar(datos, usuario_id)
    return (
        jsonify(
            {
                "success": True,
                "message": "Solicitud de arriendo enviada con éxito.",
                "data": solicitud.to_dict(),
            }
        ),
        201,
    )


@arriendos_bp.route("/mis-solicitudes", methods=["GET"])
@requiere_token
def mis_solicitudes(usuario_id=None):
    """Lista las solicitudes de arriendo enviadas por el usuario actual."""
    solicitudes = servicio.listar_mis_solicitudes(usuario_id)
    return (
        jsonify(
            {
                "success": True,
                "message": "Solicitudes obtenidas con éxito.",
                "data": [s.to_dict() for s in solicitudes],
            }
        ),
        200,
    )


@arriendos_bp.route("/solicitudes-recibidas", methods=["GET"])
@requiere_propietario
def solicitudes_recibidas(usuario_id=None):
    """Lista las solicitudes recibidas para las propiedades del propietario."""
    solicitudes = servicio.listar_solicitudes_recibidas(usuario_id)
    return (
        jsonify(
            {
                "success": True,
                "message": "Solicitudes recibidas obtenidas con éxito.",
                "data": [s.to_dict() for s in solicitudes],
            }
        ),
        200,
    )


@arriendos_bp.route("/<int:id>/responder", methods=["PATCH"])
@requiere_token
def responder(id, usuario_id=None):
    """Acepta o rechaza una solicitud de arriendo recibida."""
    try:
        datos = ResponderSolicitudDTO().load(request.get_json() or {})
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

    if datos["estado"] == "aceptada":
        fecha_inicio = datos.get("fecha_inicio")
        fecha_fin = datos.get("fecha_fin")
        precio_acordado = datos.get("precio_acordado")
        if not fecha_inicio or not fecha_fin or not precio_acordado:
            return jsonify({
                "success": False,
                "error": {"message": "Para crear el contrato debes indicar las fechas y el canon mensual acordado por el propietario."},
            }), 400
        if fecha_fin <= fecha_inicio:
            return jsonify({
                "success": False,
                "error": {"message": "La fecha de finalización debe ser posterior a la fecha de inicio."},
            }), 400

        solicitud = db.session.get(SolicitudArriendo, id)
        if solicitud is None:
            return jsonify({"success": False, "error": {"message": "Solicitud no encontrada."}}), 404
        usuario = UsuarioRepositorio.obtener_por_id(usuario_id)
        if solicitud.propiedad.propietario_id != usuario_id and not (
            usuario and usuario.rol == "admin"
        ):
            return jsonify({
                "success": False,
                "error": {"message": "No tienes permisos para responder esta solicitud."},
            }), 403
        if solicitud.estado != "pendiente":
            return jsonify({
                "success": False,
                "error": {"message": "La solicitud ya fue respondida previamente."},
            }), 409
        if not all((
            solicitud.arrendatario_nombre,
            solicitud.arrendatario_apellido,
            solicitud.arrendatario_cedula,
            solicitud.arrendatario_telefono,
        )):
            return jsonify({
                "success": False,
                "error": {"message": "La solicitud no tiene los datos obligatorios del inquilino. Pídele que complete su información y vuelva a solicitar."},
            }), 400

        perfil_propietario = solicitud.propiedad.propietario.perfil
        if not perfil_propietario or not perfil_propietario.nombre or not perfil_propietario.apellido:
            return jsonify({
                "success": False,
                "error": {"message": "Completa tu nombre y apellido en el perfil antes de generar el contrato."},
            }), 400

        try:
            plantilla = generar_plantilla_contrato()["plantilla"]
        except ServicioIAError as exc:
            return jsonify({"success": False, "error": {"message": str(exc)}}), exc.status_code

        reemplazos = {
            "ARRENDADOR_NOMBRE": f"{perfil_propietario.nombre} {perfil_propietario.apellido}",
            "ARRENDATARIO_NOMBRE": f"{solicitud.arrendatario_nombre} {solicitud.arrendatario_apellido}",
            "ARRENDATARIO_CEDULA": solicitud.arrendatario_cedula,
            "ARRENDATARIO_TELEFONO": solicitud.arrendatario_telefono,
            "INMUEBLE_DIRECCION": solicitud.propiedad.direccion,
            "INMUEBLE_BARRIO": solicitud.propiedad.barrio.nombre if solicitud.propiedad.barrio else "No especificado",
            "FECHA_INICIO": fecha_inicio.strftime("%d/%m/%Y"),
            "FECHA_FIN": fecha_fin.strftime("%d/%m/%Y"),
            "CANON_MENSUAL": f"${precio_acordado:,.0f} COP",
        }
        import re

        contenido = re.sub(
            r"\{\{([A-Z_]+)\}\}",
            lambda match: reemplazos.get(match.group(1), match.group(0)),
            plantilla,
        )
        if any(f"{{{{{clave}}}}}" in contenido for clave in reemplazos):
            return jsonify({
                "success": False,
                "error": {"message": "La IA no generó una plantilla contractual completa. Inténtalo nuevamente."},
            }), 502
        datos["contenido"] = contenido

    solicitud = servicio.responder_solicitud(id, datos, usuario_id)
    return (
        jsonify(
            {
                "success": True,
                "message": f"Solicitud {datos['estado']} con éxito.",
                "data": solicitud.to_dict(),
            }
        ),
        200,
    )


@arriendos_bp.route("/contratos", methods=["GET"])
@requiere_token
def listar_contratos(usuario_id=None):
    """Lista los contratos de arriendo asociados al usuario."""
    contratos = servicio.listar_contratos(usuario_id)
    return (
        jsonify(
            {
                "success": True,
                "message": "Contratos obtenidos con éxito.",
                "data": [c.to_dict() for c in contratos],
            }
        ),
        200,
    )
