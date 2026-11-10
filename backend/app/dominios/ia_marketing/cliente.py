"""Cliente HTTP del microservicio de IA."""

import httpx
from flask import current_app


class ServicioIAError(Exception):
    """Error de configuración, conectividad o respuesta del microservicio de IA."""

    def __init__(self, mensaje, status_code=502):
        super().__init__(mensaje)
        self.status_code = status_code


def solicitar(endpoint, payload):
    url = current_app.config.get("AI_SERVICE_URL", "").rstrip("/")
    key = current_app.config.get("AI_INTERNAL_API_KEY", "")
    if not url:
        raise ServicioIAError(
            "La URL del servicio de IA no está configurada (AI_SERVICE_URL).",
            status_code=503,
        )
    if not key:
        raise ServicioIAError(
            "La llave compartida del servicio de IA no está configurada (AI_INTERNAL_API_KEY).",
            status_code=503,
        )

    try:
        response = httpx.post(
            f"{url}{endpoint}",
            json=payload,
            headers={"X-Internal-API-Key": key},
            timeout=httpx.Timeout(45.0, connect=5.0),
        )
    except httpx.TimeoutException as exc:
        current_app.logger.warning("Timeout al llamar al servicio de IA: %s", endpoint)
        raise ServicioIAError(
            "El servicio de IA tardó demasiado en responder. Inténtalo de nuevo.",
            status_code=504,
        ) from exc
    except httpx.ConnectError as exc:
        current_app.logger.warning(
            "No se pudo conectar al servicio de IA en %s%s",
            url,
            endpoint,
        )
        raise ServicioIAError(
            "El servicio de IA no está disponible. Verifica que esté iniciado en el puerto 5001.",
            status_code=503,
        ) from exc
    except httpx.RequestError as exc:
        current_app.logger.exception("Error de comunicación con el servicio de IA: %s", endpoint)
        raise ServicioIAError(
            "Ocurrió un error de comunicación con el servicio de IA.",
            status_code=502,
        ) from exc

    if not response.is_success:
        detail = ""
        try:
            body = response.json()
            detail = body.get("detail", "") if isinstance(body, dict) else ""
        except ValueError:
            detail = ""

        current_app.logger.error(
            "El servicio de IA respondió HTTP %s en %s%s",
            response.status_code,
            url,
            endpoint,
        )
        if response.status_code in (401, 403, 503):
            raise ServicioIAError(
                "El servicio de IA rechazó la solicitud. Verifica que la llave interna "
                "coincida en el backend y ai_service."
                + (f" Detalle: {detail}" if detail else ""),
                status_code=503,
            )
        raise ServicioIAError(
            "El servicio de IA no pudo procesar la solicitud."
            + (f" Detalle: {detail}" if detail else ""),
            status_code=502,
        )

    try:
        result = response.json()
    except ValueError as exc:
        current_app.logger.error("El servicio de IA devolvió JSON inválido en %s", endpoint)
        raise ServicioIAError(
            "El servicio de IA devolvió una respuesta inválida.",
            status_code=502,
        ) from exc

    if not isinstance(result, dict):
        raise ServicioIAError(
            "El servicio de IA devolvió un formato de respuesta inesperado.",
            status_code=502,
        )
    return result


def conversar(mensaje, datos_previos, historial=None):
    from app.dominios.barrios.modelos import Barrio

    return solicitar(
        "/api/v1/ia/conversar",
        {
            "mensaje_usuario": mensaje,
            "datos_previos": datos_previos,
            "historial": historial or [],
            "barrios_disponibles": [barrio.nombre for barrio in Barrio.query.order_by(Barrio.nombre).all()],
        },
    )


def generar_plantilla_contrato():
    """Solicita una plantilla genérica, sin enviar datos de las partes ni del canon."""
    return solicitar(
        "/api/v1/ia/generar-contrato",
        {"tipo_contrato": "arrendamiento_vivienda_urbana_colombia"},
    )
