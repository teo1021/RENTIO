"""
Controladores del dominio de propiedades.

Define el blueprint `propiedades_bp` con CRUD completo, filtrado y
gestión de características.
"""

from flask import Blueprint, jsonify, request
from marshmallow import ValidationError

from app.dominios.propiedades.dtos import (
    ActualizarCaracteristicasDTO,
    ActualizarPropiedadDTO,
    CrearPropiedadDTO,
    FiltroPropiedadDTO,
)
from app.seguridad import requiere_propietario, requiere_token

# ── Servicio inyectado por el factory ──────────────────────────────────
servicio = None

# ── Blueprint ──────────────────────────────────────────────────────────
propiedades_bp = Blueprint("propiedades", __name__)


@propiedades_bp.route("", methods=["POST"])
@requiere_propietario
def crear(usuario_id=None):
    """Crea una nueva propiedad (solo propietario)."""
    try:
        datos = CrearPropiedadDTO().load(request.get_json() or {})
    except ValidationError as err:
        return (
            jsonify(
                {
                    "success": False,
                    "error": {"message": "Datos de entrada inválidos.", "details": err.messages},
                }
            ),
            400,
        )

    propiedad = servicio.crear(datos, usuario_id)
    return (
        jsonify(
            {
                "success": True,
                "message": "Propiedad creada con éxito.",
                "data": propiedad.to_dict(),
            }
        ),
        201,
    )


@propiedades_bp.route("", methods=["GET"])
def listar():
    """Lista propiedades con filtros opcionales (público)."""
    try:
        filtros = FiltroPropiedadDTO().load(request.args.to_dict())
    except ValidationError as err:
        return (
            jsonify(
                {
                    "success": False,
                    "error": {"message": "Filtros inválidos.", "details": err.messages},
                }
            ),
            400,
        )

    propiedades = servicio.listar(filtros)
    return (
        jsonify(
            {
                "success": True,
                "message": "Propiedades obtenidas con éxito.",
                "data": [p.to_dict() for p in propiedades],
            }
        ),
        200,
    )


@propiedades_bp.route("/<int:id>", methods=["GET"])
def obtener(id):
    """Obtiene una propiedad por su ID (público)."""
    propiedad = servicio.obtener_por_id(id)
    return (
        jsonify(
            {
                "success": True,
                "message": "Propiedad obtenida con éxito.",
                "data": propiedad.to_dict(),
            }
        ),
        200,
    )


@propiedades_bp.route("/<int:id>", methods=["PATCH"])
@requiere_token
def actualizar(id, usuario_id=None):
    """Actualiza parcialmente una propiedad (dueño o admin)."""
    try:
        datos = ActualizarPropiedadDTO().load(request.get_json() or {})
    except ValidationError as err:
        return (
            jsonify(
                {
                    "success": False,
                    "error": {"message": "Datos de entrada inválidos.", "details": err.messages},
                }
            ),
            400,
        )

    propiedad = servicio.actualizar(id, datos, usuario_id)
    return (
        jsonify(
            {
                "success": True,
                "message": "Propiedad actualizada con éxito.",
                "data": propiedad.to_dict(),
            }
        ),
        200,
    )


@propiedades_bp.route("/<int:id>", methods=["DELETE"])
@requiere_token
def eliminar(id, usuario_id=None):
    """Elimina una propiedad (dueño o admin)."""
    servicio.eliminar(id, usuario_id)
    return (
        jsonify(
            {
                "success": True,
                "message": "Propiedad eliminada con éxito.",
                "data": None,
            }
        ),
        200,
    )


@propiedades_bp.route("/<int:id>/caracteristicas", methods=["PATCH"])
@requiere_token
def actualizar_caracteristicas(id, usuario_id=None):
    """Actualiza las características de una propiedad (dueño o admin)."""
    try:
        datos = ActualizarCaracteristicasDTO().load(request.get_json() or {})
    except ValidationError as err:
        return (
            jsonify(
                {
                    "success": False,
                    "error": {"message": "Datos de entrada inválidos.", "details": err.messages},
                }
            ),
            400,
        )

    propiedad = servicio.actualizar_caracteristicas(id, datos["caracteristicas_ids"], usuario_id)
    return (
        jsonify(
            {
                "success": True,
                "message": "Características actualizadas con éxito.",
                "data": propiedad.to_dict(),
            }
        ),
        200,
    )


@propiedades_bp.route("/mis-propiedades", methods=["GET"])
@requiere_propietario
def mis_propiedades(usuario_id=None):
    """Lista las propiedades del propietario autenticado."""
    propiedades = servicio.listar_mis_propiedades(usuario_id)
    return (
        jsonify(
            {
                "success": True,
                "message": "Propiedades obtenidas con éxito.",
                "data": [p.to_dict() for p in propiedades],
            }
        ),
        200,
    )
