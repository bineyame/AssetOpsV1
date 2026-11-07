"""CH-9b3 L0 (CH9b3-R Q1-Q4, Q7): the pure `midday-productive-shift-1` verdict, its stored rows and its read wire.

VERIFIED / INEFFECTIVE TARGET_MISS / not judged (SHORT, later window open) / INCONCLUSIVE LATER_SHORT /
INCONCLUSIVE BASELINE_ZERO, all in Decimal and integers (the 10% boundary is exact, never a float)."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
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
    # L2: cents would show 11.00 beside 11.00 and "Target not met"; the shown figures agree with the verdict.
    assert out["baseline_mean"] == "10.00" and out["later_mean"] == "10.999" and out["threshold"] == "11.000"
    assert Decimal(out["later_mean"]) < Decimal(out["threshold"])
    assert out["line"].endswith("10.00 → 10.999 kWh a day on 3 fully checked days each")


def test_a_miss_far_from_the_threshold_keeps_cent_figures() -> None:
    out = vf.assess(plan(), baseline("10") + later(1, 2, 3, kwh="9"), TODAY)
    assert out["later_mean"] == "9.00" and out["threshold"] == "11.00"


def test_zero_baseline_has_no_pass_threshold() -> None:  # L1
    out = vf.assess(plan(), baseline("0") + later(1, 2, 3, kwh="4"), TODAY)
    assert out["reasons"] == ["BASELINE_ZERO"] and out["threshold"] is None and out["baseline_mean"] == "0.00"


def test_not_judged_table_count_is_the_lines_count() -> None:  # L3
    p = plan()
    ctx = {"action": {"id": p["domain_action_id"], "action_code": "A", "title": "t"}, "plan": p}
    live = vf.assess(p, [row(BASE[0], grade="PARTIAL"), row(BASE[1]), row(BASE[2])] + later(1, 2, 3), TODAY)
    body = vf.summary_wire(ctx, [], live)
    assert body["not_judged_text"].endswith("only 2 of 3 fully checked days before the change")
    assert body["metrics"][0]["days_before"] == 2


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
    # MV-1 test 5: every state carries `value` (null here), and the pre-existing keys keep their order
    keys = ["action_id", "action_code", "title", "rule_id", "target", "cost_check", "trial_hours", "value", "state"]
    no_plan = vf.summary_wire({**ctx, "plan": None}, [], None)
    for b in (body, waiting, no_plan):
        assert "value" in b and b["value"] is None and list(b)[:len(keys)] == keys
    assert list(body)[len(keys):] == ["reasons", "sentence", "line", "not_judged_text", "outcome", "plan", "metrics"]
    assert list(no_plan)[len(keys):] == ["outcome", "reasons", "sentence", "line", "not_judged_text", "plan",
                                         "metrics"]


# ---- MV-1 (FUEL-1 §2.4): the mill value line ----------------------------------------------------------------------

def _price(value="0.25", state="PRICED", reason=None, currency="USD"):
    from assetops_backend.financials.fuel_cost import PriceSelection

    if state != "PRICED":
        return PriceSelection(state, reason)
    return PriceSelection("PRICED", None, "rev-1", Decimal(value), currency)


def _details(b="42.00", a="110.00", nb=3, nl=3):
    return {"baseline": {"days": [f"2026-10-0{i + 1}" for i in range(nb)], "mean_kwh_per_day": b},
            "later": {"days": [f"2026-10-1{i + 1}" for i in range(nl)], "mean_kwh_per_day": a}}


def _cents(x: Decimal) -> str:
    from decimal import ROUND_HALF_EVEN

    q = abs(x).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
    return f"-{q:f}" if x < 0 and q != 0 else f"{q:f}"


def test_verified_priced_value_reads_the_shown_means_times_the_declared_price() -> None:
    a, b, p = "110.00", "42.00", "0.25"
    v = vf.mill_value(_details(b, a), "VERIFIED", _price(p))
    d = _cents((Decimal(a) - Decimal(b)) * Decimal(p))
    assert v["state"] == "PRICED" and v["reason"] is None and v["basis"] == vf.VALUE_BASIS
    assert (v["per_day"], v["before_per_day"], v["after_per_day"]) == ("17.00", "10.50", "27.50")
    assert v["per_day"] == d and v["currency"] == "USD"
    assert v["price"] == {"revision_id": "rev-1", "value": "0.25", "currency": "USD"}
    assert v["text"] == vf.VALUE_TEXT.format(d=d, cur="USD", a=a, b=b, p=p, n=3)
    assert v["cost_text"] == vf.VALUE_COST_TEXT


def test_value_reproduces_by_hand_over_a_grid_of_means_and_prices() -> None:
    from decimal import ROUND_HALF_EVEN

    means = ["0.01", "41.99", "42.00", "110.00", "109.99"]
    for b in means:
        for a in means:
            if Decimal(a) <= Decimal(b):
                continue
            for p in ("0.25", "0.255", "1", "0.1"):
                v = vf.mill_value(_details(b, a), "VERIFIED", _price(p))
                want = ((Decimal(a) - Decimal(b)) * Decimal(p)).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
                assert Decimal(v["per_day"]) == want, (a, b, p, v["per_day"])
                assert Decimal(v["before_per_day"]) == (Decimal(b) * Decimal(p)).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_EVEN)


def test_unpriced_value_names_why_and_keeps_the_cost_line() -> None:
    cases = [(_price(state="UNPRICED", reason="NO_PRICE"), "NO_PRICE", vf.VALUE_UNPRICED_WHY["NO_PRICE"]),
             (_price(state="UNPRICED", reason="PRICE_SPANS_WINDOW"), "PRICE_SPANS_WINDOW",
              vf.VALUE_UNPRICED_WHY["PRICE_SPANS_WINDOW"]),
             (_price(state="UNPRICED", reason="PRICE_CONFLICT"), "PRICE_CONFLICT", vf.VALUE_UNPRICED_OTHER),
             (None, "PRICE_UNREADABLE", vf.VALUE_UNPRICED_OTHER)]
    for price, reason, why in cases:
        v = vf.mill_value(_details(), "VERIFIED", price)
        assert v["state"] == "UNPRICED" and v["reason"] == reason, (reason, v)
        assert v["per_day"] is None and v["before_per_day"] is None and v["after_per_day"] is None
        assert v["price"] is None and v["currency"] is None
        assert v["text"] == vf.VALUE_UNPRICED_TEXT.format(why=why) and v["cost_text"] == vf.VALUE_COST_TEXT


def test_value_is_null_for_every_other_state_and_for_a_guarded_verified() -> None:
    for outcome in ("INEFFECTIVE", "INCONCLUSIVE"):
        assert vf.mill_value(_details(), outcome, _price()) is None
    for bad in (_details("42.00", "42.00"), _details("42.00", "41.00"), _details(a=None), _details(nl=2)):
        assert vf.mill_value(bad, "VERIFIED", _price()) is None
    p = plan()
    ctx = {"action": {"id": p["domain_action_id"], "action_code": "ACT-9", "title": "t"}, "plan": p}
    for kwh, state in (("12", "VERIFIED"), ("9", "INEFFECTIVE")):
        result = {**vf.assess(p, baseline() + later(1, 2, 3, kwh=kwh), TODAY), "pins": [], "today": TODAY}
        outcome, metrics = vf.outcome_rows(p, result, NOW)
        body = vf.summary_wire(ctx, [{**outcome, "metrics": metrics}], None, price=_price())
        assert body["state"] == state
        assert (body["value"] is None) == (state != "VERIFIED")
        if state == "VERIFIED":  # 10.00 -> 12.00 at 0.25: 0.50 a day
            assert body["value"]["per_day"] == "0.50"
    zero = {**vf.assess(p, baseline("0") + later(1, 2, 3, kwh="0"), TODAY), "pins": [], "today": TODAY}
    outcome, metrics = vf.outcome_rows(p, zero, NOW)
    assert vf.summary_wire(ctx, [{**outcome, "metrics": metrics}], None, price=_price())["value"] is None
    live = vf.assess(p, baseline() + later(1), TODAY)
    assert vf.summary_wire(ctx, [], live, price=_price())["value"] is None
    assert vf.summary_wire({**ctx, "plan": None}, [], None, price=_price())["value"] is None


def test_price_text_matches_the_site_outcomes_rule() -> None:
    from assetops_backend.site_outcomes.mini import price_text

    for v in ("0.25", "0.255", "1", "0.1", "12.5"):
        assert vf._price_text(v) == price_text(v), v
