"""
Controladores del dominio de características.

Define el blueprint `caracteristicas_bp` para crear y listar características.
"""

from flask import Blueprint, jsonify, request
from marshmallow import ValidationError

from app.dominios.caracteristicas.dtos import CrearCaracteristicaDTO
from app.seguridad import requiere_admin

# ── Servicio inyectado por el factory ──────────────────────────────────
servicio = None

# ── Blueprint ──────────────────────────────────────────────────────────
caracteristicas_bp = Blueprint("caracteristicas", __name__)


@caracteristicas_bp.route("", methods=["POST"])
@requiere_admin
def crear(usuario_id=None):
    """Crea una nueva característica (solo administradores)."""
    try:
        datos = CrearCaracteristicaDTO().load(request.get_json() or {})
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

    caracteristica = servicio.crear(datos)
    return (
        jsonify(
            {
                "success": True,
                "message": "Característica creada con éxito.",
                "data": caracteristica.to_dict(),
            }
        ),
        201,
    )


@caracteristicas_bp.route("", methods=["GET"])
def listar():
    """Lista todas las características disponibles (público)."""
    caracteristicas = servicio.listar()
    return (
        jsonify(
            {
                "success": True,
                "message": "Características obtenidas con éxito.",
                "data": [c.to_dict() for c in caracteristicas],
            }
        ),
        200,
    )
