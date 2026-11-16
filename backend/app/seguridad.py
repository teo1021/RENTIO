"""
Módulo de seguridad — Decoradores de autenticación y autorización.

Provee decoradores reutilizables para proteger endpoints:
- requiere_token: valida JWT e inyecta usuario_id
- requiere_admin: valida JWT + rol admin
- requiere_propietario: valida JWT + rol propietario
"""

import functools

import jwt
from flask import current_app, jsonify, request

from app.dominios.usuarios.repositorios import UsuarioRepositorio


def _usuario_autenticado():
    payload, error = _extraer_y_validar_token()
    if error:
        return None, error

    usuario_id = payload.get("usuario_id")
    if not isinstance(usuario_id, int) or isinstance(usuario_id, bool):
        return None, (
            jsonify({"success": False, "error": {"message": "Token inválido."}}),
            401,
        )

    usuario = UsuarioRepositorio.obtener_por_id(usuario_id)
    if not usuario:
        return None, (
            jsonify(
                {
                    "success": False,
                    "error": {"message": "La cuenta asociada al token ya no existe."},
                }
            ),
            401,
        )
    return usuario, None


def _extraer_y_validar_token():
    """
    Extrae y valida el token JWT del header Authorization.

    Returns:
        dict: Payload decodificado del token.

    Raises:
        tuple: (response JSON, código HTTP) en caso de error.
    """
    header = request.headers.get("Authorization", "")

    if not header:
        return None, (
            jsonify(
                {
                    "success": False,
                    "error": {"message": "Token de autenticación requerido."},
                }
            ),
            401,
        )

    partes = header.split(" ")
    if len(partes) != 2 or partes[0] != "Bearer":
        return None, (
            jsonify(
                {
                    "success": False,
                    "error": {"message": "Formato de token inválido. Use: Bearer <token>"},
                }
            ),
            401,
        )

    token = partes[1]

    try:
        payload = jwt.decode(
            token,
            current_app.config["SECRET_KEY"],
            algorithms=["HS256"],
        )
        return payload, None
    except jwt.ExpiredSignatureError:
        return None, (
            jsonify(
                {
                    "success": False,
                    "error": {"message": "El token ha expirado."},
                }
            ),
            401,
        )
    except jwt.InvalidTokenError:
        return None, (
            jsonify(
                {
                    "success": False,
                    "error": {"message": "Token inválido."},
                }
            ),
            401,
        )


def requiere_token(f):
    """Decorador que valida JWT e inyecta usuario_id como kwarg."""

    @functools.wraps(f)
    def decorador(*args, **kwargs):
        usuario, error = _usuario_autenticado()
        if error:
            return error
        kwargs["usuario_id"] = usuario.id
        return f(*args, **kwargs)

    return decorador


def requiere_admin(f):
    """Decorador que valida JWT y verifica que el usuario tenga rol 'admin'."""

    @functools.wraps(f)
    def decorador(*args, **kwargs):
        usuario, error = _usuario_autenticado()
        if error:
            return error
        if usuario.rol != "admin":
            return (
                jsonify(
                    {
                        "success": False,
                        "error": {"message": "Se requieren permisos de administrador."},
                    }
                ),
                403,
            )
        kwargs["usuario_id"] = usuario.id
        return f(*args, **kwargs)

    return decorador


def requiere_propietario(f):
    """Decorador que valida JWT y verifica que el usuario tenga rol 'propietario'."""

    @functools.wraps(f)
    def decorador(*args, **kwargs):
        usuario, error = _usuario_autenticado()
        if error:
            return error
        if usuario.rol != "propietario":
            return (
                jsonify(
                    {
                        "success": False,
                        "error": {"message": "Se requiere rol de propietario."},
                    }
                ),
                403,
            )
        kwargs["usuario_id"] = usuario.id
        return f(*args, **kwargs)

    return decorador


def requiere_arrendatario(f):
    """Decorador que valida JWT y verifica que el usuario tenga rol 'arrendatario'."""

    @functools.wraps(f)
    def decorador(*args, **kwargs):
        usuario, error = _usuario_autenticado()
        if error:
            return error
        if usuario.rol != "arrendatario":
            return (
                jsonify(
                    {
                        "success": False,
                        "error": {"message": "Se requiere rol de arrendatario."},
                    }
                ),
                403,
            )
        kwargs["usuario_id"] = usuario.id
        return f(*args, **kwargs)

    return decorador
