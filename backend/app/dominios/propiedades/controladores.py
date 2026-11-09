"""
Controladores del dominio de propiedades.

Define el blueprint `propiedades_bp` con CRUD completo, filtrado y
gestión de características.
"""

import os

from flask import Blueprint, current_app, jsonify, request
from marshmallow import ValidationError

from app import db
from app.dominios.propiedades.archivos import (
    borrar_archivos,
    eliminar_archivo_imagen,
    guardar_imagenes,
)
from app.dominios.propiedades.dtos import (
    ActualizarCaracteristicasDTO,
    ActualizarPropiedadDTO,
    CrearPropiedadDTO,
    FiltroPropiedadDTO,
)
from app.dominios.propiedades.modelos import ImagenPropiedad, Propiedad
from app.dominios.usuarios.repositorios import UsuarioRepositorio
from app.seguridad import requiere_propietario, requiere_token

# ── Servicio inyectado por el factory ──────────────────────────────────
servicio = None

# ── Blueprint ──────────────────────────────────────────────────────────
propiedades_bp = Blueprint("propiedades", __name__)


def _puede_modificar_propiedad(propiedad, usuario_id):
    if propiedad is None:
        return False
    usuario = UsuarioRepositorio.obtener_por_id(usuario_id)
    return propiedad.propietario_id == usuario_id or (usuario is not None and usuario.rol == "admin")


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


@propiedades_bp.route("/<int:id>/imagenes", methods=["POST"])
@requiere_token
def subir_imagenes(id, usuario_id=None):
    """Adjunta imágenes a una propiedad ya creada."""
    propiedad = Propiedad.query.filter_by(id=id).first()
    if propiedad is None:
        return jsonify({"success": False, "error": {"message": "Propiedad no encontrada."}}), 404
    if not _puede_modificar_propiedad(propiedad, usuario_id):
        return jsonify({"success": False, "error": {"message": "No tienes permisos para modificar esta propiedad."}}), 403

    archivos = request.files.getlist("imagenes")
    carpeta = current_app.config.get("PROPERTY_IMAGE_FOLDER") or os.path.join(
        current_app.static_folder or "", "uploads", "propiedades"
    )
    try:
        imagenes, rutas = guardar_imagenes(
            propiedad,
            archivos,
            carpeta,
            request.host_url,
        )
    except ValueError as exc:
        return jsonify({"success": False, "error": {"message": str(exc)}}), 400

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        borrar_archivos(rutas)
        raise
    return jsonify({
        "success": True,
        "message": "Imágenes cargadas con éxito.",
        "data": [imagen.to_dict() for imagen in imagenes],
    }), 200


@propiedades_bp.route("/<int:id>/imagenes/<int:imagen_id>", methods=["DELETE"])
@requiere_token
def eliminar_imagen(id, imagen_id, usuario_id=None):
    """Elimina una imagen asociada a una propiedad."""
    propiedad = Propiedad.query.filter_by(id=id).first()
    if propiedad is None:
        return jsonify({"success": False, "error": {"message": "Propiedad no encontrada."}}), 404
    if not _puede_modificar_propiedad(propiedad, usuario_id):
        return jsonify({"success": False, "error": {"message": "No tienes permisos para modificar esta propiedad."}}), 403

    imagen = ImagenPropiedad.query.filter_by(id=imagen_id, propiedad_id=id).first()
    if imagen is None:
        return jsonify({"success": False, "error": {"message": "Imagen no encontrada."}}), 404

    db.session.delete(imagen)
    db.session.commit()
    carpeta = current_app.config.get("PROPERTY_IMAGE_FOLDER") or os.path.join(
        current_app.static_folder or "", "uploads", "propiedades"
    )
    eliminar_archivo_imagen(imagen.url, carpeta)

    imagenes = [item.to_dict() for item in Propiedad.query.get(id).imagenes]
    return jsonify({"success": True, "message": "Imagen eliminada con éxito.", "data": imagenes}), 200
