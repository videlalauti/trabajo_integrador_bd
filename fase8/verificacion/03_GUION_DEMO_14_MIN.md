# Propuesta de demostración en vivo — 14 minutos

**Objetivo:** satisfacer la Etapa 8 y preparar la demostración de la Etapa 9 (venta, RN-09, transferencia, consulta con plan). **Guion planificado, NO probado contra nube.**

**Antes de entrar a clase, solo una vez autorizado el deploy:** validar la URL y el SHA, ensayar el flujo sobre registros identificados como prueba, registrar capturas auténticas, preparar cuentas sin privilegios excesivos. El plan considera **~60–90 s de margen para el primer arranque de Render Free**. Si el servicio está despierto, ese margen se usa en preguntas. No mantener el servicio artificialmente activo ni prometer disponibilidad permanente.

| Momento | Responsable sugerido | Qué mostrar y explicar | Evidencia/plan B |
|---|---|---|---|
| **00:00–01:30** | Valentino/Antonio | Abrir URL Vercel HTTPS y llamar `/salud` en Render. Si Render está frío, explicar spin-down y esperar arranque. | Evidencia previa con SHA + hora si el arranque se prolonga; no ocultar el incidente. |
| **01:30–02:20** | Valentino | Arquitectura React/Vercel → HTTPS FastAPI/Render → TLS PostgreSQL/Supabase, roles mínimos, restricciones IP. | Diagrama local impreso/captura del despliegue. |
| **02:20–03:40** | Lautaro | Pantalla de vinos: filtro, paginación y detalle; datos reales. | Captura verificada del flujo. |
| **03:40–05:50** | José | Venta autorizada de prueba; mostrar que totales salen del backend, no de React. | Comprobante de ensayo preparado; no repetir venta si se desconoce estado. |
| **05:50–07:55** | José/Fabricio | RN-09: capturar antes (stock y comprobantes/renglones), intentar exceso de stock, error, capturar después. Demostrar **rollback**. | Capturas autenticadas de la sesión autorizada si hubiera latencia; explicar qué no se escribió. |
| **07:55–09:35** | Antonio | Transferencia: estados permitidos y procesamiento según caso autorizado; explicar efecto en stock. | Registro de prueba y capturas de antes/después. |
| **09:35–10:45** | Fabricio | Tablero Reportes: top vinos, ventas por sala del trimestre, cambio de sala, tabla paginada. | Evidencias reales E09 si el navegador falla. |
| **10:45–12:10** | José/Antonio | Confirmar `bodega_api`, TLS real API→DB, allowlist aplicada + rechazo de otro origen (prueba pregrabada auténtica si es riesgoso repetir en vivo). | Inventario redactado E10–E13. |
| **12:10–13:15** | Fabricio/José | Backup `pg_dump`, destino distinto, restauración, 27 conteos iguales y ACL revisada. **Mostrar evidencias de ejecución ya autorizada, no restaurar en vivo.** | Logs y capturas redactadas E17–E20. |
| **13:15–14:00** | Equipo | Consulta con `EXPLAIN (ANALYZE, BUFFERS)` y conclusión; versión desplegada y límites del plan Free. | Plan registrado previamente y explicación de índices. |

## Preparación anti-imprevistos

- Abrir páginas por HTTPS con URLs definitivas; confirmar antes de la clase que la sesión puede completar cada pantalla.
- Probar una sola venta de ensayo que luego se pueda identificar, sin usar clientes reales de terceros.
- Reservar margen de ~1 minuto para el cold start de Render; si hay un 503 transitorio, comprobar `/salud` y logs antes de concluir que hay caída definitiva.
- La demostración de rechazo RN-09 solo se hace con coordinación y una base cloud preparada para ensayo; antes/después coherentes, no solo mensaje visual.
- No ejecutar en vivo comandos destructivos, `pg_restore`, `DROP`, `GRANT`, `REVOKE` o restricciones IP: usar las evidencias auténticas previamente obtenidas.
- Evitar mostrar contraseñas, terminales con historial sensible, connection strings, cookies o tokens.
- Si un servicio no responde: mostrar el estado real e indicar el impedimento; las capturas históricas se identifican claramente como evidencia previa y **no se presentan como prueba en vivo**.
