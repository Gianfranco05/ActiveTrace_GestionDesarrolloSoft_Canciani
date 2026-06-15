"""Calificaciones router — import, preview, confirm, reporte, umbral."""

import json
import uuid

from fastapi import APIRouter, Depends, Form, HTTPException, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import (
    UserSession,
    get_db,
    require_permission,
    require_permission_return_user,
)
from app.schemas.calificacion import (
    ImportConfirmResponse,
    ImportPreviewResponse,
    ReporteFinalizacionResponse,
    UmbralMateriaResponse,
    UmbralMateriaUpdate,
)
from app.services.calificacion_service import CalificacionService
from app.services.umbral_service import UmbralService

router = APIRouter(prefix="/api/v1/calificaciones", tags=["calificaciones"])


@router.post("/importar/preview", response_model=ImportPreviewResponse)
async def preview_import(
    file: UploadFile,
    _: None = Depends(require_permission("calificaciones:cargar")),
    current_user: UserSession = Depends(require_permission_return_user("calificaciones:cargar")),
    db: AsyncSession = Depends(get_db),
):
    content = await file.read()
    svc = CalificacionService(db, current_user.tenant_id, current_user.user_id)
    try:
        result = await svc.preview(content, file.filename)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return ImportPreviewResponse(**result)


@router.post("/importar/confirmar", response_model=ImportConfirmResponse, status_code=201)
async def confirm_import(
    file: UploadFile,
    materia_id: str = Form(...),
    cohorte_id: str = Form(...),
    actividad_mapping: str | None = Form(None),
    _: None = Depends(require_permission("calificaciones:cargar")),
    current_user: UserSession = Depends(require_permission_return_user("calificaciones:cargar")),
    db: AsyncSession = Depends(get_db),
):
    content = await file.read()
    mapping = json.loads(actividad_mapping) if actividad_mapping else None
    svc = CalificacionService(db, current_user.tenant_id, current_user.user_id)
    try:
        result = await svc.confirm_import(
            content, file.filename,
            uuid.UUID(materia_id), uuid.UUID(cohorte_id), mapping,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return ImportConfirmResponse(**result)


@router.post("/importar/reporte-finalizacion", response_model=ReporteFinalizacionResponse)
async def reporte_finalizacion(
    file: UploadFile,
    materia_id: str = Form(...),
    cohorte_id: str = Form(...),
    _: None = Depends(require_permission("calificaciones:cargar")),
    current_user: UserSession = Depends(require_permission_return_user("calificaciones:cargar")),
    db: AsyncSession = Depends(get_db),
):
    content = await file.read()
    svc = CalificacionService(db, current_user.tenant_id, current_user.user_id)
    try:
        result = await svc.reporte_finalizacion(
            content, file.filename,
            uuid.UUID(materia_id), uuid.UUID(cohorte_id),
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return ReporteFinalizacionResponse(**result)


@router.get("/umbral", response_model=UmbralMateriaResponse)
async def get_umbral(
    materia_id: uuid.UUID = Query(...),
    _: None = Depends(require_permission("calificaciones:importar")),
    current_user: UserSession = Depends(require_permission_return_user("calificaciones:importar")),
    db: AsyncSession = Depends(get_db),
):
    svc = UmbralService(db, current_user.tenant_id)
    result = await svc.get_umbral(materia_id)
    return UmbralMateriaResponse(**result)


@router.put("/umbral", response_model=UmbralMateriaResponse)
async def set_umbral(
    materia_id: uuid.UUID = Query(...),
    body: UmbralMateriaUpdate = ...,
    _: None = Depends(require_permission("calificaciones:importar")),
    current_user: UserSession = Depends(require_permission_return_user("calificaciones:importar")),
    db: AsyncSession = Depends(get_db),
):
    svc = UmbralService(db, current_user.tenant_id)
    result = await svc.set_umbral(materia_id, body.umbral_pct)
    return UmbralMateriaResponse(**result)
