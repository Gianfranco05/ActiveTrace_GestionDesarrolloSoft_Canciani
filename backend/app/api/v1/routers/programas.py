import uuid

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import (
    UserSession,
    get_db,
    require_permission_return_user,
)
from app.repositories.programa_materia_repository import ProgramaMateriaRepository
from app.schemas.programas import ProgramaMateriaCreateRequest, ProgramaMateriaResponse
from app.services.programa_service import ProgramaService

router = APIRouter(prefix="/api/programas", tags=["programas"])


@router.post("", response_model=ProgramaMateriaResponse, status_code=201)
async def upload_programa(
    archivo: UploadFile = File(...),
    materia_id: uuid.UUID = Form(...),
    carrera_id: uuid.UUID = Form(...),
    cohorte_id: uuid.UUID = Form(...),
    titulo: str = Form(...),
    current_user: UserSession = Depends(require_permission_return_user("estructura:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    repo = ProgramaMateriaRepository(db, current_user.tenant_id)
    svc = ProgramaService(db, repo)
    request = ProgramaMateriaCreateRequest(
        materia_id=materia_id,
        carrera_id=carrera_id,
        cohorte_id=cohorte_id,
        titulo=titulo,
    )
    return await svc.upload_programa(archivo, request, current_user.tenant_id, current_user.user_id)


@router.get("")
async def list_programas(
    current_user: UserSession = Depends(require_permission_return_user("estructura:gestionar")),
    db: AsyncSession = Depends(get_db),
    materia_id: uuid.UUID | None = None,
    carrera_id: uuid.UUID | None = None,
    cohorte_id: uuid.UUID | None = None,
    offset: int = 0,
    limit: int = 20,
):
    repo = ProgramaMateriaRepository(db, current_user.tenant_id)
    svc = ProgramaService(db, repo)
    items, total = await svc.listar(
        materia_id=materia_id,
        carrera_id=carrera_id,
        cohorte_id=cohorte_id,
        offset=offset,
        limit=limit,
        tenant_id=current_user.tenant_id,
    )
    return {"items": [ProgramaMateriaResponse.model_validate(i) for i in items], "total": total, "offset": offset, "limit": limit}


@router.get("/{id}", response_model=ProgramaMateriaResponse)
async def get_programa(
    id: uuid.UUID,
    current_user: UserSession = Depends(require_permission_return_user("estructura:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    repo = ProgramaMateriaRepository(db, current_user.tenant_id)
    svc = ProgramaService(db, repo)
    return await svc.obtener(id, current_user.tenant_id)


@router.delete("/{id}", status_code=204)
async def delete_programa(
    id: uuid.UUID,
    current_user: UserSession = Depends(require_permission_return_user("estructura:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    repo = ProgramaMateriaRepository(db, current_user.tenant_id)
    svc = ProgramaService(db, repo)
    await svc.eliminar(id, current_user.tenant_id, current_user.user_id)
