## 1. Schemas — Response DTOs

- [x] 1.1 Crear `backend/app/schemas/auditoria.py` con todos los DTOs de respuesta: `AccionPorDia`, `AccionesPorDiaResponse`, `EstadoPorDocente`, `EstadoComunicacionesResponse`, `InteraccionRow`, `InteraccionesResponse`, `UltimaAccionResponse`, `UltimasAccionesResponse`, `AuditoriaLogResponse` (extendido con `actor_nombre`, `materia_nombre`), `AuditoriaLogListResponse`. Todos con `model_config = ConfigDict(extra='forbid')`.

## 2. Repository — Aggregation queries

- [x] 2.1 Agregar `count_by_day()` al `AuditLogRepository`: query GROUP BY `DATE(fecha_hora)` con filtros `fecha_desde`, `fecha_hasta`, `actor_id` opcional. Retorna `list[dict]` con `{dia: date, total_acciones: int}`.
- [x] 2.2 Agregar `count_by_actor_materia_accion()` al `AuditLogRepository`: query GROUP BY `(actor_id, materia_id, accion)` con filtros `fecha_desde`, `fecha_hasta`, `actor_id` opcional. Retorna `list[dict]` con campos agregados.
- [x] 2.3 Agregar `list_with_join()` al `AuditLogRepository`: idéntico a `list()` existente pero con LEFT JOIN a `auth_user` y `materia` para resolver nombres en una sola query. Acepta filtro adicional `ip` (LIKE partial match), `usuario_id` (alias para `actor_id`), y `materia_id`.
- [x] 2.4 Agregar `count_with_filters()` al `AuditLogRepository`: igual que `count()` existente pero con los filtros adicionales de `list_with_join()`.

## 3. Service — MetricsService

- [x] 3.1 Crear `backend/app/services/auditoria/__init__.py` (vacío).
- [x] 3.2 Crear `backend/app/services/auditoria/metrics_service.py` con la clase `MetricsService`:
  - Constructor recibe `session`, `tenant_id`, `user_id`, `is_global_scope`.
  - Método `acciones_por_dia(fecha_desde, fecha_hasta)` → delega a `AuditLogRepository.count_by_day()` con scope aplicado. Default: últimos 30 días si no se especifica rango.
  - Método `interacciones_por_docente_materia(fecha_desde, fecha_hasta, usuario_id?)` → delega a `AuditLogRepository.count_by_actor_materia_accion()` con scope aplicado. Resuelve nombres de usuario y materia.
  - Método `ultimas_acciones(limit?, fecha_desde?, fecha_hasta?, usuario_id?, materia_id?)` → delega a `AuditLogRepository.list_with_join()`. Cap limit a 1000, default 200. Aplica scope.
  - Método `estado_comunicaciones_por_docente(fecha_desde, fecha_hasta, materia_id?)` → query directa sobre modelo `Comunicacion` (E21) con GROUP BY `(enviado_por, materia_id, estado)`. Con try/except ImportError para manejar ausencia del modelo pre-C-12.
- [x] 3.3 Método auxiliar `_apply_propio_scope()` — si `not is_global_scope`, filtra por `actor_id == user_id` (o `enviado_por == user_id` para comunicaciones).

## 4. Router — Endpoints

- [x] 4.1 Crear `backend/app/api/v1/routers/auditoria.py` con `APIRouter(prefix="/api/auditoria", tags=["auditoria"])`.
- [x] 4.2 `GET /panel/acciones-por-dia` — query params `fecha_desde`, `fecha_hasta` (opcionales). Guard: `require_permission_return_user("auditoria:ver")`. Construye `MetricsService` con scope derivado de roles (ADMIN/FINANZAS = global, resto = propio).
- [x] 4.3 `GET /panel/estado-comunicaciones` — query params `fecha_desde`, `fecha_hasta` (opcionales, default últimos 30 días), `materia_id` (opcional). Mismo guard y scope.
- [x] 4.4 `GET /panel/interacciones` — query params `fecha_desde`, `fecha_hasta` (opcionales, default últimos 30 días), `usuario_id` (opcional). Mismo guard y scope.
- [x] 4.5 `GET /panel/ultimas-acciones` — query params `limit` (default 200, max 1000), `fecha_desde`, `fecha_hasta`, `usuario_id`, `materia_id` (todos opcionales). Mismo guard y scope.
- [x] 4.6 `GET /log` — query params heredados de C-05 (`accion`, `fecha_desde`, `fecha_hasta`, `offset`, `limit`) más nuevos (`usuario_id`, `materia_id`, `ip`). Mismo guard y scope. Retorna `AuditoriaLogListResponse` con nombres resueltos.
- [x] 4.7 Registrar el router en `backend/app/api/v1/routers/__init__.py` y en `main.py` (si aplica).

## 5. Tests — panel-interacciones

- [x] 5.1 Tests para `acciones_por_dia`: rango default 30 días, rango personalizado, COORDINADOR scope filtrado, ADMIN scope global, sin datos (array vacío).
- [x] 5.1b **(CRÍTICO)** Test de aislamiento de scope: crear audit logs de dos usuarios distintos en mismo tenant. Verificar que COORDINADOR (user A) solo ve sus propias acciones y NUNCA las de user B. Verificar que ADMIN ve ambas. Aplicar en TODOS los endpoints del panel.
- [x] 5.2 Tests para `estado_comunicaciones_por_docente`: sin filtro (todos), filtrado por materia, COORDINADOR scope, ADMIN scope, tabla comunicacion sin datos (respuesta vacía), tabla comunicacion no disponible (ImportError manejado).
- [x] 5.3 Tests para `interacciones_por_docente_materia`: agrupación correcta por (actor, materia, acción), COORDINADOR scope, ADMIN scope, sin datos.
- [x] 5.4 Tests para `ultimas_acciones`: default 200, custom limit, cap a 1000, filtro por fecha, filtro por usuario, filtro por materia, COORDINADOR scope, resolución de nombres (actor_nombre, materia_nombre).

## 6. Tests — log-completo-auditoria

- [x] 6.1 Tests para `GET /log`: sin filtros (paginación default), filtro por fecha_desde/fecha_hasta, filtro por materia_id, filtro por usuario_id, filtro por accion, filtro por ip (partial match), filtros combinados, paginación offset/limit, COORDINADOR scope (solo propios), ADMIN scope (todos), 403 sin permiso, 405 en POST/PUT/DELETE.
- [x] 6.2 Tests para resolución de nombres: actor_nombre presente, materia_nombre presente, actor eliminado (nombre null), materia null (nombre null).
- [x] 6.3 Verificar que la suite completa de tests pasa (`pytest -q` desde `backend/`).

## 7. Verification

- [x] 7.1 Ejecutar linter y type-checker (si están configurados en el proyecto).
- [x] 7.2 Verificar cobertura ≥80% líneas en los nuevos archivos.
- [x] 7.3 Verificar que el endpoint `estado_comunicaciones_por_docente` maneja graceful degradation si C-12 no está deployado.
