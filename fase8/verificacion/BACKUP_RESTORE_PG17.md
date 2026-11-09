# Backup y restauración PostgreSQL 17 — procedimiento PREPARADO, NO EJECUTADO CLOUD

**Objetivo:** respaldo lógico de `public` en Supabase cuando José confirme FULL; restauración en **PostgreSQL 17 Docker local descartable e independiente**, no en Supabase ni en la base origen. El Docker local **solo vale como destino** si se comprueba compatibilidad de extensiones/funciones y roles; documentar diferencias en vez de ocultar errores.

## 0. Puertas de autorización

Requerir autorización explícita, ventana estable sin escrituras (o snapshot lógico consistente para dump + conteos), acceso de backup según allowlist, PG versión, espacio en disco y aprobación de José sobre roles/propietarios/`SECURITY DEFINER`. No ejecutar los comandos de nube hasta recibirla.

## 1. Herramientas y ubicación

En PowerShell, usar PostgreSQL **17** `pg_dump`, `pg_restore`, `psql` y Docker Desktop; verificar `pg_dump --version`, `pg_restore --version`, `docker version`. PostgreSQL 17 client es apropiado para servidor PostgreSQL 17. Backup guardado **fuera del repositorio**, carpeta restringida; no agregar datos ni credenciales a Git.

```powershell
$fecha = Get-Date -Format 'yyyyMMdd_HHmmss'
$evid = Join-Path $HOME "fase8_resguardos\$fecha"
New-Item -ItemType Directory -Force -Path $evid
$dump = Join-Path $evid "bodegas_full_public_$fecha.dump"
# Fuente: parametrizar host/usuario/base proporcionados por José, sin contraseña en argumentos.
# Usar PGSSLMODE=verify-full y CA certificada si la infraestructura lo permite;
# no confundir "require" con validación del certificado/hostname.
# $env:PGSSLMODE = 'verify-full'  # solo tras configurar trust de CA
# pg_dump -h HOST_ORIGEN -p PUERTO -U USUARIO_BACKUP -d postgres -W -Fc -n public -f $dump
# Si el comando falla, detener procedimiento. NO continuar con un archivo parcial.
```

El comentario `-n public` exporta objetos y datos del esquema `public`, **no** exporta roles globales ni necesariamente dependencias de extensiones fuera de ese esquema. `-W` pide contraseña interactivamente; no colocar en shell history, scripts ni capturas. Si se usa pooler, confirmar compatibilidad para `pg_dump`; priorizar conexión de sesión/directa que funcione desde la red autorizada.

## 2. Registrar metadatos cuando exista dump real

```powershell
# Solo tras dump exitoso y cerrado:
# pg_restore --list $dump | Out-File (Join-Path $evid 'inventario_dump.txt')
# Get-Item $dump | Select-Object Name,Length,LastWriteTimeUtc
# Get-FileHash -Algorithm SHA256 $dump
# El SHA-256, tamaño, versión herramienta, fecha UTC y origen REDACTADO van al acta.
```

No publicar el dump, ni datos de clientes o cadenas de conexión.

## 3. Destino PostgreSQL 17 en Docker LOCAL — operación futura autorizada

Contenedor descartable con password local fuerte facilitada **interactivamente/gestor de secretos**; el siguiente ejemplo usa una variable de sesión solo para el entorno Docker (no registrar su valor ni persistirlo). Evitar `-p` y `docker inspect` públicos si la máquina es compartida; usar loopback y limpiar al terminar.

```powershell
# PARÁMETROS DE EJEMPLO; NO EJECUTAR CONTRA NUBE SIN AUTORIZACIÓN
# $secret = Read-Host 'Password SOLO para Postgres Docker local' -AsSecureString
# Docker requiere valor texto; usar mecanismo de secretos local aprobado o --env-file
# fuera del repositorio con ACL restringida. NO hacer captura de esa configuración.
# docker run -d --name bodegas-fase8-restore-pg17 -p 127.0.0.1:55432:5432 #   --env-file C:\ruta_privada\pg17-local.env postgres:17
# docker exec bodegas-fase8-restore-pg17 pg_isready -U postgres
# pg_restore -h 127.0.0.1 -p 55432 -U postgres -d postgres -W #   --no-owner --no-acl --exit-on-error -v $dump
```

PowerShell: los ejemplos de varias líneas que usan `\` son **esquemáticos**, no copiar literalmente (PowerShell usa backtick o línea única). Consultar `ENSAYO_LOCAL_FICTICIO_DOCKER.md` para comandos locales de una sola línea y `README.md` para las puertas de autorización. La instalación local 17 no tiene roles de Supabase y quizás carezca de extensiones: `--no-owner --no-acl` permite restaurar objetos/datos, pero **NO recrea seguridad equivalente**. Crear un contenedor/base nueva sin objetos TP previos. **Nunca usar** `--clean`, `--if-exists`, `DROP`, `--disable-triggers` en origen. Validar el inventario del dump antes de restaurar; si falla cualquier paso, conservar logs, detener y no declarar éxito.

## 4. Validación de 27 tablas

```powershell
# En una ventana de origen estable, con psql --csv -X -v ON_ERROR_STOP=1:
# psql -h HOST_ORIGEN -p PUERTO -U USUARIO -d postgres -W --csv -X -v ON_ERROR_STOP=1 #   -f fase8/verificacion/sql/01_conteos_public.sql -o "$evid\conteos_origen.csv"
# psql -h 127.0.0.1 -p 55432 -U postgres -d postgres -W --csv -X -v ON_ERROR_STOP=1 #   -f fase8/verificacion/sql/01_conteos_public.sql -o "$evid\conteos_destino.csv"
# python fase8/verificacion/scripts/comparar_conteos_estricto.py #   --origen "$evid\conteos_origen.csv" --destino "$evid\conteos_destino.csv" #   --perfil nube_reducida
```

**Importante:** los conteos origen deben corresponder a un snapshot/ventana estable compatible con el instante del dump. Si hay escrituras entre exportaciones, una diferencia puede reflejar concurrencia, no fallo de restore. En cada salida, verificar EXACTAMENTE 27 tablas, no vacías y equivalentes; `--perfil nube_reducida` verifica el mínimo permitido en cloud. Para FULL local original el volumen puede evaluarse separadamente con `--perfil local_completa` si corresponde.

## 5. Restricciones, relaciones y roles

Ejecutar `sql/03_objetos_restauracion_solo_lectura.sql` y `sql/04_inventario_estructura.sql` tanto en origen como en destino; verificar FK, CHECK, UNIQUE, PK, triggers habilitados, índices, secuencias, definiciones de funciones, dependencias, propietario, EXECUTE y `search_path` de SECURITY DEFINER. Usar el `control_integridad.sql` aprobado por José. Si se restableció con `--no-owner --no-acl`, los permisos/propietarios de origen **no son iguales**: documentar y hacer que José apruebe un plan de equivalencia para roles técnicos en local, nunca declarar "seguridad restaurada" solo por haber contado filas.

## 6. Acta y cierre

`fecha UTC | PG server/client | commit | origen anonimizado | destino Docker distinto | nombre backup | bytes | SHA256 | pg_restore exit code | 27/27 conteos | integridad | triggers/ACL | incidencias`. Guardar logs redactados, no el dump, en repositorio solo si coordinación lo autoriza. Destruir contenedor **únicamente tras** aprobación de la evidencia y constancia de hashes; `docker rm -f ...` afecta SOLO al contenedor local nombrado, nunca a Supabase.

## Ensayo local opcional ANTES de FULL

Para probar mecánica sin estructura TP ni datos reales, levantar contenedor PostgreSQL 17 local, crear base ficticia `ejemplo_restore`, una tabla `public.ejemplo`, insertar dos filas ficticias, ejecutar `pg_dump -Fc`, restaurar a **otra base local nueva** y cotejar 2 filas. Registrar como `ENSAYO_LOCAL_FICTICIO`; no presentarlo como restauración de Bodegas ni como 27/27.
