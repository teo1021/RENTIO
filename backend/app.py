"""
Punto de entrada de la aplicación — Plataforma de Arriendos Medellín.

Uso:
    python app.py
"""

from app import crear_app

app = crear_app()

# Ruta principal para verificar que el servidor funciona
@app.route("/")
def inicio():
    return {"mensaje": "¡Backend conectado a PostgreSQL exitosamente!"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)