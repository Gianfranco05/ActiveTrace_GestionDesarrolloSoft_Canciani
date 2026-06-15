## Why

La KB (04_modelo_de_datos.md §E3, PA-22) establece que el mapeo materia→grupo de Plus salarial debe almacenarse como un campo directo `grupo_plus` en la entidad `Materia`. La implementación actual usa una tabla join separada `grupo_materia` (creada en C-18). Ambas funcionan, pero la KB es la fuente de verdad del dominio y el campo directo es más simple, más rápido de consultar y elimina una query JOIN en el cálculo de liquidación.

## What Changes

- **Modelo `Materia`**: agregar campo nullable `grupo_plus: str | None` (máx 50 chars).
- **Migración Alembic 020**: agrega columna `grupo_plus` a tabla `materia` y migra datos existentes desde `grupo_materia`.
- **Schemas Pydantic**: agregar `grupo_plus` a `MateriaCreate`, `MateriaUpdate`, `MateriaResponse`.
- **LiquidacionService**: reemplazar query a `GrupoMateria` con lectura directa de `Materia.grupo_plus`.
- **Frontend types**: agregar `grupo_plus?: string | null` a `Materia` y `CreateMateriaPayload`.

## Non-goals

- No se depreca ni elimina la tabla `grupo_materia` (queda como legacy para backward compat).
- No se modifica el modelo `GrupoMateria` ni sus endpoints existentes.
- No se agrega UI para editar `grupo_plus` en el frontend (se hace vía API directa o en un change futuro).

## Capabilities

### Modified Capabilities

- **estructura-academica**: `Materia` ahora incluye `grupo_plus` en create/update/response.
- **liquidaciones-y-honorarios**: el cálculo de Plus usa `Materia.grupo_plus` en vez de `GrupoMateria`.

## Governance

**MEDIO** — modifica lógica de dominio (liquidaciones) y modelo de datos. No toca auth, tenancy ni RBAC core.
