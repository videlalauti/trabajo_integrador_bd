# Plan operativo — Fase 8 · Bodegas del Atuel

Fecha: 2026-11-07. Estado: **plan de ejecución; no equivale a despliegue realizado**.

## Fuentes de verdad y punto de partida

1. `TPI_Bodegas_del_Atuel.pdf`, Etapa 8, pp. 18–19 (10 pasos, requisitos y criterios).
2. Código y migraciones de `integracion/fase7` (commit base `39f1fbedb31891c3d3927d17e9fbc0fba25168e1`).
3. Evidencias reales de pruebas locales y luego de la nube.
4. Este plan de coordinación, sujeto a las pruebas.

**Rama de integración para esta etapa:** `integracion/fase8`. **No integrar a `main` hasta aprobar las puertas de calidad.** No reescribir las fases previas.

## Objetivo y aceptación (no negociables)

- PostgreSQL alojado fuera de las computadoras del equipo, con migraciones `001`–`008` efectivamente aplicadas en orden y tres roles: propietario/administración, API con privilegios mínimos y reportes solo lectura.
- API y React accesibles públicamente mediante HTTPS; `/salud` consulta la BD con el usuario `bodega_api`.
- Conexión API→PostgreSQL cifrada (configuración explícita de `sslmode`; verificar con `pg_stat_ssl` o prueba equivalente).
- Puerto PostgreSQL **no abierto indiscriminadamente a Internet**: permitir únicamente orígenes autorizados o usar red privada. Probar rechazo de origen no autorizado. Contraseña + TLS **solos** no acreditan restricción de red.
- Variables de entorno y secretos en dashboards, nunca archivos versionados ni capturas; inspeccionar historial Git.
- Datos en nube: completa o versión reducida con **más de 10.000 registros en al menos una tabla** (usar objetivo prudente ≥12.000) y justificar; base local `full` conservada.
- Ejecutar consultas de integridad (filas, FK, totales, stock, composición) y prueba real del trigger RN-09 en la nube; demostrar rollback.
- Crear backup real con `pg_dump` y restaurar en una **base nueva** usando `pg_restore` / `psql`; comparar conteos originales/restaurados y probar consultas; documentar privilegios y objetos.
- README con URLs públicas reales, comandos y verificación, más capturas/evidencias auténticas.

## Proveedores (decisión condicionada por puertas de calidad)

**Candidato A:** Vercel Hobby (React Vite) + Render Free (FastAPI) + Supabase Free (PostgreSQL). No crear servicios definitivos antes de comprobar:
- Que la cuenta gratuita de Supabase deja aplicar **Network Restrictions** a PostgreSQL y pooler, sin pagar.
- Que el servicio Render puede salir de rangos CIDR identificables (Render publica rangos compartidos por región), permitir sólo esos rangos y documentar que no son IP exclusivas.
- Que las migraciones `001`–`008`, sobre todo `007_roles.sql` (`CREATE ROLE`, privilegios, propietarios, `SECURITY DEFINER`), funcionan/admiten adaptación controlada sin desproteger el esquema.
- Que Render accede al **pooler IPv4** adecuado con TLS y transacciones correctas.
- Que Supabase Free ofrece espacio suficiente: 500 MB; calcular tamaño real después de seed.
- Que Vercel Hobby es apropiado para proyecto académico no comercial y la API puede utilizar un rewrite `/api/:path*` a URL externa.

**Neon Free:** descartado de manera provisional si su allowlist sigue siendo sólo de planes pagos; no afirmar aceptación por TLS/contraseña solamente.

**Plan B si falla la seguridad del A:** infraestructura en una VM Always Free (p. ej., Oracle Cloud, condicionada a disponibilidad/alta) con Docker Compose; exponer únicamente HTTPS, PostgreSQL en red interna sin `ports` al exterior. No afirmar gratuidad garantizada o capacidad disponible sin verificar cuenta. La consigna admite VM, pero no la exige.

Documentación oficial a revisar al ejecutar:
- https://supabase.com/docs/guides/platform/network-restrictions
- https://supabase.com/pricing
- https://render.com/docs/free
- https://render.com/docs/outbound-ip-addresses
- https://vercel.com/docs/routing/rewrites
- https://neon.com/pricing

## Reparto en paralelo

| Responsable | Rama individual sugerida | Archivos propios / área | Entrega y prueba |
|---|---|---|---|
| José | `fase8-jose-postgres` | `db/` + scripts SQL cloud acotados | Diagnóstico de migraciones, roles, perfil cloud ≥12.000 filas, conteos/integridad y bloqueo real de red |
| Antonio | `fase8-antonio-api` | `api/`, definición Render | TLS, conexiones `bodega_api`, tamaño de pool, configuración segura, `/salud` y pruebas con BD |
| Lautaro | `fase8-lautaro-front` | `front/`, `vercel.json` **dentro de `front/`** | Build, SPA fallback, rewrite `/api` sin alterar rutas, URL pública y pantallas |
| Fabricio | `fase8-fabricio-verificacion` | `fase8/verificacion/` | Procedimientos `pg_dump` / restauración a nueva BD, comparación, RN-09 negativa y capturas con resultados |
| Valentino | `integracion/fase8` y `docs/`/README al cerrar | Proveedores, coordinación, cuentas compartidas sin exponer secretos, revisión, integración, evidencia y entrega | Checklist firmado contra consigna, demo end-to-end y README final |

**Convención:** nadie modifica archivos de otro módulo ni `README.md` raíz hasta integración. Mantener la autoría humana real de commits. Nunca usar `git add .` ni `push --force`. Cada autor entrega PR a `integracion/fase8` tras revisión.

### Dependencias y trabajo simultáneo

- Minuto 0: Valentino confirma proveedores y contrato de rutas/variables; **a la vez** José audita migraciones, Antonio prepara configuración y Lautaro prepara Vercel; Fabricio escribe scripts de pruebas sin ejecutar cambios.
- Una vez aprobada red/roles y creada BD: José aplica migraciones/carga; Antonio prueba la conexión con `bodega_api`; Fabricio prueba controles en la BD.
- Una vez que /salud responde en URL pública: Lautaro prueba el rewrite; Fabricio realiza respaldo/restauración; Valentino coordina flujos de venta, transferencias y trigger.
- Sin acceso a cuenta/servicio el responsable puede preparar y probar localmente, pero **no** afirmar que probó en nube.

## Jornada de referencia (tiempos orientativos; sin promesa)

- 0–1 h: decisiones bloqueantes, seguridad/red, estructura Git y configuración.
- 1–3 h: PostgreSQL cloud/compatibilidad, mientras API/front y verificación avanzan en paralelo.
- 3–5 h: despliegue API/front y datos, pruebas de extremos.
- 5–7 h: seguridad, integridad, backup/restauración, trigger, validación cruzada.
- 7–9 h: capturas, informe/README, PRs, integración y verificación final.
- Reservar margen para límites del proveedor, altas, fallos de roles o red; una jornada es objetivo, no resultado.

## Contrato técnico inicial

- API actual: FastAPI `api/app/main.py`; conexión en `api/app/core/{config,database}.py` y usuario obligatorio `bodega_api`, healthcheck `GET /salud`.
- Front actual: `front/src/lib/api.ts` usa rutas relativas `/api`; Nginx local quita `/api` antes de FastAPI. En Vercel: rewrite externo **`/api/:path*` → `https://HOST_API/:path*`** y luego fallback SPA a `/index.html`; con URL real del proveedor al configurar. No incluir claves en frontend.
- Definir configuración de SSL mediante entorno de la API, sin valores secretos por defecto en repositorio. Para pooler con transacciones, comprobar compatibilidad con prepared statements. En ninguna circunstancia conectarse como `postgres`.
- No desactivar triggers/FK ni recálculos en API/front. La prueba de RN-09 se hará con transacción reversible o base/sesión descartable para preservar el dataset.
- PostgreSQL gestionado puede incorporar roles internos no editables. Aplicar migraciones por rol autorizado, registrar incompatibilidades y adaptar sólo mediante procedimiento cloud documentado y aprobado, sin editar la historia original.
- Evitar importar directamente el dump de Fase 3 encima de un esquema con migraciones: elegir una sola estrategia limpia. Preferencia: migraciones desde SQL del repositorio y `PROFILE=cloud` reproducible; luego respaldo completo en formato custom y restore aislado.
- El backup/restauración debe preservar o reconstruir correctamente funciones `SECURITY DEFINER`, propietarios, dependencias y permisos mínimos; no alcanza comparar solo `COUNT(*)`.

## Puertas de calidad

1. **G0** Arquitectura compatible con plan $0, red restringida y migraciones/roles. Si falla, parar despliegue y activar plan B.
2. **G1** BD limpia creada, SQL de migraciones aplicado y roles correctamente asignados (consultas verificadas).
3. **G2** Cloud seed, conteos, FK, stock, totales y reglas sin inconsistencias. Al menos una tabla >10.000.
4. **G3** `/salud` público HTTPS OK como `bodega_api`, frontend público y cinco pantallas operativas por API real.
5. **G4** TLS y restricción de origen demostradas; RN-09 devuelve error esperado sin datos a medias.
6. **G5** Backup real restaurado en base nueva, conteos y lógica equivalentes; evidencia con comandos y salidas originales.
7. **G6** PRs revisados, documentación, URLs y capturas verificadas; recién entonces merge final.

**Prohibido inventar métricas, capturas, aceptación de restricciones, restores o URL funcional.**
