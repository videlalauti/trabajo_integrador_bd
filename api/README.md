
# API REST — Bodegas del Atuel

## 1. Descripción

API REST desarrollada para la Fase 6 del Trabajo Práctico Integrador de Bases de Datos.

Tecnologías utilizadas:

- Python 3.14 y FastAPI.
- PostgreSQL 18.
- Psycopg 3 y psycopg_pool.
- Pydantic para validación de datos.
- Pytest para pruebas automatizadas.
- Docker y Docker Compose.

La aplicación ofrece 27 endpoints funcionales y un endpoint adicional de salud.

La lógica de integridad, los cálculos de ventas, las actualizaciones de stock y las reglas de negocio se mantienen en PostgreSQL.

## 2. Arquitectura

- `app/main.py`: aplicación FastAPI y registro de routers.
- `app/routers/`: endpoints HTTP.
- `app/schemas/`: modelos de entrada y salida.
- `app/repositories/`: consultas SQL parametrizadas.
- `app/services/`: operaciones compuestas y transacciones.
- `app/core/database.py`: pool compartido de conexiones.
- `app/core/config.py`: configuración por variables de entorno.
- `app/core/errores.py`: tratamiento centralizado de errores SQLSTATE.
- `tests/`: pruebas automatizadas e integración con PostgreSQL.

No se utiliza un ORM. Las consultas SQL son explícitas y utilizan parámetros de Psycopg.

## 3. Endpoints implementados

### Vinos — 5 endpoints

| Método | Ruta | Función |
|---|---|---|
| GET | `/vinos` | Listar vinos con filtros y paginación |
| GET | `/vinos/{cod_vino}` | Consultar un vino |
| POST | `/vinos` | Crear un vino |
| PUT | `/vinos/{cod_vino}` | Actualizar un vino |
| DELETE | `/vinos/{cod_vino}` | Eliminar un vino |

### Comprobantes — 2 endpoints

| Método | Ruta | Función |
|---|---|---|
| GET | `/comprobantes/{nro_comprobante}` | Consultar una venta |
| POST | `/comprobantes` | Registrar una venta completa |

### Ingresos — 5 endpoints

| Método | Ruta | Función |
|---|---|---|
| POST | `/ingresos` | Crear ingreso |
| GET | `/ingresos/{cod_ingreso}` | Consultar ingreso |
| POST | `/ingresos/{cod_ingreso}/renglones` | Agregar renglón |
| POST | `/ingresos/{cod_ingreso}/terminar` | Terminar ingreso |
| POST | `/ingresos/{cod_ingreso}/procesar` | Procesar ingreso |

### Transferencias — 5 endpoints

| Método | Ruta | Función |
|---|---|---|
| POST | `/transferencias` | Crear transferencia |
| GET | `/transferencias/{nro_solicitud}` | Consultar transferencia |
| POST | `/transferencias/{nro_solicitud}/renglones` | Agregar renglón |
| POST | `/transferencias/{nro_solicitud}/terminar` | Terminar transferencia |
| POST | `/transferencias/{nro_solicitud}/procesar` | Procesar transferencia |

### Clientes — 5 endpoints

| Método | Ruta | Función |
|---|---|---|
| GET | `/clientes` | Listar clientes |
| GET | `/clientes/{id_cliente}` | Consultar cliente |
| POST | `/clientes` | Crear cliente |
| PUT | `/clientes/{id_cliente}` | Actualizar cliente |
| DELETE | `/clientes/{id_cliente}` | Eliminar cliente |

### Reportes — 5 endpoints

| Método | Ruta | Función |
|---|---|---|
| GET | `/reportes/top-vinos` | Diez vinos más vendidos |
| GET | `/reportes/ventas-por-sala` | Ventas del último trimestre |
| GET | `/reportes/vinos-sin-stock` | Vinos sin stock en una sala |
| GET | `/reportes/transportista-activo` | Transportista con mayor actividad |
| GET | `/reportes/trazabilidad/{cod}` | Trazabilidad limitada de un vino |

### Salud

`GET /salud`: verifica la conexión a PostgreSQL con el rol `bodega_api`.

## 4. Ejecución local

Requisitos:

- Python 3.11 o posterior.
- PostgreSQL 18.
- Base restaurada `bodegas_fase6_dev`.
- Rol `bodega_api` con permisos de la migración 007.
- Archivo `.env` local, creado a partir de `.env.example`.

Desde la raíz del repositorio, en PowerShell:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r .\api\requirements.txt

.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir api --host 127.0.0.1 --port 8001
```

La contraseña de PostgreSQL debe configurarse en `.env`, que no se versiona.

## 5. Ejecución mediante Docker Compose

La Fase 6 utiliza `compose.fase6.yml`, independiente del `docker-compose.yml` original.

Servicios:

- `db`: PostgreSQL 18.
- `api`: FastAPI con Python 3.14.

Puertos publicados:

- PostgreSQL: `127.0.0.1:55438`.
- FastAPI: `127.0.0.1:8001`.

Volumen persistente:

- `bodegas-atuel-fase6_postgres18_fase6_data`.



### Configuración de credenciales en PowerShell

Antes de ejecutar Docker Compose, definir las contraseñas
de PostgreSQL y de la API.

Desde la raíz del repositorio:

```powershell
$adminSecure = Read-Host "Clave de postgres de Docker" -AsSecureString
$apiSecure = Read-Host "Clave de bodega_api de Docker" -AsSecureString

$env:FASE6_PG_ADMIN_PASSWORD = [System.Net.NetworkCredential]::new("", $adminSecure).Password
$env:FASE6_API_PASSWORD = [System.Net.NetworkCredential]::new("", $apiSecure).Password

Remove-Variable adminSecure, apiSecure

docker compose -f .\compose.fase6.yml config --quiet
```

Utilizar contraseñas distintas y seguras.

Estas variables permanecen únicamente en la sesión actual
de PowerShell. Si se abre otra terminal, deben configurarse
nuevamente.

IMPORTANTE: si PostgreSQL ya fue inicializado en un volumen,
deben reutilizarse las contraseñas correspondientes a ese
entorno. Cambiar una variable de Docker Compose no modifica
automáticamente la contraseña almacenada en PostgreSQL.

Nunca escribir las contraseñas en el repositorio ni
compartirlas en las evidencias.




### Preparación inicial

Para preparar una instalación nueva de Docker, se necesita el
respaldo validado `db/seed/dump_completo.sql.gz`.

Desde PowerShell, en la raíz del repositorio:

**1. Configurar las contraseñas**

Definir las variables `FASE6_PG_ADMIN_PASSWORD` y
`FASE6_API_PASSWORD`, siguiendo las instrucciones de la
sección anterior.

**2. Iniciar únicamente PostgreSQL**

```powershell
docker compose -f .\compose.fase6.yml up -d db
```

**3. Verificar la base antes de restaurar**

```powershell
.\.venv\Scripts\python.exe .\fase6\docker\inicializar.py --check
```

En una base nueva debe aparecer:

`Base vacia: apta para inicializacion.`

**4. Inicializar la base vacía**

```powershell
.\.venv\Scripts\python.exe .\fase6\docker\inicializar.py --run
```

El programa solicita escribir `INICIALIZAR` para confirmar.

Realiza automáticamente:

- Verificación SHA-256 del respaldo.
- Creación de los nueve roles de PostgreSQL.
- Restauración del respaldo completo de Fase 3.
- Aplicación de los cinco índices de Fase 4.
- Configuración de contraseña y privilegios de `bodega_api`.
- Verificación de las 27 tablas, los cinco índices y el rol.

**5. Iniciar FastAPI**

```powershell
docker compose -f .\compose.fase6.yml up -d --no-build api
```

Si la imagen todavía no fue construida, utilizar
`docker compose -f .\compose.fase6.yml up -d --build api`.

**Seguridad:** el inicializador rechaza la restauración si
detecta objetos existentes en la base. No utilizar `--run`
sobre una base que ya contiene datos.

El procedimiento requiere el respaldo completo validado,
que debe entregarse junto al proyecto o proporcionarse
mediante el mecanismo acordado con la cátedra.


## 6. Seguridad

La API utiliza exclusivamente el usuario PostgreSQL `bodega_api`.

Este usuario:

- No es superusuario.
- Posee permisos limitados mediante `bodega_api_rw`.
- No puede modificar directamente `stock_deposito` ni `stock_sala`.
- Ejecuta operaciones de negocio respetando las funciones, procedimientos, triggers y restricciones de PostgreSQL.

Los errores SQLSTATE se traducen a respuestas HTTP, incluyendo conflictos de integridad y reglas de negocio.

Las credenciales se gestionan mediante variables de entorno y archivos locales excluidos de Git.

## 7. Pruebas

Los módulos tienen 66 pruebas automatizadas aprobadas:

| Responsable | Módulo | Pruebas |
|---|---|---:|
| Lautaro | Vinos | 12 |
| José | Comprobantes | 11 |
| Antonio | Ingresos y transferencias | 12 |
| Fabricio | Clientes y reportes | 31 |
| Total | | 66 |

Las pruebas de integración se ejecutaron por módulo utilizando bases descartables separadas.

Adicionalmente, se validaron:

- Registro de los 27 endpoints en OpenAPI.
- 11 consultas HTTP exitosas desde Docker.
- Restauración de 27 tablas y verificación de 32 claves foráneas.
- Ausencia de stock negativo e inconsistencias en comprobantes.
- Cinco índices de la Fase 4.
- Permisos limitados de `bodega_api`.
- Demostración de inyección SQL fallida mediante consultas parametrizadas.

La evidencia de inyección SQL se encuentra en:

`fase6/evidencias/valentino/inyeccion_sql_fallida.txt`

## 8. Integración del equipo

- Lautaro: módulo Vinos.
- José: módulo Comprobantes.
- Antonio: módulos Ingresos y Transferencias.
- Fabricio: módulos Clientes y Reportes.
- Valentino: infraestructura compartida, configuración, manejo de errores, Docker, seguridad e integración general.

La integración de los módulos se realizó en la rama `integracion/fase6`.

El proyecto mantiene las reglas de negocio en PostgreSQL y utiliza FastAPI como capa HTTP.
