"""
Modelos del dominio de características.

Define la tabla `caracteristicas` (amenities como WiFi, parqueadero, piscina, etc.).
"""

from app import db


class Caracteristica(db.Model):
    """Modelo que representa una característica o amenidad de una propiedad."""

    __tablename__ = "caracteristicas"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(100), unique=True, nullable=False, index=True)
    icono = db.Column(db.String(100), nullable=True)

    # ── Relaciones ──────────────────────────────────────────────────────
    propiedades = db.relationship(
        "Propiedad",
        secondary="propiedad_caracteristica",
        back_populates="caracteristicas",
        lazy="dynamic",
    )

    def to_dict(self):
        """Serializa la característica a diccionario."""
        return {
            "id": self.id,
            "nombre": self.nombre,
            "icono": self.icono,
        }

    def __repr__(self):
        return f"<Caracteristica {self.nombre}>"
