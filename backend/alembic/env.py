import asyncio
import os
import sys
import re
from logging.config import fileConfig

# Windows + asyncpg + Docker: ProactorEventLoop no funciona, forzar SelectorEventLoop
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from alembic import context
import sqlalchemy as sa
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.core.database import Base
from app.models import (  # noqa: F401 — register models for autogenerate
    AcknowledgmentAviso,
    Asignacion,
    AuditLog,
    AuthUser,
    Aviso,
    Calificacion,
    Carrera,
    Cohorte,
    Comunicacion,
    EntradaPadron,
    Materia,
    Permiso,
    RefreshToken,
    ResetToken,
    Rol,
    RolPermiso,
    Tenant,
    UmbralMateria,
    Usuario,
    VersionPadron,
)

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = _get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


def _get_database_url() -> str:
    """Lee DATABASE_URL del entorno o del archivo .env de la app."""
    # Intentar cargar desde el módulo de configuración (que lee .env automáticamente)
    try:
        from app.core.config import Settings
        settings = Settings()  # type: ignore[call-arg]
        env_url = settings.DATABASE_URL
    except Exception:
        env_url = os.environ.get("DATABASE_URL")

    if not env_url:
        raise RuntimeError(
            "DATABASE_URL no está definida en el entorno ni en .env. "
            "Definila antes de correr migraciones:\n"
            "  $env:DATABASE_URL = 'postgresql+asyncpg://...'  (PowerShell)\n"
            "  export DATABASE_URL='postgresql+asyncpg://...'   (Unix)"
        )
    return re.sub(r"^postgresql://", "postgresql+asyncpg://", env_url)


async def run_async_migrations() -> None:
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = _get_database_url()
    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        # Pre-crear alembic_version con VARCHAR(255) para que los IDs largos
        # de revisión (ej. 015_programa_materia_fecha_academica = 38 chars)
        # no revienten contra el VARCHAR(32) default de alembic.
        await connection.execute(
            sa.text(
                "CREATE TABLE IF NOT EXISTS alembic_version "
                "(version_num VARCHAR(255) NOT NULL PRIMARY KEY)"
            )
        )
        await connection.commit()
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
