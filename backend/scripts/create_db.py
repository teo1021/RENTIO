"""
Crea la base de datos MySQL a partir de las variables de entorno en .env.

Uso:
    python scripts/create_db.py
"""

import os

import pymysql
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_NAME = os.getenv("DB_NAME", "arriendos_medellin_db")
DB_CHARSET = os.getenv("DB_CHARSET", "utf8mb4")


def main():
    print(f"Conectando al servidor MySQL en {DB_HOST}:{DB_PORT}...")
    try:
        connection = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            charset=DB_CHARSET,
        )
        with connection.cursor() as cursor:
            sql = f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` CHARACTER SET {DB_CHARSET} COLLATE {DB_CHARSET}_unicode_ci;"
            cursor.execute(sql)
            print(f" Base de datos '{DB_NAME}' creada o verificada exitosamente.")
        connection.close()
    except Exception as e:
        print(f" Error al conectar o crear la base de datos: {e}")


if __name__ == "__main__":
    main()
