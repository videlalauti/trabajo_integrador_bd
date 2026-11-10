# Auditoría de secretos — clasificación de hallazgos Gitleaks (10/11/2026)

**Contexto:** Valentino ejecutó el escáner oficial de Gitleaks en contenedor Docker, en modo solo lectura, con `git /repo --log-opts="--all" --redact=100`. Primera ejecución: 131 commits y 3 alertas. Segunda ejecución guardando informe JSON privado: **132 commits, 3 hallazgos, código de salida 1**. La diferencia de un commit entre pasadas es compatible con la actualización de referencias/commits de documentación durante esta etapa; el conjunto de tres hallazgos se mantuvo. El JSON privado **NO** fue incorporado ni debe subirse a Git.

## Triage de las tres alertas (solo metadatos sin secretos)

| RuleID | Commit | Archivo y línea histórica | Inspección puntual del código del commit | Clasificación |
| --- | --- | --- | --- | --- |
| `generic-api-key` | `fbbc55f7` | `fase8/demo_aislada/sql/02_roles_supabase_demo.sql:492` | Línea de **comentario SQL** que describe vistas de reportes expuestas por API, sin clave o asignación de credenciales | **FALSO POSITIVO** |
| `generic-api-key` | `3fd1e1e5` | `api/tests/test_config_nube.py:15` | Constante `SECRETO` de **22 caracteres** en prueba unitaria (fixture sintética); se coloca con `monkeypatch.setenv` y se verifica que **no aparezca** en excepciones/cadenas de error | **FALSO POSITIVO (fixture)** |
| `generic-api-key` | `07a2a6aa` | `db/migrations/007_roles.sql:469` | La misma línea de **comentario SQL** sobre vistas de reportes, sin clave o asignación de credenciales | **FALSO POSITIVO** |

Las ubicaciones y los tipos de contenido se verificaron leyendo **las versiones originales de los tres commits en GitHub**, no solo las versiones actuales. No se copiaron a esta acta valores de coincidencia, campos `Match`, `Secret` o `Line` del informe privado de Gitleaks. No se observó en los tres hallazgos una contraseña, token API de servicio o conexión productiva publicable; **no se justifica rotar credenciales únicamente por estas detecciones**.

**Interpretación:** se revisaron manualmente **3/3 hallazgos**, clasificados como falsos positivos. El resultado bruto del escáner **permanece con código 1 y 3 alertas**: no describirlo como «Gitleaks 0 findings» o ejecución limpia. Esta evaluación cubre los 132 commits accesibles al escáner en el repositorio local y las reglas aplicadas; **ningún detector garantiza ausencia absoluta de secretos** en otros formatos o referencias no disponibles.

**Sin acciones destructivas:** no se borraron archivos, no se cambiaron secretos en Render/Supabase, no se reescribió el historial Git, no se creó un allowlist que silencie hallazgos. Cualquier sospecha futura de credencial real exige revocación/rotación previa a la publicación de evidencias.

**Estado de control:** **APROBADO CON TRIAGE DOCUMENTADO** (tres falsos positivos explicados), manteniendo la salida original del escáner como evidencia privada. El control de rechazo de una IP externa del DEMO se completó posteriormente con `EADDRNOTALLOWED`, documentado en [la evidencia de bloqueo](PRUEBA_RECHAZO_IP_SUPABASE_DEMO_2026-11-10.md). Restan acordar con la cátedra el alcance H1/demo y localizar el registro primario original de restauración si existiera.
