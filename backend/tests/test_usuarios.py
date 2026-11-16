"""
Tests automatizados para el dominio de usuarios y autenticación.
"""

import hashlib

from werkzeug.security import check_password_hash

from app import db
from app.dominios.usuarios.modelos import Usuario


def test_health_check(client):
    """Verifica que el endpoint de salud responda con 200 y JSON correcto."""
    res = client.get("/health")
    assert res.status_code == 200
    datos = res.get_json()
    assert datos["status"] == "ok"


def test_registro_usuario_exitoso(client):
    """Verifica el registro exitoso de un arrendatario."""
    payload = {
        "correo": "arrendatario1@rentio.com",
        "contrasena": "Secreta123*",
        "rol": "arrendatario",
        "nombre": "Carlos",
        "apellido": "Gómez",
    }
    res = client.post("/api/v1/usuarios/registro", json=payload)
    assert res.status_code == 201
    datos = res.get_json()
    assert datos["success"] is True
    assert datos["data"]["correo"] == payload["correo"]
    assert datos["data"]["rol"] == "arrendatario"
    assert "contrasena" not in datos["data"]
    usuario = Usuario.query.filter_by(correo=payload["correo"]).one()
    assert usuario.contrasena != hashlib.sha256(payload["contrasena"].encode()).hexdigest()
    assert check_password_hash(usuario.contrasena, payload["contrasena"])


def test_registro_no_permite_rol_admin(client):
    res = client.post(
        "/api/v1/usuarios/registro",
        json={
            "correo": "no-admin@rentio.com",
            "contrasena": "Secreta123*",
            "rol": "admin",
        },
    )
    assert res.status_code == 400


def test_registro_usuario_correo_duplicado(client):
    """Verifica que no se permita registrar dos veces el mismo correo."""
    payload = {
        "correo": "duplicado@rentio.com",
        "contrasena": "Secreta123*",
        "rol": "propietario",
    }
    res1 = client.post("/api/v1/usuarios/registro", json=payload)
    assert res1.status_code == 201

    res2 = client.post("/api/v1/usuarios/registro", json=payload)
    assert res2.status_code == 409
    datos = res2.get_json()
    assert datos["success"] is False


def test_login_exitoso(client):
    """Verifica el login con credenciales válidas."""
    payload = {
        "correo": "login_test@rentio.com",
        "contrasena": "Password123*",
        "rol": "arrendatario",
    }
    client.post("/api/v1/usuarios/registro", json=payload)

    login_res = client.post(
        "/api/v1/usuarios/login",
        json={"correo": payload["correo"], "contrasena": payload["contrasena"]},
    )
    assert login_res.status_code == 200
    datos = login_res.get_json()
    assert datos["success"] is True
    assert "token" in datos["data"]
    assert datos["data"]["usuario"]["correo"] == payload["correo"]


def test_login_migra_hash_sha256_heredado(client):
    correo = "hash-antiguo@rentio.com"
    contrasena = "Password123*"
    client.post(
        "/api/v1/usuarios/registro",
        json={"correo": correo, "contrasena": contrasena, "rol": "arrendatario"},
    )
    usuario = Usuario.query.filter_by(correo=correo).one()
    usuario.contrasena = hashlib.sha256(contrasena.encode()).hexdigest()
    db.session.commit()

    respuesta = client.post(
        "/api/v1/usuarios/login",
        json={"correo": correo, "contrasena": contrasena},
    )

    assert respuesta.status_code == 200
    assert check_password_hash(usuario.contrasena, contrasena)
    assert usuario.contrasena != hashlib.sha256(contrasena.encode()).hexdigest()


def test_login_credenciales_invalidas(client):
    """Verifica error 401 ante contraseña incorrecta."""
    payload = {
        "correo": "fallo_login@rentio.com",
        "contrasena": "Password123*",
        "rol": "arrendatario",
    }
    client.post("/api/v1/usuarios/registro", json=payload)

    login_res = client.post(
        "/api/v1/usuarios/login",
        json={"correo": payload["correo"], "contrasena": "PasswordErronea!"},
    )
    assert login_res.status_code == 401
    datos = login_res.get_json()
    assert datos["success"] is False


def test_obtener_y_actualizar_perfil(client, arrendatario_auth):
    """Verifica la consulta y actualización del perfil con token JWT."""
    headers = arrendatario_auth["headers"]

    # Consulta
    res = client.get("/api/v1/usuarios/perfil", headers=headers)
    assert res.status_code == 200
    datos = res.get_json()
    assert datos["success"] is True

    # Actualización parcial
    patch_res = client.patch(
        "/api/v1/usuarios/perfil",
        headers=headers,
        json={"telefono": "3001234567", "cedula": "1035000111"},
    )
    assert patch_res.status_code == 200
    perfil = patch_res.get_json()["data"]["perfil"]
    assert perfil["telefono"] == "3001234567"
    assert perfil["cedula"] == "1035000111"


def test_admin_usuarios_y_cambiar_rol(client, admin_auth, arrendatario_auth):
    """Verifica que un administrador pueda listar usuarios y modificar roles."""
    headers_admin = admin_auth["headers"]
    usuario_target = arrendatario_auth["usuario"]

    # Listar usuarios
    res = client.get("/api/v1/admin/usuarios", headers=headers_admin)
    assert res.status_code == 200
    assert len(res.get_json()["data"]) >= 2

    # Cambiar rol
    patch_res = client.patch(
        f"/api/v1/admin/usuarios/{usuario_target.id}/rol",
        headers=headers_admin,
        json={"rol": "propietario"},
    )
    assert patch_res.status_code == 200
    assert patch_res.get_json()["data"]["rol"] == "propietario"


def test_admin_no_puede_asignar_ni_modificar_rol_admin(
    client, admin_auth, arrendatario_auth, db
):
    headers_admin = admin_auth["headers"]
    usuario_admin = admin_auth["usuario"]
    usuario_objetivo = arrendatario_auth["usuario"]

    intento_usuario_normal = client.patch(
        f"/api/v1/admin/usuarios/{usuario_objetivo.id}/rol",
        headers=arrendatario_auth["headers"],
        json={"rol": "admin"},
    )
    assert intento_usuario_normal.status_code == 403

    asignar_admin = client.patch(
        f"/api/v1/admin/usuarios/{usuario_objetivo.id}/rol",
        headers=headers_admin,
        json={"rol": "admin"},
    )
    assert asignar_admin.status_code == 400

    cambiar_propio_rol = client.patch(
        f"/api/v1/admin/usuarios/{usuario_admin.id}/rol",
        headers=headers_admin,
        json={"rol": "propietario"},
    )
    assert cambiar_propio_rol.status_code == 403

    usuario_objetivo.rol = "admin"
    db.session.commit()
    cambiar_otro_admin = client.patch(
        f"/api/v1/admin/usuarios/{usuario_objetivo.id}/rol",
        headers=headers_admin,
        json={"rol": "arrendatario"},
    )
    assert cambiar_otro_admin.status_code == 403


def test_autorizacion_usa_rol_actual_de_base_de_datos(client, arrendatario_auth):
    usuario = arrendatario_auth["usuario"]
    headers = arrendatario_auth["headers"]

    usuario.rol = "propietario"
    db.session.commit()
    assert client.get("/api/v1/propiedades/mis-propiedades", headers=headers).status_code == 200

    usuario.rol = "arrendatario"
    db.session.commit()
    assert client.get("/api/v1/propiedades/mis-propiedades", headers=headers).status_code == 403


def test_listado_admin_no_expone_datos_sensibles(client, admin_auth, arrendatario_auth):
    perfil = arrendatario_auth["usuario"].perfil
    perfil.telefono = "3001234567"
    perfil.cedula = "1035000111"
    db.session.commit()

    respuesta = client.get("/api/v1/admin/usuarios", headers=admin_auth["headers"])
    usuario = next(
        item
        for item in respuesta.get_json()["data"]
        if item["id"] == arrendatario_auth["usuario"].id
    )

    assert respuesta.status_code == 200
    assert "telefono" not in usuario["perfil"]
    assert "cedula" not in usuario["perfil"]
