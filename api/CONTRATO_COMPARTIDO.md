# Contrato compartido - Fase 6 (versión inicial)

## Arquitectura

- FastAPI en `api/app/main.py`; se registra cada router con `app.include_router`.
- `api/app/routers/*.py`: solicitud HTTP y validación de respuesta. **No SQL**.
- `api/app/repositories/*.py`: una función por consulta, SQL explícito con `%s`.
- `api/app/services/*.py`: operaciones compuestas y transacciones que involucran varias sentencias.
- `api/app/schemas/*.py`: modelos de entrada y salida (Pydantic, no ORM).
- `api/app/core/database.py`: único pool compartido, disponible mediante `request.app.state.db_pool`.
- `api/app/core/errores.py`: única traducción de SQLSTATE a HTTP.

## API

- Rutas y recursos en español: `/vinos`, `/clientes`, `/comprobantes`, `/transferencias`,
  `/ingresos`, `/reportes/...`, `/salud`.
- Listados: usar `page` (inicia en 1), `page_size` (1 a 100, defecto 20),
  responder `{ "items": [], "total": 0, "pagina": 1, "tamanio": 20 }`.
- Errores de base: `{ "error": { "codigo": "23505", "mensaje": "..." } }`.
- `P0001` -> HTTP 409; FK / UNIQUE -> 409 según contexto; CHECK -> 422. Los códigos se
  resuelven en `core/errores.py` (no en cada router).
- Registrar los detalles de campos JSON en los schemas de cada módulo y contrastarlos con
  `db/migrations/001_esquema.sql` y constraints antes de programar.
- La API no cambia stock directamente ni calcula descuentos, subtotales o totales.
- No incorporar lógica nueva de negocio en Python que ya resuelva la BD.

## Reparto y convivencia Git

- Lautaro: `routers/vinos.py`, `repositories/vinos.py`, `schemas/vinos.py`, pruebas de vinos.
- Antonio: `routers/ingresos.py` y `transferencias.py`, repositorios/services asociados, pruebas.
- José: `routers/comprobantes.py`, `repositories/comprobantes.py`, services/tests de ventas.
- Fabricio: `routers/clientes.py` y `reportes.py`, repositorios y tests asociados.
- Valentino: `main.py`, `core/*`, configuración, documentación, Docker, integración y revisión.

**Semáforo de paralelización:** el código de módulos puede empezar en paralelo **después**
que se confirme y publique esta base y se comunique su commit. Mientras tanto cada integrante
puede analizar SQL, diseñar contratos JSON y preparar casos de pruebas sin modificar la base común.

No alterar `core`, `main.py`, `.env.example` o `docker-compose.yml` desde módulos sin coordinación.
