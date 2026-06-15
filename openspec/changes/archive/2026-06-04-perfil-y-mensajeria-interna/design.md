## Context

C-07 (usuarios-y-asignaciones) entregó el modelo Usuario con PII cifrada (dni, cuil, cbu, alias_cbu) y el modelo AuthUser con el email. C-03 (auth-jwt-2fa) entregó el endpoint de logout. Ahora C-20 introduce dos capacidades nuevas: edición del perfil propio (F11.1) y mensajería interna entre usuarios registrados (F3.4, F11.2, FL-10). También referencia el cierre de sesión (F11.3) que ya está implementado en C-03.

El diseño sigue los flujos FL-10 (mensajería interna), las funcionalidades F3.4 y F11.1-F11.2, y el modelo E4 Usuario del KB. Governance es **BAJO**: CRUD sobre datos propios del usuario y mensajería interna sin impacto en seguridad ni tenant isolation (se hereda del BaseModelMixin). La auditoría es obligatoria en escrituras.

## Goals / Non-Goals

**Goals:**
- Endpoint GET/PUT `/api/perfil` con guard `perfil:editar` para todos los roles autenticados
- PerfilService que lee/escribe campos editables del Usuario, respetando cifrado PII y CUIL solo lectura
- Modelo Mensaje con parent_id auto-referencial para formar hilos de conversación
- MensajeService: enviar mensaje (nuevo hilo), listar inbox (hilos recibidos), ver hilo, responder
- Routers `/api/perfil` y `/api/inbox` con guards `perfil:editar` y `mensajeria:usar`
- Una migración Alembic para la tabla `mensaje` con seed de permisos
- Schemas Pydantic v2 con `extra='forbid'`, `from_attributes=True`
- Códigos de auditoría: `PERFIL_EDITAR`, `MENSAJE_ENVIAR`

**Non-Goals:**
- Edición de email desde el perfil — el email vive en `auth_user` y su modificación requiere flujo de verificación (fuera del scope de C-20)
- Edición de CUIL — es solo lectura desde este endpoint; requiere ADMIN vía `/api/admin/usuarios`
- Notificaciones push/email cuando llega un mensaje nuevo — C-12 (comunicaciones)
- Frontend UI — C-23 (frontend-coordinacion) y C-22 (frontend-academico-docente)
- Mensajería a ALUMNO — F3.4 lista TUTOR, PROFESOR, COORDINADOR, ADMIN como destinatarios. F11.2 dice "cualquier usuario autenticado". Se adopta F11.2 (todos los roles) como scope más amplio.

## Decisions

### D1 — Mensaje con parent_id auto-referencial para formar hilos

Cada Mensaje tiene un `parent_id` (FK → mensaje.id, nullable). Un mensaje con `parent_id = NULL` es la raíz de un hilo. Las respuestas tienen `parent_id` apuntando al mensaje que responden.

```
Mensaje {
  id, tenant_id,
  sender_id, recipient_id,
  parent_id (nullable FK → mensaje.id),
  asunto, cuerpo, leido (bool), leido_at,
  created_at, updated_at, deleted_at
}
```

**Why parent_id over thread_id explícito?**
- Un `thread_id` explícito duplica información: el thread_id de la raíz es su propio id
- parent_id es más natural para consultas recursivas: "dame todos los mensajes cuyo ancestro raíz es X"
- Para listar hilos en el inbox: `SELECT ... WHERE parent_id IS NULL AND recipient_id = ? ORDER BY created_at DESC`
- Para ver un hilo: `SELECT ... WHERE id = ? OR parent_id = ? ORDER BY created_at ASC` (dos niveles; los hilos son chat-style, no deeply nested)
- Si en el futuro se requiere nesting profundo, se puede agregar `thread_root_id` sin romper backward compatibility

### D2 — Inbox lista hilos, no mensajes individuales

GET `/api/inbox` devuelve los hilos donde el usuario es destinatario del mensaje raíz. Cada item del inbox es un resumen del hilo: último mensaje, cantidad de mensajes en el hilo, indicador de no leídos.

**Why threads, not messages?**
- FL-10 paso 2: "El destinatario accede a su inbox y ve los hilos activos"
- La KB habla consistentemente de "hilos de mensajes", no de mensajes planos
- Un inbox de mensajes planos se vuelve ilegible con múltiples respuestas en una conversación
- Agrupar por hilo sigue el patrón estándar de cualquier cliente de mensajería

### D3 — Thread detail incluye el árbol completo en una sola respuesta

GET `/api/inbox/{thread_id}` devuelve el mensaje raíz (`thread_id`) y todas las respuestas (mensajes cuyo `parent_id` apunta a cualquier mensaje del hilo). Para la primera versión, se asume un solo nivel de anidamiento (respuestas directas al mensaje raíz).

**Why flat list with parent references, not nested JSON tree?**
- La mensajería interna es chat-style (pregunta-respuesta), no jerárquica
- Un flat list ordenado por created_at ASC es más simple de consumir para el frontend
- Si en el futuro se necesita nesting, se puede agregar un flag `?format=tree`

### D4 — leido a nivel de mensaje, no de hilo

El campo `leido` (bool, default False) está en cada Mensaje. Al abrir un hilo, todos los mensajes dirigidos al usuario se marcan como leídos. El inbox muestra un contador de mensajes no leídos por hilo.

**Why per-message, not per-thread?**
- Permite saber exactamente qué mensajes nuevos hay en un hilo activo
- Si un hilo tiene 10 mensajes y el usuario ya leyó 7, el contador muestra 3
- Más granularidad para futuras features (marcar como no leído, leer un mensaje específico)

### D5 — CUIL validado como solo lectura en el servicio, no en el schema

El PerfilUpdateRequest no incluye el campo `cuil`. Si el request body incluye `cuil` (vía `extra='forbid'`), Pydantic rechaza con 422. Esto da dos capas de protección: Pydantic rechaza el campo desconocido, y aunque alguien modificara el schema, el PerfilService ignora explícitamente cualquier intento de modificar `cuil`.

**Why not include cuil as read-only in response only?**
- Si `cuil` estuviera en PerfilUpdateRequest como Optional, un cliente podría enviarlo y potencialmente ser procesado
- `extra='forbid'` + campo ausente del schema de update es la defensa más robusta
- El GET response incluye `cuil` (descifrado para el dueño) pero el PUT request no lo acepta

### D6 — Email no editable desde perfil

El email vive en `auth_user.email`, no en `usuario`. Modificar el email requiere verificación (no implementada en C-20) y potencialmente afecta el login. Se excluye del scope de perfil.

**Why not add email editing now?**
- El email es la credencial de login — cambiarlo sin re-verificación es un riesgo de seguridad
- Requiere un flujo de confirmación (token al email nuevo + token al email viejo) que no está en el scope de C-20
- Se puede agregar en un change futuro como "cambio de email con verificación"

### D7 — PII se descifra en el servicio para respuesta del perfil

Al hacer GET `/api/perfil`, el PerfilService lee los campos cifrados del Usuario (dni, cuil, cbu, alias_cbu) y los descifra antes de devolverlos en la respuesta. Esto es seguro porque:
- Solo el dueño del perfil puede ver sus propios datos (el endpoint siempre devuelve el perfil del usuario autenticado)
- La respuesta viaja por HTTPS
- Los logs no deben incluir el body de respuesta (configuración de logging)

**Why not devolverlos cifrados?**
- El frontend los necesita en texto plano para mostrarlos en el formulario de edición
- El cifrado es en reposo (DB), no en tránsito (API → frontend via HTTPS)

### D8 — Permiso `mensajeria:usar` para todos los roles autenticados

Aunque F3.4 lista solo TUTOR, PROFESOR, COORDINADOR, ADMIN, F11.2 dice "cualquier usuario autenticado". Se adopta el scope más amplio de F11.2. El permiso `mensajeria:usar` se otorga a los 7 roles del sistema: ALUMNO, TUTOR, PROFESOR, COORDINADOR, NEXO, ADMIN, FINANZAS.

**Why todos los roles?**
- La KB es explícita en F11.2: "Quién: cualquier usuario autenticado"
- Restringir a ciertos roles requeriría confirmación del stakeholder
- Si en el futuro se quiere restringir, basta con remover el permiso de ciertos roles en el seed — sin cambios de código

### D9 — Cierre de sesión (F11.3) reusa C-03

F11.3 pide cierre de sesión explícito. C-03 ya implementó `POST /api/auth/logout` con revocación de sesión. No se requiere código nuevo. La tarea correspondiente en tasks.md referencia este hecho y se marca como "ya implementado — verificar cobertura".

### D10 — MensajeRepository con queries optimizadas para hilos

El repository implementa:
- `create(mensaje)` — inserta nuevo mensaje
- `get_threads_for_user(user_id, tenant_id, offset, limit)` — mensajes raíz donde recipient_id = user_id, con subquery de último mensaje y contadores, ordenados por actividad descendente
- `get_thread_detail(thread_id, tenant_id)` — mensaje raíz + todas las respuestas directas (parent_id = thread_id), ordenadas por created_at ASC
- `mark_as_read(message_id, tenant_id)` — marca un mensaje como leído
- `mark_thread_as_read(thread_id, user_id, tenant_id)` — marca todos los mensajes del hilo dirigidos al usuario como leídos

## Risks / Trade-offs

- **[Riesgo] Exposición de PII en logs** → Los campos cifrados (cuil, dni, cbu, alias_cbu) se descifran para la respuesta del perfil. **Mitigación**: el logging service ya omite request/response bodies. El PerfilService no loguea campos individuales.
- **[Riesgo] Hilos con nesting profundo** → El diseño actual asume 1 nivel de nesting (respuesta directa al mensaje raíz). Si los usuarios empiezan a responder respuestas, la query `WHERE parent_id = ?` solo trae 1 nivel. **Mitigación**: esto es aceptable para mensajería chat-style. Si se necesita nesting, se puede migrar a recursive CTE sin cambio de schema.
- **[Trade-off] Sin soft-delete en cascada para mensajes** → Si un usuario es soft-deleteado, sus mensajes permanecen (el receptor aún necesita ver el historial). Esto es intencional — los mensajes son registro histórico de comunicación.

## Migration Plan

1. Crear migración con `op.create_table` para `mensaje` con todos los campos, FKs (sender_id → usuario, recipient_id → usuario, parent_id → mensaje), e índices (recipient_id, parent_id, created_at)
2. Seed de permisos: insertar `perfil:editar` y `mensajeria:usar` en `permiso` y asociarlos a los 7 roles en `rol_permiso`
3. Rollback: `downgrade()` hace `op.drop_table` y elimina los registros de `rol_permiso` y `permiso`

## Open Questions

- **¿ALUMNO debe poder usar mensajería?** F11.2 dice "cualquier usuario autenticado" (incluye ALUMNO), pero F3.4 lista solo TUTOR, PROFESOR, COORDINADOR, ADMIN. Se adopta F11.2 (todos los roles) como scope más amplio, pero si el stakeholder prefiere restringir, se ajusta el seed de permisos sin cambios de código.
- **¿La mensajería es 1:1 o permite múltiples destinatarios?** La KB describe mensajes entre un emisor y un receptor (sender_id, recipient_id). No menciona grupos ni múltiples destinatarios. Se implementa como 1:1.
- **¿Se necesita marcar mensajes como no leídos?** La KB solo menciona "leer" y "responder". No menciona "marcar como no leído". Se omite por ahora.
