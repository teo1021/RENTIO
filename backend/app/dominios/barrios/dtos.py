"""
DTOs del dominio de barrios.

Schemas de Marshmallow para validar la creación y actualización de barrios.
"""

from marshmallow import Schema, fields, validate


class CrearBarrioDTO(Schema):
    """Validación de datos para registrar un barrio."""

    nombre = fields.String(
        required=True,
        validate=validate.Length(min=2, max=100),
        error_messages={"required": "El nombre del barrio es obligatorio."},
    )
    comuna = fields.String(
        required=True,
        validate=validate.Length(min=2, max=100),
        error_messages={"required": "La comuna es obligatoria."},
    )
    zona = fields.String(
        required=True,
        validate=validate.Length(min=2, max=100),
        error_messages={"required": "La zona es obligatoria."},
    )
