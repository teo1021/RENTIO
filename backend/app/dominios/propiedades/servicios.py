"""
Servicios del dominio de propiedades.

Lógica de negocio para crear, actualizar, eliminar y filtrar propiedades.
Define excepciones de dominio propias.
"""

from app import db
from app.dominios.caracteristicas.repositorios import CaracteristicaRepositorio
from app.dominios.propiedades.modelos import Propiedad
from app.dominios.propiedades.repositorios import PropiedadRepositorio
from app.dominios.usuarios.repositorios import UsuarioRepositorio

# ═══════════════════════════════════════════════════════════════════════════════
# Excepciones de dominio
# ═══════════════════════════════════════════════════════════════════════════════


class PropiedadNoEncontradaError(Exception):
    """Se lanza cuando no se encuentra una propiedad por ID."""

    pass


class PermisoPropiedadError(Exception):
    """Se lanza cuando un usuario intenta operar sobre una propiedad que no le pertenece."""

    pass


# ═══════════════════════════════════════════════════════════════════════════════
# Funciones auxiliares
# ═══════════════════════════════════════════════════════════════════════════════


def _verificar_propiedad_y_permisos(propiedad_id, usuario_id):
    """
    Verifica que la propiedad exista y que el usuario sea su dueño o admin.

    Returns:
        Propiedad: La propiedad encontrada.

    Raises:
        PropiedadNoEncontradaError: Si la propiedad no existe.
        PermisoPropiedadError: Si el usuario no tiene permisos.
    """
    propiedad = PropiedadRepositorio.obtener_por_id(propiedad_id)
    if not propiedad:
        raise PropiedadNoEncontradaError(f"Propiedad con id {propiedad_id} no encontrada.")

    usuario = UsuarioRepositorio.obtener_por_id(usuario_id)
    if propiedad.propietario_id != usuario_id and (not usuario or usuario.rol != "admin"):
        raise PermisoPropiedadError("No tienes permisos para modificar esta propiedad.")

    return propiedad


# ═══════════════════════════════════════════════════════════════════════════════
# Servicio
# ═══════════════════════════════════════════════════════════════════════════════


class PropiedadServicio:
    """Lógica de negocio para el dominio de propiedades."""

    @staticmethod
    def crear(datos, propietario_id):
        """
        Crea una nueva propiedad asociada a un propietario.

        Args:
            datos: Diccionario validado por CrearPropiedadDTO.
            propietario_id: ID del usuario propietario.

        Returns:
            Propiedad: La propiedad creada.
        """
        caracteristicas_ids = datos.pop("caracteristicas_ids", [])

        propiedad = Propiedad(
            titulo=datos["titulo"],
            descripcion=datos.get("descripcion"),
            precio_mensual=datos["precio_mensual"],
            direccion=datos["direccion"],
            estrato=datos["estrato"],
            area_m2=datos.get("area_m2"),
            habitaciones=datos.get("habitaciones", 1),
            banos=datos.get("banos", 1),
            tipo=datos.get("tipo", "apartamento"),
            barrio_id=datos.get("barrio_id"),
            propietario_id=propietario_id,
        )

        if caracteristicas_ids:
            for cid in caracteristicas_ids:
                caract = CaracteristicaRepositorio.obtener_por_id(cid)
                if caract:
                    propiedad.caracteristicas.append(caract)

        PropiedadRepositorio.guardar(propiedad)
        return propiedad

    @staticmethod
    def obtener_por_id(propiedad_id):
        """
        Obtiene una propiedad por su ID.

        Raises:
            PropiedadNoEncontradaError: Si no existe.
        """
        propiedad = PropiedadRepositorio.obtener_por_id(propiedad_id)
        if not propiedad:
            raise PropiedadNoEncontradaError(f"Propiedad con id {propiedad_id} no encontrada.")
        return propiedad

    @staticmethod
    def listar(filtros=None):
        """Lista propiedades con filtros opcionales."""
        return PropiedadRepositorio.obtener_todos(filtros)

    @staticmethod
    def listar_mis_propiedades(propietario_id):
        """Lista las propiedades del propietario autenticado."""
        return PropiedadRepositorio.obtener_por_propietario(propietario_id)

    @staticmethod
    def actualizar(propiedad_id, datos, usuario_id):
        """
        Actualiza parcialmente una propiedad.

        Raises:
            PropiedadNoEncontradaError: Si la propiedad no existe.
            PermisoPropiedadError: Si el usuario no tiene permisos.
        """
        propiedad = _verificar_propiedad_y_permisos(propiedad_id, usuario_id)

        campos_actualizables = [
            "titulo",
            "descripcion",
            "precio_mensual",
            "direccion",
            "estrato",
            "area_m2",
            "habitaciones",
            "banos",
            "tipo",
            "estado",
            "barrio_id",
        ]
        for campo in campos_actualizables:
            valor = datos.get(campo)
            if valor is not None:
                setattr(propiedad, campo, valor)

        PropiedadRepositorio.guardar(propiedad)
        return propiedad

    @staticmethod
    def eliminar(propiedad_id, usuario_id):
        """
        Elimina una propiedad.

        Raises:
            PropiedadNoEncontradaError: Si la propiedad no existe.
            PermisoPropiedadError: Si el usuario no tiene permisos.
        """
        propiedad = _verificar_propiedad_y_permisos(propiedad_id, usuario_id)
        PropiedadRepositorio.eliminar(propiedad)

    @staticmethod
    def actualizar_caracteristicas(propiedad_id, caracteristicas_ids, usuario_id):
        """
        Reemplaza las características de una propiedad.

        Raises:
            PropiedadNoEncontradaError: Si la propiedad no existe.
            PermisoPropiedadError: Si el usuario no tiene permisos.
        """
        propiedad = _verificar_propiedad_y_permisos(propiedad_id, usuario_id)

        propiedad.caracteristicas.clear()

        for cid in caracteristicas_ids:
            caract = CaracteristicaRepositorio.obtener_por_id(cid)
            if caract:
                propiedad.caracteristicas.append(caract)

        db.session.commit()
        return propiedad
