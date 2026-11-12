"""
Controladores del dominio de arriendos.

Define el blueprint `arriendos_bp` para el flujo completo:
  solicitud con datos personales → responder visita → generar contrato.
"""

from flask import Blueprint, jsonify, request
from marshmallow import ValidationError

from app.dominios.arriendos.dtos import (
    GenerarContratoDTO,
    ResponderSolicitudDTO,
    ResponderVisitaDTO,
    SolicitarArriendoDTO,
)
from app.dominios.arriendos.servicios import (
    EstadoSolicitudInvalidoError,
    PermisoArriendoError,
    SolicitudDuplicadaError,
    SolicitudNoEncontradaError,
)
from app.dominios.propiedades.servicios import PropiedadNoEncontradaError
from app.seguridad import requiere_propietario, requiere_token

# ── Servicio inyectado por el factory ──────────────────────────────────
servicio = None

# ── Blueprint ──────────────────────────────────────────────────────────
arriendos_bp = Blueprint("arriendos", __name__)


# ── Helpers ────────────────────────────────────────────────────────────

def _error(message, details=None, code=400):
    body = {"success": False, "error": {"message": message}}
    if details:
        body["error"]["details"] = details
    return jsonify(body), code


def _ok(data, message="", code=200):
    return jsonify({"success": True, "message": message, "data": data}), code


# ── Endpoints ──────────────────────────────────────────────────────────


@arriendos_bp.route("/solicitar", methods=["POST"])
@requiere_token
def solicitar(usuario_id=None):
    """Crea una nueva solicitud de arriendo con datos personales y fecha de visita."""
    try:
        datos = SolicitarArriendoDTO().load(request.get_json() or {})
    except ValidationError as err:
        return _error("Datos de entrada inválidos.", err.messages)

    try:
        solicitud = servicio.solicitar(datos, usuario_id)
    except PropiedadNoEncontradaError as exc:
        return _error(str(exc), code=404)
    except PermisoArriendoError as exc:
        return _error(str(exc), code=403)
    except EstadoSolicitudInvalidoError as exc:
        return _error(str(exc), code=409)
    except SolicitudDuplicadaError as exc:
        return _error(str(exc), code=409)

    return _ok(solicitud.to_dict(), "Solicitud de arriendo enviada con éxito.", 201)


@arriendos_bp.route("/mis-solicitudes", methods=["GET"])
@requiere_token
def mis_solicitudes(usuario_id=None):
    """Lista las solicitudes de arriendo enviadas por el usuario actual."""
    solicitudes = servicio.listar_mis_solicitudes(usuario_id)
    return _ok([s.to_dict() for s in solicitudes], "Solicitudes obtenidas con éxito.")


@arriendos_bp.route("/solicitudes-recibidas", methods=["GET"])
@requiere_propietario
def solicitudes_recibidas(usuario_id=None):
    """Lista las solicitudes recibidas para las propiedades del propietario."""
    solicitudes = servicio.listar_solicitudes_recibidas(usuario_id)
    return _ok([s.to_dict() for s in solicitudes], "Solicitudes recibidas obtenidas con éxito.")


@arriendos_bp.route("/<int:id>/responder-visita", methods=["PATCH"])
@requiere_token
def responder_visita(id, usuario_id=None):
    """El propietario acepta o rechaza la solicitud de visita."""
    try:
        datos = ResponderVisitaDTO().load(request.get_json() or {})
    except ValidationError as err:
        return _error("Datos de entrada inválidos.", err.messages)

    try:
        solicitud = servicio.responder_visita(id, datos, usuario_id)
    except SolicitudNoEncontradaError as exc:
        return _error(str(exc), code=404)
    except PermisoArriendoError as exc:
        return _error(str(exc), code=403)
    except EstadoSolicitudInvalidoError as exc:
        return _error(str(exc), code=409)

    accion = "aceptada" if datos["estado"] == "visita_programada" else "rechazada"
    return _ok(solicitud.to_dict(), f"Visita {accion} con éxito.")


@arriendos_bp.route("/<int:id>/generar-contrato", methods=["POST"])
@requiere_propietario
def generar_contrato(id, usuario_id=None):
    """El propietario genera el contrato formal después de la visita."""
    try:
        datos = GenerarContratoDTO().load(request.get_json() or {})
    except ValidationError as err:
        return _error("Datos de entrada inválidos.", err.messages)

    try:
        solicitud = servicio.generar_contrato(id, datos, usuario_id)
    except SolicitudNoEncontradaError as exc:
        return _error(str(exc), code=404)
    except PermisoArriendoError as exc:
        return _error(str(exc), code=403)
    except EstadoSolicitudInvalidoError as exc:
        return _error(str(exc), code=409)

    return _ok(
        solicitud.to_dict(),
        f"Contrato {solicitud.contrato.numero_contrato} generado con éxito.",
        201,
    )


@arriendos_bp.route("/<int:id>/responder", methods=["PATCH"])
@requiere_token
def responder(id, usuario_id=None):
    """Legado: acepta o rechaza una solicitud (compatibilidad con versiones anteriores)."""
    try:
        datos = ResponderSolicitudDTO().load(request.get_json() or {})
    except ValidationError as err:
        return _error("Datos de entrada inválidos.", err.messages)

    try:
        solicitud = servicio.responder_solicitud(id, datos, usuario_id)
    except SolicitudNoEncontradaError as exc:
        return _error(str(exc), code=404)
    except PermisoArriendoError as exc:
        return _error(str(exc), code=403)
    except EstadoSolicitudInvalidoError as exc:
        return _error(str(exc), code=409)

    return _ok(solicitud.to_dict(), f"Solicitud {datos['estado']} con éxito.")


@arriendos_bp.route("/contratos", methods=["GET"])
@requiere_token
def listar_contratos(usuario_id=None):
    """Lista los contratos de arriendo asociados al usuario."""
    contratos = servicio.listar_contratos(usuario_id)
    return _ok([c.to_dict() for c in contratos], "Contratos obtenidos con éxito.")
