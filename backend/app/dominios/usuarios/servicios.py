"""
Servicios del dominio de usuarios.

Contiene la lógica de negocio: registro, autenticación, gestión de perfiles.
Define excepciones de dominio propias.
"""

import hashlib
from datetime import datetime, timedelta, timezone

import jwt
from flask import current_app

from app.dominios.usuarios.modelos import PerfilUsuario, Usuario
from app.dominios.usuarios.repositorios import PerfilRepositorio, UsuarioRepositorio

# ═══════════════════════════════════════════════════════════════════════════════
# Excepciones de dominio
# ═══════════════════════════════════════════════════════════════════════════════


class CorreoYaRegistradoError(Exception):
    """Se lanza cuando se intenta registrar un correo que ya existe."""

    pass


class CredencialesInvalidasError(Exception):
    """Se lanza cuando las credenciales de login son incorrectas."""

    pass


class UsuarioNoEncontradoError(Exception):
    """Se lanza cuando no se encuentra un usuario por ID."""

    pass


# ═══════════════════════════════════════════════════════════════════════════════
# Servicio
# ═══════════════════════════════════════════════════════════════════════════════


class UsuarioServicio:
    """Lógica de negocio para el dominio de usuarios."""

    @staticmethod
    def _hash_contrasena(contrasena):
        """Genera un hash SHA-256 de la contraseña."""
        return hashlib.sha256(contrasena.encode("utf-8")).hexdigest()

    @staticmethod
    def registrar(datos):
        """
        Registra un nuevo usuario con su perfil.

        Args:
            datos: Diccionario validado por RegistroDTO.

        Returns:
            Usuario: El usuario creado.

        Raises:
            CorreoYaRegistradoError: Si el correo ya está registrado.
        """
        existente = UsuarioRepositorio.obtener_por_correo(datos["correo"])
        if existente:
            raise CorreoYaRegistradoError(f"El correo {datos['correo']} ya está registrado.")

        usuario = Usuario(
            correo=datos["correo"],
            contrasena=UsuarioServicio._hash_contrasena(datos["contrasena"]),
            rol=datos["rol"],
        )

        UsuarioRepositorio.guardar(usuario)

        perfil = PerfilUsuario(
            usuario_id=usuario.id,
            nombre=datos.get("nombre"),
            apellido=datos.get("apellido"),
        )
        PerfilRepositorio.guardar(perfil)

        return usuario

    @staticmethod
    def login(datos):
        """
        Autentica un usuario y genera un token JWT.

        Args:
            datos: Diccionario validado por LoginDTO.

        Returns:
            dict: Contiene 'token' y 'usuario'.

        Raises:
            CredencialesInvalidasError: Si correo o contraseña son incorrectos.
        """
        usuario = UsuarioRepositorio.obtener_por_correo(datos["correo"])
        if not usuario:
            raise CredencialesInvalidasError("Correo o contraseña incorrectos.")

        hash_ingresado = UsuarioServicio._hash_contrasena(datos["contrasena"])
        if usuario.contrasena != hash_ingresado:
            raise CredencialesInvalidasError("Correo o contraseña incorrectos.")

        exp_minutos = current_app.config.get("JWT_EXP_MINUTES", 15)
        payload = {
            "usuario_id": usuario.id,
            "correo": usuario.correo,
            "rol": usuario.rol,
            "exp": datetime.now(timezone.utc) + timedelta(minutes=exp_minutos),
        }
        token = jwt.encode(
            payload,
            current_app.config["SECRET_KEY"],
            algorithm="HS256",
        )

        return {"token": token, "usuario": usuario.to_dict()}

    @staticmethod
    def obtener_perfil(usuario_id):
        """
        Obtiene el perfil completo de un usuario.

        Args:
            usuario_id: ID del usuario.

        Returns:
            Usuario: El usuario con su perfil.

        Raises:
            UsuarioNoEncontradoError: Si no existe el usuario.
        """
        usuario = UsuarioRepositorio.obtener_por_id(usuario_id)
        if not usuario:
            raise UsuarioNoEncontradoError(f"Usuario con id {usuario_id} no encontrado.")
        return usuario

    @staticmethod
    def actualizar_perfil(usuario_id, datos):
        """
        Actualiza parcialmente el perfil de un usuario.

        Args:
            usuario_id: ID del usuario.
            datos: Diccionario validado por ActualizarPerfilDTO.

        Returns:
            Usuario: El usuario actualizado.

        Raises:
            UsuarioNoEncontradoError: Si no existe el usuario.
        """
        usuario = UsuarioRepositorio.obtener_por_id(usuario_id)
        if not usuario:
            raise UsuarioNoEncontradoError(f"Usuario con id {usuario_id} no encontrado.")

        perfil = PerfilRepositorio.obtener_por_usuario_id(usuario_id)
        if not perfil:
            perfil = PerfilUsuario(usuario_id=usuario_id)

        campos_actualizables = ["nombre", "apellido", "telefono", "cedula", "foto_perfil"]
        for campo in campos_actualizables:
            valor = datos.get(campo)
            if valor is not None:
                setattr(perfil, campo, valor)

        PerfilRepositorio.guardar(perfil)
        return usuario

    @staticmethod
    def listar_usuarios():
        """Retorna todos los usuarios (uso administrativo)."""
        return UsuarioRepositorio.obtener_todos()

    @staticmethod
    def cambiar_rol(usuario_id, nuevo_rol):
        """
        Cambia el rol de un usuario (operación administrativa).

        Args:
            usuario_id: ID del usuario a modificar.
            nuevo_rol: Nuevo rol a asignar.

        Returns:
            Usuario: El usuario con el rol actualizado.

        Raises:
            UsuarioNoEncontradoError: Si no existe el usuario.
        """
        usuario = UsuarioRepositorio.obtener_por_id(usuario_id)
        if not usuario:
            raise UsuarioNoEncontradoError(f"Usuario con id {usuario_id} no encontrado.")

        usuario.rol = nuevo_rol
        UsuarioRepositorio.guardar(usuario)
        return usuario
