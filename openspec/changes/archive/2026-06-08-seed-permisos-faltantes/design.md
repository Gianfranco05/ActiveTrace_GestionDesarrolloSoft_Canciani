## Context

El sistema usa RBAC fino con permisos `modulo:accion`. El catálogo vive en `PERMISSION_CODES` (`app/core/permissions.py`) y cada endpoint declara `require_permission("codigo")`. La migración `003_rbac.py` crea las tablas (`permiso`, `rol`, `rol_permiso`) y siembra los permisos iniciales. Migraciones posteriores como `008` y `017` agregan permisos nuevos siguiendo el mismo patrón idempotente (`WHERE NOT EXISTS`).

Seis permisos declarados en `PERMISSION_CODES` nunca fueron incluidos en ninguna migración. `coloquios:reservar` ni siquiera está declarado en el catálogo, aunque se usa en dos endpoints. Esto rompe la regla del archivo: _"Every permission used by `require_permission()` and seeded into the DB MUST be declared here first."_

## Goals / Non-Goals

**Goals:**
- Insertar los 6 permisos faltantes en `permiso` via migración idempotente.
- Asignar cada permiso a los roles correctos en `rol_permiso`.
- Declarar `coloquios:reservar` en `PERMISSION_CODES`.
- Verificar con tests que los permisos y asignaciones existen post-migración.

**Non-Goals:**
- No se cambia qué permisos usan los routers. Los endpoints de `fechas_academicas.py` y `programas.py` siguen usando `estructura:gestionar`.
- No se modifica la lógica de autorización ni el modelo de datos.
- No se migran datos existentes (bases ya pobladas no se ven afectadas por `WHERE NOT EXISTS`).

## Decisions

### 1. Migración standalone (018), no modificar 003

**Decisión**: Crear `018_seed_permisos_faltantes.py` en vez de editar `003_rbac.py`.

**Razón**: Las migraciones ya ejecutadas son inmutables. Modificar `003` no tiene efecto en bases ya migradas. Una migración nueva garantiza que el seed corra en el momento correcto de la cadena (post-017) para cualquier base.

**Alternativa considerada**: Editar `003_rbac.py` y generar una nueva migración vacía. Descartada porque rompe el historial de migraciones y no aplica a entornos existentes.

### 2. Seed idempotente con `WHERE NOT EXISTS`

**Decisión**: Usar el patrón establecido en `008` y `017`: `INSERT ... WHERE NOT EXISTS (SELECT 1 FROM permiso WHERE codigo = :codigo)`.

**Razón**: La migración es segura para re-ejecución y no falla si algún permiso ya existe (ej. seeds manuales o migraciones parciales).

### 3. Helper `_assign_permiso_to_roles()` extraído

**Decisión**: Seguir el patrón de `008_calificaciones_y_umbral.py` con una función helper que itera roles.

**Razón**: Consistencia con el codebase. Es el mismo helper usado en migraciones previas que agregan permisos.

### 4. `coloquios:reservar` → ALUMNO solamente

**Decisión**: Asignar `coloquios:reservar` únicamente al rol ALUMNO.

**Razón**: El endpoint `POST /{evaluacion_id}/reservas` es para que un alumno reserve su turno de coloquio. Es una acción del estudiante, no administrativa. Consistente con `evaluacion:reservar` que también es solo ALUMNO.

### 5. Role assignments consistentes con el dominio

| Permiso | Roles | Justificación |
|---------|-------|---------------|
| `padron:cargar` | PROFESOR, COORDINADOR, ADMIN | Mismo patrón que `calificaciones:cargar` |
| `analisis:ver` | TUTOR, PROFESOR, COORDINADOR, ADMIN | Mismo patrón que `atrasados:ver` |
| `coloquios:gestionar` | COORDINADOR, ADMIN | Gestión administrativa de convocatorias |
| `fechas:gestionar` | COORDINADOR, ADMIN | Mismo patrón que `estructura:gestionar` |
| `programas:gestionar` | COORDINADOR, ADMIN | Mismo patrón que `estructura:gestionar` |
| `coloquios:reservar` | ALUMNO | Acción del estudiante, como `evaluacion:reservar` |

## Risks / Trade-offs

- **[Bajo] Permisos declarados pero no usados por routers**: `analisis:ver`, `fechas:gestionar` y `programas:gestionar` están en el catálogo pero ningún endpoint los requiere actualmente. → Mitigación: seedearlos igual prepara el terreno para granularizar permisos en el futuro (separar `estructura:gestionar` en permisos específicos). No causan daño — son entradas inertes en la DB.
- **[Bajo] downgrade de la migración**: El downgrade debe eliminar los permisos y asignaciones insertados. → Mitigación: incluir `DELETE` statements en `downgrade()` con el mismo patrón que `017_mensaje.py`.

## Migration Plan

1. Ejecutar `alembic upgrade head` → la migración 018 inserta los 6 permisos y sus asignaciones.
2. Rollback: `alembic downgrade -1` → elimina las filas insertadas por 018.
3. No requiere migración de datos ni downtime.

## Open Questions

Ninguna. El scope está completamente definido.
