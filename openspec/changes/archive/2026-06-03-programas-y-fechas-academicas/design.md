## Context

C-06 (estructura-academica) estableció el catálogo de Carrera, Cohorte y Materia como base de la estructura académica del tenant. C-17 es el primer change que opera sobre esa base para dos entidades de uso cotidiano en la planificación: los programas oficiales de cada materia (el documento físico que define contenidos y objetivos) y el calendario de fechas de evaluaciones.

Actualmente los programas viven en drives personales de los coordinadores y las fechas de parciales/TPs/coloquios se manejan en planillas externas. C-17 los trae al sistema como entidades de dominio con su propia capa completa (modelo → migración → repositorio → servicio → router), más un endpoint de generación de contenido para LMS que las integra al aula virtual.

Governance es **BAJO** (CRUD simple sobre estructura académica, sin lógica financiera ni de seguridad).

## Goals / Non-Goals

**Goals:**
- `ProgramaMateria` — modelo, migración, repositorio, schemas, servicio con upload de archivo y asociación a materia×carrera×cohorte
- `FechaAcademica` — modelo, migración, repositorio, schemas, servicio con CRUD completo y listados tabular/calendario
- `/api/programas` — POST (upload + asociar), GET (listado por filtros), GET /{id}, DELETE lógico. Guard: `estructura:gestionar`
- `/api/fechas-academicas` — GET (listado tabular con filtros por materia, cohorte, tipo, período), GET /calendario (vista agrupada por fecha), POST, PATCH, DELETE lógico. Guard: `estructura:gestionar`
- `/api/fechas-academicas/lms/html` — GET con query params materia_id y cohorte_id, genera fragmento HTML con el calendario listo para copiar al aula virtual
- Referencia opaca de archivo: el backend no interpreta ni accede al contenido, solo persiste y devuelve el string de referencia
- Auditoría: `PROGRAMA_SUBIR` en upload, `FECHA_ACADEMICA_MODIFICAR` en create/update/delete de fechas
- Soft delete en ambas entidades (herencia de BaseModelMixin.deleted_at)

**Non-Goals:**
- Visualización inline del archivo de programa (PDF, DOCX) en el frontend — eso es C-23 (frontend-coordinacion)
- Servicio de almacenamiento de archivos — se asume que ya existe en la infraestructura; el backend solo recibe y devuelve la referencia opaca
- Validación de formato de archivo en el backend — aceptamos cualquier tipo, el frontend puede filtrar extensiones
- Reemplazo de programa existente — si se sube un nuevo archivo para la misma materia×carrera×cohorte, se crea un nuevo registro (histórico) y se puede soft-deletear el anterior
- Frontend UI — C-23

## Decisions

### D1 — Dos modelos independientes, no anidados

`ProgramaMateria` y `FechaAcademica` son entidades independientes, cada una con su propia tabla, repositorio, servicio y router. No hay FK entre ellas. Se agrupan en C-17 porque ambas operan sobre la misma base (materia × cohorte) y comparten el guard `estructura:gestionar`, pero son dominios separados.

**Why not una sola entidad "RecursoAcademico"?** ProgramaMateria tiene upload de archivo + referencia opaca; FechaAcademica tiene tipo enumerado + número de instancia + generación LMS. Son comportamientos distintos con schemas distintos — forzarlos en una sola entidad polimórfica complicaría queries, validación y el modelo de permisos sin ganancia real.

### D2 — referencia_archivo como string opaco

```python
class ProgramaMateria(BaseModelMixin, Base):
    __tablename__ = "programa_materia"
    materia_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("materia.id", ondelete="RESTRICT"))
    carrera_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("carrera.id", ondelete="RESTRICT"))
    cohorte_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cohorte.id", ondelete="RESTRICT"))
    titulo: Mapped[str] = mapped_column(String(300))
    referencia_archivo: Mapped[str] = mapped_column(String(500))
    cargado_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
```

`referencia_archivo` es un string que el servicio de almacenamiento genera al persistir el archivo. El backend lo trata como opaco: lo guarda, lo devuelve en responses, y nunca intenta acceder al filesystem con ese valor.

**Why not almacenar el archivo en la DB?** Los PDFs/DOCXs pueden ser grandes (varios MB). Guardarlos como BLOB en PostgreSQL degrada backups, réplicas y queries. La referencia opaca desacopla almacenamiento de datos relacionales.

**Alternativa considerada**: columna `archivo_url` con URL pública. Rechazada porque expone la ubicación física del archivo. La referencia opaca permite que el frontend pida el archivo a un endpoint de descarga sin conocer su ruta real.

### D3 — Upload en un solo endpoint con multipart/form-data

`POST /api/programas` recibe `multipart/form-data` con:
- `archivo` (UploadFile, required)
- `materia_id` (UUID, required)
- `carrera_id` (UUID, required)
- `cohorte_id` (UUID, required)
- `titulo` (str, required)

Flujo:
1. Validar que materia_id, carrera_id, cohorte_id existan y pertenezcan al tenant (404 si no)
2. Validar que el archivo no esté vacío (422 si 0 bytes)
3. Delegar el archivo al storage service → obtener `referencia_archivo`
4. Crear `ProgramaMateria` con los datos + referencia
5. Auditar `PROGRAMA_SUBIR`
6. Retornar 201 con ProgramaMateriaResponse

**Why un solo endpoint y no dos (upload → associate)?** No hay caso de uso para tener un archivo huérfano sin asociación a materia×carrera×cohorte. El upload siempre es con metadata completa. Separar en dos pasos agregaría estado intermedio innecesario.

### D4 — Periodo como string libre en FechaAcademica

```python
class FechaAcademica(BaseModelMixin, Base):
    __tablename__ = "fecha_academica"
    materia_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("materia.id", ondelete="RESTRICT"))
    cohorte_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cohorte.id", ondelete="RESTRICT"))
    tipo: Mapped[str] = mapped_column(String(20))  # Parcial | TP | Coloquio | Recuperatorio
    numero: Mapped[int] = mapped_column(Integer)
    periodo: Mapped[str] = mapped_column(String(20))  # "2026-1", "2026-2"
    fecha: Mapped[date] = mapped_column(Date)
    titulo: Mapped[str | None] = mapped_column(String(200), nullable=True)
```

`periodo` es texto libre (ej: "2026-1", "2026-2") en lugar de FK a una entidad Período. El equipo de dominio definió el formato como "AAAA-C" (año + cuatrimestre), pero no hay tabla de períodos en el modelo — es un atributo de agrupación, no una entidad con lifecycle propio.

**Why not FK a una tabla PeriodoAcademico?** C-06 no definió esa entidad y agregarla ahora requeriría un change adicional. El string es suficiente para filtrar y agrupar. Si en el futuro se necesita gestión de períodos (fechas de inicio/fin, estados), se puede migrar sin romper la API.

### D5 — Vista calendario como endpoint de listado con group-by

`GET /api/fechas-academicas/calendario` recibe:
- `materia_id` (UUID?, optional)
- `cohorte_id` (UUID?, optional)
- `periodo` (str?, optional)
- `fecha_desde` (date?, optional)
- `fecha_hasta` (date?, optional)

Response: `{"items": list[FechaAcademicaResponse], "total": int}` ordenado por fecha ASC.

El frontend se encarga del renderizado visual (grid de calendario). El backend solo devuelve los datos ordenados y filtrados — sin agrupar por semana/mes. Esto mantiene el backend simple y deja la lógica de presentación donde pertenece (frontend).

**Why not devolver agrupado por mes/semana?** La agrupación es responsabilidad de la capa de presentación. El backend entrega datos planos y el frontend los organiza en el grid del calendario. Si el frontend necesita agrupación server-side por performance, se agrega después como parámetro opcional.

### D6 — Generación LMS: HTML limpio con inline styles

`GET /api/fechas-academicas/lms/html?materia_id=X&cohorte_id=Y` devuelve:
```json
{"html": "<div style=\"...\"><h3>Cronograma de Evaluaciones — Programación I</h3><table>...</table></div>"}
```

El HTML incluye:
- Título con nombre de la materia
- Tabla con columnas: Fecha, Tipo, N° Instancia, Título
- Filas ordenadas por fecha ASC
- Estilos inline (sin dependencias CSS externas) para ser compatible con el editor HTML del LMS

Mismo patrón que F6.4 (encuentros → LMS). La generación de HTML está en el servicio, no en el router, y es testeable unitariamente.

### D7 — Permiso único: estructura:gestionar

Ambos routers usan `require_permission("estructura:gestionar")`. Este permiso ya existe y es otorgado a ADMIN y COORDINADOR desde C-06. No se crean nuevos permisos porque las capacidades de C-17 son extensiones naturales de la gestión de estructura académica.

### D8 — Repositorios con filtros por defecto

```python
class ProgramaMateriaRepository(BaseRepository[ProgramaMateria]):
    async def list_by_filters(
        self, tenant_id: UUID, *, materia_id: UUID | None = None,
        carrera_id: UUID | None = None, cohorte_id: UUID | None = None,
        offset: int = 0, limit: int = 20
    ) -> tuple[list[ProgramaMateria], int]: ...

class FechaAcademicaRepository(BaseRepository[FechaAcademica]):
    async def list_by_filters(
        self, tenant_id: UUID, *, materia_id: UUID | None = None,
        cohorte_id: UUID | None = None, tipo: str | None = None,
        periodo: str | None = None,
        fecha_desde: date | None = None, fecha_hasta: date | None = None,
        offset: int = 0, limit: int = 20
    ) -> tuple[list[FechaAcademica], int]: ...

    async def get_calendario(
        self, tenant_id: UUID, *, materia_id: UUID | None = None,
        cohorte_id: UUID | None = None, periodo: str | None = None,
        fecha_desde: date | None = None, fecha_hasta: date | None = None
    ) -> list[FechaAcademica]: ...
```

Ambos repositorios filtran por tenant_id siempre y excluyen soft-deleted rows (deleted_at IS NOT NULL) por defecto.

### D9 — Schemas

```python
# Programas
class ProgramaMateriaCreateRequest(BaseModel):
    materia_id: UUID
    carrera_id: UUID
    cohorte_id: UUID
    titulo: str  # max 300
    model_config = ConfigDict(extra='forbid')

class ProgramaMateriaResponse(BaseModel):
    id: UUID
    materia_id: UUID
    carrera_id: UUID
    cohorte_id: UUID
    titulo: str
    referencia_archivo: str
    cargado_at: datetime
    model_config = ConfigDict(from_attributes=True, extra='forbid')

# Fechas Academicas
class FechaAcademicaCreateRequest(BaseModel):
    materia_id: UUID
    cohorte_id: UUID
    tipo: str  # Parcial | TP | Coloquio | Recuperatorio
    numero: int  # >= 1
    periodo: str  # max 20
    fecha: date
    titulo: str | None = None  # max 200
    model_config = ConfigDict(extra='forbid')

class FechaAcademicaUpdateRequest(BaseModel):
    tipo: str | None = None
    numero: int | None = None
    periodo: str | None = None
    fecha: date | None = None
    titulo: str | None = None
    model_config = ConfigDict(extra='forbid')

class FechaAcademicaResponse(BaseModel):
    id: UUID
    materia_id: UUID
    cohorte_id: UUID
    tipo: str
    numero: int
    periodo: str
    fecha: date
    titulo: str | None
    model_config = ConfigDict(from_attributes=True, extra='forbid')

class FechasLmsHtmlResponse(BaseModel):
    html: str
    model_config = ConfigDict(extra='forbid')
```

### D10 — Router structure

| Método | Path | Guard | Capability |
|--------|------|-------|------------|
| POST | `/api/programas` | `estructura:gestionar` | F5.3 upload + asociar |
| GET | `/api/programas` | `estructura:gestionar` | F5.3 listado |
| GET | `/api/programas/{id}` | `estructura:gestionar` | F5.3 consulta |
| DELETE | `/api/programas/{id}` | `estructura:gestionar` | F5.3 soft delete |
| GET | `/api/fechas-academicas` | `estructura:gestionar` | F5.4 listado tabular |
| GET | `/api/fechas-academicas/calendario` | `estructura:gestionar` | F5.4 vista calendario |
| POST | `/api/fechas-academicas` | `estructura:gestionar` | F5.4 crear |
| PATCH | `/api/fechas-academicas/{id}` | `estructura:gestionar` | F5.4 editar |
| DELETE | `/api/fechas-academicas/{id}` | `estructura:gestionar` | F5.4 soft delete |
| GET | `/api/fechas-academicas/lms/html` | `estructura:gestionar` | F5.4 salida LMS |

### D11 — Auditoría

- `PROGRAMA_SUBIR`: actor_id, materia_id, detalle con `{"titulo": ..., "referencia_archivo": "..."}`
- `FECHA_ACADEMICA_MODIFICAR`: actor_id, materia_id, detalle con `{"operacion": "create"|"update"|"delete", "fecha_academica_id": ..., "tipo": ..., "numero": ...}`

Se reusa el `AuditService` existente de C-05.

## Risks / Trade-offs

- **[Archivo muy grande]** → Si un PDF supera el límite del storage service, el upload falla. Mitigación: el router valida Content-Length máximo (configurable por tenant) antes de delegar al storage service. Valor por defecto: 20 MB.
- **[Referencia opaca rota]** → Si el storage service devuelve una referencia que después no resuelve (archivo borrado fuera del sistema), el frontend mostrará error al intentar descargar. Mitigación: el storage service es responsable de la integridad; el backend solo es transportador de la referencia.
- **[Misma fecha repetida para misma materia×cohorte×tipo×numero]** → No hay unique constraint que lo impida. Dos registros con la misma combinación son válidos (ej: fecha reprogramada). El frontend puede mostrar advertencia si detecta duplicados, pero el backend no lo rechaza.
- **[HTML LMS no compatible con todos los LMS]** → El HTML usa inline styles y tabla básica, compatible con Moodle y la mayoría de LMS. Si un LMS específico requiere formato distinto, se puede agregar un parámetro `?formato=moodle|custom`.

## Migration Plan

1. Crear migración Alembic con ambas tablas (`programa_materia`, `fecha_academica`)
2. Implementar modelos en `backend/app/models/`
3. Implementar repositorios en `backend/app/repositories/`
4. Implementar schemas en `backend/app/schemas/`
5. Implementar servicios en `backend/app/services/`
6. Implementar routers en `backend/app/api/v1/routers/`
7. Registrar routers en `main.py`
8. Tests: unitarios de servicios + integración de endpoints + TDD cycle por task

Rollback: downgrade de la migración Alembic. No hay datos que migrar porque son entidades nuevas.

## Open Questions

- **¿Se requiere thumbnail o preview del archivo de programa?** No en esta versión. Si se necesita en el futuro, el storage service puede generar thumbnail al recibir el archivo.
- **¿Las fechas académicas necesitan horario además de fecha?** El modelo actual (E15) solo tiene `fecha`. Si se requiere hora específica, se agrega como campo opcional en una versión futura.
- **¿La vista calendario debe paginar?** No en esta versión. Un cuatrimestre típico tiene < 50 fechas por materia. Si el volumen crece, se agrega paginación.
