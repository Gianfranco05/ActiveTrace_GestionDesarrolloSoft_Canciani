# perfil Specification

## Purpose
Lectura y edición del perfil propio del usuario autenticado. Permite consultar todos los datos personales (incluyendo PII descifrada solo para el dueño) y actualizar campos editables con protección explícita del CUIL como campo de solo lectura.

## Requirements

### Requirement: Obtener perfil propio (F11.1)

The system SHALL allow any authenticated user to retrieve their own profile including PII fields decrypted for the owner.

- Method: GET
- Path: `/api/perfil`
- Guard: `require_permission("perfil:editar")`
- Response 200: `PerfilResponse` with `id`, `tenant_id`, `nombre`, `apellidos`, `email` (from auth_user), `dni`, `cuil`, `banco`, `cbu`, `alias_cbu`, `regional`, `legajo`, `legajo_profesional`, `facturador`, `estado`, `created_at`, `updated_at`
- The system SHALL resolve `email` from the linked `auth_user` record
- The system SHALL decrypt PII fields (dni, cuil, cbu, alias_cbu) before returning the response
- The response SHALL only contain the authenticated user's own data — no other user's profile is accessible via this endpoint

#### Scenario: Usuario obtiene su perfil con PII descifrada
- **WHEN** a PROFESOR calls GET /api/perfil
- **THEN** the system SHALL return the user's own profile with `cuil`, `dni`, `cbu`, `alias_cbu` in plain text
- **AND** the `email` SHALL be resolved from the linked auth_user

#### Scenario: Usuario no autenticado
- **WHEN** an unauthenticated request calls GET /api/perfil
- **THEN** the system SHALL respond 401 Unauthorized

#### Scenario: Usuario sin permiso perfil:editar
- **WHEN** a user without `perfil:editar` permission calls GET /api/perfil
- **THEN** the system SHALL respond 403 Forbidden

#### Scenario: Perfil incluye facturador
- **WHEN** a user whose `facturador` is True calls GET /api/perfil
- **THEN** the response SHALL include `facturador: true`

### Requirement: Editar perfil propio (F11.1)

The system SHALL allow any authenticated user to update editable fields of their own profile. CUIL SHALL NOT be modifiable through this endpoint.

- Method: PUT
- Path: `/api/perfil`
- Guard: `require_permission("perfil:editar")`
- Request body: `PerfilUpdateRequest` with optional fields: `nombre` (str?, max 120), `apellidos` (str?, max 120), `dni` (str?, optional), `banco` (str?, max 80), `cbu` (str?, optional), `alias_cbu` (str?, optional), `regional` (str?, max 80), `legajo_profesional` (str?, max 30), `facturador` (bool?, optional). CUIL SHALL NOT be present in the request schema.
- Response 200: `PerfilResponse` with updated fields
- The system SHALL encrypt PII fields (dni, cbu, alias_cbu) before persisting
- The system SHALL audit the operation with `PERFIL_EDITAR`
- Partial updates are supported: only fields present in the request body are updated; absent fields retain their current values

#### Scenario: Actualizar nombre y datos bancarios
- **WHEN** a PROFESOR sends PUT /api/perfil with `{"nombre": "Carlos", "banco": "Santander", "cbu": "2850590940090418135201"}`
- **THEN** the system SHALL update nombre and banco and cbu (encrypted) for the authenticated user
- **AND** respond 200 with the updated profile
- **AND** audit the operation with `PERFIL_EDITAR`

#### Scenario: Actualización parcial — solo regional
- **WHEN** a user sends PUT /api/perfil with `{"regional": "Rosario"}`
- **THEN** the system SHALL update only the regional field
- **AND** all other fields SHALL retain their current values

#### Scenario: Intentar modificar CUIL es rechazado
- **WHEN** a user sends PUT /api/perfil with `{"cuil": "20-12345678-9"}`
- **THEN** the system SHALL respond 422 Unprocessable Entity (rejected by `extra='forbid'` on schema)

#### Scenario: Actualizar facturador
- **WHEN** a user sends PUT /api/perfil with `{"facturador": true}`
- **THEN** the system SHALL update `facturador` to true
- **AND** respond 200

#### Scenario: Nombre excede longitud máxima
- **WHEN** a user sends PUT /api/perfil with `nombre` exceeding 120 characters
- **THEN** the system SHALL respond 422 Unprocessable Entity

#### Scenario: Usuario no autenticado
- **WHEN** an unauthenticated request calls PUT /api/perfil
- **THEN** the system SHALL respond 401 Unauthorized

### Requirement: CUIL es solo lectura

The system SHALL treat the CUIL field as read-only for profile self-editing. CUIL modifications require ADMIN privileges via a separate endpoint (not in C-20 scope).

- The `PerfilUpdateRequest` schema SHALL NOT include a `cuil` field
- The `PerfilService.update_perfil()` SHALL explicitly skip any attempt to modify `cuil`
- The `PerfilResponse` SHALL include `cuil` (decrypted) for display purposes

#### Scenario: CUIL presente en respuesta pero no modificable
- **WHEN** a user calls GET /api/perfil
- **THEN** the response SHALL include the user's CUIL
- **AND** any PUT to /api/perfil SHALL be rejected if it attempts to include `cuil` in the body

### Requirement: PII se cifra en reposo y se descifra para el dueño

The system SHALL apply AES-256 encryption to PII fields (dni, cuil, cbu, alias_cbu) when persisting to the database, and SHALL decrypt them when returning the profile to the owner.

- On PUT: fields dni, cbu, alias_cbu SHALL be encrypted before persisting
- On GET: fields dni, cuil, cbu, alias_cbu SHALL be decrypted before returning the response
- PII fields SHALL NOT appear in plain text in logs
- The encryption SHALL use the existing project encryption utility (from C-02)

#### Scenario: Cifrado round-trip para CBU
- **WHEN** a user updates their CBU via PUT and then retrieves their profile via GET
- **THEN** the GET response SHALL contain the same CBU value that was sent in the PUT

### Requirement: Tenant isolation en perfil

The system SHALL enforce that a user can only access and modify their own profile within their tenant. Cross-tenant access is impossible because the user identity is resolved from the JWT which includes tenant_id.

#### Scenario: Perfil solo del usuario autenticado
- **WHEN** any authenticated user calls GET /api/perfil
- **THEN** the system SHALL always return the profile of the authenticated user (resolved from JWT)
- **AND** no user_id parameter is accepted — the identity comes exclusively from the session
