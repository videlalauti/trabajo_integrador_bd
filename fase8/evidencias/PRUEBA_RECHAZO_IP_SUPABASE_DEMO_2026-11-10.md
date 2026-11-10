# Evidencia de seguridad — denegación por IP en Supabase DEMO

**Fecha:** 10/11/2026. **Resultado:** **APROBADO** para el control de bloqueo desde una IP externa no autorizada.

## Contexto y alcance

- **Origen:** PowerShell de Windows en la PC del coordinador, fuera de los dos rangos de salida de Render permitidos para DEMO.
- **Destino:** Session Pooler PostgreSQL de Supabase en `aws-1-us-west-1.pooler.supabase.com:5432`.
- **Proyecto:** **solo DEMO** `zfxocudcvriicrzgmxie`, no FULL `sjfyocokehaubuwwbhnw`.
- **Usuario solicitado:** `bodega_api.zfxocudcvriicrzgmxie`, base `postgres`.
- **Comando de prueba:** cliente `psql -X -W` con `PGSSLMODE=require`, `PGCONNECT_TIMEOUT=8` y consulta prevista `SELECT 1;`. Contraseña no compartida. No se modificaron reglas de red, roles ni claves.
- **Configuración previa corroborada por captura:** Network Restrictions DEMO contiene únicamente `74.220.48.0/24` y `74.220.56.0/24`; no se incluye `0.0.0.0/0` ni `::/0`.

## Respuesta recibida

Se omitió la IP concreta del cliente de la salida pública.

```text
psql: error: connection to server at <HOST_DEMO> (IP del servidor omitida), port 5432 failed:
FATAL: (EADDRNOTALLOWED) address not in tenant allow_list: {IP_CLIENTE_OMITIDA}
Codigo de salida: 2
```

**Interpretación:** el servicio Supabase denegó la conexión por **dirección de origen no incluida en la allowlist**. Es una causa explícita de **bloqueo de red**, no un error genérico de contraseña ni una prueba de login fallido. **La autenticación no fue acreditada ni era necesaria para observar este rechazo de red; el `SELECT 1` no llegó a ejecutarse.** Este control demuestra que **esa conexión externa concreta** fue bloqueada y no afirma que cualquier dirección de Internet imaginable tenga el mismo comportamiento.

**No se publican direcciones IP personales, contraseñas, tokens ni datos sensibles.** La salida completa queda en la conversación de coordinación; el expediente versionado conserva solamente el código y mensaje desensibilizados.

## Estado

**CONTROL NEGATIVO DE RESTRICCIÓN DE RED APROBADO.** No repetir para obtener otro error. Mantener H1 productivo y DEMO aislada, con los rangos ya aprobados, sin modificar la configuración.

No confundir este resultado con auditoría de FULL: se realizó contra el pooler de **DEMO**, conservando producción intacta.
