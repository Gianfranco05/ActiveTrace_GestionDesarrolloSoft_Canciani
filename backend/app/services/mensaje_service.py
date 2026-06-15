import uuid

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_codes import AuditAction
from app.models.mensaje import Mensaje
from app.models.usuario import Usuario
from app.repositories.mensaje_repository import MensajeRepository
from app.schemas.mensajes import (
    InboxThreadResponse,
    MensajeCreateRequest,
    MensajeReplyRequest,
    MensajeResponse,
    ThreadDetailResponse,
)
from app.services.audit_service import AuditService


def _make_mensaje_response(msg, sender_nombre="", recipient_nombre=""):
    return MensajeResponse(
        id=msg.id,
        sender_id=msg.sender_id,
        sender_nombre=sender_nombre or (
            f"{msg.sender.nombre} {msg.sender.apellidos}" if msg.sender else ""
        ),
        recipient_id=msg.recipient_id,
        recipient_nombre=recipient_nombre or (
            f"{msg.recipient.nombre} {msg.recipient.apellidos}" if msg.recipient else ""
        ),
        parent_id=msg.parent_id,
        asunto=msg.asunto,
        cuerpo=msg.cuerpo,
        leido=msg.leido,
        leido_at=msg.leido_at,
        created_at=msg.created_at,
    )


class MensajeService:
    def __init__(
        self,
        session: AsyncSession,
        tenant_id: uuid.UUID,
        audit_service: AuditService | None = None,
    ):
        self._session = session
        self._tenant_id = tenant_id
        self._repo = MensajeRepository(session, tenant_id)
        self._audit = audit_service

    async def enviar_mensaje(
        self,
        sender_id: uuid.UUID,
        tenant_id: uuid.UUID,
        request: MensajeCreateRequest,
    ) -> MensajeResponse:
        recip_q = select(Usuario).where(
            Usuario.id == request.recipient_id,
            Usuario.tenant_id == tenant_id,
            Usuario.deleted_at.is_(None),
        )
        result = await self._session.execute(recip_q)
        recipient = result.scalar_one_or_none()
        if recipient is None:
            raise HTTPException(status_code=404, detail="Destinatario no encontrado")

        msg = Mensaje(
            tenant_id=tenant_id,
            sender_id=sender_id,
            recipient_id=request.recipient_id,
            parent_id=None,
            asunto=request.asunto,
            cuerpo=request.cuerpo,
        )
        await self._repo.create(msg)
        await self._session.commit()
        await self._session.refresh(msg, ["sender", "recipient"])

        if self._audit:
            await self._audit.log(
                accion=AuditAction.MENSAJE_ENVIAR,
                actor_id=sender_id,
                tenant_id=tenant_id,
                detalle={"mensaje_id": str(msg.id), "destinatario_id": str(request.recipient_id)},
            )

        return _make_mensaje_response(msg)

    async def listar_inbox(
        self, user_id: uuid.UUID, tenant_id: uuid.UUID, offset: int, limit: int,
    ) -> dict:
        threads, total = await self._repo.get_threads_for_user(user_id, tenant_id, offset, limit)
        items = [
            InboxThreadResponse(
                thread_id=t["thread_id"],
                asunto=t["asunto"],
                sender_nombre=t["sender_nombre"],
                last_message_preview=t["last_message_preview"],
                message_count=t["message_count"],
                unread_count=t["unread_count"],
                last_activity=t["last_activity"],
            )
            for t in threads
        ]
        return {"items": items, "total": total, "offset": offset, "limit": limit}

    async def ver_hilo(
        self, thread_id: uuid.UUID, user_id: uuid.UUID, tenant_id: uuid.UUID,
    ) -> ThreadDetailResponse:
        root, replies = await self._repo.get_thread_detail(thread_id, tenant_id)
        if root is None:
            raise HTTPException(status_code=404, detail="Hilo no encontrado")

        participants = {root.sender_id, root.recipient_id}
        for r in replies:
            participants.add(r.sender_id)
            participants.add(r.recipient_id)

        if user_id not in participants:
            raise HTTPException(status_code=404, detail="Hilo no encontrado")

        await self._repo.mark_thread_as_read(thread_id, user_id, tenant_id)
        await self._session.commit()
        await self._session.refresh(root, ["sender", "recipient"])

        thread_resp = _make_mensaje_response(root)
        reply_resps = [_make_mensaje_response(r) for r in replies]

        return ThreadDetailResponse(thread=thread_resp, replies=reply_resps)

    async def responder(
        self,
        thread_id: uuid.UUID,
        sender_id: uuid.UUID,
        tenant_id: uuid.UUID,
        request: MensajeReplyRequest,
    ) -> MensajeResponse:
        root, _ = await self._repo.get_thread_detail(thread_id, tenant_id)
        if root is None:
            raise HTTPException(status_code=404, detail="Hilo no encontrado")

        if sender_id not in (root.sender_id, root.recipient_id):
            raise HTTPException(status_code=404, detail="Hilo no encontrado")

        recipient_id = root.sender_id if sender_id == root.recipient_id else root.recipient_id

        reply = Mensaje(
            tenant_id=tenant_id,
            sender_id=sender_id,
            recipient_id=recipient_id,
            parent_id=thread_id,
            asunto=root.asunto,
            cuerpo=request.cuerpo,
        )
        await self._repo.create(reply)
        await self._session.commit()
        await self._session.refresh(reply, ["sender", "recipient"])

        if self._audit:
            await self._audit.log(
                accion=AuditAction.MENSAJE_ENVIAR,
                actor_id=sender_id,
                tenant_id=tenant_id,
                detalle={"mensaje_id": str(reply.id), "hilo_id": str(thread_id)},
            )

        return _make_mensaje_response(reply)
