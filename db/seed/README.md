# Etapa 3 — Carga masiva de datos | Bodegas del Atuel

Este directorio contiene la carga reproducible de datos para PostgreSQL, de acuerdo con la **Etapa 3** del enunciado oficial (páginas 13–14). El README describe cómo preparar, ejecutar y verificar la carga. Los **conteos y tiempos reales** obtenidos durante las pruebas se resumen al final y se desarrollan en el informe de la Etapa 3.

## 1. Requisitos

- PostgreSQL 14 o superior (las pruebas finales del equipo se realizaron con PostgreSQL 18.1 en Windows).
- Una **base de pruebas vacía**, con las migraciones `db/migrations/001_...sql` a `007_...sql` aplicadas en ese orden.
- Python 3 y las librerías `psycopg` y `Faker`.
- Los cinco CSV de referencia en `db/seed/catalogs/` y los cuatro módulos integrados de `db/seed/modules/`.

Desde PowerShell, en la raíz del repositorio:

```powershell
python -m pip install "psycopg[binary]" faker
```

No usar datos de producción para las pruebas de carga ni guardar contraseñas en Git.

## 2. Archivos y orden de ejecución

- `config.py`: semilla, perfiles, fechas, cantidades y parámetros de conexión.
- `run_seed.py`: ejecutor común de los módulos.
- `modules/catalogos.py`: catálogos reales y maestros.
- `modules/produccion.py`: producción, vinos y composición.
- `modules/logistica.py`: ingresos, transferencias y stock.
- `modules/ventas.py`: clientes, permisos, comprobantes y renglones.
- `catalogs/`: CSV de catálogos preparados a partir de fuentes reales y datos de referencia; su procedencia se documenta a continuación.
- `control_integridad.sql`: consultas de control pedidas en el paso 7 de la Etapa 3.
- `prueba_rendimiento.py`: prueba independiente de inserciones individuales frente a `COPY`; utiliza una tabla temporal y no forma parte de la carga principal.

El ejecutor carga en orden **catálogos → producción → logística → ventas → RN-13 (actualización de precio para activar la auditoría)**. Cada módulo debe exponer `seed(conn, rng, faker, config, refs)` y compartir identificadores reales en `refs`; no debe ejecutar `commit()` ni `rollback()` por su cuenta.

### Fuentes y criterios de los catálogos (Rol A)

El paso 1 de la Etapa 3 exige cargar **cepas, maridajes, departamentos y localidades de Mendoza y tipos de vino desde CSV**, en lugar de generarlos al azar. Los archivos de `catalogs/` son selecciones o adaptaciones para el TP; **no son exportaciones íntegras de las fuentes oficiales**.

| Archivo CSV | Procedencia y criterio |
| --- | --- |
| `cepas.csv` | Selección de variedades tintas y blancas basada en la [Resolución INV 3/2026](https://www.argentina.gob.ar/normativa/nacional/norma-430315/texto), que enumera variedades reconocidas para la elaboración de vinos. Los tipos se ajustan al esquema del proyecto. |
| `maridajes.csv` | Catálogo **curado por el equipo** para las pruebas, con temperaturas de servicio orientativas. Se toma como referencia temática el **Anexo B.2 del enunciado**, sin presentarlo como un dataset oficial ni como una transcripción literal. |
| `localidades_mendoza.csv` | Selección de localidades mendocinas a partir de [Datos Abiertos Mendoza — Localidades de la Provincia](https://datosabiertos.mendoza.gov.ar/dataset/localidades-de-la-provincia-de-mendoza). Para los códigos postales se complementó con el documento del [Instituto Provincial de la Vivienda — Direcciones de Vivienda](https://www.ipvmendoza.gov.ar/wp-content/uploads/2021/11/direcciones-de-vivienda_PDF.pdf). |
| `departamentos_mendoza.csv` | Los 18 departamentos de Mendoza, de acuerdo con el **Anexo B.3 del enunciado** y la información del [Gobierno de Mendoza / Dirección General de Escuelas](https://www.mendoza.edu.ar/mapas-departamentos-mendoza/). |
| `tipos_vino.csv` | Valores `tinto`, `blanco`, `rosado` y `espumante` definidos por el tipo ENUM `tipo_vino` en [`db/migrations/001_esquema.sql`](../migrations/001_esquema.sql), coincidentes con el **Anexo B.4 del enunciado**. |

**Aclaración sobre códigos postales:** en el CSV, **Junín (5521)** y **La Paz (5591)** utilizan códigos que figuran en direcciones institucionales registradas por el Instituto Provincial de la Vivienda. Estos valores documentan ese criterio de referencia, **no implican que exista un único código postal válido para todo el departamento o localidad**. Los nombres de localidad, sede municipal y departamento pueden referirse a ámbitos geográficos distintos.

Las bodegas, salas y personas que genera `catalogos.py` son datos ficticios para pruebas, conforme al criterio del **Anexo B.4** para entidades simuladas; no representan establecimientos o personas reales. Los CSV, en cambio, se leen como datos de referencia y no se generan al azar.

## 3. Verificar la configuración sin modificar la base

```powershell
python .\db\seed\run_seed.py --check
```

El modo `--check` no abre conexiones, no crea tablas y no inserta registros. Es posible ejecutarlo incluso antes de integrar los cuatro módulos.

La configuración actual utiliza la semilla `20261027`, dos perfiles (`small` y `full`) y el período histórico del 01/01/2022 al 30/09/2026.

## 4. Ejecutar la carga

La carga integrada se validó en los perfiles `small` y `full` sobre PostgreSQL 18.1. Ejecutarla solo sobre una base **nueva y descartable** con las migraciones ya aplicadas. `run_seed.py` no crea ni limpia la base y confirma las transacciones por módulo: si uno falla, los anteriores pueden haber quedado cargados.

En PowerShell, definir los parámetros adecuados para la base de pruebas:

```powershell
$env:PROFILE = "small"
$env:SEED = "20261027"
$env:PGHOST = "127.0.0.1"
$env:PGPORT = "5432"
$env:PGDATABASE = "NOMBRE_BASE_DESCARTABLE"
$env:PGUSER = "USUARIO_POSTGRES"
# Configurar PGPASSWORD de forma segura cuando sea necesario.
python .\db\seed\run_seed.py --check
python .\db\seed\run_seed.py --run
```

Reemplazar `NOMBRE_BASE_DESCARTABLE` y `USUARIO_POSTGRES` por los valores reales. Si PostgreSQL corre dentro de Docker, el puerto indicado por `PGPORT` tiene que estar **publicado hacia localhost**; un contenedor sin puerto publicado no es accesible mediante `PGHOST=localhost`. No reutilizar las bases de Fase 2.

Luego de verificar el perfil pequeño, repetir sobre **otra base limpia** con `$env:PROFILE = "full"`. No recargar `full` encima de `small`.

## 5. Verificaciones obligatorias

El archivo `control_integridad.sql` comprueba:

1. Conteo de filas por tabla y mínimos globales de volumen.
2. Registros huérfanos para las claves foráneas.
3. Stock negativo en depósito y salas.
4. Importes inconsistentes entre comprobantes y sus renglones.

Por ejemplo, con PostgreSQL dentro de Docker y la base ya cargada:

```powershell
Get-Content .\db\seed\control_integridad.sql -Raw -Encoding UTF8 |
  docker exec -i NOMBRE_CONTENEDOR psql -X -U postgres -d NOMBRE_BASE_DESCARTABLE -v ON_ERROR_STOP=1
```

En una instalación local de Windows, se puede utilizar:

```powershell
psql -X -h 127.0.0.1 -p 5432 -U postgres -d NOMBRE_BASE_DESCARTABLE -v ON_ERROR_STOP=1 -f ".\db\seed\control_integridad.sql"
```

Sustituir los nombres del contenedor y de la base. Todas las tablas deben tener al menos una fila; al menos tres tablas deben superar las 10.000 filas y al menos una superar las 100.000. La carga `small` **no** tiene que cumplir todavía los mínimos de volumen final.

Durante la carga se conservaron **activos** triggers y FK. Se comprobaron 32 relaciones sin huérfanos, cero stock negativo y cero comprobantes con importes inconsistentes. La auditoría RN-13 se obtuvo mediante un `UPDATE` efectivo de `vino.precio`, después de generar las ventas. Se verificó reproducibilidad de dos ejecuciones `small` con la misma semilla en dos bases separadas: 27 tablas comparadas, cero diferencias, excluyendo únicamente `auditoria_precio.fecha_hora` (marca automática). Las fechas de transferencias y ventas dependientes de `CURRENT_DATE` coincidieron porque ambas cargas se realizaron el mismo día; ejecutar en otros días puede producir fechas operativas diferentes.

## 6. Respaldo de la base cargada

El paso 8 exige generar `dump_completo.sql.gz` o proporcionar instrucciones para generarlo si supera el tamaño permitido. Para PostgreSQL instalado localmente en Windows, después de validar una base `full`:

```powershell
$carpeta = Join-Path (Split-Path $PWD.Path -Parent) "evidencias_fase3"
New-Item -ItemType Directory -Force -Path $carpeta | Out-Null
$archivoSql = Join-Path $carpeta "dump_completo.sql"
$archivoGz = Join-Path $carpeta "dump_completo.sql.gz"

& "C:\Program Files\PostgreSQL\18\bin\pg_dump.exe" -h 127.0.0.1 -p 5432 -U postgres -d NOMBRE_BASE_FULL --format=plain --encoding=UTF8 --file="$archivoSql"
if ($LASTEXITCODE -ne 0) { throw "Falló pg_dump" }

python -c "import sys,gzip,shutil; f=open(sys.argv[1],'rb'); g=gzip.open(sys.argv[2],'wb',compresslevel=6); shutil.copyfileobj(f,g); g.close(); f.close()" "$archivoSql" "$archivoGz"
if ($LASTEXITCODE -ne 0) { throw "Falló la compresión GZIP" }
```

El respaldo final se creó desde `bodegas_atuel_fase3_full_final`, se comprobó la integridad de GZIP y se restauró en `bodegas_atuel_restauracion`. Las consultas de integridad sobre la base restaurada volvieron a dar **27 tablas con datos, 32 FK sin huérfanos, cero stock negativo y cero inconsistencias de importes**. No versionar un dump grande en Git sin coordinación del equipo; adjuntarlo por el medio acordado con la cátedra.

## 7. Mediciones y resultados registrados (30/10/2026)

**Carga final**: PostgreSQL 18.1, perfil `full`, semilla `20261027`, tamaño de lote `1000`.

| Módulo | Tiempo (s) |
| --- | ---: |
| Catálogos | 0,18 |
| Producción | 2,41 |
| Logística | 7,56 |
| Ventas | 172,90 |
| **Total, incluida RN-13** | **183,41** |

**Conteos y controles**: 27/27 tablas con al menos una fila; cuatro tablas por encima de 10.000; dos tablas por encima de 100.000; 20.000 clientes, 150.000 comprobantes, 500.000 renglones de venta y una auditoría de precios. Conciliación de salas: 89.537.974 botellas transferidas menos 999.954 vendidas igual a 88.538.020 existentes; cero diferencias por sala y vino.

**Prueba de rendimiento**: comparación aislada sobre tabla temporal derivada de `cliente`, sin FK ni triggers, con 10.000 filas idénticas y tres repeticiones. Mediana: `INSERT` individual **3,501 s** y `COPY FROM STDIN` **0,134 s**; `COPY` resultó **26,14 veces más rápido** en este ensayo. Esta prueba no representa el tiempo de la carga real con triggers y FK.

**Reproducibilidad**: `bodegas_atuel_rn13_small` frente a `bodegas_atuel_repro_small`, perfil `small`, semilla `20261027`: 27/27 tablas idénticas en su contenido y conteos al comparar representaciones `to_jsonb` ordenadas y huellas SHA-256, salvo la exclusión explícita de `auditoria_precio.fecha_hora`, por depender del reloj del servidor. Se utilizó la misma fecha operativa de PostgreSQL en ambas ejecuciones. El control terminó con código de salida 0.

**Integridad del dump comprimido**: 10.502.108 bytes, SHA-256 `D1A066940B9429866FB490D7CE5675159218BDB7F7376CB9582C490696DD0B78`. El archivo se guarda fuera del repositorio.

## 8. Evidencias para el informe

El informe de la Etapa 3 desarrolla fuentes de los CSV, orden y dependencias, estrategia y riesgos de triggers, conteos de las 27 tablas, resultados de `control_integridad.sql`, conciliación de stock, comparación medida de tiempos, reproducibilidad, copia de seguridad y restauración. Las salidas de ejecución y los archivos CSV/TXT se conservan como respaldo en la computadora del equipo; el dump se entrega por el mecanismo acordado con la cátedra.
