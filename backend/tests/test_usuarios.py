"""
Tests automatizados para el dominio de usuarios y autenticación.
"""


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
