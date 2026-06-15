## 0. Safety Net — Pre-existing tests baseline

- [x] 0.1 Run existing test suite: `pytest -q` from `backend/` — capture baseline
- [x] 0.2 If any test FAILS → STOP, report as pre-existing failure to orchestrator

## 1. Permisos + códigos de auditoría

- [x] 1.1 RED: Write failing test `tests/test_perfil_permisos.py` — `test_permiso_perfil_editar_exists` verifica que el permiso `perfil:editar` se inserta en `permiso`
- [x] 1.2 RED: Write failing test `tests/test_mensajeria_permisos.py` — `test_permiso_mensajeria_usar_exists` verifica que `mensajeria:usar` se inserta en `permiso`
- [x] 1.3 GREEN: Agregar `"perfil:editar": "Editar perfil propio"` y `"mensajeria:usar": "Usar mensajería interna"` a `PERMISSION_CODES` en `backend/app/core/permissions.py`
- [x] 1.4 GREEN: Agregar `PERFIL_EDITAR` y `MENSAJE_ENVIAR` a `AuditAction` en `backend/app/core/audit_codes.py`
- [x] 1.5 Implementar `_seed_perfil_mensajeria_permisos()` en la migración con inserción de `perfil:editar` y `mensajeria:usar`, y asociación a los 7 roles (ALUMNO, TUTOR, PROFESOR, COORDINADOR, NEXO, ADMIN, FINANZAS)
- [x] 1.6 TRIANGULATE: Add `test_permiso_perfil_asociado_a_profesor`, `test_permiso_mensajeria_asociado_a_admin`, `test_permiso_mensajeria_asociado_a_alumno`, `test_audit_codes_perfil_mensajeria_existen`
- [x] 1.7 Execute tests: confirm GREEN

## 2. Migración Alembic — Modelo Mensaje

- [x] 2.1 Crear `backend/alembic/versions/017_mensaje.py` con `op.create_table` para `mensaje` con todos los campos: id (UUID PK), tenant_id (FK → tenant), sender_id (FK → usuario), recipient_id (FK → usuario), parent_id (FK → mensaje, self-referential, nullable), asunto (String 250), cuerpo (Text), leido (Boolean, default False), leido_at (DateTime, nullable), más timestamps del mixin
- [x] 2.2 Agregar índices: `ix_mensaje_recipient_id`, `ix_mensaje_parent_id`, `ix_mensaje_tenant_id`, `ix_mensaje_created_at`
- [x] 2.3 Agregar `_seed_perfil_mensajeria_permisos()` en el upgrade de la migración
- [x] 2.4 Implementar downgrade con `op.drop_table("mensaje")` y eliminación de registros de seed

## 3. Modelo SQLAlchemy — Mensaje

- [x] 3.1 RED: Write failing test `tests/test_modelo_mensaje.py` — `test_mensaje_creation` verifica que se puede crear un Mensaje con sender_id, recipient_id, asunto, cuerpo; parent_id nullable; leido default False
- [x] 3.2 GREEN: Implementar `backend/app/models/mensaje.py` — clase `Mensaje(BaseModelMixin, Base)` con campos y relaciones (sender → Usuario, recipient → Usuario, parent → Mensaje self-referential, replies → list[Mensaje])
- [x] 3.3 Registrar modelo en `backend/app/models/__init__.py`
- [x] 3.4 Execute tests: confirm GREEN
- [x] 3.5 TRIANGULATE: Add `test_mensaje_parent_nullable`, `test_mensaje_leido_default_false`, `test_mensaje_self_referential_fk`, `test_mensaje_tenant_id_not_null`, `test_mensaje_soft_delete`
- [x] 3.6 Execute tests: confirm all pass

## 4. Schemas Pydantic — Perfil

- [x] 4.1 Implementar `backend/app/schemas/perfil.py` con `model_config = ConfigDict(extra='forbid', from_attributes=True)`:
  - `PerfilResponse`: id, tenant_id, nombre, apellidos, email (desde auth_user), dni, cuil, banco, cbu, alias_cbu, regional, legajo, legajo_profesional, facturador, estado, created_at, updated_at
  - `PerfilUpdateRequest`: nombre (str?, max 120), apellidos (str?, max 120), dni (str?, optional), banco (str?, max 80), cbu (str?, optional), alias_cbu (str?, optional), regional (str?, max 80), legajo_profesional (str?, max 30), facturador (bool?, optional). NO incluye cuil.
- [x] 4.2 RED: Write `tests/test_perfil_schemas.py` — `test_perfil_update_rejects_cuil` verifica que enviar `cuil` en PerfilUpdateRequest da 422 por `extra='forbid'`
- [x] 4.3 TRIANGULATE: Add `test_perfil_update_rejects_extra_fields`, `test_perfil_update_partial_fields`, `test_perfil_response_includes_cuil`, `test_perfil_update_nombre_max_length`, `test_perfil_update_banco_max_length`
- [x] 4.4 Execute tests: confirm all pass

## 5. Schemas Pydantic — Mensajes

- [x] 5.1 Implementar `backend/app/schemas/mensajes.py` con `model_config = ConfigDict(extra='forbid', from_attributes=True)`:
  - `MensajeCreateRequest`: recipient_id (UUID, required), asunto (str, max 250), cuerpo (str, required, max 5000)
  - `MensajeReplyRequest`: cuerpo (str, required, max 5000)
  - `MensajeResponse`: id, sender_id, sender_nombre, recipient_id, recipient_nombre, parent_id, asunto, cuerpo, leido, leido_at, created_at
  - `InboxThreadResponse`: thread_id (id del mensaje raíz), asunto, sender_nombre, last_message_preview (str), message_count (int), unread_count (int), last_activity (datetime)
  - `ThreadDetailResponse`: thread (MensajeResponse — mensaje raíz), replies (list[MensajeResponse] — ordenadas por created_at ASC)
- [x] 5.2 RED: Write `tests/test_mensaje_schemas.py` — `test_mensaje_create_rejects_missing_recipient` verifica 422 sin recipient_id
- [x] 5.3 TRIANGULATE: Add `test_mensaje_create_rejects_empty_cuerpo`, `test_mensaje_cuerpo_max_length`, `test_mensaje_asunto_max_length`, `test_mensaje_reply_requires_cuerpo`, `test_mensaje_create_rejects_extra_fields`
- [x] 5.4 Execute tests: confirm all pass

## 6. PerfilService — RED → GREEN → TRIANGULATE

- [x] 6.1 RED: Write failing test `tests/test_perfil_service.py` — `test_get_perfil_returns_own_data` verifica que obtener perfil devuelve datos del usuario autenticado (nombre, apellidos, email desde auth_user, PII descifrada)
- [x] 6.2 GREEN: Implementar `backend/app/services/perfil_service.py` — `PerfilService` con:
  - `get_perfil(user_id, tenant_id)` — obtiene Usuario + AuthUser (join), descifra PII, retorna PerfilResponse
  - `update_perfil(user_id, tenant_id, request: PerfilUpdateRequest)` — actualiza solo campos provistos en el request (partial update). Si request incluye `facturador`, lo actualiza. NUNCA modifica `cuil`. Cifra PII antes de persistir. Audita `PERFIL_EDITAR`.
- [x] 6.3 Execute tests: confirm GREEN
- [x] 6.4 TRIANGULATE: Add `test_update_perfil_nombre`, `test_update_perfil_banco`, `test_update_perfil_cbu_cifrado_roundtrip`, `test_update_perfil_cuil_no_modificable`, `test_update_perfil_facturador`, `test_update_perfil_partial_solo_nombre`, `test_update_perfil_audit`
- [x] 6.5 Execute tests: confirm all pass

## 7. MensajeService — RED → GREEN → TRIANGULATE

- [x] 7.1 RED: Write failing test `tests/test_mensaje_service.py` — `test_enviar_mensaje_crea_raiz` verifica que enviar un mensaje crea un Mensaje con parent_id=NULL y audita `MENSAJE_ENVIAR`
- [x] 7.2 GREEN: Implementar `backend/app/services/mensaje_service.py` — `MensajeService` con:
  - `enviar_mensaje(sender_id, tenant_id, request: MensajeCreateRequest)` — crea mensaje raíz (parent_id=NULL), setea leido=False, audita `MENSAJE_ENVIAR`. Valida que recipient existe en el tenant.
  - `listar_inbox(user_id, tenant_id, offset, limit)` — retorna hilos (mensajes raíz donde recipient_id = user_id), con último mensaje, contadores y orden por actividad descendente
  - `ver_hilo(thread_id, user_id, tenant_id)` — retorna mensaje raíz + respuestas. Valida que el usuario es sender o recipient del hilo. Marca mensajes del usuario como leídos.
  - `responder(thread_id, sender_id, tenant_id, request: MensajeReplyRequest)` — crea respuesta con parent_id=thread_id. Hereda asunto del mensaje raíz. Audita `MENSAJE_ENVIAR`.
- [x] 7.3 Execute tests: confirm GREEN
- [x] 7.4 TRIANGULATE: Add `test_enviar_mensaje_recipient_no_existe_404`, `test_enviar_mensaje_audit`, `test_listar_inbox_solo_hilos_propios`, `test_inbox_ordenado_por_actividad`, `test_inbox_thread_con_unread_count`, `test_ver_hilo_marca_como_leido`, `test_ver_hilo_incluye_respuestas`, `test_ver_hilo_ajeno_404`, `test_responder_en_hilo`, `test_responder_hilo_no_existe_404`, `test_responder_audit`, `test_inbox_tenant_isolation`
- [x] 7.5 Execute tests: confirm all pass

## 8. MensajeRepository — RED → GREEN → TRIANGULATE

- [x] 8.1 RED: Write failing test `tests/test_mensaje_repository.py` — `test_create_mensaje_persists` verifica que se persiste un mensaje con UUID y timestamps
- [x] 8.2 GREEN: Implementar `backend/app/repositories/mensaje_repository.py` — `MensajeRepository` con:
  - `create(mensaje)` — inserta nuevo mensaje
  - `get_threads_for_user(user_id, tenant_id, offset, limit)` — mensajes raíz (parent_id IS NULL, recipient_id = user_id). Para cada thread: último mensaje, count de mensajes totales, count de no leídos. Ordenado por actividad descendente.
  - `get_thread_detail(thread_id, tenant_id)` — mensaje raíz + mensajes con parent_id = thread_id, ordenados por created_at ASC
  - `mark_as_read(message_id, tenant_id)` — UPDATE leido=True, leido_at=now()
  - `mark_thread_as_read(thread_id, user_id, tenant_id)` — UPDATE leido=True, leido_at=now() para todos los mensajes del hilo donde recipient_id=user_id
- [x] 8.3 Execute tests: confirm GREEN
- [x] 8.4 TRIANGULATE: Add `test_get_threads_for_user_returns_only_roots`, `test_get_threads_for_user_tenant_isolation`, `test_get_threads_pagination`, `test_get_thread_detail_includes_replies`, `test_get_thread_detail_ordered_asc`, `test_mark_as_read_sets_timestamp`, `test_mark_thread_as_read_only_recipient`, `test_mark_thread_as_read_does_not_affect_sender`
- [x] 8.5 Execute tests: confirm all pass

## 9. Router de Perfil — RED → GREEN → TRIANGULATE

- [x] 9.1 RED: Write failing integration test `tests/test_perfil_router.py` — `test_get_perfil_200` GET /api/perfil retorna 200 con PerfilResponse incluyendo email y PII descifrada
- [x] 9.2 GREEN: Implementar `backend/app/api/v1/routers/perfil.py` con:
  - `GET /api/perfil` → `require_permission("perfil:editar")` → `PerfilService.get_perfil()`
  - `PUT /api/perfil` → `require_permission("perfil:editar")` → `PerfilService.update_perfil()`
- [x] 9.3 Execute tests: confirm GREEN
- [x] 9.4 TRIANGULATE: Add `test_put_perfil_actualiza_nombre`, `test_put_perfil_rechaza_cuil`, `test_put_perfil_parcial`, `test_get_perfil_sin_auth_401`, `test_perfil_tenant_isolation`, `test_put_perfil_facturador`
- [x] 9.5 Execute tests: confirm all pass

## 10. Router de Inbox — RED → GREEN → TRIANGULATE

- [x] 10.1 RED: Write failing integration test `tests/test_inbox_router.py` — `test_post_inbox_201` POST /api/inbox retorna 201 con MensajeResponse
- [x] 10.2 GREEN: Implementar `backend/app/api/v1/routers/inbox.py` con:
  - `GET /api/inbox` → `require_permission("mensajeria:usar")` → `MensajeService.listar_inbox()` con query params offset/limit
  - `GET /api/inbox/{thread_id}` → `require_permission("mensajeria:usar")` → `MensajeService.ver_hilo()`
  - `POST /api/inbox` → `require_permission("mensajeria:usar")` → `MensajeService.enviar_mensaje()`
  - `POST /api/inbox/{thread_id}/reply` → `require_permission("mensajeria:usar")` → `MensajeService.responder()`
- [x] 10.3 Execute tests: confirm GREEN
- [x] 10.4 TRIANGULATE: Add `test_get_inbox_lista_hilos`, `test_get_inbox_sin_auth_401`, `test_get_inbox_vacio`, `test_get_thread_detail`, `test_get_thread_detail_ajeno_404`, `test_post_reply`, `test_post_reply_hilo_inexistente`, `test_inbox_tenant_isolation`
- [x] 10.5 Execute tests: confirm all pass

## 11. Registro de routers en main.py

- [x] 11.1 Agregar imports de routers perfil e inbox en `backend/app/main.py`
- [x] 11.2 Registrar routers con `app.include_router(...)` bajo prefijo `/api`
- [x] 11.3 Write smoke tests: `test_perfil_router_registered` (401, no 404) y `test_inbox_router_registered` (401, no 404)
- [x] 11.4 Execute tests: confirm all pass

## 12. Logout reference (F11.3 — ya implementado)

- [x] 12.1 Verificar que `POST /api/auth/logout` de C-03 está operativo y con cobertura de tests
- [x] 12.2 Si no tiene test dedicado para F11.3, agregar `test_logout_invalida_sesion` en `tests/test_auth.py`
- [x] 12.3 Execute tests: confirm pass

## 13. Verificación final

- [x] 13.1 Run full test suite: `pytest -q` from `backend/` — confirm all tests pass
- [x] 13.2 Run ruff linter: confirm sin errores en nuevos archivos
- [x] 13.3 Verificar que los archivos nuevos no exceden 500 LOC
- [x] 13.4 Confirmar que existe UNA sola migración para la tabla mensaje
- [x] 13.5 Confirmar que PII no se expone en logs (revisar PerfilService.get_perfil)
