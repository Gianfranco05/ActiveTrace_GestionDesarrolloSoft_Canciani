# inbox-mensajeria Specification

## Purpose
Mensajería interna entre usuarios registrados del sistema. Permite enviar mensajes que inician hilos de conversación, ver la bandeja de entrada con los hilos recibidos, abrir un hilo para leer todos los mensajes, y responder dentro del hilo. Es un canal paralelo e independiente del sistema de emails a alumnos (Comunicacion).

## Requirements

### Requirement: Enviar mensaje (inicia hilo nuevo)

The system SHALL allow any authenticated user with `mensajeria:usar` to send a message to another user in the same tenant. Sending a message creates a new thread.

- Method: POST
- Path: `/api/inbox`
- Guard: `require_permission("mensajeria:usar")`
- Request body: `MensajeCreateRequest` with `recipient_id` (UUID, required — the message recipient), `asunto` (str, required, max 250), `cuerpo` (str, required, max 5000)
- Response 201: `MensajeResponse` with `id`, `sender_id`, `sender_nombre`, `recipient_id`, `recipient_nombre`, `parent_id` (null for new threads), `asunto`, `cuerpo`, `leido` (false), `created_at`
- The system SHALL set `sender_id` to the authenticated user
- The system SHALL set `parent_id` to null (root of new thread)
- The system SHALL set `leido` to false
- The system SHALL audit the operation with `MENSAJE_ENVIAR`
- The recipient MUST exist and belong to the same tenant

#### Scenario: PROFESOR envía mensaje a COORDINADOR
- **WHEN** a PROFESOR sends POST /api/inbox with `{"recipient_id": "<coordinator-uuid>", "asunto": "Consulta sobre cohorte", "cuerpo": "Necesito revisar las fechas del cohorte 2025-B"}`
- **THEN** the system SHALL create a Mensaje with `parent_id=null`, `sender_id=PROFESOR`, `leido=false`
- **AND** respond 201 with the created message
- **AND** audit the operation with `MENSAJE_ENVIAR`

#### Scenario: Destinatario no existe
- **WHEN** a user sends POST /api/inbox with a non-existent `recipient_id`
- **THEN** the system SHALL respond 404 Not Found

#### Scenario: Destinatario de otro tenant
- **WHEN** a user from tenant A sends POST /api/inbox to a recipient from tenant B
- **THEN** the system SHALL respond 404 Not Found (not 403, to avoid leaking existence)

#### Scenario: Mensaje sin asunto
- **WHEN** POST /api/inbox omits `asunto`
- **THEN** the system SHALL respond 422 Unprocessable Entity

#### Scenario: Cuerpo vacío
- **WHEN** POST /api/inbox with `cuerpo: ""`
- **THEN** the system SHALL respond 422 Unprocessable Entity

#### Scenario: Cuerpo excede máximo
- **WHEN** POST /api/inbox with `cuerpo` exceeding 5000 characters
- **THEN** the system SHALL respond 422 Unprocessable Entity

#### Scenario: Usuario sin permiso mensajeria:usar
- **WHEN** a user without `mensajeria:usar` calls POST /api/inbox
- **THEN** the system SHALL respond 403 Forbidden

### Requirement: Listar bandeja de entrada (inbox)

The system SHALL allow an authenticated user to list their received message threads. Threads are identified by the root message (the first message in the conversation where the user is the recipient).

- Method: GET
- Path: `/api/inbox`
- Guard: `require_permission("mensajeria:usar")`
- Query params: `offset` (int, default 0), `limit` (int, default 20, max 50)
- Response 200: `{"items": list[InboxThreadResponse], "total": int, "offset": int, "limit": int}`
- Each `InboxThreadResponse` SHALL include: `thread_id` (ID of the root message), `asunto`, `sender_nombre` (name of the thread initiator), `last_message_preview` (first 100 chars of last message body), `message_count` (total messages in thread), `unread_count` (messages where recipient_id=user AND leido=false), `last_activity` (created_at of the most recent message in the thread)
- Threads SHALL be ordered by `last_activity` descending (most recent activity first)
- The inbox SHALL only include threads where the authenticated user is the `recipient_id` of the root message
- The inbox SHALL NOT include threads initiated by the user (sent messages) — those are visible via thread detail if the user is a participant

#### Scenario: PROFESOR ve sus hilos recibidos
- **WHEN** a PROFESOR calls GET /api/inbox
- **THEN** the system SHALL return only threads where the PROFESOR is the recipient of the root message
- **AND** threads SHALL be ordered by most recent activity first
- **AND** each thread SHALL include unread count

#### Scenario: Inbox vacío
- **WHEN** a user with no received messages calls GET /api/inbox
- **THEN** the system SHALL return `{"items": [], "total": 0, "offset": 0, "limit": 20}`

#### Scenario: Paginación del inbox
- **WHEN** a user calls GET /api/inbox?offset=0&limit=10
- **THEN** the system SHALL return at most 10 threads and include `total` count of all threads

#### Scenario: Usuario no autenticado
- **WHEN** an unauthenticated request calls GET /api/inbox
- **THEN** the system SHALL respond 401 Unauthorized

#### Scenario: Tenant isolation en inbox
- **WHEN** a user calls GET /api/inbox
- **THEN** the system SHALL only return threads belonging to the user's tenant

### Requirement: Ver hilo de mensajes (thread detail)

The system SHALL allow a thread participant (sender or recipient of any message in the thread) to view the complete thread with all replies.

- Method: GET
- Path: `/api/inbox/{thread_id}`
- Guard: `require_permission("mensajeria:usar")`
- Response 200: `ThreadDetailResponse` with `thread` (MensajeResponse — root message) and `replies` (list[MensajeResponse] — ordered by created_at ASC)
- Each `MensajeResponse` SHALL include `id`, `sender_id`, `sender_nombre`, `recipient_id`, `recipient_nombre`, `parent_id`, `asunto`, `cuerpo`, `leido`, `leido_at`, `created_at`
- The system SHALL mark as read all messages in the thread where the authenticated user is the `recipient_id` and `leido=false`
- Only thread participants (sender or recipient of root message) SHALL access the thread
- Non-participants SHALL receive 404 (not 403, to avoid leaking thread existence)

#### Scenario: PROFESOR ve hilo donde es destinatario
- **WHEN** a PROFESOR calls GET /api/inbox/<thread_id> for a thread where they are the recipient
- **THEN** the system SHALL return the root message and all replies ordered by created_at ascending
- **AND** mark the PROFESOR's unread messages as read

#### Scenario: COORDINADOR ve hilo donde es emisor
- **WHEN** a COORDINADOR calls GET /api/inbox/<thread_id> for a thread they initiated
- **THEN** the system SHALL return the root message and all replies
- **AND** only mark messages where COORDINADOR is recipient as read

#### Scenario: Hilo ajeno devuelve 404
- **WHEN** a user who is neither sender nor recipient of any message in the thread calls GET /api/inbox/<thread_id>
- **THEN** the system SHALL respond 404 Not Found

#### Scenario: Hilo inexistente
- **WHEN** any user calls GET /api/inbox/<non-existent-uuid>
- **THEN** the system SHALL respond 404 Not Found

#### Scenario: Hilo con múltiples respuestas
- **WHEN** a thread has 3 replies
- **THEN** GET /api/inbox/<thread_id> SHALL return the root message plus 3 replies in chronological order

#### Scenario: Tenant isolation en hilo
- **WHEN** a user from tenant A tries to access a thread from tenant B
- **THEN** the system SHALL respond 404 Not Found

### Requirement: Responder en un hilo

The system SHALL allow a thread participant to reply within an existing thread. Replies are added to the thread and maintain the original subject.

- Method: POST
- Path: `/api/inbox/{thread_id}/reply`
- Guard: `require_permission("mensajeria:usar")`
- Request body: `MensajeReplyRequest` with `cuerpo` (str, required, max 5000)
- Response 201: `MensajeResponse` with `parent_id` set to `thread_id`
- The system SHALL set `sender_id` to the authenticated user
- The system SHALL set `recipient_id` to the other participant of the thread (root message's sender if replier is root's recipient; root message's recipient if replier is root's sender)
- The system SHALL copy `asunto` from the root message
- The system SHALL audit the operation with `MENSAJE_ENVIAR`
- Only thread participants (sender or recipient of root message) SHALL reply

#### Scenario: PROFESOR responde en hilo recibido
- **WHEN** a PROFESOR who is the recipient of thread <id> sends POST /api/inbox/<id>/reply with `{"cuerpo": "Gracias por la información, lo reviso"}`
- **THEN** the system SHALL create a Mensaje with `parent_id=<id>`, `sender_id=PROFESOR`, `recipient_id=<root-sender>`, `asunto=<root-asunto>`
- **AND** respond 201
- **AND** audit with `MENSAJE_ENVIAR`

#### Scenario: COORDINADOR responde en hilo que inició
- **WHEN** a COORDINADOR who initiated thread <id> sends POST /api/inbox/<id>/reply
- **THEN** the system SHALL set `recipient_id` to the root message's recipient
- **AND** respond 201

#### Scenario: Responder en hilo ajeno
- **WHEN** a user who is neither sender nor recipient of the root message tries to reply
- **THEN** the system SHALL respond 404 Not Found

#### Scenario: Responder en hilo inexistente
- **WHEN** POST /api/inbox/<non-existent-uuid>/reply
- **THEN** the system SHALL respond 404 Not Found

#### Scenario: Reply con cuerpo vacío
- **WHEN** POST /api/inbox/<id>/reply with `cuerpo: ""`
- **THEN** the system SHALL respond 422 Unprocessable Entity

### Requirement: Mensajes marcados como leídos al abrir hilo

The system SHALL automatically mark messages as read when a user opens a thread. Only messages where the authenticated user is the recipient are marked as read.

- On GET `/api/inbox/{thread_id}`: all messages in the thread where `recipient_id = authenticated_user_id` and `leido = false` SHALL be updated to `leido = true` with `leido_at = now()`
- Messages where the user is the sender are NOT marked as read (the sender already knows their own messages)
- The `unread_count` in inbox thread list SHALL reflect the current read state

#### Scenario: Abrir hilo marca mensajes del destinatario como leídos
- **WHEN** a user opens a thread where they are the recipient of 3 messages, 2 unread
- **THEN** after GET /api/inbox/<thread_id>, both unread messages SHALL have `leido=true` and `leido_at` set
- **AND** subsequent GET /api/inbox SHALL show `unread_count=0` for that thread

#### Scenario: Abrir hilo no afecta mensajes del emisor
- **WHEN** a user opens a thread they initiated
- **THEN** messages where the user is sender SHALL NOT have their `leido` status changed
- **AND** only messages where the user is recipient SHALL be marked as read

### Requirement: Tenant isolation en mensajería

The system SHALL enforce tenant isolation on all inbox endpoints. Users from one tenant SHALL NOT access messages or threads from another tenant.

- Every repository query SHALL filter by `tenant_id` from the authenticated session
- Cross-tenant access attempts SHALL return 404 (not 403, to avoid leaking existence)
- A user CANNOT send a message to a recipient in another tenant

#### Scenario: Mensaje de otro tenant no visible
- **WHEN** a user from tenant A tries to GET /api/inbox/<id> for a thread belonging to tenant B
- **THEN** the system SHALL respond 404 Not Found

#### Scenario: Enviar mensaje a usuario de otro tenant
- **WHEN** a user from tenant A sends POST /api/inbox with `recipient_id` of a user from tenant B
- **THEN** the system SHALL respond 404 Not Found
