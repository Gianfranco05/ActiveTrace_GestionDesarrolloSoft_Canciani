# Design: grupo-plus-en-materia (C-25)

## Decisión arquitectónica

La KB (§E3, PA-22) especifica `grupo_plus` como campo directo en `Materia`. La implementación actual usa tabla join `grupo_materia`. Se agrega el campo directo y se actualiza el servicio de liquidación para usarlo. La tabla `grupo_materia` se mantiene sin cambios (backward compat).

## Modelo

```python
# backend/app/models/materia.py
grupo_plus: Mapped[str | None] = mapped_column(String(50), nullable=True, default=None)
```

## Migración 020

1. `ALTER TABLE materia ADD COLUMN grupo_plus VARCHAR(50)`
2. Migrar datos: `UPDATE materia SET grupo_plus = gm.grupo FROM grupo_materia gm WHERE materia.id = gm.materia_id AND gm.deleted_at IS NULL`
3. Downgrade: `ALTER TABLE materia DROP COLUMN grupo_plus`

## LiquidacionService

Reemplazar el bloque que construye `materia_grupo` dict consultando `GrupoMateria` por una query directa a `Materia`:

```python
mat_query = select(Materia.id, Materia.grupo_plus).where(
    Materia.tenant_id == self._tenant_id,
    Materia.id.in_(materia_ids),
    Materia.grupo_plus.isnot(None),
    Materia.deleted_at.is_(None),
)
```

El resto del cálculo (conteo de comisiones × monto de Plus) permanece idéntico.

## Frontend

Agregar `grupo_plus?: string | null` a los types de Materia. No se agrega UI en este change.

## Archivos afectados

| Archivo | Cambio |
|---------|--------|
| `backend/app/models/materia.py` | +1 columna |
| `backend/alembic/versions/020_materia_grupo_plus.py` | nueva migración |
| `backend/app/schemas/estructura.py` | +1 campo en 3 schemas |
| `backend/app/services/liquidacion_service.py` | reemplazar query GrupoMateria → Materia.grupo_plus |
| `frontend/src/features/admin/types/estructura.types.ts` | +1 campo en 2 interfaces |
