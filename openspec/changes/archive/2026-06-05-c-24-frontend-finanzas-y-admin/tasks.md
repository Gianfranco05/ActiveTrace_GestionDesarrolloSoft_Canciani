## 1. Setup y estructura de modulos

- [x] 1.1 Crear estructura `features/finanzas/` con subdirectorios `components/`, `hooks/`, `pages/`, `services/`, `types/`
- [x] 1.2 Crear estructura `features/admin/` con subdirectorios `components/`, `hooks/`, `pages/`, `services/`, `types/`
- [x] 1.3 Agregar entradas NAV_ITEMS para Finanzas (`/finanzas/liquidaciones`, permission `liquidaciones:ver`) y Administracion (`/admin/auditoria`, permission `auditoria:ver`)
- [x] 1.4 Agregar rutas en App.tsx con `ProtectedRoute` > `AppLayout` > `RequirePermission` para todas las paginas nuevas

## 2. Finanzas — Tipos y servicios API

- [x] 2.1 Definir tipos TypeScript en `features/finanzas/types/liquidacion.types.ts`: Liquidacion, LiquidacionKPI, CerrarLiquidacionPayload
- [x] 2.2 Definir tipos en `features/finanzas/types/salario.types.ts`: SalarioBase, SalarioPlus, CreateSalarioBasePayload, CreateSalarioPlusPayload
- [x] 2.3 Definir tipos en `features/finanzas/types/factura.types.ts`: Factura, CreateFacturaPayload, FacturaFilter
- [x] 2.4 Crear `features/finanzas/services/liquidacion.service.ts` con funciones getLiquidaciones, getLiquidacionKPI, cerrarLiquidacion, getHistorialLiquidaciones
- [x] 2.5 Crear `features/finanzas/services/salario.service.ts` con CRUD SalarioBase y SalarioPlus
- [x] 2.6 Crear `features/finanzas/services/factura.service.ts` con getFacturas, createFactura (multipart), cambiarEstadoFactura

## 3. Finanzas — Vista de liquidaciones

- [x] 3.1 Crear hook `useLiquidaciones(filtros)` con TanStack useQuery
- [x] 3.2 Crear hook `useCerrarLiquidacion()` con useMutation + invalidateQueries
- [x] 3.3 Crear componente KPILiquidaciones que muestre totales (general, NEXO, factura, docentes activos)
- [x] 3.4 Crear componente TablaLiquidaciones con pestañas General/NEXO/Factura usando botones/tabs
- [x] 3.5 Crear FiltrosLiquidacion (selectores de cohorte y mes)
- [x] 3.6 Crear `LiquidacionesPage` ensamblando KPIs + filtros + tabla segmentada con ConfirmDialog para cierre
- [x] 3.7 Crear `HistorialLiquidacionesPage` con tabla plana de liquidaciones cerradas

## 4. Finanzas — Grilla salarial

- [x] 4.1 Crear hooks `useSalariosBase()` y `useMutateSalarioBase()` con TanStack Query
- [x] 4.2 Crear hooks `useSalariosPlus()` y `useMutateSalarioPlus()` con TanStack Query
- [x] 4.3 Crear formulario `SalarioBaseForm` con React Hook Form + Zod (rol, monto, desde, hasta)
- [x] 4.4 Crear formulario `SalarioPlusForm` con React Hook Form + Zod (grupo, rol, descripcion, monto, desde, hasta)
- [x] 4.5 Crear `GrillaSalarialPage` con dos secciones (SalarioBase tabla + form, SalarioPlus tabla + form)

## 5. Finanzas — Gestion de facturas

- [x] 5.1 Crear hook `useFacturas(filtros)` con useQuery y `useMutateFactura()` con useMutation
- [x] 5.2 Crear componente `FacturaForm` con React Hook Form + Zod (docente, periodo, detalle, file input PDF)
- [x] 5.3 Crear componente `FacturaFileInput` con validacion de tipo PDF y tamaño maximo 10 MB
- [x] 5.4 Crear `FacturasPage` con tabla de facturas, filtros (docente, estado, fecha), formulario de carga y cambio de estado

## 6. Admin — Tipos y servicios API

- [x] 6.1 Definir tipos en `features/admin/types/estructura.types.ts`: Carrera, Cohorte, Materia, y sus payloads de creacion
- [x] 6.2 Definir tipos en `features/admin/types/usuario.types.ts`: Usuario, CreateUsuarioPayload, UsuarioFilter
- [x] 6.3 Definir tipos en `features/admin/types/auditoria.types.ts`: MetricaPanel, InteraccionDocente, LogEntry
- [x] 6.4 Crear `features/admin/services/estructura.service.ts` con CRUD carreras, cohortes, materias
- [x] 6.5 Crear `features/admin/services/usuario.service.ts` con CRUD usuarios
- [x] 6.6 Crear `features/admin/services/auditoria.service.ts` con getMetricas, getInteracciones, getLogCompleto

## 7. Admin — Estructura academica

- [x] 7.1 Crear hooks `useCarreras()`, `useCohortes()`, `useMaterias()` con TanStack useQuery
- [x] 7.2 Crear formularios Zod: `CarreraForm`, `CohorteForm`, `MateriaForm`
- [x] 7.3 Crear componente `TablaCarreras` con acciones de editar y cambiar estado
- [x] 7.4 Crear componente `TablaCohortes` con filtro por carrera seleccionada
- [x] 7.5 Crear `EstructuraAcademicaPage` con secciones/tabs para Carreras, Cohortes y Materias

## 8. Admin — Usuarios del tenant

- [x] 8.1 Crear hook `useUsuarios(filtros)` con useQuery y `useMutateUsuario()` con useMutation
- [x] 8.2 Crear formulario `UsuarioForm` con React Hook Form + Zod (nombre, email, roles, datos bancarios opcionales)
- [x] 8.3 Crear componente `FiltrosUsuario` (rol, estado, busqueda)
- [x] 8.4 Crear `UsuariosPage` con tabla de usuarios, filtros, formulario de alta/edicion y toggle activacion

## 9. Admin — Panel de auditoria

- [x] 9.1 Crear hook `useMetricasAuditoria(filtros)` y `useLogAuditoria(filtros)` con useQuery
- [x] 9.2 Crear componente `AccionesPorDia` (tabla o grafico simple de volumen diario)
- [x] 9.3 Crear componente `EstadoComunicaciones` (distribucion de estados por docente)
- [x] 9.4 Crear componente `InteraccionesDocente` (tabla de metricas por docente y materia)
- [x] 9.5 Crear componente `UltimasAcciones` (tabla de ultimos N registros del log)
- [x] 9.6 Crear `PanelAuditoriaPage` ensamblando los 4 componentes con filtros globales (fechas, materia, usuario)
- [x] 9.7 Crear `LogAuditoriaPage` con tabla paginada server-side y filtros (accion, usuario, rango de fechas)

## 10. Tests

- [x] 10.1 Test de `LiquidacionesPage`: renderiza KPIs, tabs de segmentacion, filtros de cohorte/mes
- [x] 10.2 Test de cierre de liquidacion: boton requiere permiso, confirmacion previa, llamada API
- [x] 10.3 Test de `GrillaSalarialPage`: renderiza tablas SalarioBase y SalarioPlus, formularios crean registros
- [x] 10.4 Test de `FacturasPage`: formulario de carga con archivo, validacion de tipo/tamano, cambio de estado
- [x] 10.5 Test de `EstructuraAcademicaPage`: renderiza tabs carreras/cohortes/materias, formularios ABM
- [x] 10.6 Test de `UsuariosPage`: listado con filtros, formulario alta/edicion, toggle activacion
- [x] 10.7 Test de `PanelAuditoriaPage`: renderiza widgets de metricas, responde a filtros globales
- [x] 10.8 Test de `LogAuditoriaPage`: tabla paginada, filtros por accion y usuario, estado vacio
