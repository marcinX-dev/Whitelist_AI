import psycopg2
from psycopg2.extras import DictCursor
import os
from dotenv import load_dotenv

load_dotenv()

POSTGRES_DB_CONFIG = {
    "host": os.getenv("PG_DB_HOST", "localhost"),
    "user": os.getenv("PG_DB_USER", "postgres"),
    "password": os.getenv("PG_DB_PASSWORD"),
    "database": "system",
    "port": int(os.getenv("PG_DB_PORT", 6060)),
}


def get_postgres_connection(database_name=None):
    """Połączenie z bazą danych PostgreSQL z możliwością podania nazwy bazy."""
    config = dict(POSTGRES_DB_CONFIG)  # kopia żeby nie zmieniać globalnego
    if database_name:
        config["database"] = database_name
    conn = psycopg2.connect(
        **config,
        cursor_factory=DictCursor
    )
    conn.autocommit = True
    return conn


def  get_api_key(service_name: str) -> str:
    """
    Zwraca klucz API z bazy danych.
    """
    conn = get_postgres_connection('system')
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT value FROM api_keys WHERE name = %s",(service_name,))
            result = cursor.fetchone()
            if result:
                return result[0]
            else:
                print(f"[ERROR] Brak klucza API dla usługi: {service_name}")
                return None
    finally:
        conn.close()