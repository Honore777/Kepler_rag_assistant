"""Alembic environment for async SQLAlchemy migrations."""

from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.core.config import log_db_target, settings
from app.db.base import Base
from app.db import models  # noqa: F401  # ensure model metadata is imported
from app.db.session import _normalize_database_url

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Point Alembic to SQLAlchemy metadata for autogeneration.
target_metadata = Base.metadata


def _db_url() -> str:
    url = _normalize_database_url(settings.DATABASE_URL)
    if not url:
        raise RuntimeError("DATABASE_URL is required for Alembic migrations")
    log_db_target()
    return url


def run_migrations_offline() -> None:
    """Run migrations without a live DB connection."""
    context.configure(
        url=_db_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations with async engine and transactional DDL."""
    cfg_section = config.get_section(config.config_ini_section) or {}
    cfg_section["sqlalchemy.url"] = _db_url()

    connectable = async_engine_from_config(
        cfg_section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    import asyncio

    asyncio.run(run_migrations_online())
