"""
Tests automatizados para el dominio de características.
"""


def test_crear_caracteristica_como_admin(client, admin_auth):
    """Verifica la creación de una característica por parte de un admin."""
    res = client.post(
        "/api/v1/caracteristicas",
        headers=admin_auth["headers"],
        json={"nombre": "Piscina Climatizada", "icono": "pool"},
    )
    assert res.status_code == 201
    datos = res.get_json()
    assert datos["success"] is True
    assert datos["data"]["nombre"] == "Piscina Climatizada"


def test_crear_caracteristica_sin_permiso(client, arrendatario_auth):
    """Verifica que un no-admin no pueda crear características (403)."""
    res = client.post(
        "/api/v1/caracteristicas",
        headers=arrendatario_auth["headers"],
        json={"nombre": "Gimnasio", "icono": "gym"},
    )
    assert res.status_code == 403


def test_listar_caracteristicas_publico(client, admin_auth):
    """Verifica que cualquiera pueda consultar las características."""
    client.post(
        "/api/v1/caracteristicas",
        headers=admin_auth["headers"],
        json={"nombre": "WiFi Fibra Óptica", "icono": "wifi"},
    )

    res = client.get("/api/v1/caracteristicas")
    assert res.status_code == 200
    caracteristicas = res.get_json()["data"]
    assert any(c["nombre"] == "WiFi Fibra Óptica" for c in caracteristicas)
