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


def test_crear_barrio_requiere_admin_y_persiste(client, db, admin_auth):
    respuesta = client.post(
        "/api/v1/barrios",
        headers=admin_auth["headers"],
        json={"nombre": "Barrio de Prueba", "comuna": "Comuna 8", "zona": "Centro"},
    )
    assert respuesta.status_code == 201
    guardado = respuesta.get_json()["data"]
    assert guardado["nombre"] == "Barrio de Prueba"
    assert guardado["id"] is not None
    assert db.session.get(Barrio, guardado["id"]) is not None


def test_actualizar_barrio_conserva_relacion_y_rechaza_duplicado(
    client, db, admin_auth
):
    original = Barrio(nombre="Barrio Original", comuna="Comuna 1", zona="Norte")
    duplicado = Barrio(nombre="Barrio Existente", comuna="Comuna 1", zona="Norte")
    BarrioRepositorio.guardar(original)
    BarrioRepositorio.guardar(duplicado)

    respuesta = client.patch(
        f"/api/v1/barrios/{original.id}",
        headers=admin_auth["headers"],
        json={
            "nombre": "Barrio Corregido",
            "comuna": "Comuna 2",
            "zona": "Centro",
        },
    )
    assert respuesta.status_code == 200
    assert respuesta.get_json()["data"]["nombre"] == "Barrio Corregido"
    assert db.session.get(Barrio, original.id).id == original.id

    duplicado_response = client.patch(
        f"/api/v1/barrios/{original.id}",
        headers=admin_auth["headers"],
        json={
            "nombre": "BARRIO EXISTENTE",
            "comuna": "comuna 1",
            "zona": "Norte",
        },
    )
    assert duplicado_response.status_code == 409


def test_actualizar_barrio_requiere_administrador(client, arrendatario_auth):
    barrio = Barrio(nombre="Barrio Seguro", comuna="Comuna 3", zona="Sur")
    BarrioRepositorio.guardar(barrio)

    respuesta = client.patch(
        f"/api/v1/barrios/{barrio.id}",
        headers=arrendatario_auth["headers"],
        json={
            "nombre": "Barrio Modificado",
            "comuna": "Comuna 3",
            "zona": "Sur",
        },
    )
    assert respuesta.status_code == 403
