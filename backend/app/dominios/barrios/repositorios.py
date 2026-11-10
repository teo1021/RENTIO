"""
Repositorio del dominio de barrios.

Capa de acceso a datos para la tabla de barrios.
"""

import unicodedata

from app import db
from app.dominios.barrios.modelos import Barrio


class BarrioRepositorio:
    """Métodos de acceso a datos para la tabla de barrios."""

    @staticmethod
    def guardar(barrio):
        """Persiste un barrio en la base de datos."""
        db.session.add(barrio)
        db.session.commit()
        return barrio

    @staticmethod
    def obtener_por_id(barrio_id):
        """Obtiene un barrio por su ID."""
        return db.session.get(Barrio, barrio_id)

    @staticmethod
    def obtener_por_nombre_y_comuna(nombre, comuna):
        """Obtiene un barrio por nombre y comuna, ignorando tildes y mayúsculas."""
        nombre_normalizado = unicodedata.normalize("NFKD", nombre.strip().lower()).encode("ASCII", "ignore").decode()
        comuna_normalizada = unicodedata.normalize("NFKD", comuna.strip().lower()).encode("ASCII", "ignore").decode()
        return next(
            (
                barrio
                for barrio in Barrio.query.all()
                if unicodedata.normalize("NFKD", barrio.nombre.strip().lower()).encode("ASCII", "ignore").decode() == nombre_normalizado
                and unicodedata.normalize("NFKD", barrio.comuna.strip().lower()).encode("ASCII", "ignore").decode() == comuna_normalizada
            ),
            None,
        )

    @staticmethod
    def obtener_todos():
        """Retorna todos los barrios ordenados por comuna y nombre."""
        return Barrio.query.order_by(Barrio.comuna.asc(), Barrio.nombre.asc()).all()

    @staticmethod
    def eliminar(barrio):
        """Elimina un barrio de la base de datos."""
        db.session.delete(barrio)
        db.session.commit()
