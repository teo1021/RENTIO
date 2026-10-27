"""
Promueve un usuario a rol de administrador según su correo electrónico.

Uso:
    python scripts/promover_admin.py admin@ejemplo.com
"""

import sys

from app import crear_app
from app.dominios.usuarios.repositorios import UsuarioRepositorio


def main():
    if len(sys.argv) < 2:
        print("Uso: python scripts/promover_admin.py <correo>")
        sys.exit(1)

    correo = sys.argv[1].strip().lower()
    app = crear_app()

    with app.app_context():
        usuario = UsuarioRepositorio.obtener_por_correo(correo)
        if not usuario:
            print(f" Error: Usuario con correo '{correo}' no encontrado.")
            sys.exit(1)

        usuario.rol = "admin"
        UsuarioRepositorio.guardar(usuario)
        print(f" Éxito: Usuario '{correo}' promovido al rol 'admin'.")


if __name__ == "__main__":
    main()
