"""
Controladores del dominio de barrios.

Define el blueprint `barrios_bp` para consultar barrios y sus propiedades.
"""

from flask import Blueprint, jsonify, request
from marshmallow import ValidationError

from app.dominios.barrios.dtos import ActualizarBarrioDTO, CrearBarrioDTO
from app.dominios.barrios.servicios import BarrioDuplicadoError, BarrioNoEncontradoError
from app.seguridad import requiere_admin

# ── Servicio inyectado por el factory ──────────────────────────────────
servicio = None

# ── Blueprint ──────────────────────────────────────────────────────────
barrios_bp = Blueprint("barrios", __name__)


@barrios_bp.route("", methods=["GET"])
def listar():
    """Lista todos los barrios de Medellín (público)."""
    barrios = servicio.listar()
    return (
        jsonify(
            {
                "success": True,
                "message": "Barrios obtenidos con éxito.",
                "data": [b.to_dict() for b in barrios],
            }
        ),
        200,
    )


@barrios_bp.route("/<int:id>/propiedades", methods=["GET"])
def obtener_propiedades(id):
    """Lista las propiedades disponibles en un barrio específico (público)."""
    propiedades = servicio.obtener_propiedades_por_barrio(id)
    return (
        jsonify(
            {
                "success": True,
                "message": "Propiedades del barrio obtenidas con éxito.",
                "data": [p.to_dict() for p in propiedades],
            }
        ),
        200,
    )


@barrios_bp.route("", methods=["POST"])
@requiere_admin
def crear(usuario_id=None):
    """Crea un nuevo barrio (solo administradores)."""
    try:
        datos = CrearBarrioDTO().load(request.get_json() or {})
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

    try:
        barrio = servicio.crear(datos)
    except BarrioDuplicadoError as err:
        return jsonify({"success": False, "error": {"message": str(err)}}), 409
    return (
        jsonify(
            {
                "success": True,
                "message": "Barrio creado con éxito.",
                "data": barrio.to_dict(),
            }
        ),
        201,
    )


@barrios_bp.route("/<int:id>", methods=["PATCH"])
@requiere_admin
def actualizar(id, usuario_id=None):
    """Corrige los datos de un barrio sin cambiar sus relaciones con propiedades."""
    try:
        datos = ActualizarBarrioDTO().load(request.get_json() or {})
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

    try:
        barrio = servicio.actualizar(id, datos)
    except BarrioNoEncontradoError as err:
        return jsonify({"success": False, "error": {"message": str(err)}}), 404
    except BarrioDuplicadoError as err:
        return jsonify({"success": False, "error": {"message": str(err)}}), 409
    return (
        jsonify(
            {
                "success": True,
                "message": "Barrio actualizado con éxito.",
                "data": barrio.to_dict(),
            }
        ),
        200,
    )
