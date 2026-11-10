# Evidencia — ensayo ficticio de backup y restore (Fabricio)

**Fecha del ensayo:** 09/11/2026 · **Lugar:** Windows + Docker Desktop local  
**Alcance:** una tabla con datos ficticios; **NO es** el backup FULL de Bodegas del Atuel.

## Ejecución constatada a partir de la sesión de trabajo

| Elemento | Dato |
|---|---|
| Imagen | postgres:17 |
| Motor observado | PostgreSQL 17.11 (Debian 17.11-1.pgdg13+2) |
| Contenedor | bodegas-fase8-ficticio-pg17 |
| Enlace local | 127.0.0.1:55432 → 5432 |
| Origen local | ejemplo_origen |
| Destino local | ejemplo_destino |
| Tabla y estructura | public.ejemplo(id INTEGER PRIMARY KEY, etiqueta TEXT NOT NULL) |
| Datos insertados | (1, ficticio A), (2, ficticio B) |
| Dump | /tmp/ejemplo_ficticio.dump |
| Formato | CUSTOM; compresión gzip indicada por pg_restore -l |
| Tamaño observado | Aproximadamente 1,7 KiB (salida de ls -lh) |
| Resultado origen | COUNT(*) = 2 |
| Resultado destino | COUNT(*) = 2 |
| Restricción restaurada | ejemplo_pkey, contype = p (PRIMARY KEY) |

**SHA-256 calculado dentro del contenedor:**

~~~text
f8e47cbe3e46f4389f7d1e88d6f1fb28f483a118071390f882f0faf306abaa7f
~~~

Se observó la creación de ambas bases con CREATE DATABASE, la creación de public.ejemplo e INSERT 0 2, la salida de pg_restore -l con tabla/datos/PRIMARY KEY, igualdad de conteos y la restricción de clave primaria en destino.

## Comandos utilizados (identificadores ficticios)

~~~powershell
docker exec bodegas-fase8-ficticio-pg17 pg_isready -U postgres
docker exec bodegas-fase8-ficticio-pg17 pg_dump -U postgres -d ejemplo_origen -Fc -f /tmp/ejemplo_ficticio.dump
docker exec bodegas-fase8-ficticio-pg17 pg_restore -l /tmp/ejemplo_ficticio.dump
docker exec bodegas-fase8-ficticio-pg17 pg_restore -U postgres -d ejemplo_destino --exit-on-error --no-owner --no-acl /tmp/ejemplo_ficticio.dump
docker exec bodegas-fase8-ficticio-pg17 psql -U postgres -d ejemplo_origen -At -c 'SELECT COUNT(*) FROM public.ejemplo;'
docker exec bodegas-fase8-ficticio-pg17 psql -U postgres -d ejemplo_destino -At -c 'SELECT COUNT(*) FROM public.ejemplo;'
docker exec bodegas-fase8-ficticio-pg17 psql -U postgres -d ejemplo_destino -c "SELECT conname, contype FROM pg_constraint WHERE conrelid = 'public.ejemplo'::regclass;"
docker exec bodegas-fase8-ficticio-pg17 sha256sum /tmp/ejemplo_ficticio.dump
~~~

**Evidencia privada local guardada por Fabricio:** archivo ensayo_backup_restore_ficticio.txt bajo %LOCALAPPDATA%\BodegasFase8 (no incluido en Git). Su existencia/tamaño se observaron por PowerShell (685 bytes); no contiene contraseñas.

## Interpretación y límites

**Aprobado el ensayo de mecanismo**: dump lógico CUSTOM → lectura del TOC → restore en otra base → dos registros conservados → PK conservada.

**No demostrado aquí:** restauración de las 27 tablas FULL, integridad histórica del negocio, 32 FK, ACL equivalentes, seguridad de roles, conexión a Supabase ni valor del SHA-256 del backup real. Las dos bases eran independientes **entre sí** pero estaban en **el mismo contenedor**. Para la recuperación FULL real se exige un contenedor/base de destino separado del origen.

La contraseña local se guardó fuera del repositorio. No adjuntar el archivo de entorno ni el dump a Git.
