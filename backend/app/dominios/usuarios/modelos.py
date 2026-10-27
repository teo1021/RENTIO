"""
Modelos del dominio de usuarios.

Define las tablas `usuarios` y `perfiles_usuario` con su relación 1:1.
"""

from datetime import datetime, timezone

from app import db


class Usuario(db.Model):
    """Modelo que representa a un usuario registrado en la plataforma."""

    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    correo = db.Column(db.String(255), unique=True, nullable=False, index=True)
    contrasena = db.Column(db.String(255), nullable=False)
    rol = db.Column(
        db.Enum("arrendatario", "propietario", "admin", name="rol_usuario"),
        nullable=False,
        default="arrendatario",
    )
    fecha_creacion = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # ── Relaciones ──────────────────────────────────────────────────────
    perfil = db.relationship(
        "PerfilUsuario",
        back_populates="usuario",
        uselist=False,
        cascade="all, delete-orphan",
    )
    propiedades = db.relationship(
        "Propiedad",
        back_populates="propietario",
        lazy="dynamic",
    )
    solicitudes = db.relationship(
        "SolicitudArriendo",
        back_populates="arrendatario",
        lazy="dynamic",
    )

    def to_dict(self):
        """Serializa el usuario a diccionario (sin contraseña)."""
        resultado = {
            "id": self.id,
            "correo": self.correo,
            "rol": self.rol,
            "fecha_creacion": self.fecha_creacion.isoformat() if self.fecha_creacion else None,
        }
        if self.perfil:
            resultado["perfil"] = self.perfil.to_dict()
        return resultado

    def __repr__(self):
        return f"<Usuario {self.correo}>"


class PerfilUsuario(db.Model):
    """Modelo que almacena el perfil extendido de un usuario."""

    __tablename__ = "perfiles_usuario"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(100), nullable=True)
    apellido = db.Column(db.String(100), nullable=True)
    telefono = db.Column(db.String(20), nullable=True)
    cedula = db.Column(db.String(20), nullable=True)
    foto_perfil = db.Column(db.String(500), nullable=True)
    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey("usuarios.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    # ── Relaciones ──────────────────────────────────────────────────────
    usuario = db.relationship("Usuario", back_populates="perfil")

    def to_dict(self):
        """Serializa el perfil a diccionario."""
        return {
            "id": self.id,
            "nombre": self.nombre,
            "apellido": self.apellido,
            "telefono": self.telefono,
            "cedula": self.cedula,
            "foto_perfil": self.foto_perfil,
        }

    def __repr__(self):
        return f"<PerfilUsuario {self.nombre} {self.apellido}>"
