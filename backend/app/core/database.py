from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import Settings


def create_engine(settings: Settings):
    return create_async_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        echo=False,
    )


def create_session_factory(engine):
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


engine = None
session_factory = None


def init_db(settings: Settings):
    global engine, session_factory
    engine = create_engine(settings)
    session_factory = create_session_factory(engine)


async def close_db():
    global engine
    if engine is not None:
        await engine.dispose()


async def get_session() -> AsyncSession:
    if session_factory is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    async with session_factory() as session:
        yield session


class Base(DeclarativeBase):
    pass
