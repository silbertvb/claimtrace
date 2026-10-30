"""Acceso a Postgres: único punto por el que la API abre conexiones (ADR-004, D4)."""
import os

import psycopg


def _conectar(autocommit: bool = False) -> psycopg.Connection:
    """Abre una conexión a Postgres con las variables de entorno.

    Parámetros:
        autocommit: si es True, cada sentencia se confirma sola y las
        transacciones solo existen dentro de `conn.transaction()`.
        Por defecto False, que es el comportamiento que usa /health.

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
        autocommit=autocommit,
    )