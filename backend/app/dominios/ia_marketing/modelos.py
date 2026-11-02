"""Modelos persistentes del chat de marketing inmobiliario."""

from datetime import datetime, timezone

from app import db


class ConversacionMarketing(db.Model):
    __tablename__ = "conversaciones"
    __table_args__ = (
        db.CheckConstraint(
            "estado IN ('recopilando','lista','generada','cerrada')",
            name="ck_ia_conversacion_estado",
        ),
        {"schema": "ia_marketing"},
    )

    id = db.Column(db.Integer, primary_key=True)
    propietario_id = db.Column(
        db.Integer, db.ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    propiedad_id = db.Column(
        db.Integer, db.ForeignKey("propiedades.id", ondelete="SET NULL"), nullable=True, index=True
    )
    estado = db.Column(db.String(20), nullable=False, default="recopilando")
    datos_recopilados = db.Column(db.JSON, nullable=False, default=dict)
    fecha_creacion = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    fecha_actualizacion = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    mensajes = db.relationship("MensajeMarketing", back_populates="conversacion", cascade="all, delete-orphan", order_by="MensajeMarketing.fecha_creacion")
    resultados = db.relationship("ResultadoMarketing", back_populates="conversacion", cascade="all, delete-orphan", order_by="ResultadoMarketing.fecha_creacion")


class MensajeMarketing(db.Model):
    __tablename__ = "mensajes"
    __table_args__ = (
        db.CheckConstraint("rol IN ('usuario','asistente')", name="ck_ia_mensaje_rol"),
        {"schema": "ia_marketing"},
    )

    id = db.Column(db.Integer, primary_key=True)
    conversacion_id = db.Column(db.Integer, db.ForeignKey("ia_marketing.conversaciones.id", ondelete="CASCADE"), nullable=False, index=True)
    rol = db.Column(db.String(20), nullable=False)
    contenido = db.Column(db.Text, nullable=False)
    datos_extraidos = db.Column(db.JSON, nullable=False, default=dict)
    fecha_creacion = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    conversacion = db.relationship("ConversacionMarketing", back_populates="mensajes")


class ResultadoMarketing(db.Model):
    __tablename__ = "resultados_generados"
    __table_args__ = (
        db.CheckConstraint(
            "precio_minimo IS NULL OR precio_maximo IS NULL OR precio_minimo <= precio_maximo",
            name="ck_ia_rango_precio",
        ),
        {"schema": "ia_marketing"},
    )

    id = db.Column(db.Integer, primary_key=True)
    conversacion_id = db.Column(db.Integer, db.ForeignKey("ia_marketing.conversaciones.id", ondelete="CASCADE"), nullable=False, index=True)
    propiedad_id = db.Column(db.Integer, db.ForeignKey("propiedades.id", ondelete="SET NULL"), nullable=True, index=True)
    descripcion = db.Column(db.Text, nullable=False)
    precio_sugerido = db.Column(db.Numeric(12, 2), nullable=True)
    precio_minimo = db.Column(db.Numeric(12, 2), nullable=True)
    precio_maximo = db.Column(db.Numeric(12, 2), nullable=True)
    moneda = db.Column(db.String(3), nullable=False, default="COP")
    datos_usados = db.Column(db.JSON, nullable=False, default=dict)
    fuente_datos = db.Column(db.String(100), nullable=True)
    version_datos = db.Column(db.String(100), nullable=True)
    metadatos_calculo = db.Column(db.JSON, nullable=False, default=dict)
    fecha_creacion = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    conversacion = db.relationship("ConversacionMarketing", back_populates="resultados")
