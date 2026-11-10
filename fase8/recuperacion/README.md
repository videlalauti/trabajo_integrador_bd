# Fase 8 — Recuperación e integridad (documentación para auditoría)

**Responsable documental:** Fabricio · **Fecha de preparación:** 09/11/2026  
**Alcance:** backup lógico CUSTOM, restauración independiente PostgreSQL 17.11, controles de integridad y defensa.  
**Carácter:** propuesta de documentación para revisión de coordinación. **No ejecuta operaciones contra Supabase.**

## Distinguir tres fuentes de evidencia

| Nivel | Qué consta | Estado |
|---|---|---|
| Ensayo de Fabricio | PostgreSQL 17.11 Docker local, una tabla ficticia, dos filas, dump/restauración y clave primaria | **EJECUTADO LOCALMENTE**; resultados visibles en la conversación; acta en 02 |
| Recuperación FULL final | Coordinación informó carga FULL en Supabase y backup CUSTOM restaurado exitosamente en PostgreSQL 17.11 local | **CONFIRMADO POR COORDINACIÓN**; faltan adjuntar al expediente los logs y metadatos originales |
| Auditoría estructural y funcional | Conteos informados, stock sin negativos, conservación de botellas, logística y RN-13 | **RESULTADOS INFORMADOS**; anexar salidas SQL/identificadores redactados que sustenten cada control |

## Contenido

- **01_INFORME_BACKUP_Y_RECUPERACION.md**: estrategia, alcance, lo confirmado y lo que resta documentar.
- **02_ENSAYO_FICTICIO_FABRICIO.md**: evidencia verificable del ensayo ficticio, sin atribuirle la recuperación FULL.
- **03_INTEGRIDAD_STOCK_FK_TRIGGERS_RN13.md**: datos finales reportados, consultas y límites de inferencia.
- **04_GUIA_RESTAURACION_PG17.md**: guía reproducible con precondiciones y ejemplos; **no autoriza repetir un restore**.
- **05_MATRIZ_Y_CHECKLIST_EVIDENCIAS.md**: índice para reunir originales seguros E14/E15/E17–E20, RN-13 y capturas.
- **06_ACTA_RESTAURACION_REAL_PENDIENTE_DATOS.md**: ficha sin resultados inventados.
- **sql/verificar_recuperacion_solo_lectura.sql**: consultas SELECT de preparación, sin DML.

## Dependencias y trazabilidad

- Kit principal: **Draft PR #15**, rama **fase8-fabricio-verificacion**, carpeta **fase8/verificacion/**; este PR es independiente y no modifica los archivos del kit.
- Consigna: **TPI_Bodegas_del_Atuel.pdf**, Etapa 8 (backup, restauración en base nueva, conteos, roles y seguridad).
- Migraciones: **db/migrations/001_esquema.sql**, **002_constraints.sql** y **005_triggers.sql**.
- Control de integridad previo: **control_integridad.sql**, proporcionado por coordinación; cotejar con su versión vigente.
- El SQL de este paquete **no prueba por sí mismo** conservación histórica de botellas ni que la restauración real mantenga todas las ACL; se requieren salidas trazables.

**No subir:** dumps, datos personales, contraseñas, archivos .env, URLs de conexión, capturas sensibles ni resultados completos con PII.

**No realizar:** nuevos cambios de producción, RN-13, ventas, logística, merge o restauraciones sin autorización.
