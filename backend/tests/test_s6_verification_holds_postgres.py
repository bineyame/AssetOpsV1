"""S6-02a fix round 1: evaluator decisions under the trial lock (F1), INCONCLUSIVE continuation plans (F4) and the
causal invalidating-reading set behind `PRIOR_TRIAL_REASSESSMENT_OVERLAP` (F2).

`D-2026-10-16-s602a-holds`. Real PostgreSQL over the S4 F01/F02 cases (a `minigrid-roles-2` Site), with the same
labelled TEST-SCOPED complete windows as `test_s6_verification_evaluator_postgres` where a VERIFIED closure is needed.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest

from test_s4_finding_store_postgres import URL, run_case  # noqa: F401
from test_s1_bindings_postgres import engine, store  # noqa: F401
from test_s6_action_store_postgres import CASES, runner  # noqa: F401
from test_s6_verification_plan_postgres import applied_action, freeze, verifying, base
from test_s6_verification_evaluator_postgres import (
    AUTHORED,
    CLOSED,
    NEXT_LATER,
    bind,
    bound_plan,
    caught_up,
    complete_windows,
    continuation,
    evaluate,
    guard_code,
    kinds,
    late_reading,
    later_generator_off,
    proposal_of,
    rows,
    store_accept,
    withdrawal,
)

from assetops_backend.actions.verification import VerificationPorts, VerificationService

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set")

UTC = timezone.utc
OTHER = "another-key"


def _closed_verified(runner, h, monkeypatch, **kw):
    complete_windows(monkeypatch, h, **kw)
    action_id, plan, _ = bound_plan(runner, h)
    h.clock.at = CLOSED + timedelta(hours=1)
    made = evaluate(h, action_id, "eval-0001").json()
    assert made["outcome"]["outcome"] == "VERIFIED" and made["resolved"] is True, made
    return action_id, plan


class TestF1DecisionUnderTheLock:
    def test_a_stale_concurrent_evaluation_cannot_resolve_over_a_newer_inconclusive(self, runner, monkeypatch) -> None:
        """The review's interleaving: A starts at t0, B (source no longer coherent) commits INCONCLUSIVE at t1 > t0
        before A takes the lock. A must decide on what it reads under the lock, after B: no RESOLVED, hold kept."""
        run_case(runner, CASES["F01"])
        run_case(runner, CASES["F02"])
        h = verifying(runner)
        try:
            p2 = proposal_of(h, "2026-10-08")
            complete_windows(monkeypatch, h)
            action_id, _, _ = bound_plan(runner, h)
            t0, t1 = CLOSED + timedelta(hours=1), CLOSED + timedelta(hours=2)
            real, seen = h.store.record_evaluation, {}

            def interleaved(tenant, site, plan, request, compose):
                if "b" not in seen:
                    seen["b"] = None
                    h.service.verification_ports = VerificationPorts(
                        day_status=h.service.verification_ports.day_status,
                        provenance=lambda t, s, ids: {**AUTHORED, "state": "MIXED"})
                    h.clock.at = t1
                    seen["b"] = VerificationService(h.service).evaluate(
                        runner.tenant, runner.site, "KOBO-001", UUID(action_id), {"idempotency_key": "eval-0000b"})
                    h.clock.at = t0  # A resumes with its earlier clock reading
                return real(tenant, site, plan, request, compose)

            monkeypatch.setattr(h.store, "record_evaluation", interleaved)
            h.clock.at = t0
            a = evaluate(h, action_id, "eval-0000a")
            assert a.status_code in (200, 201), a.text
            status_b, body_b = seen["b"]
            assert status_b == 201 and body_b["outcome"]["outcome"] == "INCONCLUSIVE"
            assert a.json()["outcome"]["outcome"] == "INCONCLUSIVE" and a.json()["resolved"] is False
            assert a.json()["outcome"]["outcome_id"] == body_b["outcome"]["outcome_id"]  # same basis: reused
            assert "RESOLVED" not in kinds(runner, action_id)
            state = h.client.get(f"{base(action_id)}/outcome").json()["current_state"]
            assert state["state"] == "INCONCLUSIVE"
            assert guard_code(h, runner, p2) == "PRIOR_ACTION_UNRESOLVED"  # the hold stays
            stamps = rows(runner, f"SELECT recorded_at FROM verification_outcome WHERE action_id = '{action_id}' "
                                  "ORDER BY recorded_at, id")
            assert len(stamps) == 1
        finally:
            h.close()


class TestF4InconclusiveContinuation:
    def test_settled_inconclusive_and_pending_plans_continue_with_history_and_hold(self, runner) -> None:
        run_case(runner, CASES["F01"])
        run_case(runner, CASES["F02"])
        h = verifying(runner)
        try:
            p2 = proposal_of(h, "2026-10-08")
            action_id = applied_action(runner, h)
            plan = freeze(h, action_id).json()["plan"]
            h.clock.at = CLOSED
            later_generator_off(runner)
            caught_up(runner, h, CLOSED)
            assert bind(h, action_id, plan["plan_id"], "bind-0001").status_code == 201
            first = evaluate(h, action_id, "eval-0001").json()["outcome"]
            assert first["outcome"] == "INCONCLUSIVE"

            # Late evidence makes the INCONCLUSIVE read REASSESSMENT_PENDING: no continuation until it is reassessed.
            h.clock.at = CLOSED + timedelta(hours=2)
            late_reading(runner, "2026-11-02T12:00:00Z")
            assert continuation(h, action_id, plan)["reason"] == "REASSESSMENT_PENDING"
            caught_up(runner, h, h.clock.at)
            assert bind(h, action_id, plan["plan_id"], "bind-0002").status_code == 201
            first = evaluate(h, action_id, "eval-0001b").json()["outcome"]
            assert first["outcome"] == "INCONCLUSIVE"

            # After the later-run cutoff the same later window cannot be reused.
            same = freeze(h, action_id, key="freeze-0002", supersedes_plan_id=plan["plan_id"])
            assert same.json()["detail"]["code"] == "VERIFICATION_LATER_WINDOW_STARTED", same.text
            assert same.json()["detail"]["reason"] == "NOT_AFTER_PRIOR_LATER_WINDOW"
            made = freeze(h, action_id, key="freeze-0003", supersedes_plan_id=plan["plan_id"], later_start=NEXT_LATER)
            assert made.status_code == 201, made.text
            second = made.json()["plan"]
            assert second["supersedes_plan_id"] == plan["plan_id"] and second["plan_id"] != plan["plan_id"]
            assert second["baseline_start"] == plan["baseline_start"]  # baseline reused: still current

            # Idempotency: identical retries keep their IDs; a new key cannot replace silently.
            again = freeze(h, action_id)
            assert again.status_code == 200 and again.json()["plan"]["plan_id"] == plan["plan_id"]
            retry = freeze(h, action_id, key="freeze-0003", supersedes_plan_id=plan["plan_id"], later_start=NEXT_LATER)
            assert retry.status_code == 200 and retry.json()["plan"]["plan_id"] == second["plan_id"]
            for over in ({}, {"supersedes_plan_id": plan["plan_id"]}):
                stray = freeze(h, action_id, key="freeze-0004", later_start=NEXT_LATER, **over)
                assert stray.json()["detail"]["code"] == "VERIFICATION_PLAN_NOT_HEAD", stray.text

            # History retained; the Action stays unresolved and the battery hold is unchanged.
            history = h.client.get(f"{base(action_id)}/history").json()
            assert [p["plan_id"] for p in history["plans"]] == [plan["plan_id"], second["plan_id"]]
            assert [o["outcome_id"] for o in history["outcomes"]][-1] == first["outcome_id"]
            assert history["current_state"]["state"] == "PENDING"
            assert history["current_state"]["plan_id"] == second["plan_id"]
            old = h.client.get(f"{base(action_id)}/outcome", params={"outcome_id": first["outcome_id"]}).json()
            assert old["outcome"]["outcome"] == "INCONCLUSIVE"
            assert "RESOLVED" not in kinds(runner, action_id)
            assert guard_code(h, runner, p2) == "PRIOR_ACTION_UNRESOLVED"
            pending = evaluate(h, action_id, "eval-0002").json()
            assert pending["state"] == "PENDING" and pending["reasons"] == ["LATER_WINDOW_OPEN"]

            # A pending (no outcome) plan may be superseded before its own cutoff with the same bounds.
            third = freeze(h, action_id, key="freeze-0005", supersedes_plan_id=second["plan_id"],
                           later_start=NEXT_LATER)
            assert third.status_code == 201, third.text
            assert third.json()["plan"]["supersedes_plan_id"] == second["plan_id"]
            assert rows(runner, "SELECT count(*) FROM verification_outcome")[0][0] == 2
        finally:
            h.close()


class TestF2CausalAttribution:
    def test_bound_reading_with_undetermined_effect_is_an_ordinary_hold(self, runner, monkeypatch) -> None:
        """A bound late reading that leaves the window's result unchanged while its S3 day is pending: the
        attribution is INDETERMINATE, so an Action accepted after it and before the withdrawal is no overlap."""
        run_case(runner, CASES["F01"])
        run_case(runner, CASES["F02"])
        h = verifying(runner)
        try:
            p2 = proposal_of(h, "2026-10-08")
            action_id, _ = _closed_verified(runner, h, monkeypatch)  # nothing injected: the window cannot move
            late = late_reading(runner, "2026-11-02T13:00:00Z")
            store_accept(h, runner, p2, "accept-f02-late", datetime(2026, 11, 2, 13, 30, tzinfo=UTC))
            h.clock.at = datetime(2026, 11, 2, 14, 0, tzinfo=UTC)
            assert evaluate(h, action_id, "eval-0002").json()["withdrawn"] is True
            payload = withdrawal(runner, action_id)
            assert payload["attribution"] == "INDETERMINATE" and payload["invalidating_evidence"] == []
            assert payload["candidate_evidence_ids"] == late
            assert guard_code(h, runner, p2 | {"recommendation_key": OTHER}) == "PRIOR_ACTION_UNRESOLVED"
        finally:
            h.close()

    def test_unbound_asset_and_unrelated_role_reports_are_never_candidates(self, runner, monkeypatch) -> None:
        """TEST-SCOPED: the roles-2 Lab cannot emit an accepted reading for an unbound asset or an unbound role, so
        the late row is reported as such; it is never a candidate (NONE), unlike a bound one (INDETERMINATE)."""
        run_case(runner, CASES["F01"])
        run_case(runner, CASES["F02"])
        h = verifying(runner)
        try:
            p2 = proposal_of(h, "2026-10-08")
            action_id, _ = _closed_verified(runner, h, monkeypatch)
            real = h.store.late_evidence

            def unbound(*args, **kwargs):
                out = []
                for row in real(*args, **kwargs):
                    out += [{**row, "asset_id": uuid4()},
                            {**row, "id": uuid4(), "role": "critical_load_requested_power"}]
                return out

            monkeypatch.setattr(h.store, "late_evidence", unbound)
            late_reading(runner, "2026-11-02T13:00:00Z")
            store_accept(h, runner, p2, "accept-f02-late", datetime(2026, 11, 2, 13, 30, tzinfo=UTC))
            h.clock.at = datetime(2026, 11, 2, 14, 0, tzinfo=UTC)
            assert evaluate(h, action_id, "eval-0002").json()["withdrawn"] is True
            payload = withdrawal(runner, action_id)
            assert payload["attribution"] == "NONE" and payload["candidate_evidence_ids"] == []
            assert guard_code(h, runner, p2 | {"recommendation_key": OTHER}) == "PRIOR_ACTION_UNRESOLVED"
        finally:
            h.close()

    def test_foundation_and_source_only_withdrawals_have_no_invalidating_readings(self, runner, monkeypatch) -> None:
        run_case(runner, CASES["F01"])
        run_case(runner, CASES["F02"])
        h = verifying(runner)
        try:
            p2 = proposal_of(h, "2026-10-08")
            action_id, _ = _closed_verified(runner, h, monkeypatch)
            # Source reclassification only: the settled re-evaluation withdraws on a changed basis.
            h.service.verification_ports = VerificationPorts(
                day_status=h.service.verification_ports.day_status,
                provenance=lambda t, s, ids: {**AUTHORED, "state": "MIXED"})
            store_accept(h, runner, p2, "accept-f02-mid", CLOSED + timedelta(hours=1, minutes=30))
            h.clock.at = CLOSED + timedelta(hours=2)
            source = evaluate(h, action_id, "eval-0002").json()
            assert source["withdrawn"] is True and source["outcome"]["outcome"] == "INCONCLUSIVE"
            payload = withdrawal(runner, action_id)
            assert payload["reason"] == "BASIS_CHANGED"
            assert payload["attribution"] == "NONE" and payload["invalidating_evidence"] == []
            assert guard_code(h, runner, p2 | {"recommendation_key": OTHER}) == "PRIOR_ACTION_UNRESOLVED"

            # Back to a coherent source: VERIFIED again, then a Foundation publication inside the later window.
            complete_windows(monkeypatch, h)
            h.clock.at = CLOSED + timedelta(hours=3)
            assert evaluate(h, action_id, "eval-0003").json()["resolved"] is True
            runner.step({"do": "runtime", "value": 45, "effective_from": "2026-11-02T08:30:00Z",
                         "decided": "2026-11-02T14:10:00Z"})
            h.clock.at = datetime(2026, 11, 2, 15, 0, tzinfo=UTC)
            assert evaluate(h, action_id, "eval-0004").json()["withdrawn"] is True
            payload = withdrawal(runner, action_id)
            assert payload["attribution"] == "NONE" and payload["invalidating_evidence"] == []
            assert guard_code(h, runner, p2 | {"recommendation_key": OTHER}) == "PRIOR_ACTION_UNRESOLVED"
        finally:
            h.close()

    @pytest.mark.parametrize("accepted_after_conflict", [False, True], ids=["action-before-conflict", "control"])
    def test_a_duplicate_reading_never_moves_the_overlap_boundary(self, runner, monkeypatch,
                                                                  accepted_after_conflict) -> None:
        """Fix round 2 (re-review R1): VERIFIED and RESOLVED at 12:00; a bound SOC reading identical to the pinned
        sample accepted at 12:15; a conflicting one at 13:00; evaluation at 14:00. Only the conflicting reading is
        causal, so another Finding's Action accepted at 12:30 keeps the ordinary hold, while the control Action
        accepted after the conflicting reading is a permanent overlap."""
        run_case(runner, CASES["F01"])
        run_case(runner, CASES["F02"])
        h = verifying(runner)
        try:
            p2 = proposal_of(h, "2026-10-08")
            inject: set = set()
            action_id, _ = _closed_verified(runner, h, monkeypatch, inject=inject)
            duplicate = late_reading(runner, "2026-11-02T12:15:00Z", soc="50")
            inject.update(duplicate)
            if not accepted_after_conflict:
                store_accept(h, runner, p2, "accept-f02-mid", datetime(2026, 11, 2, 12, 30, tzinfo=UTC))
            conflict = late_reading(runner, "2026-11-02T13:00:00Z", soc="79")
            inject.update(conflict)
            if accepted_after_conflict:
                store_accept(h, runner, p2, "accept-f02-late", datetime(2026, 11, 2, 13, 30, tzinfo=UTC))
            h.clock.at = datetime(2026, 11, 2, 14, 0, tzinfo=UTC)
            assert evaluate(h, action_id, "eval-0002").json()["withdrawn"] is True
            payload = withdrawal(runner, action_id)
            assert payload["attribution"] == "CAUSAL"
            assert [e["id"] for e in payload["invalidating_evidence"]] == conflict  # never the duplicate
            assert payload["candidate_evidence_ids"] == sorted(duplicate + conflict)
            expected = "PRIOR_TRIAL_REASSESSMENT_OVERLAP" if accepted_after_conflict else "PRIOR_ACTION_UNRESOLVED"
            assert guard_code(h, runner, p2 | {"recommendation_key": OTHER}) == expected
        finally:
            h.close()
