# Preparación de Vercel Hobby — Fase 8

**Responsable:** Lautaro. **Estado (2026-11-09):** propuesta lista para auditoría; sin despliegue ni URL definitiva de Render.

## Archivos publicados en este PR

- `front/vercel.json.example`: **plantilla inerte** con los dos rewrites aprobados. Vercel **no** carga este archivo como configuración activa.
- `front/DEPLOY_VERCEL.md`: procedimiento, evidencias aportadas y plan de pruebas.

**Importante:** No se versiona `front/vercel.json` con un marcador de URL. El borrador `front/vercel.json` que Lautaro tenía en su equipo sigue siendo local/no rastreado; debe reemplazarse por una configuración válida, con URL HTTPS real, antes de subirlo y antes del primer Deploy. Este PR es Draft y NO está listo para merge/despliegue.

## Configuración prevista

| Ajuste | Valor |
|---|---|
| GitHub | `videlalauti/trabajo_integrador_bd` |
| Plan | Vercel Hobby, gratuito |
| Root Directory | `front` |
| Framework Preset | Vite |
| Build Command | `npm run build` (predeterminado) |
| Output Directory | `dist` |
| Install Command | Automático con npm; se conserva `package-lock.json` |
| Rama de producción prevista | `integracion/fase8` |
| Variables de entorno frontend | Ninguna credencial necesaria para el cliente HTTP actual |
| Secretos de PostgreSQL / API | SOLO en el servicio backend, no en Vercel ni en Git |

En la importación actual Vercel suele iniciar un despliegue al pulsar **Deploy**. Hasta contar con la URL real de Render y autorización expresa, NO pulsar Deploy ni crear un proyecto por una operación que lo despliegue automáticamente. Puede permanecer sin crear si la plataforma no permite guardar antes de desplegar.

## Rewrites y contrato API

El cliente `front/src/lib/api.ts` usa `fetch(`/api${rutaNormalizada}`, ...)` (ruta relativa, sin hostname fijo). `front/vite.config.ts` define un proxy a localhost **solo para desarrollo**; no interviene en el build publicado.

Cuando Render tenga URL real, el `front/vercel.json` definitivo deberá contener **en este orden**:

1. `/api/:path*` → `https://<HOST_REAL_RENDER>/:path*`, quitando `/api` sin cambiar métodos/cuerpos.
2. `/(.*)` → `/index.html`, fallback de SPA compatible con `BrowserRouter`.

El archivo `vercel.json.example` incluye un marcador intencional **solo como plantilla**. No copiarlo sin reemplazarlo. Revisar que la URL de Render use HTTPS y que `/api/salud` alcance `/salud` del backend.

## Pasos pendientes para activación (solo con autorización)

1. Antonio confirma la URL HTTPS real de la API y la respuesta de `GET /salud`.
2. En la rama `fase8-lautaro-front`, copiar la plantilla a `front/vercel.json` y reemplazar `__URL_HTTPS_RENDER_PENDIENTE__` por la URL exacta **sin barra final**; validar la URL y el JSON.
3. Asegurar que no quede ningún marcador: buscar `__URL_HTTPS_RENDER_PENDIENTE__` en el archivo activo. Repetir las verificaciones locales.
4. Commit adicional de **solo** `front/vercel.json`, revisión de Valentino e integración del Draft PR.
5. Importar/proseguir el proyecto en Vercel Hobby con Root Directory `front`; tras la creación, configurar en **Settings → Environments → Production → Branch Tracking** la rama `integracion/fase8` y confirmar que el despliegue sale de esa rama.
6. Desplegar únicamente cuando el equipo autorice y registrar la URL pública real más las evidencias de las pruebas.

## Evidencias del código y compilación

- En `front/src/App.tsx` están registradas las cinco pantallas principales: inicio `/`, catálogo `/vinos`, ventas `/ventas/nueva`, transferencias `/transferencias`, reportes `/reportes`.
- Rutas adicionales: `/vinos/nuevo`, `/vinos/:cod_vino` y `/vinos/:cod_vino/editar`.
- `front/src/lib/api.ts` utiliza solicitudes relativas `/api`, sin claves ni URL externa fija.
- **Última ejecución compartida por Lautaro antes de publicar este PR** (desde `fase8-lautaro-front` local):
  - `npm.cmd --prefix .\\front run build`: **aprobado**, TypeScript `tsc -b` y Vite 8.3.6, 42 módulos transformados, build completado en 441 ms.
  - `npm.cmd --prefix .\\front run lint`: **aprobado**, `eslint .` sin errores reportados.
  - `git status --short -uall`: `?? front/vercel.json` y dos ZIP antiguos de revisión sin seguimiento.
- Estas son **salidas aportadas por el responsable**, no una prueba CI ni una ejecución actual en Vercel. Repetir build/lint en la revisión final tras incorporar la URL real. Compilar no acredita pruebas de interacción con API.

Comandos para ejecutar en PowerShell, desde la raíz del repositorio:

```powershell
git branch --show-current
npm.cmd --prefix .\front run build
npm.cmd --prefix .\front run lint
Get-Content .\front\vercel.json -Raw | ConvertFrom-Json | Out-Null
git status --short -uall
```

## Checklist de pruebas end-to-end (PENDIENTE: Render + Vercel + DB)

- [ ] `/` carga el estado de conexión; `/api/salud` responde HTTPS con BD conectada vía FastAPI.
- [ ] `/vinos`: carga catálogo, filtros y paginación; alta, detalle y edición verificadas con datos de prueba.
- [ ] `/ventas/nueva`: catálogos, formulario y errores controlados; no efectuar escrituras destructivas en la base final.
- [ ] `/transferencias`: listado/estados y acciones autorizadas, con reglas del backend.
- [ ] `/reportes`: reportes/consultas con datos reales.
- [ ] Abrir cada URL directamente y recargar (F5): no debe devolver 404 de Vercel; la SPA se sirve desde `/index.html`.
- [ ] Las llamadas `/api/*` llegan a Render **sin** el prefijo `/api`, conservando método, JSON y códigos de error.
- [ ] Verificar HTTPS en navegador y API, sin secretos en red, consola, repositorio ni bundle.
- [ ] Ante API inactiva o errores 4xx/5xx, mostrar mensajes controlados y permitir reintentar; probar recuperación tras reactivación de Render.
- [ ] Documentar capturas/URLs de pruebas reales solo después del despliegue y respetando autorizaciones.

## Restricciones

No subir ZIP de revisiones, `dist/`, `node_modules/`, `.env` o credenciales. No fusionar el Draft PR ni desplegar sin aprobación de Valentino. No modificar otros módulos ni el README raíz por este PR.

## Revisión adicional — 2026-11-10

- En `front/src/App.tsx` se actualizó el encabezado visual de «Sistema de gestión — Fase 7» a «Sistema de gestión — Fase 8» mediante el commit de la misma rama. No se cambiaron rutas ni lógica de negocios.
- Verificada en el código la ruta relativa `/api` de `solicitarApi`; el destino `http://127.0.0.1:8001` solo existe como proxy local de desarrollo en `vite.config.ts`, y no queda embebido como host de las llamadas de producción.
- La última comprobación **aportada por Lautaro desde su computadora** fue: Vite 8.3.6, 42 módulos transformados, `npm.cmd --prefix .\\front run build` aprobado (684 ms) y `npm.cmd --prefix .\\front run lint` aprobado (sin errores). Esta salida es **anterior al cambio de etiqueta visual**; repetir ambas pruebas con el commit actualizado y adjuntar su salida.
- La revisión de los archivos fuente principales y de `vercel.json.example` no detectó contraseñas ni valores de conexión a PostgreSQL para el cliente. Esto **no constituye una auditoría automatizada de secretos del historial completo**; antes de liberar comprobar también los archivos versionados, el bundle generado y las variables configuradas en Vercel.
- La configuración activa `front/vercel.json` sigue pendiente de la URL HTTPS definitiva de Render. La plantilla inerte no debe renombrarse/publicarse con el marcador sin sustituirlo por el origen real.
- El Draft PR queda abierto para revisión, **sin merge y sin deploy**. La creación/importación efectiva del proyecto Vercel y la URL pública del frontend se verificarán después de la autorización.
