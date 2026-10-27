"""
DTOs del dominio de propiedades.

Schemas de Marshmallow para validar operaciones CRUD y filtrado.
"""

from marshmallow import Schema, fields, validate

TIPOS_PROPIEDAD = ["casa", "apartamento", "habitacion", "finca"]
ESTADOS_PROPIEDAD = ["disponible", "arrendada", "inactiva"]


class CrearPropiedadDTO(Schema):
    """Validación de datos para crear una nueva propiedad."""

    titulo = fields.String(
        required=True,
        validate=validate.Length(min=5, max=255),
        error_messages={"required": "El título es obligatorio."},
    )
    descripcion = fields.String(load_default=None, validate=validate.Length(max=5000))
    precio_mensual = fields.Float(
        required=True,
        validate=validate.Range(min=0, error="El precio debe ser positivo."),
        error_messages={"required": "El precio mensual es obligatorio."},
    )
    direccion = fields.String(
        required=True,
        validate=validate.Length(min=5, max=500),
        error_messages={"required": "La dirección es obligatoria."},
    )
    estrato = fields.Integer(
        required=True,
        validate=validate.Range(min=1, max=6, error="El estrato debe estar entre 1 y 6."),
        error_messages={"required": "El estrato es obligatorio."},
    )
    area_m2 = fields.Float(
        load_default=None,
        validate=validate.Range(min=1, error="El área debe ser mayor a 0."),
    )
    habitaciones = fields.Integer(
        load_default=1,
        validate=validate.Range(min=0, max=50),
    )
    banos = fields.Integer(
        load_default=1,
        validate=validate.Range(min=0, max=50),
    )
    tipo = fields.String(
        load_default="apartamento",
        validate=validate.OneOf(TIPOS_PROPIEDAD, error="Tipo de propiedad inválido."),
    )
    barrio_id = fields.Integer(load_default=None)
    caracteristicas_ids = fields.List(fields.Integer(), load_default=[])


class ActualizarPropiedadDTO(Schema):
    """Validación de datos para actualización parcial de una propiedad."""

    titulo = fields.String(load_default=None, validate=validate.Length(min=5, max=255))
    descripcion = fields.String(load_default=None, validate=validate.Length(max=5000))
    precio_mensual = fields.Float(
        load_default=None,
        validate=validate.Range(min=0, error="El precio debe ser positivo."),
    )
    direccion = fields.String(load_default=None, validate=validate.Length(min=5, max=500))
    estrato = fields.Integer(
        load_default=None,
        validate=validate.Range(min=1, max=6),
    )
    area_m2 = fields.Float(load_default=None, validate=validate.Range(min=1))
    habitaciones = fields.Integer(load_default=None, validate=validate.Range(min=0, max=50))
    banos = fields.Integer(load_default=None, validate=validate.Range(min=0, max=50))
    tipo = fields.String(
        load_default=None,
        validate=validate.OneOf(TIPOS_PROPIEDAD),
    )
    estado = fields.String(
        load_default=None,
        validate=validate.OneOf(ESTADOS_PROPIEDAD),
    )
    barrio_id = fields.Integer(load_default=None)


class FiltroPropiedadDTO(Schema):
    """Validación de filtros para la búsqueda de propiedades."""

    barrio_id = fields.Integer(load_default=None)
    estrato = fields.Integer(load_default=None, validate=validate.Range(min=1, max=6))
    precio_min = fields.Float(load_default=None, validate=validate.Range(min=0))
    precio_max = fields.Float(load_default=None, validate=validate.Range(min=0))
    tipo = fields.String(load_default=None, validate=validate.OneOf(TIPOS_PROPIEDAD))
    habitaciones = fields.Integer(load_default=None, validate=validate.Range(min=0))


class ActualizarCaracteristicasDTO(Schema):
    """Validación de datos para asignar características a una propiedad."""

    caracteristicas_ids = fields.List(
        fields.Integer(),
        required=True,
        error_messages={"required": "La lista de IDs de características es obligatoria."},
    )
