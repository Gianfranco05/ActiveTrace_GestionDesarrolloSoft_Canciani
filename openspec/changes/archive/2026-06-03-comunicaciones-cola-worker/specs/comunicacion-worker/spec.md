## ADDED Requirements

### Requirement: Worker polls DB for pending communications
The system SHALL implement an async worker (`workers/comunicacion_worker.py`) that periodically polls the database for Comunicacion records in Pendiente state that are ready for processing. The worker SHALL use `FOR UPDATE SKIP LOCKED` for concurrency-safe batch processing.

#### Scenario: Worker polls Pendiente records
- **WHEN** the worker runs its poll cycle
- **THEN** it SHALL query for Comunicacion records WHERE `estado = 'Pendiente'`
- **AND** WHERE `(requiere_aprobacion = FALSE OR aprobado_por IS NOT NULL)`
- **AND** it SHALL use `FOR UPDATE SKIP LOCKED` to lock selected rows

#### Scenario: Worker processes in configurable batches
- **WHEN** the worker queries for pending records
- **THEN** it SHALL limit results to `BATCH_SIZE` (default: 50, configurable via env `BATCH_SIZE`)

#### Scenario: Worker polls at configurable interval
- **WHEN** the worker finishes processing a batch
- **THEN** it SHALL sleep for `POLL_INTERVAL` seconds (default: 10, configurable via env `POLL_INTERVAL`)

### Requirement: Worker transitions Pendiente → Enviando → Enviado/Error
The worker SHALL step each message through the state machine: mark as Enviando, attempt send, mark as Enviado or Error.

#### Scenario: Successful send transitions to Enviado
- **WHEN** the worker processes a message and the mock sender returns success
- **THEN** the record SHALL transition to `estado = 'Enviado'`
- **AND** `enviado_at` SHALL be set to the current timestamp

#### Scenario: Failed send transitions to Error
- **WHEN** the worker processes a message and the mock sender returns failure
- **THEN** the record SHALL transition to `estado = 'Error'`
- **AND** `error_detalle` SHALL contain the error message

#### Scenario: Worker renders template before sending
- **WHEN** the worker processes a message with a `template_id` and `variables`
- **THEN** it SHALL render the `asunto` and `cuerpo` by substituting `{{variables}}` in the template
- **AND** the rendered values SHALL be stored in the record

### Requirement: Worker startup recovery
The worker SHALL recover messages stuck in Enviando state for more than 30 minutes on startup, resetting them to Pendiente with a retry counter.

#### Scenario: Stuck Enviando messages are recovered on startup
- **WHEN** the worker starts
- **THEN** it SHALL query for Comunicacion records WHERE `estado = 'Enviando'` AND `updated_at < now() - interval '30 minutes'`
- **AND** those records SHALL be reset to `estado = 'Pendiente'`

#### Scenario: Worker startup recovery logs action
- **WHEN** the worker recovers stuck messages
- **THEN** it SHALL log the count of recovered messages
- **AND** the `error_detalle` SHALL be updated with "Recovered from stuck Enviando state"

### Requirement: Worker runs as standalone process
The worker SHALL start as an independent Python process, load the application context (DB session, encryption service, template engine), and run indefinitely until stopped.

#### Scenario: Worker starts and enters poll loop
- **WHEN** the worker process starts
- **THEN** it SHALL initialize the DB session factory
- **AND** enter an infinite poll loop (poll → process → sleep → repeat)
- **AND** SHALL handle `KeyboardInterrupt` gracefully (finish current batch, close session)

#### Scenario: Worker processes only approved messages
- **WHEN** a tenant has `requiere_aprobacion_comunicaciones = True`
- **THEN** the worker SHALL skip messages with `requiere_aprobacion = True` AND `aprobado_por IS NULL`
- **AND** those messages SHALL remain in Pendiente state until approved
