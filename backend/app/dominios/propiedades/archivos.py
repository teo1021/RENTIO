"""Persistencia local de fotografías asociadas a propiedades."""

import os
import uuid

from werkzeug.utils import secure_filename

from app import db
from app.dominios.propiedades.modelos import ImagenPropiedad

MAX_IMAGE_SIZE = 5 * 1024 * 1024
ALLOWED_IMAGE_TYPES = {
    "image/jpeg": {".jpg", ".jpeg"},
    "image/png": {".png"},
    "image/webp": {".webp"},
}


def guardar_imagenes(propiedad, archivos, carpeta, base_url):
    """Guarda un grupo de fotografías ya validado y las asocia al inmueble."""
    archivos = [archivo for archivo in archivos if archivo and archivo.filename]
    if not archivos:
        raise ValueError("Debes enviar al menos una imagen.")
    if len(propiedad.imagenes) + len(archivos) > 10:
        raise ValueError("Puedes guardar máximo 10 fotos por propiedad.")

    for archivo in archivos:
        extension = os.path.splitext(secure_filename(archivo.filename))[1].lower()
        extensiones = ALLOWED_IMAGE_TYPES.get(archivo.mimetype)
        if not extensiones or extension not in extensiones:
            raise ValueError("Usa imágenes JPG, PNG o WEBP.")
        archivo.stream.seek(0, os.SEEK_END)
        size = archivo.stream.tell()
        archivo.stream.seek(0)
        if size > MAX_IMAGE_SIZE:
            raise ValueError("Cada fotografía debe pesar máximo 5 MB.")

    os.makedirs(carpeta, exist_ok=True)
    archivos_guardados = []
    imagenes = []
    try:
        for archivo in archivos:
            extension = os.path.splitext(secure_filename(archivo.filename))[1].lower()
            nombre = f"{uuid.uuid4().hex}{extension}"
            ruta = os.path.join(carpeta, nombre)
            archivo.save(ruta)
            archivos_guardados.append(ruta)

            imagen = ImagenPropiedad(
                propiedad=propiedad,
                url=f"{base_url.rstrip('/')}/static/uploads/propiedades/{nombre}",
                orden=len(propiedad.imagenes) + len(imagenes),
            )
            db.session.add(imagen)
            imagenes.append(imagen)
    except Exception:
        for ruta in archivos_guardados:
            try:
                os.remove(ruta)
            except FileNotFoundError:
                pass
        raise

    return imagenes, archivos_guardados


def borrar_archivos(rutas):
    """Elimina los archivos temporales creados para una transacción fallida."""
    for ruta in rutas:
        try:
            os.remove(ruta)
        except FileNotFoundError:
            pass


def eliminar_archivo_imagen(url, carpeta):
    """Elimina del almacenamiento local una imagen previamente guardada."""
    nombre = os.path.basename(url)
    if not nombre:
        return
    ruta = os.path.join(carpeta, nombre)
    try:
        os.remove(ruta)
    except FileNotFoundError:
        pass
