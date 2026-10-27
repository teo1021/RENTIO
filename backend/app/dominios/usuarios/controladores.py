"""
Controladores del dominio de usuarios.

Define los blueprints `usuarios_bp` y `admin_bp` con los endpoints
de registro, login, perfil y administración de usuarios.
"""

from flask import Blueprint, jsonify, request
from marshmallow import ValidationError

from app.dominios.usuarios.dtos import (
    ActualizarPerfilDTO,
    CambiarRolDTO,
    LoginDTO,
    RegistroDTO,
)
from app.seguridad import requiere_admin, requiere_token

# ── Servicio inyectado por el factory ──────────────────────────────────
servicio = None

# ── Blueprints ─────────────────────────────────────────────────────────
usuarios_bp = Blueprint("usuarios", __name__)
admin_bp = Blueprint("admin", __name__)


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINTS DE USUARIOS
# ═══════════════════════════════════════════════════════════════════════════════


@usuarios_bp.route("/registro", methods=["POST"])
def registrar():
    """Registra un nuevo usuario con rol arrendatario o propietario."""
    try:
        datos = RegistroDTO().load(request.get_json() or {})
    except ValidationError as err:
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "message": "Datos de entrada inválidos.",
                        "details": err.messages,
                    },
                }
            ),
            400,
        )

    usuario = servicio.registrar(datos)
    return (
        jsonify(
            {
                "success": True,
                "message": "Usuario registrado con éxito.",
                "data": usuario.to_dict(),
            }
        ),
        201,
    )


@usuarios_bp.route("/login", methods=["POST"])
def login():
    """Autentica un usuario y retorna un token JWT."""
    try:
        datos = LoginDTO().load(request.get_json() or {})
    except ValidationError as err:
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "message": "Datos de entrada inválidos.",
                        "details": err.messages,
                    },
                }
            ),
            400,
        )

    resultado = servicio.login(datos)
    return (
        jsonify(
            {
                "success": True,
                "message": "Inicio de sesión exitoso.",
                "data": resultado,
            }
        ),
        200,
    )


@usuarios_bp.route("/perfil", methods=["GET"])
@requiere_token
def obtener_perfil(usuario_id=None):
    """Retorna el perfil del usuario autenticado."""
    usuario = servicio.obtener_perfil(usuario_id)
    return (
        jsonify(
            {
                "success": True,
                "message": "Perfil obtenido con éxito.",
                "data": usuario.to_dict(),
            }
        ),
        200,
    )


@usuarios_bp.route("/perfil", methods=["PATCH"])
@requiere_token
def actualizar_perfil(usuario_id=None):
    """Actualiza parcialmente el perfil del usuario autenticado."""
    try:
        datos = ActualizarPerfilDTO().load(request.get_json() or {})
    except ValidationError as err:
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "message": "Datos de entrada inválidos.",
                        "details": err.messages,
                    },
                }
            ),
            400,
        )

    usuario = servicio.actualizar_perfil(usuario_id, datos)
    return (
        jsonify(
            {
                "success": True,
                "message": "Perfil actualizado con éxito.",
                "data": usuario.to_dict(),
            }
        ),
        200,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINTS DE ADMINISTRACIÓN
# ═══════════════════════════════════════════════════════════════════════════════


@admin_bp.route("/usuarios", methods=["GET"])
@requiere_admin
def listar_usuarios(usuario_id=None):
    """Lista todos los usuarios registrados (solo admin)."""
    usuarios = servicio.listar_usuarios()
    return (
        jsonify(
            {
                "success": True,
                "message": "Usuarios obtenidos con éxito.",
                "data": [u.to_dict() for u in usuarios],
            }
        ),
        200,
    )


@admin_bp.route("/usuarios/<int:id>/rol", methods=["PATCH"])
@requiere_admin
def cambiar_rol(id, usuario_id=None):
    """Cambia el rol de un usuario (solo admin)."""
    try:
        datos = CambiarRolDTO().load(request.get_json() or {})
    except ValidationError as err:
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "message": "Datos de entrada inválidos.",
                        "details": err.messages,
                    },
                }
            ),
            400,
        )

    usuario = servicio.cambiar_rol(id, datos["rol"])
    return (
        jsonify(
            {
                "success": True,
                "message": "Rol actualizado con éxito.",
                "data": usuario.to_dict(),
            }
        ),
        200,
    )
