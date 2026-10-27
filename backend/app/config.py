"""
Configuración de la aplicación.

Lee variables de entorno desde .env y construye la configuración
de Flask y SQLAlchemy.
"""

import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuración central de la aplicación, leída desde variables de entorno."""

    # ── Modo testing ────────────────────────────────────────────────────
    TESTING = os.getenv("FLASK_TESTING", "false").lower() == "true"

    # ── Seguridad ───────────────────────────────────────────────────────
    SECRET_KEY = os.getenv("SECRET_KEY", "clave_segura_123")
    JWT_EXP_MINUTES = int(os.getenv("JWT_EXP_MINUTES", "15"))

    # ── CORS ────────────────────────────────────────────────────────────
    CORS_ALLOWED_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS", "*")

    # ── Base de datos ───────────────────────────────────────────────────
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "bedoya1021")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5433")
    DB_NAME = os.getenv("DB_NAME", "rentio_electiva_3")
    DB_CHARSET = os.getenv("DB_CHARSET", "utf8mb4")

    # ── Inteligencia Artificial ─────────────────────────────────────────
    AI_PROVIDER = os.getenv("AI_PROVIDER", "openai")
    AI_API_KEY = os.getenv("AI_API_KEY", "")
    AI_MODEL = os.getenv("AI_MODEL", "gpt-4o-mini")

    # ── SQLAlchemy ──────────────────────────────────────────────────────
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    def __init__(self):
        """Construye la URI de la BD y valida variables obligatorias."""
        if self.TESTING:
            self.SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
            if not self.SECRET_KEY:
                self.SECRET_KEY = "clave-secreta-de-testing"
        else:
            self._validar_obligatorias()
            # CONEXIÓN CORREGIDA PARA POSTGRESQL
            self.SQLALCHEMY_DATABASE_URI = (
                f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASSWORD}"
                f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            )

    def _validar_obligatorias(self):
        """Lanza ValueError si falta alguna variable obligatoria."""
        faltantes = []
        if not self.DB_USER:
            faltantes.append("DB_USER")
        if not self.DB_NAME:
            faltantes.append("DB_NAME")
        if not self.SECRET_KEY:
            faltantes.append("SECRET_KEY")
        if faltantes:
            raise ValueError(
                f"Variables de entorno obligatorias faltantes: {', '.join(faltantes)}. "
                "Revisa el archivo .env"
            )