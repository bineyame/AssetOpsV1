"""Composition for the Actions domain: the only module that imports its adapters (S6-01a).

Callers receive the `ActionService` (over the `ActionStore` port); `ACTION_UNAVAILABLE` is the store's
unavailable error type.
"""

from __future__ import annotations

import os
from typing import Any, Callable
from uuid import UUID

from assetops_backend.actions.adapters.demo_grants_file import load_grants
from assetops_backend.actions.adapters.postgres_action_store import PostgresActionStore
from assetops_backend.actions.capability import CapabilityCheck, from_grants
from assetops_backend.actions.ports import ActionStore, ActionStoreUnavailable
from assetops_backend.actions.service import ActionService, FindingCurrentness

__all__ = ["ACTION_UNAVAILABLE", "GRANTS_ENV", "build_action_service", "build_action_store",
           "capability_from_environment", "finding_currentness"]

ACTION_UNAVAILABLE = ActionStoreUnavailable
GRANTS_ENV = "ASSETOPS_ACTION_DEMO_GRANTS"


def build_action_store(database_url: str | None) -> ActionStore:
    return PostgresActionStore(database_url)


def capability_from_environment() -> CapabilityCheck:
    return from_grants(load_grants(os.environ.get(GRANTS_ENV)))


def finding_currentness(reads: Any) -> FindingCurrentness:
    """Currentness of a FindingRevision from the S4 Finding read (`FindingReadService.finding`)."""
    def current(tenant_id: UUID, site_id: UUID, finding_id: UUID, revision_id: UUID | None,
                source_open: bool) -> dict[str, Any] | None:
        body = reads.finding(tenant_id, site_id, finding_id, revision_id, limit=1, source_open=source_open)
        if body is None:
            return None
        selection = body["selection"]
        return {"revision_id": selection["revision_id"], "latest_revision_id": selection["latest_revision_id"],
                "is_latest": selection["is_latest"],
                "claim_is_current": bool(body["state"]["claim_is_current"]) and selection["is_latest"]}
    return current


def build_action_service(database_url: str | None, finding_reads: Any,
                         capability: CapabilityCheck | None = None,
                         clock: Callable | None = None) -> ActionService:
    kwargs: dict[str, Any] = {}
    if clock is not None:
        kwargs["clock"] = clock
    return ActionService(build_action_store(database_url), finding_currentness(finding_reads),
                         capability_from_environment() if capability is None else capability, **kwargs)
