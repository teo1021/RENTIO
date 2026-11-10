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
    arrendatario_nombre = fields.String(required=True, validate=validate.Length(min=1, max=100))
    arrendatario_apellido = fields.String(required=True, validate=validate.Length(min=1, max=100))
    arrendatario_cedula = fields.String(
        required=True, validate=validate.Regexp(r"^[0-9A-Za-z.-]{5,20}$")
    )
    arrendatario_telefono = fields.String(
        required=True, validate=validate.Regexp(r"^[0-9+() -]{7,20}$")
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
        validate=validate.Range(min=1, error="El precio acordado debe ser mayor que cero."),
    )
