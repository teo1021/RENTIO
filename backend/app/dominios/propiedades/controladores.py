"""
Controladores del dominio de propiedades.
"""

import os
import uuid
from pathlib import Path

from flask import Blueprint, current_app, jsonify, request, url_for
from marshmallow import ValidationError
from werkzeug.utils import secure_filename

from app import db
from app.dominios.propiedades.dtos import (
    ActualizarCaracteristicasDTO,
    ActualizarPropiedadDTO,
    CrearPropiedadDTO,
    FiltroPropiedadDTO,
)
from app.dominios.propiedades.modelos import ImagenPropiedad
from app.dominios.propiedades.repositorios import PropiedadRepositorio
from app.seguridad import requiere_propietario, requiere_token

servicio = None
propiedades_bp = Blueprint("propiedades", __name__)

EXTENSIONES_PERMITIDAS = {".jpg", ".jpeg", ".png", ".webp"}
TIPOS_PERMITIDOS = {
    ".jpg": (b"\xff\xd8\xff",),
    ".jpeg": (b"\xff\xd8\xff",),
    ".png": (b"\x89PNG\r\n\x1a\n",),
    ".webp": (b"RIFF",),
}
MAX_IMAGEN_BYTES = 5 * 1024 * 1024
MAX_IMAGENES = 10


def _es_imagen_valida(archivo, extension):
    contenido = archivo.read(16)
    archivo.seek(0)
    if extension not in TIPOS_PERMITIDOS:
        return False
    if extension == ".webp":
        return contenido.startswith(b"RIFF") and contenido[8:12] == b"WEBP"
    return any(contenido.startswith(firma) for firma in TIPOS_PERMITIDOS[extension])


def _propiedad_de_usuario(propiedad_id, usuario_id):
    propiedad = PropiedadRepositorio.obtener_por_id(propiedad_id)
    if propiedad is None:
        return None, (jsonify({"success": False, "error": {"message": "Propiedad no encontrada."}}), 404)
    if propiedad.propietario_id != usuario_id:
        return None, (jsonify({"success": False, "error": {"message": "No tienes permisos sobre esta propiedad."}}), 403)
    return propiedad, None


@propiedades_bp.route("", methods=["POST"])
@requiere_propietario
def crear(usuario_id=None):
    try:
        datos = CrearPropiedadDTO().load(request.get_json() or {})
    except ValidationError as err:
        return jsonify({"success": False, "error": {"message": "Datos de entrada inválidos.", "details": err.messages}}), 400
    propiedad = servicio.crear(datos, usuario_id)
    return jsonify({"success": True, "message": "Propiedad creada con éxito.", "data": propiedad.to_dict()}), 201


@propiedades_bp.route("", methods=["GET"])
def listar():
    try:
        filtros = FiltroPropiedadDTO().load(request.args.to_dict())
    except ValidationError as err:
        return jsonify({"success": False, "error": {"message": "Filtros inválidos.", "details": err.messages}}), 400
    propiedades = servicio.listar(filtros)
    return jsonify({"success": True, "message": "Propiedades obtenidas con éxito.", "data": [p.to_dict() for p in propiedades]}), 200


@propiedades_bp.route("/mis-propiedades", methods=["GET"])
@requiere_propietario
def mis_propiedades(usuario_id=None):
    propiedades = servicio.listar_mis_propiedades(usuario_id)
    return jsonify({"success": True, "message": "Propiedades obtenidas con éxito.", "data": [p.to_dict() for p in propiedades]}), 200


@propiedades_bp.route("/<int:id>", methods=["GET"])
def obtener(id):
    propiedad = servicio.obtener_por_id(id)

    if propiedad is None:
        return jsonify({
            "success": False,
            "message": "Propiedad no encontrada.",
            "data": None
        }), 404

    return jsonify({
        "success": True,
        "message": "Propiedad obtenida con ?xito.",
        "data": propiedad.to_dict()
    }), 200

@propiedades_bp.route("/<int:id>", methods=["PATCH"])
@requiere_propietario
def actualizar(id, usuario_id=None):
    try:
        datos = ActualizarPropiedadDTO().load(request.get_json() or {})
    except ValidationError as err:
        return jsonify({"success": False, "error": {"message": "Datos de entrada inválidos.", "details": err.messages}}), 400
    propiedad = servicio.actualizar(id, datos, usuario_id)
    return jsonify({"success": True, "message": "Propiedad actualizada con éxito.", "data": propiedad.to_dict()}), 200


@propiedades_bp.route("/<int:id>", methods=["DELETE"])
@requiere_propietario
def eliminar(id, usuario_id=None):
    servicio.eliminar(id, usuario_id)
    return jsonify({"success": True, "message": "Propiedad eliminada con éxito.", "data": None}), 200


@propiedades_bp.route("/<int:id>/caracteristicas", methods=["PATCH"])
@requiere_propietario
def actualizar_caracteristicas(id, usuario_id=None):
    try:
        datos = ActualizarCaracteristicasDTO().load(request.get_json() or {})
    except ValidationError as err:
        return jsonify({"success": False, "error": {"message": "Datos de entrada inválidos.", "details": err.messages}}), 400
    propiedad = servicio.actualizar_caracteristicas(id, datos["caracteristicas_ids"], usuario_id)
    return jsonify({"success": True, "message": "Características actualizadas con éxito.", "data": propiedad.to_dict()}), 200


@propiedades_bp.route("/<int:id>/imagenes", methods=["POST"])
@requiere_propietario
def subir_imagenes(id, usuario_id=None):
    propiedad, error = _propiedad_de_usuario(id, usuario_id)
    if error:
        return error

    archivos = request.files.getlist("imagenes")
    archivos = [archivo for archivo in archivos if archivo and archivo.filename]
    if not archivos:
        return jsonify({"success": False, "error": {"message": "Selecciona al menos una imagen."}}), 400
    if len(propiedad.imagenes) + len(archivos) > MAX_IMAGENES:
        return jsonify({"success": False, "error": {"message": "Cada propiedad admite máximo 10 imágenes."}}), 400

    validaciones = []
    for archivo in archivos:
        extension = Path(secure_filename(archivo.filename)).suffix.lower()
        archivo.seek(0, os.SEEK_END)
        tamano = archivo.tell()
        archivo.seek(0)
        if extension not in EXTENSIONES_PERMITIDAS or tamano > MAX_IMAGEN_BYTES or tamano == 0 or not _es_imagen_valida(archivo, extension):
            return jsonify({"success": False, "error": {"message": "Solo se permiten imágenes JPG, PNG o WEBP de máximo 5 MB cada una."}}), 400
        validaciones.append((archivo, extension))

    carpeta = Path(current_app.root_path) / "static" / "uploads" / "propiedades" / str(id)
    carpeta.mkdir(parents=True, exist_ok=True)
    archivos_guardados = []
    try:
        for archivo, extension in validaciones:
            nombre = f"{uuid.uuid4().hex}{extension}"
            destino = carpeta / nombre
            archivo.save(destino)
            archivos_guardados.append(destino)
            url = request.host_url.rstrip("/") + url_for("static", filename=f"uploads/propiedades/{id}/{nombre}")
            imagen = ImagenPropiedad(url=url, orden=len(propiedad.imagenes))
            imagen.propiedad_id = id
            db.session.add(imagen)
        db.session.commit()
    except Exception:
        db.session.rollback()
        for archivo_path in archivos_guardados:
            archivo_path.unlink(missing_ok=True)
        raise

    propiedad = PropiedadRepositorio.obtener_por_id(id)
    return jsonify({"success": True, "message": "Imágenes guardadas.", "data": propiedad.to_dict()["imagenes"]}), 201


@propiedades_bp.route("/<int:id>/imagenes/<int:imagen_id>", methods=["DELETE"])
@requiere_propietario
def eliminar_imagen(id, imagen_id, usuario_id=None):
    propiedad, error = _propiedad_de_usuario(id, usuario_id)
    if error:
        return error
    imagen = next((item for item in propiedad.imagenes if item.id == imagen_id), None)
    if imagen is None:
        return jsonify({"success": False, "error": {"message": "Imagen no encontrada."}}), 404

    prefijo = request.host_url.rstrip("/")
    ruta_relativa = imagen.url.removeprefix(prefijo).lstrip("/")
    if ruta_relativa.startswith("static/"):
        archivo = Path(current_app.root_path) / ruta_relativa
        archivo.unlink(missing_ok=True)
    db.session.delete(imagen)
    for orden, item in enumerate([item for item in propiedad.imagenes if item.id != imagen_id]):
        item.orden = orden
    db.session.commit()
    return jsonify({"success": True, "message": "Imagen eliminada.", "data": propiedad.to_dict()["imagenes"]}), 200
