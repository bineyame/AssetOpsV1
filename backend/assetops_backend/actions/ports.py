"""Ports of the S6-01a Action store (implemented by `actions/adapters/postgres_action_store.py`)."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Protocol
from uuid import UUID

from assetops_backend.actions.reserve_trial import RuleInputs


class ActionStoreUnavailable(Exception):
    pass


class ActionRefused(Exception):
    """A typed refusal a client switches on."""

    def __init__(self, status: int, code: str, message: str, **extra: Any) -> None:
        super().__init__(message)
        self.status, self.code, self.message, self.extra = status, code, message, extra


class ApplyFailed(Exception):
    """An authorized same-Site application that reached domain validation or the S1 publish and failed.

    Raised inside the apply transaction so everything rolls back; FAILED is then appended separately."""

    def __init__(self, status: int, code: str, message: str, *, current_foundation_revision_id: UUID | None = None,
                 **extra: Any) -> None:
        super().__init__(message)
        self.status, self.code, self.message = status, code, message
        self.current_foundation_revision_id, self.extra = current_foundation_revision_id, extra


class ActionStore(Protocol):
    def rule_inputs(self, tenant_id: UUID, site_id: UUID, finding_id: UUID, finding_revision_id: UUID,
                    *, is_latest: bool, claim_is_current: bool, at: datetime) -> RuleInputs | None: ...

    def latest_revision(self, tenant_id: UUID, site_id: UUID, finding_id: UUID) -> dict[str, Any] | None: ...

    def action_for_recommendation(self, tenant_id: UUID, site_id: UUID,
                                  recommendation_key: str) -> dict[str, Any] | None: ...

    def actions_for_revision(self, tenant_id: UUID, site_id: UUID,
                             finding_revision_id: UUID) -> list[dict[str, Any]]: ...

    def actions_for_finding(self, tenant_id: UUID, site_id: UUID,
                            finding_id: UUID) -> list[dict[str, Any]]: ...

    def accept(self, tenant_id: UUID, site_id: UUID, proposal: dict[str, Any], *, payload_sha256: str,
               payload: dict[str, Any], idempotency_key: str, fixture_id: str, recorded_at: datetime,
               guard: Callable[[list[dict[str, Any]]], None]) -> tuple[dict[str, Any], dict[str, Any], bool]: ...

    def observe(self, tenant_id: UUID, site_id: UUID, action_id: UUID, *, occurred_at: datetime,
                idempotency_key: str, payload: dict[str, Any], payload_sha256: str, fixture_id: str,
                recorded_at: datetime) -> tuple[dict[str, Any], bool]: ...

    def action(self, tenant_id: UUID, site_id: UUID, action_id: UUID) -> dict[str, Any] | None: ...

    def events(self, tenant_id: UUID, site_id: UUID, action_id: UUID) -> list[dict[str, Any]]: ...

    def apply(self, tenant_id: UUID, site_id: UUID, action_id: UUID, *, idempotency_key: str,
              payload: dict[str, Any], payload_sha256: str, fixture_id: str, recorded_at: datetime,
              expected_foundation_revision_id: UUID, attempt: Callable[..., None]) -> dict[str, Any]: ...

    def change(self, tenant_id: UUID, site_id: UUID, change_id: UUID) -> dict[str, Any] | None: ...

    def change_for_action(self, tenant_id: UUID, site_id: UUID, action_id: UUID) -> dict[str, Any] | None: ...

    def foundation_revisions(self, tenant_id: UUID, site_id: UUID, ids: list[UUID]) -> list[dict[str, Any]]: ...

    def current_foundation(self, tenant_id: UUID, site_id: UUID, at: datetime) -> dict[str, Any] | None: ...


# The S1 caller-owned publish, passed in from composition (the Action adapter never imports the S1 service):
# (site_code, connection, then, *, asset_code, value, effective_from, note, expected_revision_id, expected_value,
#  recorded_at) -> None. Raises `ApplyFailed` for an S1 refusal.
FoundationPublish = Callable[..., None]
