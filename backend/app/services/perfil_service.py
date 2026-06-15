import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.audit_codes import AuditAction
from app.core.security import decrypt_or_none, encrypt_or_none
from app.models.usuario import Usuario
from app.schemas.perfil import PerfilResponse, PerfilUpdateRequest
from app.services.audit_service import AuditService


class PerfilService:
    def __init__(
        self,
        session: AsyncSession,
        tenant_id: uuid.UUID,
        audit_service: AuditService | None = None,
    ):
        self._session = session
        self._tenant_id = tenant_id
        self._audit = audit_service

    async def get_perfil(self, user_id: uuid.UUID, tenant_id: uuid.UUID) -> PerfilResponse:
        query = (
            select(Usuario)
            .options(selectinload(Usuario.auth_user))
            .where(
                Usuario.id == user_id,
                Usuario.tenant_id == tenant_id,
                Usuario.deleted_at.is_(None),
            )
        )
        result = await self._session.execute(query)
        usuario = result.scalar_one_or_none()
        if usuario is None:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        return PerfilResponse(
            id=usuario.id,
            tenant_id=usuario.tenant_id,
            nombre=usuario.nombre,
            apellidos=usuario.apellidos,
            email=usuario.auth_user.email if usuario.auth_user else "",
            dni=decrypt_or_none(usuario.dni),
            cuil=decrypt_or_none(usuario.cuil),
            banco=usuario.banco,
            cbu=decrypt_or_none(usuario.cbu),
            alias_cbu=decrypt_or_none(usuario.alias_cbu),
            regional=usuario.regional,
            legajo=usuario.legajo,
            legajo_profesional=usuario.legajo_profesional,
            facturador=usuario.facturador,
            estado=usuario.estado,
            created_at=usuario.created_at,
            updated_at=usuario.updated_at,
        )

    async def update_perfil(
        self,
        user_id: uuid.UUID,
        tenant_id: uuid.UUID,
        request: PerfilUpdateRequest,
    ) -> PerfilResponse:
        query = (
            select(Usuario)
            .options(selectinload(Usuario.auth_user))
            .where(
                Usuario.id == user_id,
                Usuario.tenant_id == tenant_id,
                Usuario.deleted_at.is_(None),
            )
        )
        result = await self._session.execute(query)
        usuario = result.scalar_one_or_none()
        if usuario is None:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        update_data = request.model_dump(exclude_unset=True)

        if "dni" in update_data and update_data["dni"] is not None:
            update_data["dni"] = encrypt_or_none(update_data["dni"])
        if "cbu" in update_data and update_data["cbu"] is not None:
            update_data["cbu"] = encrypt_or_none(update_data["cbu"])
        if "alias_cbu" in update_data and update_data["alias_cbu"] is not None:
            update_data["alias_cbu"] = encrypt_or_none(update_data["alias_cbu"])

        for key, value in update_data.items():
            setattr(usuario, key, value)

        await self._session.commit()
        await self._session.refresh(usuario)

        if self._audit:
            await self._audit.log(
                accion=AuditAction.PERFIL_EDITAR,
                actor_id=user_id,
                tenant_id=tenant_id,
                detalle={"campos": list(update_data.keys())},
            )

        return PerfilResponse(
            id=usuario.id,
            tenant_id=usuario.tenant_id,
            nombre=usuario.nombre,
            apellidos=usuario.apellidos,
            email=usuario.auth_user.email if usuario.auth_user else "",
            dni=decrypt_or_none(usuario.dni),
            cuil=decrypt_or_none(usuario.cuil),
            banco=usuario.banco,
            cbu=decrypt_or_none(usuario.cbu),
            alias_cbu=decrypt_or_none(usuario.alias_cbu),
            regional=usuario.regional,
            legajo=usuario.legajo,
            legajo_profesional=usuario.legajo_profesional,
            facturador=usuario.facturador,
            estado=usuario.estado,
            created_at=usuario.created_at,
            updated_at=usuario.updated_at,
        )
