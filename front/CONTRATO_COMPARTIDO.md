

# Contrato compartido — Fase 7

## Bodegas del Atuel



**Estado:** Base compartida en preparación.



Este documento define las reglas técnicas que deben respetar

los cinco integrantes durante el desarrollo del frontend.



## 1. Tecnologías



\- React 19.

\- Vite 8.

\- TypeScript 6.

\- React Router.

\- CSS.

\- FastAPI como backend.

\- PostgreSQL 18 como base de datos.



No instalar librerías adicionales sin coordinar previamente

con Valentino.



## 2. Arquitectura



El frontend está ubicado en `front/`.



Estructura:



\- `src/App.tsx`: navegación y registro de pantallas.

\- `src/index.css`: estilos generales.

\- `src/components/`: componentes reutilizables.

\- `src/layouts/`: estructura visual compartida.

\- `src/lib/api.ts`: cliente HTTP compartido.

\- `src/types/`: tipos compartidos.

\- `src/pages/`: módulos individuales.



Cada integrante debe mantener su código dentro del módulo

que le corresponde.



## 3. Distribución de responsabilidades



### Valentino — Infraestructura



Responsable de:



\- Configuración de React, Vite y TypeScript.

\- Navegación y componentes compartidos.

\- Cliente HTTP y manejo común de errores.

\- Configuración de Docker.

\- Coordinación de endpoints auxiliares.

\- Integración y pruebas finales.



Archivos compartidos bajo su responsabilidad:



\- `front/src/App.tsx`

\- `front/src/index.css`

\- `front/src/lib/`

\- `front/src/components/`

\- `front/src/layouts/`

\- `front/src/types/`

\- `front/vite.config.ts`

\- `front/package.json`



### Lautaro — Vinos



Directorio asignado:



`front/src/pages/vinos/`



Responsable de:



\- Catálogo paginado.

\- Filtros por tipo, cepa, bodega y añada.

\- Detalle de vinos.

\- Alta de vinos.

\- Edición de vinos.

\- Visualización de cepas y maridajes.

\- Mostrar los errores reales de PostgreSQL.



### José — Ventas



Directorio asignado:



`front/src/pages/ventas/`



Responsable de:



\- Pantalla de nueva venta.

\- Selección de cliente y sala.

\- Selección de vinos y cantidades.

\- Registro del comprobante.

\- Visualización de importes devueltos por la API.

\- Errores de stock insuficiente.

\- Confirmación de venta realizada.



### Antonio — Transferencias



Directorio asignado:



`front/src/pages/transferencias/`



Responsable de:



\- Crear transferencias.

\- Agregar renglones.

\- Consultar transferencias.

\- Mostrar los estados.

\- Terminar transferencias.

\- Procesar transferencias.

\- Mostrar errores de reglas de negocio.



### Fabricio — Reportes



Directorio asignado:



`front/src/pages/reportes/`



Responsable de:



\- Ranking de vinos más vendidos.

\- Gráfico de ventas por sala.

\- Listado de vinos sin stock.

\- Estados de carga y errores.

\- Revisión funcional de las pantallas.

\- Evidencias visuales y pruebas manuales.



## 4. Rutas del frontend



Las rutas son administradas por Valentino desde `App.tsx`.



\- `/`: inicio.

\- `/vinos`: catálogo.

\- `/vinos/:cod_vino`: detalle de un vino.

\- `/vinos/nuevo`: alta de vinos.

\- `/vinos/:cod\_vino/editar`: edición.

\- `/ventas/nueva`: nueva venta.

\- `/transferencias`: transferencias.

\- `/reportes`: tablero.



Los integrantes deben exportar sus componentes para

que Valentino los registre en la navegación.



No modificar `App.tsx` individualmente.



## 5. Comunicación con FastAPI



Todas las solicitudes deben utilizar:



`src/lib/api.ts`



Función disponible:



`solicitarApi<T>(ruta, opciones)`



Ejemplo:



```typescript

const resultado = await solicitarApi('/vinos')

```



La función utiliza el prefijo `/api`, configurado

en el proxy de Vite.



No escribir URLs como `localhost:8001` dentro de

las pantallas.



No crear clientes HTTP independientes.



## 6. Manejo de errores



El backend devuelve errores con un formato similar a:



```json

{

&#x20; "error": {

&#x20;   "codigo": "P0001",

&#x20;   "mensaje": "RN-09: Stock insuficiente"

&#x20; }

}

```



El frontend debe mostrar mensajes comprensibles para

el usuario, sin ocultar la información de negocio.



La clase `ErrorApi` contiene:



\- `status`: código HTTP.

\- `codigo`: código de error.

\- `message`: mensaje recibido.



Los errores de validación, falta de conexión y conflictos

de negocio deben tratarse de manera diferenciada.



## 7. Reglas de negocio



PostgreSQL sigue siendo la autoridad sobre:



\- Stock.

\- Descuentos.

\- Subtotales.

\- Totales.

\- Estados de ingresos y transferencias.

\- Restricciones de integridad.



El frontend puede validar formatos y cantidades básicas

para mejorar la experiencia del usuario.



No debe reemplazar ni duplicar las reglas de PostgreSQL.



Los importes de ventas deben obtenerse de la API,

no calcularse mediante JavaScript.



## 8. Contratos HTTP disponibles



### Vinos

\- GET `/vinos`

\- GET `/vinos/{cod\_vino}`

\- POST `/vinos`

\- PUT `/vinos/{cod\_vino}`

\- DELETE `/vinos/{cod\_vino}`



### Ventas

\- POST `/comprobantes`

\- GET `/comprobantes/{nro\_comprobante}`



### Clientes

\- GET `/clientes`

\- GET `/clientes/{id\_cliente}`



### Transferencias

\- POST `/transferencias`

\- GET `/transferencias/{nro\_solicitud}`

\- POST `/transferencias/{nro\_solicitud}/renglones`

\- POST `/transferencias/{nro\_solicitud}/terminar`

\- POST `/transferencias/{nro\_solicitud}/procesar`



### Reportes

\- GET `/reportes/top-vinos`

\- GET `/reportes/ventas-por-sala`

\- GET `/reportes/vinos-sin-stock`

\- GET `/reportes/transportista-activo`

\- GET `/reportes/trazabilidad/{cod}`



Los formatos exactos de entrada y salida deben consultarse

en los schemas de FastAPI y en `/docs`.



### Catálogos auxiliares

Los siguientes endpoints están implementados, probados e
integrados en `integracion/fase7`:

- GET `/salas`: id_sala, calle, numero, localidad.
- GET `/bodegas`: cuit, razon_social.
- GET `/cepas`: id_cepa, nombre, tipo.
- GET `/maridajes`: id_maridaje, nombre, temperatura_servicio_c.

Todos devuelven arreglos JSON.

El campo temperatura_servicio_c se serializa como string decimal.

Estos endpoints son de solo lectura y utilizan datos reales
de PostgreSQL 18.



No inventar endpoints ni identificadores fijos.



## 9. Reglas de trabajo con Git



Rama de integración:



`integracion/fase7`



Ramas individuales:



\- `fase7-lautaro-vinos`

\- `fase7-jose-ventas`

\- `fase7-antonio-transferencias`

\- `fase7-fabricio-tablero`



Cada rama individual debe crearse a partir de la base

compartida publicada de Fase 7.



No crear ramas desde una versión anterior de `main`.



No modificar archivos pertenecientes a otro integrante.



No modificar la API ni las migraciones de PostgreSQL

sin coordinación.



Antes de entregar, ejecutar desde `front/`:



```powershell

npm.cmd run build

npm.cmd run lint

```



Cada integrante debe informar:



1\. Archivos creados o modificados.

2\. Funcionalidad implementada.

3\. Pruebas realizadas.

4\. Errores o dependencias pendientes.



El commit y push de cada módulo se realizarán después

de la revisión correspondiente.



La integración a `main` se hará solamente cuando

la Fase 7 completa esté validada.



## 10. Criterios de aceptación



Para aprobar el frontend deben comprobarse:



\- Navegación funcional.

\- Las cinco pantallas de la consigna.

\- Comunicación real con FastAPI.

\- Datos obtenidos de PostgreSQL.

\- Formularios con validaciones.

\- Errores reales de reglas de negocio.

\- Venta sin stock rechazada correctamente.

\- Totales obtenidos desde el backend.

\- Transferencias con estados correctos.

\- Reportes y gráficos funcionales.

\- Compilación TypeScript exitosa.

\- ESLint sin errores.

\- Ejecución integrada mediante Docker.



## 11. Dependencias pendientes


Los catálogos auxiliares de salas, bodegas, cepas y maridajes
ya están disponibles en la API e integrados en la rama compartida.

Las dependencias adicionales que identifiquen los módulos
individuales deberán revisarse antes de su implementación.


Los integrantes deben informar cualquier endpoint

faltante antes de implementar soluciones alternativas.



No utilizar datos simulados como evidencia final.



## 12. Orden de integración



1\. Base compartida — Valentino.

2\. Catálogo y formularios de vinos — Lautaro.

3\. Nueva venta — José.

4\. Transferencias — Antonio.

5\. Tablero — Fabricio.

6\. Pruebas cruzadas y Docker — Equipo completo.



Este documento será la referencia común de la Fase 7.
