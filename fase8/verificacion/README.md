# Fase 8 — Verificación de despliegue (Fabricio)

**Estado:** kit de preparación local; no se ha ejecutado backup FULL, restore cloud, pruebas de RN-09 en la nube ni despliegues. PR previsto como **Draft** hacia `integracion/fase8`. La coordinación debe revisar antes del merge.

## Inventario

- `scripts/check_public_api.py`: diagnóstico HTTPS `/salud` sin redirecciones; exige `estado=ok`, `base_datos=conectada` y **`tls: true` booleano** en la conexión de FastAPI. Solo usar cuando esté desplegado y autorizado.
- `scripts/comparar_conteos.py`: comparador legado, conservado para reproducir el hallazgo.
- `scripts/comparar_conteos_estricto.py`: comparación exigente de 27 tablas y volúmenes.
- `scripts/test_kit.py` y `scripts/test_comparador_estricto.py`: 8 originales + 10 nuevas de TLS/redirecciones + 9 del comparador estricto; todas offline.
- `sql/01_conteos_public.sql`: conteo exacto de las 27 tablas.
- `sql/02_roles_tls_solo_lectura.sql`: inspección de sesión y privilegios. **Una sesión psql no prueba la conexión TLS usada por FastAPI**.
- `sql/03_objetos_restauracion_solo_lectura.sql`: cantidades de objetos y funciones SECURITY DEFINER.
- `sql/04_inventario_estructura.sql`: inventario de índices, constraints, triggers, rutinas y ACL efectivas.
- `sql/05_rn09_estado_solo_lectura.sql`: capturas pre/post de stock y conteos para ensayo autorizado.
- `ejemplos/`: datos CSV **ficticios**, nunca evidencia de la nube.
- `01_INFORME_REVISION_LOCAL.md`, `02_MATRIZ_EVIDENCIAS.md`, `03_GUION_DEMO_14_MIN.md`.
- `BACKUP_RESTORE_PG17.md`, `SEGURIDAD_Y_RN09.md`, `EVIDENCIAS_Y_ESTADOS.md`.
- `pruebas_locales/`: salidas offline reproducibles; no secretos ni dumps.

## Ejecutar tests offline

Desde raíz del repositorio, con Python 3.11+:

```powershell
python fase8/verificacion/scripts/test_kit.py
python fase8/verificacion/scripts/test_comparador_estricto.py
```

Esperado: 18 y 9 tests en estado OK (se mantienen las 17 pruebas anteriores y se agregan 10). Ninguna prueba offline consulta Supabase.

## Comparación ilustrativa (rechazo esperado)

```powershell
python fase8/verificacion/scripts/comparar_conteos_estricto.py --origen fase8/verificacion/ejemplos/origen_ejemplo.csv --destino fase8/verificacion/ejemplos/restaurado_ejemplo.csv --perfil nube_reducida
```

Los CSV contienen 3/27 tablas; **debe devolver código 1, NO APROBADO, 24 faltantes**. Una copia restaurada real exige 27 OK y revisión independiente de ACL/DDL.

## Seguridad de publicación

**No subir** `.env`, credenciales, dumps, CSV reales con PII, salidas sensibles, URLs con password ni capturas sin redactar. Ejecutar `git diff --cached --check`, revisar rutas de `git diff --cached --name-only`, y publicar solo esta carpeta. No hacer merge ni desplegar desde el PR Draft.
