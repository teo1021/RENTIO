"""
Repositorio del dominio de propiedades.

Capa de acceso a datos para propiedades e imágenes.
"""

from app import db
from app.dominios.propiedades.modelos import ImagenPropiedad, Propiedad


class PropiedadRepositorio:
    """Métodos de acceso a datos para la tabla de propiedades."""

    @staticmethod
    def guardar(propiedad):
        """Persiste una propiedad en la base de datos."""
        db.session.add(propiedad)
        db.session.commit()
        return propiedad

    @staticmethod
    def obtener_por_id(propiedad_id):
        """Obtiene una propiedad por su ID."""
        return db.session.get(Propiedad, propiedad_id)

    @staticmethod
    def obtener_todos(filtros=None):
        """
        Obtiene propiedades con filtros opcionales.

        Args:
            filtros: Diccionario con filtros validados por FiltroPropiedadDTO.

        Returns:
            list: Lista de propiedades que cumplen los filtros.
        """
        query = Propiedad.query.filter(Propiedad.estado != "inactiva")

        if filtros:
            if filtros.get("barrio_id"):
                query = query.filter(Propiedad.barrio_id == filtros["barrio_id"])
            if filtros.get("estrato"):
                query = query.filter(Propiedad.estrato == filtros["estrato"])
            if filtros.get("precio_min") is not None:
                query = query.filter(Propiedad.precio_mensual >= filtros["precio_min"])
            if filtros.get("precio_max") is not None:
                query = query.filter(Propiedad.precio_mensual <= filtros["precio_max"])
            if filtros.get("tipo"):
                query = query.filter(Propiedad.tipo == filtros["tipo"])
            if filtros.get("habitaciones") is not None:
                query = query.filter(Propiedad.habitaciones >= filtros["habitaciones"])

        return query.order_by(Propiedad.fecha_creacion.desc()).all()

    @staticmethod
    def obtener_por_propietario(propietario_id):
        """Obtiene todas las propiedades de un propietario."""
        return Propiedad.query.filter_by(propietario_id=propietario_id).all()

    @staticmethod
    def obtener_por_barrio(barrio_id):
        """Obtiene todas las propiedades de un barrio."""
        return (
            Propiedad.query.filter_by(barrio_id=barrio_id)
            .filter(Propiedad.estado != "inactiva")
            .all()
        )

    @staticmethod
    def eliminar(propiedad):
        """Elimina una propiedad de la base de datos."""
        db.session.delete(propiedad)
        db.session.commit()


class ImagenPropiedadRepositorio:
    """Métodos de acceso a datos para la tabla de imágenes de propiedad."""

    @staticmethod
    def guardar(imagen):
        """Persiste una imagen de propiedad."""
        db.session.add(imagen)
        db.session.commit()
        return imagen

    @staticmethod
    def eliminar_por_propiedad(propiedad_id):
        """Elimina todas las imágenes de una propiedad."""
        ImagenPropiedad.query.filter_by(propiedad_id=propiedad_id).delete()
        db.session.commit()
