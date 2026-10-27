"""
Tests automatizados para el dominio de barrios.
"""

from app.dominios.barrios.modelos import Barrio
from app.dominios.barrios.repositorios import BarrioRepositorio


def test_listar_barrios_y_propiedades(client, db):
    """Verifica listar barrios y consultar propiedades filtradas por barrio."""
    # Insertar barrios de prueba
    b1 = Barrio(nombre="El Poblado - Provenza", comuna="El Poblado", zona="Suroriental")
    b2 = Barrio(nombre="Laureles Central", comuna="Laureles", zona="Centro Occidental")
    BarrioRepositorio.guardar(b1)
    BarrioRepositorio.guardar(b2)

    # Listado público
    res = client.get("/api/v1/barrios")
    assert res.status_code == 200
    datos = res.get_json()["data"]
    assert len(datos) >= 2

    # Consulta de propiedades por barrio
    res_prop = client.get(f"/api/v1/barrios/{b1.id}/propiedades")
    assert res_prop.status_code == 200
    assert isinstance(res_prop.get_json()["data"], list)
