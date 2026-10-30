# Changelog
Todos los cambios relevantes de ClaimTrace. Una entrada por día de trabajo.
(La entrada más reciente va arriba.)

## 2026-10-29 · Bloque 4: migración 001 y ejecutor

### Añadido
- `app/core/migrations.py`: ejecutor de migraciones SQL, lanzable con `python -m app.core.migrations` y enganchado al arranque de la API mediante `lifespan`. Aplica las pendientes en orden, cada una en su transacción junto con su fila de registro, con bloqueo de sesión (`pg_advisory_lock`, clave 40001) y checksum SHA-256 con saltos de línea normalizados a LF (`c2ed762`).
- `services/api/migrations/001-clausulas.sql`: tabla `clausulas`, con todas las columnas `NOT NULL` y `embedding vector(1536)`.
- Tabla de registro `migrations`, creada por el ejecutor.

### Cambiado
- `_conectar()` acepta el parámetro `autocommit` (por defecto `False`, así que `/health` no cambia) y `main.py` aplica las migraciones al arrancar.

### Verificado
- Con la base real: el bloqueo se libera al cerrar la conexión; un `.sql` con varias sentencias se ejecuta sin parámetros dentro de una transacción; un `COMMIT` dentro del `.sql` rompe la atomicidad (de ahí la regla de no incluirlo).
- Dos arranques y dos ejecuciones con `python -m` no repiten la `001`; una migración ya aplicada y editada lanza `ErrorMigracion`; un nombre inválido falla antes de tocar la base; CRLF y LF dan el mismo checksum (comprobado el 30 oct).
- Esquema real: 10 columnas, `embedding` de tipo `vector(1536)`, `clausulas` vacía hasta que exista el indexador.

### Decisiones
- Ver [ADR-004](docs/decisions/004-rag-retrieval.md), D3. La frase del checksum («bytes tal cual») queda desfasada a propósito: el checksum se calcula sobre el contenido normalizado a LF.
- Pendiente para `pytest` (Bloque 10): varias sentencias por archivo con el ejecutor real.

## 2026-10-28 · Bloque 4: migraciones y esquema

### Añadido
- `app/core/db.py`, con `_conectar()` movida desde `main.py` para que el ejecutor y el recuperador no dependan del punto de entrada (`585948d`).

### Cambiado
- Entradas del 25 al 27 oct que faltaban en este archivo (`cd221e8`).
- ADR-004: migraciones concretadas en D3 (`2c14f61`); esquema de `clausulas`, versión de pgvector (0.8.6) y confirmación de `app/core/` (`43696e8`).

### Decisiones
- Ver [ADR-004](docs/decisions/004-rag-retrieval.md), D3 y D5.


## 2026-10-27 · Bloque 4: entorno y decisiones de recuperación

### Añadido
- ADR-004: decisiones de diseño de la recuperación (RAG, parte 1), con índices en `architecture.md` y `decisions/README.md` (`2f2c38e`).
- Limitaciones de las etiquetas y del umbral de abstención en `docs/evaluation.md` (`282bffa`).

### Cambiado
- La imagen de la API pasa a `python:3.13-slim` y las dependencias directas se fijan con versión exacta (`30b7f81`).
- `docs/usage.md` y la regla de Python en `architecture.md` se alinean con la versión del contenedor, 3.13 (`3b0249b`).
- Comentarios explicativos en `evaluation/particionar.py` (`99c7358`).

### Decisiones
- Ver [ADR-004](docs/decisions/004-rag-retrieval.md): D1 a D8 y D7b.

## 2026-10-26 · Bloque 4: partición de las reclamaciones

### Añadido
- Partición estratificada de las 33 reclamaciones: 20 de desarrollo, 9 de evaluación y 4 de regresión (`130b144`).
- Reglas de la partición documentadas en `docs/evaluation.md` (`24d1dfb`).

### Cambiado
- Corregida la ruta de `main.py` en el ADR-003 (`001ad43`).

## 2026-10-25

### Cambiado
- Cifras del caso marcadas como supuestos; definidos los datos de evaluación y la partición (`f4b50ac`).

## 2026-10-24

- Alcance aclarado: reclamaciones de clientes, no siniestros; glosario en `architecture.md` (`fc874fc`).
- Regla «propuesta y ejecución»: el agente solo propone y cerrar exige aprobación registrada (`4a44d41`).
- Regla «seguridad desde el origen del riesgo» (`2c6a0ae`).
- La Fase 3 se cierra al terminar el Bloque 7; las pruebas adversarias se miden allí y se automatizan en el Bloque 10. Roadmap alineado.
- El Bloque 4 incluye una prueba de cambio de versión: modificar una cláusula cambia su hash y reindexar actualiza el registro sin duplicarlo.
- Nombre del Bloque 10 unificado como «Testing del stack Docker completo» en README y Roadmap.

## 2026-10-17 · Bloque 2: entorno de desarrollo local

### Añadido
- Sección "Desarrollo local" en `docs/usage.md` (entorno virtual opcional).
- Problema frecuente en `docs/usage.md`: error de `POSTGRES_PASSWORD` sin definir.
- Comentario de contexto sobre el endpoint `/health` en `services/api/app/main.py`.

### Cambiado
- Los encabezados del changelog usan solo la fecha, sin el número de día.

## 2026-10-12 · Revisión de estructura y licencia

### Añadido
- `.gitattributes`: normaliza los finales de línea a LF para que Windows y WSL vean los mismos cambios.
- `docs/decisions/README.md`: índice de los ADR.

### Cambiado
- `README.md`: sección «Licencia» que indica que es un proyecto de portfolio con todos los derechos reservados y datos ficticios.
- `services/api/main.py` pasa a `services/api/app/main.py` y el Dockerfile arranca `app.main:app`. Sin cambios de comportamiento: `/health` responde igual.

### Decisiones
- Estructura de la API en paquete `app/` con capas bajo demanda; el núcleo no depende de la capa de seguros.
- Los datos de prueba se montarán en la API en solo lectura (`./data:/data:ro`) y la indexación correrá dentro del contenedor; el cambio del compose se hará en el Bloque 4.
- Pruebas del código en `services/api/tests/`, separadas de `evaluation/`.
- Nombres: genérico en inglés; capa de seguros, datos y scripts en español.

## 2026-10-11 · Diagrama del flujo en el Roadmap

### Añadido
- `docs/img/claimtrace-piramide-minto-flujo-e2e.png`: diagrama del flujo de extremo a extremo del MVP (Fases 0 a 3), con un caso ilustrativo ficticio. Es un diseño objetivo y está sujeto a revisión según se cierren los bloques.

### Cambiado
- `docs/roadmap.md`: incluye el diagrama con un pie que indica que es el flujo objetivo y qué está implementado.
- `docs/decisions/001-vector-db.md`: corrección de erratas y del tamaño del corpus («decenas de cláusulas»).

## 2026-10-09 · Roadmap: decisiones y documentación de arquitectura

### Añadido
- `docs/roadmap.md`: versión pública del Roadmap, con fases, bloques, criterio de «hecha» por fase y puntos de decisión.
- ADR-003: núcleo genérico y capa de seguros.
- `docs/architecture.md`: secciones «Reglas de arquitectura» y «Deuda de dominio».
- README: enlaces a la documentación y secciones «Alcance» y «Evaluación».

### Cambiado
- ADR-002: numeración de bloques alineada con el README (Bloque 5 = agente de triage, Bloque 10 = testing del stack completo) y referencia al ADR-003.
- `docs/architecture.md`: estado a 9 oct y `evaluation/` en el diagrama.

### Decisiones
- Enrutado ahora y cobertura como ampliación posterior a la Fase 3.
- Ingesta de PDF como ampliación posterior a la Fase 3, con punto de decisión escrito.
- n8n en la Fase 4; solo transporta, las decisiones y el escalado viven en LangGraph.
- Evaluación repartida por bloques, con código en `evaluation/` fuera de la API; un bloque no se cierra sin su medida.
- Núcleo sin campos de seguros; los nombres de las etiquetas de los JSON se conservan.
- Portfolio ahora; si la Fase 6 sale bien, se decide si continúa más allá.

## 2026-10-08 · Bloque 3: revisión, commit y documentación

### Añadido
- `scripts/generar_datos.py`, `data/polizas.json` (24 pólizas) y `data/usuarios.json` (3 usuarios) en el repositorio.
- ADR-002: formato de los datos de prueba y criterios de etiquetado.

### Cambiado
- Revisión del script: comentarios de las constantes, espaciado y líneas de 120 caracteres como máximo (`pycodestyle` sin avisos). Mismos datos generados que antes (mismos hashes).
- `docs/architecture.md`: estado a 8 oct, mención de `scripts/`, reglas de pólizas canceladas y de `policy_id` nulo, y sección del generador y la validación.

## 2026-10-07 · Bloque 3: comprobaciones del generador de datos

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

## 2026-10-06 · Bloque 3: generador de datos (primera parte)

### Añadido
- `scripts/generar_datos.py` con `generar_polizas` (24 pólizas, semilla 2026), `generar_usuarios` (3 usuarios), `guardar_json` y `cargar_json`.
- `polizas.json` y `usuarios.json` generados por el script en `data/`.

### Cambiado
- El script pasa de `data/` a `scripts/`: `data/` contiene solo datos.

### Decisiones
- La salida es determinista: misma semilla, mismo resultado (comprobado con hash).

## 2026-10-05 · Bloque 3: corpus y reclamaciones

### Añadido
- `data/clausulas.json`: 42 cláusulas (hogar 10, auto 9, comunes 23).
- `data/reclamaciones.json`: 33 reclamaciones etiquetadas.
- Diccionario de datos y convención de IDs en `docs/architecture.md`.

### Cambiado
- Revisión de etiquetas caso por caso: 13 reclamaciones corregidas y 7 criterios fijados.

## 2026-10-03 · Renombrado de la aseguradora ficticia

### Cambiado
- La aseguradora ficticia pasa a llamarse "VERÉGIDA Seguros S.A." (el nombre anterior coincidía con una empresa real de ciberseguridad).
- Prefijo de IDs de cláusula: `SHUGO-` pasa a `VRG-` (por ejemplo, `VRG-CG-HOG-4.2`).
- Usuario de Postgres: `shugo` pasa a `claimtrace`. Obliga a recrear el volumen de la base; no había datos que conservar.


## 2026-10-02 · Plan: ruta ampliada a 12 bloques

- Se añade el Bloque 6 (acceso y roles) y el Bloque 9 (dashboard y métricas, opcional).
- Renumeración de los bloques posteriores. Sin cambios de código.
- Enfocado en añadir capa de seguridad


## 2026-09-30 · Bloque 2: endurecimiento del stack base

### Añadido
- `services/api/.dockerignore`.

### Cambiado
- El compose exige `POSTGRES_PASSWORD`: si falta, no arranca.
- La API corre como usuario sin privilegios (`appuser`) en vez de root.

## 2026-09-29 · Bloque 2: Scaffolding Docker

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