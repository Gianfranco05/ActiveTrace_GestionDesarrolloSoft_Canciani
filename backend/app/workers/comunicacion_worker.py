import asyncio
import logging
import os
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.integrations.email_sender import MockEmailSender
from app.models.comunicacion import Comunicacion, EstadoComunicacion

logger = logging.getLogger(__name__)

BATCH_SIZE = int(os.getenv("BATCH_SIZE", "50"))
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "10"))
STUCK_TIMEOUT_MINUTES = int(os.getenv("STUCK_TIMEOUT_MINUTES", "30"))


class ComunicacionWorker:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        email_sender=None,
    ):
        self._session_factory = session_factory
        self._sender = email_sender or MockEmailSender()
        self._running = False

    async def startup_recovery(self, session: AsyncSession) -> int:
        cutoff = datetime.now(UTC) - timedelta(minutes=STUCK_TIMEOUT_MINUTES)
        result = await session.execute(
            select(Comunicacion).where(
                Comunicacion.estado == EstadoComunicacion.ENVIANDO.value,
                Comunicacion.updated_at < cutoff,
                Comunicacion.deleted_at.is_(None),
            ),
        )
        stuck = result.scalars().all()
        for c in stuck:
            c.estado = EstadoComunicacion.PENDIENTE.value
            c.error_detalle = "Recovered from stuck Enviando state"
        await session.commit()
        if stuck:
            logger.info("Recovered %d stuck Enviando messages", len(stuck))
        return len(stuck)

    async def poll_once(self, session: AsyncSession) -> int:
        query = (
            select(Comunicacion)
            .where(
                Comunicacion.estado == EstadoComunicacion.PENDIENTE.value,
                Comunicacion.deleted_at.is_(None),
            )
            .where(
                (Comunicacion.requiere_aprobacion.is_(False))
                | (Comunicacion.aprobado_por.isnot(None)),
            )
            .order_by(Comunicacion.created_at.asc())
            .limit(BATCH_SIZE)
        )
        dialect = session.bind.dialect.name if session.bind else ""
        if dialect == "postgresql":
            query = query.with_for_update(skip_locked=True)
        result = await session.execute(query)
        records = result.scalars().all()

        for record in records:
            await self._process_record(session, record)

        return len(records)

    async def _process_record(
        self, session: AsyncSession, record: Comunicacion,
    ) -> None:
        record.estado = EstadoComunicacion.ENVIANDO.value
        await session.commit()

        success = await self._sender.send(
            destinatario=record.destinatario,
            asunto=record.asunto,
            cuerpo=record.cuerpo,
        )

        if success:
            record.estado = EstadoComunicacion.ENVIADO.value
            record.enviado_at = datetime.now(UTC)
        else:
            record.estado = EstadoComunicacion.ERROR.value
            record.error_detalle = "Email send failed"

        await session.commit()

    async def run(self) -> None:
        self._running = True
        logger.info(
            "Worker starting (batch=%d, interval=%d)",
            BATCH_SIZE, POLL_INTERVAL,
        )

        async with self._session_factory() as session:
            recovered = await self.startup_recovery(session)
            if recovered:
                logger.info("Startup recovery complete: %d messages", recovered)

        while self._running:
            try:
                async with self._session_factory() as session:
                    processed = await self.poll_once(session)
                    if processed:
                        logger.info("Processed %d messages", processed)
            except Exception:
                logger.exception("Worker poll cycle failed")

            for _ in range(POLL_INTERVAL):
                if not self._running:
                    break
                await asyncio.sleep(1)

        logger.info("Worker stopped")

    def stop(self) -> None:
        self._running = False
