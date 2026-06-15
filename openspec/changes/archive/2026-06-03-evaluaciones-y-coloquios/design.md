## Context

C-07 y C-06 entregan el ecosistema de usuarios, roles y estructura académica. C-14 es el primer change que introduce el módulo de evaluaciones, usando tres modelos nuevos con migración Alembic. La complejidad está en tres áreas: (1) el control de cupos en tiempo real para reservas concurrentes, (2) el manejo de alumnos convocados como JSONB sobre Evaluacion para evitar una tabla extra, y (3) la separación de permisos entre gestión (COORDINADOR/ADMIN) y reserva (ALUMNO autenticado sobre sí mismo).

Governance es **MEDIO** porque C-14 introduce lógica de dominio nueva (evaluaciones, reservas, resultados) pero no modifica subsistemas críticos de seguridad (auth, tenancy, RBAC). La auditoría con nuevos códigos COLOQUIO_* es obligatoria en todas las operaciones de escritura.

## Goals / Non-Goals

**Goals:**
- Tres modelos ORM: `Evaluacion`, `ReservaEvaluacion`, `ResultadoEvaluacion` con una migración Alembic
- `EvaluacionService` con operaciones de dominio: `crear()`, `actualizar()`, `listar()`, `importar_alumnos()`, `metricas_panel()`, `metricas_convocatoria()`, `reservar_turno()`, `cancelar_reserva()`, `registrar_resultado()`, `consolidado()`, `agenda_reservas()`
- `POST /api/coloquios` — crear convocatoria (F7.3)
- `GET /api/coloquios` — listar convocatorias con métricas (F7.4)
- `GET /api/coloquios/{id}` — detalle de convocatoria
- `PUT /api/coloquios/{id}` — actualizar convocatoria
- `PUT /api/coloquios/{id}/convocados` — importar alumnos desde padrón o manual (F7.2)
- `GET /api/coloquios/metricas` — panel de métricas agregadas (F7.1)
- `POST /api/coloquios/{id}/reservas` — reservar turno (ALUMNO, FL-07)
- `PATCH /api/coloquios/reservas/{id}/cancelar` — cancelar reserva
- `POST /api/coloquios/{id}/resultados` — registrar resultado (F7.5)
- `GET /api/coloquios/admin/agenda` — agenda global de reservas activas (F7.5)
- `GET /api/coloquios/admin/consolidado` — registro académico consolidado (F7.5)
- `GET /api/coloquios/admin/convocatorias` — administración global de convocatorias (F7.5)
- Permisos: `coloquios:gestionar` (COORDINADOR, ADMIN) para CRUD/import/resultados; `coloquios:reservar` (ALUMNO) para reserva/cancelación propia
- Auditoría COLOQUIO_CREAR, COLOQUIO_RESERVAR, COLOQUIO_CANCELAR, COLOQUIO_RESULTADO en todas las operaciones de escritura
- Control de cupos: al reservar, contar reservas activas para el día seleccionado y rechazar si cupo lleno
- Validación de convocatoria: solo alumnos convocados (presentes en `alumnos_convocados`) pueden reservar

**Non-Goals:**
- Frontend UI para coloquios — C-23 (frontend-coordinacion) y C-24 (frontend-academico)
- Integración con Moodle para coloquios — fuera del alcance de la épica 7
- Notificaciones automáticas al crear convocatoria — responsabilidad de C-12 (comunicaciones)
- Soft-delete en cascada entre Evaluacion → ReservaEvaluacion/ResultadoEvaluacion — se maneja en el repositorio filtrando por deleted_at
- Edición de día/cupo individual posterior a la creación — la actualización de Evaluacion reemplaza `cupos_por_dia` completo
- Control de concurrencia con locks a nivel BD — la primera versión usa conteo en el servicio; si hay race conditions, migrar a SELECT FOR UPDATE en versión posterior

## Decisions

### D1 — Cupos por día como JSONB en Evaluacion

`Evaluacion.cupos_por_dia` almacena un array JSONB con objetos `{fecha: date, cupo: int}`. Esto evita crear una tabla `DiaEvaluacion` separada y mantiene el modelo compacto (3 tablas).

```python
# Estructura de cupos_por_dia
[
  {"fecha": "2026-06-15", "cupo": 5},
  {"fecha": "2026-06-16", "cupo": 3},
  {"fecha": "2026-06-17", "cupo": 8}
]
```

**Why not a separate DiaEvaluacion table?**
- Menos joins, queries más simples
- La lista de días se lee y escribe como un todo (al crear/actualizar la convocatoria)
- No hay consultas que necesiten filtrar por día individual fuera del contexto de la Evaluacion
- PostgreSQL JSONB tiene buen rendimiento para arrays de este tamaño (típicamente 1-30 días)

**Trade-off**: No se puede poner FK constraint sobre la fecha. El servicio valida que la fecha de reserva esté en `cupos_por_dia`.

### D2 — Alumnos convocados como JSONB en Evaluacion

`Evaluacion.alumnos_convocados` es un array JSONB de UUIDs. Representa el padrón de coloquio (F7.2).

```python
# Estructura de alumnos_convocados
[uuid1, uuid2, uuid3, ...]
```

**Why not a Convocado junction table?**
- El scope definido para C-14 lista explícitamente 3 modelos: Evaluacion, ReservaEvaluacion, ResultadoEvaluacion
- La operación de importar alumnos es un upsert: reemplaza la lista completa
- La consulta "está el alumno X convocado en la evaluación Y?" se resuelve con `alumno_id = ANY(alumnos_convocados)` — eficiente en PostgreSQL con índices GIN
- Para la importación desde padrón (F7.2 "desde padrón"), se consulta EntradaPadron del tenant y se extraen los usuario_ids

**Trade-off**: No se puede hacer FK constraint sobre los UUIDs individuales del array. El servicio valida que los UUIDs provistos existan en Usuario antes de persistir.

### D3 — ReservaEvaluacion: control de cupos en el servicio

Al crear una `ReservaEvaluacion`, el servicio verifica:

```python
async def reservar_turno(self, evaluacion_id, alumno_id, fecha_hora, actor_id):
    evaluacion = await self._repo.get(evaluacion_id)
    
    # 1. Validar que el alumno esté convocado
    if alumno_id not in evaluacion.alumnos_convocados:
        raise HTTPException(403, "Alumno no convocado")
    
    # 2. Validar que la fecha esté en cupos_por_dia
    dia = next((d for d in evaluacion.cupos_por_dia if d["fecha"] == fecha_hora.date()), None)
    if not dia:
        raise HTTPException(400, "Fecha no disponible")
    
    # 3. Contar reservas activas para ese día
    reservas_activas = await self._repo.count_reservas_activas(evaluacion_id, fecha_hora.date())
    if reservas_activas >= dia["cupo"]:
        raise HTTPException(409, "Cupo lleno para esta fecha")
    
    # 4. Validar que el alumno no tenga otra reserva activa para esta evaluación
    existente = await self._repo.get_reserva_activa(evaluacion_id, alumno_id)
    if existente:
        raise HTTPException(409, "Ya tiene una reserva activa")
    
    # 5. Crear reserva
    reserva = await self._repo.create_reserva({...})
    await self._audit.log(COLOQUIO_RESERVAR, actor_id, detalle={...})
    return reserva
```

**Why not DB-level constraint?** Un constraint UNIQUE (evaluacion_id, alumno_id) WHERE estado = 'Activa' evitaría duplicados pero no el conteo de cupos. El control de cupos requiere contar reservas activas antes de insertar, lo cual es inherentemente una operación de servicio.

**Race condition awareness**: En alta concurrencia, dos reservas simultáneas para el último cupo disponible podrían superar el límite. La primera versión acepta este riesgo (baja probabilidad en el dominio académico). Si se detecta en producción, migrar a `SELECT ... FOR UPDATE` sobre la fila de Evaluacion antes del conteo.

### D4 — ReservaEvaluacion: estado Activa/Cancelada (soft state change)

La cancelación es un cambio de estado (`Activa` → `Cancelada`), no un soft-delete. Esto libera el cupo inmediatamente.

```python
async def cancelar_reserva(self, reserva_id, actor_id):
    reserva = await self._repo.get_reserva(reserva_id)
    if reserva.estado != "Activa":
        raise HTTPException(409, "Reserva no activa")
    reserva.estado = "Cancelada"
    await self._session.commit()
    await self._audit.log(COLOQUIO_CANCELAR, actor_id, detalle={...})
    return reserva
```

**Why not soft-delete?** Soft-delete implica que la fila "existe pero está oculta". Cancelar es un cambio de estado de negocio: la reserva existió, se canceló, y el cupo se libera. El historial se preserva (el registro sigue existiendo) pero el conteo de cupos ignora las canceladas.

### D5 — EvaluacionService: estructura de servicios

```python
class EvaluacionService:
    def __init__(self, session: AsyncSession, audit_service: AuditService, tenant_id: UUID):
        self._session = session
        self._repo = EvaluacionRepository(session, tenant_id)
        self._usuario_repo = UsuarioRepository(session, tenant_id)
        self._padron_repo = PadronRepository(session, tenant_id)
        self._audit = audit_service
        self._tenant_id = tenant_id

    # Convocatorias (F7.3, F7.4)
    async def crear(self, data: EvaluacionCreateRequest, actor_id: UUID) -> EvaluacionResponse: ...
    async def actualizar(self, id: UUID, data: EvaluacionUpdateRequest, actor_id: UUID) -> EvaluacionResponse: ...
    async def obtener(self, id: UUID) -> EvaluacionDetailResponse: ...
    async def listar(self, filtros: dict) -> list[EvaluacionResponse]: ...

    # Importación de alumnos (F7.2)
    async def importar_alumnos(self, id: UUID, data: ImportarAlumnosRequest, actor_id: UUID) -> EvaluacionDetailResponse: ...

    # Métricas (F7.1)
    async def metricas_panel(self) -> PanelMetricasResponse: ...
    async def metricas_convocatoria(self, id: UUID) -> ConvocatoriaMetricasResponse: ...

    # Reservas (F7, FL-07)
    async def reservar_turno(self, evaluacion_id: UUID, fecha_hora: datetime, actor_id: UUID, alumno_id: UUID) -> ReservaResponse: ...
    async def cancelar_reserva(self, reserva_id: UUID, actor_id: UUID, alumno_id: UUID) -> ReservaResponse: ...

    # Resultados (F7.5)
    async def registrar_resultado(self, evaluacion_id: UUID, data: ResultadoRequest, actor_id: UUID) -> ResultadoResponse: ...

    # Admin global (F7.5)
    async def agenda_reservas(self, filtros: dict) -> list[ReservaAgendaResponse]: ...
    async def consolidado(self, filtros: dict) -> list[ConsolidadoResponse]: ...
    async def admin_convocatorias(self, filtros: dict) -> list[EvaluacionAdminResponse]: ...
```

### D6 — EvaluacionRepository

```python
class EvaluacionRepository(BaseRepository[Evaluacion]):
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        super().__init__(session, tenant_id, Evaluacion)

    async def list_with_metrics(self, **filters) -> list[dict]:
        """Lista evaluaciones con conteos agregados: convocados, reservas activas, resultados."""
    
    async def count_reservas_activas(self, evaluacion_id: UUID, fecha: date) -> int:
        """Cuenta reservas con estado='Activa' para un día específico."""
    
    async def get_reserva_activa(self, evaluacion_id: UUID, alumno_id: UUID) -> ReservaEvaluacion | None:
        """Busca reserva activa de un alumno en una evaluación."""
    
    async def create_reserva(self, data: dict) -> ReservaEvaluacion: ...
    async def get_reserva(self, reserva_id: UUID) -> ReservaEvaluacion | None: ...
    async def list_reservas(self, evaluacion_id: UUID, **filters) -> list[ReservaEvaluacion]: ...
    async def list_reservas_global(self, tenant_id: UUID, **filters) -> list[ReservaEvaluacion]: ...
    
    async def create_resultado(self, data: dict) -> ResultadoEvaluacion: ...
    async def list_resultados(self, evaluacion_id: UUID) -> list[ResultadoEvaluacion]: ...
    async def list_resultados_global(self, tenant_id: UUID, **filters) -> list[ResultadoEvaluacion]: ...
    async def get_resultado(self, evaluacion_id: UUID, alumno_id: UUID) -> ResultadoEvaluacion | None: ...
```

### D7 — Importación de alumnos: desde padrón o manual (F7.2)

`PUT /api/coloquios/{id}/convocados` acepta dos modos:

```python
class ImportarAlumnosRequest(BaseModel):
    modo: Literal["manual", "padron"]  # "manual" usa usuario_ids, "padron" usa materia_id + cohorte_id
    usuario_ids: list[UUID] | None = None  # modo manual
    materia_id: UUID | None = None  # modo padrón
    cohorte_id: UUID | None = None  # modo padrón
    model_config = ConfigDict(extra='forbid')
```

**Modo manual**: reemplaza `alumnos_convocados` con la lista de `usuario_ids` provista. Valida que todos los UUIDs existan.

**Modo padrón**: consulta `EntradaPadron` del tenant filtrado por `materia_id` y `cohorte_id`, extrae los `usuario_id` únicos, y los asigna como `alumnos_convocados`. Si no hay padrón cargado, retorna error 400.

Ambos modos validan que los usuarios tengan rol ALUMNO en el tenant.

### D8 — Métricas del panel (F7.1)

`GET /api/coloquios/metricas` retorna métricas agregadas del tenant:

```python
class PanelMetricasResponse(BaseModel):
    total_convocatorias_activas: int
    total_convocados: int  # suma de len(alumnos_convocados) en todas las activas
    total_reservas_activas: int  # count de ReservaEvaluacion con estado='Activa'
    total_resultados: int  # count de ResultadoEvaluacion
    tasa_aprobacion: float | None  # % de resultados con nota >= 4 (o None si no hay resultados)
    model_config = ConfigDict(extra='forbid')
```

Para el listado de convocatorias (F7.4), cada item incluye métricas individuales:

```python
class EvaluacionResponse(BaseModel):
    id: UUID
    materia_id: UUID
    materia_nombre: str
    cohorte_id: UUID
    cohorte_nombre: str
    tipo: str
    instancia: str
    cupos_por_dia: list[dict]
    activa: bool
    total_convocados: int
    total_reservas: int
    total_resultados: int
    cupos_libres: int  # sum(cupo) - count(reservas activas)
    model_config = ConfigDict(extra='forbid', from_attributes=True)
```

### D9 — Router structure

| Método | Path | Guard | Capability |
|--------|------|-------|------------|
| POST | `/api/coloquios` | `coloquios:gestionar` | F7.3 |
| GET | `/api/coloquios` | `coloquios:gestionar` | F7.4 |
| GET | `/api/coloquios/{id}` | `coloquios:gestionar` | F7.4 |
| PUT | `/api/coloquios/{id}` | `coloquios:gestionar` | F7.3 |
| PUT | `/api/coloquios/{id}/convocados` | `coloquios:gestionar` | F7.2 |
| GET | `/api/coloquios/metricas` | `coloquios:gestionar` | F7.1 |
| POST | `/api/coloquios/{id}/reservas` | `coloquios:reservar` | FL-07 |
| PATCH | `/api/coloquios/reservas/{id}/cancelar` | `coloquios:reservar` | FL-07 |
| GET | `/api/coloquios/mis-reservas` | `require_authenticated` (ALUMNO ve sus propias) | FL-07 |
| POST | `/api/coloquios/{id}/resultados` | `coloquios:gestionar` | F7.5 |
| GET | `/api/coloquios/admin/agenda` | `coloquios:gestionar` | F7.5 |
| GET | `/api/coloquios/admin/consolidado` | `coloquios:gestionar` | F7.5 |
| GET | `/api/coloquios/admin/convocatorias` | `coloquios:gestionar` | F7.5 |

### D10 — Schemas

```python
class CupoPorDia(BaseModel):
    fecha: date
    cupo: int = Field(gt=0)
    model_config = ConfigDict(extra='forbid')

class EvaluacionCreateRequest(BaseModel):
    materia_id: UUID
    cohorte_id: UUID
    tipo: Literal["Parcial", "TP", "Coloquio", "Recuperatorio"]
    instancia: str = Field(min_length=1, max_length=200)
    cupos_por_dia: list[CupoPorDia] = Field(min_length=1)
    model_config = ConfigDict(extra='forbid')

class EvaluacionUpdateRequest(BaseModel):
    instancia: str | None = Field(default=None, min_length=1, max_length=200)
    cupos_por_dia: list[CupoPorDia] | None = None
    activa: bool | None = None
    model_config = ConfigDict(extra='forbid')

class ImportarAlumnosRequest(BaseModel):
    modo: Literal["manual", "padron"]
    usuario_ids: list[UUID] | None = Field(default=None, max_length=500)
    materia_id: UUID | None = None
    cohorte_id: UUID | None = None
    model_config = ConfigDict(extra='forbid')

class EvaluacionResponse(BaseModel):
    id: UUID
    materia_id: UUID
    materia_nombre: str
    cohorte_id: UUID
    cohorte_nombre: str
    tipo: str
    instancia: str
    cupos_por_dia: list[dict]
    activa: bool
    total_convocados: int
    total_reservas: int
    total_resultados: int
    cupos_libres: int
    model_config = ConfigDict(extra='forbid', from_attributes=True)

class EvaluacionDetailResponse(BaseModel):
    id: UUID
    materia_id: UUID
    cohorte_id: UUID
    tipo: str
    instancia: str
    cupos_por_dia: list[dict]
    activa: bool
    alumnos_convocados: list[UUID]
    model_config = ConfigDict(extra='forbid', from_attributes=True)

class ReservaRequest(BaseModel):
    fecha_hora: datetime
    model_config = ConfigDict(extra='forbid')

class ReservaResponse(BaseModel):
    id: UUID
    evaluacion_id: UUID
    alumno_id: UUID
    fecha_hora: datetime
    estado: str
    model_config = ConfigDict(extra='forbid', from_attributes=True)

class ReservaAgendaResponse(BaseModel):
    id: UUID
    evaluacion_id: UUID
    materia_nombre: str
    cohorte_nombre: str
    instancia: str
    alumno_nombre: str
    alumno_apellidos: str
    fecha_hora: datetime
    estado: str
    model_config = ConfigDict(extra='forbid')

class ResultadoRequest(BaseModel):
    alumno_id: UUID
    nota_final: str = Field(min_length=1, max_length=50)
    model_config = ConfigDict(extra='forbid')

class ResultadoResponse(BaseModel):
    id: UUID
    evaluacion_id: UUID
    alumno_id: UUID
    alumno_nombre: str
    alumno_apellidos: str
    nota_final: str
    model_config = ConfigDict(extra='forbid', from_attributes=True)

class ConsolidadoResponse(BaseModel):
    alumno_id: UUID
    alumno_nombre: str
    alumno_apellidos: str
    materia_nombre: str
    instancia: str
    nota_final: str
    fecha_registro: datetime | None
    model_config = ConfigDict(extra='forbid')

class ConvocatoriaMetricasResponse(BaseModel):
    evaluacion_id: UUID
    total_convocados: int
    total_reservas: int
    total_resultados: int
    cupos_libres: int
    model_config = ConfigDict(extra='forbid')

class PanelMetricasResponse(BaseModel):
    total_convocatorias_activas: int
    total_convocados: int
    total_reservas_activas: int
    total_resultados: int
    tasa_aprobacion: float | None
    model_config = ConfigDict(extra='forbid')
```

### D11 — Auditoría

Cuatro nuevos códigos en `AuditAction`:

```python
COLOQUIO_CREAR = "COLOQUIO_CREAR"
COLOQUIO_RESERVAR = "COLOQUIO_RESERVAR"
COLOQUIO_CANCELAR = "COLOQUIO_CANCELAR"
COLOQUIO_RESULTADO = "COLOQUIO_RESULTADO"
```

Cada operación de escritura genera un registro con:
- `accion` = código correspondiente
- `actor_id` = usuario autenticado
- `detalle` = JSON con contexto relevante (evaluacion_id, alumno_id, etc.)

### D12 — Permisos `coloquios:gestionar` y `coloquios:reservar`

Se asume que los permisos `coloquios:gestionar` y `coloquios:reservar` serán creados vía seed migration o seed script. Los endpoints usan los guards existentes:

```python
# Gestión (COORDINADOR, ADMIN)
require_permission_return_user("coloquios:gestionar")

# Reserva (ALUMNO)
require_permission_return_user("coloquios:reservar")

# Mis reservas (cualquier rol autenticado, filtrado por identidad)
get_current_user  # sin require_permission, el servicio filtra por user_id
```

La creación de los permisos y su asignación a roles forma parte del seed data (C-01 foundation-setup) o será agregada en una migración de seed.

## Risks / Trade-offs

- **[Race condition en reservas concurrentes]** → Dos alumnos reservando el último cupo simultáneamente podrían superar el límite. Mitigación: probabilidad baja en dominio académico. Si ocurre en producción, implementar `SELECT ... FOR UPDATE` sobre Evaluacion antes del conteo de reservas. Costo de mitigación: bajo (una línea de SQL adicional).
- **[JSONB sin FK constraints]** → `alumnos_convocados` y `cupos_por_dia` no tienen integridad referencial a nivel BD. Un UUID huérfano en alumnos_convocados no rompe queries pero puede causar confusión. Mitigación: el servicio valida existencia de UUIDs antes de escribir. Los queries de lectura usan LEFT JOIN y toleran missing references.
- **[Upsert de alumnos_convocados pisa datos anteriores]** → `PUT /convocados` reemplaza la lista completa. Si dos coordinadores importan simultáneamente, el último pisa al primero. Mitigación: documentar que esta operación no es merge sino replace. Si se requiere merge parcial, exponer endpoints `POST /convocados/{alumno_id}` y `DELETE /convocados/{alumno_id}` en versión futura.
- **[Escalabilidad de JSONB alumnos_convocados]** → Para convocatorias masivas (+5000 alumnos), el array JSONB puede degradar rendimiento en escritura. Mitigación: límite de 500 alumnos por importación manual. Para importación desde padrón, si el volumen crece, migrar a tabla `Convocado` en versión posterior. El costo de migración es bajo (una migración + cambio en servicio y repo).
- **[Reserva requiere que el alumno esté convocado]** → Si un alumno fue convocado pero luego removido de alumnos_convocados, su reserva existente sigue siendo válida (no se invalidan reservas al quitar convocatoria). Esto es intencional: la reserva es un hecho consumado.

## Migration Plan

1. Agregar modelos `Evaluacion`, `ReservaEvaluacion`, `ResultadoEvaluacion` en `backend/app/models/`
2. Registrar modelos en `backend/app/models/__init__.py`
3. Crear migración Alembic con las tres tablas (una migración)
4. Agregar códigos de auditoría en `backend/app/core/audit_codes.py`
5. Implementar `EvaluacionRepository` en `backend/app/repositories/evaluacion_repository.py`
6. Implementar schemas en `backend/app/schemas/evaluaciones.py`
7. Implementar `EvaluacionService` en `backend/app/services/evaluacion_service.py`
8. Implementar router `backend/app/api/v1/routers/coloquios.py`
9. Registrar router en `backend/app/main.py`
10. Seed de permisos `coloquios:gestionar` y `coloquios:reservar` (vía seed script o migración)
11. Tests: unitarios de EvaluacionService + integración de cada endpoint + TDD cycle por task (RED → GREEN → TRIANGULATE)

**Rollback**: La migración es aditiva (solo crea tablas). Rollback seguro eliminando las tablas. No hay migración de datos desde sistema previo.

## Open Questions

- **¿El permiso `coloquios:gestionar` debe permitir ver solo las convocatorias de las materias del coordinador?** Por ahora no — el coordinador ve todas las del tenant. Si se requiere filtrado por asignación, agregar en versión posterior.
- **¿La reserva del ALUMNO requiere que la convocatoria esté `activa = True`?** Sí, se valida en el servicio.
- **¿El resultado pisa un resultado anterior del mismo alumno en la misma evaluación?** Sí — upsert por (evaluacion_id, alumno_id). La segunda carga reemplaza la primera. Esto se implementa como `ON CONFLICT (evaluacion_id, alumno_id) DO UPDATE` o lógica en el servicio.
- **¿Los cupos se validan por día o por franja horaria?** Por día. La KB menciona "cupos por franja" en HU-31 pero el modelo de datos define `fecha_hora` en ReservaEvaluacion. La primera versión valida cupo a nivel día (todas las horas del día comparten el mismo cupo).
