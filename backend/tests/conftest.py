import os

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:1234@localhost:5432/activia_trace_test",
)
os.environ.setdefault("SECRET_KEY", "a" * 32)
os.environ.setdefault("ENCRYPTION_KEY", "b" * 32)

import uuid

import pytest
import pytest_asyncio
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.pool import NullPool

import app.core.database as db
from app.core.config import Settings
from app.models.base import BaseModelMixin
from app.models.tenant import Tenant
from app.models.asignacion import Asignacion  # noqa: F401 — register model for table creation
from app.models.usuario import Usuario  # noqa: F401 — register model for table creation
from app.models.calificacion import Calificacion, UmbralMateria  # noqa: F401 — register model for table creation
from app.models.comunicacion import Comunicacion  # noqa: F401 — register model for table creation
from app.models.slot_encuentro import SlotEncuentro  # noqa: F401
from app.models.instancia_encuentro import InstanciaEncuentro  # noqa: F401
from app.models.guardia import Guardia  # noqa: F401
from app.models.evaluacion import Evaluacion  # noqa: F401
from app.models.reserva_evaluacion import ReservaEvaluacion  # noqa: F401
from app.models.resultado_evaluacion import ResultadoEvaluacion  # noqa: F401
from app.models.tarea import Tarea  # noqa: F401
from app.models.comentario_tarea import ComentarioTarea  # noqa: F401
from app.models.aviso import Aviso  # noqa: F401
from app.models.acknowledgment_aviso import AcknowledgmentAviso  # noqa: F401
from app.models.mensaje import Mensaje  # noqa: F401
from app.models.materia_carrera import MateriaCarrera  # noqa: F401
from app.models.programa_materia import ProgramaMateria  # noqa: F401
from app.models.fecha_academica import FechaAcademica  # noqa: F401
from app.models.liquidacion import (  # noqa: F401
    Factura,
    GrupoMateria,
    Liquidacion,
    SalarioBase,
    SalarioPlus,
)


class SampleEntity(BaseModelMixin, db.Base):
    __tablename__ = "sample_entity"

    name: Mapped[str] = mapped_column(sa.String(255), nullable=False)


class SampleEntityNoTenant(db.Base):
    __tablename__ = "sample_entity_no_tenant"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(sa.String(255), nullable=False)


@pytest.fixture(scope="session")
def settings() -> Settings:
    return Settings(
        _env_file=None,
        DATABASE_URL=os.getenv(
            "DATABASE_URL",
            "postgresql+asyncpg://postgres:1234@localhost:5432/activia_trace_test",
        ),
        SECRET_KEY="a" * 32,
        ENCRYPTION_KEY="b" * 32,
    )


def _create_sqlite_engine():
    engine = create_async_engine(
        "sqlite+aiosqlite:///./test_trace.db",
        poolclass=NullPool,
        echo=False,
    )

    @sa.event.listens_for(engine.sync_engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()

    return engine


def _cleanup_sqlite_db():
    import pathlib

    for f in ("test_trace.db", "test_trace.db-wal", "test_trace.db-shm"):
        p = pathlib.Path(f)
        if p.exists():
            p.unlink()


@pytest_asyncio.fixture(scope="session")
async def db_engine():
    engine = None
    database_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:1234@localhost:5432/activia_trace_test")
    try:
        engine = create_async_engine(
            database_url,
            pool_pre_ping=True,
            echo=False,
        )
        async with engine.begin() as conn:
            await conn.execute(sa.text("SELECT 1"))
    except Exception:
        if engine is not None:
            await engine.dispose()
        engine = _create_sqlite_engine()

    db.engine = engine
    db.session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    yield True
    await db.close_db()
    _cleanup_sqlite_db()


@pytest_asyncio.fixture(scope="session")
async def db_tables(db_engine):
    async with db.engine.begin() as conn:
        await conn.run_sync(db.Base.metadata.create_all)
    yield
    async with db.engine.begin() as conn:
        await conn.run_sync(db.Base.metadata.drop_all)


async def _get_or_create_tenant(name: str, slug: str) -> Tenant:
    """Idempotent tenant creation — returns existing tenant if present."""
    async with db.session_factory() as session:
        result = await session.execute(
            sa.select(Tenant).where(Tenant.name == name)
        )
        t = result.scalar_one_or_none()
        if t is None:
            t = Tenant(name=name, slug=slug)
            session.add(t)
            await session.commit()
            await session.refresh(t)
        else:
            await session.refresh(t)
        return t


@pytest_asyncio.fixture(scope="session")
async def tenant(db_tables) -> Tenant:
    return await _get_or_create_tenant("Test Tenant", "test-tenant")


@pytest_asyncio.fixture(scope="session")
async def tenant_a(db_tables) -> Tenant:
    return await _get_or_create_tenant("Tenant A", "tenant-a")


@pytest_asyncio.fixture(scope="session")
async def tenant_b(db_tables) -> Tenant:
    return await _get_or_create_tenant("Tenant B", "tenant-b")


@pytest_asyncio.fixture
async def db_session(db_tables) -> AsyncSession:
    """Provides a clean session with data isolation between tests.

    Discovers ALL tables registered in the SQLAlchemy metadata and
    deletes every row from every table *except* ``tenant`` (which is
    session-scoped) after each test.  Table discovery is dynamic so new
    models added to the codebase are cleaned automatically.
    """
    # ── discover table names from metadata (single source of truth) ──
    _EXCLUDED_TABLES = {"tenant"}
    _all_tables = tuple(
        name for name in db.Base.metadata.tables
        if name not in _EXCLUDED_TABLES
    )

    session = db.session_factory()
    yield session
    await session.close()

    async with db.engine.begin() as conn:
        # TRUNCATE is dramatically faster than DELETE for full-table cleanup.
        # On SQLite TRUNCATE is not supported → fall back to ordered DELETE.
        try:
            await conn.execute(
                sa.text("TRUNCATE TABLE " + ", ".join(_all_tables) + " CASCADE")
            )
        except Exception:
            # Fallback: DELETE row-by-row (slower but works on SQLite).
            # Multiple passes to handle FK ordering: child tables must be
            # emptied before their parent tables. 5 passes covers deep FK chains.
            remaining = list(_all_tables)
            for _pass in range(5):
                if not remaining:
                    break
                still_failing = []
                for table in remaining:
                    try:
                        await conn.execute(sa.text(f"DELETE FROM {table}"))
                    except Exception:
                        still_failing.append(table)
                remaining = still_failing
            # Last resort: disable FK checks, delete everything, re-enable
            if remaining:
                await conn.execute(sa.text("PRAGMA foreign_keys=OFF"))
                for table in remaining:
                    try:
                        await conn.execute(sa.text(f"DELETE FROM {table}"))
                    except Exception:
                        pass
                await conn.execute(sa.text("PRAGMA foreign_keys=ON"))


