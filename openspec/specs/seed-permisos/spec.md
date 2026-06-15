# seed-permisos Specification

## Purpose
TBD - created by archiving change seed-permisos-faltantes. Update Purpose after archive.
## Requirements
### Requirement: Migración 018 seedea 6 permisos faltantes
La migración 018 **SHALL** insertar 6 permisos declarados en `permissions.py` pero no presentes en `permiso`: `padron:cargar`, `analisis:ver`, `coloquios:gestionar`, `fechas:gestionar`, `programas:gestionar`, `coloquios:reservar`. Cada permiso **SHALL** insertarse con `WHERE NOT EXISTS` para garantizar idempotencia, y **SHALL** asignarse los `rol_permiso` correspondientes.

#### Scenario: Los 6 permisos existen en permiso tras migración
- **GIVEN** una base de datos con `alembic upgrade head` ejecutado
- **WHEN** se consulta la tabla `permiso` por los códigos `padron:cargar`, `analisis:ver`, `coloquios:gestionar`, `fechas:gestionar`, `programas:gestionar`, `coloquios:reservar`
- **THEN** existen exactamente una fila por cada código
- **AND** cada fila tiene `descripcion` no nula

#### Scenario: Asignaciones rol-permiso correctas
- **GIVEN** la migración 018 ejecutada
- **WHEN** se consulta `rol_permiso` uniendo `rol` y `permiso`
- **THEN** `padron:cargar` está asignado a PROFESOR, COORDINADOR, ADMIN
- **AND** `analisis:ver` está asignado a TUTOR, PROFESOR, COORDINADOR, ADMIN
- **AND** `coloquios:gestionar` está asignado a COORDINADOR, ADMIN
- **AND** `fechas:gestionar` está asignado a COORDINADOR, ADMIN
- **AND** `programas:gestionar` está asignado a COORDINADOR, ADMIN
- **AND** `coloquios:reservar` está asignado a ALUMNO

#### Scenario: La migración es idempotente
- **GIVEN** la migración 018 ya ejecutada
- **WHEN** se vuelve a ejecutar (`alembic upgrade head`)
- **THEN** no se insertan filas duplicadas en `permiso` ni en `rol_permiso`

### Requirement: coloquios:reservar en PERMISSION_CODES
`coloquios:reservar` **SHALL** agregarse al diccionario `PERMISSION_CODES` en `app/core/permissions.py` con la descripción "Reservar turno de coloquio".

#### Scenario: coloquios:reservar existe en PERMISSION_CODES
- **GIVEN** el módulo `app.core.permissions` cargado
- **WHEN** se accede a `PERMISSION_CODES["coloquios:reservar"]`
- **THEN** retorna una descripción no vacía

