"""
Controladores del dominio de usuarios.
"""

from flask import Blueprint, g, jsonify, request
from marshmallow import ValidationError

from app.dominios.usuarios.dtos import (
    ActualizarPerfilDTO,
    CambiarContextoDTO,
    CambiarRolDTO,
    LoginDTO,
    RegistroDTO,
)
from app.seguridad import requiere_admin, requiere_token

servicio = None
usuarios_bp = Blueprint("usuarios", __name__)
admin_bp = Blueprint("admin", __name__)


@usuarios_bp.route("/registro", methods=["POST"])
def registrar():
    try:
        datos = RegistroDTO().load(request.get_json() or {})
    except ValidationError as err:
        return jsonify({"success": False, "error": {"message": "Datos de entrada inválidos.", "details": err.messages}}), 400
    usuario = servicio.registrar(datos)
    return jsonify({"success": True, "message": "Usuario registrado con éxito.", "data": usuario.to_dict()}), 201


@usuarios_bp.route("/login", methods=["POST"])
def login():
    try:
        datos = LoginDTO().load(request.get_json() or {})
    except ValidationError as err:
        return jsonify({"success": False, "error": {"message": "Datos de entrada inválidos.", "details": err.messages}}), 400
    resultado = servicio.login(datos)
    return jsonify({"success": True, "message": "Inicio de sesión exitoso.", "data": resultado}), 200


@usuarios_bp.route("/cambiar-contexto", methods=["POST"])
@requiere_token
def cambiar_contexto(usuario_id=None):
    try:
        datos = CambiarContextoDTO().load(request.get_json() or {})
    except ValidationError as err:
        return jsonify({"success": False, "error": {"message": "Rol solicitado inválido.", "details": err.messages}}), 400
    resultado = servicio.cambiar_contexto(usuario_id, datos["rol"])
    return jsonify({"success": True, "message": "Modo actualizado.", "data": resultado}), 200


@usuarios_bp.route("/perfil", methods=["GET"])
@requiere_token
def obtener_perfil(usuario_id=None):
    usuario = servicio.obtener_perfil(usuario_id)
    return jsonify({"success": True, "message": "Perfil obtenido con éxito.", "data": usuario.to_dict(rol_activo=getattr(g, "rol_activo", None))}), 200


@usuarios_bp.route("/perfil", methods=["PATCH"])
@requiere_token
def actualizar_perfil(usuario_id=None):
    try:
        datos = ActualizarPerfilDTO().load(request.get_json() or {})
    except ValidationError as err:
        return jsonify({"success": False, "error": {"message": "Datos de entrada inválidos.", "details": err.messages}}), 400
    usuario = servicio.actualizar_perfil(usuario_id, datos)
    return jsonify({"success": True, "message": "Perfil actualizado con éxito.", "data": usuario.to_dict(rol_activo=getattr(g, "rol_activo", None))}), 200


@admin_bp.route("/usuarios", methods=["GET"])
@requiere_admin
def listar_usuarios(usuario_id=None):
    usuarios = servicio.listar_usuarios()
    return jsonify({"success": True, "message": "Usuarios obtenidos con éxito.", "data": [u.to_dict() for u in usuarios]}), 200


@admin_bp.route("/usuarios/<int:id>/rol", methods=["PATCH"])
@requiere_admin
def cambiar_rol(id, usuario_id=None):
    try:
        datos = CambiarRolDTO().load(request.get_json() or {})
    except ValidationError as err:
        return jsonify({"success": False, "error": {"message": "Datos de entrada inválidos.", "details": err.messages}}), 400
    usuario = servicio.cambiar_rol(id, datos["rol"])
    return jsonify({"success": True, "message": "Rol actualizado con éxito.", "data": usuario.to_dict()}), 200
