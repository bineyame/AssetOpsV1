"""S6-02a phase 1: frozen `reserve-trial-verification-1` plans, later selection binding and exact plan/evidence reads.

`D-2026-10-16-s6-verification`, `D-2026-10-16-s602-questions`. Real PostgreSQL: the S4 F01/F02 cases persist
Findings, S6-01 accepts and applies the reserve trial (effective 2026-11-02T00:00Z), then a SYSTEM demonstration
VERIFY command freezes the plan. Also the battery-scoped trial lock: two Findings on one battery race to accept.
"""

from __future__ import annotations

import threading
import time
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from test_s4_finding_store_postgres import URL, CaseRunner, run_case  # noqa: F401
from test_s1_bindings_postgres import engine, store  # noqa: F401
from test_s6_action_store_postgres import CASES, T_ACCEPT, fixture_grants, harness, runner  # noqa: F401
from test_s6_action_apply_postgres import T_APPLY, accepted, applying, apply, current_foundation

from assetops_backend.actions.capability import from_grants
from assetops_backend.actions.ports import ActionRefused
from assetops_backend.actions.reserve_trial import sha
from assetops_backend.actions.service import ActionService

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set")

COMMANDS = ["ACCEPT", "APPLY", "OBSERVE", "VERIFY"]
BASELINE = "2026-10-06T08:00:00+00:00"   # F01's Candidate interval 08:00-09:00 on the old Foundation
LATER = "2026-11-02T08:00:00+00:00"      # same UTC clock hour, after effective_from 2026-11-02T00:00Z
T_FREEZE = datetime(2026, 11, 1, 2, 0, tzinfo=timezone.utc)


def verifying(runner):
    return applying(runner, capability=from_grants(fixture_grants(runner, commands=COMMANDS)))


def applied_action(runner, h) -> str:
    action_id, _ = accepted(h, "2026-10-06")
    h.clock.at = T_APPLY
    made = apply(h, action_id, current_foundation(h, action_id), "apply-0001")
    assert made.status_code == 201, made.text
    h.clock.at = T_FREEZE
    return action_id


def base(action_id: str) -> str:
    return f"/api/sites/KOBO-001/actions/{action_id}/verification"


def freeze(h, action_id: str, key: str = "freeze-0001", **over):
    body = {"baseline_start": BASELINE, "later_start": LATER, "idempotency_key": key, **over}
    return h.client.post(f"{base(action_id)}/plans", json=body)


def deliver_later(runner, day: str = "2026-11-02", decided: str = "2026-11-02T10:00:00Z") -> None:
    runner.step({"do": "deliver", "decided": decided, "blocks": [
        {"from": f"{day}T08:00:00Z", "to": f"{day}T09:00:00Z", "pv": "40", "dis": "20", "soc": "80",
         "stop_before": True, "stop_after": True}]})


def at(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def plan_rows(runner) -> int:
    with runner.engine.connect() as c:
        return c.execute(text("SELECT count(*) FROM verification_plan")).scalar_one()


class TestFreeze:
    def test_freeze_pins_basis_replays_and_refuses_changed_retry(self, runner) -> None:
        run_case(runner, CASES["F01"])
        h = verifying(runner)
        try:
            action_id = applied_action(runner, h)
            made = freeze(h, action_id)
            assert made.status_code == 201, made.text
            plan = made.json()["plan"]
            assert "no causal or savings claim" in made.json()["label"]
            assert plan["plan_version"] == "reserve-trial-verification-1" and plan["supersedes_plan_id"] is None
            assert plan["baseline_start"] == BASELINE and plan["baseline_end"] == "2026-10-06T09:00:00+00:00"
            assert plan["later_start"] == LATER and plan["effective_from"] == "2026-11-02T00:00:00+00:00"
            assert plan["baseline_candidate_seconds"] > 0
            assert plan["old_foundation_revision_id"] != plan["new_foundation_revision_id"]
            assert plan["bands"]["feeder_demand_energy_relative"] in ("0.1", "1/10")
            assert plan["bands"]["initial_soc_points"] == "2"
            assert plan["target"]["rule"] == "4 * later_seconds <= 3 * baseline_seconds"
            assert plan["guardrails"]["below_reserve_seconds"]["basis"] == "FIVE_MINUTE_SAMPLED"
            days = plan["baseline_selection"]["days"]
            assert [d["day"] for d in days] == ["2026-10-06"] and days[0]["interval_revision_ids"]
            assert plan["baseline_selection"]["target"]["state"] == "KNOWN"
            assert plan["baseline_evidence_ids"]
            assert plan["actor"]["triggering"]["command"] == "VERIFY" and plan["actor"]["kind"] == "SYSTEM"
            with runner.engine.connect() as c:
                change = c.execute(text("SELECT new_foundation_revision_id, applied_event_id FROM "
                                        "action_policy_change WHERE action_id = :a"), {"a": action_id}).one()
            assert plan["new_foundation_revision_id"] == str(change.new_foundation_revision_id)
            assert plan["applied_event_id"] == str(change.applied_event_id)

            again = freeze(h, action_id)
            assert again.status_code == 200 and again.json()["replayed"] is True
            assert again.json()["plan"]["plan_id"] == plan["plan_id"]
            clash = freeze(h, action_id, later_start="2026-11-03T08:00:00+00:00")
            assert clash.status_code == 409 and clash.json()["detail"]["code"] == "VERIFICATION_IDEMPOTENCY_CONFLICT"
            second = freeze(h, action_id, key="freeze-0002")
            assert second.status_code == 409 and second.json()["detail"]["code"] == "VERIFICATION_PLAN_NOT_HEAD"
            assert plan_rows(runner) == 1

            # Insert-only, Same-Site FK and window CHECKs hold in the database itself.
            for sql in ("UPDATE verification_plan SET later_start = later_start + interval '1 day'",
                        "DELETE FROM verification_plan"):
                with pytest.raises(DBAPIError), runner.engine.begin() as c:
                    c.execute(text(sql))
            with pytest.raises(DBAPIError, match="verification_plan_baseline_window"), runner.engine.begin() as c:
                c.execute(text(
                    "INSERT INTO verification_plan SELECT (SELECT gen_random_uuid()), tenant_id, site_id, action_id, "
                    "plan_version, id, origin_finding_revision_id, applied_event_id, change_id, "
                    "old_foundation_revision_id, new_foundation_revision_id, battery_asset_id, field, rule_id, "
                    "effective_from, baseline_start + interval '2 minutes', baseline_end + interval '2 minutes', "
                    "later_start, later_end, baseline_candidate_seconds, baseline_selection, baseline_evidence_ids, "
                    "basis, target, guardrails, bands, coverage, later_selection_rule, plan_sha256, actor_kind, "
                    "actor_id, source_channel, authorization_basis, triggering_service, triggering_fixture, "
                    "'raw-insert-01', payload, payload_sha256, recorded_at FROM verification_plan"))
        finally:
            h.close()

    def test_preconditions_and_window_rules(self, runner) -> None:
        run_case(runner, CASES["F01"])
        h = verifying(runner)
        try:
            action_id, _ = accepted(h, "2026-10-06")
            pending = freeze(h, action_id)
            assert pending.status_code == 409 and pending.json()["detail"]["code"] == "VERIFICATION_ACTION_NOT_APPLIED"
            h.clock.at = T_APPLY
            assert apply(h, action_id, current_foundation(h, action_id), "apply-0001").status_code == 201
            h.clock.at = T_FREEZE
            cases = {
                "VERIFICATION_WINDOW_INVALID": {"baseline_start": "2026-10-06T08:02:00+00:00",
                                                "later_start": "2026-11-02T08:02:00+00:00"},
                "VERIFICATION_WINDOW_CLOCK_MISMATCH": {"later_start": "2026-11-02T09:00:00+00:00"},
                "VERIFICATION_WINDOW_STRADDLES_CHANGE": {"baseline_start": "2026-11-01T23:30:00+00:00",
                                                         "later_start": "2026-11-02T23:30:00+00:00"},
                "VERIFICATION_BASELINE_UNSUPPORTED": {"baseline_start": "2026-10-06T14:00:00+00:00",
                                                      "later_start": "2026-11-02T14:00:00+00:00"},
                "VERIFICATION_BASELINE_NOT_SELECTED": {"baseline_start": "2026-10-20T08:00:00+00:00",
                                                       "later_start": "2026-11-02T08:00:00+00:00"},
            }
            for i, (code, over) in enumerate(cases.items()):
                got = freeze(h, action_id, key=f"freeze-bad-{i:02d}", **over)
                assert got.status_code in (409, 422) and got.json()["detail"]["code"] == code, (code, got.text)
            assert plan_rows(runner) == 0
            later_than_before = freeze(h, action_id, later_start="2026-11-01T08:00:00+00:00", key="freeze-early-1")
            assert later_than_before.json()["detail"]["code"] == "VERIFICATION_WINDOW_STRADDLES_CHANGE"
        finally:
            h.close()


class TestReplacementCutoff:
    def test_replace_before_later_evidence_then_new_window_after_it(self, runner) -> None:
        run_case(runner, CASES["F01"])
        h = verifying(runner)
        try:
            action_id = applied_action(runner, h)
            first = freeze(h, action_id).json()["plan"]
            # Before any later report: a replacement may reuse the same bounds, with a new immutable ID.
            h.clock.at = T_FREEZE + timedelta(minutes=5)
            replaced = freeze(h, action_id, key="freeze-0002", supersedes_plan_id=first["plan_id"])
            assert replaced.status_code == 201, replaced.text
            second = replaced.json()["plan"]
            assert second["plan_id"] != first["plan_id"] and second["supersedes_plan_id"] == first["plan_id"]
            assert (second["baseline_start"], second["later_start"]) == (first["baseline_start"], first["later_start"])
            stale = freeze(h, action_id, key="freeze-0003", supersedes_plan_id=first["plan_id"])
            assert stale.status_code == 409 and stale.json()["detail"]["code"] == "VERIFICATION_PLAN_NOT_HEAD"

            # A later-window report is accepted: reusing the later bounds is refused, the original retry still
            # returns its ID, and a new later window gets a new plan.
            h.clock.at = datetime(2026, 11, 2, 11, 0, tzinfo=timezone.utc)
            deliver_later(runner)
            reuse = freeze(h, action_id, key="freeze-0004", supersedes_plan_id=second["plan_id"])
            assert reuse.status_code == 409 and reuse.json()["detail"]["code"] == "VERIFICATION_LATER_WINDOW_STARTED"
            retry = freeze(h, action_id)
            assert retry.status_code == 200 and retry.json()["plan"]["plan_id"] == first["plan_id"]
            moved = freeze(h, action_id, key="freeze-0005", supersedes_plan_id=second["plan_id"],
                           later_start="2026-11-03T08:00:00+00:00")
            assert moved.status_code == 201, moved.text
            third = moved.json()["plan"]
            assert third["supersedes_plan_id"] == second["plan_id"] and third["later_start"].startswith("2026-11-03")

            # Exact reads: default is the current plan; superseded plans stay addressable; cutoff selects history.
            current = h.client.get(f"{base(action_id)}/plan").json()
            assert current["plan"]["plan_id"] == third["plan_id"] and current["is_current_plan"] is True
            assert [p["plan_id"] for p in current["history"]] == [first["plan_id"], second["plan_id"], third["plan_id"]]
            assert current["verification_state"]["state"] == "PENDING"
            old = h.client.get(f"{base(action_id)}/plan", params={"plan_id": first["plan_id"]}).json()
            assert old["is_current_plan"] is False and old["superseded_by_plan_id"] == second["plan_id"]
            cut = h.client.get(f"{base(action_id)}/plan", params={"recorded_at": T_FREEZE.isoformat()}).json()
            assert cut["plan"]["plan_id"] == first["plan_id"]
            conflict = h.client.get(f"{base(action_id)}/plan", params={"plan_id": first["plan_id"],
                                                                        "recorded_at": T_FREEZE.isoformat()})
            assert conflict.status_code == 422
            assert conflict.json()["detail"]["code"] == "VERIFICATION_SELECTOR_CONFLICT"
            missing = h.client.get(f"{base(action_id)}/plan", params={"plan_id": str(uuid4())})
            assert missing.status_code == 404
            assert h.client.get(f"/api/sites/KOBO-001/actions/{uuid4()}/verification/plan").status_code == 404
        finally:
            h.close()


class TestEvidenceAndSelection:
    def test_evidence_read_twelve_slots_and_later_selection_binding(self, runner) -> None:
        run_case(runner, CASES["F01"])
        h = verifying(runner)
        try:
            action_id = applied_action(runner, h)
            plan = freeze(h, action_id).json()["plan"]
            read = h.client.get(f"{base(action_id)}/evidence").json()
            assert read["plan_id"] == plan["plan_id"] and read["verification_state"]["state"] == "PENDING"
            baseline, later = read["windows"]["baseline"], read["windows"]["later"]
            assert len(baseline["slots"]) == 12 and len(later["slots"]) == 12
            assert at(baseline["slots"][0]["slot_start"]) == at(BASELINE)
            assert at(baseline["slots"][-1]["slot_end"]) == at("2026-10-06T09:00:00+00:00")
            assert baseline["guardrail_basis"] == "FIVE_MINUTE_SAMPLED"
            # The S4 case Site binds roles-2 only: no critical-load binding, so the window is never complete.
            assert baseline["complete"] is False and later["complete"] is False
            assert read["comparability"]["state"] == "UNKNOWN"
            assert read["target"]["baseline"]["candidate_seconds"] == plan["baseline_candidate_seconds"]
            assert read["target"]["later"]["state"] == "NOT_BOUND" and read["target"]["met"] is None

            bind = f"{base(action_id)}/plans/{plan['plan_id']}/later-selection"
            early = h.client.post(bind, json={"idempotency_key": "bind-0001"})
            assert early.status_code == 409 and early.json()["detail"]["code"] == "VERIFICATION_LATER_NOT_SELECTED"
            h.clock.at = datetime(2026, 11, 2, 11, 0, tzinfo=timezone.utc)
            deliver_later(runner)
            runner.step({"do": "assess"})
            made = h.client.post(bind, json={"idempotency_key": "bind-0002"})
            assert made.status_code == 201, made.text
            binding = made.json()["binding"]
            assert binding["window_name"] == "LATER" and binding["selection"]["days"][0]["day"] == "2026-11-02"
            again = h.client.post(bind, json={"idempotency_key": "bind-0003"})
            assert again.status_code == 200 and again.json()["binding"]["id"] == binding["id"]
            after = h.client.get(f"{base(action_id)}/evidence").json()
            assert after["target"]["later_selection_binding_id"] == binding["id"]
            assert after["windows"]["later"]["evidence_ids"]
            before = h.client.get(f"{base(action_id)}/evidence", params={"recorded_at": T_FREEZE.isoformat()}).json()
            assert before["windows"]["later"]["evidence_ids"] == [] and before["target"]["later"]["state"] == "NOT_BOUND"
        finally:
            h.close()


class TestBatteryScopedLock:
    def test_two_findings_on_one_battery_race_to_one_unresolved_trial(self, runner) -> None:
        run_case(runner, CASES["F01"])
        run_case(runner, CASES["F02"])
        h = harness(runner)
        try:
            ids = h.findings()
            p1 = h.recommendation(ids["2026-10-06"]).json()["proposal"]
            p2 = h.recommendation(ids["2026-10-08"]).json()["proposal"]
            assert p1["asset_id"] == p2["asset_id"] and p1["finding_id"] != p2["finding_id"]
            out: list = []
            gate = threading.Barrier(2)

            def go(proposal: dict, key: str) -> None:
                strict = ActionService._prior_guard("KOBO-001", UUID(proposal["finding_revision_id"]),
                                                    type("E", (), {"available": True,
                                                                   "unavailable": lambda self: None})())

                def slow(prior: list) -> None:
                    strict(prior)
                    time.sleep(1.0)  # hold the transaction after the check, before the insert

                payload = {"command": "ACCEPT", "idempotency_key": key}
                gate.wait()
                try:
                    h.store.accept(runner.tenant, runner.site, proposal, payload_sha256=sha(payload), payload=payload,
                                   idempotency_key=key, fixture_id="race", recorded_at=T_ACCEPT, guard=slow)
                    out.append(("created", None))
                except ActionRefused as refused:
                    out.append((refused.code, refused.extra.get("blocking_action_id")))
                except Exception as error:  # noqa: BLE001 - surfaced by the assertion below
                    out.append(("error", repr(error)))

            threads = [threading.Thread(target=go, args=a) for a in ((p1, "race-battery-01"), (p2, "race-battery-02"))]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            assert sorted(o[0] for o in out) == ["PRIOR_ACTION_UNRESOLVED", "created"], out
            assert h.counts()["action"] == 1
        finally:
            h.close()
