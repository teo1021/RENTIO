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


class CorreoYaRegistradoError(Exception):
    pass


class CredencialesInvalidasError(Exception):
    pass


class UsuarioNoEncontradoError(Exception):
    pass


class RolNoDisponibleError(Exception):
    """Se lanza cuando se intenta activar un rol que la cuenta no tiene habilitado."""


class UsuarioServicio:
    """Lógica de negocio para el dominio de usuarios."""

    @staticmethod
    def _hash_contrasena(contrasena):
        return hashlib.sha256(contrasena.encode("utf-8")).hexdigest()

    @staticmethod
    def _crear_token(usuario, rol_activo):
        exp_minutos = current_app.config.get("JWT_EXP_MINUTES", 15)
        payload = {
            "usuario_id": usuario.id,
            "correo": usuario.correo,
            "rol": rol_activo,
            "roles": usuario.roles or [usuario.rol],
            "exp": datetime.now(timezone.utc) + timedelta(minutes=exp_minutos),
        }
        return jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")

    @staticmethod
    def registrar(datos):
        existente = UsuarioRepositorio.obtener_por_correo(datos["correo"])
        if existente:
            raise CorreoYaRegistradoError(f"El correo {datos['correo']} ya está registrado.")

        # Todas las cuentas normales pueden buscar y ofrecer inmuebles.
        # 'rol' conserva el contexto inicial elegido durante el registro.
        usuario = Usuario(
            correo=datos["correo"],
            contrasena=UsuarioServicio._hash_contrasena(datos["contrasena"]),
            rol=datos["rol"],
            roles=["arrendatario", "propietario"],
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
        usuario = UsuarioRepositorio.obtener_por_correo(datos["correo"])
        if not usuario:
            raise CredencialesInvalidasError("Correo o contraseña incorrectos.")

        hash_ingresado = UsuarioServicio._hash_contrasena(datos["contrasena"])
        if usuario.contrasena != hash_ingresado:
            raise CredencialesInvalidasError("Correo o contraseña incorrectos.")

        if usuario.rol == "admin":
            # Una cuenta administrativa no hereda permisos de los modos normales.
            if usuario.roles != ["admin"]:
                usuario.roles = ["admin"]
                UsuarioRepositorio.guardar(usuario)
        elif not usuario.roles:
            usuario.roles = ["arrendatario", "propietario"]
            UsuarioRepositorio.guardar(usuario)

        return {
            "token": UsuarioServicio._crear_token(usuario, usuario.rol),
            "usuario": usuario.to_dict(rol_activo=usuario.rol),
        }

    @staticmethod
    def cambiar_contexto(usuario_id, nuevo_rol):
        usuario = UsuarioRepositorio.obtener_por_id(usuario_id)
        if not usuario:
            raise UsuarioNoEncontradoError(f"Usuario con id {usuario_id} no encontrado.")

        roles = usuario.roles or [usuario.rol]
        if nuevo_rol not in roles:
            raise RolNoDisponibleError("Este rol no está habilitado para tu cuenta.")

        return {
            "token": UsuarioServicio._crear_token(usuario, nuevo_rol),
            "usuario": usuario.to_dict(rol_activo=nuevo_rol),
        }

    @staticmethod
    def obtener_perfil(usuario_id):
        usuario = UsuarioRepositorio.obtener_por_id(usuario_id)
        if not usuario:
            raise UsuarioNoEncontradoError(f"Usuario con id {usuario_id} no encontrado.")
        return usuario

    @staticmethod
    def actualizar_perfil(usuario_id, datos):
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
        return UsuarioRepositorio.obtener_todos()

    @staticmethod
    def cambiar_rol(usuario_id, nuevo_rol):
        usuario = UsuarioRepositorio.obtener_por_id(usuario_id)
        if not usuario:
            raise UsuarioNoEncontradoError(f"Usuario con id {usuario_id} no encontrado.")

        usuario.rol = nuevo_rol
        usuario.roles = ["admin"] if nuevo_rol == "admin" else ["arrendatario", "propietario"]
        UsuarioRepositorio.guardar(usuario)
        return usuario
