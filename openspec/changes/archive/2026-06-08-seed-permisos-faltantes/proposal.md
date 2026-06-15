## Why

Seis permisos declarados en `app/core/permissions.py` y usados por endpoints con `require_permission()` nunca se insertan en la tabla `permiso` durante las migraciones Alembic. Una base de datos fresca tras `alembic upgrade head` no tiene estas filas, lo que provoca 403 incluso para usuarios con roles correctos. Además, `coloquios:reservar` se usa en dos endpoints de `coloquios.py` pero ni siquiera está declarado en `permissions.py`.

## What Changes

- **Nueva migración Alembic (018)**: inserta los 6 permisos faltantes en `permiso` con `WHERE NOT EXISTS` (idempotente) y asigna cada uno a los roles correspondientes en `rol_permiso`.
- **Agregar `coloquios:reservar`** al catálogo `PERMISSION_CODES` en `app/core/permissions.py`.
- **Tests**: verificar que los 6 permisos existen en DB y que las asignaciones rol-permiso son correctas tras ejecutar la migración.

## Capabilities

### New Capabilities

- **seed-permisos-faltantes**: La migración 018 garantiza que `padron:cargar`, `analisis:ver`, `coloquios:gestionar`, `fechas:gestionar`, `programas:gestionar` y `coloquios:reservar` existan en `permiso` con sus asignaciones a roles. `coloquios:reservar` se agrega al catálogo de constantes.

### Modified Capabilities

Ninguna. Esto es estrictamente un bug fix de datos: los permisos ya estaban declarados y referenciados en código, solo faltaba la semilla en DB.

## Non-goals

- No se modifican los permisos que usan los routers actuales (ej. `fechas_academicas.py` sigue usando `estructura:gestionar`).
- No se cambia la lógica de `require_permission()` ni el modelo RBAC.
- No se crean nuevos endpoints ni se modifican guards existentes.

## Impact

- **`backend/app/core/permissions.py`**: se agrega `coloquios:reservar` al diccionario `PERMISSION_CODES`.
- **`backend/alembic/versions/018_seed_permisos_faltantes.py`**: nueva migración (schema-only, sin DDL de tablas).
- **`backend/tests/`**: tests de integración que verifican la presencia de los permisos y sus asignaciones post-migración.
- El modelo de dominio documentado en `knowledge-base/03_actores_y_roles.md` ya contempla estas capacidades.
