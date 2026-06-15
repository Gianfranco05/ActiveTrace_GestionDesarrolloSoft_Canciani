## Context

C-11 delivered analytical views that identify at-risk students. But teachers currently have no way to act on that insight within the platform — they export lists and email manually. C-12 adds the communication capability: async email dispatch with a DB-backed worker, mandatory preview (RN-16), configurable human approval per tenant (RN-17), and full state machine tracking (RN-15).

This is a **HIGH governance** change — it processes outbound email with PII (recipient email encrypted at rest), introduces an async worker pattern, and adds configurable approval flows that affect data visibility.

The KB defines the model at E21 (Comunicacion), the functional requirements at F3.1–F3.3, the flows at FL-02 (pasos 7–8) and FL-04, and the worker architecture at §5.2.

Key constraints from the existing architecture:
- **Clean Architecture**: Routers → Services → Repositories → Models
- **DB as queue**: no external message broker per established pattern
- **AES-256 for PII**: destinatario stored encrypted (same pattern as C-07 Usuario PII)
- **Soft delete**: Comunicacion preserves history
- **Tenant isolation**: all queries scoped by tenant_id

## Goals / Non-Goals

**Goals:**
- `ComunicacionService` — state machine enforcing RN-15 (Pendiente → Enviando → Enviado|Error|Cancelado). No invalid transitions.
- `Comunicacion` ORM model with soft-delete, encrypted destinatario, tenant_id, lote_id.
- Preview endpoint — renders template with substituted variables for each recipient. Returns estimated count.
- Enqueue endpoint — validates preview was called, creates Comunicaciones in Pendiente, assigns lote_id.
- Approval endpoint — configurable per Tenant. If require_aprobacion=true, messages stay Pendiente until approved. Lote-level and individual approval/rejection.
- List endpoint — filters by estado, lote_id, created date range.
- Detail endpoint — single Comunicacion with full state history.
- Cancel endpoint — transitions Pendiente → Cancelado. Can cancel by lote_id or individual id.
- Worker (`workers/comunicacion_worker.py`) — polls Pendiente records in batches, transitions to Enviando → Enviado/Error. Configurable poll interval and batch size.
- Template rendering with substitution variables: `{{nombre}}`, `{{apellidos}}`, `{{materia}}`, `{{comision}}`, `{{fecha}}`.
- Audit actions: `COMUNICACION_ENVIAR`, `COMUNICACION_APROBAR`, `COMUNICACION_CANCELAR`.
- Alembic migration for Comunicacion table.
- Pydantic schemas for all request/response DTOs with `extra='forbid'`.
- 6 new API endpoints under `/api/comunicaciones/`.

**Non-Goals:**
- Actual email sending (SMTP/API integration) — the worker records Enviado/Error but the sending itself is a mock call for this change. Real email transport is added when infra is ready.
- External message broker (RabbitMQ, Redis queue) — DB as queue per existing architecture.
- Retry logic for failed messages — deferred to post-MVP. Failed messages are terminal for now.
- Frontend UI — deferred to C-22 (frontend-academico-docente).
- Template management CRUD — templates are seeded by migration or config. No admin UI for editing.
- Scheduling (send at specific date/time) — enqueue happens immediately.
- Bulk preview (showing ALL recipients rendered) — preview shows a sample (first 5 + count).
- Pagination for now — list returns all results (acceptable for typical volumes).

## Decisions

### D1 — DB as queue (no external broker)

The worker polls the `comunicacion` table for records WHERE `estado = 'Pendiente' AND (requiere_aprobacion = False OR aprobado_por IS NOT NULL)`. Processed in batches of `BATCH_SIZE` (default 50) with `POLL_INTERVAL` (default 10 seconds).

```
Worker loop:
1. SELECT * FROM comunicacion WHERE estado = 'Pendiente'
   AND (requiere_aprobacion = False OR aprobado_por IS NOT NULL)
   AND tenant_id IS NOT NULL
   ORDER BY created_at ASC LIMIT BATCH_SIZE
   FOR UPDATE SKIP LOCKED
2. For each record:
   a. UPDATE estado = 'Enviando'
   b. Render template with variables
   c. Call send_mock() → mark Enviado or Error
   d. UPDATE estado = 'Enviado' OR 'Error'
3. Sleep POLL_INTERVAL
```

**Why DB-as-queue?** No external infrastructure dependency; same pattern the codebase already uses (no Celery, no Redis). `FOR UPDATE SKIP LOCKED` prevents multiple worker instances from processing the same message. Acceptable for the expected volume (hundreds, not millions).

### D2 — FOR UPDATE SKIP LOCKED for worker concurrency

Use PostgreSQL `FOR UPDATE SKIP LOCKED` on the poll query to handle multiple worker replicas safely. Each worker locks only the rows it processes; rows locked by another worker are skipped.

```sql
SELECT * FROM comunicacion
WHERE estado = 'Pendiente'
  AND (requiere_aprobacion = FALSE OR aprobado_por IS NOT NULL)
ORDER BY created_at ASC
LIMIT :batch_size
FOR UPDATE SKIP LOCKED
```

**Why SKIP LOCKED?** It's the standard PostgreSQL pattern for work queues. Avoids row-level contention between workers. No external lock manager needed.

### D3 — State machine as explicit transitions in service layer

The `ComunicacionService` enforces all valid transitions. Invalid transitions raise `InvalidStateTransitionError`.

```python
ALLOWED_TRANSITIONS = {
    EstadoComunicacion.PENDIENTE: [EstadoComunicacion.ENVIANDO, EstadoComunicacion.CANCELADO],
    EstadoComunicacion.ENVIANDO: [EstadoComunicacion.ENVIADO, EstadoComunicacion.ERROR],
    EstadoComunicacion.ENVIADO: [],  # terminal
    EstadoComunicacion.ERROR: [],    # terminal
    EstadoComunicacion.CANCELADO: [],  # terminal
}
```

**Why explicit state machine?** Prevents silent illegal transitions at the domain layer. The state machine is a dataclass/dict, not a third-party library — simple, testable, no external dependency.

### D4 — Approval check at domain layer, not just API guard

Every tenant has a `requiere_aprobacion_comunicaciones` flag on the Tenant model. When a Comunicacion is created for a tenant with this flag = True, the record is created in Pendiente state and the worker SKIPS it until `aprobado_por` is set.

The approval endpoint updates all matching records for a lote:
```sql
UPDATE comunicacion SET estado = 'Enviando', aprobado_por = :user_id
WHERE lote_id = :lote_id AND estado = 'Pendiente'
```

Or for individual approval:
```sql
UPDATE comunicacion SET estado = 'Enviando', aprobado_por = :user_id
WHERE id = :id AND estado = 'Pendiente'
```

**Why domain-level?** The tenant flag is checked in the service layer during enqueue, not in the router. This ensures the rule cannot be bypassed via API call changes or future code paths.

### D5 — Template variables with Pydantic-based substitution

Templates are stored as text with `{{variable}}` placeholders. The `TemplateEngine` (internal to ComunicacionService) resolves variables using a Pydantic model for type safety.

```python
class TemplateVariables(BaseModel):
    nombre: str
    apellidos: str
    materia: str
    comision: str | None = None
    fecha: str | None = None

def render(template: str, vars: TemplateVariables) -> str:
    for field, value in vars.model_dump(exclude_none=True).items():
        template = template.replace("{{%s}}" % field, str(value))
    return template
```

**Why not Jinja2?** The variable set is small and fixed. A simple `str.replace` loop avoids adding a template engine dependency. If template complexity grows, Jinja2 can be added later.

### D6 — Preview creates a PREVIEW audit record but no DB row

Preview does NOT create a Comunicacion record. It:
1. Loads the recipients from the selected EntradaPadron or filter
2. Renders the template for a sample (first 5 recipients)
3. Returns: sample recipients with rendered subject/body, total_recipients count, estimated variables
4. Logs a `COMUNICACION_PREVIEW` audit action (informational)

The client MUST call preview AND get a `preview_token` (a hash of the lote config + timestamp) before the enqueue endpoint accepts the request. This enforces RN-16.

```python
preview_token = hashlib.sha256(
    f"{tenant_id}:{materia_id}:{cohorte_id}:{template_id}:{timestamp}".encode()
).hexdigest()[:16]
```

Preview tokens expire after 15 minutes (configurable).

**Why preview_token?** Prevents enqueue without preview (RN-16 compliance). The token is a lightweight proof-of-preview, not a cryptographic guarantee.

### D7 — Encrypted destinatario (AES-256) reusing C-07 infrastructure

The `destinatario` field (email address) is encrypted at rest using the same `encryption_service` from C-07 (AES-256 with Fernet-like symmetric encryption).

Repository pattern: `ComunicacionRepository.create()` encrypts before insert; `ComunicacionRepository.get()` decrypts only when read by authorized users.

**Why reuse C-07?** Consistent encryption layer across all PII. No need to implement a separate encryption scheme for one field.

### D8 — Lote_id as UUID generated at enqueue time

When `POST /api/comunicaciones/enviar` is called, a batch UUID (`lote_id`) is generated server-side. All Comunicacion records created in that call share the same `lote_id`. This groups messages for approval, cancellation, and tracking.

**Why server-side?** Prevents client from injecting duplicate lote_ids or grouping unrelated messages arbitrarily.

### D9 — Router structure

| Method | Path | Guard | Description |
|--------|------|-------|-------------|
| POST | `/api/comunicaciones/preview` | `comunicacion:enviar` | Preview template rendering (F3.1) |
| POST | `/api/comunicaciones/enviar` | `comunicacion:enviar` | Mass enqueue (F3.2) |
| POST | `/api/comunicaciones/{id}/aprobar` | `comunicacion:aprobar` | Approve lote or individual (F3.3) |
| POST | `/api/comunicaciones/{id}/cancelar` | `comunicacion:enviar` | Cancel lote or individual |
| GET | `/api/comunicaciones` | `comunicacion:ver` | List with filters |
| GET | `/api/comunicaciones/{id}` | `comunicacion:ver` | Detail |

### D10 — Permission seeding

Three new permissions must exist in the permiso catalog:

| Permission | Roles | Description |
|------------|-------|-------------|
| `comunicacion:enviar` | PROFESOR (propio), COORDINADOR, ADMIN | Preview, enqueue, cancel |
| `comunicacion:aprobar` | COORDINADOR, ADMIN | Approve mass communications |
| `comunicacion:ver` | PROFESOR (propio), TUTOR (propio), COORDINADOR, ADMIN | View communications |

### D11 — Worker lifecycle management

The worker runs as a standalone Python process (separate container). It is started by the main application as a subprocess or via `docker-compose` as a separate service.

```yaml
# docker-compose.yml addition
services:
  comunicacion-worker:
    build: .
    command: python -m app.workers.comunicacion_worker
    depends_on:
      - db
    environment:
      - POLL_INTERVAL=10
      - BATCH_SIZE=50
```

The worker loads the FastAPI app context (to reuse DB session factory, encryption service, etc.) but does NOT expose HTTP endpoints.

### D12 — Audit action codes

New codes to add to the audit catalog:

| Code | Action |
|------|--------|
| `COMUNICACION_PREVIEW` | Preview executed |
| `COMUNICACION_ENVIAR` | Messages enqueued |
| `COMUNICACION_APROBAR` | Lote/individual approved |
| `COMUNICACION_CANCELAR` | Lote/individual cancelled |

## Risks / Trade-offs

- **[DB as queue vs dedicated broker]** — DB polling with `FOR UPDATE SKIP LOCKED` scales acceptably for hundreds of messages. If volume grows to thousands/min, the polling overhead and DB contention may require migration to Redis/RabbitMQ. **Mitigation**: configuration-driven poll interval; add a `processed_at` index early.
- **[Mock email sending]** — The worker "sends" by calling a mock function (`send_mock()`) that always succeeds or randomly fails. Real SMTP/API integration is out of scope. **Mitigation**: the service interface (`EmailSender`) is designed as an injectable protocol/ABC — real implementation plugs in without changing the worker.
- **[Preview token window]** — Preview tokens expire in 15 minutes. If a user previews and comes back later, they must re-preview. **Mitigation**: 15 min is generous for a single session; user gets a clear "token expired — re-preview" error.
- **[Tenant approval flag race condition]** — If the tenant flag changes after messages are enqueued but before the worker picks them up, approved messages might be blocked. **Mitigation**: the flag is checked at enqueue time and stored in `requiere_aprobacion` per message (denormalized), so changes don't affect in-flight messages.
- **[Worker crash during transition]** — If the worker crashes after setting `Enviando` but before setting `Enviado/Error`, the message stays `Enviando` forever. **Mitigation**: a startup recovery query finds messages stuck in `Enviando` for >30 minutes and resets them to `Pendiente` with an incremented retry counter.
- **[Large lote approval performance]** — Approving 5000 messages in one lote could mean a large UPDATE. **Mitigation**: use batch UPDATE with LIMIT in a loop; the UI paginates anyway.
- **[`comunicacion:enviar` scoped to PROFESOR (propio)]** — Same pattern as C-10's `calificaciones:ver (propio)`. The guard must check that the PROFESOR is assigned to the materia via Asignacion. COORDINADOR/ADMIN see all.

## Migration Plan

1. Add `requiere_aprobacion_comunicaciones` boolean to Tenant model (new column, default false)
2. Create Alembic migration `Migración 0NN: comunicacion` — creates the comunicacion table
3. Seed permissions: `comunicacion:enviar`, `comunicacion:aprobar`, `comunicacion:ver` in permiso catalog
4. Add audit codes: `COMUNICACION_PREVIEW`, `COMUNICACION_ENVIAR`, `COMUNICACION_APROBAR`, `COMUNICACION_CANCELAR`
5. Implement `Comunicacion` ORM model with soft-delete mixin
6. Implement `ComunicacionRepository` with encrypted write / decrypted read
7. Implement `ComunicacionService` with state machine, preview, enqueue, approve, cancel
8. Implement schemas in `backend/app/schemas/comunicacion.py`
9. Implement `EmailSender` protocol/mock
10. Implement worker in `backend/app/workers/comunicacion_worker.py`
11. Implement router in `backend/app/api/v1/routers/comunicaciones.py`
12. Register router and wire dependencies in `main.py`
13. Test: state machine transitions, preview flow, enqueue + worker processing, approval flow, cancel flow, tenant isolation, encrypted storage, permission guards

## Open Questions

- **OA-01**: Template storage — seeded via migration or config file? Decision: seeded as initial data via Alembic migration (simple, versioned). Template editor deferred.
