## ADDED Requirements

### Requirement: Comunicacion model with state machine
The system SHALL implement a `Comunicacion` entity (E21) that represents an outbound email message to a student. The entity SHALL support soft-delete, store the recipient email encrypted (AES-256), track state transitions (RN-15), support lote grouping, and enforce tenant isolation.

#### Scenario: Comunicacion is created in Pendiente state
- **WHEN** a new Comunicacion record is created via the enqueue endpoint
- **THEN** the record SHALL have `estado = 'Pendiente'`
- **AND** the record SHALL have a valid UUID `id`
- **AND** the record SHALL have `tenant_id` from the authenticated user's session
- **AND** the record SHALL have `created_at` and `updated_at` timestamps

#### Scenario: Destinatario is encrypted at rest
- **WHEN** a Comunicacion record is stored in the database
- **THEN** the `destinatario` field SHALL be encrypted with AES-256
- **AND** reading the raw database column SHALL show ciphertext, not the plain email
- **AND** the repository SHALL decrypt the field when returning the record to authorized callers

#### Scenario: Soft delete preserves the record
- **WHEN** a Comunicacion record is "deleted"
- **THEN** the record SHALL NOT be physically removed from the database
- **AND** the `deleted_at` timestamp SHALL be set
- **AND** standard queries SHALL filter out soft-deleted records by default

#### Scenario: Tenant isolation
- **WHEN** querying Comunicacion records
- **THEN** all queries SHALL be scoped by the current user's `tenant_id`
- **AND** a user from tenant A SHALL NOT see Comunicacion records from tenant B

### Requirement: State machine enforces valid transitions (RN-15)
The system SHALL enforce the following state machine for Comunicacion records: Pendiente → Enviando → Enviado|Error|Cancelado. Invalid transitions SHALL be rejected at the service layer.

#### Scenario: Pendiente to Enviando transition
- **WHEN** a worker picks up a Pendiente message for processing
- **THEN** the system SHALL transition the state to 'Enviando'

#### Scenario: Enviando to Enviado transition
- **WHEN** the email sending succeeds for a message in Enviando state
- **THEN** the system SHALL transition the state to 'Enviado'
- **AND** the `enviado_at` timestamp SHALL be set

#### Scenario: Enviando to Error transition
- **WHEN** the email sending fails for a message in Enviando state
- **THEN** the system SHALL transition the state to 'Error'

#### Scenario: Pendiente to Cancelado transition
- **WHEN** a user with `comunicacion:enviar` cancels a message in Pendiente state
- **THEN** the system SHALL transition the state to 'Cancelado'

#### Scenario: Invalid transition from terminal state
- **WHEN** attempting to transition a message from 'Enviado' to any other state
- **THEN** the system SHALL raise an `InvalidStateTransitionError`

#### Scenario: Invalid transition from Enviando to Cancelado
- **WHEN** attempting to cancel a message in Enviando state
- **THEN** the system SHALL raise an `InvalidStateTransitionError`

#### Scenario: Lote_id groups related messages
- **WHEN** multiple Comunicacion records are created in a single enqueue call
- **THEN** all records SHALL share the same `lote_id` (UUID)
- **AND** the `lote_id` SHALL be generated server-side

### Requirement: Comunicacion database schema
The system SHALL create a `comunicacion` table with the following columns:

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, default gen_random_uuid() | Internal key |
| tenant_id | UUID | NOT NULL, FK → Tenant | Tenant isolation |
| lote_id | UUID | NOT NULL | Groups batch sends |
| enviado_por | UUID | NOT NULL, FK → Usuario | Who triggered the send |
| materia_id | UUID | FK → Materia | Academic context (nullable) |
| entrada_padron_id | UUID | FK → EntradaPadron | Target student (nullable) |
| destinatario | TEXT | NOT NULL | Recipient email (encrypted) |
| asunto | TEXT | NOT NULL | Email subject (template rendered) |
| cuerpo | TEXT | NOT NULL | Email body (template rendered) |
| template_id | UUID | Nullable | Which template was used |
| variables | JSONB | NOT NULL, default '{}' | Variable substitutions applied |
| estado | TEXT | NOT NULL, DEFAULT 'Pendiente' | State machine |
| requiere_aprobacion | BOOLEAN | NOT NULL, DEFAULT false | Denormalized from tenant |
| aprobado_por | UUID | Nullable, FK → Usuario | Who approved |
| enviado_at | TIMESTAMPTZ | Nullable | When sent |
| error_detalle | TEXT | Nullable | Error details if any |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | Creation timestamp |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | Last update timestamp |
| deleted_at | TIMESTAMPTZ | Nullable | Soft-delete timestamp |

#### Scenario: Table creation migration
- **WHEN** the Alembic migration `Migración 0NN: comunicacion` is applied
- **THEN** the `comunicacion` table SHALL be created with all specified columns
- **AND** indexes SHALL be created on `(tenant_id, estado)`, `(lote_id)`, `(tenant_id, created_at)`

### Requirement: Encrypted storage for destinatario
The system SHALL transparently encrypt the `destinatario` field at write time and decrypt it at read time, reusing the AES-256 encryption infrastructure from C-07.

#### Scenario: Encryption round-trip
- **WHEN** a Comunicacion record is created and then read
- **THEN** the `destinatario` value SHALL match the original plaintext input

#### Scenario: Encryption does not affect non-PII fields
- **WHEN** a Comunicacion record is stored
- **THEN** non-PII fields (asunto, cuerpo, lote_id, estado) SHALL NOT be encrypted
