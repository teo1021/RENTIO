"""
Controladores del dominio de IA Marketing.

Define el blueprint `ia_bp` con endpoints especializados para propietarios.
"""

from flask import Blueprint, jsonify, request
from marshmallow import ValidationError

from app.dominios.ia_marketing.dtos import (
    AnalisisMercadoDTO,
    GenerarDescripcionDTO,
    MejorarTituloDTO,
    SugerirPrecioDTO,
)
from app.seguridad import requiere_propietario

# ── Servicio inyectado por el factory ──────────────────────────────────
servicio = None

# ── Blueprint ──────────────────────────────────────────────────────────
ia_bp = Blueprint("ia", __name__)


@ia_bp.route("/generar-descripcion", methods=["POST"])
@requiere_propietario
def generar_descripcion(usuario_id=None):
    """Genera una descripción atractiva para la propiedad con IA."""
    try:
        datos = GenerarDescripcionDTO().load(request.get_json() or {})
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

    resultado = servicio.generar_descripcion(datos)
    return (
        jsonify(
            {
                "success": True,
                "message": "Descripción generada con éxito.",
                "data": resultado,
            }
        ),
        200,
    )


@ia_bp.route("/sugerir-precio", methods=["POST"])
@requiere_propietario
def sugerir_precio(usuario_id=None):
    """Estima y sugiere rangos de precios de mercado con IA."""
    try:
        datos = SugerirPrecioDTO().load(request.get_json() or {})
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

    resultado = servicio.sugerir_precio(datos)
    return (
        jsonify(
            {
                "success": True,
                "message": "Sugerencia de precio calculada con éxito.",
                "data": resultado,
            }
        ),
        200,
    )


@ia_bp.route("/analisis-mercado", methods=["POST"])
@requiere_propietario
def analisis_mercado(usuario_id=None):
    """Genera un análisis de mercado y demanda para la zona."""
    try:
        datos = AnalisisMercadoDTO().load(request.get_json() or {})
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

    resultado = servicio.analisis_mercado(datos)
    return (
        jsonify(
            {
                "success": True,
                "message": "Análisis de mercado generado con éxito.",
                "data": resultado,
            }
        ),
        200,
    )


@ia_bp.route("/mejorar-titulo", methods=["POST"])
@requiere_propietario
def mejorar_titulo(usuario_id=None):
    """Propone mejoras llamativas para el título del anuncio."""
    try:
        datos = MejorarTituloDTO().load(request.get_json() or {})
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

    resultado = servicio.mejorar_titulo(datos)
    return (
        jsonify(
            {
                "success": True,
                "message": "Títulos mejorados generados con éxito.",
                "data": resultado,
            }
        ),
        200,
    )
