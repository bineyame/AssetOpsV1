"""3C2 (`specs/3C2-agreed-change-action/spec.md` §2.4; D-3C2.5): composes the agreed-change service; the only importer
of its Postgres adapter. DDR G10 reads `build_agreed_actions(url).service.for_tenant(tenant)`.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable

from assetops_backend.accounts.composition import build_account_service
from assetops_backend.actions.adapters.postgres_agreed_action_store import PostgresAgreedActionStore
from assetops_backend.actions.agreed import AgreedActionService

__all__ = ["AgreedActionsService", "build_agreed_actions"]


@dataclass(frozen=True)
class AgreedActionsService:
    service: AgreedActionService
    dispose: Callable[[], None]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def build_agreed_actions(database_url: str, *, clock: Callable[[], datetime] = _now) -> AgreedActionsService:
    store = PostgresAgreedActionStore(database_url)
    return AgreedActionsService(AgreedActionService(store, build_account_service(database_url), clock=clock),
                                store.dispose)
