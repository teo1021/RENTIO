"""
Servicios del dominio de barrios.

Lógica de negocio para gestionar barrios y sus propiedades.
Define excepciones de dominio propias.
"""

from app.dominios.barrios.modelos import Barrio
from app.dominios.barrios.repositorios import BarrioRepositorio

# ═══════════════════════════════════════════════════════════════════════════════
# Excepciones de dominio
# ═══════════════════════════════════════════════════════════════════════════════


class BarrioNoEncontradoError(Exception):
    """Se lanza cuando no se encuentra un barrio por ID."""

    pass


class BarrioDuplicadoError(Exception):
    """Se lanza cuando ya existe un barrio con el mismo nombre y comuna."""

    pass


# ═══════════════════════════════════════════════════════════════════════════════
# Servicio
# ═══════════════════════════════════════════════════════════════════════════════


class BarrioServicio:
    """Lógica de negocio para el dominio de barrios."""

    @staticmethod
    def crear(datos):
        """
        Crea un nuevo barrio validando duplicados.

        Args:
            datos: Diccionario validado por CrearBarrioDTO.

        Returns:
            Barrio: El barrio creado.

        Raises:
            BarrioDuplicadoError: Si ya existe en la misma comuna.
        """
        existente = BarrioRepositorio.obtener_por_nombre_y_comuna(datos["nombre"], datos["comuna"])
        if existente:
            raise BarrioDuplicadoError(
                f"El barrio '{datos['nombre']}' ya existe en la comuna '{datos['comuna']}'."
            )

        barrio = Barrio(
            nombre=datos["nombre"],
            comuna=datos["comuna"],
            zona=datos["zona"],
        )
        return BarrioRepositorio.guardar(barrio)

    @staticmethod
    def obtener_por_id(barrio_id):
        """
        Obtiene un barrio por su ID.

        Raises:
            BarrioNoEncontradoError: Si no existe.
        """
        barrio = BarrioRepositorio.obtener_por_id(barrio_id)
        if not barrio:
            raise BarrioNoEncontradoError(f"Barrio con id {barrio_id} no encontrado.")
        return barrio

    @staticmethod
    def listar():
        """Lista todos los barrios registrados."""
        return BarrioRepositorio.obtener_todos()

    @staticmethod
    def obtener_propiedades_por_barrio(barrio_id):
        """
        Obtiene las propiedades disponibles asociadas a un barrio.

        Raises:
            BarrioNoEncontradoError: Si el barrio no existe.
        """
        barrio = BarrioServicio.obtener_por_id(barrio_id)
        return barrio.propiedades.filter_by(estado="disponible").all()
