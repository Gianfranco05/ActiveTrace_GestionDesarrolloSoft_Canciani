## Why

C-06 entregó la estructura académica base (Carrera, Cohorte, Materia) y C-08 completó la gestión de equipos docentes. Ahora la institución necesita dos capacidades que operan sobre esa estructura: (1) centralizar los programas oficiales de cada materia por carrera y cohorte, y (2) calendarizar las fechas de evaluaciones (parciales, TPs, coloquios) por materia y cohorte. Sin C-17 los programas quedan dispersos en drives personales y las fechas de evaluación no tienen visibilidad sistémica, lo que afecta la planificación académica y la generación de contenido para el aula virtual del LMS.

## What Changes

- **Modelos nuevos**: `ProgramaMateria` (materia × carrera × cohorte, con `referencia_archivo` opaca al almacenamiento) y `FechaAcademica` (materia × cohorte × tipo × número, con fecha y título).
- **Migración 0NN**: nueva migración Alembic que crea las tablas `programa_materia` y `fecha_academica`.
- **`/api/programas` router** — upload de documento + asociación a materia×carrera×cohorte, listado y consulta. Guard: `estructura:gestionar`.
- **`/api/fechas-academicas` router** — CRUD completo, listado tabular y vista tipo calendario por cohorte/materia. Guard: `estructura:gestionar`.
- **Salida a LMS (F5.4)**: endpoint que genera fragmento HTML con el calendario de fechas académicas listo para publicar en el aula virtual.
- **Auditoría**: `PROGRAMA_SUBIR` y `FECHA_ACADEMICA_MODIFICAR` en todas las operaciones de escritura.
- **Repository + Service + Schema**: una capa completa por cada entidad, siguiendo el patrón Clean Architecture de C-06 y C-08.

## Capabilities

### New Capabilities
- `programas-crud`: Subir y asociar programas de materia (F5.3) — POST para upload + asociación, GET para listado y consulta por materia×carrera×cohorte, DELETE lógico. El archivo se almacena con referencia opaca, nunca expuesta como path de disco.
- `fechas-academicas-crud`: CRUD de fechas académicas (F5.4) — listado tabular con filtros por materia, cohorte, tipo, período; vista tipo calendario; creación y edición de fechas de parciales, TPs, coloquios y recuperatorios.
- `fechas-academicas-lms`: Generación de fragmento HTML para aula virtual (F5.4) — endpoint que produce contenido formateado con las fechas del período listo para publicar en el LMS.

### Modified Capabilities
- _(ninguna — C-17 introduce entidades nuevas, no modifica requerimientos de specs existentes)_

## Impact

- **New models**: `backend/app/models/programa_materia.py`, `backend/app/models/fecha_academica.py`
- **New migration**: `backend/alembic/versions/0NNN_programa_materia_fecha_academica.py`
- **New repositories**: `backend/app/repositories/programa_materia_repository.py`, `backend/app/repositories/fecha_academica_repository.py`
- **New services**: `backend/app/services/programa_service.py` (upload, asociación), `backend/app/services/fecha_academica_service.py` (CRUD, generación LMS)
- **New schemas**: `backend/app/schemas/programas.py`, `backend/app/schemas/fechas_academicas.py`
- **New routers**: `backend/app/api/v1/routers/programas.py`, `backend/app/api/v1/routers/fechas_academicas.py`
- **Modified files**: `backend/app/main.py` — registrar ambos routers bajo `/api/programas` y `/api/fechas-academicas`
- **Dependencies**: `C-06` (estructura académica: Carrera, Cohorte, Materia), `C-02` (modelos base y tenancy), `C-04` (guard `estructura:gestionar` ya existe)
- **Storage dependency**: el servicio de almacenamiento de archivos (existente en la infraestructura); `referencia_archivo` es un string opaco que el backend no interpreta
