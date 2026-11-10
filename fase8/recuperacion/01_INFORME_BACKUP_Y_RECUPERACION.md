# Informe — estrategia de respaldo y recuperación de Fase 8

**Bodegas del Atuel · 09/11/2026 · Documentación para auditoría**

## 1. Objetivo y estrategia

Demostrar que la base PostgreSQL de la nube puede respaldarse lógicamente y **recuperarse en una base distinta del origen**, con datos, claves y lógica estructural contrastados. La Etapa 8 exige usar pg_dump, restaurar con pg_restore o psql y verificar los conteos. Se conserva la fuente sin modificarla.

**Herramientas:** PostgreSQL **17.11** en el destino local reportado; **pg_dump** para el respaldo en formato **CUSTOM** (-Fc) y **pg_restore** para recuperación e inventario (-l), según el procedimiento de coordinación. No se inventan versión exacta del cliente de origen, comandos de la ejecución FULL ni flags reales que no se hayan compartido. El formato CUSTOM no es un SQL de texto: necesita pg_restore.

**Destino:** instalación PostgreSQL 17.11 local independiente del proyecto Supabase, según coordinación. No requiere otro proyecto Supabase ni servicios pagos.

**Aislamiento:** dump fuera de Git y de carpetas públicas; restauración en base vacía de PostgreSQL 17; usuarios y ACL revisados por José antes de considerar equivalente la seguridad. Un dump filtrado a public no incluye roles globales ni necesariamente todas las dependencias de extensiones. Si se usa --no-owner/--no-acl para facilitar la restauración, **no se consideran restaurados propietarios y permisos**.

## 2. Estado de la recuperación FULL final — comunicado por coordinación

Coordinación informa que **la carga FULL de Supabase terminó** y que el **backup final se restauró exitosamente en PostgreSQL 17.11 local**. También informó logística y ventas funcionando, RN-13 funcionando, stock sin valores negativos y conservación de botellas verificada. Esta afirmación **es un reporte del equipo**, no el resultado de una conexión o restauración ejecutada por Fabricio en esta entrega.

| Tabla o control | Resultado informado | Evidencia fuente |
|---|---:|---|
| public.cliente | 20.000 filas | Conteo comunicado por coordinación; salida SQL original por incorporar |
| public.permiso_exportacion | 13.278 filas | Conteo comunicado; salida SQL por incorporar |
| public.comprobante | 150.000 filas | Conteo comunicado; salida SQL por incorporar |
| public.renglon_comprobante | 500.000 filas | Conteo comunicado; salida SQL por incorporar |
| RN-13 (auditoria_precio) | Se informó una auditoría RN-13 operativa | Log/captura anonimizada de la prueba y fila auditada por incorporar |
| Stock | Sin cantidades negativas | Resultado comunicado; salida SELECT/certificación por incorporar |
| Conservación de botellas | Verificada según coordinación | Balance y método de cálculo original por incorporar |
| Restore FULL | Exitoso en PostgreSQL 17.11 local | Log pg_restore, inventario y conteos de origen/destino por incorporar |

Los cuatro conteos informados son consistentes con un volumen masivo, pero **por sí solos no acreditan igualdad de las 27 tablas** ni todos los requisitos de integridad. El número preciso de objetos, triggers válidos, FKs y ACL del destino requiere evidencia separada.

## 3. Metadatos necesarios para cerrar el acta real (SIN INVENTAR)

Registrar mediante el responsable que ejecutó el respaldo: nombre del archivo **sin ruta sensible**, fecha/hora UTC, tamaño exacto, SHA-256 real, versión de pg_dump, versión servidor origen/destino, alcance del dump (base o esquema public), código de salida de pg_dump, listado de TOC de pg_restore -l, código de salida de pg_restore, destino independiente, comandos redactados, incidentes, aprobación de José y salidas de control.

**No constan todavía en los mensajes recibidos** el nombre/tamaño/hash del FULL, las 27 parejas de conteos de la restauración, detalle de 32 FK sin huérfanos, inventario de triggers y comparación de ACL. Mantenerlos como **PENDIENTE DE ADJUNTAR**, no como pruebas aprobadas.

## 4. Controles de aceptación de recuperación

1. Respaldo identificable con fecha UTC, tamaño exacto y SHA-256 validado; dump no almacenado en Git.
2. pg_restore -l legible; restauración sin errores en base nueva e independiente de Supabase.
3. **27/27 tablas** presentes; exportaciones completas en la misma ventana/snapshot estable; comparación exacta de filas y volumen de acuerdo con la consigna.
4. Verificaciones estructurales: PK, UNIQUE, CHECK, FK validadas, índices, secuencias, triggers habilitados, funciones y SECURITY DEFINER.
5. Controles de datos: huérfanos FK = 0, stock negativo = 0, totales consistentes; conservación histórica contrastada con el balance real comunicado.
6. Permisos: roles, propietarios, EXECUTE, search_path, grants y políticas por defecto del entorno Supabase comparados y diferencias justificadas.

## 5. Evidencia vinculada

- El ensayo **ficticio de Fabricio** en 02 confirma la mecánica en PostgreSQL 17.11, no la recuperación FULL.
- La matriz **05** separa los estados comunicados de los adjuntos faltantes.
- La guía **04** sirve para reproducir una nueva restauración **solo si coordinación la autoriza**, sin usar la base productiva como destino.
- El kit del Draft PR #15 aporta el comparador estricto y SQL de inventario; ejecutar con precaución y versionar los resultados reales después de una auditoría de privacidad.
