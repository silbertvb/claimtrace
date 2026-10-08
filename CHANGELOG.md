# Changelog
Todos los cambios relevantes de ClaimTrace. Una entrada por día de trabajo.
(La entrada más reciente va arriba.)

## [Día 9] 2026-10-08 · Bloque 3: revisión, commit y documentación

### Añadido
- `scripts/generar_datos.py`, `data/polizas.json` (24 pólizas) y `data/usuarios.json` (3 usuarios) en el repositorio.
- ADR-002: formato de los datos de prueba y criterios de etiquetado.

### Cambiado
- Revisión del script: comentarios de las constantes, espaciado y líneas de 120 caracteres como máximo (`pycodestyle` sin avisos). Mismos datos generados que antes (mismos hashes).
- `docs/architecture.md`: estado a 8 oct, mención de `scripts/`, reglas de pólizas canceladas y de `policy_id` nulo, y sección del generador y la validación.

## [Día 8] 2026-10-07 · Bloque 3: comprobaciones del generador de datos

### Añadido
- 12 comprobaciones de coherencia en `scripts/generar_datos.py`: importe de CLM-0004, fechas de alta, `policy_id` existentes, cláusulas existentes, destino y abstención, totales, cláusulas de fraude, pólizas canceladas, ramo de las cláusulas, recibos duplicados, campos requeridos e importe y mes en el texto.
- `validar()`, que junta los errores de todas las comprobaciones, y `main()`, que valida antes de guardar y termina con código 1 si hay errores (sin escribir nada).

### Decisiones
- El mismo día del alta cuenta como cubierto: error solo si la fecha de la reclamación es anterior al alta.
- Cada problema lo reporta una sola comprobación; las demás lo omiten.
- Primas fijas en las pólizas con recibos en reclamaciones; el resto, con semilla.
- Las pólizas canceladas solo aparecen en casos que citan DEV-3.2, CAN-2.1 o CAN-3.2.
- Una cláusula es válida si es `comun` o coincide con el ramo de la póliza.
- Fraude: FRA-2.1 más una cláusula específica (3.1 o 3.2), comparado como conjunto.
- Ninguna póliza con dos reclamaciones de recibos del mismo mes.
- Los campos vacíos deben coincidir con `campos_faltantes`, y el motivo es `campo_ausente` si y solo si falta algún campo requerido.
- Formatos de cantidades: `importe` es un float con punto en el JSON; los textos usan el formato natural español y se reconcilian con `extraer_importes`.

## [Día 7] 2026-10-06 · Bloque 3: generador de datos (primera parte)

### Añadido
- `scripts/generar_datos.py` con `generar_polizas` (24 pólizas, semilla 2026), `generar_usuarios` (3 usuarios), `guardar_json` y `cargar_json`.
- `polizas.json` y `usuarios.json` generados por el script en `data/`.

### Cambiado
- El script pasa de `data/` a `scripts/`: `data/` contiene solo datos.

### Decisiones
- La salida es determinista: misma semilla, mismo resultado (comprobado con hash).

## [Día 6] 2026-10-05 · Bloque 3: corpus y reclamaciones

### Añadido
- `data/clausulas.json`: 42 cláusulas (hogar 10, auto 9, comunes 23).
- `data/reclamaciones.json`: 33 reclamaciones etiquetadas.
- Diccionario de datos y convención de IDs en `docs/architecture.md`.

### Cambiado
- Revisión de etiquetas caso por caso: 13 reclamaciones corregidas y 7 criterios fijados.

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