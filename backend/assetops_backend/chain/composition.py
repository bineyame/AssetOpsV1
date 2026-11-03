"""CH-2: the composition root of the thread chain; the only importer of its adapters."""
from __future__ import annotations

from assetops_backend.chain.adapters.postgres_thread_sources import PostgresThreadSources
from assetops_backend.chain.adapters.postgres_thread_store import PostgresThreadStore, ThreadStoreUnavailable

__all__ = ["PostgresThreadSources", "PostgresThreadStore", "ThreadStoreUnavailable", "build_thread_sources",
           "build_thread_store"]


def build_thread_store(database_url: str | None) -> PostgresThreadStore | None:
    return PostgresThreadStore(database_url) if database_url else None


def build_thread_sources(database_url: str | None) -> PostgresThreadSources | None:
    """The read-only source reader, or None when no database is configured (the board then reads no threads)."""
    return PostgresThreadSources(database_url) if database_url else None
