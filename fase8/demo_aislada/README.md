# Etapa 8/9 — Preparacion de demo segura AISLADA

**Estado: CANDIDATO; backend de demostracion aun NO desplegado en Render y PR sin fusionar. PostgreSQL 17 de Github Actions probado con seed small; PostgreSQL 17.11 de Supabase DEMO preparado (27 tablas, 32 FK, RLS), dataset minimo ficticio y reglas ejecutadas en CLOUD con ROLLBACK. Produccion FULL intacta.**

## Objetivo y alcance
- Etapa 8, consigna p.19: demostrar una regla de negocio en la nube.
- Etapa 9, p.20: venta valida, rechazo RN-09 con rollback, transferencia y consulta SQL con plan.
- Reutiliza los routers/services/rutinas del TP. La BD calcula importes y stock.

## Separacion de entornos
- La aplicacion publica de lectura continua usando api/app/main.py y api/Dockerfile, sin cambios ni desactivacion de H1.
- Una SEGUNDA API de ensayo usa api/app/demo_main.py y api/Dockerfile.demo; no se usa el servicio Render de produccion.
- La configuracion exige FASE8_DEMO_MODE=aislado y FASE8_DEMO_TOKEN aleatorio de 48 o mas caracteres.
- Prohibida la referencia Supabase FULL sjfyocokehaubuwwbhnw, aun con un token correcto.
- Cloud: otro Supabase diferente, FASE8_DEMO_PROJECT_REF especifica, DB_USER=bodega_api.<REF_DEMO>, host de Session Pooler, DB_PORT=5432, DB_SSLMODE=verify-full y DB_SSLROOTCERT.
- Local: DB_HOST=127.0.0.1, DB_NAME=bodegas_fase8_demo_local, DB_USER=bodega_api y FASE8_DEMO_LOCAL=1.
- Excepto /salud, todas las rutas autorizadas requieren Authorization Bearer. Solo se habilitan POST /comprobantes, POST /transferencias y los pasos de cargar renglon, terminar y procesar. Se bloquean PUT, DELETE, alta de vinos, CRUD clientes e ingresos.

## Pruebas offline, sin BD ni secretos
Desde la raiz, Python 3.13 o 3.14 y dependencias de api/requirements.txt:

    $env:PYTHONPATH = "api;fase8/demo_aislada"
    python -m pytest -q api/tests/test_demo_guard.py fase8/demo_aislada/test_cli_offline.py fase8/demo_aislada/test_circuitos_simulados.py

El workflow de GitHub Actions repite los tests en Python 3.13 y 3.14. Estos tests offline prueban autorizacion, lista de rutas, rechazo de FULL, validacion TLS y secuencia de negocios SIMULADA. Por separado, una prueba SQL transaccional de PostgreSQL en Supabase DEMO comprobo las reglas de negocio de forma real, sin persistir ventas ni transferencias.

## Preparacion local antes de cloud
1. Crear una base PostgreSQL 17 NUEVA y descartable llamada bodegas_fase8_demo_local. No usar el contenedor restaurado de G1-C ni las bases FULL.
2. Aplicar las migraciones REALES del repo en orden: 001_esquema.sql, 002_constraints.sql, 003_funciones.sql, 004_procedimientos.sql, 005_triggers.sql, 006_vistas.sql, 007_roles.sql, 008_indices.sql.
3. Crear la clave exclusiva de bodega_api con psql interactivo (no poner password en historial ni scripts).
4. Cargar PROFILE=small mediante db/seed/run_seed.py en esa base solamente, previa comprobacion --check. Nunca usar PGDATABASE=postgres.
5. Arrancar la app alternativa desde api con el entorno local, usando:
   python -m uvicorn app.demo_main:app --host 127.0.0.1 --port 8002
6. El script fase8/demo_aislada/ejecutar_demo.py hace solo GET por defecto:
   python fase8/demo_aislada/ejecutar_demo.py
7. Solo tras aprobar la base de prueba, ejecutar UNA VEZ la prueba autorizada:
   python fase8/demo_aislada/ejecutar_demo.py --ejecutar --confirmar-demo SOLO_BASE_DESCARTABLE
   Comprueba venta 201, RN-09 409/P0001 y rollback, transferencia deposito -1 y sala +1.
8. Si una escritura devuelve respuesta ambigua, STOP sin reintentar: puede haber confirmado transacciones.

## Paso Render DEMO: PENDIENTE; no ejecutar todavia
- Segundo proyecto Supabase FREE creado por costo cotizado US$0/mes, autorizado por el usuario y separado de la FULL.
- Migraciones aplicadas, rol API y dataset MINIMO ficticio creados en Supabase DEMO. No se restauro el dump FULL ni se copiaron datos personales.
- Render Free comparte 750 horas de instancia mensuales por workspace. Un segundo servicio con api/Dockerfile.demo debe mantener otra URL/clave/variables, sin modificar Render H1.
- Verificar preflight autentico y casos sobre base de ensayo, registrar logs sin secretos, EXPLAIN de solo lectura y defender la equivalencia con la catedra.
- No modificar Supabase FULL, Network Restrictions actuales ni el frontend Vercel productivo.

Fuente: TPI_Bodegas_del_Atuel.pdf (Etapas 8 y 9); docs vigentes de Render Free y Supabase Free consultados el 10/11/2026.

## Estado de infraestructura Supabase DEMO (10/11/2026)

- Organización seleccionada por coordinación: `ValentinoUTN`; costo de alta confirmado por Supabase: **US$0 mensuales**.
- Proyecto aislado creado: `bodegas-atuel-demo-aislada`, referencia **`zfxocudcvriicrzgmxie`**, región **`us-west-1`**, PostgreSQL **17.11**.
- Proyecto productivo FULL diferente: `sjfyocokehaubuwwbhnw` (region `us-west-2`); permanece protegido con H1.
- Estado actual: `ACTIVE_HEALTHY`, `current_database()=postgres`, **27 tablas, 32 FK, 27/27 RLS y 27 politicas solo para roles internos**.
- Se aplicaron 001, 002, 003, 004, 005, 006, 008 del repositorio, más la adaptación documentada de 007 para `postgres` sin SUPERUSER de Supabase.
- Se cargó un **dataset MINIMO**, distinto del perfil `small`: 1 bodega, 2 salas, 3 vinos, 2 clientes, 360 botellas en depósito y 165 en salas. No hay ventas ni transferencias persistidas.
- `bodega_api`: creado con contraseña NULL, sin acceso remoto hasta que se defina una clave exclusiva de ensayo. Tiene INSERT de comprobantes y EXECUTE sobre procedimientos; carece de UPDATE sobre stock. Los roles `anon`, `authenticated` y `service_role` no tienen SELECT de las tablas sensibles.
- Supabase Security Advisors: **0 lints de seguridad**. Avisos informativos de rendimiento sobre 17 FK sin indice; no se cambiaron las migraciones aprobadas.
- **Pendientes:** configurar Network Restrictions exclusivamente del segundo proyecto, contraseña diferente de producción y segundo Render con auto-deploy OFF. No pedir ni subir la contraseña a GitHub o chat.

## Evidencia real de PostgreSQL descartable en CI (10/11/2026)

- [GitHub Actions, ejecución completa](https://github.com/videlalauti/trabajo_integrador_bd/actions/runs/42840387018): 8 migraciones reales, perfil small, API FastAPI alternativa autenticada, venta 201, rechazo RN-09 409/P0001 con conteos y stock invariantes, transferencia procesada y EXPLAIN (ANALYZE, BUFFERS) de una consulta SELECT; **SUCCESS**.
- Comprobante de venta de ensayo número 101 y transferencia de ensayo número 11; estos IDs pertenecen únicamente al contenedor efímero de GitHub.
- El plan de consulta pequeña mostró Hash Join + HashAggregate + Sort/Limit, tiempo de ejecución aprox. 0,211 ms. No extrapolar ese valor a FULL en Supabase.
- CI adicional fail-closed con Python 3.13 y 3.14: 61 pruebas offline aprobadas por versión.
- Estas evidencias locales se complementaron con pruebas transaccionales en la BD **Supabase DEMO cloud**; todavía NO se ha probado la API DEMO desplegada en Render, y Render productivo sigue con H1.

## Ejecucion real en Supabase DEMO (10/11/2026)

Los siguientes archivos fueron aplicados **exclusivamente** al proyecto `zfxocudcvriicrzgmxie`:

1. `sql/00_preparacion_supabase_demo.sql`: centinela de identidad de proyecto y revocacion de grants por defecto de la Data API; validado con permisos ausentes.
2. Migraciones originales de `db/migrations/` 001 a 006 y 008, con guard de identidad de proyecto.
3. `sql/01_datos_minimos_ficticios.sql`: insertados únicamente datos sinteticos minimos, no el seed small.
4. `sql/02_roles_supabase_demo.sql`: adaptacion de 007 que omite cambio global TEMPORARY/CREATE a PUBLIC y sentencias ALTER ROLE NOSUPERUSER no permitidas en Supabase postgres. La ejecucion inicial fue rechazada y quedo revertida; la variante corregida se aplico con exito.
5. `sql/03_rls_supabase_demo.sql`: RLS en las 27 tablas, policies a roles técnicos internos; ningún acceso Data API de anon/authenticated para los datos.
6. `sql/05_prueba_transaccional_cloud_rollback.sql`: prueba mediante `bodega_api` dentro de una transacción de ensayo con `ROLLBACK`. Comprobó venta válida, rechazo RN-09 SQLSTATE P0001 con rollback del encabezado fallido, y transferencia terminada/procesada con conservación de stock. No conservó la venta ni la transferencia: 0 y 0; los totales permanecieron 165 y 360. Los valores de secuencias no son transaccionales y pueden avanzar.
7. `sql/04_control_cloud_solo_lectura.sql`: verificación final SELECT de estructura, política, roles, datos ficticios y conservación del estado.

**No se proporcionó ninguna contraseña de PostgreSQL a GitHub Actions ni se desplegó un nuevo Render.** Se usó el conector administrativo Supabase solo en el proyecto separado.
