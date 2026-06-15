## Why

activia-trace es multi-tenant desde el día 0 (ADR-002), pero hoy el sistema no tiene modelo de tenant, ni base común para entidades, ni repositorio que aísle datos entre instituciones. Sin estos cimientos, cada change futuro debería inventar su propio mecanismo de aislamiento — multiplicando bugs y debt. Este change materializa el contrato de tenancy: modelo Tenant, base mixin con soft delete, repositorio genérico con scope obligatorio, cifrado AES-256 para PII y la primera migración Alembic.

## What Changes

- Creación del modelo `Tenant` (UUID PK, name, slug, active) como raíz del modelo de datos
- Creación de `BaseModelMixin` con `id` (UUID v4), `tenant_id` (FK → Tenant), `created_at`, `updated_at`, `deleted_at` (soft delete)
- Creación de repositorio genérico `BaseRepository` con scope de tenant obligatorio en toda query; query sin `tenant_id` falla en code review
- Implementación de utilidades AES-256-GCM en `core/security.py`: `encrypt()` / `decrypt()` para atributos `[cifrado]`, usando `ENCRYPTION_KEY` de config, con protección contra log de secretos
- Implementación de resolución de tenant en `core/tenancy.py`: helper que deriva `tenant_id` del contexto de sesión (inyectado vía DI)
- Configuración de Alembic async (`env.py`) + migración 001 con tabla `tenant`
- Tests: aislamiento multi-tenant (tenant A no ve datos de tenant B), soft delete lifecycle, round-trip de cifrado, timestamps del mixin se auto-popolan

## Capabilities

### New Capabilities

- `tenant-model`: Entidad Tenant como raíz del modelo de datos. Campos: id (UUID), name (único), slug (único), is_active. Seed de tenant por defecto.
- `base-mixin`: Mixin declarativo SQLAlchemy que toda entidad del dominio extiende. Provee UUID PK, tenant_id FK, created_at, updated_at, deleted_at (soft delete).
- `repository-scope`: Repositorio genérico asíncrono con scope de tenant obligatorio en queries SELECT/UPDATE/DELETE. Métodos: list, get, create, update, soft_delete, with_deleted, only_deleted.
- `encryption`: Utilidades AES-256-GCM simétricas para cifrado/descifrado de atributos PII en reposo. Helpers `encrypt()`, `decrypt()` que operan sobre strings. Derivación de clave desde `ENCRYPTION_KEY`.
- `migration-001`: Setup Alembic async con engine asíncrono, env.py configurado, y primera migración que crea la tabla `tenant`.

### Modified Capabilities

*(ninguna — primer change de dominio)*

## Impact

- `backend/app/models/tenant.py` — nuevo modelo ORM Tenant
- `backend/app/models/base.py` — nuevo mixin base con UUID, tenant_id, timestamps, soft delete
- `backend/app/models/__init__.py` — exporta Base + Tenant
- `backend/app/repositories/base.py` — nuevo repositorio genérico con scope de tenant
- `backend/app/core/security.py` — se completa con utilidades AES-256 (era placeholder en C-01)
- `backend/app/core/tenancy.py` — se completa con resolución de tenant (era placeholder en C-01)
- `backend/alembic/env.py` — se configura para engine async
- `backend/alembic/versions/001_initial_tenant.py` — primera migración
- `backend/tests/` — nuevos tests de models, repositories, encryption, aislamiento
