"""Crea una base de datos vacía PostgreSQL usando las variables de entorno."""
import os

import psycopg2
from dotenv import load_dotenv
from psycopg2 import sql

load_dotenv()

DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "rentio")


def main():
    print(f"Conectando al servidor PostgreSQL en {DB_HOST}:{DB_PORT}...")
    try:
        connection = psycopg2.connect(
            host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD, dbname="postgres"
        )
        connection.autocommit = True
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_NAME,))
            if cursor.fetchone() is None:
                cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(DB_NAME)))
                print(f"Base de datos '{DB_NAME}' creada.")
            else:
                print(f"La base de datos '{DB_NAME}' ya existe.")
        connection.close()
    except Exception as e:
        raise SystemExit(f"No se pudo crear o verificar la base de datos: {e}") from e


if __name__ == "__main__":
    main()
