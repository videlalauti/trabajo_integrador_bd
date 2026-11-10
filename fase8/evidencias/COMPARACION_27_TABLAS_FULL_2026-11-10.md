# Comparación de conteos: FULL Supabase → recuperación PostgreSQL 17.11 local

**Fecha del contraste:** 10/11/2026. **Resultado: 27 de 27 conteos IDÉNTICOS** (comparación línea a línea entre los dos CSV versionados). No se realizaron operaciones de escritura ni un nuevo `pg_restore`.

## Identificación de los resultados

| Lado | Origen de la evidencia | Archivo |
| --- | --- | --- |
| Origen | `Supabase FULL`, proyecto `sjfyocokehaubuwwbhnw`. Consulta SELECT del coordinador vía conector SQL el 10/11 sobre `fase8/verificacion/sql/01_conteos_public.sql` | [`CONTEOS_FULL_ORIGEN_2026-11-10.csv`](CONTEOS_FULL_ORIGEN_2026-11-10.csv) |
| Destino | Contenedor local `bodegas-g1c-restauracion-pg17`, PostgreSQL **17.11**, base `bodegas_g1c_final_full`. Salida CSV real de PowerShell **aportada por Valentino** el 10/11 de `git show FETCH_HEAD:fase8/verificacion/sql/01_conteos_public.sql` y `docker exec ... psql --csv` | [`CONTEOS_FULL_DESTINO_LOCAL_2026-11-10.csv`](CONTEOS_FULL_DESTINO_LOCAL_2026-11-10.csv) |

**Método de comparación:** se revisaron la cabecera `tabla,filas`, las 27 filas ordenadas y sus números; las 28 líneas fueron idénticas. Total sumado de filas de todas las tablas: **727.191** en origen y destino. Los conteos coinciden en cada una de las 27 tablas, incluidas `cliente=20000`, `comprobante=150000`, `renglon_comprobante=500000`, `permiso_exportacion=13278`, `vino=750`, `stock_sala=7255` y `stock_deposito=750`.

**Respaldo origen reportado:** `g1c_final_full_REINTENTO_20261109_225055.dump`, **10.452.417 bytes** y SHA-256 **`B5E48E30A0AB0011E99DD2FA3664C0C315B15BC5F4C7196EA3106A6571BED055`**, calculado por Valentino en su equipo y no recalculado por el auditor.

## Límites explícitos

1. El **destino no fue consultado remotamente por el auditor**; las filas del CSV destino se transcribieron exactamente de la salida `psql --csv` aportada por Valentino en conversación. Los conteos de origen sí proceden de SQL directo sobre Supabase.
2. La lectura del origen es posterior al respaldo; no se ha acreditado coincidencia de snapshot temporal exacto, aunque sus conteos coinciden.
3. Igualdad de conteos **no implica igualdad de contenido por fila**. Posteriormente **sí se verificaron en el destino** los 32 FK, los 11 triggers y otros controles: **15/15 métricas numéricas iguales** en [`ESTRUCTURA_FULL_DESTINO_LOCAL_2026-11-10.csv`](ESTRUCTURA_FULL_DESTINO_LOCAL_2026-11-10.csv), cotejadas con [`ESTRUCTURA_FULL_ORIGEN_2026-11-10.csv`](ESTRUCTURA_FULL_ORIGEN_2026-11-10.csv). No demuestra identidad de definiciones/ACL (`--no-owner --no-acl`).
4. Falta adjuntar código de salida/log real del `pg_restore` y el inventario `pg_restore -l` del dump. No ejecutar una nueva restauración solo para generar evidencia.

**Conclusión:** **APROBADO — conteos 27/27 de origen y destino**. **Pendiente de cierre integral**: definiciones/propietarios/ACL del destino, registro primario del restore y controles de seguridad; inventario numérico estructural del destino 15/15 sí comprobado.
