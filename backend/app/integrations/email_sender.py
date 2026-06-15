import logging
import random
from typing import Protocol

logger = logging.getLogger(__name__)


class EmailSender(Protocol):
    async def send(self, destinatario: str, asunto: str, cuerpo: str) -> bool: ...


class MockEmailSender:
    def __init__(self, failure_rate: float = 0.0):
        self._failure_rate = failure_rate
        self._sent: list[tuple[str, str, str]] = []

    async def send(self, destinatario: str, asunto: str, cuerpo: str) -> bool:
        self._sent.append((destinatario, asunto, cuerpo))
        if random.random() < self._failure_rate:
            logger.warning("Mock send FAILED for %s", destinatario)
            return False
        logger.info("Mock send OK for %s", destinatario)
        return True
