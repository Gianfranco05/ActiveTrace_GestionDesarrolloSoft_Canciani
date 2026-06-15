## 1. Agregar coloquios:reservar al catálogo de permisos

- [x] 1.1 Agregar `"coloquios:reservar": "Reservar turno de coloquio"` al diccionario `PERMISSION_CODES` en `backend/app/core/permissions.py` (SP-04)

## 2. Tests — verificar permisos y asignaciones post-migración

- [x] 2.1 Escribir test: los 6 permisos existen en `permiso` tras migración (SP-01)
- [x] 2.2 Escribir test: asignaciones rol-permiso correctas para los 6 permisos (SP-02)
- [x] 2.3 Escribir test: la migración es idempotente — re-ejecutar no duplica filas (SP-03)

## 3. Migración Alembic 018 — seed de permisos

- [x] 3.1 Crear `backend/alembic/versions/018_seed_permisos_faltantes.py` con `down_revision = '017_mensaje'`
- [x] 3.2 Implementar `upgrade()`: insertar 6 permisos en `permiso` con `WHERE NOT EXISTS` + helper `_assign_permiso_to_roles()`
- [x] 3.3 Implementar `downgrade()`: eliminar asignaciones en `rol_permiso` y luego permisos en `permiso`
- [x] 3.4 Ejecutar migración y verificar que los 6 permisos existen en DB

## 4. Validación final

- [x] 4.1 Ejecutar `pytest -q` desde `backend/` — todos los tests pasan
- [x] 4.2 Ejecutar `alembic downgrade -1 && alembic upgrade head` — ciclo de rollback sin errores
