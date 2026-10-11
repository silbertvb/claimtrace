"""API de ClaimTrace: punto de entrada mínimo del Bloque 2.

Solo expone /health para comprobar que el servicio arranca y llega a la base.
La lógica de negocio (RAG, triage, LangGraph) se añade en bloques posteriores.
"""
import os

import psycopg
from fastapi import FastAPI, HTTPException

app = FastAPI(title="ClaimTrace API")


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


@app.get("/health")
def health() -> dict:
    """Comprueba que la API está viva y que llega a la base de datos.

    Devuelve:
        {"status": "ok", "db": "ok"} si todo responde.

    Lanza:
        HTTPException 503 si no se puede consultar la base.
    """
    try:
        with _conectar() as conn:
            conn.execute("SELECT 1")
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"db no disponible: {type(exc).__name__}")
    return {"status": "ok", "db": "ok"}