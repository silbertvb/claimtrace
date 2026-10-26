# Evaluación

Estado: pendiente. Aún no hay resultados; se publican a medida que se cierran los bloques. Este documento fija qué se mide, sobre qué datos y con qué límites, antes de medir.

## Qué se mide y cuándo

| Bloque | Medida |
|---|---|
| 4 · RAG | Calidad de recuperación frente a las cláusulas esperadas; reindexar tras cambiar una cláusula actualiza su registro sin duplicarlo |
| 5 · Agente de triage | Precisión de enrutado y de abstención; el agente solo afirma lo que sostiene la evidencia |
| 6 · Acceso y roles | Pruebas 401/403 y rol revalidado en la base para las acciones sensibles |
| 7 · LangGraph y trazabilidad | Tasa de escalado y de decisiones corregidas por una persona; pruebas adversarias con su medida |
| 10 · Testing del stack Docker completo | La evaluación, incluidas las pruebas adversarias, se ejecuta de forma automática |

El código de evaluación vive en `evaluation/`, fuera de `services/api/`, y trata al sistema como caja negra por HTTP.

## Datos de evaluación

- **33 reclamaciones etiquetadas:** 24 completas, con destino y cláusulas esperadas, y 9 de abstención esperada (6 por campo ausente, 2 sin cláusula relevante y 1 de tipo no reconocible).
- **Son una prueba de concepto**, no una muestra estadística. Las etiquetas las fija una sola persona y los datos son ficticios. Las métricas son indicativas.
- **Las cifras del caso de negocio** (volumen, horas y reclamaciones mal enrutadas) son supuestos y no entran en ninguna métrica.

## Partición desarrollo/evaluación

Se fija en el Bloque 4, **antes de elegir k y el modelo** y antes de medir. El reparto lo genera `evaluation/particionar.py` y queda en `evaluation/particion.json`; se fijó el 26 oct 2026 en el commit `130b144`.

- **Proporción:** aproximadamente dos tercios para desarrollo y un tercio para evaluación.
- **Estratificado:** el reparto se hace por separado dentro de cada grupo (estrato). El estrato es el destino esperado en las reclamaciones completas y el motivo de abstención en las de abstención.
- **Determinista:** dentro de cada estrato, los casos se ordenan por el SHA-256 de su `claim_id` (en hexadecimal, orden ascendente). Los primeros `(4n + 3) // 6` van a desarrollo, siendo n el tamaño del estrato, y el resto a evaluación. Esa fórmula es dos tercios de n redondeados con enteros.
- **Estratos de un solo caso:** van a desarrollo. Por eso `tipo_no_reconocible` no tiene ningún caso de evaluación.
- **Regresión:** `CLM-0011`, `CLM-0012`, `CLM-0013` y `CLM-0016` quedan fuera del reparto y se usan como pruebas de regresión del filtro por ramo.

Recuentos (29 casos repartidos más 4 de regresión):

| Estrato | n | Desarrollo | Evaluación |
|---|---|---|---|
| atencion_cliente | 9 | 6 | 3 |
| reclamaciones_formales | 4 | 3 | 1 |
| compliance_revision | 3 | 2 | 1 |
| fraude | 4 | 3 | 1 |
| campo_ausente | 6 | 4 | 2 |
| sin_clausula_relevante | 2 | 1 | 1 |
| tipo_no_reconocible | 1 | 1 | 0 |
| **Total** | **29** | **20** | **9** |

Los parámetros que se eligen con los casos de desarrollo son tres:

- **k:** cuántas cláusulas devuelve la búsqueda por consulta. Si es muy bajo, la cláusula correcta puede quedarse fuera; si es muy alto, entra ruido.
- **Modelo de embeddings:** el modelo que convierte cada texto en un vector numérico para poder compararlos. Cambia qué cláusulas se consideran cercanas a una reclamación.
- **Umbrales:** la puntuación de similitud mínima para aceptar un resultado. De ellos depende cuándo la búsqueda se considera «sin evidencia», base de la abstención.

Los casos de evaluación se usan solo para informar el resultado.

## Pruebas adversarias

Usan un conjunto propio, separado de los 33 casos, para no alterar estas métricas. Su formato se define en el Bloque 5, se miden en el Bloque 7 y se automatizan en el Bloque 10.

## Decisiones de alcance de la evaluación

| # | Decisión | Fecha |
|---|---|---|
| D1 | El objeto de la evaluación son las **reclamaciones de clientes**, no los siniestros | 14 oct 2026 |
| D2 | Se adopta la partición desarrollo/evaluación descrita arriba | 14 oct 2026 |
| D3 | El caso de cobertura se aplaza a la ampliación posterior a la Fase 3; los datos actuales no se tocan | 14 oct 2026 |

## Limitaciones

- Una sola persona etiqueta los datos, y una segunda persona revisaría una muestra antes de cualquier uso fuera del portfolio.
- Los datos son ficticios y pequeños, así que no permiten afirmar un rendimiento general.
- No se afirma cumplimiento de ninguna norma: antes habría que verificar cuál aplica.
- El caso de cobertura aún no existe en los datos.
- La evaluación tiene solo 9 casos y varios estratos aportan uno solo, así que un acierto o un fallo mueve mucho la métrica.
