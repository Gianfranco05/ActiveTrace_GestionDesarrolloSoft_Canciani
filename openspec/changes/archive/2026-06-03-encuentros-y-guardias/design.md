## Context

C-06 (estructura-academica) entregó Carrera, Cohorte y Materia. C-07 (usuarios-y-asignaciones) entregó Asignacion como puente entre usuarios y contexto académico. Ahora C-13 introduce tres nuevas entidades del dominio académico-operativo: encuentros sincrónicos (SlotEncuentro + InstanciaEncuentro) y guardias de atención (Guardia). Las tres son tablas nuevas con migración propia.

El diseño sigue el flujo FL-06 (encuentros recurrentes con grabaciones), las reglas RN-13 (dos modos de creación de slot) y RN-14 (estado de instancia independiente), y las funcionalidades F6.1–F6.6 de la Épica 6.

Governance es **MEDIO**: lógica de dominio sobre modelos nuevos, sin impacto en seguridad ni tenant isolation (se hereda del BaseModelMixin). La auditoría es obligatoria en todas las operaciones de escritura.

## Goals / Non-Goals

**Goals:**
- Modelos SQLAlchemy para SlotEncuentro (E9), InstanciaEncuentro (E10) y Guardia (E11) con BaseModelMixin
- SlotService: crear slot recurrente (RN-13 modo 1) generando N instancias con fechas calculadas; crear slot único (RN-13 modo 2)
- EncuentroService: editar instancia (estado, meet_url, video_url, comentario — F6.3), listar encuentros por materia/cohorte, generar bloque HTML para aula virtual (F6.4)
- GuardiaService: registrar guardia (F6.6), consultar global con filtros, exportar CSV
- Router `/api/encuentros` con guard `encuentros:gestionar`: CRUD de slots, listado de instancias, edición de instancia, generación de HTML
- Router `/api/guardias` con guard `encuentros:gestionar`: registro (TUTOR), consulta/export (COORDINADOR, ADMIN)
- Una migración Alembic (`009`) para las tres tablas con seed de permisos `encuentros:gestionar`
- Schemas Pydantic v2 con `extra='forbid'`, `from_attributes=True`
- Códigos de auditoría: `ENCUENTRO_CREAR`, `ENCUENTRO_EDITAR`, `GUARDIA_REGISTRAR`

**Non-Goals:**
- Frontend UI para encuentros y guardias — C-23 (frontend-coordinacion)
- Integración directa con Moodle para crear eventos de calendario — el bloque HTML se copia manualmente (FL-06 paso 8)
- Sistema de notificaciones a alumnos sobre encuentros — C-12 (comunicaciones)
- Calendarización visual con librería de calendario — frontend-only
- Validación cruzada entre guardias y encuentros (no hay relación directa entre ambos modelos)

## Decisions

### D1 — SlotEncuentro e InstanciaEncuentro como entidades separadas

El slot es la plantilla de recurrencia; la instancia es el encuentro concreto. Esta separación permite:

- Editar cada instancia individualmente sin afectar el slot ni otras instancias (RN-14)
- Crear instancias independientes (sin slot padre) para encuentros únicos ad-hoc
- El slot mantiene `cant_semanas` y `fecha_inicio` para calcular fechas; la instancia tiene `fecha` concreta
- Si un slot se elimina (soft delete), las instancias ya generadas permanecen

**Why not single table with recurrencia flag?**
- RN-14 exige estado independiente por instancia — un flag en tabla única obligaría a duplicar campos de estado
- La generación de instancias desde un slot es una operación de negocio importante que merece su propia entidad
- Separar slot (plan) de instancia (hecho) es un patrón consolidado en scheduling (template vs occurrence)

### D2 — Cálculo de fechas de instancias en el servicio, no en DB

Cuando se crea un slot recurrente, `SlotService` calcula las fechas de cada instancia en Python (fecha_inicio + N semanas × día_semana) y crea todas las instancias en una transacción. No se usa PostgreSQL `generate_series` ni funciones de calendario en DB.

**Why Python over DB functions?**
- El cálculo es trivial (sumar 7 días por semana, ajustar al día_semana correcto) — no justifica complejidad en DB
- Las fechas deben respetar el `dia_semana` del slot (ej: si fecha_inicio es miércoles pero dia_semana es viernes, la primera instancia es el viernes siguiente)
- Facilita testing: las fechas generadas son determinísticas y testeables sin DB
- Mantiene la lógica de negocio en la capa de servicio (Clean Architecture)

### D3 — Guardia independiente, sin FK a InstanciaEncuentro

La Guardia no referencia una InstanciaEncuentro. Son conceptos distintos: un encuentro es una clase sincrónica planificada; una guardia es atención individual o grupal a alumnos. Comparten materia pero no se solapan.

**Why no FK?**
- Una guardia puede ocurrir en cualquier día/horario, independientemente de los encuentros planificados
- El modelo de datos del KB (E11) no define relación con E10
- Agregar una FK opcional crearía ambigüedad semántica sin valor de negocio

### D4 — Bloque HTML generado server-side, no cliente-side

La generación del bloque HTML para el aula virtual (F6.4) ocurre en el backend, devolviendo un string HTML con los encuentros y sus grabaciones. El frontend muestra una preview y permite copiar.

**Why server-side?**
- El formato debe ser consistente independientemente del frontend
- Facilita testing (test de string HTML vs test de renderizado React)
- El HTML generado es simple (tabla/listado de encuentros con enlaces) — no requiere templating engine

### D5 — Permiso `encuentros:gestionar` compartido para encuentros y guardias

Un solo permiso `encuentros:gestionar` cubre ambos módulos (encuentros y guardias). Los roles con acceso son PROFESOR, COORDINADOR, ADMIN. TUTOR puede registrar guardias propias (se usa el mismo permiso pero con scope reducido en el servicio).

**Why single permiso?**
- Guardias y encuentros son facetas del mismo dominio operativo (Épica 6)
- La granularidad real está en el scope del servicio (PROFESOR ve sus slots; TUTOR registra sus guardias; COORDINADOR ve todo)
- Crear `guardias:gestionar` separado agregaría complejidad de seed sin beneficio real de seguridad

## Risks / Trade-offs

- **[Riesgo] Generación masiva de instancias** → Si `cant_semanas` es muy grande (ej: 100), se crean 100 instancias en una sola transacción. **Mitigación**: validar `cant_semanas ≤ 52` (un año) en el schema Pydantic.
- **[Riesgo] Inconsistencia si se modifica el slot después de generar instancias** → El slot y sus instancias son independientes post-creación. Si se cambia el título del slot, las instancias existentes no se actualizan. **Mitigación**: documentar en el contrato de API que la edición del slot no propaga a instancias existentes. Si el usuario quiere reflejar cambios, debe editar cada instancia individualmente (F6.3).
- **[Riesgo] Bloque HTML desactualizado** → El HTML generado es un snapshot del estado actual de las instancias. Si se agregan/quitan instancias, hay que regenerar. **Mitigación**: el endpoint de generación siempre consulta el estado actual; el frontend puede llamarlo cada vez que se necesita el bloque.
- **[Trade-off] CSV para export de guardias vs XLSX** → Se usa CSV (stdlib) como en C-08 equipos-docentes. Si se requiere formato XLSX con estilos, migrar a `openpyxl` en cambio futuro.

## Migration Plan

1. Crear migración `009_slot_encuentro_instancia_guardia.py` con `op.create_table` para las tres tablas
2. Seed de permisos: insertar `encuentros:gestionar` en `permiso` y asociarlo a roles PROFESOR, COORDINADOR, ADMIN en `rol_permiso`
3. Rollback: `downgrade()` hace `op.drop_table` en orden inverso y elimina los registros de `rol_permiso` y `permiso`

## Open Questions

- *(ninguna — el dominio está completamente definido en KB)*
