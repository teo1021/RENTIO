"""
DTOs del dominio de usuarios.

Schemas de Marshmallow para validar entrada/salida en operaciones
de registro, login y actualización de perfil.
"""

from marshmallow import Schema, fields, validate

ROLES_VALIDOS = ["arrendatario", "propietario"]


class RegistroDTO(Schema):
    """Validación de datos para el registro de un usuario nuevo."""

    correo = fields.Email(required=True, error_messages={"required": "El correo es obligatorio."})
    contrasena = fields.String(
        required=True,
        validate=validate.Length(min=8, error="La contraseña debe tener al menos 8 caracteres."),
        error_messages={"required": "La contraseña es obligatoria."},
    )
    rol = fields.String(
        required=True,
        validate=validate.OneOf(
            ROLES_VALIDOS, error="El rol debe ser 'arrendatario' o 'propietario'."
        ),
        error_messages={"required": "El rol es obligatorio."},
    )
    nombre = fields.String(
        load_default=None,
        validate=validate.Length(max=100),
    )
    apellido = fields.String(
        load_default=None,
        validate=validate.Length(max=100),
    )


class LoginDTO(Schema):
    """Validación de datos para el inicio de sesión."""

    correo = fields.Email(required=True, error_messages={"required": "El correo es obligatorio."})
    contrasena = fields.String(
        required=True,
        error_messages={"required": "La contraseña es obligatoria."},
    )


class ActualizarPerfilDTO(Schema):
    """Validación de datos para actualización parcial del perfil."""

    nombre = fields.String(load_default=None, validate=validate.Length(max=100))
    apellido = fields.String(load_default=None, validate=validate.Length(max=100))
    telefono = fields.String(load_default=None, validate=validate.Length(max=20))
    cedula = fields.String(load_default=None, validate=validate.Length(max=20))
    foto_perfil = fields.String(load_default=None, validate=validate.Length(max=500))


class CambiarRolDTO(Schema):
    """Validación de datos para que un admin cambie el rol de un usuario."""

    rol = fields.String(
        required=True,
        validate=validate.OneOf(
            ["arrendatario", "propietario", "admin"],
            error="Rol inválido.",
        ),
        error_messages={"required": "El rol es obligatorio."},
    )
