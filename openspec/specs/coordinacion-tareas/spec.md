## ADDED Requirements

### Requirement: Listado de tareas con filtros
El sistema SHALL mostrar al COORDINADOR/ADMIN la vista global de tareas del tenant con filtros por docente asignado, docente asignador, materia, estado y búsqueda libre.

#### Scenario: COORDINADOR ve todas las tareas del tenant
- **WHEN** el COORDINADOR accede a `/coordinacion/tareas`
- **THEN** el sistema carga la tabla paginada con todas las tareas, mostrando título, estado, docente asignado, materia, fecha de creación
- **AND** cada tarea muestra un badge de color según su estado (Pendiente=gris, En progreso=amarillo, Resuelta=verde, Cancelada=rojo)

#### Scenario: Filtrado de tareas por estado y docente
- **WHEN** el usuario filtra por estado "Pendiente" y un docente específico
- **THEN** el sistema muestra solo las tareas pendientes asignadas a ese docente

### Requirement: Crear tarea
El sistema SHALL permitir al COORDINADOR crear una tarea definiendo: título, descripción, materia asociada, docente asignado y criterio de cierre.

#### Scenario: Creación de tarea exitosa
- **WHEN** el COORDINADOR completa el formulario con título, materia, docente asignado y crea la tarea
- **THEN** el sistema crea la tarea en estado "Pendiente" y redirige al listado con mensaje de éxito

#### Scenario: Validación de campos obligatorios
- **WHEN** el COORDINADOR intenta crear una tarea sin título o sin docente asignado
- **THEN** el sistema muestra errores de validación y no crea la tarea

### Requirement: Cambiar estado de tarea
El sistema SHALL permitir al COORDINADOR cambiar el estado de una tarea siguiendo el workflow: Pendiente → En progreso → Resuelta. El estado Cancelada puede aplicarse desde cualquier estado activo.

#### Scenario: Avance de tarea a En progreso
- **WHEN** el COORDINADOR cambia una tarea de Pendiente a En progreso
- **THEN** el sistema actualiza el estado y la tarea aparece con badge amarillo

#### Scenario: Resolución de tarea
- **WHEN** el COORDINADOR cambia una tarea de En progreso a Resuelta
- **THEN** el sistema actualiza el estado y la tarea aparece con badge verde

#### Scenario: Cancelación de tarea
- **WHEN** el COORDINADOR cancela una tarea en cualquier estado activo
- **THEN** el sistema actualiza el estado a Cancelada y la tarea aparece con badge rojo

### Requirement: Agregar comentario a tarea
El sistema SHALL permitir al COORDINADOR agregar comentarios a una tarea como parte del workflow asincrónico.

#### Scenario: Comentario en tarea
- **WHEN** el COORDINADOR abre el detalle de una tarea y agrega un comentario
- **THEN** el sistema guarda el comentario asociado al usuario y muestra la fecha/hora

### Requirement: Vista de mis tareas (docente)
El sistema SHALL permitir al usuario ver las tareas que le fueron asignadas, filtradas por contexto académico, con capacidad de cambiar estado y agregar comentarios.

#### Scenario: Docente ve sus tareas asignadas
- **WHEN** un docente accede a la vista de mis tareas
- **THEN** el sistema muestra solo las tareas donde el docente es el asignado
- **AND** el docente puede cambiar el estado de sus tareas y agregar comentarios
