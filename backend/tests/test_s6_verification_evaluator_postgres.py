"""S6-02a phase 2: the verification evaluator job, currentness gates, resolution events and prior-trial holds.

`D-2026-10-16-s6-verification`, `D-2026-10-16-s602-questions`, `D-2026-10-16-s602a-cutoff`. Real PostgreSQL over the
S4 F01/F02 cases (a `minigrid-roles-2` Site): S6-01 accepts and applies F01's reserve trial, a SYSTEM demonstration
VERIFY command freezes the plan, binds the later selection and requests evaluation; the evaluator job alone appends
outcome, metrics and RESOLVED / RESOLUTION_WITHDRAWN.

The roles-2 Site can never complete a window (no critical-load roles), so the real path is INCONCLUSIVE. The verdict
and hold cases (VERIFIED, guardrail failure, withdrawal, overlap) replace only the pure window evidence and the
source resolution with labelled TEST-SCOPED complete windows (`complete_windows`); S3/S4 currentness, plans,
bindings, the trial lock, outcome rows and events stay real. The complete positive path over real accepted public
evidence is the `D-verification-window` replay manifest.
"""

from __future__ import annotations

import json
import os
import threading
import time
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from sqlalchemy import text

from s6_action_records import normalise
from test_s4_finding_store_postgres import URL, CaseRunner, run_case  # noqa: F401
from test_s1_bindings_postgres import engine, store  # noqa: F401
from test_s6_action_store_postgres import CASES, fixture_grants, harness, runner  # noqa: F401
from test_s6_action_apply_postgres import T_APPLY, accepted, apply, current_foundation
from test_s6_verification_plan_postgres import (
    BASELINE,
    LATER,
    T_FREEZE,
    applied_action,
    base,
    freeze,
    settle,
    verifying,
)
from test_s6_verification_rules import full_window

from assetops_backend.actions import verification_rules as vr
from assetops_backend.actions.composition import verification_ports
from assetops_backend.actions.ports import ActionRefused
from assetops_backend.actions.reserve_trial import sha
from assetops_backend.actions.service import ActionService
from assetops_backend.actions.verification import VerificationPorts, VerificationService

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set")

UTC = timezone.utc
CLOSED = datetime(2026, 11, 2, 11, 0, tzinfo=UTC)  # after later_end 09:00
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "s6_verification_api_contract.json"
AUTHORED = {"state": "AUTHORED_DEMONSTRATION", "reasons": [], "publication_ids": ["test-scoped"],
            "source_classes": ["AUTHORED_DEMONSTRATION"],
            "fixtures": [{"fixture_id": "D-verification-window-test-scoped", "fixture_version": 1}], "runs": []}
REAL_WINDOW_EVIDENCE = vr.window_evidence


def evaluate(h, action_id: str, key: str, **over):
    return h.client.post(f"{base(action_id)}/evaluations", json={"idempotency_key": key, **over})


def bind(h, action_id: str, plan_id: str, key: str):
    return h.client.post(f"{base(action_id)}/plans/{plan_id}/later-selection", json={"idempotency_key": key})


def later_generator_off(runner, decided: str = "2026-11-02T10:00:00Z") -> None:
    """The later hour with the generator stopped (it runs 09:30-09:45, outside the window, so the UTC day is still
    assessed): zero Candidate seconds in the window (the version-1 target is met)."""
    runner.step({"do": "deliver", "decided": decided, "blocks": [
        {"from": "2026-11-02T08:00:00Z", "to": "2026-11-02T09:00:00Z", "pv": "40", "dis": "20", "soc": "80",
         "only": ["load", "pv", "dis", "soc"], "stop_before": True},
        {"from": "2026-11-02T09:30:00Z", "to": "2026-11-02T09:45:00Z", "pv": "40", "dis": "20", "soc": "80",
         "stop_before": True, "stop_after": True}]})


def late_reading(runner, decided: str, at: str = "2026-11-02T08:30:00Z", soc: str = "79") -> None:
    runner.step({"do": "deliver", "decided": decided, "blocks": [{"from": at, "to": at, "soc": soc, "only": ["soc"]}]})


def bound_plan(runner, h, *, later=later_generator_off) -> tuple[str, dict, dict]:
    action_id = applied_action(runner, h)
    plan = freeze(h, action_id).json()["plan"]
    h.clock.at = CLOSED
    later(runner)
    caught_up(runner, h, CLOSED)
    made = bind(h, action_id, plan["plan_id"], "bind-0001")
    assert made.status_code == 201, made.text
    return action_id, plan, made.json()["binding"]


def complete_windows(monkeypatch, h, *, baseline_soc: str = "50", later_soc: str = "50") -> None:
    """TEST-SCOPED: complete twelve-slot windows (labelled authored source) in place of the roles-2 Site's real,
    never-complete evidence. Currentness, plans, bindings, outcomes, events and the trial lock stay real."""
    def fake(start, readings, *, load_asset_ids, critical_load_asset_id, reserves, battery_asset_id=None,
             role_assets=None):
        soc = baseline_soc if start.date() < datetime(2026, 11, 2).date() else later_soc
        synthetic = [replace(r, id=f"test-scoped-{start:%Y%m%dT%H%M}-{i:03d}")
                     for i, r in enumerate(full_window(start, soc=soc))]
        return REAL_WINDOW_EVIDENCE(start, synthetic, load_asset_ids=["load-a", "load-b"],
                                    critical_load_asset_id="crit",
                                    reserves=[vr.ReserveValue(vr.Fraction(30), start - timedelta(days=1), None, "r")])
    monkeypatch.setattr(vr, "window_evidence", fake)
    real = verification_ports(URL)
    h.service.verification_ports = VerificationPorts(day_status=real.day_status,
                                                     provenance=lambda t, s, ids: dict(AUTHORED))


def caught_up(runner, h, after: datetime) -> None:
    """S3 reassess + S4 match after `after`, then move the Action clock past the worker's selections."""
    settle(runner, after)
    h.clock.at = max(h.clock.at, runner.now + timedelta(minutes=1))


def rows(runner, sql: str) -> list:
    with runner.engine.connect() as c:
        return list(c.execute(text(sql)))


def kinds(runner, action_id: str) -> list[str]:
    return [r.kind for r in rows(runner, f"SELECT kind FROM action_event WHERE action_id = '{action_id}' "
                                         "ORDER BY recorded_at, id")]


def proposal_of(h, day: str) -> dict:
    return h.recommendation(h.findings()[day]).json()["proposal"]


def guard_code(h, runner, proposal: dict) -> str | None:
    """What accept's guard (run under the trial lock) says for a new key on this battery now."""
    guard = ActionService._prior_guard("KOBO-001", UUID(proposal["finding_revision_id"]),
                                       type("E", (), {"available": True, "unavailable": lambda self: None})())
    try:
        guard([a for a in h.store.trial_actions(runner.tenant, runner.site, proposal["asset_id"], "reserve-trial-1")
               if a["recommendation_key"] != proposal["recommendation_key"]])
    except ActionRefused as refused:
        return refused.code
    return None


def store_accept(h, runner, proposal: dict, key: str, at: datetime):
    """Accept through the store with the real prior-trial guard (the proposal was read before F01 was applied)."""
    payload = {"command": "ACCEPT", "idempotency_key": key}
    guard = ActionService._prior_guard("KOBO-001", UUID(proposal["finding_revision_id"]),
                                       type("E", (), {"available": True, "unavailable": lambda self: None})())
    return h.store.accept(runner.tenant, runner.site, proposal, payload_sha256=sha(payload), payload=payload,
                          idempotency_key=key, fixture_id="D-action-records-v1", recorded_at=at, guard=guard)


def waiting_advisory_lock(runner, seconds: float = 4.0) -> bool:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if rows(runner, "SELECT count(*) FROM pg_locks WHERE locktype = 'advisory' AND NOT granted")[0][0]:
            return True
        time.sleep(0.05)
    return False


class TestRealRoles2Path:
    def test_pending_gates_inconclusive_outcome_retries_and_access(self, runner) -> None:
        run_case(runner, CASES["F01"])
        run_case(runner, CASES["F02"])
        h = verifying(runner)
        try:
            action_id = applied_action(runner, h)
            plan = freeze(h, action_id).json()["plan"]
            early = evaluate(h, action_id, "eval-0001")
            assert early.status_code == 200 and early.json()["state"] == "PENDING", early.text
            assert early.json()["reasons"] == ["LATER_WINDOW_OPEN"] and early.json()["outcome"] is None
            h.clock.at = CLOSED
            later_generator_off(runner)
            caught_up(runner, h, CLOSED)
            unbound = evaluate(h, action_id, "eval-0002").json()
            assert unbound["state"] == "PENDING" and unbound["reasons"] == ["LATER_SELECTION_NOT_BOUND"]
            bound = bind(h, action_id, plan["plan_id"], "bind-0001")
            assert bound.status_code == 201, bound.text

            made = evaluate(h, action_id, "eval-0003")
            assert made.status_code == 201, made.text
            outcome = made.json()["outcome"]
            assert outcome["outcome"] == "INCONCLUSIVE" and outcome["actor_id"] == "service:verification-evaluator"
            assert "INCOMPLETE_BASELINE_WINDOW" in outcome["reasons"] and "SOURCE_NOT_COHERENT" in outcome["reasons"]
            assert outcome["triggering_job"].startswith("verification-evaluation:")
            assert outcome["recorded_at"].endswith("+00:00")
            assert outcome["basis"]["later_days"][0]["day"] == "2026-11-02"
            assert outcome["basis"]["source_resolutions"]["baseline"]["state"] == "UNKNOWN"  # never their union
            assert "RESOLVED" not in kinds(runner, action_id)  # INCONCLUSIVE retains the hold
            metrics = rows(runner, f"SELECT metric_key, window_name, state FROM verification_metric "
                                   f"WHERE outcome_id = '{outcome['outcome_id']}'")
            assert ("window_coverage", "BASELINE", "UNKNOWN") in [tuple(m) for m in metrics]

            same = evaluate(h, action_id, "eval-0003")
            assert same.status_code == 200 and same.json()["replayed"] is True
            assert same.json()["outcome"]["outcome_id"] == outcome["outcome_id"]
            fresh = evaluate(h, action_id, "eval-0004")
            assert fresh.status_code == 200 and fresh.json()["outcome"]["outcome_id"] == outcome["outcome_id"]
            assert rows(runner, "SELECT count(*) FROM verification_outcome")[0][0] == 1
            read = h.client.get(f"{base(action_id)}/outcome").json()
            assert read["current_state"]["state"] == "INCONCLUSIVE" and read["is_latest_outcome"] is True
            assert {m["metric_key"] for m in read["metrics"]} >= {"target_reduction", "source_provenance"}
            assert h.recommendation(h.findings()["2026-10-08"]).json()["prior_action_block"]["code"] == \
                "PRIOR_ACTION_UNRESOLVED"
            action = h.client.get(f"/api/sites/KOBO-001/actions/{action_id}").json()
            assert action["verification"]["state"] == "INCONCLUSIVE"

            # The caller can never supply a verdict; 401/403/404.
            forged = evaluate(h, action_id, "eval-0005", outcome="VERIFIED")
            assert forged.status_code == 422
            assert evaluate(h, str(uuid4()), "eval-0006").status_code == 404
            assert h.client.get(f"{base(str(uuid4()))}/outcome").status_code == 404
            assert h.client.get(f"{base(action_id)}/outcome", params={"outcome_id": str(uuid4())}).status_code == 404
            no_verify = harness(runner)
            anon = harness(runner, command_access=lambda r, c: 401)
            try:
                assert evaluate(no_verify, action_id, "eval-0007").status_code == 403
                assert evaluate(anon, action_id, "eval-0008").status_code == 401
            finally:
                no_verify.close()
                anon.close()
        finally:
            h.close()

    def test_late_evidence_reads_reassessment_pending_then_a_settled_outcome_supersedes(self, runner) -> None:
        run_case(runner, CASES["F01"])
        h = verifying(runner)
        try:
            action_id, plan, _ = bound_plan(runner, h)
            first = evaluate(h, action_id, "eval-0001").json()["outcome"]
            h.clock.at = CLOSED + timedelta(hours=2)
            late_reading(runner, "2026-11-02T12:00:00Z")
            state = h.client.get(f"{base(action_id)}/outcome").json()["current_state"]
            assert state["state"] == "REASSESSMENT_PENDING" and state["last_outcome"] == "INCONCLUSIVE"
            assert any(r.startswith("LATE_EVIDENCE:") for r in state["reasons"])
            assert any("STALE_PROJECTION" in r for r in state["reasons"])  # the later day's S3 basis changed
            pending = evaluate(h, action_id, "eval-0002").json()
            assert pending["state"] == "REASSESSMENT_PENDING" and pending["outcome"] is None
            refused = bind(h, action_id, plan["plan_id"], "bind-0002")
            assert refused.json()["detail"]["code"] == "VERIFICATION_LATER_NOT_CURRENT"

            caught_up(runner, h, h.clock.at)
            moved = evaluate(h, action_id, "eval-0003").json()
            assert moved["state"] == "REASSESSMENT_PENDING" and "append a new later selection binding" in \
                " ".join(moved["reasons"])
            assert bind(h, action_id, plan["plan_id"], "bind-0003").status_code == 201
            second = evaluate(h, action_id, "eval-0004")
            assert second.status_code == 201, second.text
            again = second.json()["outcome"]
            assert again["supersedes_outcome_id"] == first["outcome_id"] and again["outcome"] == "INCONCLUSIVE"
            old = h.client.get(f"{base(action_id)}/outcome", params={"outcome_id": first["outcome_id"]}).json()
            assert old["is_latest_outcome"] is False and old["superseded_by_outcome_id"] == again["outcome_id"]
            assert "historical_label" in old
            history = h.client.get(f"{base(action_id)}/history").json()
            assert [o["outcome_id"] for o in history["outcomes"]] == [first["outcome_id"], again["outcome_id"]]
        finally:
            h.close()


class TestCurrentnessGates:
    def test_freeze_refuses_stale_and_failed_baseline_days(self, runner) -> None:
        from assetops_backend.analytics.adapters.postgres_assessment_store import PostgresAssessmentStore
        from assetops_backend.analytics.assessment_worker import DispatchAssessmentWorker
        from test_s1_bindings_postgres import Clock

        run_case(runner, CASES["F01"])
        h = verifying(runner)
        try:
            action_id = applied_action(runner, h)
            late_reading(runner, "2026-11-01T01:30:00Z", at="2026-10-06T08:20:00Z", soc="79")
            stale = freeze(h, action_id)
            assert stale.json()["detail"]["code"] == "VERIFICATION_BASELINE_NOT_CURRENT", stale.text
            assert "STALE_PROJECTION" in json.dumps(stale.json()["detail"]["days"])

            class Broken:
                ANALYTIC_ID, MODEL_VERSION = "dispatch", "dispatch-3"

                @staticmethod
                def assess(_inputs):
                    raise RuntimeError("model crashed")

            now = datetime(2026, 11, 1, 1, 40, tzinfo=UTC)
            for _ in range(3):
                DispatchAssessmentWorker(PostgresAssessmentStore(URL), model=Broken, clock=Clock(now),
                                         backoff=timedelta(0)).run_pending(reconcile=False)
                now += timedelta(minutes=1)
            failed = freeze(h, action_id, key="freeze-0002")
            assert failed.json()["detail"]["code"] == "VERIFICATION_BASELINE_NOT_CURRENT"
            assert '"s3_status": "FAILED"' in json.dumps(failed.json()["detail"]["days"])
            assert rows(runner, "SELECT count(*) FROM verification_plan")[0][0] == 0
        finally:
            h.close()

    def test_f1_baseline_under_an_unrelated_earlier_revision_is_not_comparable(self, runner) -> None:
        run_case(runner, CASES["F01"])
        h = verifying(runner)
        try:
            action_id, _ = accepted(h, "2026-10-06")
            # An unrelated publication after the baseline but before the trial: the change then moves R1 -> R2, so
            # the baseline's covering revision (R0) is not the revision the Action changed from.
            runner.step({"do": "runtime", "value": 45, "effective_from": "2026-10-20T00:00:00Z",
                         "decided": "2026-11-01T00:30:00Z"})
            h.clock.at = T_APPLY
            assert apply(h, action_id, current_foundation(h, action_id), "apply-0001").status_code == 201
            settle(runner, T_APPLY)
            h.clock.at = T_FREEZE
            refused = freeze(h, action_id)
            assert refused.status_code == 409, refused.text
            assert refused.json()["detail"]["code"] == "VERIFICATION_FOUNDATION_NOT_COMPARABLE"
        finally:
            h.close()


class TestCutoff:
    def test_other_role_boundary_and_unaccepted_reports(self, runner) -> None:
        run_case(runner, CASES["F01"])
        h = verifying(runner)
        try:
            action_id = applied_action(runner, h)
            first = freeze(h, action_id).json()["plan"]
            h.clock.at = T_FREEZE + timedelta(hours=1)
            # Unaccepted (held) later-window report and an accepted report just before later_start: no cutoff.
            runner.step({"do": "deliver", "decided": "2026-11-01T02:10:00Z", "blocks": [
                {"from": "2026-11-02T07:59:00Z", "to": "2026-11-02T07:59:00Z", "pv": "40", "only": ["pv"]}],
                "held": {"later": [{"from": "2026-11-02T08:10:00Z", "to": "2026-11-02T08:10:00Z", "soc": "80",
                                    "only": ["soc"]}]}})
            reuse = freeze(h, action_id, key="freeze-0002", supersedes_plan_id=first["plan_id"])
            assert reuse.status_code == 201, reuse.text
            second = reuse.json()["plan"]
            # Another role and asset, exactly at later_start: the first accepted later-window report trips it.
            runner.step({"do": "deliver", "decided": "2026-11-01T02:20:00Z", "blocks": [
                {"from": "2026-11-02T08:00:00Z", "to": "2026-11-02T08:00:00Z", "pv": "41", "only": ["pv"]}]})
            tripped = freeze(h, action_id, key="freeze-0003", supersedes_plan_id=second["plan_id"])
            assert tripped.json()["detail"]["code"] == "VERIFICATION_LATER_WINDOW_STARTED", tripped.text
            assert freeze(h, action_id, key="freeze-0002", supersedes_plan_id=first["plan_id"]).status_code == 200
        finally:
            h.close()

    def test_freeze_waits_for_an_in_flight_acceptance(self, runner) -> None:
        run_case(runner, CASES["F01"])
        h = verifying(runner)
        try:
            action_id = applied_action(runner, h)
            out: list = []
            with runner.engine.connect() as holder:
                tx = holder.begin()
                holder.execute(text("SELECT pg_advisory_xact_lock(hashtextextended(CAST(:s AS text) || ':' || "
                                    "'dispatch', 0))"), {"s": str(runner.site)})
                worker = threading.Thread(target=lambda: out.append(freeze(h, action_id).status_code))
                worker.start()
                assert waiting_advisory_lock(runner), "freeze did not wait for the S2 acceptance fence"
                assert out == []
                tx.commit()
            worker.join(10)
            assert out == [201], out
        finally:
            h.close()


class TestResolutionAndHolds:
    def test_verified_resolves_then_late_evidence_withdraws_and_overlap_blocks(self, runner, monkeypatch) -> None:
        run_case(runner, CASES["F01"])
        run_case(runner, CASES["F02"])
        h = verifying(runner)
        try:
            p2 = proposal_of(h, "2026-10-08")
            complete_windows(monkeypatch, h)
            contract: dict = {}
            action_id, plan, _ = bound_plan(runner, h)
            h.clock.at = CLOSED + timedelta(hours=1)
            made = evaluate(h, action_id, "eval-0001")
            assert made.status_code == 201, made.text
            contract["evaluate_verified"] = made.json()
            first = made.json()["outcome"]
            assert first["outcome"] == "VERIFIED" and made.json()["resolved"] is True
            assert kinds(runner, action_id)[-1] == "RESOLVED"
            assert guard_code(h, runner, p2) is None  # VERIFIED releases the ordinary hold
            contract["action_resolved"] = h.client.get(f"/api/sites/KOBO-001/actions/{action_id}").json()
            assert contract["action_resolved"]["state"]["outcome"]["state"] == "VERIFIED"
            assert contract["action_resolved"]["verification"]["state"] == "VERIFIED"
            contract["plan"] = h.client.get(f"{base(action_id)}/plan").json()
            contract["evidence"] = h.client.get(f"{base(action_id)}/evidence").json()
            contract["outcome_current"] = h.client.get(f"{base(action_id)}/outcome").json()

            # Late evidence for the later window arrives; a second Finding's trial is accepted after it, before the
            # evaluator withdraws the closure: that overlap permanently blocks the battery.
            late_reading(runner, "2026-11-02T13:00:00Z")
            contract["outcome_reassessment_pending"] = h.client.get(f"{base(action_id)}/outcome").json()
            assert contract["outcome_reassessment_pending"]["current_state"]["state"] == "REASSESSMENT_PENDING"
            _, _, replayed = store_accept(h, runner, p2, "accept-f02-late", datetime(2026, 11, 2, 13, 30, tzinfo=UTC))
            assert not replayed
            h.clock.at = datetime(2026, 11, 2, 14, 0, tzinfo=UTC)
            withdrawn = evaluate(h, action_id, "eval-0002")
            contract["evaluate_withdrawn"] = withdrawn.json()
            assert withdrawn.json()["state"] == "REASSESSMENT_PENDING" and withdrawn.json()["withdrawn"] is True
            assert kinds(runner, action_id)[-1] == "RESOLUTION_WITHDRAWN"
            [payload] = [r.payload for r in rows(runner, f"SELECT payload FROM action_event WHERE action_id = "
                                                         f"'{action_id}' AND kind = 'RESOLUTION_WITHDRAWN'")]
            assert payload["invalidating_evidence"] and payload["withdrawn_outcome"] == "VERIFIED"
            assert guard_code(h, runner, p2 | {"recommendation_key": "another-key"}) == \
                "PRIOR_TRIAL_REASSESSMENT_OVERLAP"
            contract["recommendation_overlap"] = h.recommendation(h.findings()["2026-10-06"]).json()

            # S3/S4 settle, the later selection is re-bound, and the evaluator appends a superseding outcome and a
            # new RESOLVED: the overlap block stays (no reviewer override).
            caught_up(runner, h, h.clock.at)
            assert bind(h, action_id, plan["plan_id"], "bind-0002").status_code == 201
            again = evaluate(h, action_id, "eval-0003")
            assert again.status_code == 201, again.text
            assert again.json()["outcome"]["supersedes_outcome_id"] == first["outcome_id"]
            assert kinds(runner, action_id)[-1] == "RESOLVED"
            assert guard_code(h, runner, p2 | {"recommendation_key": "another-key"}) == \
                "PRIOR_TRIAL_REASSESSMENT_OVERLAP"
            contract["evaluate_resettled"] = again.json()
            contract["history"] = h.client.get(f"{base(action_id)}/history").json()
            contract["outcome_historical"] = h.client.get(f"{base(action_id)}/outcome",
                                                          params={"outcome_id": first["outcome_id"]}).json()
            check_contract(contract)
        finally:
            h.close()

    def test_an_action_accepted_before_the_late_evidence_is_not_an_overlap(self, runner, monkeypatch) -> None:
        run_case(runner, CASES["F01"])
        run_case(runner, CASES["F02"])
        h = verifying(runner)
        try:
            p2 = proposal_of(h, "2026-10-08")
            complete_windows(monkeypatch, h)
            action_id, _, _ = bound_plan(runner, h)
            h.clock.at = CLOSED + timedelta(hours=1)
            assert evaluate(h, action_id, "eval-0001").json()["outcome"]["outcome"] == "VERIFIED"
            store_accept(h, runner, p2, "accept-f02-early", datetime(2026, 11, 2, 12, 30, tzinfo=UTC))
            late_reading(runner, "2026-11-02T13:00:00Z")
            h.clock.at = datetime(2026, 11, 2, 14, 0, tzinfo=UTC)
            assert evaluate(h, action_id, "eval-0002").json()["withdrawn"] is True
            assert guard_code(h, runner, p2 | {"recommendation_key": "another-key"}) == "PRIOR_ACTION_UNRESOLVED"
        finally:
            h.close()

    def test_guardrail_failure_closes_but_blocks_a_different_finding(self, runner, monkeypatch) -> None:
        run_case(runner, CASES["F01"])
        run_case(runner, CASES["F02"])
        h = verifying(runner)
        try:
            p2 = proposal_of(h, "2026-10-08")
            complete_windows(monkeypatch, h, baseline_soc="30", later_soc="29")
            action_id, _, _ = bound_plan(runner, h)
            made = evaluate(h, action_id, "eval-0001").json()
            outcome = made["outcome"]
            assert outcome["outcome"] == "INEFFECTIVE" and outcome["reasons"][0] == "GUARDRAIL_FAIL"
            assert made["resolved"] is True and kinds(runner, action_id)[-1] == "RESOLVED"
            assert guard_code(h, runner, p2) == "PRIOR_TRIAL_GUARDRAIL_FAILED"
            with pytest.raises(ActionRefused) as refused:
                store_accept(h, runner, p2, "accept-f02", CLOSED + timedelta(hours=1))
            assert refused.value.code == "PRIOR_TRIAL_GUARDRAIL_FAILED"
            assert refused.value.extra["blocking_outcome_id"] == outcome["outcome_id"]
            action = h.client.get(f"/api/sites/KOBO-001/actions/{action_id}").json()
            assert action["verification"]["state"] == "INEFFECTIVE"
        finally:
            h.close()

    def test_target_miss_only_releases_the_hold(self, runner, monkeypatch) -> None:
        from test_s6_verification_plan_postgres import deliver_later

        run_case(runner, CASES["F01"])
        run_case(runner, CASES["F02"])
        h = verifying(runner)
        try:
            p2 = proposal_of(h, "2026-10-08")
            complete_windows(monkeypatch, h)
            action_id, _, _ = bound_plan(runner, h, later=deliver_later)  # generator runs the whole later hour
            outcome = evaluate(h, action_id, "eval-0001").json()["outcome"]
            assert outcome["outcome"] == "INEFFECTIVE" and outcome["reasons"] == ["TARGET_MISS"], outcome
            assert guard_code(h, runner, p2) is None
        finally:
            h.close()

    def test_the_evaluator_waits_for_the_battery_trial_lock(self, runner, monkeypatch) -> None:
        run_case(runner, CASES["F01"])
        h = verifying(runner)
        try:
            complete_windows(monkeypatch, h)
            action_id, plan, _ = bound_plan(runner, h)
            out: list = []
            with runner.engine.connect() as holder:
                tx = holder.begin()
                holder.execute(text("SELECT pg_advisory_xact_lock(hashtext('action-trial:' || :t || ':' || :s || "
                                    "':' || :a || ':' || :f || ':' || :r))"),
                               {"t": str(runner.tenant), "s": str(runner.site), "a": plan["battery_asset_id"],
                                "f": "reserve-state-of-charge", "r": "reserve-trial-1"})
                worker = threading.Thread(target=lambda: out.append(evaluate(h, action_id, "eval-0001").status_code))
                worker.start()
                assert waiting_advisory_lock(runner), "the evaluator did not wait for the trial lock"
                assert rows(runner, "SELECT count(*) FROM verification_outcome")[0][0] == 0
                tx.commit()
            worker.join(15)
            assert out == [201], out
        finally:
            h.close()


def check_contract(contract: dict) -> None:
    """The versioned S6-02b API fixture: persisted responses, normalised (IDs, digests, codes)."""
    document = {"schema": "assetops.s6-verification-api-contract", "version": 1,
                "label": ("TEST-SCOPED complete windows and authored source resolution over a real roles-2 Site; "
                          "shapes and states only, never a real or simulated trial result. Simulated/authored "
                          "policy trial wording; no causal or savings claim; RESOLVED can later be withdrawn."),
                "timestamps": "ISO 8601 UTC with +00:00 (D-2026-10-16-s602a-cutoff)",
                "responses": normalise(contract)}
    stamps = [v for v in _strings(document["responses"]) if len(v) >= 19 and v[4] == "-" and v[10] == "T"]
    assert stamps and all(s.endswith("+00:00") for s in stamps), [s for s in stamps if not s.endswith("+00:00")][:5]
    if os.environ.get("ASSETOPS_WRITE_S6_VERIFICATION_CONTRACT"):
        FIXTURE.write_text(json.dumps(document, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    stored = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert _shape(stored) == _shape(json.loads(json.dumps(document, sort_keys=True)))


def _strings(value):
    if isinstance(value, dict):
        for v in value.values():
            yield from _strings(v)
    elif isinstance(value, list):
        for v in value:
            yield from _strings(v)
    elif isinstance(value, str):
        yield value


def _shape(value):
    """Keys, list lengths, states and codes; free values (times, numbers) are compared by type only."""
    if isinstance(value, dict):
        return {k: _shape(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_shape(v) for v in value]
    if isinstance(value, str) and (value.isupper() or value in ("<uuid>", "<sha256>")):
        return value
    return type(value).__name__
