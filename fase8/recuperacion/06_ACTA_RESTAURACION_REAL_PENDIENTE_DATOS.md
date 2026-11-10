# Acta de restauración FULL real — ficha para completar con evidencia auténtica

**Estado:** coordinacion informó restauración **EXITOSA** en PostgreSQL 17.11 local, pero **este documento no contiene aún los logs ni metadatos originales de la ejecución**. Completar únicamente con datos verificados por el ejecutor. No hacer un restore adicional para llenar casilleros.

| Campo del acta | Resultado verificable |
|---|---|
| Responsable ejecutor del FULL | **PENDIENTE DE INDICAR** |
| Fecha/hora inicio y fin del backup (UTC) | **PENDIENTE** |
| Origen | Supabase, proyecto anonimizado; confirmar versión y modalidad de conexión |
| Alcance del dump | **PENDIENTE** (base completa o `public`) |
| Herramienta y versión real de pg_dump | **PENDIENTE** (formato CUSTOM según coordinación) |
| Nombre de archivo (solo basename, no ruta) | **PENDIENTE** |
| Tamaño exacto en bytes | **PENDIENTE** |
| SHA-256 del archivo FULL | **PENDIENTE** — **no usar** el SHA del ensayo ficticio |
| `pg_restore -l` / inventario TOC | **PENDIENTE DE ADJUNTAR** |
| Fecha/hora y nombre técnico del destino | **PENDIENTE**; destino informado como PostgreSQL 17.11 local independiente |
| Versión PostgreSQL destino | **17.11** (comunicado por coordinación) |
| `pg_restore` código de salida y log | **PENDIENTE DE ADJUNTAR** (coordinación informa éxito) |
| Errores/advertencias y tratamiento | **PENDIENTE** |
| Tablas origen/destino | 27 esperadas; comparación exacta **PENDIENTE DE ADJUNTAR** |
| Stock negativo | 0 informado por coordinación; salida SQL **PENDIENTE** |
| FK huérfanas | **PENDIENTE DE ADJUNTAR** |
| Balance de conservación | Verificado según coordinación; prueba primaria **PENDIENTE** |
| RN-13 | Funcionando según coordinación; log anon. **PENDIENTE** |
| Triggers, funciones, índices y ACL posrestore | **PENDIENTE DE ADJUNTAR** |
| Validación/firmas de José y Valentino | **PENDIENTE** |

## Conteos recibidos de coordinación

| Tabla | Filas |
|---|---:|
| `cliente` | 20.000 |
| `permiso_exportacion` | 13.278 |
| `comprobante` | 150.000 |
| `renglon_comprobante` | 500.000 |

**Interpretación:** estos cuatro valores fueron comunicados como resultados finales de la carga FULL. Sin el reporte de origen y destino **no se afirma que los cuatro pertenezcan a ambos**, ni que los 27 conteos restaurados hayan coincidido, ni que todas las ACL sean iguales.

## Evidencias que debe solicitar Fabricio (sin conexión a producción)

1. A José: hash y tamaño reales del backup FULL, hora UTC, versión `pg_dump` y alcance.
2. Al responsable del restore: `pg_restore -l`, salida final redactada y código de salida, identificación del destino local.
3. A coordinación: archivos de conteos/tabla completos origen/destino y resultado del comparador; control de stock y las 32 relaciones FK.
4. A José/Antonio: inventario de triggers/constraints/roles, balance de conservación y prueba RN-13 anonimizada.

Todo dato se confirma contra la evidencia auténtica y se somete a revisión de privacidad antes de publicarse. El respaldo original permanece fuera de GitHub.
