"""
Servicios del dominio de arriendos.

Lógica de negocio para el flujo completo:
  solicitud con datos personales → visita → contrato con info completa.
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
    """Se lanza cuando ya existe una solicitud activa para la misma propiedad."""
    pass


class EstadoSolicitudInvalidoError(Exception):
    """Se lanza cuando se realiza una acción sobre una solicitud en estado incompatible."""
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
        Crea una nueva solicitud de arriendo con datos personales y fecha de visita propuesta.

        Args:
            datos: Diccionario validado por SolicitarArriendoDTO.
            arrendatario_id: ID del usuario solicitante.

        Raises:
            PropiedadNoEncontradaError: Si la propiedad no existe.
            PermisoArriendoError: Si intenta solicitar su propia propiedad.
            EstadoSolicitudInvalidoError: Si la propiedad no está disponible.
            SolicitudDuplicadaError: Si ya tiene solicitud activa.
        """
        propiedad_id = datos["propiedad_id"]
        propiedad = PropiedadRepositorio.obtener_por_id(propiedad_id)
        if not propiedad:
            raise PropiedadNoEncontradaError(
                f"Propiedad con id {propiedad_id} no encontrada."
            )

        if propiedad.propietario_id == arrendatario_id:
            raise PermisoArriendoError(
                "No puedes solicitar arriendo para tu propia propiedad."
            )

        if propiedad.estado != "disponible":
            raise EstadoSolicitudInvalidoError(
                f"La propiedad no está disponible (estado actual: {propiedad.estado})."
            )

        activa = SolicitudRepositorio.obtener_activa(propiedad_id, arrendatario_id)
        if activa:
            raise SolicitudDuplicadaError(
                "Ya tienes una solicitud activa para esta propiedad."
            )

        solicitud = SolicitudArriendo(
            propiedad_id=propiedad_id,
            arrendatario_id=arrendatario_id,
            mensaje=datos.get("mensaje"),
            cedula_arrendatario=datos.get("cedula_arrendatario"),
            telefono_arrendatario=datos.get("telefono_arrendatario"),
            fecha_visita_propuesta=datos.get("fecha_visita_propuesta"),
            estado="pendiente_visita",
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
    def responder_visita(solicitud_id, datos, usuario_id):
        """
        Permite al propietario aceptar o rechazar la solicitud de visita.

        Si se acepta, el estado pasa a 'visita_programada'.
        Si se rechaza, el estado pasa a 'rechazada'.

        Raises:
            SolicitudNoEncontradaError: Si la solicitud no existe.
            PermisoArriendoError: Si el usuario no es el dueño ni admin.
            EstadoSolicitudInvalidoError: Si la solicitud no está en estado pendiente_visita.
        """
        solicitud = SolicitudRepositorio.obtener_por_id(solicitud_id)
        if not solicitud:
            raise SolicitudNoEncontradaError(
                f"Solicitud con id {solicitud_id} no encontrada."
            )

        usuario = UsuarioRepositorio.obtener_por_id(usuario_id)
        es_admin = usuario and usuario.rol == "admin"
        if solicitud.propiedad.propietario_id != usuario_id and not es_admin:
            raise PermisoArriendoError(
                "No tienes permisos para responder esta solicitud."
            )

        estados_validos = {"pendiente", "pendiente_visita"}
        if solicitud.estado not in estados_validos:
            raise EstadoSolicitudInvalidoError(
                f"La solicitud está en estado '{solicitud.estado}' y no puede responderse ahora."
            )

        nuevo_estado = datos["estado"]
        solicitud.estado = nuevo_estado

        if nuevo_estado == "visita_programada":
            solicitud.fecha_visita_confirmada = (
                datos.get("fecha_visita_confirmada")
                or solicitud.fecha_visita_propuesta
            )

        SolicitudRepositorio.guardar(solicitud)
        return solicitud

    @staticmethod
    def generar_contrato(solicitud_id, datos, usuario_id):
        """
        Formaliza el contrato de arriendo después de la visita.

        Solo el propietario puede ejecutar esta acción y la solicitud debe
        estar en estado 'visita_programada'.

        Args:
            solicitud_id: ID de la solicitud.
            datos: Diccionario validado por GenerarContratoDTO.
            usuario_id: ID del propietario autenticado.

        Raises:
            SolicitudNoEncontradaError
            PermisoArriendoError
            EstadoSolicitudInvalidoError
        """
        solicitud = SolicitudRepositorio.obtener_por_id(solicitud_id)
        if not solicitud:
            raise SolicitudNoEncontradaError(
                f"Solicitud con id {solicitud_id} no encontrada."
            )

        usuario = UsuarioRepositorio.obtener_por_id(usuario_id)
        es_admin = usuario and usuario.rol == "admin"
        if solicitud.propiedad.propietario_id != usuario_id and not es_admin:
            raise PermisoArriendoError(
                "No tienes permisos para generar el contrato de esta solicitud."
            )

        estados_validos = {"visita_programada", "aceptada"}
        if solicitud.estado not in estados_validos:
            raise EstadoSolicitudInvalidoError(
                f"El contrato solo puede generarse cuando la solicitud está en estado "
                f"'visita_programada' (estado actual: '{solicitud.estado}')."
            )

        if solicitud.contrato:
            raise EstadoSolicitudInvalidoError(
                "Esta solicitud ya tiene un contrato generado."
            )

        fecha_inicio = datos.get("fecha_inicio") or date.today()
        fecha_fin = datos.get("fecha_fin") or (fecha_inicio + timedelta(days=365))
        precio_acordado = datos.get("precio_acordado") or float(
            solicitud.propiedad.precio_mensual
        )

        numero_contrato = ContratoRepositorio.siguiente_numero()

        contrato = ContratoArriendo(
            numero_contrato=numero_contrato,
            solicitud_id=solicitud.id,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            precio_acordado=precio_acordado,
            estado="activo",
            trabaja=datos.get("trabaja"),
            empresa=datos.get("empresa"),
            cargo=datos.get("cargo"),
            ingreso_mensual=datos.get("ingreso_mensual"),
            fiador_nombre=datos.get("fiador_nombre"),
            fiador_cedula=datos.get("fiador_cedula"),
            fiador_telefono=datos.get("fiador_telefono"),
            clausulas_adicionales=datos.get("clausulas_adicionales"),
        )
        ContratoRepositorio.guardar(contrato)

        solicitud.estado = "contrato_generado"
        solicitud.propiedad.estado = "arrendada"
        PropiedadRepositorio.guardar(solicitud.propiedad)
        SolicitudRepositorio.guardar(solicitud)

        return solicitud

    @staticmethod
    def responder_solicitud(solicitud_id, datos, usuario_id):
        """
        Legado: acepta o rechaza una solicitud y, si acepta, genera el contrato al mismo tiempo.
        Se mantiene por retrocompatibilidad. Usar responder_visita + generar_contrato en su lugar.
        """
        solicitud = SolicitudRepositorio.obtener_por_id(solicitud_id)
        if not solicitud:
            raise SolicitudNoEncontradaError(
                f"Solicitud con id {solicitud_id} no encontrada."
            )

        usuario = UsuarioRepositorio.obtener_por_id(usuario_id)
        es_admin = usuario and usuario.rol == "admin"
        if solicitud.propiedad.propietario_id != usuario_id and not es_admin:
            raise PermisoArriendoError(
                "No tienes permisos para responder esta solicitud."
            )

        estados_respondibles = {"pendiente", "pendiente_visita", "visita_programada"}
        if solicitud.estado not in estados_respondibles:
            raise EstadoSolicitudInvalidoError(
                "La solicitud ya fue respondida previamente."
            )

        nuevo_estado = datos["estado"]

        if nuevo_estado == "aceptada":
            fecha_inicio = datos.get("fecha_inicio") or date.today()
            fecha_fin = datos.get("fecha_fin") or (fecha_inicio + timedelta(days=365))
            precio_acordado = datos.get("precio_acordado") or float(
                solicitud.propiedad.precio_mensual
            )

            numero_contrato = ContratoRepositorio.siguiente_numero()
            contrato = ContratoArriendo(
                numero_contrato=numero_contrato,
                solicitud_id=solicitud.id,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                precio_acordado=precio_acordado,
                estado="activo",
            )
            ContratoRepositorio.guardar(contrato)

            solicitud.estado = "contrato_generado"
            solicitud.propiedad.estado = "arrendada"
            PropiedadRepositorio.guardar(solicitud.propiedad)
        else:
            solicitud.estado = "rechazada"

        SolicitudRepositorio.guardar(solicitud)
        return solicitud

    @staticmethod
    def listar_contratos(usuario_id):
        """Lista los contratos de arriendo en los que participa el usuario."""
        return ContratoRepositorio.obtener_por_usuario(usuario_id)
