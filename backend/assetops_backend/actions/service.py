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
    APPLIED,
    FAILED,
    OBSERVATION_CODE,
    PENDING,
    RESOLUTION_WITHDRAWN,
    RESOLVED,
    SYSTEM_DEMO,
    Selector,
    UnknownEvent,
    reduce,
    select,
)
from assetops_backend.actions.ports import ActionRefused, ActionStore, ApplyFailed, FoundationPublish
from assetops_backend.evidence.provenance_read import PROVENANCE_NOT_WIRED, PROVENANCE_UNREADABLE, unresolved

# (tenant_id, site_id, finding_id, revision_id | None, source_open) ->
#   {"revision_id", "latest_revision_id", "is_latest", "claim_is_current"} | None (unknown in this Site)
FindingCurrentness = Callable[[UUID, UUID, UUID, "UUID | None", bool], "dict[str, Any] | None"]
# S4-05b phase 2 (D-2026-10-16-s405b-label item 3): (tenant_id, site_id, finding_revision_id) -> the stored
# exact-revision source provenance block (`evidence/provenance_read.py`). Never a Site, date, spec or latest head.
SourceRead = Callable[[UUID, UUID, Any], "dict[str, Any]"]

OBSERVATION_WINDOW = timedelta(days=30)
FAILURE_STATUS = {"ACTION_FOUNDATION_STALE": 409, "ACTION_PUBLISH_REFUSED": 409}
OUTCOME_PENDING = {"state": "PENDING", "statement": "No verification exists yet; nothing is claimed about an effect, "
                                                    "a saving or approval."}


PRIOR_ACTION_UNRESOLVED = "PRIOR_ACTION_UNRESOLVED"
PRIOR_ACTION_MESSAGE = ("An earlier reserve-trial-1 Action on this Finding is unresolved (application pending, "
                        "including failed attempts awaiting retry, or applied with verification pending), so a new "
                        "trial cannot be accepted. Follow the earlier Action.")
# `D-2026-10-15-s601-reopen`: after acceptance an Action is PENDING (failed attempts leave it PENDING) or APPLIED.
# Both are unresolved: no verification exists yet, and even a completed verification outcome is not permission for
# another trial until S6-02 defines an explicit resolved/closed transition. So no reduced state releases the guard.
UNRESOLVED_APPLICATION = (PENDING, APPLIED)
# S6-02a (`D-2026-10-16-s6-verification`): the latest ordered RESOLVED releases the hold; RESOLUTION_WITHDRAWN restores
# it. A RESOLVED INEFFECTIVE with a measured GUARDRAIL_FAIL closes the trial but blocks the battery trial scope, and a
# closure/late-reading overlap blocks it permanently (no reviewer override here).
PRIOR_TRIAL_GUARDRAIL_FAILED = "PRIOR_TRIAL_GUARDRAIL_FAILED"
PRIOR_TRIAL_REASSESSMENT_OVERLAP = "PRIOR_TRIAL_REASSESSMENT_OVERLAP"
BLOCK_MESSAGES = {
    PRIOR_ACTION_UNRESOLVED: PRIOR_ACTION_MESSAGE,
    PRIOR_TRIAL_GUARDRAIL_FAILED: (
        "An earlier reserve-trial-1 Action on this battery was resolved INEFFECTIVE with a measured reserve/service "
        "guardrail failure, so no new trial can be accepted until a future rollback/review contract."),
    PRIOR_TRIAL_REASSESSMENT_OVERLAP: (
        "An Action on this battery was accepted after late evidence had invalidated an earlier trial's resolution "
        "but before the evaluator withdrew it; new trials on this battery are permanently blocked (no reviewer "
        "override exists yet)."),
}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def is_unresolved(state: dict[str, Any]) -> bool:
    resolution = state.get("resolution")
    return state["application"] in UNRESOLVED_APPLICATION and not (
        resolution is not None and resolution["state"] == RESOLVED)


def _instant_of(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None


def ordered_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(events, key=lambda e: (e["recorded_at"], str(e["id"])))


def reassessment_overlaps(actions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Closure/late-reading overlaps among one battery trial scope's Actions, from persisted times and lineage.

    `D-2026-10-16-s602a-holds` F2: only a RESOLUTION_WITHDRAWN whose persisted attribution is CAUSAL counts (the
    exact accepted readings that made that closure lose its pinned basis; NONE and INDETERMINATE never overlap).
    Every other Action accepted strictly after the earliest such reading's acceptance (itself after the closure)
    and before the withdrawal was recorded overlaps. An Action accepted before the evidence arrived does not."""
    out = []
    for closed in actions:
        resolved_at = resolved_id = None
        for event in ordered_events(closed["events"]):
            if event["kind"] == RESOLVED:
                resolved_at, resolved_id = event["recorded_at"], event["id"]
            elif event["kind"] == RESOLUTION_WITHDRAWN and resolved_at is not None:
                payload = event.get("payload") or {}
                causal = payload.get("attribution") == "CAUSAL"
                evidence = (payload.get("invalidating_evidence") or []) if causal else []
                arrived = [t for t in (_instant_of(e.get("accepted_at")) for e in evidence) if t is not None]
                if arrived and len(arrived) == len(evidence):
                    lo, hi = min(arrived), event["recorded_at"]
                    for other in actions:
                        if other["id"] != closed["id"] and resolved_at < lo < other["created_at"] < hi:
                            out.append({"action_id": str(other["id"]), "action_code": other["action_code"],
                                        "closure_action_id": str(closed["id"]),
                                        "closure_action_code": closed["action_code"],
                                        "resolved_event_id": str(resolved_id),
                                        "withdrawn_event_id": str(event["id"]),
                                        "withdrawn_outcome_id": str(event.get("verification_outcome_id")),
                                        "invalidating_evidence_ids": sorted(str(e["id"]) for e in evidence),
                                        "earliest_invalidating_accepted_at": lo.isoformat(),
                                        "withdrawn_at": hi.isoformat()})
                resolved_at = None
    return out


def action_links(site_code: str, action_id: Any) -> dict[str, str]:
    return {"action": f"/sites/{site_code}/actions/{action_id}",
            "api_action": f"/api/sites/{site_code}/actions/{action_id}"}


def prior_action(action: dict[str, Any], site_code: str, selected_revision_id: str | None) -> dict[str, Any]:
    """One Action on the canonical Finding, labelled with its own origin revision (never the selected one)."""
    state = reduce(action["events"])
    origin = str(action["origin_finding_revision_id"])
    return {"action_id": str(action["id"]), "action_code": action["action_code"],
            "recommendation_key": action["recommendation_key"], "rule_id": action["rule_id"],
            "asset_id": str(action["asset_id"]), "field": action["field"],
            "accepted_at": action["created_at"].isoformat(),
            "origin": {"finding_id": str(action["origin_finding_id"]), "finding_revision_id": origin,
                       "revision_no": action.get("origin_revision_no"),
                       "is_selected_revision": origin == selected_revision_id},
            "application": {"state": state["application"], "application_attempts": state["application_attempts"],
                            "failed_attempts": state["failed_attempts"],
                            "last_failure": _wire(state["last_failure"])},
            "outcome": state["outcome"], "unresolved": is_unresolved(state),
            **({"resolution": _wire(state["resolution"])} if state.get("resolution") else {}),
            **({"trial_block": PRIOR_TRIAL_GUARDRAIL_FAILED} if guardrail_closed(state) else {}),
            "links": action_links(site_code, action["id"])}


def guardrail_closed(state: dict[str, Any]) -> bool:
    resolution = state.get("resolution")
    return bool(resolution and resolution["state"] == RESOLVED and resolution["guardrail_failed"])


def blocks_trial(prior: dict[str, Any]) -> bool:
    return (prior["unresolved"] or prior.get("trial_block") == PRIOR_TRIAL_GUARDRAIL_FAILED) \
        and prior["rule_id"] == reserve_trial.RULE_ID and prior["field"] == reserve_trial.FIELD


def prior_action_refusal(blocking: list[dict[str, Any]],
                         overlaps: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """The typed prior-trial reason over `prior_action` entries (the first is the earliest). Precedence: a
    closure/late-reading overlap, then a guardrail-failed closure, then an unresolved trial."""
    by_id = {p["action_id"]: p for p in blocking}
    if overlaps:
        code = PRIOR_TRIAL_REASSESSMENT_OVERLAP
        first = by_id.get(overlaps[0]["closure_action_id"]) or blocking[0]
    elif any(p.get("trial_block") == PRIOR_TRIAL_GUARDRAIL_FAILED for p in blocking):
        code = PRIOR_TRIAL_GUARDRAIL_FAILED
        first = next(p for p in blocking if p.get("trial_block") == PRIOR_TRIAL_GUARDRAIL_FAILED)
    else:
        code, first = PRIOR_ACTION_UNRESOLVED, blocking[0]
    out = {"code": code, "message": BLOCK_MESSAGES[code],
           "blocking_action_id": first["action_id"], "blocking_action_code": first["action_code"],
           "origin_finding_revision_id": first["origin"]["finding_revision_id"],
           "origin_revision_no": first["origin"]["revision_no"], "links": first["links"],
           "blocking_actions": blocking}
    if code == PRIOR_TRIAL_GUARDRAIL_FAILED:
        out["blocking_outcome_id"] = first["resolution"]["outcome_id"]
    if overlaps:
        out["overlaps"] = overlaps
    return out


def trial_refusal(actions: list[dict[str, Any]], priors: list[dict[str, Any]]) -> dict[str, Any] | None:
    """The block over one battery trial scope: `actions` are its store rows (with events), `priors` the
    `prior_action` entries that may block (already filtered to the offered scope)."""
    overlaps = reassessment_overlaps(actions)
    blocking = [p for p in priors if blocks_trial(p)]
    if overlaps:
        ids = {o["closure_action_id"] for o in overlaps} | {o["action_id"] for o in overlaps}
        blocking += [p for p in priors if p["action_id"] in ids and p not in blocking]
    if not blocking:
        return None
    return prior_action_refusal(blocking, overlaps)


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
                 capability: CapabilityCheck = no_capability, clock: Callable[[], datetime] = utc_now,
                 publish: FoundationPublish | None = None, source: SourceRead | None = None) -> None:
        self.store, self.currentness, self.capability, self.clock = store, currentness, capability, clock
        self.publish, self.source = publish, source
        self.verification_ports = None  # S6-02a: S3/S4 day currentness and source provenance (composition sets it)

    def source_provenance(self, tenant_id: UUID, site_id: UUID, finding_revision_id: Any) -> dict[str, Any]:
        """The exact pinned FindingRevision's stored source; unwired or failing reads are UNKNOWN, never positive."""
        if self.source is None:
            return unresolved(PROVENANCE_NOT_WIRED, tenant_id, site_id, finding_revision_id)
        try:
            return self.source(tenant_id, site_id, finding_revision_id)
        except Exception as error:  # noqa: BLE001 - fail closed: Source unverified
            return unresolved(PROVENANCE_UNREADABLE, tenant_id, site_id, finding_revision_id,
                              detail=type(error).__name__)

    # ---- capability --------------------------------------------------------------------------------------

    def demand(self, tenant_id: UUID, site_id: UUID, site_code: str, command: str,
               finding_id: UUID | None) -> Capability:
        granted = self.capability(tenant_id, site_id, site_code, command, finding_id)
        if not granted.allowed:
            raise ActionRefused(403, "SYSTEM_DEMO_CAPABILITY_DENIED", granted.unavailable_reason or "Denied.",
                                system_demo_capability=granted.wire())
        return granted

    def authorize_accept(self, tenant_id: UUID, site_id: UUID, site_code: str, finding_id: UUID) -> Capability:
        """Unknown or wrong-Site Finding 404, then the scoped grant for this fixture record (403)."""
        if self.store.latest_revision(tenant_id, site_id, finding_id) is None:
            raise ActionRefused(404, "FINDING_NOT_FOUND", "No such Finding or revision for this Site.")
        return self.demand(tenant_id, site_id, site_code, "ACCEPT", finding_id)

    def authorize_action(self, tenant_id: UUID, site_id: UUID, site_code: str, command: str,
                         action_id: UUID) -> tuple[Capability, dict[str, Any]]:
        """Unknown or wrong-Site Action 404, then the grant for its origin Finding's fixture record (403)."""
        action = self.store.action(tenant_id, site_id, action_id)
        if action is None:
            raise ActionRefused(404, "ACTION_NOT_FOUND", "No such Action for this Site.")
        return self.demand(tenant_id, site_id, site_code, command, action["origin_finding_id"]), action

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
        current = self.currentness(tenant_id, site_id, finding_id, revision_id, source_open)
        if current is None:
            return None
        selected = str(current["revision_id"])
        # Read before the live recomputation, so no live result (stale basis, later revision, failure) hides them.
        prior = [prior_action(a, site_code, selected)
                 for a in self.store.actions_for_finding(tenant_id, site_id, finding_id)]
        inputs = self.store.rule_inputs(tenant_id, site_id, finding_id, UUID(selected),
                                        is_latest=bool(current["is_latest"]),
                                        claim_is_current=bool(current["claim_is_current"]) and source_open,
                                        at=self.clock())
        evaluation = (reserve_trial.evaluate(inputs) if inputs is not None
                      else reserve_trial.Evaluation(False, "LIVE_RECOMPUTATION_FAILED", None))
        accepted = self.store.actions_for_revision(tenant_id, site_id, UUID(selected))
        offered = evaluation.proposal if evaluation.available else None
        # A new acceptance is held while another unresolved trial on this Finding exists: against the live key when
        # one is offered, otherwise (stale basis, later revision, failure) for any. An accepted selected revision
        # with no new key on offer shows its own snapshot instead.
        # S6-02a: the hold is battery-scoped - every Action of this (Site, battery asset, reserve field, rule) trial
        # scope, on any Finding, counts (`D-2026-10-16-s6-verification`). With no live key on offer the battery is
        # not known, so every battery of the Site is that scope.
        seen = {p["action_id"] for p in prior}
        scope_rows = self.store.trial_actions(tenant_id, site_id, offered["asset_id"] if offered else None,
                                              reserve_trial.RULE_ID)
        pool = list(prior) + [p for p in (prior_action(a, site_code, selected) for a in scope_rows)
                              if p["action_id"] not in seen]
        candidates = [p for p in pool if offered is None or (
            p["asset_id"] == offered["asset_id"] and p["recommendation_key"] != offered["recommendation_key"])]
        rows = [a for a in scope_rows if offered is None or a["recommendation_key"] != offered["recommendation_key"]]
        block = None if accepted and offered is None else trial_refusal(rows, candidates)
        capability = self.capability(tenant_id, site_id, site_code, "ACCEPT", finding_id)
        if block is not None:  # no Accept capability for a new key while the battery trial scope is held
            capability = Capability(False, "ACCEPT", capability.fixture_id,
                                    f"{block['code']}: {block['message']}", capability.manifest_id)
        live = {"label": "Live recomputation from current persisted inputs (not the accepted proposal)",
                "state": "AVAILABLE" if evaluation.available else "UNAVAILABLE",
                "unavailable": evaluation.unavailable(), "segments": list(evaluation.segments),
                "proposal": evaluation.proposal}
        base = f"/sites/{site_code}/findings/{finding_id}"
        body: dict[str, Any] = {
            "site_code": site_code, "finding_id": str(finding_id), "revision_id": selected,
            "source_provenance": self.source_provenance(tenant_id, site_id, selected),
            "money_consequence": {
                "label": "Consequence", "basis": {"finding_id": str(finding_id), "finding_revision_id": selected},
                "statement": "The stored S4 cost consequence belongs to this exact Finding revision, not to the "
                             "trial. The trial predicts no saving, runtime or safety change.",
                "links": {"api_consequences": f"/api{base}/financial-consequences?revision_id={selected}"}},
            "latest_revision_id": str(current["latest_revision_id"]), "is_latest": bool(current["is_latest"]),
            "rule": {"id": reserve_trial.RULE_ID, "version": reserve_trial.RULE_VERSION,
                     "limitation": {"code": reserve_trial.LIMITATION_CODE, "text": reserve_trial.LIMITATION_TEXT}},
            "system_demo_capability": capability.wire(),
            "prior_actions": {
                "label": "Actions accepted on this Finding (any revision). Each keeps its own origin revision; the "
                         "selected revision is `revision_id`.", "items": prior},
            "prior_action_block": block,
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
        elif block is not None:
            # The prior Action is the reason; the current-basis result stays a separate live reason beside it.
            body.update(state=block["code"], basis="SERVED_FROM_PERSISTED_INPUTS", proposal=None,
                        unavailable={k: block[k] for k in ("code", "message", "blocking_action_id",
                                                           "origin_finding_revision_id", "links")},
                        segments=list(evaluation.segments), accepted=[], live_status=live)
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
                "links": action_links(site_code, action["id"])}

    # ---- accept ------------------------------------------------------------------------------------------

    def accept(self, tenant_id: UUID, site_id: UUID, site_code: str, finding_id: UUID, command: dict[str, Any],
               source_open: bool) -> tuple[int, dict[str, Any]]:
        granted = self.authorize_accept(tenant_id, site_id, site_code, finding_id)
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
        offered = evaluation.proposal if evaluation.available else None
        guard = self._prior_guard(site_code, revision_id, evaluation)
        # Checked here so a stale or unavailable live result is reported beside the prior Action, and again
        # atomically under the store's trial lock (two accepts on different revisions cannot both pass).
        guard([a for a in self.store.trial_actions(tenant_id, site_id, offered["asset_id"] if offered else None,
                                                    reserve_trial.RULE_ID)
               if offered is None or a["recommendation_key"] != offered["recommendation_key"]])
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
            recorded_at=self.clock(), guard=guard)
        if replayed:
            return self._replay(action, digest, site_code)
        return 201, self._accepted_body(action, event, site_code, replayed=False)

    @staticmethod
    def _prior_guard(site_code: str, revision_id: UUID, evaluation: reserve_trial.Evaluation):
        """Raise 409 with the typed prior-trial code (unresolved, guardrail-failed closure or reassessment overlap)
        over the given Actions of this battery trial scope."""
        def guard(actions: list[dict[str, Any]]) -> None:
            refusal = trial_refusal(actions, [prior_action(a, site_code, str(revision_id)) for a in actions])
            if refusal is not None:
                raise ActionRefused(409, refusal["code"], refusal["message"],
                                    **{k: v for k, v in refusal.items() if k not in ("code", "message")},
                                    live_status={"label": "Live recomputation from current persisted inputs (a "
                                                          "separate reason, not the refusal)",
                                                 "state": "AVAILABLE" if evaluation.available else "UNAVAILABLE",
                                                 "unavailable": evaluation.unavailable()})
        return guard

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
        granted, _action = self.authorize_action(tenant_id, site_id, site_code, "OBSERVE", action_id)
        occurred: datetime = command["occurred_at"].astimezone(timezone.utc)  # one digest per instant (review L5)
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

    # ---- apply (Action lock -> S1 publish under the Site lock -> artifact + APPLIED, one commit) ----------

    def apply(self, tenant_id: UUID, site_id: UUID, site_code: str, action_id: UUID,
              command: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        granted, _action = self.authorize_action(tenant_id, site_id, site_code, "APPLY", action_id)
        if self.publish is None:
            raise ActionRefused(503, "ACTION_PUBLISH_UNAVAILABLE", "No Foundation publish is composed.")
        value: Decimal = command["value"]
        effective: datetime = command["effective_from"].astimezone(timezone.utc)
        expected: UUID = command["expected_foundation_revision_id"]
        payload = {"command": "APPLY", "action_id": str(action_id), "expected_foundation_revision_id": str(expected),
                   "value": reserve_trial.text_of(value), "effective_from": effective.isoformat(),
                   "idempotency_key": command["idempotency_key"]}
        digest = reserve_trial.sha(payload)
        recorded = self.clock()
        publish = self.publish

        def attempt(connection: Any, action: dict[str, Any], events: list[dict[str, Any]], then) -> None:
            # Runs after the store's Action lock and idempotency check, so an identical retry returns its original
            # event before any of these checks, including no-change.
            accepted_at = next(e["recorded_at"] for e in events if e["kind"] == ACCEPTED)
            if value != action["proposed_value"]:
                raise ApplyFailed(422, "ACTION_VALUE_INVALID",
                                  f"Only the accepted proposal {reserve_trial.text_of(action['proposed_value'])}"
                                  f"{action['unit']} can be applied.")
            if effective < recorded or effective <= accepted_at:
                raise ApplyFailed(422, "ACTION_EFFECTIVE_TIME_INVALID",
                                  "effective_from must be at or after the server time and after acceptance.",
                                  recorded_at=recorded.isoformat(), accepted_at=accepted_at.isoformat())
            publish(site_code, connection, then, asset_code=action["snapshot"]["asset_code"], value=float(value),
                    effective_from=effective, recorded_at=recorded, expected_revision_id=expected,
                    expected_value=float(action["old_value"]),
                    note=f"{action['action_code']}: SYSTEM demonstration application of reserve-trial-1 "
                         "(a policy-sensitivity trial, not a predicted saving)")

        out = self.store.apply(tenant_id, site_id, action_id, idempotency_key=command["idempotency_key"],
                               payload=payload, payload_sha256=digest, fixture_id=granted.fixture_id or "",
                               recorded_at=recorded, expected_foundation_revision_id=expected, attempt=attempt)
        outcome = out["outcome"]
        if outcome == "NOT_FOUND":
            raise ActionRefused(404, "ACTION_NOT_FOUND", "No such Action for this Site.")
        if outcome == "FOUNDATION_UNKNOWN":
            raise ActionRefused(404, "FOUNDATION_REVISION_NOT_FOUND",
                                "expected_foundation_revision_id is not a Foundation revision of this Site.")
        if outcome == "ALREADY_APPLIED":
            raise ActionRefused(409, "ACTION_ALREADY_APPLIED",
                                "This Action is already applied; nothing was attempted.",
                                applied_event_id=str(out["event"]["id"]))
        event = out["event"]
        if event["payload_sha256"] != digest:
            raise ActionRefused(409, "IDEMPOTENCY_KEY_CONFLICT",
                                "This idempotency key was already used with a different command.",
                                event_id=str(event["id"]))
        if event["kind"] == FAILED:
            failure = out.get("failure")
            raise ActionRefused(FAILURE_STATUS.get(event["failure_code"], 422), event["failure_code"],
                                failure.message if failure is not None else "This attempt failed earlier.",
                                replayed=outcome == "REPLAY", event=event_wire(event),
                                expected_foundation_revision_id=str(expected),
                                current_foundation_revision_id=_wire(event["current_foundation_revision_id"]),
                                **({} if failure is None else failure.extra))
        change = out.get("change")
        return (200 if outcome == "REPLAY" else 201), {
            "replayed": outcome == "REPLAY", "event": event_wire(event),
            "change": None if change is None else self._change_wire(tenant_id, site_id, site_code, change),
            "outcome": OUTCOME_PENDING}

    # ---- change artifact ---------------------------------------------------------------------------------

    def _change_wire(self, tenant_id: UUID, site_id: UUID, site_code: str,
                     change: dict[str, Any]) -> dict[str, Any]:
        ids = [change[k] for k in ("expected_foundation_revision_id", "superseded_foundation_revision_id",
                                   "new_foundation_revision_id", "split_foundation_revision_id") if change[k]]
        revisions = [_wire(r) for r in self.store.foundation_revisions(tenant_id, site_id, ids)]
        action_base = f"/api/sites/{site_code}/actions/{change['action_id']}"
        return {
            "change_id": str(change["id"]), "action_id": str(change["action_id"]),
            "applied_event_id": str(change["applied_event_id"]),
            "command_idempotency_key": change["command_idempotency_key"],
            "asset_id": str(change["asset_id"]), "field": change["field"], "unit": change["unit"],
            "old_value": _wire(change["old_value"]), "new_value": _wire(change["new_value"]),
            "expected_foundation_revision_id": str(change["expected_foundation_revision_id"]),
            "superseded_foundation_revision_id": str(change["superseded_foundation_revision_id"]),
            "new_foundation_revision_id": str(change["new_foundation_revision_id"]),
            "split_foundation_revision_id": _wire(change["split_foundation_revision_id"]),
            "foundation_revisions": revisions,  # ordered by version
            "binding_set_revisions": {
                relation.lower(): [str(b["binding_set_revision_id"]) for b in change["bindings"]
                                   if b["relation"] == relation] for relation in ("SUPERSEDED", "INSERTED")},
            "effective_from": change["effective_from"].isoformat(),
            "recorded_at": change["recorded_at"].isoformat(),
            "validity": change["validity"], "label": SYSTEM_DEMO.label, "outcome": OUTCOME_PENDING,
            "statement": "The Site Foundation reserve was changed by a SYSTEM demonstration command. No measured "
                         "effect, saving or verification is claimed.",
            "links": {"self": f"/api/sites/{site_code}/foundation/changes/{change['id']}",
                      "action": action_base,
                      "applied_event": f"{action_base}/events?event_id={change['applied_event_id']}",
                      "ui_action": f"/sites/{site_code}/actions/{change['action_id']}"},
        }

    def change(self, tenant_id: UUID, site_id: UUID, site_code: str, change_id: UUID) -> dict[str, Any] | None:
        change = self.store.change(tenant_id, site_id, change_id)
        if change is None:
            return None
        return {"site_code": site_code, "change": self._change_wire(tenant_id, site_id, site_code, change)}

    def _change_in(self, tenant_id: UUID, site_id: UUID, site_code: str, action: dict[str, Any],
                   prefix: list[dict[str, Any]]) -> dict[str, Any] | None:
        """The change artifact only when its APPLIED event is inside the selected history prefix."""
        if not any(e["kind"] == APPLIED for e in prefix):
            return None
        change = self.store.change_for_action(tenant_id, site_id, action["id"])
        return None if change is None else self._change_wire(tenant_id, site_id, site_code, change)

    def _application_basis(self, tenant_id: UUID, site_id: UUID, action: dict[str, Any]) -> dict[str, Any]:
        now = self.clock()
        current = self.store.current_foundation(tenant_id, site_id, now)
        reserve = None if current is None else next(
            (r for r in current["reserves"] if str(r["asset_id"]) == str(action["asset_id"])), None)
        return {"label": "The Site Foundation revision covering the read time (covers_instant). An apply command names "
                         "a revision as expected_foundation_revision_id and the server re-checks it under the Site "
                         "lock against the revision covering the command's own effective_from, so a Foundation change "
                         "dated between the read time and effective_from makes the apply ACTION_FOUNDATION_STALE.",
                "read_at": now.isoformat(), "covers_instant": now.isoformat(),
                "current_foundation_revision_id": None if current is None else str(current["id"]),
                "current_reserve": None if reserve is None else {"value": _wire(reserve["value"]),
                                                                 "unit": reserve["unit"]},
                "matches_accepted_basis": reserve is not None
                and reserve_trial.number(reserve["value"]) == action["old_value"]}

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
        capability = {c.lower(): self.capability(tenant_id, site_id, site_code, c, action["origin_finding_id"]).wire()
                      for c in ("APPLY", "OBSERVE")}
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
            "change": self._change_in(tenant_id, site_id, site_code, action, prefix),
            "application_basis": self._application_basis(tenant_id, site_id, action),
            "source_provenance": self.source_provenance(tenant_id, site_id, action["origin_finding_revision_id"]),
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
