"""Ports of the S6-01a Action store (implemented by `actions/adapters/postgres_action_store.py`)."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol
from uuid import UUID

from assetops_backend.actions.reserve_trial import RuleInputs


class ActionStoreUnavailable(Exception):
    pass


class ActionRefused(Exception):
    """A typed refusal a client switches on."""

    def __init__(self, status: int, code: str, message: str, **extra: Any) -> None:
        super().__init__(message)
        self.status, self.code, self.message, self.extra = status, code, message, extra


class ActionStore(Protocol):
    def rule_inputs(self, tenant_id: UUID, site_id: UUID, finding_id: UUID, finding_revision_id: UUID,
                    *, is_latest: bool, claim_is_current: bool, at: datetime) -> RuleInputs | None: ...

    def latest_revision(self, tenant_id: UUID, site_id: UUID, finding_id: UUID) -> dict[str, Any] | None: ...

    def action_for_recommendation(self, tenant_id: UUID, site_id: UUID,
                                  recommendation_key: str) -> dict[str, Any] | None: ...

    def actions_for_revision(self, tenant_id: UUID, site_id: UUID,
                             finding_revision_id: UUID) -> list[dict[str, Any]]: ...

    def accept(self, tenant_id: UUID, site_id: UUID, proposal: dict[str, Any], *, payload_sha256: str,
               payload: dict[str, Any], idempotency_key: str, fixture_id: str,
               recorded_at: datetime) -> tuple[dict[str, Any], dict[str, Any], bool]: ...

    def observe(self, tenant_id: UUID, site_id: UUID, action_id: UUID, *, occurred_at: datetime,
                idempotency_key: str, payload: dict[str, Any], payload_sha256: str, fixture_id: str,
                recorded_at: datetime) -> tuple[dict[str, Any], bool]: ...

    def action(self, tenant_id: UUID, site_id: UUID, action_id: UUID) -> dict[str, Any] | None: ...

    def events(self, tenant_id: UUID, site_id: UUID, action_id: UUID) -> list[dict[str, Any]]: ...
