import logging

from fastapi import APIRouter
from sqlalchemy import text

import app.core.database as db

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/health")
async def health_check():
    db_status = "down"
    sf = db.session_factory
    if sf is not None:
        try:
            async with sf() as session:
                await session.execute(text("SELECT 1"))
                db_status = "up"
        except Exception as exc:
            logger.warning("Health check DB down: %s", exc)

    return {"status": "ok", "database": db_status}
