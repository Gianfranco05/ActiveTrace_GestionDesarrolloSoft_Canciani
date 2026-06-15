import uuid

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_codes import AuditAction
from app.core.tenant_aware import get_tenant_scoped
from app.models.instancia_encuentro import InstanciaEncuentro
from app.repositories.instancia_encuentro_repository import InstanciaEncuentroRepository
from app.schemas.encuentros import InstanciaUnicaCreateRequest, InstanciaUpdateRequest
from app.services.audit_service import AuditService


class EncuentroService:
    def __init__(
        self,
        session: AsyncSession,
        tenant_id: uuid.UUID,
        audit_service: AuditService,
    ):
        self._session = session
        self._tenant_id = tenant_id
        self._repo = InstanciaEncuentroRepository(session, tenant_id)
        self._audit = audit_service

    async def crear_instancia_unica(
        self, request: InstanciaUnicaCreateRequest, actor_id: uuid.UUID,
    ) -> InstanciaEncuentro:
        instancia = InstanciaEncuentro(
            tenant_id=self._tenant_id,
            materia_id=request.materia_id,
            asignacion_id=request.asignacion_id,
            slot_id=None,
            fecha=request.fecha,
            hora=request.hora,
            titulo=request.titulo,
            estado="Programado",
            meet_url=request.meet_url,
        )
        await self._repo.create(instancia)
        await self._session.commit()

        await self._audit.log(
            accion=AuditAction.ENCUENTRO_CREAR,
            actor_id=actor_id,
            tenant_id=self._tenant_id,
            detalle={
                "modo": "instancia_unica",
                "instancia_id": str(instancia.id),
                "materia_id": str(request.materia_id),
            },
        )
        return instancia

    async def editar_instancia(
        self,
        instancia_id: uuid.UUID,
        request: InstanciaUpdateRequest,
        actor_id: uuid.UUID,
        roles: list[str],
    ) -> InstanciaEncuentro | None:
        from fastapi import HTTPException

        instancia = await self._repo.get_by_id(instancia_id, self._tenant_id)
        if instancia is None:
            return None

        if "COORDINADOR" not in roles and "ADMIN" not in roles:
            from app.models.asignacion import Asignacion
            result = await self._session.execute(
                sa.select(Asignacion).where(
                    Asignacion.id == instancia.asignacion_id,
                    Asignacion.usuario_id == actor_id,
                    Asignacion.tenant_id == self._tenant_id,
                    Asignacion.deleted_at.is_(None),
                )
            )
            if result.scalar_one_or_none() is None:
                raise HTTPException(status_code=403, detail="No puedes editar esta instancia")

        data = request.model_dump(exclude_none=True)
        for key, value in data.items():
            setattr(instancia, key, value)

        await self._session.commit()

        await self._audit.log(
            accion=AuditAction.ENCUENTRO_EDITAR,
            actor_id=actor_id,
            tenant_id=self._tenant_id,
            detalle={
                "instancia_id": str(instancia_id),
                "campos_modificados": list(data.keys()),
            },
        )
        return instancia

    async def listar_instancias(
        self,
        materia_id: uuid.UUID | None,
        slot_id: uuid.UUID | None,
        estado: str | None,
        actor_id: uuid.UUID,
        tenant_id: uuid.UUID,
        roles: list[str],
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[InstanciaEncuentro], int]:
        asignacion_id = None
        if "COORDINADOR" not in roles and "ADMIN" not in roles:
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
            items = []
            for aid in own_ids:
                chunk, _ = await self._repo.list_by_filters(
                    tenant_id, materia_id=materia_id, slot_id=slot_id,
                    estado=estado, asignacion_id=aid, offset=0, limit=100,
                )
                items.extend(chunk)
            total = len(items)
            return items[offset:offset + limit], total

        return await self._repo.list_by_filters(
            tenant_id, materia_id=materia_id, slot_id=slot_id,
            estado=estado, asignacion_id=asignacion_id,
            offset=offset, limit=limit,
        )

    async def generar_html_slot(
        self, slot_id: uuid.UUID, tenant_id: uuid.UUID
    ) -> str | None:
        from app.models.slot_encuentro import SlotEncuentro

        slot_q = sa.select(SlotEncuentro).where(
            SlotEncuentro.id == slot_id,
            SlotEncuentro.tenant_id == tenant_id,
            SlotEncuentro.deleted_at.is_(None),
        )
        result = await self._session.execute(slot_q)
        slot = result.scalar_one_or_none()
        if slot is None:
            return None

        instancias = await self._repo.list_by_slot(slot_id, tenant_id)

        partes = ['<div style="font-family:sans-serif;">']
        partes.append(f"<h2>{slot.titulo}</h2>")
        partes.append('<table style="border-collapse:collapse;width:100%;">')
        partes.append(
            '<tr style="background:#f0f0f0;"><th>Fecha</th><th>Hora</th>'
            '<th>Estado</th><th>Enlace</th><th>Grabación</th></tr>'
        )

        for i in instancias:
            estado_style = (
                'color:red;font-weight:bold;' if i.estado == "Cancelado"
                else 'color:green;' if i.estado == "Realizado" else ''
            )
            enlace = (
                f'<a href="{i.meet_url}" target="_blank">Meet</a>'
                if i.meet_url and i.estado != "Cancelado" else ""
            )
            grabacion = (
                f'<a href="{i.video_url}" target="_blank">Video</a>'
                if i.video_url else ""
            )
            partes.append(
                f'<tr><td>{i.fecha}</td><td>{i.hora}</td>'
                f'<td style="{estado_style}">{i.estado}</td>'
                f'<td>{enlace}</td><td>{grabacion}</td></tr>'
            )

        partes.append("</table>")
        partes.append("</div>")
        return "".join(partes)

    async def generar_html_materia(
        self, materia_id: uuid.UUID, tenant_id: uuid.UUID
    ) -> str | None:
        """Generate HTML for all slots and single instances of a materia."""
        from app.models.instancia_encuentro import InstanciaEncuentro
        from app.models.materia import Materia
        from app.models.slot_encuentro import SlotEncuentro

        materia = await get_tenant_scoped(self._session, Materia, materia_id, tenant_id)
        if materia is None:
            return None

        # ── Slots ──
        q_slots = sa.select(SlotEncuentro).where(
            SlotEncuentro.materia_id == materia_id,
            SlotEncuentro.tenant_id == tenant_id,
            SlotEncuentro.deleted_at.is_(None),
        )
        r_slots = await self._session.execute(q_slots)
        slots = r_slots.scalars().all()

        # ── Instancias sueltas ──
        q_inst = sa.select(InstanciaEncuentro).where(
            InstanciaEncuentro.materia_id == materia_id,
            InstanciaEncuentro.tenant_id == tenant_id,
            InstanciaEncuentro.deleted_at.is_(None),
            InstanciaEncuentro.slot_id.is_(None),
        )
        r_inst = await self._session.execute(q_inst)
        instancias = r_inst.scalars().all()

        if not slots and not instancias:
            return None

        partes = ['<div style="font-family:sans-serif;">']
        partes.append(f"<h2>{materia.nombre}</h2>")

        if slots:
            partes.append("<h3>Encuentros Recurrentes</h3>")
            for slot in slots:
                slot_insts = await self._repo.list_by_slot(slot.id, tenant_id)
                partes.append(f"<h4>{slot.titulo or 'Sin título'} — {len(slot_insts)} clases</h4>")
                partes.append('<table style="border-collapse:collapse;width:100%;margin-bottom:16px;">')
                partes.append(
                    '<tr style="background:#f0f0f0;"><th>Fecha</th><th>Hora</th>'
                    '<th>Estado</th><th>Enlace</th></tr>'
                )
                for i in slot_insts:
                    estado_color = 'red' if i.estado == "Cancelado" else 'green' if i.estado == "Realizado" else '#333'
                    estado_label = {"Programado": "Pendiente", "Realizado": "Realizado", "Cancelado": "Cancelado"}.get(i.estado, i.estado)
                    enlace = f'<a href="{i.meet_url}" target="_blank">🔗 Acceder</a>' if i.meet_url else "—"
                    hora_str = i.hora.strftime("%H:%M") if i.hora else ""
                    partes.append(
                        f'<tr><td>{i.fecha}</td><td>{hora_str}</td>'
                        f'<td style="color:{estado_color};font-weight:bold;">{estado_label}</td>'
                        f'<td>{enlace}</td></tr>'
                    )
                partes.append("</table>")

        if instancias:
            partes.append("<h3>Encuentros Únicos</h3>")
            partes.append('<table style="border-collapse:collapse;width:100%;">')
            partes.append(
                '<tr style="background:#f0f0f0;"><th>Fecha</th><th>Hora</th>'
                '<th>Título</th><th>Estado</th><th>Enlace</th></tr>'
            )
            for i in instancias:
                estado_color = 'red' if i.estado == "Cancelado" else 'green' if i.estado == "Realizado" else '#333'
                estado_label = {"Programado": "Pendiente", "Realizado": "Realizado", "Cancelado": "Cancelado"}.get(i.estado, i.estado)
                enlace = f'<a href="{i.meet_url}" target="_blank">🔗 Acceder</a>' if i.meet_url else "—"
                hora_str = i.hora.strftime("%H:%M") if i.hora else ""
                partes.append(
                    f'<tr><td>{i.fecha}</td><td>{i.hora}</td>'
                    f'<td>{i.titulo}</td>'
                    f'<td style="color:{estado_color}">{i.estado}</td>'
                    f'<td>{enlace}</td></tr>'
                )
            partes.append("</table>")

        partes.append("</div>")
        return "".join(partes)
