"""
Servicios del dominio de arriendos.

Lógica de negocio para solicitudes y formalización de contratos.
Define excepciones de dominio propias.
"""

from datetime import date, timedelta

from app.dominios.arriendos.modelos import ContratoArriendo, SolicitudArriendo
from app.dominios.arriendos.repositorios import ContratoRepositorio, SolicitudRepositorio
from app.dominios.propiedades.repositorios import PropiedadRepositorio
from app.dominios.propiedades.servicios import PropiedadNoEncontradaError
from app.dominios.usuarios.repositorios import UsuarioRepositorio

# ═══════════════════════════════════════════════════════════════════════════════
# Excepciones de dominio
# ═══════════════════════════════════════════════════════════════════════════════


class SolicitudNoEncontradaError(Exception):
    """Se lanza cuando no se encuentra una solicitud por ID."""

    pass


class SolicitudDuplicadaError(Exception):
    """Se lanza cuando ya existe una solicitud pendiente para la misma propiedad."""

    pass


class EstadoSolicitudInvalidoError(Exception):
    """Se lanza cuando se realiza una acción sobre una solicitud o propiedad en estado incompatible."""

    pass


class PermisoArriendoError(Exception):
    """Se lanza cuando un usuario intenta operar sobre una solicitud sin autorización."""

    pass


class ContratoNoEncontradoError(Exception):
    """Se lanza cuando no se encuentra un contrato por ID."""

    pass


# ═══════════════════════════════════════════════════════════════════════════════
# Servicio
# ═══════════════════════════════════════════════════════════════════════════════


class ArriendoServicio:
    """Lógica de negocio para solicitudes y contratos de arriendo."""

    @staticmethod
    def solicitar(datos, arrendatario_id):
        """
        Crea una nueva solicitud de arriendo para una propiedad.

        Args:
            datos: Diccionario validado por SolicitarArriendoDTO.
            arrendatario_id: ID del usuario solicitante.

        Raises:
            PropiedadNoEncontradaError: Si la propiedad no existe.
            PermisoArriendoError: Si intenta solicitar su propia casa.
            EstadoSolicitudInvalidoError: Si la propiedad no está disponible.
            SolicitudDuplicadaError: Si ya tiene solicitud pendiente.
        """
        propiedad_id = datos["propiedad_id"]
        propiedad = PropiedadRepositorio.obtener_por_id(propiedad_id)
        if not propiedad:
            raise PropiedadNoEncontradaError(f"Propiedad con id {propiedad_id} no encontrada.")

        if propiedad.propietario_id == arrendatario_id:
            raise PermisoArriendoError("No puedes solicitar arriendo para tu propia propiedad.")

        if propiedad.estado != "disponible":
            raise EstadoSolicitudInvalidoError(
                f"La propiedad no está disponible para arriendo (estado actual: {propiedad.estado})."
            )

        pendiente = SolicitudRepositorio.obtener_pendiente(propiedad_id, arrendatario_id)
        if pendiente:
            raise SolicitudDuplicadaError("Ya tienes una solicitud pendiente para esta propiedad.")

        solicitud = SolicitudArriendo(
            propiedad_id=propiedad_id,
            arrendatario_id=arrendatario_id,
            mensaje=datos.get("mensaje"),
        )
        return SolicitudRepositorio.guardar(solicitud)

    @staticmethod
    def listar_mis_solicitudes(arrendatario_id):
        """Lista todas las solicitudes enviadas por el arrendatario."""
        return SolicitudRepositorio.obtener_por_arrendatario(arrendatario_id)

    @staticmethod
    def listar_solicitudes_recibidas(propietario_id):
        """Lista todas las solicitudes recibidas para propiedades del propietario."""
        return SolicitudRepositorio.obtener_por_propietario(propietario_id)

    @staticmethod
    def responder_solicitud(solicitud_id, datos, usuario_id):
        """
        Permite al propietario de la propiedad aceptar o rechazar una solicitud.

        Si se acepta, se genera el contrato de arriendo respectivo y se marca la propiedad como arrendada.

        Raises:
            SolicitudNoEncontradaError: Si la solicitud no existe.
            PermisoArriendoError: Si el usuario no es el dueño ni admin.
            EstadoSolicitudInvalidoError: Si ya fue respondida.
        """
        solicitud = SolicitudRepositorio.obtener_por_id(solicitud_id)
        if not solicitud:
            raise SolicitudNoEncontradaError(f"Solicitud con id {solicitud_id} no encontrada.")

        usuario = UsuarioRepositorio.obtener_por_id(usuario_id)
        es_admin = usuario and usuario.rol == "admin"
        if solicitud.propiedad.propietario_id != usuario_id and not es_admin:
            raise PermisoArriendoError("No tienes permisos para responder esta solicitud.")

        if solicitud.estado != "pendiente":
            raise EstadoSolicitudInvalidoError("La solicitud ya fue respondida previamente.")

        nuevo_estado = datos["estado"]
        solicitud.estado = nuevo_estado

        if nuevo_estado == "aceptada":
            fecha_inicio = datos.get("fecha_inicio") or date.today()
            fecha_fin = datos.get("fecha_fin") or (fecha_inicio + timedelta(days=365))
            precio_acordado = datos.get("precio_acordado") or float(
                solicitud.propiedad.precio_mensual
            )

            contrato = ContratoArriendo(
                solicitud_id=solicitud.id,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                precio_acordado=precio_acordado,
                estado="activo",
            )
            ContratoRepositorio.guardar(contrato)

            # Actualiza estado de la propiedad a arrendada
            solicitud.propiedad.estado = "arrendada"
            PropiedadRepositorio.guardar(solicitud.propiedad)

        SolicitudRepositorio.guardar(solicitud)
        return solicitud

    @staticmethod
    def listar_contratos(usuario_id):
        """Lista los contratos de arriendo en los que participa el usuario."""
        return ContratoRepositorio.obtener_por_usuario(usuario_id)
