# Verificaciones de seguridad y RN-09 — solo preparación

## Seguridad (NO EJECUTAR EN CLOUD HASTA AUTORIZACIÓN)

1. **Render / Vercel HTTPS:** URL real `https://`, certificado del hostname y ausencia de contenido mixto; en Render `GET /salud` debe devolver 200 y base conectada. Registrar commit desplegado, primera latencia/cold start y logs redactados. En Vercel recarga SPA y cinco pantallas con Network (ocultar cookies y tokens).
2. **TLS API→DB:** `pg_stat_ssl` con `pg_backend_pid()` en la **misma conexión efectiva de FastAPI**; identificar `current_user`, `ssl`, versión y cipher. Una consulta desde SQL Editor/psql administrativo **no prueba** TLS de la API. Coordinar con Antonio un diagnóstico temporal seguro que no exponga credenciales.
3. **Restricciones de red Supabase:** José/Valentino aplican rangos Outbound compartidos de Render y acceso administrativo esencial; chequear IPv4 e IPv6 y modos direct/session-pooler. Confirmar éxito desde origen permitido y denegación de conexión válida desde red excluida; un `password authentication failed` no valida bloqueo IP. No tocar red sin plan de recuperación.
4. **Permisos mínimos:** validar roles, propiedades y ACL efectivos (`has_table_privilege`, `has_function_privilege`, esquema, `anon`, `authenticated`, `PUBLIC`, `SECURITY DEFINER` y `search_path`). Las consultas catálogo no sustituyen ensayos negativos con autorización. Asegurar que `bodega_api` no es superusuario ni propietario de tablas TP.
5. **Errores controlados:** API sin stock, validación HTTP 4xx, DB inaccesible (503 para salud), cold start y reintentos acotados. No simular caída de nube modificando reglas/secretos. Registrar respuesta sanitizada y hash versión.

## RN-09: venta sin stock con rollback completo

**Permiso obligatorio:** José aprueba caso controlado, cliente de prueba, sala, vino, cantidad, ventana sin otras escrituras. No probar sobre FULL activo sin autorización.

**Antes:** ejecutar DOS VECES si hace falta `sql/05_rn09_estado_solo_lectura.sql` desde psql con `-v sala=... -v vino=...`; guardar fecha/hora y stock exacto, número de comprobantes y renglones. Solicitar a Antonio un identificador de correlación de la venta de ensayo, sin datos personales. Complementar con consulta por comprobante/ID de transacción aprobada; los conteos globales por sí solos no atribuyen resultados cuando hay escrituras concurrentes.

**Acción:** desde la pantalla de Ventas o cliente HTTP autorizado, intentar cantidad mayor que stock de sala y registrar error específico RN-09 (sin secretos). No ejecutar SQL DML artesanal para el ensayo: se busca demostrar el camino real por API + transacción de base.

**Después:** repetir exactamente los SELECT antes; stock idéntico, sin comprobante ni renglón parcial atribuible al intento, y 4xx apropiado. Registrar pruebas antes/error/después, logs redactados, responsable y tiempos. Si existió concurrencia, NO concluir rollback; aislar caso y repetir bajo control.

**Resultado esperado:** rechazo RN-09 y estado SQL conservado. No confundir un mensaje visual con prueba de transacción revertida.
