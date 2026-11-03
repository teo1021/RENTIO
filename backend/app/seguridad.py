"""
Decoradores de autenticación y autorización de RENTIO.
"""

import functools

import jwt
from flask import current_app, g, jsonify, request


def _extraer_y_validar_token():
    header = request.headers.get("Authorization", "")
    if not header:
        return None, (jsonify({"success": False, "error": {"message": "Token de autenticación requerido."}}), 401)

    partes = header.split(" ")
    if len(partes) != 2 or partes[0] != "Bearer":
        return None, (jsonify({"success": False, "error": {"message": "Formato de token inválido. Use: Bearer <token>"}}), 401)

    try:
        payload = jwt.decode(partes[1], current_app.config["SECRET_KEY"], algorithms=["HS256"])
        return payload, None
    except jwt.ExpiredSignatureError:
        return None, (jsonify({"success": False, "error": {"message": "El token ha expirado."}}), 401)
    except jwt.InvalidTokenError:
        return None, (jsonify({"success": False, "error": {"message": "Token inválido."}}), 401)


def requiere_token(f):
    """Valida JWT e inyecta el identificador y contexto activo del usuario."""

    @functools.wraps(f)
    def decorador(*args, **kwargs):
        payload, error = _extraer_y_validar_token()
        if error:
            return error
        g.rol_activo = payload.get("rol")
        g.roles_usuario = payload.get("roles", [payload.get("rol")])
        kwargs["usuario_id"] = payload["usuario_id"]
        return f(*args, **kwargs)

    return decorador


def requiere_admin(f):
    """Valida que el contexto autenticado sea administrador."""

    @functools.wraps(f)
    def decorador(*args, **kwargs):
        payload, error = _extraer_y_validar_token()
        if error:
            return error
        if payload.get("rol") != "admin":
            return (jsonify({"success": False, "error": {"message": "Se requieren permisos de administrador."}}), 403)
        kwargs["usuario_id"] = payload["usuario_id"]
        return f(*args, **kwargs)

    return decorador


def requiere_propietario(f):
    """Valida que la cuenta tenga el rol de propietario habilitado y activo."""

    @functools.wraps(f)
    def decorador(*args, **kwargs):
        payload, error = _extraer_y_validar_token()
        if error:
            return error
        roles = payload.get("roles", [payload.get("rol")])
        if payload.get("rol") != "admin" and (payload.get("rol") != "propietario" or "propietario" not in roles):
            return (jsonify({"success": False, "error": {"message": "Cambia al modo propietario para realizar esta acción."}}), 403)
        kwargs["usuario_id"] = payload["usuario_id"]
        return f(*args, **kwargs)

    return decorador
