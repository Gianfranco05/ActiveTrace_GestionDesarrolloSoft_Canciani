## Context

C-06 (estructura-academica) entregó Carrera, Cohorte y Materia. C-07 (usuarios-y-asignaciones) entregó Usuario y Asignacion como puente de autorización con jerarquía docente (responsable_id). Ahora C-16 introduce dos nuevas entidades del dominio operativo: Tarea y ComentarioTarea, que materializan el workflow de coordinación interna descrito en FL-05.

El diseño sigue el flujo FL-05 (workflow de tareas coordinación ↔ docente), las funcionalidades F8.1–F8.3 de la Épica 8, y el modelo de datos E12 del KB. Es un módulo de alto uso: la plataforma gestiona varios cientos de tareas en simultáneo durante el período activo.

Governance es **MEDIO**: lógica de dominio sobre modelos nuevos, sin impacto en seguridad ni tenant isolation (se hereda del BaseModelMixin). La auditoría es obligatoria en todas las operaciones de escritura.

## Goals / Non-Goals

**Goals:**
- Modelos SQLAlchemy para Tarea (E12) y ComentarioTarea (E12) con BaseModelMixin
- TareaService: creación de tareas, delegación/reasignación con trazabilidad, máquina de estados, comentarios en hilo, listados con scope por rol y filtros compuestos
- Router `/api/tareas` con guard `tareas:gestionar`: CRUD de tareas, cambio de estado, comentarios
- Una migración Alembic para las tablas `tarea` y `comentario_tarea` con seed de permisos `tareas:gestionar`
- Schemas Pydantic v2 con `extra='forbid'`, `from_attributes=True`
- Códigos de auditoría: `TAREA_CREAR`, `TAREA_ASIGNAR`, `TAREA_ESTADO`, `COMENTARIO_TAREA`
- Scope por rol: PROFESOR ve y gestiona solo sus tareas asignadas; COORDINADOR/ADMIN tienen visión y control global

**Non-Goals:**
- Frontend UI para tareas — C-23 (frontend-coordinacion)
- Notificaciones push/email al docente cuando se le asigna una tarea — C-12 (comunicaciones)
- Vinculación automática de tareas a entidades del dominio (contexto_id) — es una referencia opcional manual
- Workflow de aprobación multi-step (tipo PR review) — el flujo es lineal: Pendiente → En progreso → Resuelta / Cancelada
- SLA o deadlines en tareas — no definidos en KB; podrían agregarse en change futuro

## Decisions

### D1 — Tarea y ComentarioTarea como entidades separadas

La Tarea es la unidad de trabajo; el ComentarioTarea es el registro de comunicación en el hilo. Esta separación sigue el patrón 1:N definido en el KB y permite:

- Múltiples comentarios por tarea sin límite, cada uno con su autor y timestamp
- Los comentarios son append-only: no se editan ni se eliminan (integridad del historial de conversación)
- Al resolver o cancelar una tarea, los comentarios permanecen como registro histórico
- Soft-delete de tarea no elimina comentarios (se conservan para auditoría)

**Why not embebbed JSON array?**
- Perderías capacidad de filtrar por autor, ordenar por fecha, o paginar comentarios
- Los comentarios pueden ser numerosos en tareas activas — un JSON array crece sin control
- Append-only en JSON requiere leer-modificar-escribir todo el documento, rompiendo atomicidad

### D2 — Máquina de estados explícita en el servicio

Los estados y transiciones válidas se validan en TareaService, no en el modelo ni en el schema:

```
Pendiente ──→ En progreso
Pendiente ──→ Cancelada
En progreso ──→ Resuelta
En progreso ──→ Cancelada
Resuelta ──→ En progreso   (reapertura por coordinador — FL-05 paso 7)
```

Transiciones inválidas (ej: Resuelta → Pendiente, Cancelada → cualquier cosa) retornan 422 con mensaje descriptivo.

**Why service-level over DB constraint?**
- Las reglas de transición son lógica de negocio, no de integridad de datos
- Mensajes de error descriptivos en la capa de servicio (vs errores genéricos de CHECK constraint)
- Testeable sin DB: las transiciones se prueban con mocks del repository
- Si en el futuro se agrega un estado nuevo (ej: "Bloqueada"), solo cambia el servicio

### D3 — Delegación = cambio de asignado_a con trazabilidad

Delegar una tarea significa cambiar el campo `asignado_a` a otro usuario. El campo `asignado_por` registra quién hizo la última asignación. La auditoría captura el cambio con `TAREA_ASIGNAR` incluyendo el asignado anterior y el nuevo en el detalle JSON.

**Why no tabla de historial de delegaciones?**
- El audit log ya registra cada delegación con actor, timestamp y detalle
- Una tabla intermedia agregaría complejidad sin valor adicional (el historial se reconstruye del audit log)
- El campo `asignado_por` en Tarea da la trazabilidad inmediata de "quién delegó esto"

### D4 — contexto_id como UUID genérico sin FK

El campo `contexto_id` es un UUID opcional que referencia a cualquier entidad del dominio (una Materia, una Cohorte, una Guardia, etc.). No tiene foreign key constraint porque puede apuntar a distintas tablas.

**Why no polymorphic FK?**
- El KB define `contexto_id` como "referencia opcional a otra entidad del dominio" — no específica una tabla concreta
- Una FK polimórfica (entity_type + entity_id) es compleja de modelar en SQLAlchemy y aporta poco valor
- El contexto es informativo (ayuda a filtrar/agrupar tareas), no es una restricción de integridad referencial
- Si el futuro requiere navegación tipada, se puede agregar `contexto_tipo` como enum sin romper backward compatibility

### D5 — Permiso único `tareas:gestionar` con scope por rol

Un solo permiso `tareas:gestionar` cubre todo el módulo. Los roles con acceso son PROFESOR, COORDINADOR, ADMIN. El scope se resuelve en el servicio:

- **PROFESOR**: GET lista solo tareas donde `asignado_a = actor_id`. Puede cambiar estado de sus tareas y agregar comentarios. No puede crear tareas ni delegar a otros.
- **TUTOR**: Incluido según matriz de capacidades KB (F8.1 "Vista de mis tareas" lista TUTOR, PROFESOR, COORDINADOR; pero "Gestionar tareas internas" en la matriz solo tiene PROFESOR, COORDINADOR, ADMIN). El permiso `tareas:gestionar` se otorga a TUTOR, PROFESOR, COORDINADOR, ADMIN — TUTOR puede ver sus tareas pero no crearlas.
- **COORDINADOR/ADMIN**: GET lista todas las tareas del tenant. Pueden crear, delegar, cambiar estado de cualquier tarea, y agregar comentarios.

**Why no `tareas:admin` separado?**
- La granularidad real está en el scope del servicio, no en el permiso
- Los roles ya diferencian capacidades: PROFESOR no tiene "Gestionar equipos docentes" ni "Gestionar estructura académica"
- Crear un permiso adicional solo para distinguir "crear tarea" de "ver mis tareas" fragmentaría el seed sin beneficio de seguridad

### D6 — Comentarios son append-only

Los comentarios no se editan ni se eliminan. El endpoint solo soporta POST (crear) y GET (listar). No hay PATCH ni DELETE para comentarios.

**Why?**
- El historial de conversación en una tarea es un registro de auditoría en sí mismo
- Editar o borrar comentarios rompería la trazabilidad del workflow
- Patrón consistente con el audit log (append-only, inmutable)

### D7 — Filtros compuestos en listado de tareas

El endpoint GET `/api/tareas` soporta filtros por: `asignado_a`, `asignado_por`, `materia_id`, `estado`, `contexto_id` y búsqueda libre (`q` sobre descripción). Los filtros se combinan con AND. El scope de tenant y rol se aplica siempre (no depende de los filtros del usuario).

**Why query params over POST body?**
- GET con query params es cacheable, bookmarkeable y RESTful
- Los filtros son todos opcionales y atómicos — no requieren estructura anidada
- Sigue el patrón establecido en C-08 (equipos-docentes) y C-13 (encuentros-y-guardias)

## Risks / Trade-offs

- **[Riesgo] Alta concurrencia en tareas** → Cientos de tareas simultáneas con múltiples usuarios comentando y cambiando estados. **Mitigación**: las operaciones son atómicas a nivel de fila (UPDATE sobre una tarea). No hay locks de tabla. El listado usa paginación (offset/limit) para evitar cargas completas.
- **[Riesgo] Race condition en cambio de estado** → Dos usuarios (el PROFESOR y el COORDINADOR) podrían intentar cambiar el estado simultáneamente. **Mitigación**: usar `SELECT ... FOR UPDATE` en el repository al obtener la tarea para escritura, o optimistic locking con un campo `version` (evaluar en implementación según perfil de uso real).
- **[Riesgo] contexto_id huérfano** → Si la entidad referenciada se elimina (soft delete), el contexto_id queda apuntando a un registro inactivo. **Mitigación**: es aceptable — el contexto es informativo. El frontend puede mostrar "referencia no disponible" si la entidad no se encuentra.
- **[Trade-off] TUTOR puede ver tareas pero no crearlas** → Según la matriz de capacidades, TUTOR tiene "Gestionar tareas internas" solo con scope propio. La KB lista F8.1 para TUTOR, PROFESOR, COORDINADOR. Se otorga el permiso a TUTOR con la restricción de solo lectura + comentarios en el servicio. Si en el futuro TUTOR necesita crear tareas, se agrega sin migración de permisos.
## Migration Plan

1. Crear migración con `op.create_table` para `tarea` y `comentario_tarea`
2. Seed de permisos: insertar `tareas:gestionar` en `permiso` y asociarlo a roles TUTOR, PROFESOR, COORDINADOR, ADMIN en `rol_permiso`
3. Rollback: `downgrade()` hace `op.drop_table` en orden inverso y elimina los registros de `rol_permiso` y `permiso`

## Open Questions

- *(ninguna — el dominio está completamente definido en KB)*
