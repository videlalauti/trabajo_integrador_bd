# Bodegas del Atuel — Trabajo Práctico Integrador de Bases de Datos

Sistema de gestión de bodegas desarrollado para el Trabajo Práctico Integrador de Bases de Datos, Ingeniería en Sistemas de Información. El proyecto abarca el modelado y las reglas de negocio en PostgreSQL, una API REST en FastAPI y una aplicación web en React.

**Estado de esta documentación (10 de noviembre de 2026):** Fases 1–7 implementadas y probadas en local; **Fase 8 desplegada en la nube y en proceso de cierre de aceptación**, con frontend y API públicos de solo lectura, base PostgreSQL FULL protegida y una segunda API aislada para ensayos controlados. La Fase 9 y la demostración operativa final siguen pendientes. La regla de negocio ya fue demostrada por HTTPS en la base ficticia aislada. La Fase 8 todavía requiere cerrar evidencia primaria de backup/restauración, controles de seguridad restantes y la aceptación del alcance de demostración con la cátedra.

## Fase 8 — versión pública HTTPS

- **Sitio web:** <https://bodegas-del-atuel.vercel.app>
- **API pública (H1, solo lectura):** <https://bodegas-atuel-api.onrender.com> — comprobación `GET /salud`, catálogo de vinos y ranking.
- **Base cloud:** PostgreSQL 17.11 en Supabase, proyecto FULL separado de los datos ficticios de ensayo.
- **API de ensayo aislada y protegida (no para uso anónimo):** <https://bodegas-atuel-demo-api.onrender.com>. La URL permite únicamente salud sin token; las pruebas de negocio requieren autorización y token privado. **Nunca escribir contra FULL.**
- **Informe de Fase 8:** [`fase8/CIERRE_Y_EVIDENCIAS.md`](fase8/CIERRE_Y_EVIDENCIAS.md).
- **Acta y pendientes de aceptación:** [`fase8/ACTA_CONTROL_FINAL_2026-11-10.md`](fase8/ACTA_CONTROL_FINAL_2026-11-10.md), con 27 conteos reales de FULL y pasos no destructivos para verificar backup/restore.
- **Código de demo en revisión:** [Draft PR #22](https://github.com/videlalauti/trabajo_integrador_bd/pull/22), separado de producción; commit candidato `9e7a07af9a7054c38e3a63f45fabca92aec22dcb`.

El frontend público mantiene voluntariamente bloqueadas las altas, ventas y transferencias: no se debe desactivar H1 para cumplir la demostración. El circuito de escritura **ya se verificó en la nube** sobre la segunda base ficticia: venta válida, RN-09 y transferencia con auditoría SQL independiente. Corresponde validar con la cátedra el alcance de esta demostración separada.

## Equipo

| Integrante | Responsabilidad principal en la Fase 7 |
| --- | --- |
| Lautaro | Catálogo de vinos, detalle, alta y edición |
| José | Formulario y registro de ventas |
| Antonio | Gestión y estados de transferencias |
| Fabricio | Tablero de reportes |
| Valentino | Infraestructura Docker/Nginx, rutas React, integración y pruebas conjuntas |

El proyecto se desarrolló en equipo; las responsabilidades por módulo no sustituyen el conocimiento común del modelo, la API y las reglas de negocio.

## Tecnologías y arquitectura

- **Base de datos:** PostgreSQL 18, con SQL explícito, restricciones, funciones, procedimientos, triggers y roles.
- **API:** Python, FastAPI, Pydantic, Psycopg 3 y pool de conexiones; consultas SQL parametrizadas, sin ORM.
- **Frontend:** React 19, TypeScript, Vite y React Router.
- **Contenedores:** Docker Compose; Nginx sirve el frontend compilado y reenvía `/api/` al servicio FastAPI.
- **Pruebas:** Pytest para la API y pruebas funcionales de integración sobre una base descartable.

Flujo de comunicación:

```text
Navegador → Nginx / React (puerto 8087)
                  │
                  └─ /api/* → FastAPI (servicio api:8000)
                                     │
                                     └─ Psycopg → PostgreSQL 18
```

Los **importes, descuentos y movimientos de stock** se determinan en el backend y en PostgreSQL. React muestra las respuestas de la API y los mensajes de error de las reglas de negocio.

## Requisitos

Para la ejecución integrada:

- Docker Desktop con Docker Compose disponible.
- Git para clonar el repositorio.
- Los archivos del repositorio, incluido `db/seed/dump_completo.sql.gz`, que utiliza el inicializador de PostgreSQL en el primer arranque.
- Dos contraseñas de uso local: una para `postgres` y otra para `bodega_api` (no se versionan).

Para ejecutar o desarrollar sin el frontend de Docker, también se requiere Node.js compatible con `front/package.json`; para ejecutar la API localmente se requiere Python y `api/requirements.txt`.

## Ejecución completa con Docker Compose (Windows / PowerShell)

**Importante:** todos los comandos de esta sección se ejecutan en **PowerShell, desde la carpeta raíz del repositorio** `trabajo_integrador_bd`, no desde `psql` ni desde `front/`.

### 1. Configurar credenciales para la sesión actual

```powershell
$adminSegura = Read-Host "Contraseña PostgreSQL para Docker" -AsSecureString
$apiSegura = Read-Host "Contraseña del rol bodega_api para Docker" -AsSecureString

$env:FASE6_PG_ADMIN_PASSWORD = [System.Net.NetworkCredential]::new("", $adminSegura).Password
$env:FASE6_API_PASSWORD = [System.Net.NetworkCredential]::new("", $apiSegura).Password

Remove-Variable adminSegura, apiSegura
```

En una instalación **nueva**, definir dos contraseñas seguras distintas. Si los contenedores ya se habían inicializado, utilizar las contraseñas **vigentes** de esa instalación: cambiar las variables no cambia las claves almacenadas en una base existente.

**No incluir contraseñas en commits, capturas, archivos `.env` versionados ni documentación.**

### 2. Validar y levantar los tres servicios

```powershell
docker compose -f .\compose.fase6.yml -f .\compose.fase7.yml config --quiet

docker compose -f .\compose.fase6.yml -f .\compose.fase7.yml up -d --build

docker compose -f .\compose.fase6.yml -f .\compose.fase7.yml ps
```

La primera puesta en marcha con un **volumen vacío** inicializa PostgreSQL, restaura el respaldo y configura los roles mediante `fase6/docker/01_inicializar_postgres.sh`. Las siguientes ejecuciones reutilizan el volumen existente: **no reaplicar las migraciones o el dump sobre una base ya restaurada**.

### 3. Verificar el funcionamiento

En PowerShell:

```powershell
Invoke-RestMethod http://127.0.0.1:8087/api/salud
Invoke-RestMethod http://127.0.0.1:8001/salud
```

La respuesta esperada de salud incluye `estado: ok` y `base_datos: conectada`.

En el navegador:

| Dirección | Función |
| --- | --- |
| <http://127.0.0.1:8087/> | Inicio y navegación de React |
| <http://127.0.0.1:8087/vinos> | Catálogo de vinos |
| <http://127.0.0.1:8087/vinos/nuevo> | Alta de vinos |
| <http://127.0.0.1:8087/ventas/nueva> | Nueva venta |
| <http://127.0.0.1:8087/transferencias> | Transferencias |
| <http://127.0.0.1:8087/reportes> | Tablero de reportes |
| <http://127.0.0.1:8001/docs> | Documentación interactiva Swagger de la API |

**Puertos predeterminados:** PostgreSQL `127.0.0.1:55438`, API `127.0.0.1:8001` y frontend `127.0.0.1:8087`. Los puertos publicados pueden configurarse mediante `FASE6_DB_HOST_PORT`, `FASE6_API_HOST_PORT` y `FASE7_FRONT_HOST_PORT`.

### Protección de los datos existentes

La composición Docker utiliza la base original `bodegas_fase6_docker` y su volumen persistente. **Las pruebas de escritura (alta/edición, ventas y transferencias) no deben realizarse contra esa base.** Para esas pruebas, utilizar una copia aislada, por ejemplo `bodegas_fase7_integracion_test`, con una instancia de API configurada expresamente para la copia.

Para detener los servicios sin borrar datos:

```powershell
docker compose -f .\compose.fase6.yml -f .\compose.fase7.yml stop
```

**No ejecutar `docker compose down -v`: eliminaría volúmenes y podría destruir datos.** No detener ni modificar contenedores ajenos al proyecto.

## Desarrollo y comprobaciones del frontend

El frontend usa la capa HTTP común `front/src/lib/api.ts`, que solicita rutas `/api/*` y conserva los mensajes de error devueltos por FastAPI. En desarrollo, `front/vite.config.ts` reenvía `/api` a `http://127.0.0.1:8001`.

Desde PowerShell en la raíz del repositorio:

```powershell
npm --prefix .\front ci
npm --prefix .\front run lint
npm --prefix .\front run build
```

Para abrir Vite en desarrollo, con la API de Fase 6 iniciada:

```powershell
npm --prefix .\front run dev
```

La aplicación suele quedar disponible en `http://localhost:5173/`. **El proxy de desarrollo predeterminado apunta a la API original**; no ejecutar pruebas que modifiquen datos allí. Las pruebas de integración de escritura se realizaron con una configuración local de Vite y una API independiente conectadas a la base descartable, sin versionar contraseñas ni esa configuración temporal.

## Funcionalidades implementadas en la Fase 7

1. **Catálogo de vinos:** paginación, filtros por tipo, cepa, bodega y añada; detalle con composición de cepas y maridajes.
2. **Alta y edición de vino:** formularios con catálogos reales, validación de campos y composición de cepas que debe sumar exactamente 100 %.
3. **Nueva venta:** elección de cliente y sala, renglones de vinos, confirmación del comprobante y total calculado en PostgreSQL; manejo del error de stock insuficiente.
4. **Transferencias:** creación, agregado de renglones, consulta y cambios de estado `en_confeccion → terminado → procesado`.
5. **Tablero de reportes:** ranking de los 10 vinos más vendidos, ventas por sala del último trimestre y vinos sin stock en la sala seleccionada.

La navegación de las pantallas está declarada en `front/src/App.tsx` y se conecta con los endpoints de `api/app/routers/`.

## Pruebas funcionales y reglas de negocio verificadas

Las pruebas de **escritura** se realizaron sobre `bodegas_fase7_integracion_test`, una copia descartable. La base original `bodegas_fase6_docker` se preservó. Se registraron las siguientes comprobaciones:

| Caso | Resultado observado |
| --- | --- |
| Alta de vino | Se creó el vino 751 en la base de pruebas; el catálogo pasó de 750 a 751 registros. |
| RN-13: auditoría de precio | Cambio de precio de 15.000 a 16.500 con registro en `auditoria_precio`. |
| Venta válida | Se confirmó el comprobante 150004 y se verificaron renglones y decremento de stock. |
| RN-09: stock insuficiente | Respuesta HTTP 409; sin comprobante parcial ni descuento indebido de existencias. |
| Transferencia | Solicitud 2001 procesada; depósito 9.822 → 9.821 y sala 4.232 → 4.233 para el vino 15. |
| Reportes | Ranking, ventas por sala y stock sin existencias para las salas consultadas. |
| RN-05: composición de cepas | React rechazó una composición del 90 %. Una petición directa a la API devolvió HTTP 409, SQLSTATE `P0001` y mensaje RN-05; PostgreSQL conservó 0 vinos con el nombre de prueba. |
| Docker | PostgreSQL, API y frontend activos; comprobación de salud y navegación entre pantallas. |

Evidencias de Valentino: [`fase7/evidencias/valentino/`](fase7/evidencias/valentino/). Las capturas complementarias de RN-05 deben publicarse en esa carpeta al realizar el último commit documental.

Los mensajes de reglas de negocio se originan en PostgreSQL y se traducen a respuestas HTTP mediante `api/app/core/errores.py`. No debe interpretarse un HTTP 422 por formato inválido como si fuera una demostración de RN-05; el caso válido de prueba fue HTTP 409 con `P0001`.

## Pruebas y documentación de las fases anteriores

- **Esquema, migraciones y reglas:** `db/migrations/`, incluidos los índices de la Fase 4.
- **Carga masiva y controles de integridad:** [`db/seed/README.md`](db/seed/README.md), `db/seed/run_seed.py` y `db/seed/control_integridad.sql`. La carga reproducible se debe ejecutar **solamente sobre una base nueva y descartable**.
- **Consultas SQL de la Fase 5:** `consultas/` (`update.sql`, `insert.sql`, `delete.sql`, `select.sql`).
- **API y pruebas automatizadas:** [`api/README.md`](api/README.md), `api/tests/` y Swagger en `/docs`.
- **Docker:** `compose.fase6.yml`, `compose.fase7.yml`, `front/Dockerfile` y `front/nginx.conf`.

Las pruebas automatizadas de API necesitan un entorno de pruebas debidamente configurado; no deben ejecutarse contra la base de datos original si pueden escribir registros.

## Estructura resumida

```text
trabajo_integrador_bd/
├── api/                     # FastAPI, SQL parametrizado y pruebas
├── consultas/               # Consultas SQL de la Fase 5
├── db/
│   ├── migrations/          # Esquema, reglas, permisos e índices
│   └── seed/                # Carga reproducible y respaldo
├── fase6/                   # Inicializador y evidencias de API/Docker
├── fase7/evidencias/        # Evidencias funcionales del frontend
├── front/                   # React + TypeScript + Vite + Nginx
├── compose.fase6.yml        # PostgreSQL y API
├── compose.fase7.yml        # Extensión con frontend
└── README.md
```

## Alcance y siguientes fases

La Fase 7 demuestra la integración **local** de los tres niveles y las reglas de negocio visibles en la interfaz. La **Fase 8 ya dispone de URLs públicas HTTPS** y de una arquitectura con bases FULL y DEMO separadas, con la regla de negocio cloud ya probada; su aceptación definitiva exige completar los controles de seguridad restantes y el acta de backup/restauración, según la [matriz final](fase8/ACTA_CONTROL_FINAL_2026-11-10.md). La Fase 9 reunirá el informe final, la trazabilidad completa de reglas y la defensa del equipo.

Repositorio: <https://github.com/videlalauti/trabajo_integrador_bd>
