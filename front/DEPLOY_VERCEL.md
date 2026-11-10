# Despliegue de Vercel Hobby — Fase 8 (H1 SOLO LECTURA)

## Nota posterior a la preparación — 10/11/2026

**Estado operativo posterior:** el frontend quedó publicado en **<https://bodegas-del-atuel.vercel.app>**, con backend productivo H1 en **<https://bodegas-atuel-api.onrender.com>**. Este archivo original describía el estado **previo al despliegue** de la propuesta de Lautaro (incluida la frase «NO desplegado» y tareas pendientes), por lo que esos renglones deben leerse como evidencia histórica y no como estado actual.

La arquitectura, los resultados cloud de la demo separada y los controles de aceptación restantes están documentados en [`../fase8/CIERRE_Y_EVIDENCIAS.md`](../fase8/CIERRE_Y_EVIDENCIAS.md) y [`../fase8/ACTA_CONTROL_FINAL_2026-11-10.md`](../fase8/ACTA_CONTROL_FINAL_2026-11-10.md). La prueba HTTP 3/3 de negocio se hizo sobre **Supabase DEMO** y no habilita escrituras en el frontend público. Los ítems de la lista original que requieran capturas de navegador todavía deben contrastarse contra evidencias auténticas.

---


**Responsable:** Lautaro. **Estado:** configuración final preparada para revisión. NO desplegado, NO fusionado.

## Configuración aprobada para revisar

- GitHub: `videlalauti/trabajo_integrador_bd`
- Rama de PR: `fase8-lautaro-front` → `integracion/fase8`
- Vercel Hobby gratuito; Root Directory: `front`; Framework: Vite.
- Build: `npm run build`; Output: `dist`; instalación: npm (`package-lock.json`).
- Rama de producción prevista: `integracion/fase8` (configurar en Vercel tras la creación del proyecto, antes de publicación final).
- Sin variables de frontend que contengan credenciales; `DB_PASSWORD`, secretos de Supabase y credenciales pertenecen exclusivamente a Render/Supabase.

`front/vercel.json` define exactamente dos rewrites, en orden:

1. `/api/:path*` → `https://bodegas-atuel-api.onrender.com/:path*` (quita el prefijo `/api`).
2. `/(.*)` → `/index.html` (fallback SPA para `BrowserRouter` y rutas directas).

El ejemplo `front/vercel.json.example` documenta el mismo origen HTTPS real. No hay URL ficticia activa.

## Contrato público H1

La interfaz NO presenta opciones funcionales de alta/edición de vinos, registro de ventas, creación/procesamiento de transferencias ni otros reportes no habilitados.

| Pantalla/ruta | Comportamiento |
|---|---|
| `/` | Estado de salud `GET /api/salud` |
| `/vinos` | Catálogo, filtros y paginación `GET /api/vinos`; catálogos auxiliares `GET /api/bodegas`, `/api/cepas`, `/api/maridajes` |
| `/vinos/:cod_vino` | Detalle mediante `GET /api/vinos/:cod_vino`, sin enlace para editar |
| `/reportes` | Únicamente `GET /api/reportes/top-vinos` |
| `/ventas/nueva`, `/transferencias`, `/vinos/nuevo`, `/vinos/:cod_vino/editar` | Aviso visible de operación bloqueada, sin montar formularios ni emitir POST/PUT/DELETE |

El frontend utiliza `front/src/lib/api.ts` y URL relativa `/api`; el proxy `127.0.0.1:8001` del archivo `vite.config.ts` corresponde solo al desarrollo con Vite y no es una URL de producción. La protección H1 efectiva corresponde también a FastAPI; ocultar controles en React **no** reemplaza un bloqueo de escritura en el backend.

## Evidencia y límites

**Últimas pruebas de compilación aportadas por Lautaro, antes del cambio H1**: `npm.cmd --prefix .\front run build` OK (TypeScript + Vite 8.3.6, 42 módulos, 583 ms) y `npm.cmd --prefix .\front run lint` OK (ESLint sin errores). **Repetir ambos comandos tras recibir el commit H1**; no reportar resultados nuevos sin ejecutarlos.

Comandos PowerShell desde la raíz de `trabajo_integrador_bd`:

```powershell
git switch fase8-lautaro-front
git pull --ff-only
npm.cmd --prefix .\front run build
npm.cmd --prefix .\front run lint
Get-Content .\front\vercel.json -Raw | ConvertFrom-Json | Out-Null
git status --short -uall
```

**Atención:** si el antiguo borrador `front/vercel.json` existe localmente como archivo sin seguimiento, NO hacer `git add .` ni sobrescribir a ciegas: revisar su contenido y conservar respaldo fuera del repositorio antes del `git pull`. Para incorporar la configuración nueva, retirar/renombrar el borrador local y ejecutar `git pull --ff-only`.

La inspección de las rutas del cliente y de los archivos modificados no muestra contraseñas ni cadena de conexión a PostgreSQL. Antes del despliegue, auditar el historial y el bundle final; no incluir secretos en Vercel.

## Checklist original pre-despliegue — conservar como referencia histórica

- [ ] Proyecto importado en Hobby con GitHub correcto, Root Directory `front`, framework Vite, rama `integracion/fase8`.
- [ ] Build remoto aprobado y URL de frontend publicada por HTTPS; capturar URL real.
- [ ] `GET https://<HOST_VERCEL>/api/salud`: HTTP 200, respuesta válida de API/BD.
- [ ] `/vinos`: registros reales, filtros, paginación, selectores de bodegas/cepas y maridajes.
- [ ] `/vinos/:cod_vino`: detalle real, cepas y maridajes; sin opción de editar.
- [ ] `/reportes`: ranking real; sin solicitudes de ventas-por-sala ni stock no autorizadas.
- [ ] `/ventas/nueva`, `/transferencias`, `/vinos/nuevo`, `/vinos/:cod_vino/editar`: solo avisos de bloqueo, sin formularios ni solicitudes de escritura.
- [ ] Recargar las rutas con F5 y abrir enlaces directos; no deben producir 404 de Vercel.
- [ ] Inspeccionar Network: solo GET habilitados; `/api/*` se reescribe al backend sin `/api`; probar HTTP 403 para método no permitido desde una sesión controlada, sin tocar datos FULL.
- [ ] Verificar HTTPS, mensajes de error y reintento cuando API esté temporalmente indisponible.
- [ ] Adjuntar capturas auténticas y controles realizados; no inventar resultados.

**Nota de actualización (10/11/2026):** el PR #14 **ya fue fusionado** en `integracion/fase8` y el frontend ya está publicado en Vercel. La prohibición anterior correspondía exclusivamente a la etapa de preparación y **no es una instrucción operativa vigente**. Las casillas vacías anteriores son el checklist de ese momento; no sustituirlas por capturas o pruebas que no fueron compartidas. Para el estado final consultar [el acta de cierre](../fase8/ACTA_CONTROL_FINAL_2026-11-10.md).
