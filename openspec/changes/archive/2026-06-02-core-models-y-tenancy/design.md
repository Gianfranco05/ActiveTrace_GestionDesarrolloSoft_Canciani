## Context

activia-trace es multi-tenant desde el día 0 (ADR-002, row-level). C-01 dejó el esqueleto FastAPI con slots reservados en `core/`. Este change (C-02, governance **CRITICO**) construye los cimientos de tenancy que toda entidad futura va a usar: modelo Tenant, base mixin con soft delete, repositorio genérico con tenant scope obligatorio, cifrado AES-256, resolución de tenant, y la primera migración.

El contrato de C-01 asigna:
- `core/tenancy.py` → C-02 (resolución/aislamiento de tenant) — se completa ahora
- `core/security.py` → C-03 (JWT, Argon2, AES-256) — se completa la parte AES-256 ahora, JWT/Argon2 quedan para C-03

## Goals / Non-Goals

**Goals:**
- Modelo `Tenant` como raíz del modelo de datos con UUID PK
- `BaseModelMixin` que toda entidad extiende: UUID id, tenant_id FK, timestamps, soft delete
- `BaseRepository` asíncrono con scope de tenant obligatorio en toda query
- Utilidades AES-256-GCM para cifrado de PII (`encrypt`/`decrypt`)
- Resolución de tenant desde la sesión (`get_tenant_id()`)
- Alembic async configurado + migración 001 con tabla `tenant`
- Tests de aislamiento, soft delete, cifrado round-trip, timestamps

**Non-Goals:**
- Modelos de dominio (Carrera, Cohorte, Materia, Usuario, etc.) → C-06+
- Auth, JWT, Argon2id, refresh rotation → C-03
- RBAC, matriz de permisos, `require_permission` → C-04
- Audit log, impersonación → C-05
- Seed de datos de negocio (solo se siembra un tenant por defecto)

## Decisions

### D1 — Tenant model: UUID PK, unique name/slug, active flag

El modelo Tenant es la raíz de todo el modelo de datos. Diseño:

```
Tenant {
  id            : UUID        — PK, default uuid4
  name          : String(255) — nombre institucional, unique, not null
  slug          : String(100) — identificador URL-safe, unique, not null, indexed
  is_active     : Boolean     — soft toggle de disponibilidad, default True
  created_at    : DateTime    — auto
  updated_at    : DateTime    — auto
}
```

- `slug` se usa en URLs y referencias externas; `name` es el nombre legible
- `is_active` permite deshabilitar un tenant sin borrar datos
- Se siembra un tenant por defecto (`slug: "default"`) para que los tests y el desarrollo tengan un tenant raíz

**Alternativa descartada**: `tenant_id` como entero autoincremental. Se descarta porque UUID permite generar IDs fuera de la DB (tests, migraciones, sistemas distribuidos) sin colisiones. El contrato del proyecto (KB §Supuestos base) ya establece UUID como identidad de todas las entidades.

### D2 — Base mixin with UUID PK, tenant_id FK, timestamps, soft delete

`BaseModelMixin` es un mixin declarativo de SQLAlchemy que provee los campos comunes a TODA entidad del sistema:

| Campo | Tipo | Default | Notas |
|-------|------|---------|-------|
| `id` | `uuid.UUID` | `uuid.uuid4` | PK, no sequence |
| `tenant_id` | `uuid.UUID` | — | FK → Tenant(id), NOT NULL, indexed |
| `created_at` | `datetime` | `utcnow()` | server_default o Python default con timezone |
| `updated_at` | `datetime` | `utcnow()` | onupdate = utcnow |
| `deleted_at` | `datetime` | `NULL` | soft delete marker, indexed para filtro rápido |

Regla: toda tabla del dominio usa `__tablename__` explícito y hereda de `BaseModelMixin`. La columna `tenant_id` es siempre NOT NULL y con FK a Tenant.

Implementación técnica:
- Se usa `MappedAsDataclass` o `declarative_mixin` con anotaciones SQLAlchemy 2.0 type-annotation style
- `__tablename__` no se define en el mixin (cada subclase lo define)
- `deleted_at` se indexa para queries rápidas de soft delete

**Alternativa descartada**: `Base = declarative_base()` con `__abstract__ = True` y mixin manual. Se descarta porque SQLAlchemy 2.0 recomienda `DeclarativeBase` con anotaciones.

### D3 — Repository pattern with mandatory tenant scope

`BaseRepository` es un repositorio genérico asíncrono que recibe `tenant_id` en el constructor y filtra TODAS las queries por defecto. Firma:

```python
class BaseRepository[T: BaseModelMixin]:
    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None: ...

    async def list(self, **filters) -> list[T]
    async def get(self, id: uuid.UUID) -> T | None
    async def create(self, data: dict) -> T
    async def update(self, id: uuid.UUID, data: dict) -> T | None
    async def soft_delete(self, id: uuid.UUID) -> bool

    # Escapes del scope de soft delete (pero mantienen tenant_id)
    def with_deleted(self) -> Self     # incluye registros con deleted_at IS NOT NULL
    def only_deleted(self) -> Self     # solo registros borrados
```

Comportamiento:
- `list()`: `WHERE tenant_id = :tid AND deleted_at IS NULL`
- `get()`: `WHERE id = :id AND tenant_id = :tid AND deleted_at IS NULL`
- `create()`: setea `tenant_id` del constructor si no viene en `data`
- `update()`: verifica `tenant_id` + `deleted_at IS NULL` antes de actualizar
- `soft_delete()`: hace UPDATE `deleted_at = now()` con filtro `tenant_id` + `id`
- `with_deleted()`: retorna una copia del repo que omite el filtro `deleted_at IS NULL`
- `only_deleted()`: retorna una copia del repo que filtra solo `deleted_at IS NOT NULL`

Patrón de implementación: el repositorio usa un objeto `QueryBuilder` interno que ensambla la WHERE clause base con `tenant_id` y `deleted_at IS NULL`. Los métodos públicos delegan en el builder.

### D4 — AES-256-GCM encryption for PII

Se implementan dos funciones en `core/security.py`:

- `encrypt(plaintext: str) -> str`: cifra un string con AES-256-GCM, retorna base64 (nonce + ciphertext + tag)
- `decrypt(ciphertext_b64: str) -> str`: descifra, retorna string original

Detalles técnicos:
- Algoritmo: AES-256-GCM (autenticado, sin padding)
- Clave: derivada de `ENCRYPTION_KEY` (32 bytes, se lee de Settings) vía HKDF o directamente como bytes
- Nonce: 12 bytes aleatorios por operación de cifrado
- Output: base64 URL-safe de `nonce + ciphertext + tag` (un solo string)
- Error handling: si `decrypt` falla (clave incorrecta, datos corruptos, nonce inválido) → raise `EncryptionError` (excepción propia)
- Nunca loguear el texto plano ni la clave. El helper `encrypt_or_none` maneja `None` inputs

Ubicación: `backend/app/core/security.py`. Este archivo estaba reservado en C-01 y ahora se implementa la sección AES-256. El docstring marca qué partes son de C-02 y qué reserva para C-03 (JWT, Argon2).

**Alternativa descartada**: Fernet (AES-128-CBC + HMAC). Se descarta porque la `ENCRYPTION_KEY` es de 32 bytes (256 bits) y AES-256-GCM ofrece authenticated encryption en una sola operación, sin el overhead de HMAC por separado.

### D5 — Tenancy resolution: `get_tenant_id()`

Se completa `core/tenancy.py` con:

- `get_tenant_id_from_session(request) -> uuid.UUID`: extrae `tenant_id` del request state (seteado por el middleware de auth, que se implementa en C-03). En C-02, este helper se deja funcional pero dependiente de que C-03 inyecte el tenant en la sesión.
- Para tests, se acepta un dependency override que inyecte `tenant_id` directamente.

El helper se usa en la capa de Routers → Services para obtener el `tenant_id` y pasarlo a los repositorios.

### D6 — Alembic async setup + migration 001

El setup de Alembic se configura para engine async (asyncpg):
- `alembic/env.py`: usa `AsyncEngine` y `run_async` para migraciones async
- Migración 001: crea tabla `tenant` con los campos definidos en D1
- Convención: una migración por cambio de schema, numeración secuencial (`001`, `002`, ...)
- `alembic.ini` se reusa del setup de C-01

### D7 — Soft delete transversal

Toda entidad hereda `deleted_at` del mixin. El repositorio base filtra `deleted_at IS NULL` por defecto. Nunca se ejecuta DELETE SQL — solo UPDATE de `deleted_at`.

El flag `deleted_at` significa "el registro ya no está activo pero se conserva para auditoría e histórico." No se debe interpretar como "eliminado irreversiblemente." Las únicas operaciones que permiten ver datos "borrados" son los escapes explícitos `with_deleted()` y `only_deleted()`.

## Risks / Trade-offs

- **[AES-256 en C-02 vs C-01 design que lo asigna a C-03]** → El contrato de C-01 es correcto para JWT/Argon2, pero AES-256 es necesario ahora porque los modelos con PII (Usuario en C-07) dependen de C-02. La implementación en C-02 deja el espacio para JWT/Argon2 con docstring claro. Mitigación: el archivo `security.py` queda con secciones marcadas `# C-02: AES-256` y `# C-03: JWT/Argon2 (reserved)`.
- **[Tenancy resolution sin auth real]** → `tenancy.py` queda funcional pero requiere que C-03 inyecte `tenant_id` en el request state. Hasta entonces, tests y desarrollo usan dependency override. Mitigación: el helper es correcto, solo espera su dependency.
- **[Soft delete + unique constraints]** → Si una entidad tiene unique constraint sobre `(tenant_id, codigo)` y se soft-deletea un registro, no se podría crear otro con el mismo código. Mitigación: las unique constraints pueden incluir `deleted_at IS NULL` como partial index en PostgreSQL, o la app verifica unicidad solo sobre registros activos.
- **[Repositorio genérico con tipos SQLAlchemy]** → El tipo genérico `T` debe estar acotado a subtipos de `BaseModelMixin`. SQLAlchemy 2.0 con anotaciones tipadas puede generar conflictos con Mypy/pyright. Mitigación: usar `TypeVar('T', bound=BaseModelMixin)` y testear el tipado.

## Migration Plan

1. Implementar modelos (Tenant + BaseModelMixin)
2. Implementar repositorio genérico
3. Implementar AES-256 en security.py
4. Completar tenancy.py
5. Configurar Alembic async y generar migración 001
6. Ejecutar migración contra DB de desarrollo
7. Sembrar tenant por defecto (seed)
8. Escribir tests: aislamiento, soft delete, cifrado, timestamps
9. Verificar que tests pasen con DB real (PostgreSQL en compose)

Rollback: `alembic downgrade -1` elimina la tabla tenant. El resto (modelos, repositorio, cifrado) no requiere rollback de datos por ser código nuevo sin estado.

## Open Questions

- **Partial unique index para soft delete**: ¿se implementa en migración 001 o en cada migración de dominio? Recomendación: en cada migración de dominio, porque el partial index depende de las columnas de unicidad de cada entidad.
- **Encryption key rotation**: ¿soporte inicial en C-02 o se deja para cuando haya datos cifrados reales? Decisión: sin soporte de rotation en C-02. Se agrega cuando se implemente Usuario (C-07).
- **¿Repositorio unit of work o transacción explícita?**: se mantiene simple: cada método del repo es una transacción implícita (session autocommit). Para operaciones multi-repo, el Service orquesta la sesión compartida.
