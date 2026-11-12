"""
Modelos del dominio de arriendos.

Define las tablas `solicitudes_arriendo` y `contratos_arriendo`
con el flujo completo: solicitud → visita → contrato.
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

    # Datos personales del interesado (recopilados al solicitar)
    cedula_arrendatario = db.Column(db.String(20), nullable=True)
    telefono_arrendatario = db.Column(db.String(20), nullable=True)

    # Visita
    fecha_visita_propuesta = db.Column(db.Date, nullable=True)
    fecha_visita_confirmada = db.Column(db.Date, nullable=True)

    estado = db.Column(
        db.Enum(
            "pendiente",           # legado – no usar en nuevas solicitudes
            "pendiente_visita",    # solicitud enviada, esperando respuesta del propietario
            "visita_programada",   # propietario aceptó la visita
            "contrato_generado",   # se formalizó el contrato
            "aceptada",            # legado
            "rechazada",
            name="estado_solicitud",
        ),
        nullable=False,
        default="pendiente_visita",
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
                        self.arrendatario.perfil.to_dict()
                        if self.arrendatario.perfil
                        else None
                    ),
                }
                if self.arrendatario
                else None
            ),
            "mensaje": self.mensaje,
            "cedula_arrendatario": self.cedula_arrendatario,
            "telefono_arrendatario": self.telefono_arrendatario,
            "fecha_visita_propuesta": (
                self.fecha_visita_propuesta.isoformat()
                if self.fecha_visita_propuesta
                else None
            ),
            "fecha_visita_confirmada": (
                self.fecha_visita_confirmada.isoformat()
                if self.fecha_visita_confirmada
                else None
            ),
            "estado": self.estado,
            "fecha_solicitud": (
                self.fecha_solicitud.isoformat() if self.fecha_solicitud else None
            ),
            "contrato": self.contrato.to_dict() if self.contrato else None,
        }

    def __repr__(self):
        return f"<SolicitudArriendo {self.id} - Propiedad {self.propiedad_id}>"


class ContratoArriendo(db.Model):
    """Modelo que representa un contrato formalizado de arriendo."""

    __tablename__ = "contratos_arriendo"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    numero_contrato = db.Column(db.String(20), nullable=True, unique=True)
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

    # ── Información laboral del arrendatario ────────────────────────────
    trabaja = db.Column(db.Boolean, nullable=True)
    empresa = db.Column(db.String(200), nullable=True)
    cargo = db.Column(db.String(200), nullable=True)
    ingreso_mensual = db.Column(db.Numeric(12, 2), nullable=True)

    # ── Fiador (opcional) ────────────────────────────────────────────────
    fiador_nombre = db.Column(db.String(200), nullable=True)
    fiador_cedula = db.Column(db.String(20), nullable=True)
    fiador_telefono = db.Column(db.String(20), nullable=True)

    # ── Cláusulas adicionales ────────────────────────────────────────────
    clausulas_adicionales = db.Column(db.Text, nullable=True)

    # ── Relaciones ──────────────────────────────────────────────────────
    solicitud = db.relationship("SolicitudArriendo", back_populates="contrato")

    def to_dict(self):
        """Serializa el contrato a diccionario."""
        return {
            "id": self.id,
            "numero_contrato": self.numero_contrato,
            "solicitud_id": self.solicitud_id,
            "fecha_inicio": (
                self.fecha_inicio.isoformat() if self.fecha_inicio else None
            ),
            "fecha_fin": (
                self.fecha_fin.isoformat() if self.fecha_fin else None
            ),
            "precio_acordado": (
                float(self.precio_acordado) if self.precio_acordado else None
            ),
            "estado": self.estado,
            "fecha_creacion": (
                self.fecha_creacion.isoformat() if self.fecha_creacion else None
            ),
            "trabaja": self.trabaja,
            "empresa": self.empresa,
            "cargo": self.cargo,
            "ingreso_mensual": (
                float(self.ingreso_mensual) if self.ingreso_mensual else None
            ),
            "fiador_nombre": self.fiador_nombre,
            "fiador_cedula": self.fiador_cedula,
            "fiador_telefono": self.fiador_telefono,
            "clausulas_adicionales": self.clausulas_adicionales,
        }

    def __repr__(self):
        return f"<ContratoArriendo {self.numero_contrato or self.id} - Solicitud {self.solicitud_id}>"
