"""
Repositorio del dominio de usuarios.

Capa de acceso a datos — solo queries y operaciones de persistencia.
"""

from app import db
from app.dominios.usuarios.modelos import PerfilUsuario, Usuario


class UsuarioRepositorio:
    """Métodos de acceso a datos para la tabla de usuarios."""

    @staticmethod
    def guardar(usuario):
        """Persiste un usuario (nuevo o existente) en la base de datos."""
        db.session.add(usuario)
        db.session.commit()
        return usuario

    @staticmethod
    def obtener_por_id(usuario_id):
        """Obtiene un usuario por su ID."""
        return db.session.get(Usuario, usuario_id)

    @staticmethod
    def obtener_por_correo(correo):
        """Obtiene un usuario por su correo electrónico."""
        return Usuario.query.filter_by(correo=correo).first()

    @staticmethod
    def obtener_todos():
        """Retorna todos los usuarios registrados."""
        return Usuario.query.all()

    @staticmethod
    def eliminar(usuario):
        """Elimina un usuario de la base de datos."""
        db.session.delete(usuario)
        db.session.commit()


class PerfilRepositorio:
    """Métodos de acceso a datos para la tabla de perfiles."""

    @staticmethod
    def guardar(perfil):
        """Persiste un perfil (nuevo o existente) en la base de datos."""
        db.session.add(perfil)
        db.session.commit()
        return perfil

    @staticmethod
    def obtener_por_usuario_id(usuario_id):
        """Obtiene el perfil asociado a un usuario."""
        return PerfilUsuario.query.filter_by(usuario_id=usuario_id).first()
