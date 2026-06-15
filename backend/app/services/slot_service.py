import uuid
from datetime import date, timedelta

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_codes import AuditAction
from app.models.instancia_encuentro import InstanciaEncuentro
from app.models.slot_encuentro import SlotEncuentro
from app.repositories.instancia_encuentro_repository import InstanciaEncuentroRepository
from app.repositories.slot_encuentro_repository import SlotEncuentroRepository
from app.schemas.encuentros import SlotRecurrenteCreateRequest, SlotUnicoCreateRequest
from app.services.audit_service import AuditService

DIAS = {
    "Lunes": 0, "Martes": 1, "Miércoles": 2, "Jueves": 3,
    "Viernes": 4, "Sábado": 5, "Domingo": 6,
}


def _calcular_fechas_instancias(
    dia_semana: str, fecha_inicio: date, cant_semanas: int
) -> list[date]:
    target = DIAS[dia_semana]
    offset = (target - fecha_inicio.weekday()) % 7
    primera = fecha_inicio + timedelta(days=offset)
    return [primera + timedelta(weeks=i) for i in range(cant_semanas)]


async def _verificar_asignacion_es_del_usuario(
    session: AsyncSession,
    asignacion_id: uuid.UUID,
    actor_id: uuid.UUID,
    roles: list[str],
    tenant_id: uuid.UUID,
) -> None:
    from fastapi import HTTPException
    if "COORDINADOR" in roles or "ADMIN" in roles:
        return
    from app.models.asignacion import Asignacion
    result = await session.execute(
        sa.select(Asignacion).where(
            Asignacion.id == asignacion_id,
            Asignacion.usuario_id == actor_id,
            Asignacion.tenant_id == tenant_id,
            Asignacion.deleted_at.is_(None),
        )
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=403, detail="No puedes usar esta asignación")


class SlotService:
    def __init__(
        self,
        session: AsyncSession,
        tenant_id: uuid.UUID,
        audit_service: AuditService,
    ):
        self._session = session
        self._tenant_id = tenant_id
        self._slot_repo = SlotEncuentroRepository(session, tenant_id)
        self._instancia_repo = InstanciaEncuentroRepository(session, tenant_id)
        self._audit = audit_service

    async def crear_slot_recurrente(
        self, request: SlotRecurrenteCreateRequest, actor_id: uuid.UUID, roles: list[str]
    ) -> SlotEncuentro:
        await _verificar_asignacion_es_del_usuario(
            self._session, request.asignacion_id, actor_id, roles, self._tenant_id
        )

        fechas = _calcular_fechas_instancias(
            request.dia_semana.value, request.fecha_inicio, request.cant_semanas
        )

        slot = SlotEncuentro(
            tenant_id=self._tenant_id,
            asignacion_id=request.asignacion_id,
            materia_id=request.materia_id,
            titulo=request.titulo,
            hora=request.hora,
            dia_semana=request.dia_semana.value,
            fecha_inicio=request.fecha_inicio,
            cant_semanas=request.cant_semanas,
            meet_url=request.meet_url,
        )

        await self._slot_repo.create(slot)

        instancias = [
            InstanciaEncuentro(
                tenant_id=self._tenant_id,
                materia_id=request.materia_id,
                asignacion_id=request.asignacion_id,
                slot_id=slot.id,
                fecha=f,
                hora=request.hora,
                titulo=request.titulo,
                estado="Programado",
                meet_url=request.meet_url,
            )
            for f in fechas
        ]
        await self._instancia_repo.bulk_create(instancias)
        await self._session.commit()

        await self._audit.log(
            accion=AuditAction.ENCUENTRO_CREAR,
            actor_id=actor_id,
            tenant_id=self._tenant_id,
            detalle={
                "modo": "recurrente",
                "slot_id": str(slot.id),
                "materia_id": str(request.materia_id),
                "cant_instancias": len(instancias),
            },
            filas_afectadas=1,
        )

        return slot

    async def crear_slot_unico(
        self, request: SlotUnicoCreateRequest, actor_id: uuid.UUID, roles: list[str]
    ) -> SlotEncuentro:
        await _verificar_asignacion_es_del_usuario(
            self._session, request.asignacion_id, actor_id, roles, self._tenant_id
        )

        slot = SlotEncuentro(
            tenant_id=self._tenant_id,
            asignacion_id=request.asignacion_id,
            materia_id=request.materia_id,
            titulo=request.titulo,
            hora=request.hora,
            fecha_unica=request.fecha_unica,
            meet_url=request.meet_url,
        )
        await self._slot_repo.create(slot)

        instancia = InstanciaEncuentro(
            tenant_id=self._tenant_id,
            materia_id=request.materia_id,
            asignacion_id=request.asignacion_id,
            slot_id=slot.id,
            fecha=request.fecha_unica,
            hora=request.hora,
            titulo=request.titulo,
            estado="Programado",
            meet_url=request.meet_url,
        )
        await self._instancia_repo.create(instancia)
        await self._session.commit()

        await self._audit.log(
            accion=AuditAction.ENCUENTRO_CREAR,
            actor_id=actor_id,
            tenant_id=self._tenant_id,
            detalle={
                "modo": "unico",
                "slot_id": str(slot.id),
                "materia_id": str(request.materia_id),
            },
            filas_afectadas=1,
        )

        return slot

    async def listar_slots(
        self,
        materia_id: uuid.UUID | None,
        actor_id: uuid.UUID,
        tenant_id: uuid.UUID,
        roles: list[str],
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[SlotEncuentro], int]:
        if "COORDINADOR" in roles or "ADMIN" in roles:
            slots, total = await self._slot_repo.list_by_materia(
                materia_id, tenant_id, offset=offset, limit=limit
            ) if materia_id else ([], 0)
            if not materia_id:
                return [], 0
            return slots, total

        from app.models.asignacion import Asignacion
        result = await self._session.execute(
            sa.select(Asignacion.id).where(
                Asignacion.usuario_id == actor_id,
                Asignacion.tenant_id == tenant_id,
                Asignacion.deleted_at.is_(None),
            )
        )
        own_ids = [r[0] for r in result.all()]

        if not own_ids:
            return [], 0

        all_slots = []
        for aid in own_ids:
            slots, _ = await self._slot_repo.list_by_materia(
                materia_id, tenant_id, asignacion_id=aid,
                offset=0, limit=100,
            ) if materia_id else ([], 0)
            all_slots.extend(slots)

        total = len(all_slots)
        paginated = all_slots[offset:offset + limit]
        return paginated, total

    async def get_slot(
        self, slot_id: uuid.UUID, tenant_id: uuid.UUID
    ) -> SlotEncuentro | None:
        return await self._slot_repo.get_by_id(slot_id, tenant_id)

    async def soft_delete_slot(
        self, slot_id: uuid.UUID, tenant_id: uuid.UUID, actor_id: uuid.UUID
    ) -> bool:
        deleted = await self._slot_repo.soft_delete(slot_id, tenant_id)
        if deleted:
            await self._session.commit()
        return deleted
