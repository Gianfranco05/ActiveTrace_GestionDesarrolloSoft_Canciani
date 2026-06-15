import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_codes import AuditAction
from app.models.audit_log import AuditLog
from app.repositories.audit_repository import AuditLogRepository


class AuditService:

    def __init__(
        self,
        session: AsyncSession,
        repository: AuditLogRepository,
    ) -> None:
        self._session = session
        self._repository = repository

    async def log(
        self,
        accion: AuditAction,
        actor_id: uuid.UUID,
        tenant_id: uuid.UUID,
        detalle: dict | None = None,
        filas_afectadas: int = 0,
        impersonado_id: uuid.UUID | None = None,
        materia_id: uuid.UUID | None = None,
        ip: str | None = None,
        user_agent: str | None = None,
    ) -> AuditLog:
        entry = AuditLog(
            tenant_id=tenant_id,
            actor_id=actor_id,
            accion=accion.value if isinstance(accion, AuditAction) else accion,
            detalle=detalle,
            filas_afectadas=filas_afectadas,
            impersonado_id=impersonado_id,
            materia_id=materia_id,
            ip=ip,
            user_agent=user_agent,
        )
        return await self._repository.create(entry)
