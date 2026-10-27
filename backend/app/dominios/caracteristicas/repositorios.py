"""
Repositorio del dominio de características.

Capa de acceso a datos para la tabla de características.
"""

from app import db
from app.dominios.caracteristicas.modelos import Caracteristica


class CaracteristicaRepositorio:
    """Métodos de acceso a datos para la tabla de características."""

    @staticmethod
    def guardar(caracteristica):
        """Persiste una característica en la base de datos."""
        db.session.add(caracteristica)
        db.session.commit()
        return caracteristica

    @staticmethod
    def obtener_por_id(caracteristica_id):
        """Obtiene una característica por su ID."""
        return db.session.get(Caracteristica, caracteristica_id)

    @staticmethod
    def obtener_por_nombre(nombre):
        """Obtiene una característica por su nombre exacto."""
        return Caracteristica.query.filter_by(nombre=nombre).first()

    @staticmethod
    def obtener_todos():
        """Retorna todas las características disponibles."""
        return Caracteristica.query.order_by(Caracteristica.nombre.asc()).all()

    @staticmethod
    def eliminar(caracteristica):
        """Elimina una característica de la base de datos."""
        db.session.delete(caracteristica)
        db.session.commit()
