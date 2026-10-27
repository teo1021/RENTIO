"""
Servicios del dominio de características.

Lógica de negocio para gestionar características de propiedades.
Define excepciones de dominio propias.
"""

from app.dominios.caracteristicas.modelos import Caracteristica
from app.dominios.caracteristicas.repositorios import CaracteristicaRepositorio

# ═══════════════════════════════════════════════════════════════════════════════
# Excepciones de dominio
# ═══════════════════════════════════════════════════════════════════════════════


class CaracteristicaNoEncontradaError(Exception):
    """Se lanza cuando no se encuentra una característica por ID."""

    pass


class CaracteristicaDuplicadaError(Exception):
    """Se lanza cuando se intenta crear una característica con nombre existente."""

    pass


# ═══════════════════════════════════════════════════════════════════════════════
# Servicio
# ═══════════════════════════════════════════════════════════════════════════════


class CaracteristicaServicio:
    """Lógica de negocio para el dominio de características."""

    @staticmethod
    def crear(datos):
        """
        Crea una nueva característica verificando que no esté duplicada.

        Args:
            datos: Diccionario validado por CrearCaracteristicaDTO.

        Returns:
            Caracteristica: La característica creada.

        Raises:
            CaracteristicaDuplicadaError: Si el nombre ya existe.
        """
        existente = CaracteristicaRepositorio.obtener_por_nombre(datos["nombre"])
        if existente:
            raise CaracteristicaDuplicadaError(f"La característica '{datos['nombre']}' ya existe.")

        caracteristica = Caracteristica(
            nombre=datos["nombre"],
            icono=datos.get("icono"),
        )
        return CaracteristicaRepositorio.guardar(caracteristica)

    @staticmethod
    def obtener_por_id(caracteristica_id):
        """
        Obtiene una característica por su ID.

        Raises:
            CaracteristicaNoEncontradaError: Si no existe.
        """
        caracteristica = CaracteristicaRepositorio.obtener_por_id(caracteristica_id)
        if not caracteristica:
            raise CaracteristicaNoEncontradaError(
                f"Característica con id {caracteristica_id} no encontrada."
            )
        return caracteristica

    @staticmethod
    def listar():
        """Lista todas las características disponibles."""
        return CaracteristicaRepositorio.obtener_todos()

    @staticmethod
    def eliminar(caracteristica_id):
        """
        Elimina una característica por ID.

        Raises:
            CaracteristicaNoEncontradaError: Si no existe.
        """
        caracteristica = CaracteristicaRepositorio.obtener_por_id(caracteristica_id)
        if not caracteristica:
            raise CaracteristicaNoEncontradaError(
                f"Característica con id {caracteristica_id} no encontrada."
            )
        CaracteristicaRepositorio.eliminar(caracteristica)
