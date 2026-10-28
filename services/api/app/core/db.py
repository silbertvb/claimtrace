"""Acceso a Postgres: único punto por el que la API abre conexiones (ADR-004, D4)."""
import os

import psycopg


def _conectar() -> psycopg.Connection:
    """Abre una conexión a Postgres con las variables de entorno.

    Devuelve:
        Conexión abierta. Quien la llama debe cerrarla.
    """
    return psycopg.connect(
        host=os.environ["POSTGRES_HOST"],
        port=os.environ["POSTGRES_PORT"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        dbname=os.environ["POSTGRES_DB"],
        connect_timeout=3,
    )