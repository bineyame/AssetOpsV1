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
from assetops_backend.actions.ports import ActionStore, ActionStoreUnavailable, ApplyFailed, FoundationPublish
from assetops_backend.actions.service import ActionService, FindingCurrentness
from assetops_backend.actions.verification import VerificationPorts
from assetops_backend.sites.foundation_service import CallerTransaction, FoundationRefused

__all__ = ["ACTION_UNAVAILABLE", "GRANTS_ENV", "build_action_service", "build_action_store",
           "capability_from_environment", "finding_currentness", "foundation_publish", "verification_ports"]

# S1 refusal under the Site lock -> the Action failure code a FAILED event records.
S1_FAILURES = {
    "FOUNDATION_EXPECTED_REVISION_STALE": (409, "ACTION_FOUNDATION_STALE"),
    "FOUNDATION_EXPECTED_VALUE_STALE": (409, "ACTION_FOUNDATION_STALE"),
    # The apply's server time is taken before the Site lock; a publish that committed in that window is a
    # change to the Foundation since the basis was read, so it is the stale basis (S6-01a review L1).
    "FOUNDATION_CLOCK_BEHIND": (409, "ACTION_FOUNDATION_STALE"),
    "FOUNDATION_NO_CHANGE": (422, "ACTION_NO_CHANGE"),
    "FOUNDATION_VALUE_INVALID": (422, "ACTION_VALUE_INVALID"),
    "FOUNDATION_INTERVAL_INVALID": (422, "ACTION_EFFECTIVE_TIME_INVALID"),
}

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
                "is_latest": selection["is_latest"], "episode": body["revision"]["episode"],
                "claim_is_current": bool(body["state"]["claim_is_current"]) and selection["is_latest"]}
    return current


def foundation_publish(registry: Any) -> FoundationPublish:
    """The S1 caller-owned-connection battery-reserve publish, handed to the Action service (M1).

    `registry` is the imported-Site registry (`sites.cutover.ImportedSiteRegistry`). The Action adapter never
    imports the S1 service; it receives this callable and its own connection is passed straight through.
    """
    def publish(site_code: str, connection: Any, then: Callable[[dict[str, Any]], None], *, asset_code: str,
                value: float, effective_from: Any, recorded_at: Any, expected_revision_id: UUID,
                expected_value: float, note: str) -> None:
        service, tenant, site = registry.service, registry.tenant(), registry.imported(site_code)
        if service is None or tenant is None or site is None:
            raise ActionStoreUnavailable("No Foundation publish is composed for this Site.")
        try:
            service.publish_battery_reserve(
                tenant, site, asset_code=asset_code, value=value, effective_from=effective_from, note=note,
                expected_revision_id=expected_revision_id, expected_value=expected_value,
                caller=CallerTransaction(connection=connection, then=then, recorded_at=recorded_at))
        except FoundationRefused as refused:
            status, code = S1_FAILURES.get(refused.code, (refused.status, "ACTION_PUBLISH_REFUSED"))
            raise ApplyFailed(status, code, refused.message, current_foundation_revision_id=refused.current_revision_id,
                              foundation_code=refused.code) from refused
    return publish


def verification_ports(database_url: str | None) -> VerificationPorts:
    """S6-02a: the S3/S4 day currentness and S4-05 per-window source resolution the verification service reads.

    `day_status(tenant, site, day)` is S3's own `derive_status` for the UTC day's selection (via the dispatch read)
    beside S4's `match_state` for that day window; `provenance(tenant, site, ids)` is the S4-05a resolver."""
    from datetime import datetime, timezone

    from assetops_backend.analytics.composition import build_dispatch_read_service, build_finding_store
    from assetops_backend.evidence.composition import build_source_provenance

    reads, findings = build_dispatch_read_service(database_url), build_finding_store(database_url)
    resolver = build_source_provenance(database_url)

    def day_status(tenant_id: UUID, site_id: UUID, day: Any) -> dict[str, Any]:
        window = reads.window(tenant_id, site_id, day)
        match = findings.match_state(tenant_id, site_id, "dispatch",
                                     datetime(day.year, day.month, day.day, tzinfo=timezone.utc))
        selection = window["selection"] or {}
        return {"day": day.isoformat(), "s3_status": window["status"], "s3_reasons": list(window["status_reasons"]),
                "run_id": None if not selection else str(selection["run_id"]),
                "input_sha256": selection.get("input_sha256"),
                "configuration_sha256": selection.get("configuration_sha256"),
                "s4_matched": bool(match["matched"]), "s4_match_deferred": bool(match["match_deferred"]),
                "s4_match_pass_id": match["match_pass_id"]}

    def provenance(tenant_id: UUID, site_id: UUID, evidence_ids: list[str]) -> dict[str, Any]:
        return resolver.resolve(tenant_id, site_id, evidence_ids)

    return VerificationPorts(day_status=day_status, provenance=provenance)


def build_action_service(database_url: str | None, finding_reads: Any,
                         capability: CapabilityCheck | None = None,
                         clock: Callable | None = None, registry: Any = None) -> ActionService:
    kwargs: dict[str, Any] = {}
    if clock is not None:
        kwargs["clock"] = clock
    service = ActionService(build_action_store(database_url), finding_currentness(finding_reads),
                            capability_from_environment() if capability is None else capability,
                            publish=None if registry is None else foundation_publish(registry), **kwargs)
    service.verification_ports = verification_ports(database_url)
    return service
