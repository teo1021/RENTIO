"""
DTOs del dominio de características.

Schemas de Marshmallow para validar la creación de características.
"""

from marshmallow import Schema, fields, validate


class CrearCaracteristicaDTO(Schema):
    """Validación de datos para crear una nueva característica."""

    nombre = fields.String(
        required=True,
        validate=validate.Length(min=2, max=100),
        error_messages={"required": "El nombre es obligatorio."},
    )
    icono = fields.String(
        load_default=None,
        validate=validate.Length(max=100),
    )
