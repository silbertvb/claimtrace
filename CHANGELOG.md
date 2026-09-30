# Changelog
Todos los cambios relevantes de ClaimTrace. Una entrada por día de trabajo.
(La entrada más reciente va arriba.)

## [Día 3] 2026-09-30 · Bloque 2: endurecimiento del stack base

### Añadido
- `services/api/.dockerignore`.

### Cambiado
- El compose exige `POSTGRES_PASSWORD`: si falta, no arranca.
- La API corre como usuario sin privilegios (`appuser`) en vez de root.

## [Día 2] 2026-09-29 · Bloque 2: Scaffolding Docker

### Añadido
- `docker-compose.yml` con los servicios `db` (Postgres 16 + pgvector) y `api`
  (FastAPI). `api` espera a que `db` esté sana antes de arrancar.
- `services/api/` con `Dockerfile`, `requirements.txt` y `main.py`, que expone
  `/health` y comprueba la conexión a la base.
- `services/db/init/01-extension.sql`, que activa la extensión `vector`.
- `.env.example` con cada variable comentada. Las de n8n quedan reservadas para
  el Bloque 7.
- Carpeta `docs/` con `architecture.md` (diagrama Mermaid), `usage.md` y el
  ADR-001.

### Cambiado
- El puerto de Postgres publicado en la máquina se separa del puerto interno
  (`POSTGRES_HOST_PORT` frente a `POSTGRES_PORT`), porque el 5432 puede estar
  ocupado por otro Postgres local.

### Decisiones
- ADR-001: elección de la base de datos vectorial (pgvector).