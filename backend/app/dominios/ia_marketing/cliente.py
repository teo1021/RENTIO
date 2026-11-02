"""Cliente HTTP del microservicio de IA."""

import httpx
from flask import current_app


class ServicioIAError(Exception):
    """El microservicio de IA no respondió correctamente."""


def solicitar(endpoint, payload):
    url = current_app.config.get("AI_SERVICE_URL", "").rstrip("/")
    key = current_app.config.get("AI_INTERNAL_API_KEY", "")
    if not url or not key:
        raise ServicioIAError("El servicio de IA no está configurado.")
    try:
        response = httpx.post(
            f"{url}{endpoint}",
            json=payload,
            headers={"X-Internal-API-Key": key},
            timeout=30.0,
        )
        response.raise_for_status()
        return response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise ServicioIAError("No fue posible procesar el mensaje con el servicio de IA.") from exc


def conversar(mensaje, datos_previos):
    return solicitar(
        "/api/v1/ia/conversar",
        {"mensaje_usuario": mensaje, "datos_previos": datos_previos, "historial": []},
    )
