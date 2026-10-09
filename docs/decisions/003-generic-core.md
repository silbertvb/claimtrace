# ADR-003: Núcleo genérico y capa de seguros

- **Estado:** aceptada
- **Fecha:** 2026-10-09
- **Bloque:** 3. Datos de prueba (cierre) y diseño previo al Bloque 4
- **Afecta a:** Bloque 4 (esquema y RAG), Bloque 5 (agente de triage),
  Bloque 7 (LangGraph y trazabilidad), Bloque 8 (n8n), Bloque 10 (testing)
- **Relacionada con:** ADR-001 (pgvector), ADR-002 (formato de los datos)

## Contexto
El Roadmap plantea ClaimTrace como una aplicación vertical de seguros cuyas
piezas de confianza (evidencia, decisión, aprobación, auditoría) podrían
reutilizarse en otros dominios. Es una hipótesis aún no contrastada con el
mercado. Lo que sí es verificable hoy es lo que fija el repositorio: los datos
del Bloque 3 son de **enrutado** (a qué equipo va cada reclamación, o
abstención), no de cobertura, y todavía no existe ningún esquema, modelo ni
código de negocio (`services/api/main.py` solo expone `/health`).

Eso permite decidir la forma del núcleo antes de escribirlo. Si lo propio de
seguros (póliza, importe, ramo) se mezcla con las piezas de confianza, la Fase 5
del Roadmap (separar lo específico de lo reutilizable) sería una refactorización
cara. Esta decisión fija esa separación desde el principio, sin construir por
ello una plataforma genérica.

## Opciones consideradas
1. **Núcleo genérico y capa de seguros separada desde el esquema:** las piezas de
   confianza no llevan campos de seguros y lo propio del dominio va en los datos
   de la reclamación / exige disciplina al diseñar y una traducción de nombres
   al cargar los datos.
2. **Todo específico de seguros ahora y separar en la Fase 5:** más rápido al
   principio y sin traducciones / la Fase 5 pasa a ser una refactorización de
   esquema, API y evaluación ya construidos, y el riesgo es que no se haga.
3. **Plataforma genérica completa desde el Bloque 4** (capa de abstracción,
   registro de agentes, varios dominios): la más preparada para el futuro /
   sobreingeniería sin un segundo dominio que la justifique, y retrasa lo que
   hay que demostrar primero (evaluación real, Fase 3).

## Decisión
Opción 1: **núcleo genérico y capa de seguros separada**, sin crear una
plataforma. No se añade ninguna abstracción que no tenga hoy un uso en seguros.

**Piezas del núcleo genérico** (nombres del Roadmap, Fase 5): Evidence,
Decision, Approval, AuditEvent, Agent y AgentRun. No llevan campos de seguros.

**Qué es capa de seguros** (datos y reglas del dominio): la reclamación y sus
campos propios (`policy_id`, `importe`, `fecha`, tipo de reclamación), la póliza,
el ramo, el corpus de cláusulas de VERÉGIDA y las reglas de enrutado. Lo propio
del dominio va en los datos de la reclamación y en metadatos, nunca en las
piezas del núcleo.

**Nombres genéricos de la decisión y correspondencia con las etiquetas.** Los
JSON del Bloque 3 **no se renombran** (se conservan datos, hashes y validador);
la traducción se hace al cargarlos. Las etiquetas son la respuesta esperada y la
decisión es lo que produce el agente: la evaluación compara una con la otra.

| Etiqueta del Bloque 3 (esperada) | Campo genérico de Decision | Significado |
|---|---|---|
| `destino_esperado` | `outcome` | Resultado de la decisión (en seguros: el destino de enrutado) |
| `clausulas_esperadas` | `evidence_ids` | Identificadores de las evidencias que justifican el resultado |
| `esperado_abstencion` | `abstained` | Si el sistema se abstiene y escala |
| `motivo_abstencion` | `abstain_reason` | Por qué se abstiene |
| `campos_faltantes` | `missing_fields` | Datos que faltan en el caso |

**Evidencia.** El `source_id` de una evidencia es el ID de la cláusula (por
ejemplo `VRG-CG-HOG-6.1`): sigue siendo el contrato entre RAG, evaluación y
auditoría, como fija el ADR-002. `ramo` y `documento` van en un campo de
metadatos y no como columnas del núcleo. Cada evidencia guarda su puntuación de
similitud (será el `relevance` del Evidence Engine) y el hash de su contenido; al
indexar se calcula también un hash del corpus. El esquema exacto se diseña en el
Bloque 4.

**Qué cambia por dominio** (y solo eso): el corpus, el esquema de la
reclamación o caso, el conjunto de resultados posibles, las etiquetas de
evaluación y la validación de coherencia de los datos.

**Reglas de arquitectura relacionadas**
- **n8n y LangGraph:** toda decisión y escalado viven en LangGraph y se
  registran en la auditoría. n8n solo transporta: entrada (recibir la
  reclamación y llamar a la API) y salida (notificar lo que la API ya decidió).
  n8n no lleva umbrales ni reglas de negocio.
- **Evaluación:** el código vive en `evaluation/`, fuera de `services/api/`, y
  trata al sistema como caja negra por HTTP. Un bloque no se cierra sin su medida.
- **Deuda de dominio:** cada vez que algo propio de seguros se cuele en una
  pieza del núcleo, se anota en una sección «Deuda de dominio» de
  `docs/architecture.md`. Esa lista será el trabajo de la Fase 5.
- **Sin movimientos prematuros:** `data/` no pasa a `data/seguros/` hasta que
  exista un segundo dominio, y no se crea ninguna abstracción sin segundo caso.

## Consecuencias
- **Positivas:** la Fase 5 deja de ser una refactorización de esquema; la
  evaluación del Bloque 4 y la auditoría del Bloque 7 se construyen sobre piezas
  que no cambian de dominio; los datos, los hashes y el validador del Bloque 3
  siguen intactos; `n8n` y LangGraph no compiten por la lógica de decisión.
- **Negativas / riesgos:** hay que mantener una traducción entre los nombres de
  los JSON y los del núcleo; la disciplina de no mezclar campos de seguros
  depende de que se aplique al escribir cada pieza (por eso la lista de deuda);
  la generalidad es una hipótesis: con un solo dominio no se sabe si el núcleo
  es de verdad reutilizable hasta la Fase 6; el riesgo contrario es la
  sobreingeniería, que se limita con la regla de no abstraer sin segundo caso.
- **Cuándo se revisaría:** si la validación multidominio (Fase 6) muestra que el
  núcleo no sirve fuera de seguros, si un campo propio del dominio resulta
  imprescindible dentro de una pieza genérica, o si se añade la decisión de
  cobertura (ampliación posterior a la Fase 3), que pedirá `Coverage` y
  `Exclusion` en la capa de seguros y no en el núcleo.