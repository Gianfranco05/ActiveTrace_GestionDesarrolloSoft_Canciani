import uuid
from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_codes import AuditAction
from app.models.acknowledgment_aviso import AcknowledgmentAviso
from app.repositories.aviso_repository import AvisoRepository
from app.schemas.avisos import (
    AckResponse,
    AckStatsResponse,
    AcuseResponse,
    AlcanceEnum,
    AvisoCreateRequest,
    AvisoDetailResponse,
    AvisoListItemResponse,
    AvisoListResponse,
    AvisoResponse,
    AvisoUpdateRequest,
)
from app.services.audit_service import AuditService


class AvisoService:
    def __init__(
        self,
        session: AsyncSession,
        audit_service: AuditService,
        tenant_id: uuid.UUID,
    ):
        self._session = session
        self._repo = AvisoRepository(session, tenant_id)
        self._audit = audit_service
        self._tenant_id = tenant_id

    async def create(
        self,
        data: AvisoCreateRequest,
        actor_id: uuid.UUID,
    ) -> AvisoResponse:
        self._validate_scope(data)
        if data.inicio_en >= data.fin_en:
            raise HTTPException(
                status_code=422,
                detail="inicio_en debe ser anterior a fin_en",
            )

        aviso_data = data.model_dump()
        aviso_data["tenant_id"] = self._tenant_id
        aviso = await self._repo.create(aviso_data)

        await self._audit.log(
            accion=AuditAction.AVISO_PUBLICAR,
            actor_id=actor_id,
            tenant_id=self._tenant_id,
            filas_afectadas=1,
        )

        return AvisoResponse.model_validate(aviso)

    async def update(
        self,
        aviso_id: uuid.UUID,
        data: AvisoUpdateRequest,
        actor_id: uuid.UUID,
    ) -> AvisoResponse:
        existing = await self._repo.get_by_id(aviso_id)
        if existing is None or existing.deleted_at is not None:
            raise HTTPException(status_code=404, detail="Aviso no encontrado")

        update_dict = data.model_dump(exclude_unset=True)

        # Build effective alcance for validation
        effective_alcance = update_dict.get("alcance", existing.alcance)
        effective_materia_id = update_dict.get("materia_id", existing.materia_id)
        if "materia_id" in update_dict and update_dict["materia_id"] is not None:
            effective_materia_id = update_dict["materia_id"]
        elif "materia_id" in update_dict and update_dict["materia_id"] is None:
            effective_materia_id = None

        effective_cohorte_id = update_dict.get("cohorte_id", existing.cohorte_id)
        if "cohorte_id" in update_dict and update_dict["cohorte_id"] is not None:
            effective_cohorte_id = update_dict["cohorte_id"]
        elif "cohorte_id" in update_dict and update_dict["cohorte_id"] is None:
            effective_cohorte_id = None

        effective_rol = update_dict.get("rol_destino", existing.rol_destino)
        if "rol_destino" in update_dict:
            effective_rol = update_dict["rol_destino"]

        # Validate scope with effective values
        self._validate_scope_dict(effective_alcance, effective_materia_id, effective_cohorte_id, effective_rol)

        # Validate vigencia if both provided
        inicio = update_dict.get("inicio_en", existing.inicio_en)
        fin = update_dict.get("fin_en", existing.fin_en)
        if inicio is not None and fin is not None and inicio >= fin:
            raise HTTPException(
                status_code=422,
                detail="inicio_en debe ser anterior a fin_en",
            )

        updated = await self._repo.update_aviso(aviso_id, update_dict)
        if updated is None:
            raise HTTPException(status_code=404, detail="Aviso no encontrado")

        await self._audit.log(
            accion=AuditAction.AVISO_MODIFICAR,
            actor_id=actor_id,
            tenant_id=self._tenant_id,
            filas_afectadas=1,
        )

        return AvisoResponse.model_validate(updated)

    async def soft_delete(
        self,
        aviso_id: uuid.UUID,
        actor_id: uuid.UUID,
    ) -> None:
        existing = await self._repo.get_by_id(aviso_id)
        if existing is None or existing.deleted_at is not None:
            raise HTTPException(status_code=404, detail="Aviso no encontrado")

        await self._repo.soft_delete_aviso(aviso_id)

        await self._audit.log(
            accion=AuditAction.AVISO_ELIMINAR,
            actor_id=actor_id,
            tenant_id=self._tenant_id,
            filas_afectadas=1,
        )

    async def get_by_id(
        self,
        aviso_id: uuid.UUID,
        usuario_id: uuid.UUID,
    ) -> AvisoDetailResponse:
        aviso = await self._repo.get_aviso_detail(aviso_id)
        if aviso is None:
            raise HTTPException(status_code=404, detail="Aviso no encontrado")

        ack = await self._repo.get_ack(aviso_id, usuario_id)
        acknowledged = ack is not None

        response_dict = AvisoResponse.model_validate(aviso).model_dump()
        response_dict["acknowledged"] = acknowledged
        return AvisoDetailResponse(**response_dict)

    async def list_visibles(
        self,
        usuario_id: uuid.UUID,
        offset: int,
        limit: int,
        activo: bool | None = None,
        alcance: str | None = None,
        busqueda: str | None = None,
        admin: bool = False,
    ) -> AvisoListResponse:
        items, total = await self._repo.list_visibles(
            usuario_id, offset, limit,
            activo=activo, alcance=alcance, busqueda=busqueda,
            admin=admin,
        )

        list_items = []
        for aviso in items:
            ack = await self._repo.get_ack(aviso.id, usuario_id)
            list_items.append(
                AvisoListItemResponse(
                    id=aviso.id,
                    alcance=AlcanceEnum(aviso.alcance),
                    severidad=aviso.severidad,
                    titulo=aviso.titulo,
                    inicio_en=aviso.inicio_en,
                    fin_en=aviso.fin_en,
                    orden=aviso.orden,
                    activo=aviso.activo,
                    requiere_ack=aviso.requiere_ack,
                    acknowledged=ack is not None,
                    created_at=aviso.created_at,
                )
            )

        return AvisoListResponse(
            items=list_items,
            total=total,
            offset=offset,
            limit=limit,
        )

    async def acknowledge(
        self,
        aviso_id: uuid.UUID,
        usuario_id: uuid.UUID,
        actor_id: uuid.UUID,
    ) -> tuple[AckResponse, int]:
        aviso = await self._repo.get_aviso_detail(aviso_id)
        if aviso is None:
            raise HTTPException(status_code=404, detail="Aviso no encontrado")

        if not aviso.requiere_ack:
            raise HTTPException(
                status_code=422,
                detail="Este aviso no requiere confirmación de lectura",
            )

        now_utc = datetime.now(UTC)
        if aviso.inicio_en > now_utc or aviso.fin_en < now_utc:
            raise HTTPException(status_code=404, detail="Aviso no encontrado")

        is_visible = await self._repo.is_visible_by_scope(aviso_id, usuario_id)
        if not is_visible:
            raise HTTPException(status_code=404, detail="Aviso no encontrado")

        ack = AcknowledgmentAviso(
            aviso_id=aviso_id,
            usuario_id=usuario_id,
        )
        result = await self._repo.create_ack(ack)

        if result is None:
            existing = await self._repo.get_ack(aviso_id, usuario_id)
            return AckResponse.model_validate(existing), 200

        await self._audit.log(
            accion=AuditAction.AVISO_CONFIRMAR,
            actor_id=actor_id,
            tenant_id=self._tenant_id,
            filas_afectadas=1,
        )

        return AckResponse.model_validate(result), 201

    async def get_stats(
        self,
        aviso_id: uuid.UUID,
    ) -> AckStatsResponse:
        aviso = await self._repo.get_aviso_detail(aviso_id)
        if aviso is None:
            raise HTTPException(status_code=404, detail="Aviso no encontrado")

        total_views = await self._repo.count_distinct_users(aviso_id)
        total_acks = await self._repo.count_acks(aviso_id)
        pendientes_ack = max(0, total_views - total_acks)

        return AckStatsResponse(
            aviso_id=aviso_id,
            total_views=total_views,
            total_acks=total_acks,
            pendientes_ack=pendientes_ack,
        )

    def _validate_scope(self, data: AvisoCreateRequest) -> None:
        self._validate_scope_dict(
            str(data.alcance.value),
            data.materia_id,
            data.cohorte_id,
            data.rol_destino,
        )

    def _validate_scope_dict(
        self,
        alcance: str,
        materia_id: uuid.UUID | None,
        cohorte_id: uuid.UUID | None,
        rol_destino: str | None,
    ) -> None:
        if alcance == "Global":
            if materia_id is not None or cohorte_id is not None or rol_destino is not None:
                raise HTTPException(
                    status_code=422,
                    detail="Alcance Global no requiere materia_id, cohorte_id ni rol_destino",
                )
        elif alcance == "PorMateria":
            if materia_id is None:
                raise HTTPException(
                    status_code=422,
                    detail="materia_id es requerido para alcance PorMateria",
                )
        elif alcance == "PorCohorte":
            if cohorte_id is None:
                raise HTTPException(
                    status_code=422,
                    detail="cohorte_id es requerido para alcance PorCohorte",
                )
        elif alcance == "PorRol":
            if rol_destino is None:
                raise HTTPException(
                    status_code=422,
                    detail="rol_destino es requerido para alcance PorRol",
                )

    async def get_acuses(self, aviso_id: uuid.UUID) -> list[AcuseResponse]:
        rows = await self._repo.list_acks(aviso_id)
        return [
            AcuseResponse(
                id=row["id"],
                aviso_id=row["aviso_id"],
                usuario_id=row["usuario_id"],
                usuario_nombre=row["usuario_nombre"],
                confirmado=row["confirmado"],
                confirmado_at=row["confirmado_at"],
            )
            for row in rows
        ]
