# Matriz de evidencias — Etapa 8, Bodegas del Atuel

**Estado al 09/11/2026:** matriz planificada. Las pruebas offline del kit (8/8) y comparador estricto (9/9) constan en `pruebas_locales/`; **ninguna evidencia cloud ha sido ejecutada**. Las verificaciones son pendientes hasta registro auténtico.

| ID | Control | Prueba futura / comprobación esperada | Evidencia a conservar (sin secretos) | Responsable de apoyo | Estado |
|---|---|---|---|---|---|
| E01 | Render HTTPS público | Abrir `https://<render-real>/salud`; certificado válido, respuesta 200 | Captura URL, hora, JSON, SHA desplegado, log redactado | Antonio/Valentino | PENDIENTE CLOUD |
| E02 | Cold start Render Free | Primera solicitud tras inactividad; distinguir espera temporal de 503 persistente; reintento razonable | Tiempos de primer intento y segundo; logs sin secretos | Antonio | PENDIENTE CLOUD |
| E03 | Vercel HTTPS | Abrir dominio definitivo desde navegador sin VPN; certificado HTTPS válido | URL pública, fecha/hora y screenshot | Lautaro/Valentino | PENDIENTE CLOUD |
| E04 | Front→API y CORS/rewrite | Inspeccionar llamadas `/api/*`, respuesta real, navegación y recarga profunda `/reportes` | DevTools Network sin cookies/headers sensibles, captura SPA refrescada | Lautaro/Valentino | PENDIENTE CLOUD |
| E05 | Pantalla 1: Inicio/salud | Indicador de conexión API/DB y acceso público | Screenshot con URL del front | Valentino | PENDIENTE CLOUD |
| E06 | Pantalla 2: Vinos | Catálogo paginado, detalle y acción habilitada según rol | Screenshot datos reales y solicitud HTTP | Lautaro | PENDIENTE CLOUD |
| E07 | Pantalla 3: Ventas | Selección cliente/sala, venta de ensayo autorizada, totales backend | Screenshot y comprobante de ensayo identificado | José | PENDIENTE CLOUD |
| E08 | Pantalla 4: Transferencias | Estados y procesamiento controlado; stock pre/post cuando esté autorizado | Screenshot del flujo y operaciones acordadas | Antonio | PENDIENTE CLOUD |
| E09 | Pantalla 5: Reportes | Ranking, gráfico ventas de tres meses, selector de sala y paginación | Screenshots con valores reales y URL HTTPS | Fabricio | PENDIENTE CLOUD |
| E10 | Rol mínimo API | `current_user=bodega_api` en sesión backend, sin atributos elevados ni propiedad de objetos TP | Resultado administrativo redactado, ACL efectiva y prueba negativa | José/Antonio | PENDIENTE CLOUD |
| E11 | TLS DB API→Supabase | Comprobación **principal**: `bool(conn.pgconn.ssl_in_use)` en la conexión efectiva FastAPI (Session Pooler); `/salud` responde `"tls": true`, sin redirecciones. `pg_stat_ssl` solo complementario si se correlaciona la sesión | Respuesta `/salud` real por HTTPS, commit API, diagnóstico redactado del cliente libpq; no exponer secretos | José/Antonio | PENDIENTE CLOUD |
| E12 | Restricciones de red | CIDR Render compartidos + IP mantenimiento permitidas; rechazo autenticado desde origen excluido | Capturas reglas efectivas, origen permitido OK, origen excluido rechazado | José/Valentino | PENDIENTE CLOUD |
| E13 | Secretos y roles | Secretos solo variables proveedor; revisar historial Git y privilegios `anon/authenticated/PUBLIC` | Checklist redacción, inventario grants/roles sin contraseñas | José/Valentino | PENDIENTE CLOUD |
| E14 | Migraciones y objetos | `001` a `008` en orden y rol creador correcto; 27 tablas, rutinas, índices, constraints, triggers habilitados | Hash/registro migraciones, salidas SQL, diferencias origen/destino | José | PENDIENTE CLOUD |
| E15 | Integridad y volumen | `control_integridad.sql`: 27 tablas, FK huérfanas=0, stock negativo=0, totales coherentes | Salida por tabla; justificar carga reducida cloud (>=10000 en una) | José/Fabricio | PENDIENTE CLOUD |
| E16 | RN-09 y rollback | Ensayo sin stock con antes/rechazo/después: no nuevo comprobante/renglón ni alteración de stock | Capturas frontend/error negocio, consultas pre/post consistentes | José/Fabricio | PENDIENTE CLOUD |
| E17 | Backup lógico | `pg_dump` cloud sobre esquema aprobado, copia fuera de Git, tamaño y hash SHA-256 | Comando sin secretos, versión herramienta, tamaño/hash, archivo fuera del repo | José/Fabricio | PENDIENTE AUTORIZACIÓN |
| E18 | Restauración independiente | `pg_restore` solo en PostgreSQL 17 Docker local nuevo aprobado; reconstrucción de roles/ACL antes de habilitar acceso | Contenedor/base independientes acreditados, log, lista del dump, ausencia de errores | José/Fabricio | PENDIENTE AUTORIZACIÓN |
| E19 | Conteos restauración | Exportar CSV de 27 tablas en origen/destino dentro de ventana estable; igualdad exacta | CSV reales protegidos, comparador estricto y salida con 27 OK | Fabricio | PENDIENTE CLOUD |
| E20 | Permisos pos-restore | Comparar propietarios, SECURITY DEFINER, search_path, EXECUTE, triggers, FK y ACL | Inventario comparado firmado/revisado por José | José/Fabricio | PENDIENTE CLOUD |
| E21 | Informe final / límites gratis | Proveedor elegido vs alternativa, región, plan, inactividad, límites y URL pública | README con links, pasos reproducibles y limitaciones | Valentino | PENDIENTE CLOUD |

## Criterios generales para toda captura

- Identificar **fecha/hora**, servicio, URL real HTTPS, escenario concreto y SHA desplegado cuando corresponda.
- Nunca mostrar claves, cookies, tokens, encabezados `Authorization`, contraseñas, connection strings, certificados privados ni PII no necesaria.
- No colocar en Git dumps ni CSV de datos personales o credenciales. La evidencia de trabajo se clasifica y publica **solo después de revisión**.
- Captura del frontend debe corresponder al código/commit desplegado: evitar el error de Fase 7 de capturar una versión anterior.
- Las evidencias deben distinguir claramente **servicios reales** de **ejemplos ficticios locales**.
- La validación del sistema exige varios controles independientes; un `/salud` 200 o conteos iguales no bastan solos.

## Orden sugerido de recopilación (cuando coordinación lo autorice)

1. SHA y URL pública HTTPS (E01–E04); verificar Render frío/activo.
2. Rol, TLS y red antes de escrituras (E10–E13).
3. Migraciones, integridad, volumen y 5 pantallas reales (E05–E09, E14–E15).
4. RN-09 con rollback, únicamente con caso de ensayo autorizado (E16).
5. Backup/restore en destino independiente y comprobaciones de 27 tablas, rutinas y ACL (E17–E20).
6. Documentar limitaciones y procedimiento reproducible (E21).

## Estado por entorno y responsable

| Entorno | Evidencias | Estado actual | Próximo desbloqueo |
|---|---|---|---|
| Offline ficticio | Test kit 8/8, test comparador 9/9, rechazo 24 tablas faltantes | COMPLETADO LOCAL (resultados reproducibles) | Ninguno |
| Supabase | E10–E16, E17 origen, E19 conteos, E20 comparación | PENDIENTE CLOUD y autorización para escritura/backup | José certifica FULL y accesos |
| Render | E01–E02, E04 backend, E11 sesión API | PENDIENTE RENDER | Antonio/Valentino publican API |
| Vercel | E03–E09 | PENDIENTE VERCEL | Lautaro/Valentino publican front |
| Docker local PostgreSQL 17 | E18 restore, E19–E20 comparación | PENDIENTE RESTORE REAL; ensayo ficticio opcional | Docker disponible, backup autorizado y roles aprobados |

Los archivos ficticios NO constituyen evidencias de 27 tablas restauradas.
