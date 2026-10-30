"""API de ClaimTrace: punto de entrada mínimo del Bloque 2.

Solo expone /health para comprobar que el servicio arranca y llega a la base.
La lógica de negocio (RAG, triage, LangGraph) se añade en bloques posteriores.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from app.core.db import _conectar
from app.core.migrations import aplicar_migraciones

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Aplica las migraciones al arrancar; si una falla, la API no arranca."""
    aplicar_migraciones()
    yield

app = FastAPI(title="ClaimTrace API", lifespan=lifespan)


# PRIMER ENDPOINT DE CLAIMTRACE (Bloque 2/12).
# Sirve para comprobar que la API arranca y que llega a Postgres.
# Prueba: http://127.0.0.1:8000/docs -> GET /health -> Try it out -> Execute.
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