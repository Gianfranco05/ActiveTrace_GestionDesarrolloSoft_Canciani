import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import (
    UserSession,
    get_db,
    require_permission_return_user,
)
from app.repositories.carrera_repository import CarreraRepository
from app.repositories.cohorte_repository import CohorteRepository
from app.repositories.materia_repository import MateriaRepository
from app.schemas.estructura import (
    CarreraCreate,
    CarreraResponse,
    CarreraUpdate,
    CohorteCreate,
    CohorteResponse,
    CohorteUpdate,
    EstructuraListResponse,
    MateriaCreate,
    MateriaResponse,
    MateriaUpdate,
)
from app.services.estructura_service import CohorteService

router = APIRouter(prefix="/api/v1/estructura", tags=["estructura"])

# --- Carreras ---

carreras_router = APIRouter(prefix="/carreras")


@carreras_router.get("", response_model=EstructuraListResponse)
async def list_carreras(
    current_user: UserSession = Depends(require_permission_return_user("estructura:gestionar")),
    db: AsyncSession = Depends(get_db),
    offset: int = 0,
    limit: int = 100,
):
    repo = CarreraRepository(db, current_user.tenant_id)
    items = await repo.list()
    return EstructuraListResponse(
        items=[CarreraResponse.model_validate(c) for c in items],
        total=len(items),
        offset=offset,
        limit=limit,
    )


@carreras_router.post("", response_model=CarreraResponse, status_code=201)
async def create_carrera(
    body: CarreraCreate,
    current_user: UserSession = Depends(require_permission_return_user("estructura:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    repo = CarreraRepository(db, current_user.tenant_id)
    data = body.model_dump(exclude_none=True)
    data.pop("estado", None) if body.estado is None else None
    try:
        entity = await repo.create(data)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Carrera codigo already exists") from None
    return entity


@carreras_router.get("/{id}", response_model=CarreraResponse)
async def get_carrera(
    id: uuid.UUID,
    current_user: UserSession = Depends(require_permission_return_user("estructura:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    repo = CarreraRepository(db, current_user.tenant_id)
    entity = await repo.get(id)
    if not entity:
        raise HTTPException(status_code=404, detail="Carrera not found")
    return entity


@carreras_router.put("/{id}", response_model=CarreraResponse)
async def update_carrera(
    id: uuid.UUID,
    body: CarreraUpdate,
    current_user: UserSession = Depends(require_permission_return_user("estructura:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    repo = CarreraRepository(db, current_user.tenant_id)
    data = body.model_dump(exclude_none=True)
    if not data:
        raise HTTPException(status_code=400, detail="No fields to update")
    entity = await repo.update(id, data)
    if not entity:
        raise HTTPException(status_code=404, detail="Carrera not found")
    return entity


@carreras_router.delete("/{id}", status_code=204)
async def delete_carrera(
    id: uuid.UUID,
    current_user: UserSession = Depends(require_permission_return_user("estructura:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    repo = CarreraRepository(db, current_user.tenant_id)
    deleted = await repo.soft_delete(id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Carrera not found")


@carreras_router.patch("/{id}/estado", response_model=CarreraResponse)
async def toggle_carrera_estado(
    id: uuid.UUID,
    current_user: UserSession = Depends(require_permission_return_user("estructura:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    repo = CarreraRepository(db, current_user.tenant_id)
    entity = await repo.get(id)
    if not entity:
        raise HTTPException(status_code=404, detail="Carrera not found")
    entity.estado = "Inactiva" if entity.estado == "Activa" else "Activa"
    await db.commit()
    await db.refresh(entity)
    return entity

router.include_router(carreras_router)

# --- Cohortes ---

cohortes_router = APIRouter(prefix="/cohortes")


@cohortes_router.get("", response_model=EstructuraListResponse)
async def list_cohortes(
    current_user: UserSession = Depends(require_permission_return_user("estructura:gestionar")),
    db: AsyncSession = Depends(get_db),
    offset: int = 0,
    limit: int = 100,
    carrera_id: uuid.UUID | None = None,
):
    repo = CohorteRepository(db, current_user.tenant_id)
    if carrera_id:
        items = await repo.get_by_carrera(carrera_id)
    else:
        items = await repo.list()
    return EstructuraListResponse(
        items=[CohorteResponse.model_validate(c) for c in items],
        total=len(items),
        offset=offset,
        limit=limit,
    )


@cohortes_router.post("", response_model=CohorteResponse, status_code=201)
async def create_cohorte(
    body: CohorteCreate,
    current_user: UserSession = Depends(require_permission_return_user("estructura:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    repo = CohorteRepository(db, current_user.tenant_id)
    service = CohorteService(repo, db, current_user.tenant_id)
    data = body.model_dump(exclude_none=True)
    data.pop("estado", None) if body.estado is None else None
    try:
        entity = await service.create(data)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Cohorte name already exists") from None
    return entity


@cohortes_router.get("/{id}", response_model=CohorteResponse)
async def get_cohorte(
    id: uuid.UUID,
    current_user: UserSession = Depends(require_permission_return_user("estructura:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    repo = CohorteRepository(db, current_user.tenant_id)
    entity = await repo.get(id)
    if not entity:
        raise HTTPException(status_code=404, detail="Cohorte not found")
    return entity


@cohortes_router.put("/{id}", response_model=CohorteResponse)
async def update_cohorte(
    id: uuid.UUID,
    body: CohorteUpdate,
    current_user: UserSession = Depends(require_permission_return_user("estructura:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    repo = CohorteRepository(db, current_user.tenant_id)
    service = CohorteService(repo, db, current_user.tenant_id)
    data = body.model_dump(exclude_none=True)
    if not data:
        raise HTTPException(status_code=400, detail="No fields to update")
    try:
        entity = await service.update(id, data)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Cohorte name already exists") from None
    if not entity:
        raise HTTPException(status_code=404, detail="Cohorte not found")
    return entity


@cohortes_router.delete("/{id}", status_code=204)
async def delete_cohorte(
    id: uuid.UUID,
    current_user: UserSession = Depends(require_permission_return_user("estructura:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    repo = CohorteRepository(db, current_user.tenant_id)
    deleted = await repo.soft_delete(id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Cohorte not found")


@cohortes_router.patch("/{id}/estado", response_model=CohorteResponse)
async def toggle_cohorte_estado(
    id: uuid.UUID,
    current_user: UserSession = Depends(require_permission_return_user("estructura:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    repo = CohorteRepository(db, current_user.tenant_id)
    entity = await repo.get(id)
    if not entity:
        raise HTTPException(status_code=404, detail="Cohorte not found")
    entity.estado = "Inactiva" if entity.estado == "Activa" else "Activa"
    await db.commit()
    await db.refresh(entity)
    return entity


router.include_router(cohortes_router)

# --- Materias ---

materias_router = APIRouter(prefix="/materias")


@materias_router.get("", response_model=EstructuraListResponse)
async def list_materias(
    current_user: UserSession = Depends(require_permission_return_user("estructura:gestionar")),
    db: AsyncSession = Depends(get_db),
    offset: int = 0,
    limit: int = 100,
):
    repo = MateriaRepository(db, current_user.tenant_id)
    items = await repo.list()
    return EstructuraListResponse(
        items=[MateriaResponse.model_validate(c) for c in items],
        total=len(items),
        offset=offset,
        limit=limit,
    )


@materias_router.post("", response_model=MateriaResponse, status_code=201)
async def create_materia(
    body: MateriaCreate,
    current_user: UserSession = Depends(require_permission_return_user("estructura:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    from app.models.materia_carrera import MateriaCarrera

    repo = MateriaRepository(db, current_user.tenant_id)
    data = body.model_dump(exclude={"carrera_ids"}, exclude_none=True)
    data.pop("estado", None) if body.estado is None else None
    try:
        entity = await repo.create(data)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Materia codigo already exists") from None

    # Create materia_carrera associations
    for cid in body.carrera_ids:
        db.add(MateriaCarrera(
            materia_id=entity.id,
            carrera_id=cid,
            tenant_id=current_user.tenant_id,
        ))
    await db.commit()

    return entity


@materias_router.get("/{id}", response_model=MateriaResponse)
async def get_materia(
    id: uuid.UUID,
    current_user: UserSession = Depends(require_permission_return_user("estructura:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    repo = MateriaRepository(db, current_user.tenant_id)
    entity = await repo.get(id)
    if not entity:
        raise HTTPException(status_code=404, detail="Materia not found")
    return entity


@materias_router.put("/{id}", response_model=MateriaResponse)
async def update_materia(
    id: uuid.UUID,
    body: MateriaUpdate,
    current_user: UserSession = Depends(require_permission_return_user("estructura:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    from app.models.materia_carrera import MateriaCarrera

    repo = MateriaRepository(db, current_user.tenant_id)
    data = body.model_dump(exclude={"carrera_ids"}, exclude_none=True)
    if not data and body.carrera_ids is None:
        raise HTTPException(status_code=400, detail="No fields to update")
    if data:
        entity = await repo.update(id, data)
        if not entity:
            raise HTTPException(status_code=404, detail="Materia not found")

    # Update carrera associations if provided
    if body.carrera_ids is not None:
        # Soft-delete existing
        existing = await db.execute(
            select(MateriaCarrera).where(
                MateriaCarrera.materia_id == id,
                MateriaCarrera.deleted_at.is_(None),
            )
        )
        for mc in existing.scalars().all():
            mc.deleted_at = func.now()
        # Create new
        for cid in body.carrera_ids:
            db.add(MateriaCarrera(
                materia_id=id,
                carrera_id=cid,
                tenant_id=current_user.tenant_id,
            ))
        await db.commit()

    return entity


@materias_router.delete("/{id}", status_code=204)
async def delete_materia(
    id: uuid.UUID,
    current_user: UserSession = Depends(require_permission_return_user("estructura:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    repo = MateriaRepository(db, current_user.tenant_id)
    deleted = await repo.soft_delete(id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Materia not found")


@materias_router.patch("/{id}/estado", response_model=MateriaResponse)
async def toggle_materia_estado(
    id: uuid.UUID,
    current_user: UserSession = Depends(require_permission_return_user("estructura:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    repo = MateriaRepository(db, current_user.tenant_id)
    entity = await repo.get(id)
    if not entity:
        raise HTTPException(status_code=404, detail="Materia not found")
    entity.estado = "Inactiva" if entity.estado == "Activa" else "Activa"
    await db.commit()
    await db.refresh(entity)
    return entity


router.include_router(materias_router)
