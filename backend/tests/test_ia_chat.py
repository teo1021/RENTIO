"""Pruebas de persistencia del chat de marketing."""


def test_chat_persiste_mensajes_y_resultado(client, propietario_auth, monkeypatch):
    from app.dominios.ia_marketing import controladores

    monkeypatch.setattr(
        controladores,
        "conversar_con_ia",
        lambda mensaje, datos, historial=None: {
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
    assert data["estado"] == "recopilando"


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


def test_confirmar_registro_guarda_propiedad_y_fotografias_en_una_operacion(
    app, client, propietario_auth, monkeypatch, tmp_path
):
    import json
    from io import BytesIO

    from app import db
    from app.dominios.barrios.modelos import Barrio
    from app.dominios.caracteristicas.modelos import Caracteristica
    from app.dominios.ia_marketing.modelos import ConversacionMarketing
    from app.dominios.propiedades.modelos import Propiedad

    monkeypatch.setitem(app.config, "PROPERTY_IMAGE_FOLDER", str(tmp_path))
    barrio = Barrio(nombre="Laureles", comuna="11", zona="Centro-occidental")
    cocina = Caracteristica(nombre="Cocina integral")
    db.session.add_all([barrio, cocina])
    db.session.flush()
    conversacion = ConversacionMarketing(
        propietario_id=propietario_auth["usuario"].id,
        estado="lista",
        datos_recopilados={
            "barrio": "Laureles",
            "tipo": "apartamento",
            "habitaciones": 3,
            "banos": 2,
            "direccion": "Calle 30 # 80-25",
            "estrato": 4,
            "precio_mensual": 2_000_000,
            "canon_confirmado": True,
            "area_m2": 85,
            "caracteristicas": ["Cocina integral"],
        },
    )
    db.session.add(conversacion)
    db.session.commit()

    response = client.post(
        f"/api/v1/ia/conversaciones/{conversacion.id}/crear-propiedad",
        headers=propietario_auth["headers"],
        data={
            "datos": json.dumps({"titulo": "Apartamento en Laureles"}),
            "imagenes": [(BytesIO(b"test image bytes"), "sala.png", "image/png")],
        },
        content_type="multipart/form-data",
    )
    assert response.status_code == 201
    property_data = response.get_json()["data"]
    assert property_data["propietario_id"] == propietario_auth["usuario"].id
    assert property_data["precio_mensual"] == 2_000_000
    assert property_data["barrio"]["nombre"] == "Laureles"
    assert [item["nombre"] for item in property_data["caracteristicas"]] == ["Cocina integral"]
    assert len(property_data["imagenes"]) == 1
    filename = property_data["imagenes"][0]["url"].rsplit("/", 1)[-1]
    assert (tmp_path / filename).exists()
    assert conversacion.propiedad_id == property_data["id"]
    assert Propiedad.query.count() == 1

    repeated = client.post(
        f"/api/v1/ia/conversaciones/{conversacion.id}/crear-propiedad",
        headers=propietario_auth["headers"],
        json={},
    )
    assert repeated.status_code == 200
    assert Propiedad.query.count() == 1


def test_confirmar_registro_guarda_ubicacion_manual_como_sector(
    app, client, propietario_auth
):
    from app import db
    from app.dominios.ia_marketing.modelos import ConversacionMarketing

    conversacion = ConversacionMarketing(
        propietario_id=propietario_auth["usuario"].id,
        estado="lista",
        datos_recopilados={
            "barrio": "La Arboleda",
            "barrio_comuna": "Comuna 15",
            "tipo": "apartamento",
            "habitaciones": 2,
            "banos": 1,
            "direccion": "Calle 10 # 50-20",
            "estrato": 4,
            "precio_mensual": 1_800_000,
            "canon_confirmado": True,
        },
    )
    db.session.add(conversacion)
    db.session.commit()

    response = client.post(
        f"/api/v1/ia/conversaciones/{conversacion.id}/crear-propiedad",
        headers=propietario_auth["headers"],
        json={"titulo": "Apartamento en La Arboleda"},
    )

    assert response.status_code == 201
    ubicacion = response.get_json()["data"]["barrio"]
    assert ubicacion["nombre"] == "La Arboleda"
    assert ubicacion["comuna"] == "Comuna 15"
    assert ubicacion["tipo"] == "sector"


def test_confirmar_registro_ignora_puntuacion_del_nombre_oficial(
    app, client, propietario_auth
):
    from app import db
    from app.dominios.barrios.modelos import Barrio
    from app.dominios.ia_marketing.modelos import ConversacionMarketing

    barrio = Barrio(
        nombre="El Nogal-Los Almendros",
        comuna="Comuna 16 - Belén",
        zona="Suroccidental",
    )
    db.session.add(barrio)
    db.session.flush()
    conversacion = ConversacionMarketing(
        propietario_id=propietario_auth["usuario"].id,
        estado="lista",
        datos_recopilados={
            "barrio": "El Nogal Los Almendros",
            "barrio_comuna": "Comuna 16",
            "tipo": "apartamento",
            "habitaciones": 2,
            "banos": 1,
            "direccion": "Calle 10 # 50-20",
            "estrato": 4,
            "precio_mensual": 1_800_000,
            "canon_confirmado": True,
        },
    )
    db.session.add(conversacion)
    db.session.commit()

    response = client.post(
        f"/api/v1/ia/conversaciones/{conversacion.id}/crear-propiedad",
        headers=propietario_auth["headers"],
        json={"titulo": "Apartamento en El Nogal"},
    )

    assert response.status_code == 201
    assert response.get_json()["data"]["barrio"]["id"] == barrio.id
    assert response.get_json()["data"]["barrio"]["tipo"] == "barrio"


def test_confirmar_registro_rechaza_datos_obligatorios_incompletos(
    client, propietario_auth
):
    from app import db
    from app.dominios.ia_marketing.modelos import ConversacionMarketing

    conversacion = ConversacionMarketing(
        propietario_id=propietario_auth["usuario"].id,
        estado="lista",
        datos_recopilados={
            "barrio": "Laureles",
            "tipo": "apartamento",
            "habitaciones": 2,
            "banos": 1,
            "direccion": "Calle 30 # 80-25",
            "estrato": 4,
        },
    )
    db.session.add(conversacion)
    db.session.commit()

    response = client.post(
        f"/api/v1/ia/conversaciones/{conversacion.id}/crear-propiedad",
        headers=propietario_auth["headers"],
        json={},
    )
    assert response.status_code == 400
    assert "precio_mensual" in response.get_json()["error"]["details"]["faltantes"]


def test_fallo_de_conexion_ia_se_devuelve_como_servicio_no_disponible(
    app, client, propietario_auth, monkeypatch
):
    from app import db
    from app.dominios.ia_marketing.modelos import ConversacionMarketing

    conversacion = ConversacionMarketing(
        propietario_id=propietario_auth["usuario"].id,
        datos_recopilados={},
    )
    db.session.add(conversacion)
    db.session.commit()
    monkeypatch.setitem(app.config, "AI_SERVICE_URL", "http://127.0.0.1:1")
    monkeypatch.setitem(app.config, "AI_INTERNAL_API_KEY", "local-test-key")

    response = client.post(
        f"/api/v1/ia/conversaciones/{conversacion.id}/mensajes",
        headers=propietario_auth["headers"],
        json={"mensaje": "Apartamento en Laureles"},
    )
    assert response.status_code == 503
    assert "puerto 5001" in response.get_json()["error"]["message"]
