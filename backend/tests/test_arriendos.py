"""
Tests automatizados para el dominio de arriendos y contratos.
"""

from app.dominios.propiedades.modelos import Propiedad
from app.dominios.propiedades.repositorios import PropiedadRepositorio


def test_flujo_solicitud_y_contrato_arriendo(client, propietario_auth, arrendatario_auth, db):
    """Verifica el flujo completo de arriendo: solicitud con datos personales y visita, confirmación de visita y formalización de contrato con info laboral y fiador."""
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

    # 2. Arrendatario envía solicitud con datos personales y fecha propuesta de visita
    res_sol = client.post(
        "/api/v1/arriendos/solicitar",
        headers=headers_arren,
        json={
            "propiedad_id": propiedad.id,
            "mensaje": "Hola, estoy interesado para mudarme pronto.",
            "cedula_arrendatario": "1020304050",
            "telefono_arrendatario": "3001234567",
            "fecha_visita_propuesta": "2026-11-20",
        },
    )
    assert res_sol.status_code == 201
    sol_data = res_sol.get_json()["data"]
    sol_id = sol_data["id"]
    assert sol_data["estado"] == "pendiente_visita"
    assert sol_data["cedula_arrendatario"] == "1020304050"
    assert sol_data["telefono_arrendatario"] == "3001234567"
    assert sol_data["fecha_visita_propuesta"] == "2026-11-20"

    # 3. Validar que no se permita solicitud duplicada activa (409)
    res_dup = client.post(
        "/api/v1/arriendos/solicitar",
        headers=headers_arren,
        json={
            "propiedad_id": propiedad.id,
            "cedula_arrendatario": "1020304050",
            "telefono_arrendatario": "3001234567",
            "fecha_visita_propuesta": "2026-11-21",
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

    # 5. Propietario confirma la visita
    res_visita = client.patch(
        f"/api/v1/arriendos/{sol_id}/responder-visita",
        headers=headers_prop,
        json={
            "estado": "visita_programada",
            "fecha_visita_confirmada": "2026-11-20",
        },
    )
    assert res_visita.status_code == 200
    sol_visita = res_visita.get_json()["data"]
    assert sol_visita["estado"] == "visita_programada"
    assert sol_visita["fecha_visita_confirmada"] == "2026-11-20"

    # 6. Tras la visita, el propietario genera el contrato con información laboral y fiador
    res_contrato = client.post(
        f"/api/v1/arriendos/{sol_id}/generar-contrato",
        headers=headers_prop,
        json={
            "fecha_inicio": "2026-12-01",
            "fecha_fin": "2027-11-30",
            "precio_acordado": 4500000.0,
            "trabaja": True,
            "empresa": "Tech Solutions S.A.S.",
            "cargo": "Desarrollador Senior",
            "ingreso_mensual": 8000000.0,
            "fiador_nombre": "Carlos Gómez",
            "fiador_cedula": "70809010",
            "fiador_telefono": "3119876543",
            "clausulas_adicionales": "Se permite mascota educada.",
        },
    )
    assert res_contrato.status_code == 201
    sol_contrato = res_contrato.get_json()["data"]
    assert sol_contrato["estado"] == "contrato_generado"
    assert sol_contrato["contrato"] is not None
    assert sol_contrato["contrato"]["trabaja"] is True
    assert sol_contrato["contrato"]["empresa"] == "Tech Solutions S.A.S."
    assert sol_contrato["contrato"]["fiador_nombre"] == "Carlos Gómez"
    assert sol_contrato["contrato"]["numero_contrato"].startswith("RNT-")

    # Verificar que la propiedad ahora esté en estado 'arrendada'
    prop_actualizada = PropiedadRepositorio.obtener_por_id(propiedad.id)
    assert prop_actualizada.estado == "arrendada"

    # 7. Consultar contratos formalizados
    res_contratos = client.get(
        "/api/v1/arriendos/contratos",
        headers=headers_arren,
    )
    assert res_contratos.status_code == 200
    contratos = res_contratos.get_json()["data"]
    assert len(contratos) >= 1
    assert contratos[0]["precio_acordado"] == 4500000.0
    assert contratos[0]["cargo"] == "Desarrollador Senior"
