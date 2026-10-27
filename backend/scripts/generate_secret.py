"""
Genera una clave secreta segura para SECRET_KEY.

Uso:
    python scripts/generate_secret.py
"""

import secrets


def main():
    clave = secrets.token_hex(32)
    print("=" * 60)
    print("SECRET_KEY generada:")
    print(clave)
    print("=" * 60)
    print("Copia este valor en tu archivo .env en la variable SECRET_KEY.")


if __name__ == "__main__":
    main()
