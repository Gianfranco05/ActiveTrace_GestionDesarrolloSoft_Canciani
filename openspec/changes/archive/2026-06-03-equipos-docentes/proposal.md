## Why

C-07 entregó Usuario y Asignacion como el puente entre identidad y autorización. Ahora los actores del sistema (PROFESOR, TUTOR, NEXO, COORDINADOR, ADMIN) necesitan **operar sobre los equipos docentes** — ver sus propias asignaciones, gestionar equipos completos, clonar entre períodos, modificar vigencias en bloque y exportar.

Sin C-08 los coordinadores deben manipular asignaciones una por una vía CRUD, no existe "mis equipos" para que un docente vea dónde está asignado, y el FL-03 (setup de cuatrimestre) no puede clonar equipos entre cohortes — operación crítica cada inicio de período.

## What Changes

- **EquipoService** — servicio de dominio que orquesta las 5 operaciones nuevas sobre Asignacion: listado por usuario, gestión individual, asignación masiva, clonación entre cohortes, modificación de vigencia en bloque, exportación.
- **`/api/equipos/*` router** — endpoints bajo prefix `/api/equipos` con guard `equipos:asignar` (COORDINADOR, ADMIN). El endpoint de mis-equipos permite acceso también a PROFESOR, TUTOR, NEXO (lectura propia).
- **Mis equipos (F4.2)** — GET /api/equipos/mis-equipos devuelve las asignaciones activas del usuario autenticado, filtrable por estado, materia, rol, carrera, cohorte.
- **Gestión de asignaciones (F4.3)** — CRUD sobre el conjunto completo de asignaciones del tenant, con filtros por materia, carrera, cohorte, usuario, rol. Reusa los schemas de C-07 pero expone más filtros y vistas.
- **Asignación masiva (F4.4)** — POST /api/equipos/masiva acepta una combinación materia × carrera × cohorte × rol × vigencia y una lista de usuarios, crea todas las asignaciones en una transacción. Incluye búsqueda con autocompletado de usuarios.
- **Clonar equipo entre períodos (F4.5, RN-12)** — POST /api/equipos/clonar duplica asignaciones vigentes de un origen (materia × carrera × cohorte) a un destino con nuevas fechas de vigencia. Las nuevas asignaciones apuntan al mismo responsable_id (resuelto contra las nuevas).
- **Modificar vigencia general (F4.6)** — PATCH /api/equipos/{equipo_id}/vigencia actualiza vig_desde/vig_hasta de todas las asignaciones de un equipo (materia × carrera × cohorte) en una operación.
- **Exportar equipo (F4.7)** — GET /api/equipos/{equipo_id}/export devuelve un archivo descargable (CSV/XLSX) con el detalle de todas las asignaciones del equipo.
- **Auditoría** — todos los endpoints de escritura (masiva, clonar, vigencia) generan auditoría `ASIGNACION_MODIFICAR`.
- **EquipoResponse** — nueva vista schemas que agrupa asignaciones bajo un `equipo_id` compuesto (materia_id + carrera_id + cohorte_id).
- **EquipoService** contiene la lógica de negocio de clonación (transaccional, con re-resolución de responsable_id), validación de vigencia, y generación de export.

## Capabilities

### New Capabilities
- `equipos-listado`: Mis equipos (F4.2) + gestión de asignaciones (F4.3) — endpoints para que el docente vea sus asignaciones y el coordinador administre el conjunto completo
- `equipos-masiva`: Asignación masiva de docentes (F4.4) — bulk create de asignaciones con búsqueda de usuarios
- `equipos-clonar`: Clonar equipo entre períodos (F4.5, RN-12) — duplica asignaciones de cohorte origen a destino
- `equipos-vigencia`: Modificar vigencia general (F4.6) — batch update de vig_desde/vig_hasta para todo un equipo
- `equipos-export`: Exportar equipo docente (F4.7) — descarga CSV/XLSX con detalle de asignaciones

### Modified Capabilities
- `backend/app/repositories/asignacion_repository.py` — nuevos métodos: `get_equipo(materia_id, carrera_id, cohorte_id)`, `get_equipo_export()`, `bulk_create()`, `update_vigencia_batch()`
- `backend/app/schemas/asignaciones.py` — nuevos schemas: `EquipoResponse` (agrupación de asignaciones), `AsignacionMasivaRequest`, `ClonarRequest`, `VigenciaUpdateRequest`
- `backend/app/models/asignacion.py` — sin cambios (todo es servicio/repo sobre el modelo existente)

## Impact

- **New service**: `backend/app/services/equipo_service.py` — lógica de negocio de equipos (masiva, clonar, vigencia, export)
- **New router**: `backend/app/api/v1/routers/equipos.py` — prefix `/api/equipos`
- **Modified repository**: `backend/app/repositories/asignacion_repository.py` — bulk queries, batch update
- **Modified schemas**: `backend/app/schemas/asignaciones.py` — nuevos request/response DTOs
- **Modified files**: `backend/app/main.py` — registrar equipos router
- **Export dependency**: `openpyxl` o `csv` nativo para exportación
- **No new migration** — C-08 opera 100% sobre el modelo Asignacion existente (C-07)
- **Dependencies**: `C-07` (Asignacion model, schemas, repository, service), `C-04` (guard `equipos:asignar`)
