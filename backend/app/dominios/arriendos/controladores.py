"""
Controladores del dominio de arriendos.

Define el blueprint `arriendos_bp` para solicitudes y contratos.
"""

from flask import Blueprint, jsonify, request
from marshmallow import ValidationError

from app.dominios.arriendos.dtos import ResponderSolicitudDTO, SolicitarArriendoDTO
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
