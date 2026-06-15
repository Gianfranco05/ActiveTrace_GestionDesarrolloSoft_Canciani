## 1. Feature Module Structure

- [x] 1.1 Crear `features/coordinacion/` con sub-directorios: `equipos/`, `avisos/`, `tareas/`, `encuentros/`, `coloquios/`, `monitores/`, `setup/`
- [x] 1.2 Crear `types/` en cada sub-módulo con interfaces TypeScript (Equipo, Aviso, Tarea, Encuentro, Coloquio, etc.)
- [x] 1.3 Crear `services/` en cada sub-módulo con funciones Axios hacia endpoints de C-08, C-13, C-14, C-15, C-16, C-17
- [x] 1.4 Crear `hooks/` en cada sub-módulo con custom hooks de TanStack Query (useQuery, useMutation, useInfiniteQuery)

## 2. Dashboard de Coordinacion

- [x] 2.1 Crear `CoordinacionDashboardPage` en `/coordinacion` como landing con cards navegables y KPIs
- [x] 2.2 Agregar ruta `/coordinacion` en App.tsx bajo ProtectedRoute + AppLayout + RequirePermission
- [x] 2.3 Actualizar Sidebar con seccion COORDINACION y enlaces a cada sub-modulo

## 3. Equipos Docentes

- [x] 3.1 Crear `EquiposPage` con tabla de mis equipos, filtros (estado, materia, rol, carrera, cohorte) y estado vacio
- [x] 3.2 Crear `AsignacionesPage` con tabla paginada de asignaciones del tenant y filtros
- [x] 3.3 Crear `AsignacionMasivaPage` con wizard multi-step: seleccionar materia/carrera/cohorte, seleccionar docentes, definir rol, vigencia
- [x] 3.4 Crear `ClonarEquipoPage` con formulario de dos pasos: origen (materia x carrera x cohorte) → destino (cohorte)
- [x] 3.5 Crear accion de modificar vigencia general con modal de fechas desde/hasta
- [x] 3.6 Crear accion de exportar equipo con descarga de archivo
- [x] 3.7 Agregar rutas: `/coordinacion/equipos`, `/coordinacion/equipos/asignaciones`, `/coordinacion/equipos/asignacion-masiva`, `/coordinacion/equipos/clonar`

## 4. Avisos

- [x] 4.1 Crear `AvisosPage` con tabla paginada, filtros (estado, alcance, materia, cohorte, busqueda) y badges de severidad/ack
- [x] 4.2 Crear `AvisoFormPage` con formulario completo: titulo, cuerpo (rich text), alcance, roles, severidad, visibilidad, prioridad, require_ack
- [x] 4.3 Crear accion de editar aviso (mismo formulario, precargado)
- [x] 4.4 Crear accion de eliminar aviso con dialogo de confirmacion
- [x] 4.5 Crear vista de acuses de recibo con contador y lista de destinatarios
- [x] 4.6 Agregar rutas: `/coordinacion/avisos`, `/coordinacion/avisos/nuevo`, `/coordinacion/avisos/:id/editar`

## 5. Tareas Internas

- [x] 5.1 Crear `TareasPage` con tabla paginada, filtros (docente asignado, asignador, materia, estado, busqueda) y badges de color por estado
- [x] 5.2 Crear `TareaFormPage` con formulario: titulo, descripcion, materia, docente asignado, criterio de cierre
- [x] 5.3 Crear acciones de cambio de estado con dropdown/botones segun workflow (Pendiente→En progreso→Resuelta, Cancelar)
- [x] 5.4 Crear `TareaDetallePage` con detalle de tarea, historial de cambios y seccion de comentarios
- [x] 5.5 Crear accion de agregar comentario con fecha/hora y autor
- [x] 5.6 Agregar rutas: `/coordinacion/tareas`, `/coordinacion/tareas/nueva`, `/coordinacion/tareas/:id`

## 6. Encuentros

- [x] 6.1 Crear `EncuentrosPage` con tabla de encuentros del tenant, filtros (materia, docente, estado, rango fechas)
- [x] 6.2 Crear formulario de encuentro recurrente: materia, dia, horario, inicio, semanas, titulo, enlace
- [x] 6.3 Crear formulario de encuentro unico: fecha, horario, titulo, enlace
- [x] 6.4 Crear modal/accion de editar instancia: estado, enlace, grabacion, comentario
- [x] 6.5 Crear accion de generar contenido para aula virtual con boton copiar
- [x] 6.6 Agregar rutas: `/coordinacion/encuentros`

## 7. Coloquios

- [x] 7.1 Crear `ColoquiosPage` con panel de metricas (cards) y tabla de convocatorias con acciones
- [x] 7.2 Crear `ConvocatoriaFormPage` con formulario: materia, instancia, dias con cupos
- [x] 7.3 Crear accion de importar alumnos a convocatoria con upload de archivo
- [x] 7.4 Crear `AgendaReservasPage` con tabla de reservas activas y filtros (materia, convocatoria, dia)
- [x] 7.5 Crear `RegistroAcademicoPage` con tabla de resultados y notas finales
- [x] 7.6 Agregar rutas: `/coordinacion/coloquios`, `/coordinacion/coloquios/nueva`, `/coordinacion/coloquios/:id/reservas`, `/coordinacion/coloquios/registro`

## 8. Monitores

- [x] 8.1 Crear `MonitoresPage` con tabs: General (F2.7) y Seguimiento por docente (F2.9)
- [x] 8.2 Implementar Monitor General: tabla paginada con filtros (materia, regional, comision, busqueda, estado, criterio) y useInfiniteQuery
- [x] 8.3 Implementar accion de exportar datos del monitor
- [x] 8.4 Implementar accion de limpiar filtros
- [x] 8.5 Implementar Monitor Seguimiento por Docente: tabla con filtros adicionales (rango fechas, minimo actividades)
- [x] 8.6 Agregar rutas: `/coordinacion/monitores`

## 9. Setup de Cuatrimestre

- [x] 9.1 Crear `SetupCuatrimestrePage` como wizard con 7 pasos y barra de progreso
- [x] 9.2 Implementar Paso 1: Crear cohorte (formulario con validacion de duplicados)
- [x] 9.3 Implementar Paso 2: Clonar equipo docente (seleccion origen → destino)
- [x] 9.4 Implementar Paso 3: Ajustar asignaciones (asignacion masiva embebida)
- [x] 9.5 Implementar Paso 4: Ajustar vigencias (formulario de fechas en lote)
- [x] 9.6 Implementar Paso 5: Cargar programas (upload de archivo por materia)
- [x] 9.7 Implementar Paso 6: Cargar fechas de evaluaciones (tabla con ABM de fechas)
- [x] 9.8 Implementar Paso 7: Publicar aviso de bienvenida (formulario de aviso pre-configurado)
- [x] 9.9 Agregar ruta: `/coordinacion/setup`

## 10. Tests

- [x] 10.1 Tests unitarios para servicios API de equipos (asignacion masiva, clonar, exportar)
- [x] 10.2 Tests unitarios para servicios API de avisos (CRUD, acuses)
- [x] 10.3 Tests unitarios para servicios API de tareas (crear, cambiar estado, comentar)
- [x] 10.4 Tests de integracion para formularios multi-step (asignacion masiva, clonar equipos, setup)
- [x] 10.5 Tests de integracion para monitores con filtros y paginacion
- [x] 10.6 Tests de integracion para workflow de tareas (transiciones de estado)
