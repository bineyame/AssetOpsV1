"""Composition for the work domain: the only module that imports its adapter (W4-01 commit 2).

Callers receive the `WorkService` over `PostgresWorkStore`, whose provenance reads use the evidence ledger's
caller-connection link-row reader (the shared W3 `PublicProvenance` contract; no second DTO).
"""

from __future__ import annotations

from typing import Callable
from uuid import UUID, uuid4

from assetops_backend.evidence.composition import build_link_rows_reader
from assetops_backend.work.adapters.postgres_work_store import PostgresWorkStore
from assetops_backend.work.model import WorkStoreUnavailable
from assetops_backend.work.service import WorkService

__all__ = ["WORK_UNAVAILABLE", "build_work_service", "build_work_store"]

WORK_UNAVAILABLE = WorkStoreUnavailable


def build_work_store(database_url: str | None) -> PostgresWorkStore:
    return PostgresWorkStore(database_url, link_rows=build_link_rows_reader())


def build_work_service(database_url: str | None, *, new_id: Callable[[], UUID] = uuid4) -> WorkService:
    return WorkService(build_work_store(database_url), new_id=new_id)
