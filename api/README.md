# API de Bodegas del Atuel - Base común de Fase 6

Esta es la **base inicial**, no la API terminada. Contiene `/salud` conectado a PostgreSQL con
`psycopg` y `psycopg_pool`. Las rutas de negocio aún deben implementarse entre integrantes.

## Condiciones antes de ejecutar

- Python 3.11 o posterior; PostgreSQL 18 local para desarrollo.
- Base **descartable** `bodegas_fase6_dev`, restaurada desde el dump full del proyecto y con la
  migración `008_indices.sql` aplicada. No reutilizar `bodegas_fase5_integracion`.
- Rol de API `bodega_api` existente, con contraseña configurada de forma segura.
- Archivo `.env` en la raíz del repositorio, copiado desde `.env.example`, con credenciales reales
  solamente en la máquina. **Nunca versionar `.env`.**

## Comandos en PowerShell, desde la raíz `trabajo_integrador_bd`

```powershell
py -3 --version
py -3 -m venv .\.venv
.\.venv\Scripts\python.exe -m pip install -r .\api\requirements.txt
Copy-Item .\.env.example .\.env
notepad .\.env
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir api --host 127.0.0.1 --port 8000 --reload
```

**Importante:** no ejecutar Uvicorn hasta preparar la base y la contraseña de `bodega_api`.
En otro PowerShell:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/salud
```

Documentación automática: http://127.0.0.1:8000/docs

## Compromisos del equipo

- Los routers no escriben SQL: llaman a `repositories` / `services`.
- Todos los valores del usuario se pasan mediante parámetros `%s` de psycopg.
- Las ventas, transferencias e ingresos utilizan transacciones; no recalcular stock o totales en Python.
- Se usa únicamente el rol `bodega_api`, con permisos de la migración 007.
- Los módulos se reparten según `api/CONTRATO_COMPARTIDO.md`.
- No editar `docker-compose.yml` de fases anteriores hasta coordinar configuración nueva con volúmenes separados.
