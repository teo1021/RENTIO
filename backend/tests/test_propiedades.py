"""
Tests automatizados para el dominio de propiedades.
"""

from app.dominios.barrios.modelos import Barrio
from app.dominios.barrios.repositorios import BarrioRepositorio
from app.dominios.caracteristicas.modelos import Caracteristica
from app.dominios.caracteristicas.repositorios import CaracteristicaRepositorio
from app.dominios.propiedades.modelos import Propiedad
from app.dominios.propiedades.repositorios import PropiedadRepositorio


def test_crud_completo_propiedades(client, propietario_auth, arrendatario_auth, db):
    """Verifica el ciclo de vida de una propiedad: creación, consulta, filtro, actualización y eliminación."""
    # Crear un barrio y una característica
    barrio = BarrioRepositorio.guardar(
        Barrio(nombre="Manila", comuna="El Poblado", zona="Suroriental")
    )
    caract = CaracteristicaRepositorio.guardar(
        Caracteristica(nombre="Balcón con vista", icono="balcony")
    )

    headers_prop = propietario_auth["headers"]

    # 1. Crear Propiedad
    payload = {
        "titulo": "Apartamento moderno en Manila",
        "descripcion": "Excelente iluminación y acabados de lujo cerca a Provenza.",
        "precio_mensual": 3500000.0,
        "direccion": "Calle 10 # 43E-12",
        "estrato": 5,
        "area_m2": 85.0,
        "habitaciones": 2,
        "banos": 2,
        "tipo": "apartamento",
        "barrio_id": barrio.id,
        "caracteristicas_ids": [caract.id],
    }

    res_crear = client.post("/api/v1/propiedades", headers=headers_prop, json=payload)
    assert res_crear.status_code == 201
    prop_data = res_crear.get_json()["data"]
    prop_id = prop_data["id"]
    assert prop_data["titulo"] == payload["titulo"]
    assert len(prop_data["caracteristicas"]) == 1

    # 2. Consultar por ID
    res_get = client.get(f"/api/v1/propiedades/{prop_id}")
    assert res_get.status_code == 200
    assert res_get.get_json()["data"]["id"] == prop_id

    # 3. Listar con filtros
    res_filtro = client.get(
        "/api/v1/propiedades",
        query_string={"estrato": 5, "tipo": "apartamento", "precio_min": 2000000.0},
    )
    assert res_filtro.status_code == 200
    assert len(res_filtro.get_json()["data"]) >= 1

    # 4. Actualizar parcialmente (dueño)
    res_patch = client.patch(
        f"/api/v1/propiedades/{prop_id}",
        headers=headers_prop,
        json={"precio_mensual": 3800000.0},
    )
    assert res_patch.status_code == 200
    assert res_patch.get_json()["data"]["precio_mensual"] == 3800000.0

    # 5. Intentar actualizar sin ser el dueño (arrendatario -> 403)
    res_fallo = client.patch(
        f"/api/v1/propiedades/{prop_id}",
        headers=arrendatario_auth["headers"],
        json={"precio_mensual": 1000000.0},
    )
    assert res_fallo.status_code == 403

    # 6. Mis propiedades
    res_mis = client.get("/api/v1/propiedades/mis-propiedades", headers=headers_prop)
    assert res_mis.status_code == 200
    assert len(res_mis.get_json()["data"]) >= 1

    # 7. Eliminar propiedad
    res_del = client.delete(f"/api/v1/propiedades/{prop_id}", headers=headers_prop)
    assert res_del.status_code == 200

    # Verificar que ya no existe (404)
    res_get_del = client.get(f"/api/v1/propiedades/{prop_id}")
    assert res_get_del.status_code == 404


def test_solo_admin_puede_consultar_inventario_completo(
    client, admin_auth, propietario_auth, db
):
    propiedad_inactiva = PropiedadRepositorio.guardar(
        Propiedad(
            titulo="Propiedad archivada",
            precio_mensual=1500000,
            direccion="Calle 10",
            estrato=3,
            estado="inactiva",
            propietario_id=propietario_auth["usuario"].id,
        )
    )

    publico = client.get("/api/v1/propiedades")
    assert all(
        item["id"] != propiedad_inactiva.id
        for item in publico.get_json()["data"]
    )

    no_admin = client.get(
        "/api/v1/propiedades/administracion",
        headers=propietario_auth["headers"],
    )
    assert no_admin.status_code == 403

    inventario = client.get(
        "/api/v1/propiedades/administracion",
        headers=admin_auth["headers"],
    )
    assert inventario.status_code == 200
    assert any(
        item["id"] == propiedad_inactiva.id
        for item in inventario.get_json()["data"]
    )


def test_eliminar_propiedad_con_solicitudes(client, propietario_auth, arrendatario_auth, db):
    """Verifica que un propietario pueda eliminar una propiedad aunque tenga solicitudes de arriendo asociadas (cascade)."""
    headers_prop = propietario_auth["headers"]
    headers_arren = arrendatario_auth["headers"]

    # Crear propiedad
    res_crear = client.post(
        "/api/v1/propiedades",
        headers=headers_prop,
        json={
            "titulo": "Apartamento en Laureles",
            "descripcion": "Cerca al primer parque",
            "precio_mensual": 2800000.0,
            "direccion": "Circular 2 # 73-10",
            "estrato": 4,
            "habitaciones": 2,
            "banos": 2,
            "tipo": "apartamento",
        },
    )
    assert res_crear.status_code == 201
    prop_id = res_crear.get_json()["data"]["id"]

    # Arrendatario envía solicitud
    res_sol = client.post(
        "/api/v1/arriendos/solicitar",
        headers=headers_arren,
        json={
            "propiedad_id": prop_id,
            "mensaje": "Quiero arrendar este apartamento",
            "cedula_arrendatario": "987654321",
            "telefono_arrendatario": "3109876543",
            "fecha_visita_propuesta": "2026-11-25",
        },
    )
    assert res_sol.status_code == 201

    # Propietario elimina la propiedad (debe tener éxito con cascade en solicitudes)
    res_del = client.delete(f"/api/v1/propiedades/{prop_id}", headers=headers_prop)
    assert res_del.status_code == 200
    assert "éxito" in res_del.get_json()["message"]

    # Verificar que la propiedad ya no existe
    res_check = client.get(f"/api/v1/propiedades/{prop_id}")
    assert res_check.status_code == 404
