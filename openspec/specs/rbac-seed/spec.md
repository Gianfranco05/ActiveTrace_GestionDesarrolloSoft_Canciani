# rbac-seed Specification

## Purpose
TBD - created by archiving change rbac-permisos-finos. Update Purpose after archive.
## Requirements
### Requirement: Migration 003 creates RBAC tables
The system SHALL provide Alembic migration 003 that creates the following tables: rol, permiso, rol_permiso. The migration SHALL be additive (no destructive changes to previous migrations).

#### Scenario: Migration creates rol table
- **WHEN** running alembic upgrade head to include migration 003
- **THEN** the rol table SHALL exist with columns: id (UUID PK), tenant_id (UUID FK), nombre (VARCHAR 50), descripcion (TEXT nullable), created_at, updated_at, deleted_at

#### Scenario: Migration creates permiso table
- **WHEN** running alembic upgrade head to include migration 003
- **THEN** the permiso table SHALL exist with columns: id (UUID PK), codigo (VARCHAR 80 UNIQUE), descripcion (TEXT nullable), created_at, updated_at, deleted_at

#### Scenario: Migration creates rol_permiso table
- **WHEN** running alembic upgrade head to include migration 003
- **THEN** the rol_permiso table SHALL exist with columns: id (UUID PK), rol_id (UUID FK), permiso_id (UUID FK), created_at with UNIQUE(rol_id, permiso_id)

#### Scenario: Migration rollback removes tables
- **WHEN** running alembic downgrade -1 from migration 003
- **THEN** the rol, permiso, and rol_permiso tables SHALL be removed

### Requirement: Seed all 7 roles
The system SHALL seed the following 7 roles as part of migration 003 (using INSERT ON CONFLICT DO NOTHING for idempotency): ALUMNO, TUTOR, PROFESOR, COORDINADOR, NEXO, ADMIN, FINANZAS. Each role SHALL have a description matching its domain function.

#### Scenario: All 7 roles exist after migration
- **WHEN** migration 003 has been applied
- **THEN** the rol table SHALL contain exactly 7 rows with nombres: ALUMNO, TUTOR, PROFESOR, COORDINADOR, NEXO, ADMIN, FINANZAS

#### Scenario: Migration is idempotent for roles
- **WHEN** running migration 003 twice
- **THEN** the rol table SHALL still contain exactly 7 rows (no duplicates)

### Requirement: Seed all permissions from the KB matrix
The system SHALL seed all permissions from the KB §3.3 matrix as part of migration 003. Each permission SHALL have codigo in format `modulo:accion` and a user-friendly description.

#### Scenario: All 21 permissions exist after migration
- **WHEN** migration 003 has been applied
- **THEN** the permiso table SHALL contain 21 rows with the following codigos:
  - estado_academico:ver
  - evaluacion:reservar
  - aviso:confirmar
  - calificaciones:importar
  - atrasados:ver
  - entregas:detectar_sin_corregir
  - comunicacion:enviar
  - comunicacion:aprobar
  - encuentros:gestionar
  - guardias:registrar
  - tareas:gestionar
  - avisos:publicar
  - equipos:asignar
  - estructura:gestionar
  - usuarios:gestionar
  - auditoria:ver
  - liquidaciones:operar_grilla
  - liquidaciones:calcular_cerrar
  - facturas:gestionar
  - tenant:configurar
  - impersonacion:usar

#### Scenario: Migration is idempotent for permissions
- **WHEN** running migration 003 twice
- **THEN** the permiso table SHALL still contain exactly 21 rows (no duplicates)

### Requirement: Seed all role-permission mappings
The system SHALL seed the full RolPermiso matrix from KB §3.3. The mapping SHALL be seeded per-tenant (using the first tenant's ID or a mechanism for default tenant seeding). The matrix:

| Rol | Permisos |
|-----|----------|
| ALUMNO | estado_academico:ver, evaluacion:reservar, aviso:confirmar |
| TUTOR | aviso:confirmar, atrasados:ver, entregas:detectar_sin_corregir, encuentros:gestionar, guardias:registrar |
| PROFESOR | aviso:confirmar, calificaciones:importar, atrasados:ver, entregas:detectar_sin_corregir, comunicacion:enviar, encuentros:gestionar, guardias:registrar, tareas:gestionar |
| COORDINADOR | aviso:confirmar, calificaciones:importar, atrasados:ver, entregas:detectar_sin_corregir, comunicacion:enviar, comunicacion:aprobar, encuentros:gestionar, guardias:registrar, tareas:gestionar, avisos:publicar, equipos:asignar, auditoria:ver |
| ADMIN | aviso:confirmar, calificaciones:importar, atrasados:ver, entregas:detectar_sin_corregir, comunicacion:enviar, comunicacion:aprobar, encuentros:gestionar, guardias:registrar, tareas:gestionar, avisos:publicar, equipos:asignar, estructura:gestionar, usuarios:gestionar, auditoria:ver, tenant:configurar, impersonacion:usar |
| FINANZAS | aviso:confirmar, auditoria:ver, liquidaciones:operar_grilla, liquidaciones:calcular_cerrar, facturas:gestionar |
| NEXO | *(none — zero permissions until PA-25 is resolved)* |

#### Scenario: ALUMNO has correct permissions
- **WHEN** querying effective permissions for ALUMNO
- **THEN** the result SHALL contain exactly: estado_academico:ver, evaluacion:reservar, aviso:confirmar

#### Scenario: ADMIN has all 16 permissions
- **WHEN** querying effective permissions for ADMIN
- **THEN** the result SHALL contain 16 permissions spanning all modules

#### Scenario: NEXO has zero permissions
- **WHEN** querying effective permissions for NEXO
- **THEN** the result SHALL be an empty set

#### Scenario: FINANZAS has only financial permissions
- **WHEN** querying effective permissions for FINANZAS
- **THEN** the result SHALL contain exactly: aviso:confirmar, auditoria:ver, liquidaciones:operar_grilla, liquidaciones:calcular_cerrar, facturas:gestionar

