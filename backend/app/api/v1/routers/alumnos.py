from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import UserSession, get_db, require_permission, require_permission_return_user
from app.schemas.alumno import EstadoAcademicoResponse
from app.services.alumno_service import AlumnoService

router = APIRouter(prefix="/api/v1/alumnos", tags=["alumnos"])


@router.get("/estado-academico", response_model=EstadoAcademicoResponse)
async def get_estado_academico(
    _: None = Depends(require_permission("estado_academico:ver")),
    current_user: UserSession = Depends(require_permission_return_user("estado_academico:ver")),
    db: AsyncSession = Depends(get_db),
):
    svc = AlumnoService(db, current_user.tenant_id, current_user.user_id)
    return await svc.get_estado_academico()
