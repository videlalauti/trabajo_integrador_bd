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
| Backup, restore en base nueva, conteos | FULL CUSTOM restaurado en PostgreSQL 17.11 local **según informe del equipo** | **PENDIENTE DE ACREDITACIÓN PRIMARIA**: hash/log/27 conteos origen-destino |
| Regla de negocio cloud, con captura | Render DEMO: venta n.º3, rechazo RN-09 409/P0001 y transferencia n.º2 `procesado`; auditadas por SQL READ ONLY | **CUMPLIDO** |
| README reproducible + URLs | Actualizado en Draft PR #23, junto con `CIERRE_Y_EVIDENCIAS.md` | **PREPARADO**; pendiente revisión/fusión |
| Cualquier persona abre URL y usa sistema | Catálogo y reportes accesibles con H1; para escrituras se usa API demo con token y datos ficticios | **ALCANCE POR CONFIRMAR CON CÁTEDRA** |

## 2. Conteos de origen FULL obtenidos directamente

Se ejecutó el SQL **solo SELECT** `fase8/verificacion/sql/01_conteos_public.sql` sobre el proyecto productivo el 10/11/2026, **después** de la recuperación FULL reportada por el equipo. Resultado real: **27/27 tablas presentes**, volcado en [`evidencias/CONTEOS_FULL_ORIGEN_2026-11-10.csv`](evidencias/CONTEOS_FULL_ORIGEN_2026-11-10.csv).

Ejemplos: `cliente=20000`, `comprobante=150000`, `renglon_comprobante=500000`, `vino=750`, `ingreso=2000`, `transferencia=2000`, `stock_deposito=750`, `stock_sala=7255`.

**Límite fundamental:** este CSV es una **lectura actual del origen**; **NO ES** una medición del destino restaurado ni está demostrado que provenga del mismo snapshot exacto del `pg_dump`. La igualdad real origen–destino **NO** se declara hasta adjuntar el resultado de la base local.

## 3. Restore FULL — datos ya conocidos y falta exacta

| Dato | Valor / procedencia |
| --- | --- |
| Archivo FULL final reportado | `g1c_final_full_REINTENTO_20261109_225055.dump` |
| Tamaño reportado | 10.452.417 bytes (**requiere verificación sobre el archivo real**) |
| Formato/alcance reportados | CUSTOM / `public` |
| Destino local reportado | Contenedor `bodegas-g1c-restauracion-pg17`, BD `bodegas_g1c_final_full`, PostgreSQL 17.11 |
| Restore reportado | Correcto; opciones `--no-owner --no-acl --clean --if-exists --exit-on-error` solo destino local |
| SHA-256 **primario del dump final** | **FALTA** (no confundir con hash del dump `g1c_prelogistica_...`) |
| Código de salida + log `pg_restore` | **FALTA como evidencia primaria** |
| 27 conteos destino + comparador contra origen | **FALTA** |
| Propietarios/ACL del destino | **No equivalentes automáticamente** con `--no-owner --no-acl` |

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

Para comparar, obtener el CSV de origen de este PR y usar el comparador estricto ya versionado:
```powershell
python -B .\fase8\verificacion\scripts\comparar_conteos_estricto.py --origen .\fase8\evidencias\CONTEOS_FULL_ORIGEN_2026-11-10.csv --destino "$env:TEMP\fase8_conteos_destino.csv" --perfil local_completa
```
El CSV origen estará disponible después de incorporar este PR o al obtener el archivo directamente desde la rama documental. **Si el destino no existe o falla un comando, STOP:** no recrear, limpiar, ni restaurar otra vez para obtener evidencias sin evaluación.

## 4. Auditoría preliminar de secretos e IP

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
- [ ] SHA-256 real del **dump final**, inventario `pg_restore -l` y log con código de salida.
- [ ] Conteos 27/27 de la **base LOCAL ya restaurada** y salida comparador.
- [ ] Prueba negativa de red desde IP externa.
- [ ] Análisis completo del historial Git (no solamente PRs).
- [ ] Revisión y fusión **controlada** de PR #23; PR #22 de la demo permanece separado.
- [ ] Confirmar con la cátedra si H1 público + demostración autenticada en base ficticia satisface “usar el sistema”.

**Cierre prohibido sin evidencias:** no confundir una demostración funcional correcta con haber terminado todos los requisitos de seguridad/recuperación de la etapa 8.
