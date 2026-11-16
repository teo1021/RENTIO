"""
Promueve un usuario a rol de administrador según su correo electrónico.

Uso:
    python scripts/promover_admin.py admin@ejemplo.com --confirmar
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import crear_app
from app.dominios.usuarios.repositorios import UsuarioRepositorio


def main():
    parser = argparse.ArgumentParser(
        description="Promueve una cuenta ya registrada a administradora mediante acceso local controlado."
    )
    parser.add_argument("correo", help="Correo de la cuenta que ya fue creada y verificada")
    parser.add_argument(
        "--confirmar",
        action="store_true",
        help="Confirma que el correo corresponde a la cuenta autorizada",
    )
    args = parser.parse_args()
    if not args.confirmar:
        parser.error("la promoción requiere --confirmar")

    correo = args.correo.strip().lower()
    app = crear_app()

    with app.app_context():
        usuario = UsuarioRepositorio.obtener_por_correo(correo)
        if not usuario:
            print(f" Error: Usuario con correo '{correo}' no encontrado.")
            raise SystemExit(1)

        usuario.rol = "admin"
        UsuarioRepositorio.guardar(usuario)
        print(f" Éxito: Usuario '{correo}' promovido al rol 'admin'.")


if __name__ == "__main__":
    main()
