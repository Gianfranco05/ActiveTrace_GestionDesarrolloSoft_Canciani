## 1. Migración y Modelos

- [x] 1.1 Crear migración Alembic `0NN_create_aviso_acknowledgment.py` con tabla `aviso` (id UUID PK, tenant_id FK, alcance enum, materia_id FK nullable, cohorte_id FK nullable, rol_destino VARCHAR nullable, severidad enum, titulo VARCHAR 200, cuerpo TEXT, inicio_en TIMESTAMPTZ, fin_en TIMESTAMPTZ, orden INT, activo BOOLEAN, requiere_ack BOOLEAN, created_at, updated_at, deleted_at) y tabla `acknowledgment_aviso` (id UUID PK, aviso_id FK, usuario_id FK, confirmado_at TIMESTAMPTZ, UNIQUE(aviso_id, usuario_id))
- [x] 1.2 Crear modelo SQLAlchemy `backend/app/models/aviso.py` con clase `Aviso` (hereda de Base + TimestampMixin + SoftDeleteMixin, tenant_id + alcance + materia_id + cohorte_id + rol_destino + severidad + titulo + cuerpo + inicio_en + fin_en + orden + activo + requiere_ack)
- [x] 1.3 Crear modelo SQLAlchemy `backend/app/models/acknowledgment_aviso.py` con clase `AcknowledgmentAviso` (hereda de Base, aviso_id + usuario_id + confirmado_at, UniqueConstraint(aviso_id, usuario_id))
- [x] 1.4 Ejecutar migración y verificar que ambas tablas existen en la DB de test

## 2. Schemas Pydantic

- [x] 2.1 Crear `backend/app/schemas/avisos.py` con enums `AlcanceEnum` (Global, PorMateria, PorCohorte, PorRol) y `SeveridadEnum` (Info, Advertencia, Critico)
- [x] 2.2 Agregar `AvisoCreateRequest` con validaciones Pydantic: `alcance` requerido, `titulo` max 200, `inicio_en` y `fin_en` requeridos, `model_config = ConfigDict(extra='forbid')`
- [x] 2.3 Agregar `AvisoUpdateRequest` con todos los campos opcionales, `model_config = ConfigDict(extra='forbid')`
- [x] 2.4 Agregar `AvisoResponse` y `AvisoListItemResponse` con `model_config = ConfigDict(from_attributes=True, extra='forbid')`
- [x] 2.5 Agregar `AvisoDetailResponse` (extiende AvisoResponse con `acknowledged: bool`)
- [x] 2.6 Agregar `AckResponse` (aviso_id, usuario_id, confirmado_at) y `AckStatsResponse` (aviso_id, total_views, total_acks, pendientes_ack)
- [x] 2.7 Tests: validar que `AvisoCreateRequest` rechaza campos extra, requiere `alcance`, trunca `titulo` >200 chars (test unitario de schemas)

## 3. AvisoRepository

- [x] 3.1 Crear `backend/app/repositories/aviso_repository.py` con `AvisoRepository(BaseRepository[Aviso])` — métodos `create`, `get_by_id`, `update`, `soft_delete`
- [x] 3.2 Agregar `list_visibles(tenant_id, usuario_id, offset, limit)` — query de filtrado por audiencia (D2 del design) con subqueries sobre `Asignacion` para resolver materia/cohorte/rol, ventana de vigencia, exclusión de avisos con ack, orden por prioridad
- [x] 3.3 Agregar métodos de AcknowledgmentAviso: `get_ack(aviso_id, usuario_id)`, `create_ack(ack)` con `ON CONFLICT DO NOTHING` (D3), `count_acks(aviso_id)`, `count_distinct_users(aviso_id)`
- [x] 3.4 Tests: `list_visibles` filtra correctamente por alcance Global (todas las asignaciones lo ven), PorMateria (solo asignados), PorCohorte (solo asignados), PorRol (solo rol matching), fuera de vigencia (no aparece), soft-deleted (no aparece), activo=false (no aparece), requiere_ack ya confirmado (no aparece), ordenamiento por prioridad

## 4. AvisoService

- [x] 4.1 Crear `backend/app/services/aviso_service.py` con `AvisoService(session, audit_service)` — constructor con `AvisoRepository`
- [x] 4.2 Implementar `create(data, tenant_id, actor_id)` — validar scope (D6: materia_id si PorMateria, cohorte_id si PorCohorte, rol_destino si PorRol), validar `inicio_en < fin_en`, crear Aviso, auditar `AVISO_PUBLICAR`, retornar `AvisoResponse`
- [x] 4.3 Implementar `update(aviso_id, data, tenant_id, actor_id)` — validar existencia, aplicar cambios parciales, validar scope y vigencia si se modifican, auditar `AVISO_MODIFICAR`, retornar `AvisoResponse`
- [x] 4.4 Implementar `soft_delete(aviso_id, tenant_id, actor_id)` — validar existencia, marcar deleted_at, auditar `AVISO_ELIMINAR`
- [x] 4.5 Implementar `get_by_id(aviso_id, tenant_id, usuario_id)` — obtener aviso, resolver `acknowledged` consultando `get_ack`, retornar `AvisoDetailResponse`
- [x] 4.6 Implementar `list_visibles(usuario_id, tenant_id, offset, limit)` — delegar a `list_visibles` del repo, mapear a `AvisoListItemResponse` con `acknowledged` resuelto por aviso
- [x] 4.7 Implementar `acknowledge(aviso_id, usuario_id, tenant_id)` — validar que el aviso existe, es visible para el usuario (alcance + vigencia), tiene `requiere_ack=true`. Intentar `create_ack`; si devuelve None → consultar existente → 200, si devuelve registro → 201. Auditar `AVISO_CONFIRMAR` solo en creación nueva
- [x] 4.8 Implementar `get_stats(aviso_id, tenant_id)` — delegar a `count_distinct_users` y `count_acks`, calcular `pendientes_ack`, retornar `AckStatsResponse`
- [x] 4.9 Tests unitarios de AvisoService con repo mockeado: create con scope inválido lanza error, acknowledge idempotente, acknowledge en aviso sin requiere_ack lanza error, stats calcula correctamente pendientes_ack

## 5. Router `/api/avisos`

- [x] 5.1 Crear `backend/app/api/v1/routers/avisos.py` con `APIRouter(prefix="/api/avisos", tags=["Avisos"])`
- [x] 5.2 `POST /api/avisos` — requiere `require_permission("avisos:publicar")`, recibe `AvisoCreateRequest`, delega a `AvisoService.create`, retorna 201 `AvisoResponse`
- [x] 5.3 `PUT /api/avisos/{aviso_id}` — requiere `require_permission("avisos:publicar")`, recibe `AvisoUpdateRequest`, delega a `AvisoService.update`, retorna 200 `AvisoResponse`
- [x] 5.4 `DELETE /api/avisos/{aviso_id}` — requiere `require_permission("avisos:publicar")`, delega a `AvisoService.soft_delete`, retorna 204
- [x] 5.5 `GET /api/avisos/{aviso_id}` — requiere `require_authenticated`, delega a `AvisoService.get_by_id`, retorna 200 `AvisoDetailResponse`
- [x] 5.6 `GET /api/avisos` — requiere `require_authenticated`, recibe `offset`/`limit` query params, delega a `AvisoService.list_visibles`, retorna 200 `{"items": [...], "total": N, "offset": N, "limit": N}`
- [x] 5.7 `POST /api/avisos/{aviso_id}/ack` — requiere `require_permission("aviso:confirmar")`, delega a `AvisoService.acknowledge`, retorna 201 (nuevo) o 200 (existente)
- [x] 5.8 `GET /api/avisos/{aviso_id}/ack/stats` — requiere `require_permission("avisos:publicar")`, delega a `AvisoService.get_stats`, retorna 200 `AckStatsResponse`
- [x] 5.9 Registrar router en `backend/app/main.py`

## 6. Auditoría

- [x] 6.1 Agregar códigos de auditoría `AVISO_PUBLICAR`, `AVISO_MODIFICAR`, `AVISO_ELIMINAR`, `AVISO_CONFIRMAR` en `backend/app/core/audit_codes.py`
- [x] 6.2 Verificar que todas las operaciones de escritura generan registro de auditoría con `tenant_id`, `actor_id`, código de acción, `filas_afectadas=1`

## 7. Tests de Integración

- [x] 7.1 Test: POST /api/avisos con COORDINADOR crea aviso y retorna 201
- [x] 7.2 Test: POST /api/avisos sin permisos retorna 403
- [x] 7.3 Test: PUT /api/avisos/{id} actualiza campos parciales y retorna 200
- [x] 7.4 Test: DELETE /api/avisos/{id} soft-delete y retorna 204; siguiente GET retorna 404
- [x] 7.5 Test: GET /api/avisos como PROFESOR retorna solo avisos de sus materias/cohortes + globales + su rol
- [x] 7.6 Test: GET /api/avisos como ALUMNO retorna solo avisos de su cohorte + globales + rol ALUMNO
- [x] 7.7 Test: GET /api/avisos no retorna avisos fuera de ventana de vigencia
- [x] 7.8 Test: GET /api/avisos no retorna avisos con `requiere_ack=true` ya confirmados por el usuario
- [x] 7.9 Test: POST /api/avisos/{id}/ack confirma lectura y retorna 201; segunda vez retorna 200 (idempotente)
- [x] 7.10 Test: POST /api/avisos/{id}/ack en aviso sin `requiere_ack=true` retorna 422
- [x] 7.11 Test: POST /api/avisos/{id}/ack en aviso fuera de vigencia retorna 404
- [x] 7.12 Test: POST /api/avisos/{id}/ack en aviso no visible por scope retorna 404
- [x] 7.13 Test: GET /api/avisos/{id}/ack/stats retorna contadores correctos
- [x] 7.14 Test: GET /api/avisos/{id}/ack/stats sin permisos retorna 403
- [x] 7.15 Test: avisos ordenados por prioridad (`orden` DESC, luego `inicio_en` DESC)
