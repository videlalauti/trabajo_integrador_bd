# Matriz de evidencias — recuperación FULL e integridad

**Preparación documental:** 09/11/2026. Esta matriz se centra en la recuperación FULL y los controles de integridad; complementa la matriz general E01–E21 del **Draft PR #15**, sin sustituirla.

## Leyenda

- **OBSERVADO EN ENSAYO:** salidas del trabajo local ficticio de Fabricio, mostradas en conversación.
- **INFORMADO POR COORDINACIÓN:** resultado comunicado por el equipo, aún sin la salida primaria adjunta aquí.
- **PENDIENTE DE DOCUMENTAR:** dato exacto/log/captura que debe facilitar el responsable. No significa que la prueba no se haya realizado.
- **NO EJECUTAR:** ninguna repetición de operaciones productivas para generar capturas.

| ID | Control / evidencia | Estado de esta entrega | Evidencia original a aportar sin información sensible |
|---|---|---|---|
| F01 | Herramienta y formato backup CUSTOM | INFORMADO POR COORDINACIÓN | Comando redactado, versión de pg_dump 17, alcance del dump, registro de resultado |
| F02 | Backup FULL: nombre, fecha UTC, tamaño en bytes, SHA-256 | PENDIENTE DE DOCUMENTAR | Acta de responsable y comprobación hash, sin adjuntar dump |
| F03 | Inventario `pg_restore -l` del FULL | PENDIENTE DE DOCUMENTAR | TOC redactado: tablas, datos, constraints, funciones, índices |
| F04 | Destino distinto: PostgreSQL 17.11 local | INFORMADO POR COORDINACIÓN | Evidencia de base local, versionado, conexión sin secretos |
| F05 | Restauración exitosa FULL | INFORMADO POR COORDINACIÓN | Log `pg_restore`, código de salida 0 y errores/avisos resueltos |
| F06 | Conteos 27/27 origen y destino | PENDIENTE DE DOCUMENTAR | Dos CSV de conteos y salida del comparador estricto con 27 OK; ventana consistente |
| F07 | Cuatro conteos finales compartidos | INFORMADO POR COORDINACIÓN | `cliente=20000`, `permiso_exportacion=13278`, `comprobante=150000`, `renglon_comprobante=500000` |
| F08 | Integridad de las 32 FK | PENDIENTE DE DOCUMENTAR | Lista de huérfanos por relación = 0; FKs validadas, inventario de destino |
| F09 | Stocks no negativos | INFORMADO POR COORDINACIÓN | Salida de ambos conteos de `cantidad < 0` con 0 |
| F10 | Conservación de botellas | INFORMADO POR COORDINACIÓN | Balance real de entradas, salidas, transferencias y stock por corte y escenarios |
| F11 | Triggers y constraints restaurados | PENDIENTE DE DOCUMENTAR | Inventario de origen/destino, `tgenabled`, `convalidated`, diferencias explicadas |
| F12 | RN-13 — auditoría efectiva | INFORMADO POR COORDINACIÓN | Evidencia original de una actualización autorizada y fila auditada anonimizada; **NO repetir** |
| F13 | Roles, ACL y SECURITY DEFINER posrestore | PENDIENTE DE DOCUMENTAR | Comparativa técnica revisada por José; `--no-owner/--no-acl` no restaura ACL |
| F14 | Ensayo de Fabricio en Docker PG17 | OBSERVADO EN ENSAYO | `02_ENSAYO_FICTICIO_FABRICIO.md`, conteos 2=2, PK y SHA-256 local |
| F15 | Pruebas offline kit | OBSERVADO EN ENSAYO | En PR #15: 18 tests de HTTPS/TLS y 9 del comparador aprobados |
| F16 | Guía reproducible / README | DOCUMENTADO | `04_GUIA_RESTAURACION_PG17.md` y `README.md` |

## Inventario para organizar archivos originales (propuesta; no adjuntar dumps)

| Archivo privado sugerido | Fuente / acción |
|---|---|
| `acta_backup_full_sin_secretos.md` | Responsable de backup completa F02–F05 |
| `inventario_dump_redactado.txt` | Salida `pg_restore -l`; validar que no contenga datos personales |
| `conteos_origen_privado.csv`, `conteos_destino_privado.csv` | Guardar localmente con control de acceso; solo publicar resumen autorizado |
| `comparacion_27_tablas_resumen.txt` | 27 filas OK sin PII, obtenido de comparador real |
| `control_integridad_resumen.txt` | Stock, 32 FKs, totales y validación, siempre sin filas personales |
| `triggers_constraints_resumen.txt` | Inventario de objetos PG17 y diferencias |
| `rn13_anonimizado.png` | Captura auténtica redactada aportada por José; no crear ensayos nuevos |
| `ensayo_backup_restore_ficticio.txt` | Ya guardado localmente por Fabricio (NO es FULL) |

## Checklist de aceptación antes de la defensa

- [ ] Verificar SHA-256, tamaño y fecha reales del dump FULL.
- [ ] Adjuntar identidad del destino y versión PostgreSQL 17.11.
- [ ] Adjuntar log de restauración y resultado; informar cualquier advertencia.
- [ ] Comparar exactamente 27 tablas entre un origen consistente y el destino.
- [ ] Adjuntar control de 32 FK, stock no negativo y totales.
- [ ] Anexar balance original de conservación de botellas.
- [ ] Confirmar triggers, constraints, índices, funciones y ACL posrestore.
- [ ] Incorporar la evidencia RN-13 auténtica y anonimizada, sin repetir el `UPDATE`.
- [ ] Mantener separado el ensayo ficticio del trabajo real.
- [ ] Redactar todo rastro sensible antes de publicar evidencias, previa aprobación de Valentino/José.

## Orden de exposición sugerido (3–4 min dentro del guion general)

1. Explicar PostgreSQL/Supabase → `pg_dump -Fc` → respaldo privado con SHA-256.
2. Mostrar destino local PostgreSQL 17.11 y el log auténtico del `pg_restore`.
3. Mostrar igualdad de 27 tablas y una muestra de controles estructurales.
4. Demostrar la conservación de botellas y stock no negativo con el balance existente.
5. Mostrar auditoría RN-13 anonimizando usuarios/identificadores sensibles; explicar trigger `AFTER UPDATE`.
6. Separar claramente la prueba ficticia de 2 registros de la restauración FULL, mencionar límites de los permisos `--no-owner/--no-acl`.

**No sustituir una evidencia auténtica por una captura generada o por los datos ficticios del kit.**
