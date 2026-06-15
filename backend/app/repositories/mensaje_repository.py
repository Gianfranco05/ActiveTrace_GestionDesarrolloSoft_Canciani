import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.mensaje import Mensaje


class MensajeRepository:
    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID):
        self._session = session
        self._tenant_id = tenant_id

    async def create(self, mensaje: Mensaje) -> Mensaje:
        self._session.add(mensaje)
        await self._session.flush()
        return mensaje

    async def get_threads_for_user(
        self, user_id: uuid.UUID, tenant_id: uuid.UUID, offset: int, limit: int,
    ) -> tuple[list[dict], int]:
        base = (
            select(Mensaje)
            .options(
                selectinload(Mensaje.sender),
            )
            .where(
                Mensaje.tenant_id == tenant_id,
                Mensaje.parent_id.is_(None),
                Mensaje.recipient_id == user_id,
                Mensaje.deleted_at.is_(None),
            )
        )

        count_q = select(func.count()).select_from(base.subquery())
        total = (await self._session.execute(count_q)).scalar_one()

        items_q = base.order_by(Mensaje.created_at.desc()).offset(offset).limit(limit)
        result = await self._session.execute(items_q)
        roots = list(result.scalars().all())

        threads = []
        for root in roots:
            replies = await self._get_replies_for_root(root.id, tenant_id)
            all_msgs = [root] + replies
            datetimes = [m.created_at.replace(tzinfo=None) if m.created_at.tzinfo else m.created_at for m in all_msgs]
            last_activity = max(datetimes)
            msg_count = len(all_msgs)
            unread = sum(1 for m in all_msgs if m.recipient_id == user_id and not m.leido)
            last_msg_body = ""
            if replies:
                last_reply = max(replies, key=lambda r: r.created_at)
                last_msg_body = last_reply.cuerpo[:100] if last_reply.cuerpo else ""
            else:
                last_msg_body = root.cuerpo[:100] if root.cuerpo else ""

            threads.append({
                "thread_id": root.id,
                "asunto": root.asunto,
                "sender_nombre": f"{root.sender.nombre} {root.sender.apellidos}" if root.sender else "",
                "last_message_preview": last_msg_body,
                "message_count": msg_count,
                "unread_count": unread,
                "last_activity": last_activity,
            })

        threads.sort(key=lambda t: t["last_activity"].replace(tzinfo=None) if t["last_activity"].tzinfo else t["last_activity"], reverse=True)
        return threads, total

    async def _get_replies_for_root(self, root_id: uuid.UUID, tenant_id: uuid.UUID) -> list[Mensaje]:
        query = (
            select(Mensaje)
            .options(selectinload(Mensaje.sender))
            .where(
                Mensaje.tenant_id == tenant_id,
                Mensaje.parent_id == root_id,
                Mensaje.deleted_at.is_(None),
            )
            .order_by(Mensaje.created_at.asc())
        )
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def get_thread_detail(
        self, thread_id: uuid.UUID, tenant_id: uuid.UUID,
    ) -> tuple[Mensaje | None, list[Mensaje]]:
        query = (
            select(Mensaje)
            .options(
                selectinload(Mensaje.sender),
                selectinload(Mensaje.recipient),
            )
            .where(
                Mensaje.id == thread_id,
                Mensaje.tenant_id == tenant_id,
                Mensaje.parent_id.is_(None),
                Mensaje.deleted_at.is_(None),
            )
        )
        result = await self._session.execute(query)
        root = result.scalar_one_or_none()
        if root is None:
            return None, []

        query = (
            select(Mensaje)
            .options(
                selectinload(Mensaje.sender),
                selectinload(Mensaje.recipient),
            )
            .where(
                Mensaje.tenant_id == tenant_id,
                Mensaje.parent_id == thread_id,
                Mensaje.deleted_at.is_(None),
            )
            .order_by(Mensaje.created_at.asc())
        )
        result = await self._session.execute(query)
        replies = list(result.scalars().all())
        return root, replies

    async def mark_as_read(self, message_id: uuid.UUID, tenant_id: uuid.UUID) -> None:
        from sqlalchemy import update

        stmt = (
            update(Mensaje)
            .where(
                Mensaje.id == message_id,
                Mensaje.tenant_id == tenant_id,
            )
            .values(leido=True, leido_at=datetime.now(UTC))
        )
        await self._session.execute(stmt)
        await self._session.flush()

    async def mark_thread_as_read(
        self, thread_id: uuid.UUID, user_id: uuid.UUID, tenant_id: uuid.UUID,
    ) -> None:
        from sqlalchemy import update

        stmt = (
            update(Mensaje)
            .where(
                Mensaje.tenant_id == tenant_id,
                Mensaje.recipient_id == user_id,
                Mensaje.leido == False,  # noqa: E712
                (Mensaje.id == thread_id) | (Mensaje.parent_id == thread_id),
            )
            .values(leido=True, leido_at=datetime.now(UTC))
        )
        await self._session.execute(stmt)
        await self._session.flush()
