# Guía reproducible — restaurar un backup FULL de Bodegas del Atuel en PostgreSQL 17 local

**Clasificación:** procedimiento para demostración, **no un registro de ejecución**. La restauración final FULL fue reportada como exitosa por coordinación, pero esta guía **no constituye otra restauración**. No volver a ejecutar el backup ni realizar conexiones a Supabase sin autorización expresa.

## 0. Condiciones y autorización

- El backup CUSTOM real ya fue generado por el equipo: solicitar a José la **copia autorizada** en un medio privado, su SHA-256 oficial, bytes, versión de pg_dump y alcance (`public` o base completa); nunca pedir ni publicar credenciales.
- Mantener el archivo de respaldo **fuera del repositorio** y de sincronizaciones públicas. Confirmar autorización de tratamiento de datos personales; no publicar el contenido de los CSV.
- Destino: **nuevo contenedor PostgreSQL 17, base vacía** sin objetos del TP. No usar el contenedor `bodegas-fase8-ficticio-pg17` ya creado para el ensayo ni el origen Supabase como destino.
- Revisar extensiones, roles, propietarios y privilegios con José. Un dump CUSTOM de `public` puede depender de extensiones fuera del esquema o de objetos/roles externos.
- Todo comando a continuación corre en **PowerShell de Windows**, excepto cuando se ve `psql` ejecutado dentro del contenedor. Los nombres son ejemplos **no secretos**.

## 1. Herramientas y preflight seguro

```powershell
docker --version
docker info --format '{{.ServerVersion}}'
docker image inspect postgres:17 --format '{{.RepoTags}}'
docker ps -a --format '{{.Names}} | {{.Status}}'
Get-NetTCPConnection -LocalPort 55433 -State Listen -ErrorAction SilentlyContinue
```

El puerto 55433 y nombre `bodegas-fase8-restore-full-pg17` deben estar libres. **Detenerse si ya existen**; no borrar ni sobrescribir ningún contenedor. Docker 17 local sirve como destino gratuito y fuera de Supabase.

## 2. Preparar el destino independiente (solo después de autorización)

Crear un archivo privado `pg17-restore.env` **fuera de Git**, con contraseña fuerte generada y resguardada para la restauración, sin imprimirla en consola. No compartir ese archivo ni registrar su contenido en la evidencia. El nombre y ruta local se personalizan.

```powershell
$envFile = Join-Path $env:LOCALAPPDATA "BodegasFase8\pg17-restore.env"
# Preparar manualmente el archivo con una línea POSTGRES_PASSWORD=... fuera del repo.
# No ejecutar el siguiente comando hasta que José apruebe el destino y el envFile exista.
docker run -d --name bodegas-fase8-restore-full-pg17 -p 127.0.0.1:55433:5432 --env-file $envFile postgres:17
docker exec bodegas-fase8-restore-full-pg17 pg_isready -U postgres
docker exec bodegas-fase8-restore-full-pg17 psql -U postgres -d postgres -v ON_ERROR_STOP=1 -c 'CREATE DATABASE bodegas_recuperacion;'
```

**NOTA:** la contraseña local puede ser visible para el administrador de Docker; restringir acceso al host y respaldos. Alternativa: crear el destino bajo gestión de José. Nunca ejecutar estos pasos en producción.

## 3. Verificación previa del archivo recibido, sin conectarse a la nube

```powershell
$dump = 'C:\ruta_privada\bodegas_full_autorizado.dump' # Sustituir por ruta real fuera de Git
Get-Item -LiteralPath $dump | Select-Object Name,Length,LastWriteTimeUtc
Get-FileHash -LiteralPath $dump -Algorithm SHA256
# Si pg_restore está instalado localmente:
pg_restore --version
pg_restore --list "$dump"
```

Comparar el hash con el comunicado por el responsable. Si difiere, **detenerse** y preservar evidencia. Confirmar compatibilidad entre versión del dump, extensión/roles y PostgreSQL 17.11. No seguir con un dump parcial.

## 4. Restauración SOLO en la base local vacía (con aprobación)

Los comandos siguientes son una **plantilla**; PostgreSQL cliente 17 debe estar disponible en PowerShell para usar `pg_restore`. La conexión es solo `127.0.0.1:55433` y **no el host de Supabase**. Usar autenticación local interactiva y nunca poner password en argumentos ni capturas.

```powershell
pg_restore --host 127.0.0.1 --port 55433 --username postgres --dbname bodegas_recuperacion --password --exit-on-error --verbose --no-owner --no-acl "$dump"
```

**Precaución importante:** `--no-owner --no-acl` omite restaurar dueños y permisos; es útil en entorno técnico aislado, pero **no prueba equivalencia de seguridad**. José debe aprobar el mapeo de roles y comparaciones posteriores (incluido `SECURITY DEFINER`, `search_path` y EXECUTE). No usar `--clean`, `--disable-triggers` ni ningún `DROP` sobre el origen.

Si el equipo no dispone de `pg_restore` en Windows, también puede copiar el dump al contenedor con `docker cp` (solo a un contenedor de destino aprobado) y ejecutar `docker exec ... pg_restore -U postgres -d bodegas_recuperacion ...`; el archivo no debe quedar en Git. Registrar exactamente el método elegido.

## 5. Integridad y conteos de las 27 tablas

La fuente de verdad es el conjunto de conteos del **origen en la misma ventana/snapshot lógico estable que el dump**, facilitado por José. No generar un «origen» posterior y afirmar equivalencia sin registrar posibles escrituras entre ambos instantes.

Desde PowerShell con `psql` cliente 17, contra el **destino local**, ejecutar:

```powershell
psql -X --csv -v ON_ERROR_STOP=1 -h 127.0.0.1 -p 55433 -U postgres -d bodegas_recuperacion -W -f fase8/verificacion/sql/01_conteos_public.sql -o "$env:LOCALAPPDATA\BodegasFase8\conteos_destino_privado.csv"
python fase8/verificacion/scripts/comparar_conteos_estricto.py --origen "C:\ruta_privada\conteos_origen_privado.csv" --destino "$env:LOCALAPPDATA\BodegasFase8\conteos_destino_privado.csv" --perfil local_completa
```

El comparador exige las 27 tablas; **27/27 coincidencias exactas** son necesarias. Verificar primero el **formato CSV** compatible con el comparador. Si la fuente es un FULL local, el perfil `local_completa` refleja los mínimos completos; si coordinación usó explícitamente carga reducida cloud, justificar perfil distinto. No importar los conteos finales de esta documentación como sustitutos de CSV reales.

## 6. Estructura, lógica y permisos

Con acceso de solo lectura a la base **destino** y, cuando lo autorice José, consultar:

- Conteos, huérfanos de 32 FK, stock negativo y totales: `control_integridad.sql` entregado por coordinación, o su versión vigente auditada.
- Objetos: `fase8/verificacion/sql/03_objetos_restauracion_solo_lectura.sql` y `04_inventario_estructura.sql`.
- Solo lectura adicional: `fase8/recuperacion/sql/verificar_recuperacion_solo_lectura.sql`.
- Integridad estructural: 27 tablas, FK validadas, triggers habilitados, CHECK, UNIQUE, PK, índices y secuencias; cotejar inventario del origen.
- Roles: propietarios, privilegios, SECURITY DEFINER y extensiones; el entorno local no hereda los roles de clúster de Supabase.

**No repetir** ventas, RN-13 ni movimientos; la documentación de esos casos usa las evidencias ya capturadas por coordinación.

## 7. Acta y defensa

Registrar archivo, fecha UTC, tamaño, SHA-256, versión herramienta, origen anonimizado, destino local claramente distinto, código de salida real de `pg_restore`, 27 conteos, validación estructural, ACL y observaciones. Capturar las pantallas y logs **sin datos personales**. Si el restore falla, conservar error exacto redactado y declarar `NO APROBADO` hasta resolverlo.

La defensa puede mostrar el **backup real previamente restaurado**, los logs, el manifiesto y la comparación completa sin repetir procesos largos o destructivos en vivo. Diferenciar claramente el ensayo ficticio de 2 filas (02) de la restauración FULL comunicada por coordinación (01/06).
