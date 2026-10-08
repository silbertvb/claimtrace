# ClaimTrace

🚧 En construcción. Proyecto desarrollado como preparación para el rol de Forward Deployed Engineer.

Agente de IA agentic para el triage de reclamaciones de una aseguradora ficticia (VERÉGIDA Seguros S.A.), con RAG sobre políticas y condiciones generales. La trazabilidad y la auditoría están integradas desde el diseño: cada decisión cita la política que la respalda, pasa por revisión humana registrada y, si faltan datos, el agente no decide y escala.

> Todos los datos del proyecto (clientes, pólizas y reclamaciones) son ficticios.

## Stack
Python · LangChain · LangGraph · Docker · n8n · Postgres + pgvector

## Estado
- [x] Bloque 1: Caso de negocio
- [x] Bloque 2: Scaffolding Docker
- [x] Bloque 3: Datos de prueba  (VERÉGIDA Seguros S.A. y todos los datos (clientes, pólizas, cláusulas y reclamaciones) son ficticios.)
- [ ] Bloque 4: RAG de políticas y condiciones generales
- [ ] Bloque 5: Agente de triage
- [ ] Bloque 6: Acceso y roles
- [ ] Bloque 7: LangGraph + trazabilidad
- [ ] Bloque 8: n8n (integración)
- [ ] Bloque 9: Dashboard y métricas (opcional, se valorará más adelante)
- [ ] Bloque 10: Testing stack Docker completo
- [ ] Bloque 11: Documentación 
- [ ] Bloque 12: Pitch