"""S6-01a Action service: `reserve-trial-1` recommendation, acceptance, the demo observation and exact reads.

The service decides; the store persists. Every command is a SYSTEM demonstration command run only under the
server-issued scoped capability (checked here again even though the read contract exposes it). Acceptance and
observation use server time for `recorded_at`; only OBSERVED carries a client-stated `occurred_at`, bounded by
`accepted_at <= occurred_at <= recorded_at` and at most 30 days back.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Callable
from uuid import UUID

from assetops_backend.actions import reserve_trial
from assetops_backend.actions.capability import Capability, CapabilityCheck, no_capability
from assetops_backend.actions.lifecycle import (
    ACCEPTED,
    OBSERVATION_CODE,
    SYSTEM_DEMO,
    Selector,
    UnknownEvent,
    reduce,
    select,
)
from assetops_backend.actions.ports import ActionRefused, ActionStore

# (tenant_id, site_id, finding_id, revision_id | None, source_open) ->
#   {"revision_id", "latest_revision_id", "is_latest", "claim_is_current"} | None (unknown in this Site)
FindingCurrentness = Callable[[UUID, UUID, UUID, "UUID | None", bool], "dict[str, Any] | None"]

OBSERVATION_WINDOW = timedelta(days=30)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _wire(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Decimal):
        return reserve_trial.text_of(value)
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, dict):
        return {k: _wire(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_wire(v) for v in value]
    return value


def event_wire(event: dict[str, Any]) -> dict[str, Any]:
    out = _wire(event)
    out["actor"] = {"kind": event["actor_kind"], "id": event["actor_id"], "label": SYSTEM_DEMO.label,
                    "source_channel": event["source_channel"], "authorization_basis": event["authorization_basis"],
                    "triggering": {"service": event["triggering_service"], "job": event["triggering_job"],
                                   "command": event["triggering_command"], "fixture": event["triggering_fixture"]}}
    out["occurred_before_recorded"] = event["occurred_at"] < event["recorded_at"]
    return out


class ActionService:
    def __init__(self, store: ActionStore, currentness: FindingCurrentness,
                 capability: CapabilityCheck = no_capability, clock: Callable[[], datetime] = utc_now) -> None:
        self.store, self.currentness, self.capability, self.clock = store, currentness, capability, clock

    # ---- capability --------------------------------------------------------------------------------------

    def demand(self, tenant_id: UUID, site_id: UUID, site_code: str, command: str) -> Capability:
        granted = self.capability(tenant_id, site_id, site_code, command)
        if not granted.allowed:
            raise ActionRefused(403, "SYSTEM_DEMO_CAPABILITY_DENIED", granted.unavailable_reason or "Denied.",
                                system_demo_capability=granted.wire())
        return granted

    # ---- recommendation ----------------------------------------------------------------------------------

    def _evaluate(self, tenant_id: UUID, site_id: UUID, finding_id: UUID, revision_id: UUID | None,
                  source_open: bool) -> tuple[dict[str, Any], reserve_trial.Evaluation] | None:
        current = self.currentness(tenant_id, site_id, finding_id, revision_id, source_open)
        if current is None:
            return None
        inputs = self.store.rule_inputs(tenant_id, site_id, finding_id, UUID(str(current["revision_id"])),
                                        is_latest=bool(current["is_latest"]),
                                        claim_is_current=bool(current["claim_is_current"]) and source_open,
                                        at=self.clock())
        if inputs is None:
            return None
        return current, reserve_trial.evaluate(inputs)

    def recommendation(self, tenant_id: UUID, site_id: UUID, site_code: str, finding_id: UUID,
                       revision_id: UUID | None, source_open: bool) -> dict[str, Any] | None:
        found = self._evaluate(tenant_id, site_id, finding_id, revision_id, source_open)
        if found is None:
            return None
        current, evaluation = found
        selected = str(current["revision_id"])
        accepted = self.store.actions_for_revision(tenant_id, site_id, UUID(selected))
        live = {"label": "Live recomputation from current persisted inputs (not the accepted proposal)",
                "state": "AVAILABLE" if evaluation.available else "UNAVAILABLE",
                "unavailable": evaluation.unavailable(), "segments": list(evaluation.segments),
                "proposal": evaluation.proposal}
        base = f"/sites/{site_code}/findings/{finding_id}"
        body: dict[str, Any] = {
            "site_code": site_code, "finding_id": str(finding_id), "revision_id": selected,
            "latest_revision_id": str(current["latest_revision_id"]), "is_latest": bool(current["is_latest"]),
            "rule": {"id": reserve_trial.RULE_ID, "version": reserve_trial.RULE_VERSION,
                     "limitation": {"code": reserve_trial.LIMITATION_CODE, "text": reserve_trial.LIMITATION_TEXT}},
            "system_demo_capability": self.capability(tenant_id, site_id, site_code, "ACCEPT").wire(),
            "links": {"finding": f"{base}?revision_id={selected}",
                      "recommendation": f"{base}/recommendation?revision_id={selected}",
                      "api_recommendation": f"/api{base}/recommendation?revision_id={selected}"},
        }
        if accepted:
            # Once accepted, the stored snapshot is the proposal; live status is shown beside it, never instead.
            body.update(state="ACCEPTED", basis="ACCEPTED_SNAPSHOT", proposal=None, unavailable=None,
                        accepted=[self._accepted(a, site_code) for a in accepted], live_status={
                            **live, "already_accepted": evaluation.available and any(
                                a["recommendation_key"] == evaluation.proposal["recommendation_key"]  # type: ignore[index]
                                for a in accepted)})
        else:
            body.update(state="AVAILABLE" if evaluation.available else "UNAVAILABLE",
                        basis="SERVED_FROM_PERSISTED_INPUTS", proposal=evaluation.proposal,
                        unavailable=evaluation.unavailable(), segments=list(evaluation.segments),
                        accepted=[], live_status=None)
        return body

    @staticmethod
    def _accepted(action: dict[str, Any], site_code: str) -> dict[str, Any]:
        return {"action_id": str(action["id"]), "action_code": action["action_code"],
                "accepted_at": action["created_at"].isoformat(), "snapshot": _wire(action["snapshot"]),
                "snapshot_sha256": action["snapshot_sha256"],
                "links": {"action": f"/sites/{site_code}/actions/{action['id']}",
                          "api_action": f"/api/sites/{site_code}/actions/{action['id']}"}}

    # ---- accept ------------------------------------------------------------------------------------------

    def accept(self, tenant_id: UUID, site_id: UUID, site_code: str, finding_id: UUID, command: dict[str, Any],
               source_open: bool) -> tuple[int, dict[str, Any]]:
        granted = self.demand(tenant_id, site_id, site_code, "ACCEPT")
        revision_id = command["revision_id"]
        if self.currentness(tenant_id, site_id, finding_id, revision_id, source_open) is None:
            raise ActionRefused(404, "FINDING_NOT_FOUND", "No such Finding or revision for this Site.")
        payload = {"command": "ACCEPT", "finding_id": str(finding_id), "revision_id": str(revision_id),
                   "recommendation_key": command["recommendation_key"],
                   "foundation_revision_id": str(command["foundation_revision_id"]),
                   "proposed_value": reserve_trial.text_of(command["proposed_value"]),
                   "idempotency_key": command["idempotency_key"]}
        digest = reserve_trial.sha(payload)
        existing = self.store.action_for_recommendation(tenant_id, site_id, command["recommendation_key"])
        if existing is not None:
            return self._replay(existing, digest, site_code)
        found = self._evaluate(tenant_id, site_id, finding_id, revision_id, source_open)
        if found is None:
            raise ActionRefused(404, "FINDING_NOT_FOUND", "No such Finding or revision for this Site.")
        evaluation = found[1]
        if not evaluation.available:
            raise ActionRefused(422, "RECOMMENDATION_UNAVAILABLE", "No trial can be accepted for this revision.",
                                unavailable=evaluation.unavailable())
        proposal = evaluation.proposal or {}
        mismatched = [name for name, want in (
            ("recommendation_key", proposal["recommendation_key"]),
            ("foundation_revision_id", proposal["foundation_revision_id"]),
            ("proposed_value", proposal["proposed_value"])) if payload[name] != want]
        if mismatched:
            raise ActionRefused(422, "RECOMMENDATION_MISMATCH",
                                "The command does not match the server's current proposal.", fields=mismatched)
        action, event, replayed = self.store.accept(
            tenant_id, site_id, proposal, payload_sha256=digest, payload=payload,
            idempotency_key=command["idempotency_key"], fixture_id=granted.fixture_id or "",
            recorded_at=self.clock())
        if replayed:
            return self._replay(action, digest, site_code)
        return 201, self._accepted_body(action, event, site_code, replayed=False)

    def _replay(self, action: dict[str, Any], digest: str, site_code: str) -> tuple[int, dict[str, Any]]:
        if action["acceptance_payload_sha256"] != digest:
            raise ActionRefused(409, "ACTION_ACCEPTANCE_CONFLICT",
                                "This recommendation was already accepted with a different command.",
                                action_id=str(action["id"]))
        events = self.store.events(action["tenant_id"], action["site_id"], action["id"])
        accepted = next(e for e in events if e["kind"] == ACCEPTED)
        return 200, self._accepted_body(action, accepted, site_code, replayed=True)

    def _accepted_body(self, action: dict[str, Any], event: dict[str, Any], site_code: str, *,
                       replayed: bool) -> dict[str, Any]:
        return {"replayed": replayed, "action": self._accepted(action, site_code), "event": event_wire(event)}

    # ---- observe (state-neutral demo note) ---------------------------------------------------------------

    def observe(self, tenant_id: UUID, site_id: UUID, site_code: str, action_id: UUID,
                command: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        granted = self.demand(tenant_id, site_id, site_code, "OBSERVE")
        action = self.store.action(tenant_id, site_id, action_id)
        if action is None:
            raise ActionRefused(404, "ACTION_NOT_FOUND", "No such Action for this Site.")
        occurred: datetime = command["occurred_at"]
        payload = {"command": "OBSERVE", "action_id": str(action_id), "observation_code": OBSERVATION_CODE,
                   "occurred_at": occurred.isoformat(), "idempotency_key": command["idempotency_key"]}
        digest = reserve_trial.sha(payload)
        events = self.store.events(tenant_id, site_id, action_id)
        prior = next((e for e in events if e["idempotency_key"] == command["idempotency_key"]), None)
        if prior is not None:
            return self._observed(prior, digest)
        recorded = self.clock()
        accepted_at = next(e["recorded_at"] for e in events if e["kind"] == ACCEPTED)
        if occurred > recorded:
            raise ActionRefused(422, "OBSERVATION_IN_FUTURE", "occurred_at is later than the server time.")
        if occurred < accepted_at or recorded - occurred > OBSERVATION_WINDOW:
            raise ActionRefused(422, "OBSERVATION_TIME_OUT_OF_BOUNDS",
                                "occurred_at must be at or after acceptance and at most 30 days before now.",
                                accepted_at=accepted_at.isoformat(), recorded_at=recorded.isoformat())
        event, replayed = self.store.observe(tenant_id, site_id, action_id, occurred_at=occurred,
                                             idempotency_key=command["idempotency_key"], payload=payload,
                                             payload_sha256=digest, fixture_id=granted.fixture_id or "",
                                             recorded_at=recorded)
        if replayed:
            return self._observed(event, digest)
        return 201, {"replayed": False, "event": event_wire(event),
                     "statement": "A state-neutral SYSTEM demonstration note; it changes no application or "
                                  "verification state and claims no effect."}

    @staticmethod
    def _observed(event: dict[str, Any], digest: str) -> tuple[int, dict[str, Any]]:
        if event["payload_sha256"] != digest:
            raise ActionRefused(409, "IDEMPOTENCY_KEY_CONFLICT",
                                "This idempotency key was already used with a different command.",
                                event_id=str(event["id"]))
        return 200, {"replayed": True, "event": event_wire(event)}

    # ---- exact reads -------------------------------------------------------------------------------------

    def _prefix(self, tenant_id: UUID, site_id: UUID, action_id: UUID,
                chosen: Selector) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]] | None:
        action = self.store.action(tenant_id, site_id, action_id)
        if action is None:
            return None
        events = self.store.events(tenant_id, site_id, action_id)
        try:
            prefix = select(events, chosen)
        except UnknownEvent:
            raise ActionRefused(404, "ACTION_EVENT_NOT_FOUND", "No such event for this Action.")
        return action, events, prefix

    def _selection(self, chosen: Selector, events: list[dict[str, Any]], prefix: list[dict[str, Any]]):
        return {**chosen.wire(), "order": "(recorded_at, id)",
                "basis": "server recorded_at; never a client time or occurred_at",
                "event_count": len(prefix), "total_event_count": len(events),
                "cutoff_event_id": str(prefix[-1]["id"]) if prefix else None,
                "cutoff_recorded_at": prefix[-1]["recorded_at"].isoformat() if prefix else None}

    def _links(self, site_code: str, action: dict[str, Any], chosen: Selector) -> dict[str, Any]:
        base = f"/sites/{site_code}/actions/{action['id']}"
        finding = f"/sites/{site_code}/findings/{action['origin_finding_id']}"
        q = chosen.query()
        return {"site": f"/sites/{site_code}", "canonical": base, "selected": f"{base}{q}",
                "history": f"{base}/history{q}", "api_action": f"/api{base}{q}", "api_events": f"/api{base}/events{q}",
                "origin_finding": f"{finding}?revision_id={action['origin_finding_revision_id']}",
                "finding": finding,
                "recommendation": f"/api{finding}/recommendation?revision_id={action['origin_finding_revision_id']}"}

    def action(self, tenant_id: UUID, site_id: UUID, site_code: str, action_id: UUID,
               chosen: Selector) -> dict[str, Any] | None:
        found = self._prefix(tenant_id, site_id, action_id, chosen)
        if found is None:
            return None
        action, events, prefix = found
        latest = self.store.latest_revision(tenant_id, site_id, action["origin_finding_id"])
        is_origin = latest is not None and latest["id"] == action["origin_finding_revision_id"]
        newer = None if latest is None or is_origin else {
            "latest_revision_id": str(latest["id"]), "revision_no": latest["revision_no"],
            "lifecycle": latest["lifecycle"], "transition": latest["transition"],
            "statement": "The Finding has a newer revision. This Action stays pinned to the revision it was "
                         "accepted for; the newer revision is shown beside it, not substituted."}
        capability = {c.lower(): self.capability(tenant_id, site_id, site_code, c).wire() for c in ("APPLY", "OBSERVE")}
        return {
            "site_code": site_code,
            "action": {"id": str(action["id"]), "action_code": action["action_code"],
                       "created_at": action["created_at"].isoformat(), "label": SYSTEM_DEMO.label,
                       "recommendation_key": action["recommendation_key"],
                       "acceptance_key": action["acceptance_key"]},
            "origin": {"finding_id": str(action["origin_finding_id"]),
                       "finding_revision_id": str(action["origin_finding_revision_id"]),
                       "primary_assessment_revision_id": str(action["primary_assessment_revision_id"])},
            "latest_finding_revision": None if latest is None else {
                "id": str(latest["id"]), "revision_no": latest["revision_no"], "lifecycle": latest["lifecycle"],
                "transition": latest["transition"], "is_origin": is_origin},
            "newer_revision_notice": newer,
            "basis": {"foundation_revision_id": str(action["foundation_revision_id"]),
                      "asset_id": str(action["asset_id"]), "input_sha256": action["input_sha256"],
                      "assessments": _wire(action["basis_assessments"]),
                      "evidence": _wire(action["basis_evidence"])},
            "accepted_recommendation": {"rule_id": action["rule_id"], "rule_version": action["rule_version"],
                                        "field": action["field"], "unit": action["unit"],
                                        "old_value": _wire(action["old_value"]),
                                        "proposed_value": _wire(action["proposed_value"]),
                                        "limitation": {"code": action["limitation_code"],
                                                       "text": action["limitation_text"]},
                                        "snapshot": _wire(action["snapshot"]),
                                        "snapshot_sha256": action["snapshot_sha256"]},
            "selection": self._selection(chosen, events, prefix),
            "state": _wire(reduce(prefix)),
            "last_event": event_wire(prefix[-1]) if prefix else None,
            "change": None,
            "system_demo_capability": capability,
            "links": self._links(site_code, action, chosen),
        }

    def events(self, tenant_id: UUID, site_id: UUID, site_code: str, action_id: UUID,
               chosen: Selector) -> dict[str, Any] | None:
        found = self._prefix(tenant_id, site_id, action_id, chosen)
        if found is None:
            return None
        action, events, prefix = found
        return {"site_code": site_code, "action_id": str(action_id), "action_code": action["action_code"],
                "selection": self._selection(chosen, events, prefix), "state": _wire(reduce(prefix)),
                "events": [event_wire(e) for e in prefix], "links": self._links(site_code, action, chosen)}
