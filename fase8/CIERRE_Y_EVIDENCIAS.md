# Fase 8 — Despliegue en la nube y cierre de evidencias

**Documento de coordinación, 10/11/2026. Estado: despliegue público operativo; cierre de aceptación EN CURSO.** **Actualización: circuito funcional cloud 3/3 probado mediante HTTPS y auditado de forma independiente.** No confundir un control configurado con una prueba ejecutada. Fuente de requisitos: `TPI_Bodegas_del_Atuel.pdf`, etapa 8, pp. 18–19; demostración de etapa 9, p. 20.

## 1. Arquitectura realmente desplegada

```text
Visitante → HTTPS https://bodegas-del-atuel.vercel.app
              └─ /api/* (rewrite de Vercel)
                   → HTTPS https://bodegas-atuel-api.onrender.com
                       → Session Pooler TLS verify-full
                         → PostgreSQL 17.11 Supabase FULL (sjfyocokehaubuwwbhnw)
```

- **Frontend:** React/Vite en Vercel Hobby, con rutas relativas `/api` y fallback SPA. La versión pública utiliza el contrato **H1 (solo lectura)**: catálogo, detalle, ranking y salud; no permite altas, ventas ni transferencias desde visitantes anónimos.
- **Backend productivo:** FastAPI en Render Free; `app.main`, conexión con rol `bodega_api` de privilegios limitados y variables secretas del proveedor. La API pública bloquea escrituras por seguridad, sin depender de ocultar formularios.
- **Base FULL:** Supabase PostgreSQL 17.11, proyecto `sjfyocokehaubuwwbhnw`, migraciones 001–008 y datos completos; conexión cifrada y allowlist de red. No realizar demostraciones de escritura en este proyecto.
- **Ensayo funcional SEPARADO:** `https://bodegas-atuel-demo-api.onrender.com` (`app.demo_main`, `api/Dockerfile.demo`), conectado al Supabase `zfxocudcvriicrzgmxie` (dataset ficticio: 3 vinos, 2 clientes, 2 salas), exclusivamente para pruebas autorizadas. Autenticación con bearer secreto; lista cerrada de rutas; nunca usar la referencia FULL. No hay frontend público para escribir en FULL.
- **Commit exacto del segundo Render verificado en evidencia:** `9e7a07af9a7054c38e3a63f45fabca92aec22dcb`. El código de la demo está en el **Draft PR #22** y NO debe mezclarse con la API pública sin revisión.

## 2. Proveedores evaluados y decisión

| Alternativa | Ventajas y límites relevantes | Decisión |
| --- | --- | --- |
| **Vercel Hobby + Render Free + Supabase Free** | Front estático por HTTPS, API FastAPI en contenedor, PostgreSQL administrado separado. Vercel Hobby es para uso personal/no comercial; Render comparte **750 horas de instancia Free por workspace por mes** (los dos servicios consumen el mismo cupo; pueden suspenderse o dormir); Supabase Free contempla **2 proyectos activos**, con cuota de base **500 MB por proyecto** y pausa por inactividad. Su disco provisionado puede mostrar **2 GB**: no confundir capacidad asignada de disco con cuota del plan; verificar siempre el panel actual. | **Elegida** para TP académico, con vigilancia de límites y sin contratar servicios. |
| **Railway (API y PostgreSQL)** | Plataforma integrada; su Free anuncia recursos gratuitos limitados (US$1 de recursos según su documentación de precios), con planes pagos si se exceden. No ofrecía la misma certeza de sostener este esquema completo en presupuesto US$0. | No elegida. |
| **VM propia con Docker** | Flexibilidad y control; exige administrar SO, firewall, certificados, parches, backup y uptime. No se presupuso una VM gratuita garantizada disponible. | No elegida: complejidad innecesaria para el alcance académico. |

La comparación y los límites corresponden a las páginas oficiales consultadas el 10/11/2026: [Render Free](https://render.com/docs/free), [Vercel Hobby](https://vercel.com/docs/plans/hobby), [Supabase Free](https://supabase.com/pricing), [Railway Pricing](https://docs.railway.com/pricing). Confirmar límites/costos vigentes en los paneles antes de cambiar planes o sumar servicios. **No activar planes de pago por accidente.**

## 3. Seguridad y operación

- **TLS de extremo de BD:** en Render `DB_SSLMODE=verify-full`, `DB_SSLROOTCERT` como Secret File y host del **Session Pooler**; `GET /salud` de la API demo devolvió `200 {"estado":"ok","base_datos":"conectada","tls":true}` según evidencia de Antonio del 10/11.
- **IP permitidas del DEMO:** `74.220.48.0/24`, `74.220.56.0/24` (salidas de Render Oregon); captura del Dashboard sin `0.0.0.0/0` ni `::/0`. La allowlist controla conexiones directas PostgreSQL/pooler, no sustituye RLS ni permisos. La prueba desde IP NO autorizada sigue pendiente; no confundir fallo de password con bloqueo de red.
- **Permisos:** la API usa rol técnico no propietario; evitar `postgres`, `service_role` o superusuario en servicios públicos. Proyecto DEMO con roles técnicos, 27 tablas con RLS y acceso Data API público a tablas del TP revocado.
- **Secretos:** `DB_PASSWORD` y `FASE8_DEMO_TOKEN` se cargaron ocultos en Environment de **Render DEMO**, y no se imprimieron en evidencias. Mantener fuera de Git, scripts, URLs, capturas y logs. **La auditoría del historial completo de Git no se da por concluida aún.**
- **Fail-closed:** la demo rechaza configuración insegura, referencia del proyecto FULL y rutas ajenas al alcance; requiere bearer para lectura y para las operaciones de prueba. Desplegada de forma manual con Auto-Deploy OFF, PR #22 Draft.
- **H1:** no desactivar bloqueo de escrituras productivo para probar la Fase 8. Las escrituras, si se autorizan, se ejecutan únicamente en `zfxocudcvriicrzgmxie` con datos ficticios.

## 4. Migraciones, datos y controles

**FULL:** migraciones `db/migrations/001_esquema.sql` a `008_indices.sql`, carga histórica `full` con 750 vinos, 20.000 clientes, 150.000 comprobantes y 500.000 renglones de comprobantes según controles anteriores del equipo. Cumple el umbral cloud de 10.000 filas en al menos una tabla; no fue necesario invocar la excepción de carga reducida para FULL. Revalidar conteos en la evidencia final.

**DEMO:** migraciones 001–006 y 008 originales más adaptación documentada de 007 compatible con Supabase gestionado; 27 tablas, 32 FK y dataset **mínimo sintético**, no un reemplazo de FULL ni el perfil `small`. Archivos y controles del proyecto de ensayo en el [Draft PR #22](https://github.com/videlalauti/trabajo_integrador_bd/pull/22), carpeta `fase8/demo_aislada/sql/`.

**Corte adicional de evidencia FULL:** el 10/11/2026 se ejecutó directamente contra Supabase FULL, en modo **solo SELECT**, el SQL exacto `fase8/verificacion/sql/01_conteos_public.sql`. Resultado: **27 de 27 tablas presentes y contadas**. El CSV observado está en [`fase8/evidencias/CONTEOS_FULL_ORIGEN_2026-11-10.csv`](evidencias/CONTEOS_FULL_ORIGEN_2026-11-10.csv). Este corte **NO** acredita por sí solo coincidencia con la base local restaurada; ver [acta de cierre y pendientes](ACTA_CONTROL_FINAL_2026-11-10.md).

Se probó en el PostgreSQL DEMO cloud el circuito de venta válida, RN-09 y transferencia **dentro de una transacción revertida (ROLLBACK)**. En GitHub Actions se probaron circuitos reales por HTTP con PostgreSQL 17 descartable, además de la batería de seguridad y regresión para el SHA indicado. **Además, el 10/11/2026 se completó y auditó independientemente la prueba HTTP sobre Render DEMO cloud; consultar sección 7.**

## 5. Reproducción sin exponer credenciales

1. Clonar el repositorio y seleccionar el commit/branch revisado de la entrega. Para local ver [README principal](../README.md), `compose.fase6.yml` y `compose.fase7.yml`.
2. Crear **otro** PostgreSQL vacío y aislado (no reutilizar la base FULL). Preparar los roles propietario, API lectura/escritura y solo lectura según `db/migrations/007_roles.sql`. En Supabase administrado, utilizar la adaptación de 007 documentada del entorno de ensayo.
3. Aplicar `db/migrations/001_esquema.sql` … `008_indices.sql` en orden con el rol propietario. No repetir migraciones destructivas contra una base ya poblada.
4. Poblar la base siguiendo `db/seed/README.md`, los CSV y `db/seed/run_seed.py`; fijar `PROFILE` y validar controles de integridad antes de publicar. Elegir `small` o `full` según el tamaño real permitido.
5. Configurar **solo en el proveedor** `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_SSLMODE=verify-full`, `DB_SSLROOTCERT` y pool pequeño. Prohibido subir `.env` con secretos.
6. Restringir la red de la BD a los CIDR de salida verdaderos del backend; conservar vías administrativas necesarias. Probar rechazo desde IP ajena de manera que se distinga de error de autenticación.
7. Construir y desplegar `api/Dockerfile` para la aplicación pública con **H1 habilitado**. Comprobar `GET /salud` (estado 200, conexión y TLS), `GET /vinos` y rechazos de métodos bloqueados.
8. Compilar y publicar `front/` en Vercel Hobby, con el rewrite `/api/:path*` apuntando a la URL HTTPS **real** del backend y el fallback `/(.*)` a `/index.html`. Verificar `/api/salud`, catálogo, ranking, recarga de rutas y que no se envíen POST en H1.
9. Mantener las pruebas que escriben sobre una **base descartable** usando `api/Dockerfile.demo` y `app.demo_main`, token bearer exclusivo, `FASE8_DEMO_PROJECT_REF` distinto de FULL y los gates de `fase8/demo_aislada/README.md`. No activar esta API hasta revisar controles de seguridad.
10. Crear `pg_dump` del origen, restaurar con `pg_restore` o `psql` en una **base NUEVA**, ejecutar los mismos SELECT de conteos/integridad antes y después, y archivar hash, comandos y resultados sin secretos.

## 6. Estado de aceptación y evidencia exigida

| Criterio de etapa 8 (consigna pp. 18–19) | Estado y respaldo |
| --- | --- |
| PostgreSQL en nube; API y frontend públicos HTTPS | **Verificado**: URLs públicas; Render productivo y Vercel, SQL cloud FULL. |
| Migraciones y volumen mínimo cloud | **Verificado en implementaciones**; consolidar log/captura y conteos finales FULL. |
| TLS, rol mínimo, secretos en proveedor y puerto restringido | **Configurado y parcialmente probado**. DEMO health TLS true y CIDR en Dashboard; falta prueba negativa desde IP no permitida y auditoría histórica de secretos. |
| Backup `pg_dump`, restauración en base nueva y conteos coincidentes | **Restauración local informada**; archivo final y tamaño reportados por el equipo; **SHA-256 calculado en PowerShell por Valentino y documentado**. Faltan evidencia primaria de `pg_restore` y 27 conteos del destino restaurado. No declarar cerrado sin acta reproducible. |
| Trigger funcionando en nube | **APROBADO**: venta HTTP 201, RN-09 HTTP 409/P0001 sin filas extra ni cambios de stock y transferencia procesada en API Render DEMO con PostgreSQL cloud; auditoría independiente documentada en sección 7. |
| README con URL pública y reproducción | Actualización preparada en el Draft PR documental; pendiente integrar y revisar la versión publicada. |
| Cualquier persona abre URL y usa el sistema | **Parcial**: consulta pública real funcionando, pero las operaciones de escritura quedan restringidas por H1. Confirmar con cátedra si demo separada cumple este criterio. |

### Próximos gates (sin modificar FULL)

1. **Antonio:** completó GET sin token (`401`, `401`, `403`), preflight autenticado y un único ensayo funcional por HTTPS con resultado **3/3**; ya auditado.
2. **Coordinación:** conservar sin repetir la evidencia del ensayo cloud; mantener el token privado y el entorno H1 protegido. Revisar con cátedra el alcance de la demostración separada.
3. **Fabricio / Valentino:** cerrar acta de backup/restore sobre una base distinta, con SHA-256 y conteos comparados; guardar evidencias finales sin contraseñas ni dumps sensibles.
4. **Lautaro:** capturas de Vercel y navegación H1, HTTPS, rewrite y ausencia de operaciones de escritura públicas.
5. **Equipo:** comprobar bloqueo IP desde origen no permitido, auditar historial Git para secretos, revisar PRs y consolidar README; decidir con cátedra alcance de la demo pública para Fase 8/9.

**Regla de seguridad para el cierre:** sin deshabilitar H1 productivo, sin PR #22 a producción, sin tocar FULL para pruebas de negocio y sin fusionar ni desplegar automáticamente esta documentación.

## 7. Evidencia confirmada: venta, RN-09 y transferencia HTTPS cloud (10/11/2026)

**Ámbito:** exclusivamente API Render DEMO y Supabase `zfxocudcvriicrzgmxie`, datos ficticios. SHA probado `9e7a07af9a7054c38e3a63f45fabca92aec22dcb`. Antonio ejecutó una sola vez el CLI `fase8/demo_aislada/ejecutar_demo.py --ejecutar --confirmar-demo SOLO_BASE_DESCARTABLE`, tras comprobaciones 401/401/403 y preflight autenticado/dry run. No se compartieron secretos.

**Salida observada por Antonio:** `PRECHECK OK`, `VENTA OK: comprobante=3, stock -1`, `RN-09 OK: 409/P0001 y rollback completo`, `TRANSFERENCIA OK: nro=2, deposito -1, sala +1`, `RESULTADO 3/3`. El script comprueba con lecturas HTTP después de cada operación que el rechazo de stock insuficiente no cambie conteos ni stock.

| Verificación | Antes | Después AUDITADO por consulta SQL directa READ ONLY |
| --- | ---: | ---: |
| Comprobantes | 0 | **1** (nro. **3**, cliente 1, sala 1) |
| Renglones de comprobante | 0 | **1** (vino 1, cantidad 1) |
| Transferencias | 0 | **1** (nro. **2**, estado `procesado`, vino 1, cantidad 1) |
| Stock vino 1, sala 1 | 30 | **30** (venta -1; transferencia +1) |
| Stock vino 1, depósito | 120 | **119** (transferencia -1) |
| Stock total en salas | 165 | **165** |
| Stock total en depósito | 360 | **359** |

El comprobante 3 presenta subtotal **1.300,00**, descuento **130,00** y total **1.170,00**; fecha de transferencia **2026-11-10**. El intento RN-09 demandó 30 botellas cuando quedaban 29 y devolvió 409/P0001 sin crear segundo comprobante ni consumir stock, acorde a los controles del script y a los conteos finales. Que los números reales empiecen en 3 y 2 no es anomalía: las secuencias consumen valores incluso cuando `ROLLBACK` revierte las filas; el intento RN-09 avanzó la secuencia de comprobantes hasta 4. **No modificar ni reiniciar secuencias.**

**Auditoría READ ONLY de la FULL posterior:** vinos **750**, clientes **20.000**, comprobantes **150.000**, renglones **500.000**, transferencias **2.000**, stock salas **88.538.020** y depósito **22.384.854**, sin cambios respecto de los controles previos. No se ejecutaron escrituras contra FULL.

**Resultado:** **demostración técnica de reglas de negocio en la nube APROBADA** mediante API separada. La Fase 8 en su conjunto **NO** queda automáticamente cerrada: siguen pendientes las evidencias primarias de restauración y los 27 conteos del destino (el SHA del dump ya está informado), prueba denegada desde IP no autorizada, auditoría de secretos histórica y confirmación del alcance H1/demo con la cátedra.
