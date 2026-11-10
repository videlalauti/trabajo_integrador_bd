# Fase 8 — Web funcional de evaluación (RAMA AISLADA, NO PUBLICADA)

**Fecha:** 10/11/2026. **Base de la rama:** commit `9e7a07af9a7054c38e3a63f45fabca92aec22dcb` del PR #22, API DEMO aislada de Antonio. **El frontend H1 publicado, la API FULL y la base FULL no se modifican.**

## Objetivo

Recuperar las pantallas reales de Fase 7 (ventas, vinos, transferencias) y sumar clientes, ingresos y los cinco reportes para que la cátedra pueda utilizar el sistema por HTTPS desde un navegador, sin instalar software ni ejecutar SQL. Las escrituras ocurren **solo** en Supabase DEMO (`zfxocudcvriicrzgmxie`) con datos ficticios y las reglas de negocio PostgreSQL originales.

## Trabajo programado en esta rama

- `front/src/App.tsx`: navegador con acceso de evaluación, rutas reales de vinos, clientes, ventas, ingresos, transferencias y reportes; no hay botones H1 bloqueados en esta rama.
- `api/app/core/evaluador.py`: cookie `__Host-bodegas_eval` firmada con HMAC-SHA256 y expiración de 2 h; cookie HttpOnly + Secure + SameSite=Lax, CSRF para mutaciones, limitación básica de intentos.
- `api/app/core/demo_guard.py`: preserva intacto el contrato de bearer técnico del PR #22 y agrega las nuevas operaciones **solo** cuando existe sesión web de evaluación válida. Fail-closed en configuración incorrecta.
- `api/app/demo_main.py`: `POST /demo/acceso`, `GET /demo/sesion`, `POST /demo/salir`; catálogos de localidades y transportistas para formularios; router de ingresos. **Nunca** incorporar este guardián en `api/app/main.py`.
- `front/src/lib/api.ts`: las mutaciones envían CSRF, la sesión se mantiene mediante cookie de origen; ni clave ni token técnico aparecen en el bundle.
- `api/tests/test_demo_guard_web.py` + workflow offline: pruebas de sesión, cookies, CSRF, login inválido, límites, bearer y fail-closed.

**No se han desplegado estos cambios, no se ha corrido ninguna venta HTTP en cloud para este feature y no se afirma que todas las pantallas funcionen en la nube hasta superar los tests de integración y la aceptación real.**

## Configuración segura pendiente — exclusivo Render DEMO

Además de las variables **ya existentes y secretas** de Antonio, introducir en las variables privadas de **Render DEMO**:

- `FASE8_EVAL_ENABLED=1` — mantener deshabilitado hasta que el nuevo código esté validado.
- `FASE8_EVAL_PASSWORD` — **nueva** clave aleatoria exclusiva de evaluadores de al menos 20 caracteres; distinta de `FASE8_DEMO_TOKEN`. Comunicar a la cátedra por canal privado, no al chat ni a Git.
- `FASE8_EVAL_SIGNING_KEY` — **nuevo** secreto aleatorio de al menos 48 caracteres; distinto de la contraseña y de `FASE8_DEMO_TOKEN`. Nunca entregarlo a usuarios.
- Mantener `FASE8_DEMO_MODE=aislado`, `FASE8_DEMO_PROJECT_REF=zfxocudcvriicrzgmxie`, TLS `verify-full`, Session Pooler y los CIDR de Render. La lógica deniega explícitamente el project ref de FULL.

**No reutilizar la contraseña PostgreSQL ni el token técnico para el acceso web.** Con variables ausentes o inseguras, el servicio WEB falla cerrado.

## Vercel: NO cambiar la producción a ciegas

La plantilla `front/vercel.demo.json.example` apunta los `/api/*` a `https://bodegas-atuel-demo-api.onrender.com` y conserva el fallback SPA. Es una **plantilla no activa**, distinta de `front/vercel.json.example`, que sigue apuntando al backend H1.

Para ensayar usar **una publicación de previsualización aislada** de Vercel, asociada a esta rama, con su propio rewrite; verificar que `/api/demo/sesion` llega exclusivamente a DEMO. **NO** incorporar `front/vercel.json` en Git ni reemplazar el rewrite de la web actualmente pública sin haber aprobado la integración y contado con un camino de retorno. El dominio actual seguirá apuntando a H1 hasta el cambio controlado.

## Evidencia técnica necesaria antes de publicar

1. Workflow `Fase 8 - DEMO web completa (offline, sin claves)` en verde: compilación, lint, guard viejo y nuevo, aislamiento de FULL.
2. Revisar en DEMO **solo lectura** permisos específicos por columna de vino/cliente y EXECUTE de procedimientos; no ampliar privilegios por un `has_table_privilege(... UPDATE)` negativo si existen GRANT UPDATE por columna. Comprobación realizada el 10/11: las columnas usadas por el servicio sí tenían UPDATE y los cuatro procedimientos EXECUTE.
3. Probar servicios contra PostgreSQL 17 **descartable**, con datos completos de los módulos utilizados; verificar que las transacciones y los errores sean iguales a producción lógica.
4. Publicar código DEMO solo en el segundo Render, con nuevos secretos cargados ocultos. Verificar respuestas sin sesión: `/demo/acceso` debe estar accesible, `/vinos` y mutaciones deben rechazar; sesión con clave: GET y operaciones permitidas; POST sin CSRF: 403.
5. Probar formularios desde un navegador, con contraseña entregada de modo privado: alta/edición de vinos, clientes, venta válida, rechazo RN-09, ingresos, transferencias y reportes. Validar que la FULL no cambió. No imprimir ni registrar secretos.
6. Proteger la demo frente a visitantes concurrentes y uso repetido; documentar datos iniciales y recuperación. Solo después decidir si reemplazar la web principal o mantener una URL de evaluación separada.

## Límites actuales y pendientes

- El primer paso implementa la **interfaz de evaluación completa** y la puerta de autenticación. La capacidad de usarla por HTTPS **depende del nuevo despliegue y pruebas end-to-end**: aún no está publicada.
- La limitación de intentos en memoria es apropiada solo como defensa complementaria para un servicio académico de una instancia; no sustituye cuotas/gateway ni seguridad perimetral.
- La sesión firmada se invalida por vencimiento o rotación del secreto. `/demo/salir` elimina la cookie del navegador; las cookies copiadas antes del logout siguen criptográficamente válidas hasta su expiración, por lo que debe preservarse HTTPS y protegerse el acceso al dispositivo.
- **Nunca** fusionar el PR #22 ni este cambio directamente en la API FULL sin revisar configuración y rutas; `app.main` de producción debe seguir protegida.

## Estado

**DESARROLLO EN CURSO**. Branch `fase8-demo-web-completa-20261110` apilada sobre `fase8-demo-aislada-candidata`. Validar CI y promover de forma controlada, no declarar «funcional en la URL publicada» hasta la prueba real.
