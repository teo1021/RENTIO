"""
Tests automatizados para el dominio de IA Marketing.
"""


def test_ia_marketing_generar_descripcion(client, propietario_auth, arrendatario_auth):
    """Verifica la generación de descripción atractiva con IA (solo propietario)."""
    payload = {
        "barrio": "El Poblado",
        "tipo": "apartamento",
        "estrato": 6,
        "habitaciones": 3,
        "banos": 3,
        "area_m2": 110.0,
        "caracteristicas": ["Piscina", "Vigilancia 24/7", "Vista panorámica"],
        "tono": "elegante",
    }

    # Fallo con arrendatario (403)
    res_fallo = client.post(
        "/api/v1/ia/generar-descripcion",
        headers=arrendatario_auth["headers"],
        json=payload,
    )
    assert res_fallo.status_code == 403

    # Éxito con propietario
    res = client.post(
        "/api/v1/ia/generar-descripcion",
        headers=propietario_auth["headers"],
        json=payload,
    )
    assert res.status_code == 200
    datos = res.get_json()
    assert datos["success"] is True
    assert "descripcion" in datos["data"]
    assert len(datos["data"]["puntos_destacados"]) >= 1


def test_ia_marketing_sugerir_precio(client, propietario_auth):
    """Verifica la sugerencia y estimación de rangos de precio con IA."""
    payload = {
        "barrio": "Laureles",
        "estrato": 5,
        "tipo": "apartamento",
        "area_m2": 90.0,
        "habitaciones": 3,
        "banos": 2,
    }
    res = client.post(
        "/api/v1/ia/sugerir-precio",
        headers=propietario_auth["headers"],
        json=payload,
    )
    assert res.status_code == 200
    datos = res.get_json()["data"]
    assert datos["precio_sugerido"] > 0
    assert datos["precio_minimo"] <= datos["precio_sugerido"] <= datos["precio_maximo"]


def test_ia_marketing_analisis_mercado(client, propietario_auth):
    """Verifica la generación de análisis de mercado por barrio en Medellín."""
    payload = {
        "barrio": "Belén",
        "tipo": "apartamento",
        "estrato": 4,
    }
    res = client.post(
        "/api/v1/ia/analisis-mercado",
        headers=propietario_auth["headers"],
        json=payload,
    )
    assert res.status_code == 200
    datos = res.get_json()["data"]
    assert "nivel_demanda" in datos
    assert "tiempo_promedio_vacancia_dias" in datos


def test_ia_marketing_mejorar_titulo(client, propietario_auth):
    """Verifica la optimización de títulos llamativos para portales."""
    payload = {
        "titulo_actual": "Apartamento arriendo medellin",
        "barrio": "Conquistadores",
        "tipo": "apartamento",
        "caracteristicas_destacadas": ["Cerca a Parques del Río", "Balcón"],
    }
    res = client.post(
        "/api/v1/ia/mejorar-titulo",
        headers=propietario_auth["headers"],
        json=payload,
    )
    assert res.status_code == 200
    datos = res.get_json()["data"]
    assert len(datos["titulos_sugeridos"]) >= 2
