"""Comunicaciones router — preview, enqueue, approve, cancel, list, detail."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import (
    UserSession,
    get_db,
    require_permission_return_user,
)
from app.schemas.comunicacion import (
    ApproveRequest,
    ApproveResponse,
    CancelResponse,
    ComunicacionListResponse,
    ComunicacionResponse,
    EnqueueRequest,
    EnqueueResponse,
    PreviewRequest,
    PreviewResponse,
)
from app.services.comunicacion_service import ComunicacionService

router = APIRouter(prefix="/api/comunicaciones", tags=["comunicaciones"])


@router.post("/preview", response_model=PreviewResponse)
async def preview(
    body: PreviewRequest,
    current_user: UserSession = Depends(require_permission_return_user("comunicacion:enviar")),
    db: AsyncSession = Depends(get_db),
):
    svc = ComunicacionService(db, current_user.tenant_id, current_user.user_id)
    try:
        result = await svc.preview(
            materia_id=body.materia_id,
            cohorte_id=body.cohorte_id,
            template_body=body.template_body,
            template_asunto=body.template_asunto,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return PreviewResponse(**result)


@router.post("/enviar", response_model=EnqueueResponse)
async def enqueue(
    body: EnqueueRequest,
    current_user: UserSession = Depends(require_permission_return_user("comunicacion:enviar")),
    db: AsyncSession = Depends(get_db),
):
    svc = ComunicacionService(db, current_user.tenant_id, current_user.user_id)
    try:
        result = await svc.enqueue(
            preview_token=body.preview_token,
            preview_token_timestamp=body.preview_token_timestamp,
            materia_id=body.materia_id,
            cohorte_id=body.cohorte_id,
            template_body=body.template_body,
            template_asunto=body.template_asunto,
            template_id=body.template_id,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return EnqueueResponse(**result)


@router.post("/{id}/aprobar", response_model=ApproveResponse)
async def approve_individual(
    id: uuid.UUID,
    body: ApproveRequest | None = None,
    current_user: UserSession = Depends(require_permission_return_user("comunicacion:aprobar")),
    db: AsyncSession = Depends(get_db),
):
    svc = ComunicacionService(db, current_user.tenant_id, current_user.user_id)
    try:
        result = await svc.approve(comunicacion_id=id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return ApproveResponse(**result)


@router.post("/lote/{lote_id}/aprobar", response_model=ApproveResponse)
async def approve_lote(
    lote_id: uuid.UUID,
    current_user: UserSession = Depends(require_permission_return_user("comunicacion:aprobar")),
    db: AsyncSession = Depends(get_db),
):
    svc = ComunicacionService(db, current_user.tenant_id, current_user.user_id)
    try:
        result = await svc.approve(lote_id=lote_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return ApproveResponse(**result)


@router.post("/{id}/cancelar", response_model=CancelResponse)
async def cancel_individual(
    id: uuid.UUID,
    current_user: UserSession = Depends(require_permission_return_user("comunicacion:enviar")),
    db: AsyncSession = Depends(get_db),
):
    svc = ComunicacionService(db, current_user.tenant_id, current_user.user_id)
    try:
        result = await svc.cancel(comunicacion_id=id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return CancelResponse(**result)


@router.post("/lote/{lote_id}/cancelar", response_model=CancelResponse)
async def cancel_lote(
    lote_id: uuid.UUID,
    current_user: UserSession = Depends(require_permission_return_user("comunicacion:enviar")),
    db: AsyncSession = Depends(get_db),
):
    svc = ComunicacionService(db, current_user.tenant_id, current_user.user_id)
    try:
        result = await svc.cancel(lote_id=lote_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return CancelResponse(**result)


@router.get("", response_model=ComunicacionListResponse)
async def list_comunicaciones(
    estado: str | None = Query(None),
    lote_id: uuid.UUID | None = Query(None),
    desde: str | None = Query(None),
    hasta: str | None = Query(None),
    current_user: UserSession = Depends(require_permission_return_user("comunicacion:ver")),
    db: AsyncSession = Depends(get_db),
):
    svc = ComunicacionService(db, current_user.tenant_id, current_user.user_id)
    desde_dt = None
    hasta_dt = None
    if desde:
        from datetime import datetime
        desde_dt = datetime.fromisoformat(desde)
    if hasta:
        from datetime import datetime
        hasta_dt = datetime.fromisoformat(hasta)

    items = await svc._repo.list_filtered(
        estado=estado, lote_id=lote_id, desde=desde_dt, hasta=hasta_dt,
    )
    return ComunicacionListResponse(
        items=[ComunicacionResponse.model_validate(c) for c in items],
        total=len(items),
    )


@router.get("/{id}", response_model=ComunicacionResponse)
async def get_comunicacion(
    id: uuid.UUID,
    current_user: UserSession = Depends(require_permission_return_user("comunicacion:ver")),
    db: AsyncSession = Depends(get_db),
):
    svc = ComunicacionService(db, current_user.tenant_id, current_user.user_id)
    c = await svc._repo.get_by_id(id)
    if c is None:
        raise HTTPException(status_code=404, detail="Comunicacion not found")
    return ComunicacionResponse.model_validate(c)
