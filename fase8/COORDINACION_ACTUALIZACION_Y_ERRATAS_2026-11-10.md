# Fase 8 — Actualización de coordinación y fe de erratas (10/11/2026)

**Objeto:** actualizar el estado a posteriori de los informes históricos de Fabricio (PR #15 y #16), sin reescribir sus evidencias ni alterar el inventario SHA-256 original. **Este documento no es un log de ejecución, acta firmada ni autorización para nuevas escrituras.**

## 1. Cómo leer la documentación

Los documentos `fase8/verificacion/` y `fase8/recuperacion/` se prepararon entre el 9 y el 10 de noviembre, en un momento en que Render no estaba activo y aún no se habían incorporado a sus actas todos los datos de la recuperación FULL. Sus estados «PENDIENTE CLOUD» y «SIN DESPLIEGUE» deben interpretarse como **fotografías históricas de preparación**, no como el estado posterior al despliegue.

Las dos fuentes de prueba son **distintas**:

- **Ensayo ficticio de Fabricio:** Docker PostgreSQL 17.11, tabla `public.ejemplo`, dos filas y clave primaria preservada en otra base local. Es una prueba del mecanismo de backup/restore, no del dataset de Bodegas.
- **Restauración FULL real:** coordinación informó que un dump CUSTOM de `public` de Supabase fue restaurado en PostgreSQL 17.11 local independiente. **No fue realizada por Fabricio en su PR** y los logs completos, hash oficial y comparación exacta de las 27 tablas origen/destino aún no están adjuntos al expediente documental.

## 2. Metadatos FULL conocidos y límites de la evidencia

| Elemento | Dato reportado por coordinación |
|---|---|
| Archivo final | `g1c_final_full_REINTENTO_20261109_225055.dump` |
| Tamaño exacto reportado | 10.452.417 bytes |
| Formato | `pg_dump` CUSTOM, exportación del esquema `public` |
| Destino de restauración local | Contenedor `bodegas-g1c-restauracion-pg17`, base `bodegas_g1c_final_full` |
| PostgreSQL destino | 17.11 |
| Opciones de restauración informadas | `--no-owner --no-acl --clean --if-exists --exit-on-error`, **solo sobre destino local**, nunca sobre Supabase |
| Resultado comunicado | Restauración terminada satisfactoriamente |
| SHA-256 del dump final | **PENDIENTE: no se transcribe sin registro primario verificable** |
| Informe 27/27 de filas origen y destino | **PENDIENTE DE ADJUNTAR Y CONTRASTAR** |
| Roles/propietarios/ACL del destino | **NO equivalentes por defecto**: las opciones `--no-owner --no-acl` no reconstruyen la seguridad del origen |

El sello `20261109_225055` pertenece al **nombre del archivo**; no se afirma que esa sea una fecha UTC de ejecución sin evidencia adicional. Las opciones `--clean --if-exists` fueron informadas para la restauración local ya realizada; no son una instrucción de repetir el restore.

Estos valores no sustituyen la necesidad de conservar el log primario de `pg_restore`, el inventario TOC, el SHA-256 correcto del fichero y el resultado de los controles de FK/triggers de origen y destino.

## 3. Estado real de Render y Supabase a 10/11/2026

- Integración del backend en `integracion/fase8`: PR #12 (TLS/configuración nube), #13 (Docker Secret File), #17 (bloqueo H1) y #18 (regresión offline), fusionados.
- Commit desplegado en Render: `9f0e124c8732589abdc9b859da726f02b457c4bf`.
- URL backend: `https://bodegas-atuel-api.onrender.com`.
- Evidencia de Antonio revisada por coordinación: `GET /salud` HTTP 200 con `{"estado":"ok","base_datos":"conectada","tls":true}`, `GET /vinos` HTTP 200 con `total=750`, `GET /docs` HTTP 403 y POST a ruta de verificación inexistente HTTP 403. No se informaron operaciones de escritura.
- Network Restrictions de Supabase: coordinación confirma alta de los rangos de salida compartidos de Render `74.220.48.0/24` y `74.220.56.0/24`; IP temporales de Antonio y José retiradas.
- Verificación independiente por consultas `SELECT` de coordinación **antes y después** del despliegue:

| Control | Antes | Después |
|---|---:|---:|
| `vino` | 750 | 750 |
| `cliente` | 20.000 | 20.000 |
| `comprobante` | 150.000 | 150.000 |
| `renglon_comprobante` | 500.000 | 500.000 |
| `ingreso` | 2.000 | 2.000 |
| `transferencia` | 2.000 | 2.000 |
| `stock_deposito` registros | 750 | 750 |
| `stock_sala` registros | 7.255 | 7.255 |
| Total de botellas `stock_deposito` | 22.384.854 | 22.384.854 |
| Total de botellas `stock_sala` | 88.538.020 | 88.538.020 |
| Registros con stock negativo | 0 | 0 |
| `auditoria_precio` | 1 | 1 |

**Alcance limitado:** estos resultados demuestran invariancia en los 12 controles observados; no constituyen una comparación restauración origen/destino ni prueban integridad histórica completa de las 32 FK.

## 4. Auditoría del kit de Fabricio — PR #15 y #19

- PR #15: kit documental y scripts incorporados sin ejecutar conexiones a producción.
- PR #19: workflow de auditoría offline integrado. [GitHub Actions run 42823819020](https://github.com/videlalauti/trabajo_integrador_bd/actions/runs/42823819020).
- Python 3.13: **18/18** pruebas del kit y **9/9** pruebas del comparador estricto, más **31/31** SHA-256 y tamaños del manifiesto.
- Python 3.14: idénticos resultados.
- **Fe de erratas:** el archivo `INVENTARIO_SHA256.txt` contiene **31 entradas**, no 30 como decía la descripción inicial del PR.
- **Referencias de archivos antiguas:** `fase8/verificacion/EVIDENCIAS_Y_ESTADOS.md` menciona `pruebas_locales/07_rechazo_csv_incompletos_fabricio.txt`, `08_tests_originales_fabricio.txt` y `09_tests_estrictos_fabricio.txt`, archivos que no forman parte del PR. El material reproducido que sí está versionado se llama `10_test_kit_reproducido_entorno_preparacion.txt`, `11_test_estricto_reproducido_entorno_preparacion.txt` y `12_rechazo_24_tablas_reproducido.txt`. No atribuir los archivos reproducidos a una ejecución directa de Fabricio.
- Las notas del kit que denominan «H1» al problema de un comparador incompleto son **independientes** del bloqueo de seguridad H1 de FastAPI.

## 5. Pendientes para la defensa

1. Reunir sin secretos el SHA-256 **primario** y metadatos finales del dump, el log de `pg_restore`, TOC, comparación 27/27, integridad de 32 FK, triggers, y diferencias de ACL/roles; **no volver a restaurar por duplicado ni asignar nuevas cargas de datos** para producir evidencia documental.
2. Aportar evidencia anonimizada original de RN-13 y del balance de conservación histórica, separando los controles posteriores a Render de la prueba de recuperación.
3. Integrar y desplegar el frontend Vercel desde el PR #14 tras aprobación, en **modo solo lectura**.
4. Para una demostración de venta, RN-09 y transferencia funcional en Internet, diseñar y probar **autenticación/autorización** sobre una base descartable; el H1 actual bloquea métodos mutantes y lecturas sensibles.

**Control de seguridad:** no subir `.dump`, CSV con PII, cadenas de conexión, contraseñas, variables `DB_PASSWORD` ni capturas sensibles a GitHub.
