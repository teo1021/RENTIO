"""
Configuración central y fixtures de pytest para Arriendos Medellín API.

Utiliza SQLite en memoria y tokens JWT generados dinámicamente para pruebas.
"""

import os
import sys
import uuid
from pathlib import Path

import pytest

# Asegurar que el directorio backend esté en sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# ── Variables de entorno configuradas antes de importar la app ───────────
os.environ["FLASK_TESTING"] = "true"
os.environ["SECRET_KEY"] = "clave-secreta-para-tests-arriendos-medellin"
os.environ["JWT_EXP_MINUTES"] = "60"

from app import crear_app
from app import db as _db
from app.dominios.usuarios.servicios import UsuarioServicio


@pytest.fixture(scope="session")
def app():
    """Fixture de la aplicación Flask para toda la sesión de pruebas."""
    _app = crear_app()
    _app.config["TESTING"] = True
    _app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    return _app


@pytest.fixture(scope="function")
def db(app):
    """Fixture que crea y destruye las tablas por cada test."""
    with app.app_context():
        _db.create_all()
        yield _db
        _db.session.remove()
        _db.drop_all()


@pytest.fixture(scope="function")
def client(app, db):
    """Cliente HTTP de prueba para realizar peticiones."""
    return app.test_client()


def _crear_usuario_y_token(rol="arrendatario"):
    """Crea un usuario único y retorna su instancia y token JWT."""
    uid = uuid.uuid4().hex[:8]
    datos = {
        "correo": f"test_{rol}_{uid}@rentio.com",
        "contrasena": "Password123*",
        "rol": rol,
        "nombre": f"Test {rol.capitalize()}",
        "apellido": "Medellín",
    }
    usuario = UsuarioServicio.registrar(datos)
    token = UsuarioServicio.login({"correo": datos["correo"], "contrasena": datos["contrasena"]})[
        "token"
    ]
    return usuario, token


@pytest.fixture
def arrendatario_auth(db):
    """Fixture para un usuario autenticado con rol arrendatario."""
    usuario, token = _crear_usuario_y_token("arrendatario")
    return {"usuario": usuario, "token": token, "headers": {"Authorization": f"Bearer {token}"}}


@pytest.fixture
def propietario_auth(db):
    """Fixture para un usuario autenticado con rol propietario."""
    usuario, token = _crear_usuario_y_token("propietario")
    return {"usuario": usuario, "token": token, "headers": {"Authorization": f"Bearer {token}"}}


@pytest.fixture
def admin_auth(db):
    """Fixture para un usuario autenticado con rol admin."""
    usuario, _ = _crear_usuario_y_token("arrendatario")
    usuario.rol = "admin"
    _db.session.commit()
    token = UsuarioServicio.login({"correo": usuario.correo, "contrasena": "Password123*"})["token"]
    return {"usuario": usuario, "token": token, "headers": {"Authorization": f"Bearer {token}"}}
