## Why

C-06 y C-07 entregaron la estructura académica (Carrera, Cohorte, Materia) y el puente de autorización (Asignacion). Los docentes necesitan ahora planificar encuentros sincrónicos recurrentes, registrar guardias de atención a alumnos, y generar contenido para publicar en el aula virtual del LMS. Sin C-13 no existe gestión de encuentros ni registro de guardias en el sistema — dos capacidades críticas del FL-06 (encuentros recurrentes) y F6.6 (guardias).

## What Changes

- **Modelo SlotEncuentro (E9)** — plantilla de recurrencia semanal para encuentros sincrónicos. Define materia, día, horario, fecha de inicio, cantidad de semanas, y opcionalmente una fecha única para encuentros puntuales. Un slot pertenece a una Asignacion (el docente que lo crea).
- **Modelo InstanciaEncuentro (E10)** — encuentro concreto generado desde un slot o creado independientemente. Cada instancia tiene su propio estado (Programado, Realizado, Cancelado), meet_url, video_url y comentario. El estado de cada instancia es independiente del slot y de otras instancias (RN-14).
- **Modelo Guardia (E11)** — registro de guardias de atención cubiertas por tutores, con materia, carrera, cohorte, día, horario, estado y comentarios.
- **SlotService + EncuentroService + GuardiaService** — servicios de dominio que orquestan la creación de slots recurrentes (con generación automática de N instancias según RN-13), edición de instancias, generación de bloque HTML para LMS, y registro/consulta de guardias.
- **`/api/encuentros/*` router** — endpoints bajo prefix `/api/encuentros` con guard `encuentros:gestionar` (PROFESOR, COORDINADOR, ADMIN). PROFESOR limitado a sus propias asignaciones.
- **`/api/guardias/*` router** — endpoints bajo prefix `/api/guardias` con guard `encuentros:gestionar` para consulta; TUTOR puede registrar sus propias guardias con permiso propio.
- **Migración Alembic** — nueva migración para las tablas `slot_encuentro`, `instancia_encuentro`, `guardia` con sus constraints, FK hacia materia, asignacion, carrera, cohorte.
- **Seed de permisos** — `encuentros:gestionar` para roles PROFESOR, COORDINADOR, ADMIN.
- **Códigos de auditoría** — `ENCUENTRO_CREAR`, `ENCUENTRO_EDITAR`, `GUARDIA_REGISTRAR`.

## Capabilities

### New Capabilities
- `encuentros`: SlotEncuentro e InstanciaEncuentro — creación recurrente (F6.1, RN-13), encuentro único (F6.2), edición de instancia (F6.3), generación de bloque HTML para aula virtual (F6.4), vista admin de encuentros (F6.5)
- `guardias`: Guardia — registro por tutor (F6.6), consulta global por COORDINADOR/ADMIN, exportación del registro

### Modified Capabilities
- *(ninguna — C-13 introduce modelos y endpoints nuevos, no modifica specs existentes)*

## Impact

- **New models**: `backend/app/models/slot_encuentro.py`, `instancia_encuentro.py`, `guardia.py` — tres modelos con BaseModelMixin
- **New migration**: `backend/alembic/versions/<rev>_slot_encuentro_instancia_guardia.py` — una migración para las tres tablas
- **New repositories**: `backend/app/repositories/slot_encuentro_repository.py`, `instancia_encuentro_repository.py`, `guardia_repository.py`
- **New services**: `backend/app/services/slot_service.py`, `encuentro_service.py`, `guardia_service.py`
- **New routers**: `backend/app/api/v1/routers/encuentros.py` (prefix `/api/encuentros`), `guardias.py` (prefix `/api/guardias`)
- **New schemas**: `backend/app/schemas/encuentros.py`, `guardias.py` — request/response DTOs con `extra='forbid'`
- **Modified files**: `backend/app/main.py` — registrar routers de encuentros y guardias
- **Modified seed**: seed de permisos para `encuentros:gestionar`
- **Modified audit codes**: agregar `ENCUENTRO_CREAR`, `ENCUENTRO_EDITAR`, `GUARDIA_REGISTRAR`
- **Dependencies**: `C-06` (Carrera, Cohorte, Materia models), `C-07` (Asignacion model, repository)
