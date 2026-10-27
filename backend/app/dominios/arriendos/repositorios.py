"""
Repositorio del dominio de arriendos.

Capa de acceso a datos para solicitudes y contratos de arriendo.
"""

from app import db
from app.dominios.arriendos.modelos import ContratoArriendo, SolicitudArriendo
from app.dominios.propiedades.modelos import Propiedad


class SolicitudRepositorio:
    """Métodos de acceso a datos para solicitudes de arriendo."""

    @staticmethod
    def guardar(solicitud):
        """Persiste una solicitud de arriendo."""
        db.session.add(solicitud)
        db.session.commit()
        return solicitud

    @staticmethod
    def obtener_por_id(solicitud_id):
        """Obtiene una solicitud por su ID."""
        return db.session.get(SolicitudArriendo, solicitud_id)

    @staticmethod
    def obtener_por_arrendatario(arrendatario_id):
        """Obtiene todas las solicitudes realizadas por un arrendatario."""
        return (
            SolicitudArriendo.query.filter_by(arrendatario_id=arrendatario_id)
            .order_by(SolicitudArriendo.fecha_solicitud.desc())
            .all()
        )

    @staticmethod
    def obtener_por_propietario(propietario_id):
        """Obtiene todas las solicitudes recibidas para propiedades de un propietario."""
        return (
            SolicitudArriendo.query.join(Propiedad)
            .filter(Propiedad.propietario_id == propietario_id)
            .order_by(SolicitudArriendo.fecha_solicitud.desc())
            .all()
        )

    @staticmethod
    def obtener_pendiente(propiedad_id, arrendatario_id):
        """Verifica si ya existe una solicitud pendiente del arrendatario para la propiedad."""
        return SolicitudArriendo.query.filter_by(
            propiedad_id=propiedad_id,
            arrendatario_id=arrendatario_id,
            estado="pendiente",
        ).first()


class ContratoRepositorio:
    """Métodos de acceso a datos para contratos de arriendo."""

    @staticmethod
    def guardar(contrato):
        """Persiste un contrato de arriendo."""
        db.session.add(contrato)
        db.session.commit()
        return contrato

    @staticmethod
    def obtener_por_id(contrato_id):
        """Obtiene un contrato por su ID."""
        return db.session.get(ContratoArriendo, contrato_id)

    @staticmethod
    def obtener_por_usuario(usuario_id):
        """Obtiene todos los contratos donde el usuario participa como arrendatario o propietario."""
        return (
            ContratoArriendo.query.join(SolicitudArriendo)
            .join(Propiedad, SolicitudArriendo.propiedad_id == Propiedad.id)
            .filter(
                (SolicitudArriendo.arrendatario_id == usuario_id)
                | (Propiedad.propietario_id == usuario_id)
            )
            .order_by(ContratoArriendo.fecha_creacion.desc())
            .all()
        )
