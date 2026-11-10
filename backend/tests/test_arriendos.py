"""
Tests automatizados para el dominio de arriendos y contratos.
"""

from app.dominios.propiedades.modelos import Propiedad
from app.dominios.propiedades.repositorios import PropiedadRepositorio


def test_flujo_solicitud_y_contrato_arriendo(
    client, propietario_auth, arrendatario_auth, db, monkeypatch
):
    """Verifica el flujo completo de arriendo: solicitud, respuesta del propietario y generación de contrato."""
    propietario = propietario_auth["usuario"]
    headers_prop = propietario_auth["headers"]
    headers_arren = arrendatario_auth["headers"]

    # 1. Crear una propiedad disponible
    propiedad = PropiedadRepositorio.guardar(
        Propiedad(
            titulo="Casa Campestre en Envigado",
            descripcion="Amplios jardines y zona BBQ.",
            precio_mensual=4500000.0,
            direccion="Loma de las Brujas",
            estrato=5,
            habitaciones=3,
            banos=3,
            tipo="casa",
            estado="disponible",
            propietario_id=propietario.id,
        )
    )

    # 2. Arrendatario envía solicitud de arriendo
    res_sol = client.post(
        "/api/v1/arriendos/solicitar",
        headers=headers_arren,
        json={
            "propiedad_id": propiedad.id,
            "mensaje": "Hola, estoy interesado para mudarme pronto.",
            "arrendatario_nombre": "Ana",
            "arrendatario_apellido": "Pérez",
            "arrendatario_cedula": "123456789",
            "arrendatario_telefono": "3001234567",
        },
    )
    assert res_sol.status_code == 201
    sol_data = res_sol.get_json()["data"]
    sol_id = sol_data["id"]
    assert sol_data["estado"] == "pendiente"

    # 3. Validar que no se permita solicitud duplicada pendiente (409)
    res_dup = client.post(
        "/api/v1/arriendos/solicitar",
        headers=headers_arren,
        json={
            "propiedad_id": propiedad.id,
            "arrendatario_nombre": "Ana",
            "arrendatario_apellido": "Pérez",
            "arrendatario_cedula": "123456789",
            "arrendatario_telefono": "3001234567",
        },
    )
    assert res_dup.status_code == 409

    # 4. Propietario consulta solicitudes recibidas
    res_recibidas = client.get(
        "/api/v1/arriendos/solicitudes-recibidas",
        headers=headers_prop,
    )
    assert res_recibidas.status_code == 200
    assert len(res_recibidas.get_json()["data"]) >= 1

    # 5. Propietario acepta la solicitud -> genera contrato y arrienda propiedad
    from app.dominios.arriendos import controladores

    llamada_ia = []
    monkeypatch.setattr(
        controladores,
        "generar_plantilla_contrato",
        lambda: llamada_ia.append(True),
    )
    respuesta_no_autorizada = client.patch(
        f"/api/v1/arriendos/{sol_id}/responder",
        headers=headers_arren,
        json={
            "estado": "aceptada",
            "fecha_inicio": "2026-12-01",
            "fecha_fin": "2027-11-30",
            "precio_acordado": 4500000.0,
        },
    )
    assert respuesta_no_autorizada.status_code == 403
    assert llamada_ia == []

    monkeypatch.setattr(
        controladores,
        "generar_plantilla_contrato",
        lambda: {
            "plantilla": (
                "{{ARRENDADOR_NOMBRE}} {{ARRENDATARIO_NOMBRE}} "
                "{{ARRENDATARIO_CEDULA}} {{ARRENDATARIO_TELEFONO}} "
                "{{INMUEBLE_DIRECCION}} {{INMUEBLE_BARRIO}} "
                "{{FECHA_INICIO}} {{FECHA_FIN}} {{CANON_MENSUAL}}"
            )
        },
    )
    res_resp = client.patch(
        f"/api/v1/arriendos/{sol_id}/responder",
        headers=headers_prop,
        json={
            "estado": "aceptada",
            "fecha_inicio": "2026-12-01",
            "fecha_fin": "2027-11-30",
            "precio_acordado": 4500000.0,
        },
    )
    assert res_resp.status_code == 200
    sol_actualizada = res_resp.get_json()["data"]
    assert sol_actualizada["estado"] == "aceptada"

    # Verificar que la propiedad ahora esté en estado 'arrendada'
    prop_actualizada = PropiedadRepositorio.obtener_por_id(propiedad.id)
    assert prop_actualizada.estado == "arrendada"

    # 6. Consultar contratos formalizados
    res_contratos = client.get(
        "/api/v1/arriendos/contratos",
        headers=headers_arren,
    )
    assert res_contratos.status_code == 200
    contratos = res_contratos.get_json()["data"]
    assert len(contratos) >= 1
    assert contratos[0]["precio_acordado"] == 4500000.0
    assert "123456789" in contratos[0]["contenido"]
    assert "3001234567" in contratos[0]["contenido"]
    assert "$4,500,000 COP" in contratos[0]["contenido"]
