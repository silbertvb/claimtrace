# ADR-004: Decisiones de diseño de la recuperación (RAG, parte 1)

- **Estado:** aceptada
- **Fecha:** 2026-10-27
- **Bloque:** 4. RAG (parte 1)
- **Afecta a:** Bloque 4 (esquema, indexación, `/retrieve` y medida),
  Bloque 5 (generación con citas y validador), Bloque 7 (rol de la base de
  datos, ADR-005), Bloque 10 (testing)
- **Relacionada con:** ADR-001 (pgvector), ADR-002 (formato de los datos),
  ADR-003 (núcleo genérico)

## Contexto
El Bloque 4 indexa las 42 cláusulas de `data/clausulas.json`, las recupera por
similitud con un filtro obligatorio por ramo y mide la calidad de esa
recuperación. Solo recupera: la generación con citas y el validador de citas
son del Bloque 5.

Antes de escribir código se cerraron las decisiones que recoge este ADR, para
que el esquema, la API y la evaluación se construyan sobre ellas. Punto de
partida: una cláusula es un fragmento (97 a 443 caracteres), sin troceado; la
búsqueda es exacta y sin índice (42 filas); y las 33 reclamaciones se
repartieron el 26 oct de forma fija (commit `130b144`): 20 de desarrollo, 9 de
evaluación y 4 de regresión. El filtro por ramo es una condición `WHERE`
obligatoria, no una preferencia de orden: `HOG-7.1`/`AUTO-7.1` y
`HOG-7.2`/`AUTO-7.2` tienen textos idénticos, y por tanto vectores idénticos
(lo usa `CLM-0014`, que espera `HOG-7.2`).

## Decisiones

### D1. Modelo de embeddings
- **Decisión:** `text-embedding-3-small`, 1536 dimensiones. La columna será
  `vector(1536)`. Al indexar se registran modelo, dimensiones, hash y fecha,
  de modo que cambiar de modelo es reindexar.
- **Descartadas:** `text-embedding-3-large` (3072 dimensiones, no cabe en un
  índice `vector`, que llega a 2.000; con 42 filas no hace falta índice) y un
  modelo local (instalación pesada y compatibilidad sin verificar).
- **Motivo:** es el modelo que se conoce, el coste es irrelevante (del orden
  de 0,0001 $ por pasada completa, estimación) y los datos son ficticios.
- **Pendiente:** compararlo con `3-large` usando los casos de desarrollo (con
  `dimensions=1536` o en memoria, dentro de `evaluation/`). Si más adelante se
  ingieren PDF, se reevalúa.

### D2. Medida de la recuperación
- **Distancia:** coseno (`<=>`); similitud = 1 − distancia. Con vectores
  normalizados, coseno, L2 y producto escalar ordenan igual; se elige coseno
  porque su valor se lee como similitud, útil para el umbral (D8).
- **Métrica principal:** recall@k. **Secundaria:** porcentaje de casos con
  **todas** las cláusulas esperadas recuperadas. Descartadas como principal:
  acierto@k (acertar una sola no basta cuando 14 casos esperan dos o tres),
  precisión@k (sale baja por diseño) y MRR.
- **Elección de k:** el más pequeño a partir del cual el recall en desarrollo
  deja de mejorar. Se probará de k = 1 a 10 y se concreta al medir. Con 20
  casos de desarrollo, una diferencia de un caso es ruido.
- **Casos de abstención:** quedan fuera de estas métricas (no tienen cláusulas
  esperadas) y se miden con el umbral (D8).
- **Cláusulas esperadas por reclamación (33):** 9 con ninguna (las
  abstenciones), 10 con una, 12 con dos y 2 con tres. `CLM-0016` es de
  regresión, así que entre los casos medidos solo `CLM-0027` exige k ≥ 3 en
  la métrica estricta.
- **Limitación de las etiquetas:** `CAN-2.1` remite a `DEV-3.2` para los
  cobros posteriores a la baja, y las etiquetas usan `DEV-3.2` en `CLM-0002` y
  `CLM-0005` y `CAN-2.1` en `CLM-0023` y `CLM-0027`. Con una sola etiqueta por
  caso, si la recuperación devolviera la otra cláusula sería correcta en el
  fondo pero contaría como fallo. Las etiquetas no se cambian; se anota en
  `docs/evaluation.md`.
- **Casos de evaluación:** se miran después, una sola vez, para informar.
- **Versión de pgvector:** 0.8.6, comprobada el 28 oct con `\dx vector` (la
  imagen `pgvector/pgvector:pg16` es una etiqueta flotante, así que la versión
  puede cambiar al reconstruirla).

### D3. Esquema y migraciones
- **Decisión:** migraciones SQL numeradas (`NNN-descripcion.sql`) en una
  carpeta propia, una tabla en la base que registra cuáles se aplicaron y un
  ejecutor pequeño con `psycopg` (ya presente) que aplica las pendientes sin
  repetir ninguna. `services/db/init/` conserva solo la activación de la
  extensión.
  - **Concretado el 28 oct:**
    - **Carpeta:** `services/api/migrations/`. Entra en la imagen con el
      `COPY . .` existente, sin cambios en el compose ni en el Dockerfile. Se
      descartaron `services/db/migrations/` con volumen (depende de permisos del
      montaje) y con contexto de build en la raíz (cambia todo el Dockerfile).
    - **Ejecución:** al arrancar la API, mediante `lifespan` de FastAPI. El
      ejecutor es una función independiente que también se puede lanzar con
      `python -m`, de modo que en el Bloque 7 (rol mínimo) solo hay que mover la
      llamada. Si una migración falla, la API no arranca. Se descartaron el
      servicio `migrate` aparte (es lo que D4 aplazó), el comando manual (la
      Fase 0 exige que `docker compose up` deje el esquema listo) y el script de
      entrada (cambia el `CMD` y depende de los finales de línea).
    - **Concurrencia:** bloqueo de sesión (`pg_advisory_lock`) con clave fija.
      Hoy hay una sola instancia, así que es una precaución, no una protección
      necesaria.
    - **Registro:** el ejecutor crea la tabla con `CREATE TABLE IF NOT EXISTS`;
      columnas `version` (clave primaria), `nombre`, `checksum` y `aplicada_en`.
      El checksum se calcula sobre los bytes del archivo tal cual y hace fallar
      el arranque si se edita una migración ya aplicada. Cada migración se
      aplica en una transacción junto con su fila de registro. Es la única tabla
      creada así; el esquema de negocio va siempre en migraciones.
    - **Esquema de `clausulas` (concretado el 28 oct):**
      - **Qué se embebe y se hashea:** la cadena `titulo + "\n" + texto`,
        exactamente la que se envía al modelo. `titulo` y `texto` se guardan
        también tal cual, para mostrarlos y citarlos. Cambiar el separador cambia
        todos los hashes y obliga a reindexar. Se descartó añadir `ramo` o
        `documento` a la cadena: haría distintos los vectores de `HOG-7.1` y
        `AUTO-7.1` (textos y títulos idénticos), que es lo que justifica el
        filtro `WHERE` obligatorio.
      - **Columnas:** `id` (identidad, clave primaria), `source_id`
        (`text UNIQUE NOT NULL`, el `clause_id` completo del JSON), `titulo`,
        `texto`, `metadatos` (`jsonb` con `ramo` y `documento`), `hash_contenido`,
        `embedding vector(1536)` y, por fila, `modelo`, `dimensiones` e
        `indexada_en`.
      - **Bitácora:** la tabla `indexaciones` (hash del corpus, recuento y fecha
        de cada pasada) irá en una migración `002`, cuando exista el indexador. La
        `001` solo crea `clausulas`.
      - **Filtro por ramo:** `metadatos->>'ramo' = ANY(...)`, sin índice (42
        filas).
- **Descartadas:** scripts en `init/` recreando el volumen (cada cambio
  borraría datos, inaceptable cuando haya registro de auditoría),
  `CREATE TABLE IF NOT EXISTS` al arrancar (no sabe modificar ni deja
  historial) y Alembic (exige SQLAlchemy, que el proyecto no usa).
- **Motivo:** la base tiene que poder evolucionar sin recrearse.

### D4. Rol de la base de datos
- **Decisión:** la API mantiene el superusuario durante los Bloques 4 a 6
  («A reforzada»). Coincide con el ADR-001, los datos son ficticios y
  reconstruibles y los puertos solo escuchan en `127.0.0.1`.
- **Controles de este bloque:** todo acceso a la base pasa por `_conectar()`,
  la recuperación vive en una única función y las consultas llevan siempre
  parámetros.
- **Descartada:** crear ya un rol de aplicación mínimo (B). Toca varios
  archivos (`.env`, compose con un servicio de migraciones, `_conectar()`,
  migraciones de rol y permisos, pruebas negativas), añade piezas a un bloque
  que ya es grande y se solapa con el ADR-005. El trabajo no desaparece: se
  hace una vez, en el Bloque 7 en lugar del 4.
- **Riesgo asumido:** con el superusuario, una explotación de la API daría
  control total de la base. El rol mínimo limita el daño; no sustituye a las
  consultas parametrizadas.
- **Disparador de revisión:** antes de crear la tabla de auditoría (Bloque 7,
  ADR-005), donde se introduce el rol mínimo.

### D5. Puertos y adaptadores
- **Decisión:** dos puertos, `EmbeddingProvider` (convierte textos en vectores
  e informa de su modelo y dimensiones) y `EvidenceRetriever` (recibe la
  consulta, un filtro genérico y `k`, y devuelve evidencias con su `source_id`
  y su puntuación). Adaptadores reales: OpenAI y pgvector con coseno. Falsos
  para las pruebas, en `services/api/tests/`: vectores deterministas a partir
  del texto y una lista fija de evidencias. La carga de `data/` es una función
  normal de `seguros/`, no un puerto.
- **Reglas:** un puerto se justifica si oculta un sistema externo y hace falta
  un falso para probar. El filtro es genérico (por ejemplo, «el campo `ramo`
  está en `[comun, hogar]`»); traducir «esta póliza es de hogar» a ese filtro
  vive en `seguros/`, porque `core/` no conoce conceptos de seguros (ADR-003).
- **Descartadas:** sin puertos (las pruebas necesitarían red, clave y base);
  «B ligera», sin clases y con el proveedor pasado como parámetro (respeta
  incluso la lectura estricta del ADR-003, pero el contrato es menos
  explícito y modelo y dimensiones viajan aparte); y un tercer puerto para la
  carga de datos (hoy solo hay una fuente, JSON; se reconsidera con la
  ingesta de PDF).
- **Qué no incluye:** ninguna capa de repositorio, fábrica ni registro de
  proveedores.
- **Límite del falso:** prueba la mecánica (reindexar dos veces sin duplicar,
  que un cambio de texto cambia el hash y actualiza el registro, que el filtro
  por ramo se aplica y que una consulta sin resultados no es un error), no la
  calidad de la recuperación, que solo mide `evaluation/` con el modelo real.
- **Sin cambios en `evaluation/`:** sigue siendo caja negra por HTTP y no
  importa nada de `app/`. Eso no choca con la trazabilidad: lo que `/retrieve`
  devuelve (`source_id`, puntuación, hash, metadatos y umbral aplicado) basta
  para auditar y para medir desde fuera.
- **Estructura prevista:** puertos y adaptadores en `app/core/`; la carga y
  la traducción póliza → filtro en `app/seguros/`. Confirmada el 28 oct al
  crear el primer archivo, `app/core/db.py` (`585948d`, con `_conectar()`).

### D6. LangChain
- **Decisión:** el Bloque 4 no usa LangChain: `psycopg` y el SDK de OpenAI
  directos, detrás de los puertos de D5. Se revisa al llegar la ingesta de
  PDF, donde `langchain-text-splitters` o sus cargadores podrían usarse como
  herramienta aislada, sin tocar los puertos de recuperación.
- **Motivo:** con 42 filas no aporta nada que justifique las dependencias, se
  solaparía con los puertos propios y oculta pasos que se quieren entender y
  auditar. `PGVectorStore` permite personalizar columnas, así que el choque
  de esquemas no es seguro, pero tampoco hace falta.
- **Nota para la Fase 2:** LangGraph funciona sin el paquete `langchain`, pero
  arrastra `langchain-core` como dependencia.

### D7. Versión de Python
- **Decisión:** Python 3.13 en el contenedor (`python:3.13-slim`, etiqueta
  flotante: recibe los parches de seguridad) y en el entorno local. La misma
  versión menor; el parche puede diferir (el 27 oct: 3.13.18 en el contenedor
  y 3.13.17 en el equipo).
- **Antecedentes:** el contenedor usaba 3.12 y el equipo 3.14.3, y
  `docs/usage.md` lo daba por válido («basta con una versión reciente»,
  commit `b5c8b84`). Era una diferencia conocida y documentada, pendiente de
  decidir si se igualaba. Se decide igualar porque las pruebas con falsos
  importan código de `app/`. El 27 oct las librerías comunes tenían las mismas
  versiones en ambos entornos; la diferencia era solo el intérprete.
- **Descartada 3.12:** python.org no ofrece instalador de Windows más allá de
  la 3.12.10 (versión solo de seguridad y solo código fuente). La 3.13 tiene
  instalador oficial (3.13.17), soporte de seguridad hasta ~octubre de 2029 y
  está dentro del rango documentado de LangGraph (3.10 a 3.13).
- **Corregido en:** `30b7f81` (Dockerfile y dependencias) y `3b0249b`
  (`docs/usage.md` y regla en `docs/architecture.md`).

### D7b. Dependencias
- **Decisión:** las dependencias directas se fijan con versión exacta (`==`)
  en `services/api/requirements.txt` (antes eran rangos): `fastapi==0.143.3`,
  `uvicorn[standard]==0.54.0`, `psycopg[binary]==3.3.6`.
- **Motivo:** la trazabilidad exige que lo medido sea lo desplegado y que un
  build no cambie solo. Se descartó `~=` por la misma razón.
- **Límite:** las dependencias indirectas no se fijan. Ya se observó: entre
  dos construcciones del mismo día, `starlette` pasó de 1.8.0 a 1.10.0. Fijar
  exacto también retrasa los parches de seguridad hasta que se actualice a
  mano. Revisión en el Bloque 7 con un archivo de bloqueo multiplataforma con
  hashes.

### D8. Abstención y umbral
- **Alcance:** en el Bloque 4, abstenerse solo significa «no hay evidencia
  relevante» (`sin_clausula_relevante`). `campo_ausente` y
  `tipo_no_reconocible` no dependen de la similitud y son del triaje
  (Bloque 5).
- **D8a. Resultado:** `/retrieve` devuelve siempre las k mejores con su
  puntuación y una marca `supera_umbral` por evidencia, más `umbral_aplicado`
  y `abstencion` (verdadera si ninguna lo supera). La abstención es un
  resultado normal, no un error. El umbral empieza sin aplicarse y se fija
  tras medir en desarrollo.
- **D8b. Dónde vive:** como constante en `seguros/`, versionada en Git, que
  declara el modelo con el que se calibró. Descartadas: variable de entorno
  (no queda versionada), tabla en la base (prematuro) y parámetro de la
  petición (cualquier cliente podría rebajarlo).
- **Límite:** solo hay un caso `sin_clausula_relevante` en desarrollo y otro en
  evaluación. Eso permite comprobar que el umbral separa ese caso de los
  positivos, pero no calibrarlo con rigor estadístico. Los demás casos sin
  cláusulas esperadas se abstienen por otra razón y no sirven de ejemplos
  negativos. Los datos y la partición no se tocan.

## Aclaraciones a decisiones anteriores
- **ADR-003, «no se crea ninguna abstracción sin segundo caso»:** se entiende
  como regla de las abstracciones **de dominio**, cuyo segundo caso es un
  segundo dominio (Fase 6). Los puertos de infraestructura se justifican por
  ocultar un sistema externo y necesitar un falso para las pruebas; el falso
  cuenta como segundo caso.
- **ADR-003, puntuación de similitud en la evidencia:** la puntuación depende
  de la consulta, así que pertenece a cada recuperación (el resultado de
  `/retrieve`), no a la cláusula almacenada. De la cláusula se guardan texto,
  `source_id`, metadatos y hash de contenido.
- **ADR-001, recuperación aislada en una función:** se cumple con el puerto
  `EvidenceRetriever`.
- **SHA-256:** se usa para integridad y orden (partición, hash de contenido y
  del corpus), no para proteger secretos. Las contraseñas del Bloque 6
  necesitarán una función de derivación lenta y con sal (Argon2id, bcrypt o
  scrypt).

## Consecuencias
- **Positivas:** la recuperación se prueba sin red, clave ni base; el esquema
  evoluciona sin recrearse; la medida y el umbral quedan trazables; el entorno
  de desarrollo coincide con el de ejecución; no se añaden dependencias
  innecesarias.
- **Negativas / riesgos:** dos interfaces y sus adaptadores más; el
  superusuario sigue en uso hasta el Bloque 7; las dependencias indirectas
  flotan; el umbral no se puede calibrar con rigor con un solo caso de
  abstención por similitud; con una única etiqueta por caso, una cláusula
  equivalente cuenta como fallo; la comparación con `3-large` está pendiente.
- **Cuándo se revisaría:** D1, si la comparación con `3-large` o la ingesta de
  PDF lo piden; D4, antes de la tabla de auditoría (ADR-005); D5 y D6, con la
  ingesta de PDF; D7b, en el Bloque 7; D7, cuando la 3.13 se acerque al fin de
  su soporte (~octubre de 2029) o si LangGraph (Fase 2) exigiera otra versión;
  D8, si se amplían los casos de abstención.
