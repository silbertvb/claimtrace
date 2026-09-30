# Arquitectura de ClaimTrace

Estado a 29 sep 2026 (Bloque 2). Los elementos punteados están previstos y aún
no se han construido.

## Servicios

```mermaid
flowchart LR
    usuario["Reclamación<br/>(formulario simulado)"]
    n8n["n8n<br/>capa de entrada<br/>(Bloque 7, pendiente)"]
    api["api<br/>FastAPI · puerto 8000"]
    db[("db<br/>Postgres + pgvector<br/>puerto 5432")]

    usuario -.-> n8n
    n8n -.-> api
    api --> db
```

| Servicio | Función | Puerto en tu máquina | Puerto interno |
|---|---|---|---|
| `db` | Postgres 16 con pgvector: vectores de políticas y registro de auditoría | 5433 (`POSTGRES_HOST_PORT`) | 5432 |
| `api` | Agente, RAG y LangGraph (Python). Por ahora solo `/health` | 8000 (`API_PORT`) | 8000 |
| `n8n` | Capa de entrada (Bloque 7, pendiente) | 5678 (`N8N_PORT`) | 5678 |

Los puertos se publican solo en `127.0.0.1`. Dentro de la red de Docker, `api`
llega a la base por el nombre del servicio (`db`) y el puerto interno (5432).

## Decisiones

- Base vectorial: pgvector, ver [ADR-001](decisions/001-vector-db.md).

