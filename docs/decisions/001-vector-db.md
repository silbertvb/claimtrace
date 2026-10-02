# ADR-001: Elección de la base de datos vectorial

- **Estado:** aceptada
- **Fecha:** 2026-09-29
- **Bloque:** 2. Scaffolding Docker
- **Afecta a:** Bloque 4 (RAG), Bloque 7 (registro de auditoría)

## Contexto
El RAG necesita almacenar y recuperar fragmentos de políticas con su ID de
cláusula estable (por ejemplo `SHUGO-CG-HOG-4.2`). El registro de auditoría es
solo-añadir y también debe guardarse en algún sitio. El corpus (los documentos
que el RAG indexa: condiciones generales de Hogar y Auto y politicas de devolución,
cancelación, fraude y reclamaciones formales) es pequeño (cientos de cláusulas),
y el tiempo por bloque es limitado.

## Opciones consideradas
1. **pgvector (extensión de Postgres):** una sola base para vectores y
   auditoría, con transacciones y `JOIN` / menas funciones específicas de
   vectores que una base dedicada.
2. **Qdrant:** base vectorial dedicada, muy buena en filtrado y escala / obliga
   a mantener además una Postgres para la auditoría, con dos conexiones y sin
   transacción entre ambas.
3. **Chroma:** muy rápida de arrancar / menos habitual en entornos
   profesionales y tampoco resuelve la auditoría.

## Decisión
pgvector, porque el valor del proyecto es la trazabilidad y permite guardar
fragmentos, decisión y registro de auditoría en una única base transaccional.

## Consecuencias
- **Positivas:** decisión y registro se guardan en una sola transacción; la
  cita consultada y la decisión se cruzan con un `JOIN`; un servicio menos en
  el compose.
- **Negativas / riesgos:** menor rendimiento vectorial que una base dedicada a
  gran escala; el carácter solo-añadir del registro se reforzará con permisos
  y triggers (Bloque 7, ADR-005). Hasta entonces la API se conecta con el
  superusuario de la base, así que no está protegido, y aun después un
  superusuario podría saltárselo.
- **Cuándo se revisaría:** si el corpus creciera a millones de fragmentos o
  hiciera falta filtrado vectorial avanzado, se valoraría Qdrant. La
  recuperación quedará aislada en una función para facilitar ese cambio.