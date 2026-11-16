"""
Punto de entrada de la aplicación — Plataforma de Arriendos Medellín.

Uso:
    python app.py
"""

import os

from app import crear_app

app = crear_app()

# Ruta principal para verificar que el servidor funciona
@app.route("/")
def inicio():
    return {"mensaje": "La API de RENTIO está en ejecución."}

if __name__ == "__main__":
    app.run(
        host=os.getenv("FLASK_HOST", "127.0.0.1"),
        port=int(os.getenv("FLASK_PORT", "5000")),
        debug=os.getenv("FLASK_DEBUG", "false").lower() == "true",
    )