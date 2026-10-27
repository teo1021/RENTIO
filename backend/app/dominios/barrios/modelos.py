"""
Modelos del dominio de barrios.

Define la tabla `barrios` que agrupa los barrios de Medellín por comuna y zona.
"""

from app import db


class Barrio(db.Model):
    """Modelo que representa un barrio o sector de Medellín."""

    __tablename__ = "barrios"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(100), nullable=False, index=True)
    comuna = db.Column(db.String(100), nullable=False)
    zona = db.Column(db.String(100), nullable=False)

    # ── Relaciones ──────────────────────────────────────────────────────
    propiedades = db.relationship(
        "Propiedad",
        back_populates="barrio",
        lazy="dynamic",
    )

    def to_dict(self):
        """Serializa el barrio a diccionario."""
        return {
            "id": self.id,
            "nombre": self.nombre,
            "comuna": self.comuna,
            "zona": self.zona,
        }

    def __repr__(self):
        return f"<Barrio {self.nombre} ({self.comuna})>"
