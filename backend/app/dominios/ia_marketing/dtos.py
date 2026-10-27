"""
DTOs del dominio de IA Marketing.

Schemas de Marshmallow para validar la entrada de prompts de marketing.
"""

from marshmallow import Schema, fields, validate


class GenerarDescripcionDTO(Schema):
    """Validación de datos para generar una descripción atractiva con IA."""

    barrio = fields.String(
        required=True,
        validate=validate.Length(min=2, max=100),
        error_messages={"required": "El barrio es obligatorio."},
    )
    tipo = fields.String(load_default="apartamento")
    estrato = fields.Integer(load_default=4, validate=validate.Range(min=1, max=6))
    habitaciones = fields.Integer(load_default=2, validate=validate.Range(min=0, max=50))
    banos = fields.Integer(load_default=2, validate=validate.Range(min=0, max=50))
    area_m2 = fields.Float(load_default=None)
    caracteristicas = fields.List(fields.String(), load_default=[])
    precio_mensual = fields.Float(load_default=None)
    tono = fields.String(load_default="atractivo y moderno")


class SugerirPrecioDTO(Schema):
    """Validación de datos para estimar el precio de arriendo según el mercado."""

    barrio = fields.String(
        required=True,
        validate=validate.Length(min=2, max=100),
        error_messages={"required": "El barrio es obligatorio."},
    )
    estrato = fields.Integer(
        required=True,
        validate=validate.Range(min=1, max=6),
        error_messages={"required": "El estrato es obligatorio."},
    )
    tipo = fields.String(load_default="apartamento")
    area_m2 = fields.Float(load_default=None)
    habitaciones = fields.Integer(load_default=2)
    banos = fields.Integer(load_default=2)
    caracteristicas = fields.List(fields.String(), load_default=[])


class AnalisisMercadoDTO(Schema):
    """Validación de datos para consultar el análisis de mercado de una zona."""

    barrio = fields.String(
        required=True,
        validate=validate.Length(min=2, max=100),
        error_messages={"required": "El barrio es obligatorio."},
    )
    tipo = fields.String(load_default="apartamento")
    estrato = fields.Integer(load_default=4, validate=validate.Range(min=1, max=6))


class MejorarTituloDTO(Schema):
    """Validación de datos para mejorar el título de un anuncio inmobiliario."""

    titulo_actual = fields.String(
        required=True,
        validate=validate.Length(min=3, max=255),
        error_messages={"required": "El título actual es obligatorio."},
    )
    barrio = fields.String(
        required=True,
        validate=validate.Length(min=2, max=100),
        error_messages={"required": "El barrio es obligatorio."},
    )
    tipo = fields.String(load_default="apartamento")
    caracteristicas_destacadas = fields.List(fields.String(), load_default=[])
