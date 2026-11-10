# Integridad de datos — stock, claves foráneas, triggers y RN-13

**Corte documental:** 09/11/2026. **No se ejecutan consultas contra Supabase desde esta entrega.** Las cantidades y resultados finales fueron **comunicados por coordinación**, no obtenidos por Fabricio en una sesión SQL de producción.

## 1. Volumen final confirmado por coordinación

| Tabla | Conteo informado | Estado de prueba primaria |
|---|---:|---|
| `public.cliente` | 20.000 | Salida SQL original pendiente de adjuntar |
| `public.permiso_exportacion` | 13.278 | Salida SQL original pendiente |
| `public.comprobante` | 150.000 | Salida SQL original pendiente |
| `public.renglon_comprobante` | 500.000 | Salida SQL original pendiente |
| `public.auditoria_precio` | Existe al menos una auditoría RN-13 según coordinación | Conteo exacto y registro anonimizado pendientes |

No se dispone en este expediente de la exportación completa con los **27 conteos** de origen y restauración. Los números precedentes tampoco permiten por sí solos afirmar que cada tabla del destino tiene igual número de filas.

## 2. Stock y conservación de botellas

**Reportado como aprobado:** coordinación verificó que `stock_deposito` y `stock_sala` no tienen cantidades negativas y que se conserva la cantidad de botellas en los movimientos de logística y ventas.

**Respaldo de lectura:** `control_integridad.sql` del proyecto consulta ambas tablas con `WHERE cantidad < 0` (esperado: cero filas negativas). El esquema aplica `chk_stock_sala_cantidad` y `chk_stock_deposito_cantidad` (`cantidad >= 0`). El archivo `sql/verificar_recuperacion_solo_lectura.sql` de esta entrega incluye conteos resumidos y verificaciones adicionales de consulta.

**Límite importante:** una captura del stock final no demuestra sola la **conservación histórica**. Hace falta el balance utilizado por José (ingresos procesados, transferencias, ventas y stock inicial), su alcance temporal, y el antes/después o salidas SQL auténticas de los movimientos. **No se inventan** fórmulas del balance real, valores del stock ni cifras de diferencias.

## 3. Claves foráneas e integridad referencial

El script `control_integridad.sql` suministrado incluye controles explícitos para **32 relaciones FK**: por ejemplo, comprobante→cliente/sala, renglón→comprobante/vino, stock→vino/sala, transferencia→sala, ingreso→transportista/bodega y auditoría→vino. Cada consulta espera **0 huérfanos**.

El resultado individual de las 32 consultas **no fue compartido en esta solicitud**. Se debe anexar la salida original redactada, idealmente tanto del origen como del destino, y revisar que todas las restricciones FK estén `convalidated=true`. El esquema en `db/migrations/001_esquema.sql` y `002_constraints.sql` define PK/FK y reglas de borrado/cascada/restricción; el inventario de catálogo es una verificación distinta de contar huérfanos.

## 4. Triggers y RN-13

La migración real `db/migrations/005_triggers.sql` crea `fn_trg_auditoria_precio_vino()` y el trigger `trg_auditoria_precio_vino`:

- Se ejecuta **AFTER UPDATE** sobre `vino`.
- Solo inserta una auditoría cuando `NEW.precio IS DISTINCT FROM OLD.precio`.
- Escribe `cod_vino`, `precio_anterior`, `precio_nuevo`, `fecha_hora` y `usuario` en `auditoria_precio`.

**Confirmación del equipo:** RN-13 funcionó y existe una auditoría del ensayo. No tenemos identificador, fecha, precio ni usuario anonimizados; **no repetimos `UPDATE vino`** para documentarlo. Una inspección `SELECT` de `pg_trigger` permite demostrar que está habilitado; el registro auditado debe estar redactado y vinculado a la ejecución real para demostrar funcionalidad.

## 5. Controles que faltan para aprobar formalmente el expediente

| Control | Resultado comunicado | Evidencia primaria a anexar |
|---|---|---|
| Volúmenes | Cuatro conteos finales comunicados | Salida de `SELECT COUNT(*)` y CSV 27 tablas origen/destino |
| No negativos | Aprobado por coordinación | Resultado completo de controles sobre ambos stocks |
| Conservación | Aprobada por coordinación | Consulta/balance histórico y criterio, sin datos privados |
| 32 FK | Hay script de verificación | Resultado por relación: 0 huérfanos + `convalidated` |
| RN-13 | Una auditoría informada | Trigger habilitado y log/registro auditado anonimizado |
| Restore | Exitoso según coordinación | Log `pg_restore`, código de salida, objetos y ACL |

## 6. Cómo obtener evidencia adicional sin escribir

Usar únicamente consultas `SELECT` autorizadas, preferentemente desde una **copia restaurada**, con una cuenta de solo lectura. Archivo incluido: `sql/verificar_recuperacion_solo_lectura.sql`. No ejecutar `INSERT`, `UPDATE`, `DELETE`, rutinas que cambien datos, ni replicar RN-13 en producción. La extracción y publicación de salidas deben ser revisadas para evitar PII y secretos.

**Fuente de contraste:** `control_integridad.sql` y migraciones `001`, `002` y `005` del repositorio, además de las confirmaciones remitidas por coordinación.
