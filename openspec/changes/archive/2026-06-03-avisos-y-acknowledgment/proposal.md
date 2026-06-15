## Why

El sistema carece de un tablón de avisos institucionales que permita a COORDINADOR y ADMIN comunicar novedades a segmentos específicos de usuarios (por materia, cohorte, rol, o global), con control de vigencia temporal (RN-18), segmentación de audiencia (RN-20), y confirmación de lectura obligatoria cuando corresponda (RN-19). Sin este módulo, operaciones críticas como el FL-03 (setup de cuatrimestre) quedan incompletas — el paso 7 "publicar aviso de bienvenida" no tiene soporte.

## What Changes

- **Modelos `Aviso` y `AcknowledgmentAviso`** — nuevas tablas en el schema de BD. `Aviso` define el mensaje institucional con alcance (Global/PorMateria/PorCohorte/PorRol), severidad (Info/Advertencia/Crítico), ventana de vigencia (`inicio_en`, `fin_en`), prioridad (`orden`), flag `requiere_ack`, y estado `activo`. `AcknowledgmentAviso` registra la confirmación de lectura por usuario, y es la fuente de verdad para todos los contadores (no hay campos denormalizados en Aviso).
- **Migración Alembic** — nueva migración `0NN_create_aviso_acknowledgment.py` con índices para filtrado por audiencia.
- **AvisoService** — lógica de dominio: ABM de avisos, filtrado de avisos visibles para un usuario dado (según su rol, cohorte, y materias asignadas), validación de ventana de vigencia activa, confirmación de lectura (ack), y cálculo de contadores (vistas/acknowledgments) desde AcknowledgmentAviso.
- **`/api/avisos/*` router** — endpoints bajo prefix `/api/avisos`:
  - `POST /api/avisos` — crear aviso (guard `avisos:publicar`, COORDINADOR/ADMIN)
  - `PUT /api/avisos/{aviso_id}` — editar aviso existente
  - `DELETE /api/avisos/{aviso_id}` — soft-delete aviso
  - `GET /api/avisos` — listar avisos visibles para el usuario autenticado (filtrado por rol/alcance/cohorte/asignación + ventana de vigencia activa)
  - `GET /api/avisos/{aviso_id}` — detalle de un aviso
  - `POST /api/avisos/{aviso_id}/ack` — confirmar lectura (acknowledge) de un aviso que lo requiera
  - `GET /api/avisos/{aviso_id}/ack/stats` — contadores de vistas y confirmaciones
- **AvisoSchema** (Pydantic v2) — request/response DTOs con `extra='forbid'` para create/update/response/ack.
- **Auditoría** — códigos `AVISO_PUBLICAR`, `AVISO_MODIFICAR`, `AVISO_ELIMINAR`, `AVISO_CONFIRMAR`.
- **Seed de permisos** — `avisos:publicar` en roles COORDINADOR y ADMIN.

## Capabilities

### New Capabilities
- `avisos-crud`: ABM de avisos (F3.5). Crear, editar, soft-delete y consultar avisos por COORDINADOR/ADMIN. Incluye validación de alcance, severidad, vigencia, y orden.
- `avisos-visualizacion`: Visualización de avisos por destinatario (RN-18, RN-20). Filtrado por rol del usuario autenticado, materias y cohortes asignadas, ventana de vigencia activa (`inicio_en` ≤ now ≤ `fin_en`), y estado `activo=true`. Ordenados por prioridad (`orden`) descendente y luego por fecha de inicio. Los avisos con `requiere_ack=true` que ya fueron confirmados por el usuario no se muestran en el listado principal.
- `avisos-acknowledgment`: Confirmación de lectura (RN-19). Registro de `AcknowledgmentAviso` cuando el usuario confirma un aviso que requiere acuse de recibo. Contadores de vistas totales y confirmaciones derivados de la tabla `AcknowledgmentAviso` (no denormalizados).

### Modified Capabilities
<!-- None — los permisos avisos:publicar (COORDINADOR/ADMIN) y aviso:confirmar (todos los roles) ya existen en el seed de rbac-seed -->
Ninguna.

## Impact

- **New models**: `backend/app/models/aviso.py`, `backend/app/models/acknowledgment_aviso.py` — modelos SQLAlchemy async
- **New migration**: `backend/alembic/versions/0NN_create_aviso_acknowledgment.py`
- **New schemas**: `backend/app/schemas/avisos.py` — `AvisoCreateRequest`, `AvisoUpdateRequest`, `AvisoResponse`, `AvisoListItemResponse`, `AckResponse`, `AckStatsResponse`
- **New repository**: `backend/app/repositories/aviso_repository.py`
- **New service**: `backend/app/services/aviso_service.py`
- **New router**: `backend/app/api/v1/routers/avisos.py` — prefix `/api/avisos`
- **Modified**: `backend/app/main.py` — registrar avisos router
- **Modified**: `backend/app/core/seed/permisos.py` — agregar `avisos:publicar` al seed
- **Modified**: `backend/app/core/audit_codes.py` — agregar `AVISO_PUBLICAR`, `AVISO_MODIFICAR`, `AVISO_ELIMINAR`, `AVISO_CONFIRMAR`
- **Dependencies**: C-06 estructura-academica ✅ (Materia, Cohorte existen), C-04 rbac ✅ (permisos finos), C-07 usuarios-y-asignaciones ✅ (Usuario, Asignacion para resolver qué materias/cohortes ve un usuario)
