# Changelog
Todos los cambios relevantes de ClaimTrace. Una entrada por día de trabajo.
(La entrada más reciente va arriba.)

## [Día 5] 2026-10-03 · Renombrado de la aseguradora ficticia

### Cambiado
- La aseguradora ficticia pasa de "Shugo Seguros" a "VERÉGIDA Seguros S.A." (el nombre anterior coincidía con una empresa real de ciberseguridad).
- Prefijo de IDs de cláusula: `SHUGO-` pasa a `VRG-` (por ejemplo, `VRG-CG-HOG-4.2`).
- Usuario de Postgres: `shugo` pasa a `claimtrace`. Obliga a recrear el volumen de la base; no había datos que conservar.


## [Día 4] 2026-10-02 · Plan: ruta ampliada a 12 bloques

- Se añade el Bloque 6 (acceso y roles) y el Bloque 9 (dashboard y métricas, opcional).
- Renumeración de los bloques posteriores. Sin cambios de código.
- Enfocado en añadir capa de seguridad


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
  el Bloque 8.
- Carpeta `docs/` con `architecture.md` (diagrama Mermaid), `usage.md` y el
  ADR-001.

### Cambiado
- El puerto de Postgres publicado en la máquina se separa del puerto interno
  (`POSTGRES_HOST_PORT` frente a `POSTGRES_PORT`), porque el 5432 puede estar
  ocupado por otro Postgres local.

### Decisiones
- ADR-001: elección de la base de datos vectorial (pgvector).