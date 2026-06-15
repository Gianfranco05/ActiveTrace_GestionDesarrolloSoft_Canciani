import io
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import (
    UserSession,
    get_db,
    require_permission_return_user,
)
from app.repositories.audit_repository import AuditLogRepository
from app.schemas.guardias import (
    GuardiaCreateRequest,
    GuardiaResponse,
    GuardiasListResponse,
    GuardiaUpdateRequest,
)
from app.services.audit_service import AuditService

router = APIRouter(prefix="/api/guardias", tags=["guardias"])


def _build_audit_service(db: AsyncSession, tenant_id: uuid.UUID) -> AuditService:
    repo = AuditLogRepository(db, tenant_id)
    return AuditService(db, repo)


@router.post("", response_model=GuardiaResponse, status_code=201)
async def registrar_guardia(
    body: GuardiaCreateRequest,
    current_user: UserSession = Depends(require_permission_return_user("encuentros:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    from app.services.guardia_service import GuardiaService

    svc = GuardiaService(db, current_user.tenant_id, _build_audit_service(db, current_user.tenant_id))
    try:
        guardia = await svc.registrar_guardia(body, current_user.user_id, current_user.roles)
    except HTTPException:
        raise
    await db.refresh(guardia)
    return GuardiaResponse.model_validate(guardia)


@router.get("", response_model=GuardiasListResponse)
async def listar_guardias(
    current_user: UserSession = Depends(require_permission_return_user("encuentros:gestionar")),
    db: AsyncSession = Depends(get_db),
    materia_id: uuid.UUID | None = Query(default=None),
    carrera_id: uuid.UUID | None = Query(default=None),
    cohorte_id: uuid.UUID | None = Query(default=None),
    dia: str | None = Query(default=None),
    estado: str | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
):
    from app.models.carrera import Carrera
    from app.models.cohorte import Cohorte
    from app.models.materia import Materia
    from app.services.guardia_service import GuardiaService

    svc = GuardiaService(db, current_user.tenant_id, _build_audit_service(db, current_user.tenant_id))
    filtros = {
        "materia_id": materia_id,
        "carrera_id": carrera_id,
        "cohorte_id": cohorte_id,
        "dia": dia,
        "estado": estado,
        "offset": offset,
        "limit": limit,
    }
    items, total = await svc.listar_guardias(
        filtros, current_user.user_id, current_user.tenant_id, current_user.roles,
    )

    responses = []
    for g in items:
        resp = GuardiaResponse.model_validate(g)
        if g.materia_id:
            mat = await db.get(Materia, g.materia_id)
            resp.materia_nombre = mat.nombre if mat else None
        if g.carrera_id:
            car = await db.get(Carrera, g.carrera_id)
            resp.carrera_nombre = car.nombre if car else None
        if g.cohorte_id:
            coh = await db.get(Cohorte, g.cohorte_id)
            resp.cohorte_nombre = coh.nombre if coh else None
        responses.append(resp)

    return GuardiasListResponse(items=responses, total=total, offset=offset, limit=limit)


@router.patch("/{guardia_id}", response_model=GuardiaResponse)
async def editar_guardia(
    guardia_id: uuid.UUID,
    body: GuardiaUpdateRequest,
    current_user: UserSession = Depends(require_permission_return_user("encuentros:gestionar")),
    db: AsyncSession = Depends(get_db),
):
    from app.services.guardia_service import GuardiaService

    svc = GuardiaService(db, current_user.tenant_id, _build_audit_service(db, current_user.tenant_id))
    try:
        guardia = await svc.editar_guardia(
            guardia_id, body, current_user.user_id, current_user.roles,
        )
    except HTTPException:
        raise
    if guardia is None:
        raise HTTPException(status_code=404, detail="Guardia no encontrada")
    await db.refresh(guardia)
    return GuardiaResponse.model_validate(guardia)


@router.get("/export")
async def exportar_guardias(
    current_user: UserSession = Depends(require_permission_return_user("encuentros:gestionar")),
    db: AsyncSession = Depends(get_db),
    materia_id: uuid.UUID | None = Query(default=None),
    carrera_id: uuid.UUID | None = Query(default=None),
    cohorte_id: uuid.UUID | None = Query(default=None),
    dia: str | None = Query(default=None),
    estado: str | None = Query(default=None),
):
    from app.services.guardia_service import GuardiaService

    svc = GuardiaService(db, current_user.tenant_id, _build_audit_service(db, current_user.tenant_id))
    filtros = {
        "materia_id": materia_id,
        "carrera_id": carrera_id,
        "cohorte_id": cohorte_id,
        "dia": dia,
        "estado": estado,
    }
    csv_data = await svc.exportar_guardias(
        filtros, current_user.user_id, current_user.tenant_id, current_user.roles,
    )
    return StreamingResponse(
        io.StringIO(csv_data),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=guardias.csv"},
    )
