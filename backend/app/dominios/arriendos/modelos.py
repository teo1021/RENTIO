"""
Modelos del dominio de arriendos.

Define las tablas `solicitudes_arriendo` y `contratos_arriendo`.
"""

from datetime import datetime, timezone

from app import db


class SolicitudArriendo(db.Model):
    """Modelo que representa una solicitud de arriendo enviada por un arrendatario."""

    __tablename__ = "solicitudes_arriendo"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    propiedad_id = db.Column(
        db.Integer,
        db.ForeignKey("propiedades.id", ondelete="CASCADE"),
        nullable=False,
    )
    arrendatario_id = db.Column(
        db.Integer,
        db.ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
    )
    mensaje = db.Column(db.Text, nullable=True)
    estado = db.Column(
        db.Enum("pendiente", "aceptada", "rechazada", name="estado_solicitud"),
        nullable=False,
        default="pendiente",
    )
    fecha_solicitud = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # ── Relaciones ──────────────────────────────────────────────────────
    propiedad = db.relationship("Propiedad", back_populates="solicitudes")
    arrendatario = db.relationship("Usuario", back_populates="solicitudes")
    contrato = db.relationship(
        "ContratoArriendo",
        back_populates="solicitud",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def to_dict(self):
        """Serializa la solicitud de arriendo a diccionario."""
        return {
            "id": self.id,
            "propiedad_id": self.propiedad_id,
            "propiedad": (
                {
                    "id": self.propiedad.id,
                    "titulo": self.propiedad.titulo,
                    "precio_mensual": (
                        float(self.propiedad.precio_mensual)
                        if self.propiedad.precio_mensual
                        else None
                    ),
                    "direccion": self.propiedad.direccion,
                }
                if self.propiedad
                else None
            ),
            "arrendatario_id": self.arrendatario_id,
            "arrendatario": (
                {
                    "id": self.arrendatario.id,
                    "correo": self.arrendatario.correo,
                    "perfil": (
                        self.arrendatario.perfil.to_dict() if self.arrendatario.perfil else None
                    ),
                }
                if self.arrendatario
                else None
            ),
            "mensaje": self.mensaje,
            "estado": self.estado,
            "fecha_solicitud": self.fecha_solicitud.isoformat() if self.fecha_solicitud else None,
            "contrato": self.contrato.to_dict() if self.contrato else None,
        }

    def __repr__(self):
        return f"<SolicitudArriendo {self.id} - Propiedad {self.propiedad_id}>"


class ContratoArriendo(db.Model):
    """Modelo que representa un contrato formalizado de arriendo."""

    __tablename__ = "contratos_arriendo"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    solicitud_id = db.Column(
        db.Integer,
        db.ForeignKey("solicitudes_arriendo.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    fecha_inicio = db.Column(db.Date, nullable=False)
    fecha_fin = db.Column(db.Date, nullable=False)
    precio_acordado = db.Column(db.Numeric(10, 2), nullable=False)
    estado = db.Column(
        db.Enum("activo", "finalizado", "cancelado", name="estado_contrato"),
        nullable=False,
        default="activo",
    )
    fecha_creacion = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # ── Relaciones ──────────────────────────────────────────────────────
    solicitud = db.relationship("SolicitudArriendo", back_populates="contrato")

    def to_dict(self):
        """Serializa el contrato a diccionario."""
        return {
            "id": self.id,
            "solicitud_id": self.solicitud_id,
            "fecha_inicio": self.fecha_inicio.isoformat() if self.fecha_inicio else None,
            "fecha_fin": self.fecha_fin.isoformat() if self.fecha_fin else None,
            "precio_acordado": float(self.precio_acordado) if self.precio_acordado else None,
            "estado": self.estado,
            "fecha_creacion": self.fecha_creacion.isoformat() if self.fecha_creacion else None,
        }

    def __repr__(self):
        return f"<ContratoArriendo {self.id} - Solicitud {self.solicitud_id}>"
