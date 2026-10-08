"""Alembic environment for the AssetOps product database.

`DATABASE_URL` is required. There is no fallback URL here: only the
development Compose file documents a local default, and it is supplied by the
operator's environment, never by this module.
"""

from __future__ import annotations

import os

from alembic import context
from sqlalchemy import create_engine, pool


def _database_url() -> str:
    configured = context.config.attributes.get("database_url") or os.environ.get(
        "DATABASE_URL"
    )
    if not configured:
        raise RuntimeError(
            "DATABASE_URL is required to run migrations. See backend/README-db.md "
            "for the local development value."
        )
    return configured


def run_migrations_online() -> None:
    engine = create_engine(_database_url(), poolclass=pool.NullPool)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=None)
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()


if context.is_offline_mode():
    raise RuntimeError("Offline (SQL script) migrations are not supported.")
run_migrations_online()
