# Roadmap de ClaimTrace

Estado a 9 oct 2026. Los bloques son los del [README](../README.md); las decisiones
de diseño, los ADR de [`decisions/`](decisions/).

## Criterio de Orden

ClaimTrace es un sistema de IA auditable para el triage de reclamaciones de una
aseguradora ficticia (VERÉGIDA Seguros S.A.). Lo planteo para demostrar que sé
diseñar, construir, evaluar, asegurar y explicar un sistema de IA empresarial, no
para acumular funcionalidades. Por eso he ordenado el trabajo así: primero un
caso concreto que funcione de extremo a extremo, después medirlo y auditarlo, y
solo entonces ver si las piezas de confianza se pueden reutilizar fuera de
seguros. Esto último es una hipótesis que la Fase 6 pondrá a prueba, no algo ya
demostrado.

**Principio fijo:** si la evidencia no basta para decidir con fiabilidad, el
sistema no inventa: se abstiene y escala el caso a una persona.

**Cadena que recorre cada caso:** reclamación → evidencia → decisión → revisión
humana → auditoría.

## Alcance

- **Qué decide el MVP:** a qué equipo va cada reclamación (`atencion_cliente`,
  `reclamaciones_formales`, `fraude`, `compliance_revision`) y cuándo debe
  abstenerse. No decide si una póliza cubre un siniestro.
- **Ampliaciones posteriores a la Fase 3:** decisión de cobertura (con
  exclusiones) e ingesta de documentos PDF. Cada una tiene su punto de decisión
  (ver más abajo).
- **Los datos son ficticios.** Las métricas se calculan sobre 33 casos etiquetados
  por una sola persona, así que son indicativas, no estadísticas.

## Fases

| Fase | Qué entrega | Bloques | Cómo se da por hecha | Estado |
|---|---|---|---|---|
| **0 · MVP fundacional** | Flujo de extremo a extremo con `docker compose up`: corpus en la base, recuperación de cláusulas, clasificación del destino y recomendación | 1, 2, 3 (hechos), 4, 5 | El sistema levanta con un solo comando y enruta los 33 casos de prueba, citando cláusulas | 🟡 En curso (Bloques 1 a 3 cerrados) |
| **1 · Triage explicable** | Destino, cláusulas citadas con su texto, abstención con motivo, confianza y ranking de evidencias | 4, 5 | Cada decisión muestra qué evidencia la sostiene; la recuperación y el enrutado se miden contra las etiquetas | ⬜ |
| **2 · Orquestación y revisión humana** | Flujo en LangGraph con estado compartido, umbrales de confianza, escalado y aprobación o rechazo por una persona | 6, 7 | Un caso de baja confianza llega a una persona y su resolución queda registrada | ⬜ |
| **3 · Auditoría, seguridad y evaluación** | Registro de auditoría, autenticación con roles, controles de seguridad de IA y evaluación publicada | 6, 7 y `evaluation/` desde el 4 | Resultados de evaluación publicados en el README y reproducibles con un comando | ⬜ |
| **4 · Producción mínima** | Pruebas automáticas, integración continua, registros, integración con n8n y, si hay tiempo, dashboard | 8, 9 (opcional), 10 | El stack completo se prueba de forma automática | ⬜ |
| **5 · Núcleo reutilizable** | Separar la capa de seguros del núcleo genérico (Evidence, Decision, Approval, AuditEvent, Agent, AgentRun) | Fuera de los 12 bloques | La lista de «deuda de dominio» de `architecture.md` queda resuelta | ⬜ |
| **6 · Validación multidominio** | Casos pequeños fuera de seguros (alerta de blanqueo, solicitud de préstamo, revisión de contratos) sobre el mismo núcleo | Fuera de los 12 bloques | El núcleo funciona sin cambios de fondo en al menos un dominio distinto | ⬜ |

Los Bloques 11 (documentación) y 12 (pitch) son transversales y cierran el
proyecto.

Las fases posteriores a la 6 dependen de que la Fase 6 salga bien y no se
planifican aquí.

## Medida obligatoria para cerrar cada bloque

La evaluación no tiene un bloque propio: se construye a la vez que lo que mide,
con el código en `evaluation/` (fuera de `services/api/`, tratando al sistema
como caja negra por HTTP). Un bloque no se cierra sin su medida.

| Bloque | Medida |
|---|---|
| 4 · RAG | Calidad de recuperación frente a las cláusulas esperadas |
| 5 · Agente de triage | Precisión de enrutado y de abstención; el agente solo afirma lo que sostiene la evidencia |
| 7 · LangGraph y trazabilidad | Tasa de escalado y de decisiones corregidas por una persona; protección contra instrucciones inyectadas en el texto |
| 10 · Testing del stack | La evaluación se ejecuta de forma automática |

## Reglas de arquitectura

- **Núcleo genérico:** Evidence, Decision, Approval y AuditEvent no llevan campos
  de seguros. Lo propio del dominio (póliza, importe, ramo) va en los datos de la
  reclamación. Ver [ADR-003](decisions/003-generic-core.md).
- **n8n y LangGraph:** toda decisión y escalado viven en LangGraph y se registran
  en la auditoría. n8n solo transporta: recibe la reclamación y notifica lo que
  la API ya decidió, sin umbrales ni reglas de negocio.

## Puntos de decisión

| Cuándo | Qué se decide |
|---|---|
| Al cerrar la Fase 3 (y como tarde antes de la Fase 6) | Si se añade la ingesta de PDF. El corpus actual está en JSON y cada cláusula conserva su identificador; un adaptador de entrada podría asignarlo a cada trozo de un PDF sin tocar el RAG ni la evaluación |
| Al cerrar la Fase 3 | Si se añade la decisión de cobertura, con exclusiones, sobre el mismo núcleo |
| Al cerrar la Fase 6 | Si el proyecto continúa más allá del portfolio y con qué alcance |

## Qué queda fuera por ahora

- Multi-tenant, gestión completa de usuarios y dashboard (solo si sobra tiempo
  tras la Fase 4).
- Cualquier cumplimiento normativo declarado: antes de afirmarlo habría que
  verificar qué regulación aplica realmente a este caso.