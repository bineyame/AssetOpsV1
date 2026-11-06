"""CH-9b3 L0 (CH9b3-R Q1-Q4, Q7): the pure `midday-productive-shift-1` verdict, its stored rows and its read wire.

VERIFIED / INEFFECTIVE TARGET_MISS / not judged (SHORT, later window open) / INCONCLUSIVE LATER_SHORT /
INCONCLUSIVE BASELINE_ZERO, all in Decimal and integers (the 10% boundary is exact, never a float)."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

from assetops_backend.actions import verification_families as vf

EFF = date(2026, 10, 20)
NOW = datetime(2026, 11, 6, 12, tzinfo=timezone.utc)
BASE = [EFF - timedelta(days=b) for b in (3, 2, 1)]


def row(day: date, kwh: str | None = "10", grade: str = "COMPLETE", subject: str = "asset:mill"):
    return SimpleNamespace(local_day=day, grade=grade, subject_ref=subject, measure=vf.MEASURE,
                           value=None if kwh is None else {"kwh": kwh}, revision=1, input_fp=f"fp-{day}-{subject}")


def plan(state: str = "COMPLETE", days: list[date] = BASE) -> dict:
    return {"id": uuid4(), "domain_action_id": uuid4(), "plan_sha256": "a" * 64,
            "baseline_selection": {"state": state, "found": len(days), "days": [d.isoformat() for d in days],
                                   "pins": []},
            "basis": {"effective_day": EFF.isoformat(), "timezone": "Africa/Nairobi"},
            "later_selection_rule": {"candidates": {"from": (EFF + timedelta(days=1)).isoformat(),
                                                    "to": (EFF + timedelta(days=14)).isoformat()}}}


def later(*offsets: int, kwh: str = "11") -> list:
    return [row(EFF + timedelta(days=o), kwh) for o in offsets]


def baseline(kwh: str = "10") -> list:
    return [row(d, kwh) for d in BASE]


TODAY = EFF + timedelta(days=6)


def test_verified_at_exactly_ten_percent_is_exact_decimal() -> None:
    # 10*mean(later) >= 11*mean(baseline): 11.0 vs 10.0 is the boundary, met exactly (no float rounding).
    out = vf.assess(plan(), baseline("10.0") + later(1, 2, 4, kwh="11.0") + [row(EFF, "999")], TODAY)
    assert out["decided"] and out["outcome"] == "VERIFIED" and out["reasons"] == ["TARGET_MET"]
    assert out["later_days"] == [EFF + timedelta(days=o) for o in (1, 2, 4)]  # the effective day is not used
    assert out["sentence"] == "Midday use rose by at least the declared 10% on fully checked days"
    assert out["line"] == "Midday use before and after the change: 10.00 → 11.00 kWh a day on 3 fully checked days each"


def test_just_under_ten_percent_is_ineffective_target_miss() -> None:
    out = vf.assess(plan(), baseline("10") + later(1, 2, 3, kwh="10.999"), TODAY)
    assert out["outcome"] == "INEFFECTIVE" and out["reasons"] == ["TARGET_MISS"] and out["sentence"] is None
    assert out["baseline_mean"] == "10.00" and out["later_mean"] == "11.00" and out["threshold"] == "11.00"


def test_day_value_is_the_sum_of_the_days_subject_rows() -> None:
    rows = baseline("5") + [row(d, "5", subject="asset:pump") for d in BASE] + later(1, 2, 3, kwh="11")
    out = vf.assess(plan(), rows, TODAY)
    assert out["baseline_mean"] == "10.00" and out["outcome"] == "VERIFIED"


def test_short_baseline_is_not_judged_with_the_frozen_text() -> None:
    p = plan("SHORT", BASE[:2])
    out = vf.assess(p, [row(d) for d in BASE[:2]] + later(1, 2, 3), TODAY)
    assert not out["decided"] and out["outcome"] is None
    assert out["not_judged_text"] == "Not judged yet: only 2 of 3 fully checked days before the change"


def test_a_frozen_baseline_day_no_longer_complete_is_not_judged() -> None:
    rows = [row(BASE[0], grade="PARTIAL"), row(BASE[1]), row(BASE[2])] + later(1, 2, 3)
    out = vf.assess(plan(), rows, TODAY)
    assert not out["decided"]
    assert out["not_judged_text"] == "Not judged yet: only 2 of 3 fully checked days before the change"


def test_later_window_open_with_fewer_than_three_days_is_not_judged() -> None:
    rows = baseline() + later(1, 3) + [row(EFF + timedelta(days=2), grade="LOW")]
    out = vf.assess(plan(), rows, EFF + timedelta(days=14))  # day +14 has not ended: the look-ahead is open
    assert not out["decided"] and not out["look_ahead_closed"]
    assert out["not_judged_text"] == "Not judged yet: only 2 of 3 fully checked days after the change"


def test_a_day_not_yet_ended_never_counts() -> None:
    out = vf.assess(plan(), baseline() + later(1, 2, 3), EFF + timedelta(days=3))
    assert not out["decided"] and out["later_days"] == [EFF + timedelta(days=1), EFF + timedelta(days=2)]


def test_look_ahead_closed_with_fewer_than_three_days_is_inconclusive_later_short() -> None:
    rows = baseline() + later(1, 9) + later(15, 16)  # +15, +16 are outside the 14-day look-ahead
    out = vf.assess(plan(), rows, EFF + timedelta(days=15))
    assert out["decided"] and out["outcome"] == "INCONCLUSIVE" and out["reasons"] == ["LATER_SHORT"]
    assert out["line"].startswith("Only 2 of 3 fully checked days after the change in the 14 days allowed")


def test_zero_baseline_is_inconclusive_baseline_zero_even_when_later_is_zero() -> None:
    for later_kwh in ("0", "4"):
        out = vf.assess(plan(), baseline("0") + later(1, 2, 3, kwh=later_kwh), TODAY)
        assert out["outcome"] == "INCONCLUSIVE" and out["reasons"] == ["BASELINE_ZERO"]
        assert out["sentence"] == "No midday use was measured before the change, so a 10% rise cannot be measured"


def test_a_complete_row_without_a_kwh_value_does_not_count() -> None:
    rows = baseline() + later(1, 2) + [row(EFF + timedelta(days=3), None)]
    assert not vf.assess(plan(), rows, TODAY)["decided"]


def test_outcome_rows_name_the_domain_action_and_three_metric_windows() -> None:
    p = plan()
    result = {**vf.assess(p, baseline() + later(1, 2, 3, kwh="12"), TODAY), "pins": [], "today": TODAY,
              "known_at": NOW}
    outcome, metrics = vf.outcome_rows(p, result, NOW)
    assert outcome["domain_action_id"] == p["domain_action_id"] and "action_id" not in outcome
    assert outcome["evaluation_request_id"] is None and outcome["idempotency_key"] == f"midday-outcome-{p['id']}"
    assert outcome["actor_id"] == "service:verification-evaluator" and outcome["outcome"] == "VERIFIED"
    assert [(m["window_name"], m["state"], m["value_text"]) for m in metrics] == [
        ("BASELINE", "PASS", "10.00"), ("LATER", "PASS", "12.00"), ("COMPARISON", "PASS", "12.00")]
    assert metrics[2]["threshold_text"] == "11.00" and metrics[2]["reason"] == vf.TARGET["rule"]
    assert outcome["details"]["baseline"]["sum_kwh"] == "30" and outcome["details"]["later"]["sum_kwh"] == "36"


def test_site_index_gives_a_mini_action_the_mill_verdict_href_only_with_lineage() -> None:
    from assetops_backend.work.site_index import DOMAIN_ACTION, _action_link

    mini = {"kind": DOMAIN_ACTION, "action_id": "a1", "action_event_id": None, "finding_revision_id": None,
            "opportunity_revision_id": "r1"}
    assert _action_link("KOBO-001", mini, {"lineage": True})["href"] == "/sites/KOBO-001/domain-actions/a1/verification"
    assert _action_link("KOBO-001", mini, {"lineage": False})["href"] is None
    cold = {**mini, "finding_revision_id": "f1", "opportunity_revision_id": None}
    assert _action_link("GH-1", cold, {"lineage": True})["href"] == "/sites/GH-1/actions/a1/verification"


def test_summary_wire_reads_the_stored_outcome_and_the_not_judged_state() -> None:
    p = plan()
    ctx = {"action": {"id": p["domain_action_id"], "action_code": "ACT-9", "title": "Run the mill at midday"},
           "plan": p}
    result = {**vf.assess(p, baseline() + later(1, 2, 3, kwh="9"), TODAY), "pins": [], "today": TODAY}
    outcome, metrics = vf.outcome_rows(p, result, NOW)
    body = vf.summary_wire(ctx, [{**outcome, "metrics": metrics}], None)
    assert body["state"] == "INEFFECTIVE" and body["reasons"] == ["TARGET_MISS"]
    assert body["cost_check"] is None and body["trial_hours"] is None
    assert body["metrics"][0] | {} == {**body["metrics"][0], "before": "10.00", "after": "9.00", "state": "FAIL",
                                       "days_before": 3, "days_after": 3}
    live = vf.assess(p, baseline() + later(1), TODAY)
    waiting = vf.summary_wire(ctx, [], live)
    assert waiting["state"] == "NOT_JUDGED" and waiting["outcome"] is None
    assert waiting["not_judged_text"] == "Not judged yet: only 1 of 3 fully checked days after the change"
    assert vf.summary_wire({**ctx, "plan": None}, [], None)["state"] == "NO_PLAN"
