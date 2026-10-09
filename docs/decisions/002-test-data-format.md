# ADR-002: Formato de los datos de prueba y criterios de etiquetado

- **Estado:** aceptada
- **Fecha:** 2026-10-08
- **Bloque:** 3. Datos de prueba
- **Afecta a:** Bloque 4 (RAG de políticas: carga de cláusulas en la base e
  indexación), Bloque 5 (agente de triage, que se evalúa contra las etiquetas),
  Bloque 6 (acceso y roles: usuarios sintéticos), Bloque 10 (testing del stack
  completo)
- **Relacionada con:** ADR-003 (núcleo genérico y capa de seguros). Los nombres
  de las etiquetas de este ADR se conservan; su correspondencia con los campos
  genéricos de la decisión está en el ADR-003.

## Contexto
El RAG y el agente de triage necesitan datos ficticios sobre los que trabajar y,
sobre todo, contra los que medirse: para saber si el agente enruta y cita bien
hace falta una respuesta correcta conocida de antemano (la etiqueta). Los datos
deben ser reproducibles (que cualquiera obtenga los mismos), coherentes entre sí
(una reclamación no puede citar una póliza que no existe) y cargables en
Postgres en el Bloque 4. Todo es ficticio: VERÉGIDA Seguros S.A. no corresponde
a ninguna empresa real.

## Opciones consideradas
1. **JSON, un archivo por entidad en `data/`, con un script que genera y valida:**
   los campos vacíos se escriben como `null` y cargan directos en Postgres /
   las cláusulas y las reclamaciones se escriben a mano, así que hay que
   revisarlas una a una.
2. **CSV o ficheros SQL de carga:** más directos para la base / un campo vacío
   y una cadena vacía se confunden con facilidad, y las listas (cláusulas
   esperadas, campos faltantes) no caben bien en una celda.
3. **Generar todo con un script o con un modelo, sin revisión manual:** más
   rápido y con más volumen / las etiquetas serían de dudosa fiabilidad, y la
   etiqueta es justo lo que mide al agente.

## Decisión
Opción 1: JSON por entidad en `data/` (`clausulas.json`, `reclamaciones.json`,
`polizas.json`, `usuarios.json`), con el código en `scripts/`, separado de los
datos. El corpus y las 33 reclamaciones se escriben a mano y se revisan caso por
caso; las pólizas y los usuarios los genera `scripts/generar_datos.py` con
semilla fija (2026). El script valida los cuatro archivos antes de guardar.

**Formato y etiquetado**
- **IDs:** cláusula `VRG-{CG|POL}-{materia}-{n.m}`, póliza `VRG-PLZ-{nnnn}`,
  reclamación `CLM-{nnnn}`, usuario `USR-{nnn}`. El ID de cláusula es el
  contrato con los bloques de RAG y auditoría.
- **Abstención con una sola fuente de verdad:** `esperado_abstencion` y
  `motivo_abstencion` (`campo_ausente`, `sin_clausula_relevante`,
  `tipo_no_reconocible`). `campos_faltantes` solo se rellena con `campo_ausente`.
- **Cláusulas esperadas:** se citan las que justifican el destino y ninguna más.
  En fraude, la específica (`FRA-3.1` o `FRA-3.2`) más `FRA-2.1`; `FRA-1.1` no se
  cita. Cobros posteriores a la baja: `DEV-3.2` en `cobro_indebido` y `CAN-2.1`
  en `cancelacion_poliza`.
- **Fecha del recibo:** si el texto solo da el mes, el día es el de cargo del
  ramo (5 en Hogar, 10 en Auto); si no da ni el mes, falta la fecha y el caso
  es de abstención. En las cancelaciones, la fecha es la que da el cliente.
- **Un solo disparador por caso:** si un texto activa dos reglas con destinos
  distintos, el corpus no dice cuál prevalece, así que cada texto activa solo una.
- **Coherencia:** una póliza nunca tiene dos recibos del mismo mes.

**Reglas del script generador y validador**
- El mismo día del alta cuenta como cubierto: error solo si la fecha de la
  reclamación es anterior al alta.
- Cada problema lo reporta una sola comprobación; las demás lo omiten.
- Primas fijas en las pólizas con recibos en reclamaciones, porque las
  reclamaciones citan esos importes; el resto, con semilla.
- Las pólizas canceladas solo aparecen en casos que citan `DEV-3.2`, `CAN-2.1`
  o `CAN-3.2`.
- Una cláusula es válida si su ramo es `comun` o coincide con el de la póliza.
- Los campos vacíos deben coincidir con `campos_faltantes`, y el motivo es
  `campo_ausente` si y solo si falta algún campo requerido.
- `importe` es un float con punto en el JSON; los textos usan el formato natural
  español y la validación los reconcilia sin normalizarlos.
- Si alguna comprobación falla, se muestran todos los errores, no se guarda nada
  y el script termina con código 1.

## Consecuencias
- **Positivas:** los datos son reproducibles (mismo hash con la misma semilla);
  la validación automática encontró un error que la lectura manual no vio
  (`CLM-0008`, su texto no decía el mes); el formato carga directo en Postgres;
  el agente se evaluará contra etiquetas revisadas una a una.
- **Negativas / riesgos:** las etiquetas las fija una sola persona, así que
  pueden reflejar su criterio y no el único posible (los dos casos de
  `sin_clausula_relevante` son los más discutibles); la validación solo
  comprueba coherencia interna, no que el criterio sea el correcto; 33 casos
  son pocos para sacar estadísticas finas; los umbrales de enrutado (150 € y
  1.000 €) son ficticios y, si cambian, hay que tocar a la vez
  `VRG-POL-DEV-2.1`, `2.2` y `2.3` y los casos `CLM-0001` a `0006`.
- **Cuándo se revisaría:** si la evaluación (recuperación en el Bloque 4,
  enrutado y abstención en el Bloque 5) revela etiquetas ambiguas, si cambian los
  umbrales o el corpus, o si hace falta más volumen. En el Bloque 10 (testing del
  stack completo) la validación podría separarse en `scripts/validar_datos.py`
  para ejecutarla en las pruebas automáticas sin regenerar los datos.