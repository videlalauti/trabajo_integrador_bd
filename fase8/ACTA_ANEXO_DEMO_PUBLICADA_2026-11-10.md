# Anexo de cierre — DEMO institucional y Bloque 4 (10/11/2026)

> Evidencia documental complementaria del [acta técnica original](ACTA_CONTROL_FINAL_2026-11-10.md) y [cierre de despliegue](CIERRE_Y_EVIDENCIAS.md). No cambia ni borra la cronología de ensayos anteriores. Sin secretos.

## Despliegue

- FULL H1 solo lectura: https://bodegas-del-atuel.vercel.app → Render FULL → Supabase FULL `sjfyocokehaubuwwbhnw`.
- DEMO institucional autenticada: https://bodegas-del-atuel-demo-profesores.vercel.app → Render DEMO → Supabase DEMO `zfxocudcvriicrzgmxie`.
- Proyecto Vercel independiente `bodegas-del-atuel-demo-profesores`, Production branch `fase8-vercel-preview-demo-20261110`, commit `9339932a1abe661cc1d026376ae1db72db7036be`. Confirmado por Lautaro; pruebas en navegador realizadas por Lautaro y acceso confirmado por coordinación.
- `front/vercel.json` en la rama DEMO apunta las rutas API a `https://bodegas-atuel-demo-api.onrender.com`. No se fusionó la rama DEMO en la FULL.
- En el entorno de esta auditoría no se logró confirmar por DNS el dominio nuevo; no se interpreta como fallo de Vercel ni se atribuye una respuesta HTTP inexistente.

## Pruebas web y auditoría independiente en PostgreSQL DEMO

| Caso | Resultado observado |
| --- | --- |
| Alta y actualización de vino | Vino 4 `VINO PRUEBA WEB FASE8`, cepa 1 al 100 %, maridaje 1 existente, precio 2.200 |
| RN-13 | Un registro en auditoría: precio 2.000 → 2.200, usuario `bodega_api` |
| Alta y edición de cliente | Cliente ficticio 3; dirección actualizada |
| Venta válida | Comprobante 5: sala 1, cliente 1, vino 1, cantidad 1; subtotal 1.300, descuento 130, total 1.170; stock sala vino 1: 30 → 29 |
| RN-09 | Rechazo HTTP 409 / P0001 reportado por navegador; vino 2 en sala 1 conservó cantidad 30; sin comprobante incompleto |
| RN-10 ingreso | Ingreso 1, transportista 1, vino 2 × 2, `procesado`; depósito vino 2: 120 → 122 |
| RN-11 transferencia | Solicitud 3, vino 3 × 1 a sala 2, `procesado`; depósito 120 → 119; sala 2: 25 → 26 |
| Reportes (5/5) | Ranking vino 1: 2 botellas; ventas sala 1: 2.340; consulta sin stock sala 2: 0 filas; transportista más activo: 1 ingreso; trazabilidad vino 1: 0 lotes de prueba |
| Explicación de acumulados | Comprobantes **3 y 5** de 1.170 cada uno; dos renglones de una botella cada uno; sin duplicación |
| Integridad adicional | 0 cantidades negativas de stock; 0 comprobantes sin renglones |
| Acceso y sesión | Login, F5, detalle vino 4 y reportes probados en URL estable por Lautaro |

Las pruebas de negocio **no se repiten** para cerrar la documentación. No se realizaron modificaciones de datos durante esta redacción.

## Aislamiento y privilegios

- Supabase FULL conservó por consulta READ ONLY: **27 tablas**, **150.000 comprobantes**, **500.000 renglones** y **20.000 clientes**. No se hicieron escrituras sobre FULL.
- DEMO posee permisos de `EXECUTE` para `sp_procesar_ingreso(integer)` y `sp_procesar_transferencia(integer)` del rol `bodega_api`; el rol no tiene `UPDATE` general sobre `stock_sala` y los movimientos los realizan los procedimientos/triggers de PostgreSQL.
- La autenticación de evaluación usa sesión firmada, cookie HttpOnly/Secure, CSRF y límite de intentos en memoria. Este último es **control básico**, no defensa de escala para una exposición pública de alto tráfico.
- La contraseña de evaluación se entrega privadamente y no debe figurar en el repositorio.

## Backup y restauración FULL

Evidencias ya documentadas en `fase8/evidencias/` y `ACTA_CONTROL_FINAL_2026-11-10.md`:

- Dump final: `g1c_final_full_REINTENTO_20261109_225055.dump`, **10.452.417 bytes**; SHA-256 comunicado desde `Get-FileHash`: `B5E48E30A0AB0011E99DD2FA3664C0C315B15BC5F4C7196EA3106A6571BED055`. No se recalculó independientemente desde los bytes del dump en esta auditoría.
- Restauración previa en PostgreSQL **17.11** local reportada por coordinación. Conteos entre origen FULL y destino restaurado: **27/27** coincidentes. Controles estructurales numéricos: **15/15** coincidentes.
- Se inspeccionó el TOC con `pg_restore --list` sobre el dump final, pero **no se localizó el log original de `pg_restore` ni el código de salida**; el TOC no es evidencia equivalente del comando de restore.
- Los conteos estructurales no prueban identidad de definiciones de objetos, filas individuales, propietarios ni ACL; se usó restauración con `--no-owner --no-acl`.
- Intento de backup DEMO desde PC no completado por problema de certificados TLS y argumentos del script; **no hay backup/restore DEMO validado**. Se decidió priorizar disponibilidad funcional con datos ficticios. Queda como riesgo de recuperación hasta generar respaldo DEMO comprobado.
- No es necesario ni deseable volver a ejecutar restauraciones o pruebas de escritura sobre FULL para completar el expediente existente.

## Pendiente de aceptación documental

1. Incorporar formalmente esta documentación revisando el **Draft PR #23**, sin mezclar las ramas de código DEMO (#22–#25) con FULL.
2. Explicar a la cátedra el modelo de acceso: **FULL H1 solo lectura** y **DEMO autenticada con operaciones completas**. No atribuir aceptación docente no recibida.
3. Si la cátedra exige un log primario o igualdad de ACL/propietarios, adjuntar evidencia existente si aparece o reconocer la limitación; no fabricar resultados.
4. Cerrar informe de Fase 9 y matriz de trazabilidad con URL estable y evidencias definitivas.
