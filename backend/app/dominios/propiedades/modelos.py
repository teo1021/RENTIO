"""
Modelos del dominio de propiedades.

Define las tablas `propiedades` e `imagenes_propiedad`, junto con la
tabla intermedia `propiedad_caracteristica` para la relación N:M.
"""

from datetime import datetime, timezone

from app import db

# ── Tabla intermedia N:M ────────────────────────────────────────────────
propiedad_caracteristica = db.Table(
    "propiedad_caracteristica",
    db.Column(
        "propiedad_id",
        db.Integer,
        db.ForeignKey("propiedades.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    db.Column(
        "caracteristica_id",
        db.Integer,
        db.ForeignKey("caracteristicas.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Propiedad(db.Model):
    """Modelo que representa un inmueble disponible para arriendo."""

    __tablename__ = "propiedades"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    titulo = db.Column(db.String(255), nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    precio_mensual = db.Column(db.Numeric(10, 2), nullable=False)
    direccion = db.Column(db.String(500), nullable=False)
    estrato = db.Column(db.Integer, nullable=False)
    area_m2 = db.Column(db.Numeric(10, 2), nullable=True)
    habitaciones = db.Column(db.Integer, nullable=False, default=1)
    banos = db.Column(db.Integer, nullable=False, default=1)
    tipo = db.Column(
        db.Enum("casa", "apartamento", "habitacion", "finca", name="tipo_propiedad"),
        nullable=False,
        default="apartamento",
    )
    estado = db.Column(
        db.Enum("disponible", "arrendada", "inactiva", name="estado_propiedad"),
        nullable=False,
        default="disponible",
    )
    fecha_creacion = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # ── Foreign Keys ────────────────────────────────────────────────────
    barrio_id = db.Column(
        db.Integer,
        db.ForeignKey("barrios.id"),
        nullable=True,
    )
    propietario_id = db.Column(
        db.Integer,
        db.ForeignKey("usuarios.id"),
        nullable=False,
    )

    # ── Relaciones ──────────────────────────────────────────────────────
    propietario = db.relationship("Usuario", back_populates="propiedades")
    barrio = db.relationship("Barrio", back_populates="propiedades")
    imagenes = db.relationship(
        "ImagenPropiedad",
        back_populates="propiedad",
        cascade="all, delete-orphan",
        order_by="ImagenPropiedad.orden",
    )
    caracteristicas = db.relationship(
        "Caracteristica",
        secondary=propiedad_caracteristica,
        back_populates="propiedades",
        lazy="joined",
    )
    solicitudes = db.relationship(
        "SolicitudArriendo",
        back_populates="propiedad",
        lazy="dynamic",
    )

    def to_dict(self):
        """Serializa la propiedad a diccionario."""
        return {
            "id": self.id,
            "titulo": self.titulo,
            "descripcion": self.descripcion,
            "precio_mensual": float(self.precio_mensual) if self.precio_mensual else None,
            "direccion": self.direccion,
            "estrato": self.estrato,
            "area_m2": float(self.area_m2) if self.area_m2 else None,
            "habitaciones": self.habitaciones,
            "banos": self.banos,
            "tipo": self.tipo,
            "estado": self.estado,
            "barrio_id": self.barrio_id,
            "barrio": self.barrio.to_dict() if self.barrio else None,
            "propietario_id": self.propietario_id,
            "caracteristicas": [c.to_dict() for c in self.caracteristicas],
            "imagenes": [img.to_dict() for img in self.imagenes],
            "fecha_creacion": self.fecha_creacion.isoformat() if self.fecha_creacion else None,
        }

    def __repr__(self):
        return f"<Propiedad {self.titulo}>"


class ImagenPropiedad(db.Model):
    """Modelo que almacena las imágenes de una propiedad."""

    __tablename__ = "imagenes_propiedad"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    url = db.Column(db.String(500), nullable=False)
    orden = db.Column(db.Integer, nullable=False, default=0)
    propiedad_id = db.Column(
        db.Integer,
        db.ForeignKey("propiedades.id", ondelete="CASCADE"),
        nullable=False,
    )

    # ── Relaciones ──────────────────────────────────────────────────────
    propiedad = db.relationship("Propiedad", back_populates="imagenes")

    def to_dict(self):
        """Serializa la imagen a diccionario."""
        return {
            "id": self.id,
            "url": self.url,
            "orden": self.orden,
        }

    def __repr__(self):
        return f"<ImagenPropiedad {self.url}>"
