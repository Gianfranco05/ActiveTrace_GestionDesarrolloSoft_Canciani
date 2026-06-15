## Why

Los roles COORDINADOR y ADMIN necesitan una interfaz para las capacidades de gestión académica que el backend ya expone: equipos docentes (C-08), avisos (C-15), tareas internas (C-16), encuentros (C-13), coloquios/evaluaciones (C-14) y monitores transversales. El frontend actual solo tiene shell, login y dashboard; sin estas pantallas, coordinación no puede operar el sistema.

## What Changes

- Nuevo feature module `features/coordinacion/` con sub-secciones: equipos, avisos, tareas, encuentros, coloquios, monitores
- Páginas con guards de permiso: EquiposPage, AsignacionMasivaPage, AvisosPage, TareasPage, EncuentrosPage, ColoquiosPage, MonitoresPage, SetupCuatrimestrePage
- Dashboard de coordinación con vista resumen de monitores
- Formularios multi-step para operaciones masivas (asignación, clonar equipos)
- Workflow visual de tareas (Pendiente → En progreso → Resuelta/Cancelada)
- Vista de monitores: general (F2.7) y seguimiento por docente (F2.9)
- Integración con servicios API de los backends C-08, C-13, C-14, C-15, C-16, C-17
- Nuevas rutas en App.tsx bajo ProtectedRoute + RequirePermission

## Capabilities

### New Capabilities
- `coordinacion-equipos`: Gestión de equipos docentes (mis-equipos, asignación masiva, clonar, vigencia, export)
- `coordinacion-avisos`: ABM de avisos del sistema con scope, severidad, vigencia y acknowledgment
- `coordinacion-tareas`: Workflow de tareas internas (Pendiente → En progreso → Resuelta/Cancelada) con filtros y comentarios
- `coordinacion-encuentros`: Vista admin de encuentros, creación recurrente/única, edición de instancias
- `coordinacion-coloquios`: Gestión de convocatorias, importación de alumnos, métricas y reservas
- `coordinacion-monitores`: Monitores transversales — general (F2.7) y seguimiento por docente (F2.9)
- `coordinacion-setup`: Setup de inicio de cuatrimestre (FL-03): cohorte, clonar equipo, programas, fechas, aviso

### Modified Capabilities
<!-- No existing capabilities are modified at spec level. -->

## Impact

- **Nuevo feature**: `frontend/src/features/coordinacion/` con sub-módulos
- **Rutas**: ~8 nuevas rutas en `App.tsx` bajo `ProtectedRoute > AppLayout > RequirePermission`
- **Sidebar**: nuevos ítems de navegación para COORDINADOR/ADMIN en `Sidebar.tsx`
- **Servicios API**: nuevos archivos de servicio consumiendo endpoints de C-08 (equipos), C-13 (encuentros), C-14 (coloquios), C-15 (avisos), C-16 (tareas), C-17 (programas/fechas)
- **Tipos**: interfaces TypeScript para cada dominio (Equipo, Aviso, Tarea, Encuentro, Coloquio, etc.)
- **Testing**: tests unitarios (hooks, servicios) y de integración (páginas con TanStack Query + React Hook Form)
