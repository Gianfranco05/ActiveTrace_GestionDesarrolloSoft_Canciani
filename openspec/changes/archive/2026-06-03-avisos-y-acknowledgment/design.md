## Context

C-06 entregó Carrera, Cohorte y Materia. C-07 entregó Usuario, Asignacion y el puente identidad-autorización. C-04 estableció el RBAC fino con el permiso `avisos:publicar` ya seedeado para COORDINADOR y ADMIN, y `aviso:confirmar` para todos los roles. Ahora C-15 implementa el tablón de avisos institucionales (F3.5) con dos nuevas tablas: `Aviso` y `AcknowledgmentAviso`, más un servicio de dominio que orquesta el filtrado de audiencia por scope y la confirmación de lectura.

La complejidad está en: (1) el filtrado multidimensional de avisos visibles por usuario (rol + materias asignadas + cohortes asignadas + ventana de vigencia + estado de ack), (2) la idempotencia del acknowledgment, y (3) los contadores derivados de `AcknowledgmentAviso` sin denormalizar.

Governance es **MEDIO** — es lógica de dominio sin riesgo de corrupción de datos sensibles ni seguridad crítica.

## Goals / Non-Goals

**Goals:**
- Modelos `Aviso` y `AcknowledgmentAviso` con migración Alembic
- `AvisoService` con operaciones: `create`, `update`, `soft_delete`, `get_by_id`, `list_visibles` (filtrado por audiencia), `acknowledge` (idempotente), `get_stats`
- `POST /api/avisos` — crear aviso (guard `avisos:publicar`)
- `PUT /api/avisos/{aviso_id}` — editar aviso
- `DELETE /api/avisos/{aviso_id}` — soft-delete aviso
- `GET /api/avisos` — listar avisos visibles por destinatario (según rol/alcance/cohorte/materia)
- `GET /api/avisos/{aviso_id}` — detalle de aviso con flag `acknowledged`
- `POST /api/avisos/{aviso_id}/ack` — confirmar lectura (idempotente)
- `GET /api/avisos/{aviso_id}/ack/stats` — contadores de vistas y confirmaciones
- Auditoría `AVISO_PUBLICAR`, `AVISO_MODIFICAR`, `AVISO_ELIMINAR`, `AVISO_CONFIRMAR`
- Validación de scope: materia_id requerido si alcance=PorMateria, cohorte_id si PorCohorte, rol_destino si PorRol
- Validación de vigencia: `inicio_en < fin_en`

**Non-Goals:**
- Frontend UI para tablón de avisos — C-23 (frontend-coordinacion) y C-24
- Notificaciones push/email cuando se publica un aviso — fuera del scope de C-15
- Edición del contenido enriquecido (WYSIWYG) — se acepta texto plano/markdown; el renderizado es responsabilidad del frontend
- Historial de versiones de un aviso editado — no hay versionado de contenido
- Export de reportes de acknowledgment — no requerido en F3.5

## Decisions

### D1 — AvisoRepository: repositorio nuevo, no extensión de otro

Se crea `AvisoRepository` como un repositorio independiente para operaciones sobre `Aviso` y `AcknowledgmentAviso`. Sigue el patrón `BaseRepository[Modelo]` de C-02.

```python
class AvisoRepository(BaseRepository[Aviso]):
    async def create(self, aviso: Aviso) -> Aviso: ...
    async def get_by_id(self, aviso_id: UUID, tenant_id: UUID) -> Aviso | None: ...
    async def update(self, aviso: Aviso) -> Aviso: ...
    async def soft_delete(self, aviso_id: UUID, tenant_id: UUID) -> None: ...
    async def list_visibles(
        self,
        tenant_id: UUID,
        usuario_id: UUID,
        offset: int,
        limit: int,
    ) -> tuple[list[Aviso], int]: ...

    # AcknowledgmentAviso operations
    async def get_ack(self, aviso_id: UUID, usuario_id: UUID) -> AcknowledgmentAviso | None: ...
    async def create_ack(self, ack: AcknowledgmentAviso) -> AcknowledgmentAviso: ...
    async def count_acks(self, aviso_id: UUID) -> int: ...
    async def count_distinct_users(self, aviso_id: UUID) -> int: ...
```

**Why not split into AvisoRepository and AcknowledgmentRepository?** AcknowledgmentAviso no tiene entidad propia de negocio — es un registro de interacción que solo tiene sentido en el contexto de un Aviso. Mantenerlos juntos simplifica el servicio que los orquesta.

### D2 — Filtrado de audiencia: subquery sobre Asignacion

El endpoint `GET /api/avisos` debe resolver qué avisos son visibles para el usuario autenticado. La lógica de filtrado opera sobre las `Asignacion` activas del usuario:

```python
# Pseudocódigo de la query de visibilidad
WHERE aviso.deleted_at IS NULL
  AND aviso.activo = true
  AND aviso.inicio_en <= NOW()
  AND aviso.fin_en >= NOW()
  AND (
    -- Global: siempre visible
    aviso.alcance = 'Global'
    OR
    -- PorMateria: el usuario tiene asignación a esa materia
    (aviso.alcance = 'PorMateria' AND aviso.materia_id IN (
      SELECT DISTINCT a.materia_id FROM asignaciones a
      WHERE a.usuario_id = :usuario_id AND a.tenant_id = :tenant_id
        AND a.deleted_at IS NULL AND a.vig_desde <= CURRENT_DATE
        AND (a.vig_hasta IS NULL OR a.vig_hasta >= CURRENT_DATE)
    ))
    OR
    -- PorCohorte: el usuario tiene asignación a esa cohorte
    (aviso.alcance = 'PorCohorte' AND aviso.cohorte_id IN (
      SELECT DISTINCT a.cohorte_id FROM asignaciones a
      WHERE a.usuario_id = :usuario_id AND a.tenant_id = :tenant_id
        AND a.deleted_at IS NULL AND a.vig_desde <= CURRENT_DATE
        AND (a.vig_hasta IS NULL OR a.vig_hasta >= CURRENT_DATE)
    ))
    OR
    -- PorRol: el usuario tiene una asignación con ese rol
    (aviso.alcance = 'PorRol' AND aviso.rol_destino IN (
      SELECT DISTINCT a.rol FROM asignaciones a
      WHERE a.usuario_id = :usuario_id AND a.tenant_id = :tenant_id
        AND a.deleted_at IS NULL AND a.vig_desde <= CURRENT_DATE
        AND (a.vig_hasta IS NULL OR a.vig_hasta >= CURRENT_DATE)
    ))
  )
  -- Excluir avisos con requiere_ack=true ya confirmados
  AND NOT (
    aviso.requiere_ack = true
    AND EXISTS (
      SELECT 1 FROM acknowledgment_aviso ack
      WHERE ack.aviso_id = aviso.id AND ack.usuario_id = :usuario_id
    )
  )
ORDER BY aviso.orden DESC, aviso.inicio_en DESC
```

**Why subqueries and not application-level filtering?** La paginación se rompe si filtrás en aplicación después de traer registros. Hacerlo en SQL garantiza que `LIMIT/OFFSET` opere sobre el conjunto ya filtrado.

**Alternative considered**: Traer todas las asignaciones del usuario, construir una lista de materia_ids/cohorte_ids/roles en Python, y pasarlos como arrays a la query. Esto sería más legible pero requiere dos round-trips a la DB. Para la escala esperada (cientos de avisos por tenant, no millones), la subquery es aceptable.

### D3 — AcknowledgmentAviso: INSERT ON CONFLICT DO NOTHING

La confirmación de lectura es idempotente por (aviso_id, usuario_id). Se modela con un unique constraint compuesto:

```sql
CREATE TABLE acknowledgment_aviso (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    aviso_id UUID NOT NULL REFERENCES aviso(id) ON DELETE CASCADE,
    usuario_id UUID NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,
    confirmado_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(aviso_id, usuario_id)
);
```

El servicio usa `INSERT ... ON CONFLICT (aviso_id, usuario_id) DO NOTHING` o su equivalente en SQLAlchemy:

```python
async def create_ack(self, ack: AcknowledgmentAviso) -> AcknowledgmentAviso:
    stmt = insert(AcknowledgmentAviso).values(
        aviso_id=ack.aviso_id,
        usuario_id=ack.usuario_id,
        confirmado_at=func.now(),
    ).on_conflict_do_nothing(
        index_elements=['aviso_id', 'usuario_id']
    ).returning(AcknowledgmentAviso)
    result = await self._session.execute(stmt)
    return result.scalar_one_or_none()
```

Si `scalar_one_or_none()` devuelve `None`, el servicio consulta el registro existente y devuelve 200 (en vez de 201).

**Why ON CONFLICT and not SELECT-then-INSERT?** Evita la race condition entre el check y el insert. `ON CONFLICT DO NOTHING` es atómico.

### D4 — Contadores derivados, no denormalizados

Los contadores de vistas y confirmaciones NO se almacenan en la tabla `Aviso`. Se calculan en tiempo real:

- `total_views`: `COUNT(DISTINCT usuario_id) FROM acknowledgment_aviso WHERE aviso_id = :id`
- `total_acks`: `COUNT(*) FROM acknowledgment_aviso WHERE aviso_id = :id`
- `pendientes_ack`: `total_views - total_acks` (solo significativo si `requiere_ack=true`)

**Why not denormalize?** La regla del modelo de datos es explícita (E13): "Los contadores de vistas y confirmaciones se derivan consultando `AcknowledgmentAviso`; no se almacenan como campos denormalizados". Para la escala de C-15 (docenas de avisos con cientos de confirmaciones), un `COUNT` con índice es más que suficiente. Si en el futuro la escala lo requiere, se puede agregar un contador materializado, pero no en esta iteración.

### D5 — AvisoService: patrón establecido

`AvisoService` sigue el mismo patrón que `EquipoService` (C-08): recibe `AsyncSession` + `AuditService`, orquesta repositorio + validaciones + auditoría.

```python
class AvisoService:
    def __init__(self, session: AsyncSession, audit_service: AuditService):
        self._repo = AvisoRepository(session)
        self._audit = audit_service

    async def create(self, data: AvisoCreateRequest, tenant_id: UUID, actor_id: UUID) -> AvisoResponse: ...
    async def update(self, aviso_id: UUID, data: AvisoUpdateRequest, tenant_id: UUID, actor_id: UUID) -> AvisoResponse: ...
    async def soft_delete(self, aviso_id: UUID, tenant_id: UUID, actor_id: UUID) -> None: ...
    async def get_by_id(self, aviso_id: UUID, tenant_id: UUID, usuario_id: UUID) -> AvisoDetailResponse: ...
    async def list_visibles(self, usuario_id: UUID, tenant_id: UUID, offset: int, limit: int) -> PaginatedResponse[AvisoListItemResponse]: ...
    async def acknowledge(self, aviso_id: UUID, usuario_id: UUID, tenant_id: UUID) -> AckResponse: ...
    async def get_stats(self, aviso_id: UUID, tenant_id: UUID) -> AckStatsResponse: ...
```

### D6 — Validación de scope contextual

Al crear o editar un aviso, el servicio valida las reglas de integridad del scope:

| Alcance | Validación |
|---------|-----------|
| Global | `materia_id`, `cohorte_id`, `rol_destino` deben ser null |
| PorMateria | `materia_id` requerido, existe en el tenant |
| PorCohorte | `cohorte_id` requerido, existe en el tenant |
| PorRol | `rol_destino` requerido, valor válido del enum Rol |

Esto se implementa en el servicio (no en el schema Pydantic) porque requiere consultas a la DB para validar existencia de materia/cohorte.

### D7 — Router structure

| Método | Path | Guard | Capability |
|--------|------|-------|------------|
| POST | `/api/avisos` | `avisos:publicar` | F3.5 crear |
| PUT | `/api/avisos/{aviso_id}` | `avisos:publicar` | F3.5 editar |
| DELETE | `/api/avisos/{aviso_id}` | `avisos:publicar` | F3.5 eliminar |
| GET | `/api/avisos` | `require_authenticated` | F3.5 visualizar (filtrado server-side) |
| GET | `/api/avisos/{aviso_id}` | `require_authenticated` | F3.5 detalle |
| POST | `/api/avisos/{aviso_id}/ack` | `aviso:confirmar` | RN-19 confirmar |
| GET | `/api/avisos/{aviso_id}/ack/stats` | `avisos:publicar` | RN-19 estadísticas |

### D8 — Nuevos schemas Pydantic

```python
class AvisoCreateRequest(BaseModel):
    alcance: AlcanceEnum  # Global, PorMateria, PorCohorte, PorRol
    materia_id: UUID | None = None
    cohorte_id: UUID | None = None
    rol_destino: str | None = None
    severidad: SeveridadEnum  # Info, Advertencia, Critico
    titulo: str  # max 200
    cuerpo: str
    inicio_en: datetime
    fin_en: datetime
    orden: int = 0
    activo: bool = True
    requiere_ack: bool = False
    model_config = ConfigDict(extra='forbid')

class AvisoUpdateRequest(BaseModel):
    alcance: AlcanceEnum | None = None
    materia_id: UUID | None = None
    cohorte_id: UUID | None = None
    rol_destino: str | None = None
    severidad: SeveridadEnum | None = None
    titulo: str | None = None
    cuerpo: str | None = None
    inicio_en: datetime | None = None
    fin_en: datetime | None = None
    orden: int | None = None
    activo: bool | None = None
    requiere_ack: bool | None = None
    model_config = ConfigDict(extra='forbid')

class AvisoResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    alcance: AlcanceEnum
    materia_id: UUID | None
    cohorte_id: UUID | None
    rol_destino: str | None
    severidad: SeveridadEnum
    titulo: str
    cuerpo: str
    inicio_en: datetime
    fin_en: datetime
    orden: int
    activo: bool
    requiere_ack: bool
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True, extra='forbid')

class AvisoListItemResponse(BaseModel):
    id: UUID
    alcance: AlcanceEnum
    severidad: SeveridadEnum
    titulo: str
    inicio_en: datetime
    fin_en: datetime
    orden: int
    requiere_ack: bool
    acknowledged: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True, extra='forbid')

class AvisoDetailResponse(AvisoResponse):
    acknowledged: bool
    model_config = ConfigDict(from_attributes=True, extra='forbid')

class AckResponse(BaseModel):
    aviso_id: UUID
    usuario_id: UUID
    confirmado_at: datetime
    model_config = ConfigDict(from_attributes=True, extra='forbid')

class AckStatsResponse(BaseModel):
    aviso_id: UUID
    total_views: int
    total_acks: int
    pendientes_ack: int
    model_config = ConfigDict(extra='forbid')
```

### D9 — Auditoría

| Operación | Código | filas_afectadas |
|-----------|--------|-----------------|
| Crear aviso | `AVISO_PUBLICAR` | 1 |
| Editar aviso | `AVISO_MODIFICAR` | 1 |
| Soft-delete aviso | `AVISO_ELIMINAR` | 1 |
| Confirmar aviso | `AVISO_CONFIRMAR` | 1 |

## Risks / Trade-offs

- **[Riesgo] Subqueries sobre Asignacion en cada GET /api/avisos pueden degradar con muchos avisos** → Mitigación: índices en `asignaciones(usuario_id, tenant_id)` ya existen de C-07. Para la carga esperada (cientos de avisos), las subqueries con IN sobre arrays pequeños (materias/cohortes del usuario, típicamente <10) tienen costo aceptable. Monitorear con slow query log.
- **[Riesgo] `ON CONFLICT DO NOTHING` + `returning` no devuelve la fila si hubo conflicto** → Mitigación: el servicio hace un fallback `SELECT` cuando `scalar_one_or_none()` retorna None. Esto es correcto y no introduce race condition.
- **[Trade-off] Contadores calculados en cada request de stats** → Para avisos con miles de acks podría ser lento. Aceptado por ahora; la regla del modelo de datos prohíbe denormalizar. Si se vuelve un problema, cachear con TTL corto (30s) o vista materializada.
- **[Trade-off] No hay permiso `avisos:ver` separado** → La visualización de avisos usa `require_authenticated` y filtra server-side por audiencia. Esto sigue el modelo de la KB donde "Ver avisos" no es una capacidad explícita — todo usuario autenticado ve los que le corresponden (RN-20). Si en el futuro se necesita restringir la lectura, se agrega `avisos:ver`.

## Open Questions

- Ninguna. Los permisos (`avisos:publicar`, `aviso:confirmar`) ya están seedeados en rbac-seed de C-04. Las reglas de negocio RN-18/19/20 están cerradas en la KB.
