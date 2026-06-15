"""activia-trace worker entrypoint — placeholder no-op loop.

La tecnología real de la cola (ADR-003) se definirá en el change de comunicaciones.
"""
import asyncio
import logging

from app.core.logging import setup_logging

logger = logging.getLogger(__name__)


async def main():
    setup_logging()
    logger.info("Worker started (placeholder — no-op loop)")

    try:
        while True:
            await asyncio.sleep(60)
            logger.debug("Worker heartbeat")
    except KeyboardInterrupt:
        logger.info("Worker stopped")


if __name__ == "__main__":
    asyncio.run(main())
