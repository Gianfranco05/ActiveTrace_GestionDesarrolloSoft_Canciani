## Why

C-07 entregó el puente de autorización (Asignacion) que permite modelar equipos docentes con jerarquía. La coordinación académica necesita ahora un mecanismo de workflow para asignar tareas de seguimiento entre docentes, hacerles tracking y resolverlas con trazabilidad completa. Sin C-16 no existe gestión de tareas internas en el sistema — el FL-05 (workflow de tareas coordinación ↔ docente) queda sin soporte. Es un módulo de alto uso: la plataforma gestiona varios cientos de tareas en simultáneo durante el período activo.

## What Changes

- **Modelo Tarea (E12)** — tarea de seguimiento asignada entre roles del equipo docente o de coordinación. Campos: materia_id (nullable, si es institucional), asignado_a, asignado_por, estado (Pendiente, En progreso, Resuelta, Cancelada), descripcion, contexto_id (referencia opcional a otra entidad del dominio).
- **Modelo ComentarioTarea (E12)** — comentario en el hilo de una tarea. Campos: tarea_id, autor_id, texto, creado_at. Relación 1:N desde Tarea.
- **TareaService** — servicio de dominio que orquesta: creación de tarea (COORDINADOR/ADMIN), delegación/asignación, transiciones de estado con validación, agregado de comentarios, listado con filtros y scope por rol.
- **`/api/tareas/*` router** — endpoints bajo prefix `/api/tareas` con guard `tareas:gestionar`. PROFESOR ve y gestiona sus tareas asignadas; COORDINADOR/ADMIN tiene visión global con filtros por docente, materia, estado.
- **Migración Alembic** — nueva migración para las tablas `tarea` y `comentario_tarea` con sus constraints, FK hacia usuario (asignado_a, asignado_por), materia, y tenant_id.
- **Seed de permisos** — `tareas:gestionar` para roles PROFESOR, COORDINADOR, ADMIN.
- **Códigos de auditoría** — `TAREA_CREAR`, `TAREA_ASIGNAR`, `TAREA_ESTADO`, `COMENTARIO_TAREA`.

## Capabilities

### New Capabilities
- `tareas`: Gestión completa de tareas internas — creación y asignación (F8.2), vista de mis tareas por docente (F8.1), administración global con filtros por docente, materia y estado (F8.3), workflow de estados (Pendiente → En progreso → Resuelta / Cancelada) con comentarios en hilo y trazabilidad de asignador y asignado.

### Modified Capabilities
- *(ninguna — C-16 introduce modelos y endpoints nuevos, no modifica specs existentes)*

## Impact

- **New models**: `backend/app/models/tarea.py`, `comentario_tarea.py` — dos modelos con BaseModelMixin
- **New migration**: `backend/alembic/versions/<rev>_tarea_comentario_tarea.py` — una migración para ambas tablas
- **New repository**: `backend/app/repositories/tarea_repository.py` — operaciones CRUD con filtros compuestos por asignado_a, asignado_por, materia, estado; `comentario_tarea_repository.py`
- **New service**: `backend/app/services/tarea_service.py` — creación, delegación, transiciones de estado, comentarios, listados con scope
- **New router**: `backend/app/api/v1/routers/tareas.py` (prefix `/api/tareas`)
- **New schemas**: `backend/app/schemas/tareas.py` — request/response DTOs con `extra='forbid'`
- **Modified files**: `backend/app/main.py` — registrar router de tareas
- **Modified seed**: seed de permisos para `tareas:gestionar`
- **Modified audit codes**: agregar `TAREA_CREAR`, `TAREA_ASIGNAR`, `TAREA_ESTADO`, `COMENTARIO_TAREA`
- **Dependencies**: `C-07` (Usuario model, Asignacion model/repository)
