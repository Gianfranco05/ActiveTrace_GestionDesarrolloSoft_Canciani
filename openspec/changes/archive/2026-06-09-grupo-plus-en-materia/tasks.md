# Tasks: grupo-plus-en-materia (C-25)

## 1. Modelo
- [x] 1.1 Agregar `grupo_plus: Mapped[str | None]` a `backend/app/models/materia.py`

## 2. Migración
- [x] 2.1 Crear `backend/alembic/versions/020_materia_grupo_plus.py`
- [x] 2.2 Implementar upgrade: ADD COLUMN + migrar datos desde grupo_materia
- [x] 2.3 Implementar downgrade: DROP COLUMN

## 3. Schemas
- [x] 3.1 Agregar `grupo_plus` a `MateriaCreate`, `MateriaUpdate`, `MateriaResponse` en `backend/app/schemas/estructura.py`

## 4. LiquidacionService
- [x] 4.1 Reemplazar query a `GrupoMateria` con lectura directa de `Materia.grupo_plus`
- [x] 4.2 Importar `Materia` en `liquidacion_service.py` si no está importado

## 5. Frontend
- [x] 5.1 Agregar `grupo_plus?: string | null` a `Materia` interface
- [x] 5.2 Agregar `grupo_plus?: string | null` a `CreateMateriaPayload` interface

## 6. Verificación
- [x] 6.1 Correr tests de materia y liquidacion (backend) → 1324 passed, 2 skipped
- [x] 6.2 Correr tests frontend → 117 passed
