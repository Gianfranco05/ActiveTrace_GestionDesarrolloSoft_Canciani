## Why

C-06 y C-07 entregaron la estructura académica completa (Carrera, Cohorte, Materia) y el puente Usuario-Asignacion que asigna roles en contextos académicos. Ahora el sistema necesita soportar el ciclo completo de **evaluaciones y coloquios**: que el COORDINADOR cree convocatorias con días y cupos, importe alumnos elegibles, que el ALUMNO reserve su turno, se registren resultados, y se consolide métricas operativas.

Sin C-14 no existe forma de gestionar instancias de evaluación en el sistema. Los flujos FL-07 (coloquio), F7.1-F7.5 (épica completa de coloquios) y las HUs 30-33 + 47 quedan sin implementar.

## What Changes

- **Modelos nuevos**: `Evaluacion` (E14), `ReservaEvaluacion`, `ResultadoEvaluacion` — tres tablas con migración Alembic. `Evaluacion` almacena la convocatoria (materia, cohorte, tipo, instancia, cupos por día como JSONB, alumnos convocados como JSONB). `ReservaEvaluacion` registra el turno reservado por un alumno en una fecha-hora con estado Activa/Cancelada. `ResultadoEvaluacion` consolida la nota final por alumno.
- **EvaluacionService** — servicio de dominio con 9 operaciones: crear convocatoria, actualizar, listar, importar alumnos (desde padrón o manual), métricas del panel, y administración global.
- **`/api/coloquios/*` router** — endpoints bajo prefix `/api/coloquios` con guards `coloquios:gestionar` (COORDINADOR, ADMIN) para gestión y `coloquios:reservar` (ALUMNO) para reserva.
- **Crear convocatoria (F7.3)** — POST /api/coloquios define materia, cohorte, instancia, tipo, días con cupos. Retorna la Evaluacion creada.
- **Importar alumnos (F7.2)** — PUT /api/coloquios/{id}/convocados acepta lista de usuario_ids (manual) o materia_id + cohorte_id (desde padrón). Actualiza alumnos_convocados (JSONB) en la Evaluacion.
- **Listado de convocatorias (F7.4)** — GET /api/coloquios con filtros por materia, cohorte, tipo, activa. Retorna métricas por convocatoria (convocados, reservas, libres).
- **Panel de métricas (F7.1)** — GET /api/coloquios/metricas con datos agregados: total convocatorias activas, total convocados, reservas activas, notas registradas, tasa de aprobación.
- **Reservar turno (F7, FL-07)** — POST /api/coloquios/{id}/reservas crea una ReservaEvaluacion para el alumno autenticado en un día con cupo disponible. Valida que el alumno esté convocado, que haya cupo, y que no tenga reserva activa previa para la misma evaluación.
- **Cancelar reserva** — PATCH /api/coloquios/reservas/{id}/cancelar cambia estado a Cancelada.
- **Registrar resultado** — POST /api/coloquios/{id}/resultados asigna nota_final a un alumno.
- **Admin global (F7.5)** — GET /api/coloquios/admin/agenda (reservas activas globales), GET /api/coloquios/admin/consolidado (resultados consolidados).
- **Permisos**: `coloquios:gestionar` (COORDINADOR, ADMIN) y `coloquios:reservar` (ALUMNO).
- **Auditoría**: COLOQUIO_CREAR, COLOQUIO_RESERVAR, COLOQUIO_CANCELAR, COLOQUIO_RESULTADO — nuevos códigos en AuditAction.

## Capabilities

### New Capabilities
- `evaluaciones`: Gestión de convocatorias de evaluación (F7.3, F7.2, F7.4) — crear, listar, actualizar, importar alumnos, métricas operativas
- `reservas`: Sistema de reserva de turnos con control de cupos (F7.1, FL-07) — reservar, cancelar, agenda, validación de cupo y convocatoria
- `resultados`: Registro y consolidación de notas de evaluación (F7.5) — carga de resultados, listado consolidado, administración global

### Modified Capabilities
- `backend/app/core/audit_codes.py` — nuevos códigos COLOQUIO_CREAR, COLOQUIO_RESERVAR, COLOQUIO_CANCELAR, COLOQUIO_RESULTADO
- `backend/app/models/__init__.py` — registrar Evaluacion, ReservaEvaluacion, ResultadoEvaluacion
- `backend/app/main.py` — registrar coloquios router

## Impact

- **New models**: `backend/app/models/evaluacion.py`, `backend/app/models/reserva_evaluacion.py`, `backend/app/models/resultado_evaluacion.py`
- **New migration**: Alembic para tablas evaluacion, reserva_evaluacion, resultado_evaluacion (una migración)
- **New repository**: `backend/app/repositories/evaluacion_repository.py`
- **New service**: `backend/app/services/evaluacion_service.py`
- **New router**: `backend/app/api/v1/routers/coloquios.py` — prefix `/api/coloquios`
- **New schemas**: `backend/app/schemas/evaluaciones.py`
- **Modified files**: `backend/app/models/__init__.py`, `backend/app/core/audit_codes.py`, `backend/app/main.py`
- **Dependencies**: `C-07` (Usuario, Asignacion models y repos), `C-06` (Carrera, Cohorte, Materia models y repos), `C-04` (RBAC guards `coloquios:gestionar` y `coloquios:reservar`), `C-05` (AuditService)
