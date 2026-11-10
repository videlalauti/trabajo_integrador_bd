# Segunda API Render — preparación (NO DESPLEGAR CON CREDENCIALES AÚN)

**Objetivo:** permitir la demostración de venta, RN-09 y transferencia en la base de ensayo **`zfxocudcvriicrzgmxie`**, con URL y secretos distintos de la aplicación pública FULL.

## Configuración preliminar

| Opción | Valor o instrucción |
|---|---|
| Servicio | Web Service separado, nombre sugerido `bodegas-atuel-demo-api` |
| Plan | Free, confirmar costo $0 y horas disponibles |
| Runtime | Docker |
| GitHub repo | `videlalauti/trabajo_integrador_bd` |
| Branch | `fase8-demo-aislada-candidata` (**PR #22 aún Draft**) |
| Dockerfile Path | `api/Dockerfile.demo` |
| Docker Build Context | `api/` |
| Región | Oregon, igual que el servicio productivo para mantener egress previsible |
| Auto-Deploy | **OFF** |
| Health Check | `/salud` |
| Credenciales en creación | **NO** cargar `DB_PASSWORD` ni `FASE8_DEMO_TOKEN` en el primer deploy |
| Resultado de primera creación | Se espera fallo de arranque por falta de configuración; confirmar que la API no abre el pool |

**No modificar** el servicio `bodegas-atuel-api`, su rama productiva, su secret file, ni `bodegas-del-atuel.vercel.app`.

## Variables no secretas predefinidas

- `DB_HOST`: **obtener el Session Pooler host del NUEVO proyecto demo desde Supabase Connect**; no copiar el host del proyecto FULL sin verificar.
- `DB_PORT=5432`
- `DB_NAME=postgres`
- `DB_USER=bodega_api.zfxocudcvriicrzgmxie`
- `DB_SSLMODE=verify-full`
- `DB_SSLROOTCERT=/etc/secrets/prod-ca-2021.crt`
- `DB_POOL_MIN=1`, `DB_POOL_MAX=2`
- `DB_CONNECT_TIMEOUT=10`, `DB_POOL_TIMEOUT=10`
- `FASE8_DEMO_MODE=aislado`
- `FASE8_DEMO_PROJECT_REF=zfxocudcvriicrzgmxie`
- `FASE8_DEMO_LOCAL`: **no definir en Render**.
- `WEB_CONCURRENCY=1` (la imagen ya arranca un solo proceso Uvicorn).

Secret File: CA raíz del pooler Supabase que corresponda al proyecto demo; verificar el contenido y SHA-256 en origen, sin suponer que es idéntico al del proyecto FULL. Ubicarlo en `/etc/secrets/prod-ca-2021.crt`.

## Gates obligatorios ANTES de habilitar la API

1. Crear servicio de **solo preparación**, sin password y sin token, Auto-Deploy OFF. Compartir URL y **todos** los Outbound CIDR. No realizar POST.
2. En el proyecto demo Supabase, activar **Network Restrictions** exclusivamente con las salidas que indique el segundo servicio; no aplicar esta configuración al proyecto FULL ni usar `0.0.0.0/0`.
3. Configurar una contraseña nueva y exclusiva del rol `bodega_api` **en el proyecto demo** por un canal privado/seguro, sin publicarla en SQL de GitHub, capturas, mensajes ni archivos.
4. Generar un Bearer token criptográficamente aleatorio de 48+ caracteres para `FASE8_DEMO_TOKEN`, distinto de DB_PASSWORD y de cualquier secreto productivo. Guardarlo únicamente en Environment de Render y en entorno local privado del cliente de pruebas.
5. Con código del PR #22 revisado y commit exacto fijado, cargar `DB_PASSWORD` y `FASE8_DEMO_TOKEN` con **Save only**, ejecutar el deploy del commit auditado y comprobar TLS, 401 sin token, 403 en rutas no permitidas y solo lectura con token.
6. Antes de usar `--ejecutar`, correr `fase8/demo_aislada/ejecutar_demo.py` sin argumentos (**solo GET**) contra esa URL. Si falla, STOP y no forzar operaciones.
7. Ejecutar una sola ventana de demostración autorizada, registrar resultados sin PII ni secretos. Si una solicitud de escritura tiene respuesta ambigua, no repetirla sin verificar el estado.
8. Conservar intacto H1 en el Render productivo y no compartir DB_PASSWORD de producción.

## Estado técnico verificado en Supabase demo

- PostgreSQL 17.11; 27 tablas, 32 FK, 27 tablas con RLS y 27 policies para roles técnicos; **0 lints de seguridad**.
- Rol `bodega_api` con contraseña **NULL** (no hay conexión externa viable todavía).
- Dataset mínimo *ficticio*: 3 vinos, 2 clientes, 2 salas, stock depósito 360 y salas 165.
- Prueba SQL cloud de venta, RN-09 y transferencia con **ROLLBACK completo**: 0 comprobantes y 0 transferencias persistidos.
- Pruebas PostgreSQL 17 GitHub Actions con seed small completo: [evidencia de ejecución](https://github.com/videlalauti/trabajo_integrador_bd/actions/runs/42840387018).

**Conector Render:** en la sesión de coordinación, la conexión no encontró el servicio productivo esperado en el workspace disponible; por seguridad no se creó ningún segundo servicio desde esa conexión. La creación queda pendiente en el Dashboard del **workspace correcto**.
