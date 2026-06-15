## ADDED Requirements

### Requirement: GET /api/admin/usuarios — list usuarios

The system SHALL provide a paginated list endpoint for Usuarios.

- Method: GET
- Path: `/api/admin/usuarios`
- Guard: `require_permission("usuarios:gestionar")`
- Query params: `offset` (int, default 0), `limit` (int, default 20, max 100)
- Response: `{"items": list[UsuarioSafeResponse], "total": int, "offset": int, "limit": int}`
- PII fields SHALL NOT be returned in list responses (use UsuarioSafeResponse)

#### Scenario: List usuarios returns paginated safe responses
- **WHEN** calling GET /api/admin/usuarios with a valid token having usuarios:gestionar
- **THEN** a paginated response SHALL be returned with UsuarioSafeResponse items

#### Scenario: List usuarios excludes PII
- **WHEN** calling GET /api/admin/usuarios
- **THEN** dni, cuil, cbu, alias_cbu SHALL NOT be present in any item

#### Scenario: List usuarios returns 403 without permission
- **WHEN** calling GET /api/admin/usuarios without usuarios:gestionar permission
- **THEN** 403 Forbidden SHALL be returned

#### Scenario: List usuarios returns 401 without auth
- **WHEN** calling GET /api/admin/usuarios without a valid token
- **THEN** 401 Unauthorized SHALL be returned

### Requirement: POST /api/admin/usuarios — create usuario

The system SHALL provide a create endpoint for Usuarios.

- Method: POST
- Path: `/api/admin/usuarios`
- Guard: `require_permission("usuarios:gestionar")`
- Request body: UsuarioCreate (nombre, apellidos, dni, cuil, cbu, alias_cbu, banco?, regional?, legajo?, legajo_profesional?, facturador?, estado?)
- Response: 201 with UsuarioResponse (full, with decrypted PII)
- PII fields SHALL be encrypted before storage

#### Scenario: Create usuario returns 201 with full response
- **WHEN** calling POST /api/admin/usuarios with valid data
- **THEN** 201 Created SHALL be returned with UsuarioResponse including decrypted PII

#### Scenario: Create usuario encrypts PII in DB
- **WHEN** calling POST /api/admin/usuarios
- **THEN** the stored values for dni, cuil, cbu, alias_cbu SHALL be encrypted

#### Scenario: Create usuario rejects extra fields
- **WHEN** calling POST /api/admin/usuarios with unknown fields
- **THEN** 422 validation error SHALL be returned

### Requirement: GET /api/admin/usuarios/{id} — get usuario detail

The system SHALL provide a detail endpoint returning full Usuario with decrypted PII.

- Method: GET
- Path: `/api/admin/usuarios/{id}`
- Guard: `require_permission("usuarios:gestionar")`
- Response: UsuarioResponse (full, with decrypted PII)

#### Scenario: Get usuario by id returns full response with PII
- **WHEN** calling GET /api/admin/usuarios/{id} with an existing id
- **THEN** 200 OK SHALL be returned with UsuarioResponse including decrypted PII

#### Scenario: Get usuario by id returns 404
- **WHEN** calling GET /api/admin/usuarios/{id} with a non-existent id
- **THEN** 404 Not Found SHALL be returned

### Requirement: PUT /api/admin/usuarios/{id} — update usuario

The system SHALL provide an update endpoint for Usuarios.

- Method: PUT
- Path: `/api/admin/usuarios/{id}`
- Guard: `require_permission("usuarios:gestionar")`
- Request body: UsuarioUpdate (all fields optional)
- Response: UsuarioResponse (full, with decrypted PII)
- PII fields provided SHALL be re-encrypted before storage

#### Scenario: Update usuario returns updated response
- **WHEN** calling PUT /api/admin/usuarios/{id} with valid update data
- **THEN** 200 OK SHALL be returned with updated UsuarioResponse including decrypted PII

#### Scenario: Update usuario encrypts new PII
- **WHEN** calling PUT /api/admin/usuarios/{id} with new dni value
- **THEN** the new dni SHALL be encrypted before storage

### Requirement: DELETE /api/admin/usuarios/{id} — soft delete usuario

The system SHALL provide a soft delete endpoint for Usuarios.

- Method: DELETE
- Path: `/api/admin/usuarios/{id}`
- Guard: `require_permission("usuarios:gestionar")`
- Response: 204 No Content
- The deletion SHALL be soft (deleted_at set, not hard delete)

#### Scenario: Soft delete usuario returns 204
- **WHEN** calling DELETE /api/admin/usuarios/{id} with an existing id
- **THEN** 204 No Content SHALL be returned
- **AND** the Usuario SHALL have deleted_at set

#### Scenario: Soft deleted usuario excluded from list
- **WHEN** calling GET /api/admin/usuarios after soft-deleting a usuario
- **THEN** the deleted usuario SHALL NOT appear in results
