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
        payload, error = _extraer_y_validar_token()
        if error:
            return error
        kwargs["usuario_id"] = payload["usuario_id"]
        return f(*args, **kwargs)

    return decorador


def requiere_admin(f):
    """Decorador que valida JWT y verifica que el usuario tenga rol 'admin'."""

    @functools.wraps(f)
    def decorador(*args, **kwargs):
        payload, error = _extraer_y_validar_token()
        if error:
            return error
        if payload.get("rol") != "admin":
            return (
                jsonify(
                    {
                        "success": False,
                        "error": {"message": "Se requieren permisos de administrador."},
                    }
                ),
                403,
            )
        kwargs["usuario_id"] = payload["usuario_id"]
        return f(*args, **kwargs)

    return decorador


def requiere_propietario(f):
    """Decorador que valida JWT y verifica que el usuario tenga rol 'propietario'."""

    @functools.wraps(f)
    def decorador(*args, **kwargs):
        payload, error = _extraer_y_validar_token()
        if error:
            return error
        if payload.get("rol") != "propietario":
            return (
                jsonify(
                    {
                        "success": False,
                        "error": {"message": "Se requiere rol de propietario."},
                    }
                ),
                403,
            )
        kwargs["usuario_id"] = payload["usuario_id"]
        return f(*args, **kwargs)

    return decorador
