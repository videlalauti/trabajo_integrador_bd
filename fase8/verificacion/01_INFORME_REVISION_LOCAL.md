# Bodegas del Atuel — Fase 8
## Informe de revisión del kit y propuesta de verificación de Fabricio

**Fecha:** 09/11/2026
**Estado:** propuesta técnica para auditoría de Valentino, **NO AUTORIZA EJECUCIÓN EN NUBE**.
**Origen:** `FASE8_KIT_FABRICIO.zip`, `FASE8_AUDITORIA_DESPLIEGUE_Y_VERIFICACION.md`, `TPI_Bodegas_del_Atuel.pdf` (Etapas 8 y 9), `control_integridad.sql` suministrado.
**Operaciones realizadas:** lectura y comparación de archivos, pruebas de Python sin red ni base de datos, generación de documentación y pruebas con datos ficticios.
**Operaciones NO realizadas:** consultas a Supabase, Render o Vercel; migraciones; roles; cambios de ACL/IP; backup/restore; DML; commit/PR.

## 1. Dictamen ejecutivo

**Resultado: APTO PARA SEGUIR PREPARANDO; NO APTO AÚN COMO EVIDENCIA DE DESPLIEGUE.**

1. Los ocho tests originales del kit pasan en este entorno (`Ran 8 tests ... OK`).
2. Los CSV ficticios incluidos son aceptados por el comparador original, que informa `APROBADO` sobre **solo tres tablas**. Es una debilidad demostrada del criterio de auditoría, porque el TP contiene **27 tablas**.
3. `sql/01_conteos_public.sql` contiene exactamente **27 nombres distintos** y su conjunto coincide con las 27 tablas citadas por el `control_integridad.sql` aportado. Esta es una comprobación estática; **no** verifica que las tablas existan en Supabase.
4. Por separado, la propuesta `mejoras_propuestas/comparar_conteos_estricto.py` rechaza CSV incompletos y comprueba los umbrales del perfil escogido. Sus **9 pruebas ficticias** pasaron. No sustituir el comparador del equipo sin aprobación.
5. Los SQL `01`, `02` y `03` son consultas `SELECT` por inspección del contenido; **no fueron ejecutados contra PostgreSQL** en esta revisión.
6. No hay evidencia real disponible de despliegue, permisos, SSL de la conexión de Render, allowlist aplicada, backup cloud, restauración ni RN-09 en la nube. Todo ello sigue **pendiente de autorizaciones y dependencias**.

## 2. Contraste contra la consigna

| Exigencia oficial (Etapa 8, pp. 18–19) | En kit / auditoría | Evaluación |
|---|---|---|
| PostgreSQL gestionado o servidor en nube | Supabase definido; preparación centralizada pendiente | Pendiente de ejecución real |
| API + front en URLs públicas HTTPS | Comprobador `/salud` de Render y plan Vercel | Parcial; falta control público Vercel, SPA y operación |
| Migraciones **en orden** desde archivos SQL | Procedimiento descrito; no se entregaron migraciones `001`–`008` completas en este paquete | No es posible certificar orden, modificaciones ni propietarios solo con este material |
| Cifrado DB `sslmode=require` o equivalente | `pg_stat_ssl` para sesión de psql | Es válido para esa sesión, no prueba por sí solo la conexión Render→DB |
| Puerto BD no expuesto ampliamente | Restricciones de red planificadas | Falta captura de reglas efectivas y rechazo desde origen excluido |
| Secretos solo en entorno y sin historial Git | Reglas de redacción correctas | Pendiente revisión real de secretos en repositorio **e historial** |
| API con rol mínimo, no propietario | ACL de tablas + identidad en psql | Falta prueba de rol efectivo desde el proceso de API y privilegios de funciones/secuencias |
| Backup con `pg_dump`, restauración en base nueva | Instrucciones prudentes | Bloqueado hasta autorización/rol técnico; probar destino independiente |
| Conteos coincidentes | SQL con 27 tablas + comparador | Corregir comparador incompleto (ver H1) |
| Carga nube reducida: ≥10.000 en una tabla, justificada | `--minimo 10000` | Correcto **solo para perfil reducido**; no equivale a base completa |
| Trigger RN-09 en nube | Procedimiento antes/error/después | Correcto como diseño; requiere prueba real y control de rollback |
| README de proveedor y reproducción | Previsto por coordinación | Pendiente evidencia/publicación oficial |

**Distinción clave (Etapa 3 vs. 8):** el volumen **completo local** exige que las 27 tablas tengan filas, que **tres** superen **10.000** y que **una** supere **100.000**. La excepción de **nube reducida** admite **al menos 10.000** en una tabla (con justificación), sin convertir eso en criterio para la base completa. Para las verificaciones internas propongo además que ninguna de las 27 tablas quede vacía.

## 3. Hallazgos priorizados y propuesta de resolución

| ID / prioridad | Evidencia y alcance | Recomendación / aceptación por coordinación |
|---|---|---|
| **H1 — Alta** | `comparar_conteos.py` no exige 27 tablas; aprobó CSV con `cliente`, `comprobante`, `vino` solamente. | Rechazar listas incompletas/sobrantes y comprobar igualdad de las 27. Se adjunta propuesta autocontenida, probada solo con datos ficticios. |
| **H2 — Alta** | `--minimo 10000` valida solo una tabla; no detecta carencias del perfil local completo. | Seleccionar explícitamente `nube_reducida` o `local_completa`, y aplicar umbrales adecuados, sin confundir `>` con `>=`. |
| **H3 — Alta** | SQL de TLS muestra `pg_stat_ssl` del `pg_backend_pid()` de quien ejecuta psql. | Evidencia separada para conexión **real de FastAPI en Render**: consulta del proceso en su sesión / inspección por rol administrador de backend identificable. No afirmar TLS API mediante SQL Editor. |
| **H4 — Alta** | `03_objetos...sql` compara cantidades y solo enumera funciones `SECURITY DEFINER`; conteos idénticos pueden ocultar funciones, propietarios, índices o triggers distintos. | Contrastar inventarios exactos, definición de constraints/índices, estado `tgenabled`, rutinas y search_path, privilegios de EXECUTE y propietarios; conservar reporte de diferencias. |
| **H5 — Alta** | El backup custom de `public` no incluye roles de clúster; `--no-owner` en `pg_dump -Fc` no resuelve la restauración de propietarios. | Aplicar `--no-owner --no-acl` **en `pg_restore`**, como ya indica el kit, y procedimiento aprobado por José para crear roles, reasignar propietarios y revocar grants predeterminados. Evitar falsa equivalencia de ACL. |
| **H6 — Media** | El script HTTP exige URL inicial `https://`, pero `urllib` puede seguir redirecciones y el script no verifica explícitamente la **URL final**; captura `Content-Type` sin validarlo. | Agregar inspección de `response.geturl()` con HTTPS final (o validación equivalente), y registrar si hubo redirección. Es mejora preventiva, no incidencia observada. |
| **H7 — Alta** | Las consultas de `has_table_privilege` incluyen unas pocas tablas y no certifican roles/membresías/permisos por defecto o EXECUTE público. | José debe aprobar inventario efectivo de todas las tablas, secuencias, funciones y grants por defecto; probar que `anon`, `authenticated`, `PUBLIC` y roles no autorizados carezcan de accesos indebidos. |
| **H8 — Alta** | Una pantalla mostrando RN-09 no demuestra rollback; las escrituras concurrentes pueden falsear conteos antes/después. | Preparar caso de ensayo autorizado, ventana sin escrituras, stock y conteos pre/post, ausencia de comprobante/renglones nuevos; distinguir error PostgreSQL de error frontend. |
| **H9 — Media** | SQL `02` presupone que existen los roles `bodega_api` y `bodega_reportes`. | Ejecutar solo tras la puesta en marcha aprobada por José; una falla por rol ausente no debe confundirse con TLS. |
| **H10 — Media** | Documentación de auditoría refleja un estado de rama y PRs al 08/11. Coordinación ya comunicó avances posteriores. | Marcar el inventario de commits como **fotografía histórica**, revisar Git antes del despliegue y registrar el SHA realmente desplegado. |
| **H11 — Alta** | La consigna exige migraciones SQL en orden con rol propietario; no se proporcionaron en este paquete las ocho migraciones originales ni la adaptación aprobada para Supabase. | Solicitar a José/Valentino inventario, hash y registro de ejecución; **no afirmar compatibilidad exacta** de `001`–`008` ni de `007_roles.sql` sin inspeccionarlos y ejecutar pruebas autorizadas. |
| **H12 — Media** | `/salud` 200 demuestra solamente API/DB en ese instante, no seguridad completa ni frontend. | Exigir evidencias independientes de HTTPS de Vercel, CORS/rewrite, cinco pantallas y refresco SPA. |

**Sobre `sslmode=require`:** satisface la exigencia mínima de conexión cifrada de la consigna, pero no equivale necesariamente a validar la identidad del servidor mediante certificado. Evaluar `verify-full` si la infraestructura y CA del servicio lo soportan; no cambiar configuración sin coordinación.

## 4. Pruebas locales y límites

| Prueba | Resultado | Medio |
|---|---|---|
| `python scripts/test_kit.py -v` del ZIP original | **8/8 aprobadas** | Python, sin red |
| `python scripts/comparar_conteos.py --origen ejemplos/origen_ejemplo.csv --destino ejemplos/restaurado_ejemplo.csv --minimo 10000` | **APROBADO** con 3 tablas ficticias | Evidencia del falso positivo de completitud |
| Comparación estática nombres SQL del kit vs. `control_integridad.sql` | **27/27 coincidentes** | Lectura de archivos |
| Propuesta `comparar_conteos_estricto.py` | **9/9 pruebas aprobadas** | Datos sintéticos, sin BD |
| Consulta directa a Supabase | **NO EJECUTADA** | No autorizada |
| HTTPS Render / Vercel real | **NO EJECUTADA** | Servicios todavía no habilitados para pruebas |
| Backup y restauración / RN-09 | **NO EJECUTADOS** | Prohibidos hasta aprobación explícita |

No se debe presentar ningún CSV ficticio, test aislado ni captura anterior como resultado de producción en la nube.

## 5. Dependencias y aprobaciones necesarias

**De Valentino:** URLs definitivas HTTPS, commit/SHA desplegado en Render y Vercel, habilitación de prueba, coordinación de 5 pantallas, confirmación de reglas de CORS y reescrituras, permiso para capturas de dashboards redactadas.

**De Antonio:** salud real y versión de API, evidencia de conexión SSL **del proceso de API**, confirmación de rol mínimo y errores RN-09 verificables desde la aplicación; contrato de endpoint/JSON vigente.

**De José:** inventario y adaptaciones de las migraciones `001`–`008`, roles técnicos, permisos efectivos, owners y `SECURITY DEFINER`, política de red y usuario/host de backup, estrategia de restauración en **proyecto nuevo**, autorización de prueba de escritura y snapshot estable.

**De Lautaro/equipo:** frontend en Vercel, cinco pantallas navegables, errores reales, refresco SPA, posibilidad de ensayar RN-09 y transferencia en el entorno acordado.

**Condiciones de stop:** si el destino de restore no es inequívocamente distinto y vacío, si falta política de roles, si `ssl=false`, si el rol de API es propietario/superusuario, si la allowlist excluye accesos administrativos imprescindibles, si falta autorización para escrituras, **no seguir** y escalar a coordinación.

## 6. Recomendación de entrega

Enviar este informe, `02_MATRIZ_EVIDENCIAS.md`, `03_GUION_DEMO_14_MIN.md`, `04_PROCEDIMIENTO_FUTURO.md`, los logs **locales** y la propuesta aislada de comparador estricto en un único ZIP. La propuesta no altera ningún script original del kit ni exige merges/commits.

**Aprobación solicitada:** validar H1/H2 para robustecer comparador; validar inventario de migraciones/ACL y estrategia restore con José; aprobar matriz, orden de pruebas y guion antes de entrar a Supabase o desplegar.

### Fuentes documentales

- Consigna oficial entregada: `TPI_Bodegas_del_Atuel.pdf`, páginas impresas 18–19 (Etapa 8) y 20 (Etapa 9).
- Kit original `FASE8_KIT_FABRICIO.zip` y `FASE8_AUDITORIA_DESPLIEGUE_Y_VERIFICACION.md` entregados por coordinación, 08/11/2026.
- Control local: `control_integridad.sql` suministrado.
- Render Free: https://render.com/docs/free
- Render Outbound: https://render.com/docs/outbound-ip-addresses
- Supabase Network Restrictions: https://supabase.com/docs/guides/platform/network-restrictions
- PostgreSQL pg_dump: https://www.postgresql.org/docs/current/app-pgdump.html
- Supabase conexión: https://supabase.com/docs/guides/database/connecting-to-postgres

**Estas fuentes públicas son documentación, no evidencias de configuración real de la cuenta del grupo.**
