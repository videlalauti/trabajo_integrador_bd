# Ensayo opcional y descartable — PostgreSQL 17, datos ficticios

**No se ejecutó en la sesión de preparación porque Docker/psql no están disponibles en este entorno.** Ejecutar únicamente si Docker Desktop está operativo y se dispone de un puerto 55432 libre. Este ensayo **no prueba** las 27 tablas ni RN-09.

Ejecutar en **PowerShell**, desde la carpeta raíz del repositorio. Usar una clave local aleatoria que no se muestre ni guarde en Git. Docker `--env-file` sigue siendo visible para quien tenga acceso a Docker; mantener el archivo fuera del repositorio con permisos limitados.

```powershell
# Crear C:\ruta_privada\pg17-local.env MANUALMENTE fuera de Git
# Contenido: POSTGRES_PASSWORD=<clave_larga_aleatoria_local>
# Verificar que la ruta sea privada y el puerto 55432 esté disponible.
docker run -d --name bodegas-fase8-ficticio-pg17 -p 127.0.0.1:55432:5432 --env-file C:\ruta_privada\pg17-local.env postgres:17
# Esperar hasta readiness (ejecutar de nuevo si está iniciando)
docker exec bodegas-fase8-ficticio-pg17 pg_isready -U postgres
# Para evitar contraseña en historial, usar psql dentro del contenedor para ejemplo SIN secretos de fuente
docker exec bodegas-fase8-ficticio-pg17 psql -U postgres -d postgres -v ON_ERROR_STOP=1 -c 'CREATE DATABASE ejemplo_origen;'
docker exec bodegas-fase8-ficticio-pg17 psql -U postgres -d postgres -v ON_ERROR_STOP=1 -c 'CREATE DATABASE ejemplo_destino;'
docker exec bodegas-fase8-ficticio-pg17 psql -U postgres -d ejemplo_origen -v ON_ERROR_STOP=1 -c 'CREATE TABLE public.ejemplo(id integer PRIMARY KEY, etiqueta text NOT NULL); INSERT INTO public.ejemplo VALUES (1, ''ficticio A''), (2, ''ficticio B'');'
# Dump creado dentro del contenedor, no en Git
docker exec bodegas-fase8-ficticio-pg17 pg_dump -U postgres -d ejemplo_origen -Fc -f /tmp/ejemplo_ficticio.dump
docker exec bodegas-fase8-ficticio-pg17 pg_restore -U postgres -d ejemplo_destino --exit-on-error --no-owner --no-acl /tmp/ejemplo_ficticio.dump
docker exec bodegas-fase8-ficticio-pg17 psql -U postgres -d ejemplo_origen -At -c 'SELECT COUNT(*) FROM public.ejemplo;'
docker exec bodegas-fase8-ficticio-pg17 psql -U postgres -d ejemplo_destino -At -c 'SELECT COUNT(*) FROM public.ejemplo;'
# Ambos conteos deben ser 2. Guardar logs con etiqueta ENSAYO_FICTICIO.
```

Después de verificar y **con autorización del responsable local**, destruir exclusivamente este contenedor descartable: `docker rm -f bodegas-fase8-ficticio-pg17`. Este comando elimina el contenedor y su contenido; nunca se aplica a la base FULL ni a Supabase.

**Nota:** el ejemplo reutiliza un solo contenedor con dos bases independientes, solo para ensayar mecanismo. Para FULL se exige contenedor PostgreSQL 17 nuevo distinto del origen.
