"""
Factory de la aplicación Flask — Arriendos Medellín.

Inicializa la aplicación, extensiones (SQLAlchemy, Migrate, CORS),
registra los blueprints por dominio bajo /api/v1/ e inyecta los servicios.
"""

from flask import Flask, jsonify
from flask_cors import CORS
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from app.config import Config

# ── Instancias a nivel de módulo ─────────────────────────────────────────
db = SQLAlchemy()
migrate = Migrate()


def crear_app(config_class=None):
    """
    Application Factory para crear e inicializar la aplicación Flask.

    Args:
        config_class: Clase o instancia de configuración opcional.

    Returns:
        Flask: Instancia configurada de la aplicación.
    """
    app = Flask(__name__)

    # ── Configuración ────────────────────────────────────────────────────
    if config_class is None:
        config_obj = Config()
        app.config.from_object(config_obj)
    elif isinstance(config_class, type):
        app.config.from_object(config_class())
    else:
        app.config.from_object(config_class)

    # ── Extensiones ──────────────────────────────────────────────────────
    db.init_app(app)
    migrate.init_app(app, db)
    CORS(
        app,
        resources={
            r"/api/*": {"origins": app.config.get("CORS_ALLOWED_ORIGINS", "*")},
            r"/health": {"origins": "*"},
        },
    )

    # ── Importar e inyectar servicios en controladores ────────────────────
    from app.dominios.arriendos import controladores as arriendos_ctrl
    from app.dominios.arriendos.servicios import (
        ArriendoServicio,
        ContratoNoEncontradoError,
        EstadoSolicitudInvalidoError,
        PermisoArriendoError,
        SolicitudDuplicadaError,
        SolicitudNoEncontradaError,
    )
    from app.dominios.barrios import controladores as barrios_ctrl
    from app.dominios.barrios.servicios import (
        BarrioDuplicadoError,
        BarrioNoEncontradoError,
        BarrioServicio,
    )
    from app.dominios.caracteristicas import controladores as caracteristicas_ctrl
    from app.dominios.caracteristicas.servicios import (
        CaracteristicaDuplicadaError,
        CaracteristicaNoEncontradaError,
        CaracteristicaServicio,
    )
    from app.dominios.ia_marketing import controladores as ia_ctrl
    from app.dominios.ia_marketing.servicios import (
        IAMarketingError,
        IAMarketingServicio,
    )
    from app.dominios.propiedades import controladores as propiedades_ctrl
    from app.dominios.propiedades.servicios import (
        PermisoPropiedadError,
        PropiedadNoEncontradaError,
        PropiedadServicio,
    )
    from app.dominios.usuarios import controladores as usuarios_ctrl
    from app.dominios.usuarios.servicios import (
        CorreoYaRegistradoError,
        CredencialesInvalidasError,
        UsuarioNoEncontradoError,
        UsuarioServicio,
    )

    usuarios_ctrl.servicio = UsuarioServicio()
    propiedades_ctrl.servicio = PropiedadServicio()
    caracteristicas_ctrl.servicio = CaracteristicaServicio()
    barrios_ctrl.servicio = BarrioServicio()
    arriendos_ctrl.servicio = ArriendoServicio()
    ia_ctrl.servicio = IAMarketingServicio()

    # ── Registrar Blueprints ─────────────────────────────────────────────
    app.register_blueprint(usuarios_ctrl.usuarios_bp, url_prefix="/api/v1/usuarios")
    app.register_blueprint(usuarios_ctrl.admin_bp, url_prefix="/api/v1/admin")
    app.register_blueprint(propiedades_ctrl.propiedades_bp, url_prefix="/api/v1/propiedades")
    app.register_blueprint(
        caracteristicas_ctrl.caracteristicas_bp, url_prefix="/api/v1/caracteristicas"
    )
    app.register_blueprint(barrios_ctrl.barrios_bp, url_prefix="/api/v1/barrios")
    app.register_blueprint(arriendos_ctrl.arriendos_bp, url_prefix="/api/v1/arriendos")
    app.register_blueprint(ia_ctrl.ia_bp, url_prefix="/api/v1/ia")

    # ── Endpoint de salud ────────────────────────────────────────────────
    @app.route("/health", methods=["GET"])
    def salud():
        """Endpoint público para verificar el estado del servicio."""
        return (
            jsonify(
                {
                    "status": "ok",
                    "app": "Plataforma de Arriendos Medellín API",
                    "version": "1.0.0",
                }
            ),
            200,
        )

    # ── Manejadores de errores globales para excepciones de dominio ──────
    def _crear_error_handler(codigo_http):
        def handler(error):
            return (
                jsonify(
                    {
                        "success": False,
                        "error": {"message": str(error)},
                    }
                ),
                codigo_http,
            )

        return handler

    # 401 Unauthorized
    app.register_error_handler(CredencialesInvalidasError, _crear_error_handler(401))

    # 403 Forbidden
    app.register_error_handler(PermisoPropiedadError, _crear_error_handler(403))
    app.register_error_handler(PermisoArriendoError, _crear_error_handler(403))

    # 404 Not Found
    app.register_error_handler(UsuarioNoEncontradoError, _crear_error_handler(404))
    app.register_error_handler(PropiedadNoEncontradaError, _crear_error_handler(404))
    app.register_error_handler(CaracteristicaNoEncontradaError, _crear_error_handler(404))
    app.register_error_handler(BarrioNoEncontradoError, _crear_error_handler(404))
    app.register_error_handler(SolicitudNoEncontradaError, _crear_error_handler(404))
    app.register_error_handler(ContratoNoEncontradoError, _crear_error_handler(404))

    # 400 Bad Request
    app.register_error_handler(EstadoSolicitudInvalidoError, _crear_error_handler(400))

    # 409 Conflict
    app.register_error_handler(CorreoYaRegistradoError, _crear_error_handler(409))
    app.register_error_handler(CaracteristicaDuplicadaError, _crear_error_handler(409))
    app.register_error_handler(BarrioDuplicadoError, _crear_error_handler(409))
    app.register_error_handler(SolicitudDuplicadaError, _crear_error_handler(409))

    # 502 Bad Gateway / IA Error
    app.register_error_handler(IAMarketingError, _crear_error_handler(502))

    # Handlers HTTP genéricos
    @app.errorhandler(404)
    def no_encontrado(error):
        return (
            jsonify(
                {
                    "success": False,
                    "error": {"message": "El recurso solicitado no fue encontrado."},
                }
            ),
            404,
        )

    @app.errorhandler(405)
    def metodo_no_permitido(error):
        return (
            jsonify(
                {
                    "success": False,
                    "error": {"message": "Método HTTP no permitido para esta ruta."},
                }
            ),
            405,
        )

    @app.errorhandler(500)
    def error_servidor(error):
        return (
            jsonify(
                {
                    "success": False,
                    "error": {"message": "Error interno del servidor."},
                }
            ),
            500,
        )

    return app
