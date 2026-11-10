# Etapa 8/9 — Preparacion de demo segura AISLADA

**Estado: CANDIDATO; probado sobre PostgreSQL 17 DESCARTABLE en GitHub Actions (migraciones 8/8, seed small, venta 201, RN-09 409/rollback, transferencia y EXPLAIN). NO DESPLEGADO EN NUBE. NO MERGE.**

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

El workflow de GitHub Actions repite los tests en Python 3.13 y 3.14. Estos tests prueban autorizacion, lista de rutas, rechazo de FULL, validacion TLS y secuencia de negocios SIMULADA: no se declaran probados los triggers en la nube.

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

## Paso cloud: PENDIENTE, no autorizado todavia
- Supabase Free permite actualmente dos proyectos activos; la cuenta conectada tiene uno. Confirmar con el usuario la ORGANIZACION y el precio $0 antes de crear el segundo.
- Preparar dataset minimo ficticio y usuarios/ACL en nuevo proyecto cloud; NO restaurar el dump FULL ni copiar datos personales.
- Render Free comparte 750 horas de instancia mensuales por workspace. Un segundo servicio con api/Dockerfile.demo debe mantener otra URL/clave/variables, sin modificar Render H1.
- Verificar preflight autentico y casos sobre base de ensayo, registrar logs sin secretos, EXPLAIN de solo lectura y defender la equivalencia con la catedra.
- No modificar Supabase FULL, Network Restrictions actuales ni el frontend Vercel productivo.

Fuente: TPI_Bodegas_del_Atuel.pdf (Etapas 8 y 9); docs vigentes de Render Free y Supabase Free consultados el 10/11/2026.

## Evidencia real de PostgreSQL descartable en CI (10/11/2026)

- [GitHub Actions, ejecución completa](https://github.com/videlalauti/trabajo_integrador_bd/actions/runs/42840387018): 8 migraciones reales, perfil small, API FastAPI alternativa autenticada, venta 201, rechazo RN-09 409/P0001 con conteos y stock invariantes, transferencia procesada y EXPLAIN (ANALYZE, BUFFERS) de una consulta SELECT; **SUCCESS**.
- Comprobante de venta de ensayo número 101 y transferencia de ensayo número 11; estos IDs pertenecen únicamente al contenedor efímero de GitHub.
- El plan de consulta pequeña mostró Hash Join + HashAggregate + Sort/Limit, tiempo de ejecución aprox. 0,211 ms. No extrapolar ese valor a FULL en Supabase.
- CI adicional fail-closed con Python 3.13 y 3.14: 61 pruebas offline aprobadas por versión.
- Estas evidencias **no sustituyen** demostrar al menos una regla dentro de la nube del proyecto de ensayo y no acreditan que las operaciones de escritura puedan ejecutarse en Render productivo (continúa H1).
