# Acta de control final — Fase 8 (10/11/2026)

**Estado:** control técnico y documental avanzado, **NO cerrado** por falta de algunas evidencias primarias. Fuente de aceptación: `TPI_Bodegas_del_Atuel.pdf`, etapa 8, páginas 18–19. Este documento se actualiza solo con hechos respaldados y no reemplaza el informe final de Fase 9.

## 1. Matriz contra la consigna

| Criterio de etapa 8 | Evaluación verificable | Estado |
| --- | --- | --- |
| Base PostgreSQL cloud | Supabase FULL `sjfyocokehaubuwwbhnw`; PostgreSQL 17.11 y datos reales | **CUMPLIDO** |
| Front/API HTTPS público | `https://bodegas-del-atuel.vercel.app` y `https://bodegas-atuel-api.onrender.com`; H1 solo lectura | **CUMPLIDO**, con alcance H1 a explicar |
| Migraciones SQL y tres roles | 001–008 implementadas; rol API no propietario; proyecto DEMO usa 007 adaptado al servicio gestionado | **CUMPLIDO TÉCNICO**; anexar prueba documental de ejecución del FULL |
| Datos cloud, 10.000+ filas | 27 conteos del FULL consultados el 10/11; comprobante 150.000, renglón 500.000 | **CUMPLIDO** |
| TLS y acceso restringido | API demo `/salud` devolvió `tls:true`; Network Restrictions DEMO incluye solo rangos Render `74.220.48.0/24` y `74.220.56.0/24` | **CONFIGURADO**; falta conexión fallida desde IP no autorizada |
| Secretos en proveedor y fuera de Git | Variables Render ocultas; token demo secreto, RLS y guard; inspección preliminar de PR 1–23 | **PARCIAL**: auditoría exhaustiva del historial Git pendiente |
| Rol mínimo de API | `bodega_api`, no propietario; TLS y rol efectivo revisados vía healthcheck y roles | **CUMPLIDO EN EJECUCIÓN** |
| Backup, restore en base nueva, conteos | FULL CUSTOM restaurado en PostgreSQL 17.11 local **según informe del equipo** | **CONTEOS 27/27 COINCIDENTES**: origen verificado con SQL directo, destino obtenido de salida PostgreSQL 17.11 local aportada por Valentino; hash y tamaño informados por cálculo local. Falta log/inventario primario del restore y comparación detallada de definiciones/ACL posrestore; **15/15 conteos estructurales ya coinciden**. |
| Regla de negocio cloud, con captura | Render DEMO: venta n.º3, rechazo RN-09 409/P0001 y transferencia n.º2 `procesado`; auditadas por SQL READ ONLY | **CUMPLIDO** |
| README reproducible + URLs | Actualizado en Draft PR #23, junto con `CIERRE_Y_EVIDENCIAS.md` | **PREPARADO**; pendiente revisión/fusión |
| Cualquier persona abre URL y usa sistema | Catálogo y reportes accesibles con H1; para escrituras se usa API demo con token y datos ficticios | **ALCANCE POR CONFIRMAR CON CÁTEDRA** |

## 1.1 Control independiente de privilegios en FULL

Consulta READ ONLY a `pg_roles` y `pg_class` del 10/11/2026:

- Existen roles separados `bodega_propietario` (**NOLOGIN**), `bodega_api_rw` (**NOLOGIN**), `bodega_reportes_ro` (**NOLOGIN**), `bodega_admin`, `bodega_api` y `bodega_reportes`.
- El login `bodega_api` tiene `rolsuper=false`, `rolcreatedb=false`, `rolcreaterole=false` y `rolbypassrls=false`; hereda `bodega_api_rw`, no `bodega_propietario`.
- Tablas auditadas `comprobante`, `stock_sala`, `stock_deposito` y `vino` son propiedad de `bodega_propietario`. `bodega_api` **no** tiene privilegio `TRUNCATE` en ninguna de ellas.
- El rol API sí conserva operaciones autorizadas del sistema (por ejemplo `INSERT` sobre `comprobante` y `vino`); la prohibición **H1 de escrituras públicas** depende además del guardián de FastAPI y no se debe equiparar con un rol SQL exclusivamente lector.

Esto evidencia separación entre **usuario de conexión**, **rol propietario** y **protección HTTP**. No se cambió ninguna ACL ni rol.

## 1.2 Integridad estructural y stock del FULL (solo lectura)

Consulta directa del 10/11/2026, sin modificar datos ni metadatos:

| Control FULL | Resultado |
| --- | ---: |
| Foreign keys en `public` | **32** |
| FK sin validar | **0** |
| Triggers de usuario | **11** |
| Triggers de usuario deshabilitados | **0** |
| Filas con stock de sala negativo | **0** |
| Filas con stock de depósito negativo | **0** |

Este inventario fue obtenido directamente del origen FULL. **El destino local también reportó 32 FK (0 sin validar), 11 triggers (0 deshabilitados) y stock sin negativos**, cotejados posteriormente en los 15 controles del siguiente apartado. La igualdad de inventarios numéricos no prueba que las definiciones individuales sean iguales.

## 1.3 Inventario estructural ampliado de origen FULL (15 controles)

Se ejecutó adicionalmente un SQL de solo lectura contra la base FULL de Supabase. Se conserva la consulta exacta en [`evidencias/SQL_CONTROL_ESTRUCTURAL_SOLO_LECTURA.sql`](evidencias/SQL_CONTROL_ESTRUCTURAL_SOLO_LECTURA.sql) y el resultado en [`evidencias/ESTRUCTURA_FULL_ORIGEN_2026-11-10.csv`](evidencias/ESTRUCTURA_FULL_ORIGEN_2026-11-10.csv). Controles verificados en origen: **27 tablas, 27 PK, 32 FK (0 sin validar), 25 CHECK, 6 UNIQUE, 38 índices, 14 secuencias, 3 vistas, 13 funciones, 4 procedimientos y 11 triggers de usuario (0 deshabilitados), 0 stock negativo**. **Valentino ejecutó el mismo SQL en el Docker local** y compartió la salida CSV: **15/15 controles idénticos**. Se conserva en [`evidencias/ESTRUCTURA_FULL_DESTINO_LOCAL_2026-11-10.csv`](evidencias/ESTRUCTURA_FULL_DESTINO_LOCAL_2026-11-10.csv). Los resultados numéricos se cotejaron línea por línea con la salida de Supabase. **No equivalen a una comparación exacta de definiciones de funciones, vistas, triggers y ACL**; diferencias de propietarios y permisos son esperables con `--no-owner --no-acl`.

## 2. Conteos de origen FULL obtenidos directamente

Se ejecutó el SQL **solo SELECT** `fase8/verificacion/sql/01_conteos_public.sql` sobre el proyecto productivo el 10/11/2026, **después** de la recuperación FULL reportada por el equipo. Resultado real: **27/27 tablas presentes**, volcado en [`evidencias/CONTEOS_FULL_ORIGEN_2026-11-10.csv`](evidencias/CONTEOS_FULL_ORIGEN_2026-11-10.csv).

Ejemplos: `cliente=20000`, `comprobante=150000`, `renglon_comprobante=500000`, `vino=750`, `ingreso=2000`, `transferencia=2000`, `stock_deposito=750`, `stock_sala=7255`.

**Comparación completada:** Valentino ejecutó el mismo SQL mediante `docker exec` sobre la base local `bodegas_g1c_final_full` (PostgreSQL 17.11) y aportó las 27 filas. La salida se conserva en [`evidencias/CONTEOS_FULL_DESTINO_LOCAL_2026-11-10.csv`](evidencias/CONTEOS_FULL_DESTINO_LOCAL_2026-11-10.csv) y su evaluación en [`evidencias/COMPARACION_27_TABLAS_FULL_2026-11-10.md`](evidencias/COMPARACION_27_TABLAS_FULL_2026-11-10.md). **Resultado: 27/27 conteos exactamente iguales.** El auditor obtuvo el CSV de destino de la salida proporcionada por coordinación, no de conexión directa a Docker. El corte de origen fue posterior al dump; **NO** se acredita todavía igualdad de snapshot o de contenido por fila.

## 3. Restore FULL — datos ya conocidos y falta exacta

| Dato | Valor / procedencia |
| --- | --- |
| Archivo FULL final reportado | `g1c_final_full_REINTENTO_20261109_225055.dump` |
| Tamaño del dump FULL final | **10.452.417 bytes** según salida de `Get-Item` proporcionada el 10/11/2026; coincide con el tamaño previamente reportado, sin acceso directo al archivo desde esta auditoría |
| Formato/alcance reportados | CUSTOM / `public` |
| Destino local reportado | Contenedor `bodegas-g1c-restauracion-pg17`, BD `bodegas_g1c_final_full`, PostgreSQL 17.11 |
| Restore reportado | Correcto; opciones `--no-owner --no-acl --clean --if-exists --exit-on-error` solo destino local |
| Inspección del inventario del dump | **VERIFICADA POR SALIDA LOCAL APORTADA (10/11/2026)**: `pg_restore (PostgreSQL) 18.6` pudo leer el archivo CUSTOM y mostró los últimos 15 objetos tipo `FK CONSTRAINT public ...`, entre ellos `fk_vino_bodega`, `fk_stock_sala_vino`, `fk_renglon_transferencia_vino`; la selección `-Last 15` no acredita el TOC completo. El cliente 18.6 es distinto del servidor 17.11 restaurado |
| SHA-256 **del dump final** | `B5E48E30A0AB0011E99DD2FA3664C0C315B15BC5F4C7196EA3106A6571BED055` — valor comunicado por Valentino tras ejecutar `Get-FileHash -Algorithm SHA256` sobre el dump final, **formato hexadecimal de 64 caracteres validado**. Pendiente de corroboración independiente contra el mismo archivo, si se requiere |
| Código de salida + log de la ejecución original de `pg_restore` | **FALTA como evidencia primaria**; la inspección posterior `pg_restore --list` tuvo salida exitosa, pero **no prueba el código de salida de la restauración histórica** |
| 27 conteos destino + comparador contra origen | **27/27 COINCIDEN**: CSV real del Docker local aportado por Valentino, transcrito y cotejado línea a línea contra CSV de Supabase; [acta comparativa](evidencias/COMPARACION_27_TABLAS_FULL_2026-11-10.md). Comparación temporal y contenido por fila no demostrados |
| Propietarios/ACL del destino | **No equivalentes automáticamente** con `--no-owner --no-acl` |

**Trazabilidad del SHA:** no se obtuvo del servidor Supabase ni del repositorio: es el hash SHA-256 calculado por el coordinador en su PC y transmitido en el chat el 10/11/2026. Coincide el nombre y el tamaño que mostró PowerShell; la existencia y contenido del archivo no fueron inspeccionados por esta auditoría. No reemplazar el hash por el correspondiente al dump previo a logística (`g1c_prelogistica_...`).

**Procedimiento solo lectura en el equipo que conserva dump y restore** (PowerShell, sin nuevos restores ni conexión cloud):

```powershell
# Completar la ruta privada del archivo FULL FINAL; no compartir la ruta si revela datos personales.
$dump = 'C:\RUTA_PRIVADA\g1c_final_full_REINTENTO_20261109_225055.dump'
if (-not (Test-Path -LiteralPath $dump)) { throw "No se encontro el dump FINAL" }
Get-Item -LiteralPath $dump | Select-Object Name,Length,LastWriteTimeUtc
Get-FileHash -LiteralPath $dump -Algorithm SHA256

# Comprobar la base LOCAL ya restaurada, sin DDL ni escrituras:
docker ps -a --filter "name=bodegas-g1c-restauracion-pg17"
docker exec bodegas-g1c-restauracion-pg17 psql -U postgres -d bodegas_g1c_final_full -X -v ON_ERROR_STOP=1 -c 'SELECT version();'

# Desde la RAIZ del repositorio; solo lee las 27 tablas del destino local.
Get-Content .\fase8\verificacion\sql\01_conteos_public.sql -Raw |
  docker exec -i bodegas-g1c-restauracion-pg17 psql -U postgres -d bodegas_g1c_final_full -X --csv -v ON_ERROR_STOP=1 |
  Set-Content -Path "$env:TEMP\fase8_conteos_destino.csv" -Encoding utf8
```

**Comparación realizada mediante los dos CSV versionados con resultado 27/27 idéntico.** La sección siguiente documenta una verificación local opcional si se requiere reproducir la comparación con el script estricto; no hace falta repetirla para obtener otra evidencia:

Para comparar, obtener el CSV de origen de este PR y usar el comparador estricto ya versionado:
```powershell
python -B .\fase8\verificacion\scripts\comparar_conteos_estricto.py --origen .\fase8\evidencias\CONTEOS_FULL_ORIGEN_2026-11-10.csv --destino "$env:TEMP\fase8_conteos_destino.csv" --perfil local_completa
```
El CSV origen estará disponible después de incorporar este PR o al obtener el archivo directamente desde la rama documental. **Si el destino no existe o falla un comando, STOP:** no recrear, limpiar, ni restaurar otra vez para obtener evidencias sin evaluación.


## 3.1 Búsqueda de log original en equipo de coordinación (10/11/2026)

Valentino ejecutó una enumeración **solo lectura** de archivos bajo `%LOCALAPPDATA%\BodegasFase8`, filtrando nombres por `restore|restaur|log|acta`. Los únicos resultados aportados fueron archivos `.dump` de **pre/postlogística**:

- `g1c_postlogistica_public_20261109_212311.dump` — **0 bytes**; no es una copia válida utilizable para recuperación.
- `g1c_postlogistica_public_20261109_212613.dump` — **423.506 bytes**; copia intermedia, **no** es el FULL definitivo.
- `g1c_prelogistica_public_20261109_194221.dump` — **318.347 bytes**; copia intermedia, **no** es el FULL definitivo.

Los nombres coinciden con el patrón porque `logistica` incluye la cadena `log`; **ninguno es un log de ejecución de `pg_restore`**. Por tanto **no se localizó un acta/log primario dentro de esa carpeta con ese filtro**. No implica que el log no exista en PowerShell, otra carpeta u otro equipo. La restauración ya quedó corroborada por 27/27 conteos, 15/15 métricas estructurales y `pg_restore --list` del dump final, sin reejecutar `pg_restore`. El resultado/código de salida original sigue **no acreditado documentalmente**.

## 4. Auditoría preliminar de secretos e IP

**Escaneo ampliado informado por Valentino (10/11/2026):** Gitleaks oficial en Docker `ghcr.io/gitleaks/gitleaks:latest`, sobre el repositorio local, con `git /repo --log-opts="--all" --redact=100` después de actualizar referencias. Salida de resumen: **131 commits escaneados, 3 posibles secretos, código de salida 1**. **Estado: ALERTAS SIN CLASIFICAR.** El código 1 refleja detecciones del escáner y no por sí solo fallo de Docker. No está demostrado si son credenciales reales, pruebas o falsos positivos. **No fusionar PRs ni declarar aprobado el historial de secretos hasta revisar regla, archivo, línea y commit sin revelar coincidencias.** La auditoría documental inicial sobre los 23 PR no sustituye esta nueva detección. No se registran ni se publican valores de posibles secretos en esta acta.

**GitHub — alcance limitado:** se revisaron con patrones de detección las líneas agregadas en los parches de **PR #1–#23**. Los avisos identificados se relacionan con **URLs deliberadamente inválidas de tests en `example.com`**, credenciales de **PostgreSQL efímero local del workflow de CI** y token simulado CI; no se detectó en esta pasada una credencial productiva verificable. Es una revisión heurística de los **parches de PR**, **no cubre** commits directos, blobs eliminados, todos los refs, ni todos los formatos de secreto. **NO declarar “historial completamente limpio”**.

Para auditar **todo** el historial en un clon completo y actualizado con Gitleaks v8.19+ (lectura, sin publicarlo), desde PowerShell en la raíz del repo:
```powershell
gitleaks version
gitleaks git --log-opts="--all" --redact .
```
Si la utilidad no está instalada, documentar la ausencia y usar otro análisis de historial equivalente antes de declarar completado. Tratar los hallazgos como sensibles, analizar los falsos positivos de los tests y **no subir el informe con secretos** al repo. El comando puede terminar con código 1 al detectar hallazgos; investigar antes de firmar.

**Red DENEGADA desde origen externo:** el Dashboard DEMO muestra exclusivamente los dos CIDR Render, pero falta un intento `psql` desde una conexión de Internet realmente ajena a esas redes. Debe utilizarse el host Session Pooler DEMO con usuario **solo de ensayo** y contraseña introducida de forma oculta (nunca en URL ni en comandos), ejecutar un simple `SELECT 1` y conservar solo el resultado redactado. No clasificar un error de contraseña como bloqueo de IP. Esta comprobación no se puede simular desde una conexión administrativa que elude las restricciones de la plataforma.

## 5. Aprobación final pendiente

- [x] 27 conteos actuales de FULL auditados y guardados como evidencia de origen.
- [x] Sistema productivo HTTPS H1; salud y base protegidos.
- [x] Venta, RN-09 y transferencia 3/3 DEMO cloud verificadas; no repetir POST.
- [x] Pruebas autenticación demo 401/401/403 y preflight autenticado.
- [x] Nombre, tamaño y SHA-256 del dump FINAL **informados mediante salida de PowerShell**, con formato SHA-256 válido; corroboración independiente opcional sobre el archivo original.
- [x] Apertura y lectura del dump definitivo con `pg_restore --list` en PowerShell (cliente 18.6), evidenciada por los últimos 15 ítems de FK; obtener inventario completo si hace falta.
- [ ] Log primario de la ejecución de restauración y código de salida auténtico (no derivable del `--list` posterior).
- [x] Conteos **27/27** de la **base LOCAL restaurada**, proporcionados como salida CSV de PowerShell y comparados exactamente contra Supabase FULL; evidencia y acta publicadas.
- [x] **15/15 controles estructurales** y stock negativo comparados entre origen y destino, con salida original y copia local documentadas.
- [ ] Comparación de **definiciones** de objetos y permisos/propietarios, si se exige equivalencia total; las ACL no se restauraron automáticamente.
- [ ] Prueba negativa de red desde IP externa.
- [ ] Análisis completo del historial Git (no solamente PRs).
- [ ] Revisión y fusión **controlada** de PR #23; PR #22 de la demo permanece separado.
- [ ] Confirmar con la cátedra si H1 público + demostración autenticada en base ficticia satisface “usar el sistema”.

**Cierre prohibido sin evidencias:** no confundir una demostración funcional correcta con haber terminado todos los requisitos de seguridad/recuperación de la etapa 8.
