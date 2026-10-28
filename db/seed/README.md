# Etapa 3 — Carga masiva de datos | Bodegas del Atuel

Este directorio contiene la carga reproducible de datos para PostgreSQL, de acuerdo con la **Etapa 3** del enunciado oficial (páginas 13–14). El README describe cómo preparar y ejecutar la carga; los **conteos y tiempos reales** se incorporarán al informe una vez realizadas las pruebas.

## 1. Requisitos

- PostgreSQL 14 o superior (se trabaja con PostgreSQL 16).
- Una **base de pruebas vacía**, con las migraciones `db/migrations/001_...sql` a `007_...sql` aplicadas en ese orden.
- Python 3 y las librerías `psycopg` y `Faker`.
- Los CSV reales de catálogo en `db/seed/catalogs/` y los cuatro módulos de `db/seed/modules/`, una vez integrados.

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

El ejecutor carga en orden **catálogos → producción → logística → ventas**. Cada módulo debe exponer `seed(conn, rng, faker, config, refs)` y compartir identificadores reales en `refs`; no debe ejecutar `commit()` ni `rollback()` por su cuenta.

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

## 4. Ejecutar la carga (cuando estén integrados los cuatro módulos)

**Este paso aún no está validado de extremo a extremo.** Ejecutarlo solo sobre una base **nueva y descartable** con las migraciones ya aplicadas. `run_seed.py` no crea ni limpia la base y confirma las transacciones por módulo: si uno falla, los anteriores pueden haber quedado cargados.

En PowerShell, definir los parámetros adecuados para la base de pruebas:

```powershell
$env:PROFILE = "small"
$env:SEED = "20261027"
$env:PGHOST = "localhost"
$env:PGPORT = "5432"
$env:PGDATABASE = "NOMBRE_BASE_DESCARTABLE"
$env:PGUSER = "USUARIO_POSTGRES"
# Definir PGPASSWORD en el entorno solo si la conexión lo requiere.
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

Sustituir los nombres del contenedor y de la base. Todas las tablas deben tener al menos una fila; al menos tres tablas deben superar las 10.000 filas y al menos una superar las 100.000. La carga `small` **no** tiene que cumplir todavía los mínimos de volumen final.

También se debe documentar la estrategia de triggers, comparar inserción individual frente a lotes/COPY y repetir la carga con la misma semilla en bases limpias para verificar reproducibilidad. Los timestamps automáticos y `CURRENT_DATE` (RN-11) requieren atención especial al comparar dos ejecuciones en fechas distintas.

## 6. Respaldo de la base cargada

El paso 8 exige generar `dump_completo.sql.gz` o proporcionar instrucciones para generarlo si supera el tamaño permitido. Por ejemplo, con Docker y PowerShell, **solo después de la carga final**:

```powershell
# Ejecutar dentro del contenedor para conservar la codificación del SQL.
docker exec NOMBRE_CONTENEDOR bash -o pipefail -c "pg_dump -U postgres -d NOMBRE_BASE_CARGADA | gzip > /tmp/dump_completo.sql.gz"
if ($LASTEXITCODE -ne 0) { throw "Falló pg_dump" }
docker cp NOMBRE_CONTENEDOR:/tmp/dump_completo.sql.gz .\dump_completo.sql.gz
```


No dar por válido el respaldo sin comprobar que el comando se completó correctamente y que puede restaurarse. No versionar un dump grande en Git sin coordinación del equipo.

## 7. Evidencias para el informe

El informe de la Etapa 3 contendrá: fuentes de los CSV, diagrama de dependencias, metodología y riesgos de triggers, conteos reales, comparación medida de tiempos fila a fila frente a lotes, resultados de `control_integridad.sql`, verificación de reproducibilidad y respaldo o instrucciones de generación. **No se consignarán resultados numéricos hasta haberlos medido.**
