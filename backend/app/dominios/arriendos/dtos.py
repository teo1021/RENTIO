"""
DTOs del dominio de arriendos.

Schemas de Marshmallow para solicitudes y formalización de contratos.
"""

from marshmallow import Schema, fields, validate

ESTADOS_RESPUESTA = ["aceptada", "rechazada"]


class SolicitarArriendoDTO(Schema):
    """Validación de datos para enviar una solicitud de arriendo."""

    propiedad_id = fields.Integer(
        required=True,
        error_messages={"required": "El ID de la propiedad es obligatorio."},
    )
    mensaje = fields.String(
        load_default=None,
        validate=validate.Length(max=1000),
    )


class ResponderSolicitudDTO(Schema):
    """Validación de datos para que el propietario responda a una solicitud."""

    estado = fields.String(
        required=True,
        validate=validate.OneOf(
            ESTADOS_RESPUESTA,
            error="El estado debe ser 'aceptada' o 'rechazada'.",
        ),
        error_messages={"required": "El estado de la respuesta es obligatorio."},
    )
    fecha_inicio = fields.Date(load_default=None)
    fecha_fin = fields.Date(load_default=None)
    precio_acordado = fields.Float(
        load_default=None,
        validate=validate.Range(min=0, error="El precio acordado debe ser positivo."),
    )
