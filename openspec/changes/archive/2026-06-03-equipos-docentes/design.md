## Context

C-07 entregó el modelo Asignacion con su repositorio, servicio, schemas y CRUD en `/api/asignaciones`. El ecosistema actual permite crear/leer/actualizar/eliminar asignaciones individuales, pero no ofrece operaciones de dominio sobre **equipos docentes** como conjunto — no hay "mis equipos" para el docente, no hay asignación masiva, no hay clonación entre cohortes, no hay modificación de vigencia en bloque ni exportación.

C-08 es el primer change que opera sobre el modelo existente sin nuevas tablas. La complejidad está en la lógica de negocio (clonación transaccional, validación de overlaps en masiva, generación de export) y en los nuevos endpoints que operan sobre conjuntos de asignaciones identificadas por el par (materia_id, carrera_id, cohorte_id) como clave compuesta de "equipo".

Governance es **ALTO** porque C-08 modifica el estado de Asignaciones en bloque (masiva, clonar, vigencia), y cualquier error puede dejar equipos docentes inconsistentes. Auditoría `ASIGNACION_MODIFICAR` es obligatoria en todas las operaciones de escritura.

## Goals / Non-Goals

**Goals:**
- EquipoService con operaciones de dominio: `listar_mis_equipos`, `asignacion_masiva`, `clonar_equipo`, `modificar_vigencia`, `exportar_equipo`
- `GET /api/equipos/mis-equipos` — filtrado por usuario autenticado, con filtros opcionales (estado, materia, rol, carrera, cohorte)
- `GET /api/equipos` — listado completo de equipos del tenant (agrupados por materia × carrera × cohorte)
- `GET /api/equipos/{equipo_id}` — detalle de un equipo con todas sus asignaciones
- `POST /api/equipos/masiva` — crear N asignaciones en una transacción con la misma materia × carrera × cohorte × rol × vigencia
- `POST /api/equipos/clonar` — duplicar asignaciones vigentes de origen a destino con nuevas fechas
- `PATCH /api/equipos/{equipo_id}/vigencia` — actualizar vig_desde/vig_hasta de todas las asignaciones del equipo
- `GET /api/equipos/{equipo_id}/export` — descargar CSV con detalle de asignaciones
- `GET /api/equipos/usuarios/search?q=` — búsqueda con autocompletado para asignación masiva (RN-30)
- Auditoría `ASIGNACION_MODIFICAR` en todos los endpoints de escritura
- Todos los endpoints de escritura requieren `equipos:asignar`; mis-equipos permite acceso con cualquier rol autenticado

**Non-Goals:**
- Frontend UI para equipos docentes — C-23 (frontend-coordinacion)
- Modificación del modelo Asignacion existente — no se agregan columnas ni nuevas tablas
- CRUD individual de asignaciones — ya existe en C-07 `/api/asignaciones`
- Validación de superposición de fechas en masiva (se hereda la validación de C-07 en creación individual)
- Export a XLSX con formato — la primera versión usa CSV (std lib); migrar a openpyxl si se requiere formato

## Decisions

### D1 — Equipo como clave compuesta, no entidad separada

Un "equipo docente" NO es una entidad propia. Es un conjunto de asignaciones identificado por la tupla `(materia_id, carrera_id, cohorte_id)`. Esta clave compuesta se serializa como `equipo_id` en formato `${materia_id}:${carrera_id}:${cohorte_id}`.

```python
def make_equipo_id(materia_id: UUID, carrera_id: UUID, cohorte_id: UUID) -> str:
    return f"{materia_id}:{carrera_id}:{cohorte_id}"
```

**Why not a separate Equipo table?**
- El modelo Asignacion ya tiene materia_id, carrera_id, cohorte_id — la agrupación es una vista, no una entidad
- No hay atributos propios del equipo (solo existen las asignaciones que lo componen)
- Crear una tabla Equipo agregaría complejidad de sync (mantener consistencia entre Equipo y Asignaciones)
- La clave compuesta es estable: materia × carrera × cohorte define unívocamente un equipo

### D2 — EquipoService: lógica de dominio pura

`EquipoService` encapsula toda la lógica de negocio de C-08. Sigue el patrón de C-07: Routers → Services → Repositories → Models.

```python
class EquipoService:
    def __init__(self, session: AsyncSession, audit_service: AuditService):
        self._repo = AsignacionRepository(session)
        self._usuario_repo = UsuarioRepository(session)
        self._audit = audit_service

    async def listar_mis_equipos(self, usuario_id: UUID, tenant_id: UUID, filtros: ...) -> list[AsignacionResponse]: ...
    async def listar_equipos(self, tenant_id: UUID) -> list[EquipoResponse]: ...
    async def obtener_equipo(self, materia_id: UUID, carrera_id: UUID, cohorte_id: UUID) -> EquipoDetailResponse: ...
    async def asignacion_masiva(self, request: AsignacionMasivaRequest, actor_id: UUID) -> list[AsignacionResponse]: ...
    async def clonar_equipo(self, request: ClonarRequest, actor_id: UUID) -> EquipoDetailResponse: ...
    async def modificar_vigencia(self, request: VigenciaUpdateRequest, actor_id: UUID) -> EquipoDetailResponse: ...
    async def exportar_equipo(self, materia_id: UUID, carrera_id: UUID, cohorte_id: UUID) -> str: ...
    async def buscar_usuarios(self, query: str, tenant_id: UUID, limit: int) -> list[UsuarioSafeResponse]: ...
```

### D3 — AsignacionRepository.extendido

Se agregan métodos al repositorio existente de C-07 (sin romper compatibilidad):

```python
class AsignacionRepository(BaseRepository[Asignacion]):
    # ... métodos existentes: list, get, create, update, soft_delete,
    #     get_by_usuario, get_activas_by_usuario ...

    async def get_equipo(
        self, materia_id: UUID, carrera_id: UUID, cohorte_id: UUID
    ) -> list[Asignacion]: ...

    async def get_equipos_agrupados(
        self, tenant_id: UUID
    ) -> list[tuple[UUID, UUID, UUID, int]]:
        """Returns distinct (materia_id, carrera_id, cohorte_id, count) tuples."""

    async def bulk_create(
        self, asignaciones: list[Asignacion]
    ) -> list[Asignacion]: ...

    async def update_vigencia_batch(
        self, equipo_key: tuple[UUID, UUID, UUID],
        vig_desde: date, vig_hasta: date | None
    ) -> int: ...  # returns count updated

    async def get_equipo_with_relations(
        self, materia_id: UUID, carrera_id: UUID, cohorte_id: UUID
    ) -> list[dict]: ...  # joined data for export

    async def search_usuarios(
        self, query: str, tenant_id: UUID, limit: int = 20
    ) -> list[Usuario]: ...
```

### D4 — Asignación masiva: transaccional con rollback

`POST /api/equipos/masiva` recibe:

```python
class AsignacionMasivaRequest(BaseModel):
    materia_id: UUID
    carrera_id: UUID
    cohorte_id: UUID
    rol_id: UUID
    usuario_ids: list[UUID]
    vig_desde: date
    vig_hasta: date | None = None
    comisiones: str | None = None
    model_config = ConfigDict(extra='forbid')
```

**Flujo:**
1. Validar que todos los usuario_ids existan (404 si alguno no)
2. Validar vig_desde <= vig_hasta (si vig_hasta presente)
3. Para cada usuario_id, crear Asignacion con los datos comunes
4. Si alguna creación falla (unique constraint, FK), rollback total
5. Generar auditoría `ASIGNACION_MODIFICAR` con filas_afectadas = len(usuario_ids)
6. Retornar 201 con listado de AsignacionResponse

**Why bulk create instead of N individual inserts?** Una transacción con N INSERTs es más rápida que N requests HTTP, y el rollback automático garantiza consistencia — o se crean todas o ninguna.

### D5 — Clonación de equipo (RN-12)

`POST /api/equipos/clonar` recibe:

```python
class ClonarRequest(BaseModel):
    origen_materia_id: UUID
    origen_carrera_id: UUID
    origen_cohorte_id: UUID
    destino_materia_id: UUID
    destino_carrera_id: UUID
    destino_cohorte_id: UUID
    nueva_vig_desde: date
    nueva_vig_hasta: date | None = None
    model_config = ConfigDict(extra='forbid')
```

**Flujo:**
1. Obtener todas las asignaciones vigentes del origen (deleted_at IS NULL AND vigente)
2. Si el origen no tiene asignaciones → 404
3. Para cada asignación origen, crear una copia con:
   - mismo usuario_id, rol_id, comisiones
   - materia_id = destino_materia_id, carrera_id = destino_carrera_id, cohorte_id = destino_cohorte_id
   - vig_desde = nueva_vig_desde, vig_hasta = nueva_vig_hasta
   - responsable_id = buscar la asignación equivalente del responsable en el destino (si existe y está vigente; si no, None)
4. Bulk create de todas las copias en una transacción
5. Generar auditoría `ASIGNACION_MODIFICAR` con filas_afectadas = cantidad clonada
6. Retornar 201 con EquipoDetailResponse del destino

**Responsable resolution**: Si el responsable original también estaba en el equipo origen, su nueva asignación en el destino tendrá un nuevo id. Buscamos ese nuevo id por (usuario_id, rol_id, destino_materia_id, destino_carrera_id, destino_cohorte_id).

### D6 — Modificar vigencia general (F4.6)

`PATCH /api/equipos/{equipo_id}/vigencia` recibe:

```python
class VigenciaUpdateRequest(BaseModel):
    vig_desde: date
    vig_hasta: date | None = None
    model_config = ConfigDict(extra='forbid')
```

`equipo_id` se parsea como `{materia_id}:{carrera_id}:{cohorte_id}` o se pasan los 3 UUIDs como query params. Decisión: usar query params para mantener REST-semántica.

```
PATCH /api/equipos/vigencia?materia_id=X&carrera_id=Y&cohorte_id=Z
Body: { "vig_desde": "...", "vig_hasta": "..." }
```

**Flujo:**
1. Validar que el equipo exista (al menos una asignación)
2. UPDATE todas las asignaciones del equipo con nuevos valores
3. Generar auditoría `ASIGNACION_MODIFICAR` con filas_afectadas = count
4. Retornar EquipoDetailResponse actualizado

### D7 — Exportar equipo (F4.7)

`GET /api/equipos/export?materia_id=X&carrera_id=Y&cohorte_id=Z` retorna:

```
Content-Type: text/csv
Content-Disposition: attachment; filename="equipo_{materia}_{carrera}_{cohorte}.csv"

usuario_id,nombre,apellidos,rol,materia,carrera,cohorte,comisiones,vig_desde,vig_hasta,estado_vigencia
uuid1,Pérez,Juan,PROFESOR,Programación I,TUPAD,AGO-2025,A1;A2,2025-03-01,2025-07-31,Vigente
```

**Why CSV over XLSX?** CSV no requiere dependencias externas (stdlib `csv`), es universalmente legible, y cualquier hoja de cálculo lo abre. Si se requiere formato (colores, estilos), migrar a openpyxl en una versión posterior.

### D8 — Router structure

| Método | Path | Guard | Capability |
|--------|------|-------|------------|
| GET | `/api/equipos/mis-equipos` | `require_authenticated` (cualquier rol autenticado) | F4.2 |
| GET | `/api/equipos` | `equipos:asignar` | F4.3 |
| GET | `/api/equipos/{materia_id}/{carrera_id}/{cohorte_id}` | `equipos:asignar` o `require_authenticated` (propio) | F4.3 |
| POST | `/api/equipos/masiva` | `equipos:asignar` | F4.4 |
| POST | `/api/equipos/clonar` | `equipos:asignar` | F4.5 |
| PATCH | `/api/equipos/vigencia` | `equipos:asignar` | F4.6 |
| GET | `/api/equipos/export` | `equipos:asignar` | F4.7 |
| GET | `/api/equipos/usuarios/search` | `equipos:asignar` | F4.4 (autocomplete) |

### D9 — Nuevos schemas

```python
class EquipoResponse(BaseModel):
    materia_id: UUID
    carrera_id: UUID
    cohorte_id: UUID
    materia_nombre: str
    carrera_nombre: str
    cohorte_nombre: str
    total_asignaciones: int
    model_config = ConfigDict(extra='forbid')

class EquipoDetailResponse(BaseModel):
    materia_id: UUID
    carrera_id: UUID
    cohorte_id: UUID
    asignaciones: list[AsignacionResponse]
    model_config = ConfigDict(extra='forbid')

class AsignacionMasivaRequest(BaseModel):
    materia_id: UUID
    carrera_id: UUID
    cohorte_id: UUID
    rol_id: UUID
    usuario_ids: list[UUID]
    vig_desde: date
    vig_hasta: date | None = None
    comisiones: str | None = None
    model_config = ConfigDict(extra='forbid')

class ClonarRequest(BaseModel):
    origen_materia_id: UUID
    origen_carrera_id: UUID
    origen_cohorte_id: UUID
    destino_materia_id: UUID
    destino_carrera_id: UUID
    destino_cohorte_id: UUID
    nueva_vig_desde: date
    nueva_vig_hasta: date | None = None
    model_config = ConfigDict(extra='forbid')

class VigenciaUpdateRequest(BaseModel):
    vig_desde: date
    vig_hasta: date | None = None
    model_config = ConfigDict(extra='forbid')

class EquipoExportRow(BaseModel):
    usuario_id: UUID
    nombre: str
    apellidos: str
    rol: str
    materia: str
    carrera: str
    cohorte: str
    comisiones: str | None
    vig_desde: date
    vig_hasta: date | None
    estado_vigencia: str
    model_config = ConfigDict(extra='forbid')

class UsuarioSearchResponse(BaseModel):
    id: UUID
    nombre: str
    apellidos: str
    legajo: str | None
    model_config = ConfigDict(from_attributes=True, extra='forbid')
```

### D10 — Auditoría

Todos los endpoints de escritura del router de equipos generan un registro de auditoría con:
- `accion = "ASIGNACION_MODIFICAR"`
- `actor_id = usuario autenticado`
- `detalle = {"operacion": "masiva"|"clonar"|"vigencia", "materia_id": ..., "carrera_id": ..., "cohorte_id": ..., "filas_afectadas": N}`

Se reusa el `AuditService` existente de C-05.

## Risks / Trade-offs

- **[Clonación con responsables fuera del equipo]** → Si el responsable de una asignación origen NO está en el equipo destino (no se clonó), el responsable_id queda como None en la copia. Esto es correcto: el coordinador debe re-asignar manualmente.
- **[Unique constraint violation en masiva]** → Si algunos usuarios ya tienen asignación activa para el mismo contexto, el bulk INSERT falla con IntegrityError y se hace rollback total. Trade-off intencional: o todas o ninguna. Alternativa sería skip-existing, pero eso introduce ambigüedad (el usuario no sabe cuáles se crearon y cuáles no).
- **[Misma materia × carrera × cohorte puede tener múltiples roles]** → El equipo se define por la clave compuesta, no por rol. Una misma materia×carrera×cohorte puede tener asignaciones de distintos roles (PROFESOR, TUTOR, NEXO). Esto es correcto y deseado.
- **[CSV export sin formato]** → CSV es funcional pero carece de estilos. Si se requiere formato Excel (colores, filtros, columnas autosize), migrar a openpyxl. Costo bajo: el cambio está encapsulado en `EquipoService.exportar_equipo()`.
- **[equipo_id como string compuesto]** → Parsear `${materia_id}:${carrera_id}:${cohorte_id}` es frágil si los UUIDs contienen `:`. Usamos `_` como separador: `${materia_id}_${carrera_id}_${cohorte_id}`. En los endpoints REST usamos query params (materia_id, carrera_id, cohorte_id) en lugar de path params con el string compuesto.

## Migration Plan

1. Extender `AsignacionRepository` con métodos bulk (get_equipo, get_equipos_agrupados, bulk_create, update_vigencia_batch, get_equipo_with_relations, search_usuarios)
2. Agregar nuevos schemas en `schemas/asignaciones.py` (EquipoResponse, EquipoDetailResponse, AsignacionMasivaRequest, ClonarRequest, VigenciaUpdateRequest, UsuarioSearchResponse)
3. Implementar `EquipoService` en `services/equipo_service.py`
4. Implementar router `api/v1/routers/equipos.py`
5. Registrar router en `main.py`
6. Tests: unitarios de EquipoService + integración de cada endpoint + TDD cycle por task (RED → GREEN → TRIANGULATE)

No hay nueva migración Alembic — C-08 opera sobre tablas existentes.

## Open Questions

- **¿Misma materia × carrera × cohorte puede tener asignaciones de diferentes roles?** Sí, y el equipo las agrupa todas. La vista "mis equipos" muestra TODAS las asignaciones del usuario, sin filtrar por un equipo específico.
- **¿El endpoint de mis-equipos debe incluir asignaciones vencidas?** Sí, con filtro por defecto "vigentes" y opción de mostrar "todas". El coordinador necesita ver el histórico.
- **¿La búsqueda de usuarios (RN-30) busca en nombre, apellido, legajo?** Sí, busca en nombre, apellidos y legajo mediante ILIKE. Límite: 20 resultados.
