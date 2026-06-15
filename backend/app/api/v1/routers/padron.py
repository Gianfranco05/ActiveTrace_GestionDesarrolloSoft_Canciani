"""Padron router — import, preview, confirm, list, vaciar."""

import uuid

from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import (
    UserSession,
    get_db,
    require_permission,
    require_permission_return_user,
)
from app.schemas.common import ListResponse
from app.schemas.padron import (
    EntradaPadronResponse,
    ImportConfirmRequest,
    ImportPreviewResponse,
    VaciarResponse,
    VersionPadronResponse,
)
from app.services.padron_service import PadronService

router = APIRouter(prefix="/api/v1/padron", tags=["padron"])


@router.post("/importar/preview", response_model=ImportPreviewResponse)
async def preview_import(
    file: UploadFile,
    _: None = Depends(require_permission("padron:cargar")),
    current_user: UserSession = Depends(require_permission_return_user("padron:cargar")),
    db: AsyncSession = Depends(get_db),
):
    content = await file.read()
    svc = PadronService(db, current_user.tenant_id, current_user.user_id)
    result = svc.preview(content, file.filename)
    return ImportPreviewResponse(**result)


@router.post("/importar/confirmar", response_model=VersionPadronResponse, status_code=201)
async def confirm_import(
    body: ImportConfirmRequest,
    _: None = Depends(require_permission("padron:cargar")),
    current_user: UserSession = Depends(require_permission_return_user("padron:cargar")),
    db: AsyncSession = Depends(get_db),
):
    svc = PadronService(db, current_user.tenant_id, current_user.user_id)
    version = await svc.confirm_import(
        entries=body.entries,
        materia_id=body.materia_id,
        cohorte_id=body.cohorte_id,
    )
    return VersionPadronResponse.model_validate(version)


@router.get("/versiones", response_model=ListResponse[VersionPadronResponse])
async def list_versiones(
    _: None = Depends(require_permission("padron:ver")),
    current_user: UserSession = Depends(require_permission_return_user("padron:ver")),
    db: AsyncSession = Depends(get_db),
    materia_id: uuid.UUID | None = None,
    cohorte_id: uuid.UUID | None = None,
    offset: int = 0,
    limit: int = 100,
):
    svc = PadronService(db, current_user.tenant_id, current_user.user_id)
    items, total = await svc.list_versions(
        materia_id=materia_id,
        cohorte_id=cohorte_id,
        offset=offset,
        limit=limit,
    )
    return ListResponse(
        items=[VersionPadronResponse.model_validate(v) for v in items],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/versiones/{id}", response_model=VersionPadronResponse)
async def get_version(
    id: uuid.UUID,
    _: None = Depends(require_permission("padron:ver")),
    current_user: UserSession = Depends(require_permission_return_user("padron:ver")),
    db: AsyncSession = Depends(get_db),
):
    svc = PadronService(db, current_user.tenant_id, current_user.user_id)
    version = await svc.get_version(id)
    return VersionPadronResponse.model_validate(version)


@router.get("/versiones/{id}/entradas", response_model=ListResponse[EntradaPadronResponse])
async def list_entradas(
    id: uuid.UUID,
    _: None = Depends(require_permission("padron:ver")),
    current_user: UserSession = Depends(require_permission_return_user("padron:ver")),
    db: AsyncSession = Depends(get_db),
    offset: int = 0,
    limit: int = 100,
):
    svc = PadronService(db, current_user.tenant_id, current_user.user_id)
    items, total = await svc.get_entries(id, offset, limit)
    return ListResponse(
        items=[EntradaPadronResponse.model_validate(e) for e in items],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.post("/versiones/{id}/vaciar", response_model=VaciarResponse)
async def vaciar_version(
    id: uuid.UUID,
    _: None = Depends(require_permission("padron:cargar")),
    current_user: UserSession = Depends(require_permission_return_user("padron:cargar")),
    db: AsyncSession = Depends(get_db),
):
    svc = PadronService(db, current_user.tenant_id, current_user.user_id)
    count = await svc.vaciar_version(id)
    return VaciarResponse(version_id=id, deleted_entries=count)
