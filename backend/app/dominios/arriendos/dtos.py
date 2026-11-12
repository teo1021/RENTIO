"""
DTOs del dominio de arriendos.

Schemas de Marshmallow para el flujo completo:
  solicitud con datos personales → respuesta de visita → generación de contrato.
"""

from marshmallow import Schema, fields, validate

# ── Estados válidos ──────────────────────────────────────────────────────────

ESTADOS_VISITA = ["visita_programada", "rechazada"]
ESTADOS_RESPUESTA_LEGADO = ["aceptada", "rechazada"]


# ── DTOs de solicitud ────────────────────────────────────────────────────────


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
    cedula_arrendatario = fields.String(
        required=True,
        validate=validate.Length(min=5, max=20),
        error_messages={"required": "La cédula es obligatoria para identificarte."},
    )
    telefono_arrendatario = fields.String(
        required=True,
        validate=validate.Length(min=7, max=20),
        error_messages={"required": "El número de celular es obligatorio."},
    )
    fecha_visita_propuesta = fields.Date(
        required=True,
        error_messages={"required": "Debes proponer una fecha para la visita."},
    )


# ── DTOs de respuesta del propietario ────────────────────────────────────────


class ResponderVisitaDTO(Schema):
    """Validación para que el propietario acepte o rechace la visita."""

    estado = fields.String(
        required=True,
        validate=validate.OneOf(
            ESTADOS_VISITA,
            error="El estado debe ser 'visita_programada' o 'rechazada'.",
        ),
        error_messages={"required": "El estado de la respuesta es obligatorio."},
    )
    fecha_visita_confirmada = fields.Date(load_default=None)


class GenerarContratoDTO(Schema):
    """Validación para que el propietario formalice el contrato después de la visita."""

    fecha_inicio = fields.Date(
        required=True,
        error_messages={"required": "La fecha de inicio del contrato es obligatoria."},
    )
    fecha_fin = fields.Date(
        required=True,
        error_messages={"required": "La fecha de fin del contrato es obligatoria."},
    )
    precio_acordado = fields.Float(
        load_default=None,
        validate=validate.Range(min=0, error="El precio acordado debe ser positivo."),
    )

    # Información laboral
    trabaja = fields.Boolean(load_default=None)
    empresa = fields.String(load_default=None, validate=validate.Length(max=200))
    cargo = fields.String(load_default=None, validate=validate.Length(max=200))
    ingreso_mensual = fields.Float(
        load_default=None,
        validate=validate.Range(min=0),
    )

    # Fiador
    fiador_nombre = fields.String(load_default=None, validate=validate.Length(max=200))
    fiador_cedula = fields.String(load_default=None, validate=validate.Length(max=20))
    fiador_telefono = fields.String(load_default=None, validate=validate.Length(max=20))

    # Cláusulas
    clausulas_adicionales = fields.String(load_default=None, validate=validate.Length(max=5000))


# ── DTO legado (retrocompatibilidad) ─────────────────────────────────────────


class ResponderSolicitudDTO(Schema):
    """Legado: se mantiene para no romper integraciones existentes.
    Usar ResponderVisitaDTO y GenerarContratoDTO en su lugar.
    """

    estado = fields.String(
        required=True,
        validate=validate.OneOf(
            ESTADOS_RESPUESTA_LEGADO,
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
