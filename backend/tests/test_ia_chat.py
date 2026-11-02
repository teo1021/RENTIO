"""Pruebas de persistencia del chat de marketing."""


def test_chat_persiste_mensajes_y_resultado(client, propietario_auth, monkeypatch):
    from app.dominios.ia_marketing import controladores

    monkeypatch.setattr(
        controladores,
        "conversar_con_ia",
        lambda mensaje, datos: {
            "datos_actualizados": {"barrio": "Laureles", "tipo": "apartamento", "habitaciones": 2, "banos": 1},
            "datos_extraidos": {"banos": 1},
            "datos_faltantes": [],
            "es_completo": True,
            "respuesta_asistente": "Descripción lista.",
            "resultado_generado": {
                "descripcion_sugerida": "Apartamento de dos habitaciones en Laureles.",
                "precio_estimado": 3400000,
                "precio_minimo": 3000000,
                "precio_maximo": 5200000,
                "moneda": "COP",
                "metadatos_calculo": {"version_fuente": "test"},
            },
        },
    )
    headers = propietario_auth["headers"]
    creado = client.post("/api/v1/ia/conversaciones", headers=headers, json={})
    assert creado.status_code == 201
    cid = creado.get_json()["data"]["id"]
    envio = client.post(
        f"/api/v1/ia/conversaciones/{cid}/mensajes",
        headers=headers,
        json={"mensaje": "Apartamento en Laureles, dos habitaciones y un baño"},
    )
    assert envio.status_code == 200
    recuperado = client.get(f"/api/v1/ia/conversaciones/{cid}", headers=headers)
    assert recuperado.status_code == 200
    data = recuperado.get_json()["data"]
    assert len(data["mensajes"]) == 2
    assert len(data["resultados"]) == 1
    assert data["estado"] == "lista"


def test_chat_rechaza_mensaje_vacio(client, propietario_auth):
    headers = propietario_auth["headers"]
    cid = client.post("/api/v1/ia/conversaciones", headers=headers, json={}).get_json()["data"]["id"]
    response = client.post(
        f"/api/v1/ia/conversaciones/{cid}/mensajes", headers=headers, json={"mensaje": "  "}
    )
    assert response.status_code == 400


def test_otro_propietario_no_puede_leer_conversacion(client, propietario_auth):
    import uuid

    from app import db
    from app.dominios.ia_marketing.modelos import ConversacionMarketing
    from app.dominios.usuarios.servicios import UsuarioServicio

    segundo = UsuarioServicio.registrar({
        "correo": f"otro_{uuid.uuid4().hex[:8]}@rentio.com",
        "contrasena": "Password123*",
        "rol": "propietario",
        "nombre": "Otro",
        "apellido": "Propietario",
    })
    conversacion = ConversacionMarketing(
        propietario_id=propietario_auth["usuario"].id,
        datos_recopilados={},
    )
    db.session.add(conversacion)
    db.session.commit()
    token = UsuarioServicio.login({"correo": segundo.correo, "contrasena": "Password123*"})["token"]
    response = client.get(
        f"/api/v1/ia/conversaciones/{conversacion.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404
