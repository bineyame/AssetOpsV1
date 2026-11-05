"""W4-03 unit 4: the frozen `mini-opportunity/1` result (`.agent/W4-03-build-spec.md` "Unit-4 rulings (u4)"):
day rows, the weakest-eligible-hour headroom predicate, stored status precedence and limitation aggregation. Pure;
no database.
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from assetops_backend.mini_decisions import projection
from assetops_backend.mini_decisions.projection import DayHead, ProjectionIntegrityError, frozen_result
from assetops_backend.mini_depth.inputs import local_noon
from assetops_backend.mini_depth.read import iso

ZONE = "Africa/Nairobi"
DAYS = [date(2026, 10, d) for d in range(6, 11)]
E = ["00000000-0000-4000-8000-00000000000" + str(i) for i in range(1, 10)]


def head(day: date, decision: str | None, bound=None, constraints=(), cited=(), accepted=None, **row) -> DayHead:
    w = local_noon(day, ZONE)
    if decision is None:
        return DayHead(day, w)
    accepted = tuple(sorted(accepted if accepted is not None else cited))
    body = {"day": day.isoformat(), "from": iso(w.start), "to": iso(w.end), "opportunity_kwh": bound,
            "constraints": list(constraints), "decision": decision, "evidence_ids": list(cited), **row}
    return DayHead(day, w, 1, w.end, f"r-{day.day}", "sha256:" + "0" * 64, decision, accepted, w.end,
                   (w.start, w.end), {"hour": {"decision": decision}, "rows": [body]})


def eligible(day: date, low, high, cited=()) -> DayHead:
    return head(day, "ELIGIBLE", {"low": low, "high": high}, cited=cited)


def excluded(day: date, *codes, cited=()) -> DayHead:
    return head(day, "EXCLUDED", None, codes or ("HEADROOM_NON_POSITIVE",), cited)


def test_literal_example_four_missing_one_limited() -> None:
    days = [head(d, None) for d in DAYS]
    days[2] = head(DAYS[2], "LIMITED", None, ("CAPABILITY_MISSING",))
    # CH-9 owned change (CH9-R2 Q5, `mini-opportunity/2`): each day row adds `window_hours` (None for a missing
    # day, 0 for a day with no ELIGIBLE hour) and its `hours` rows; the result adds `window_hours`. Values unchanged.
    rows = [{"local_day": d.isoformat(), "decision": "LIMITED" if i == 2 else None, "opportunity_kwh": None,
             "constraints": ["CAPABILITY_MISSING"] if i == 2 else [], "evidence_ids": []} for i, d in enumerate(DAYS)]
    assert frozen_result(days, "UNKNOWN") == {
        "status": "UNKNOWN", "assessed_days": 0, "eligible_days": 0, "headroom_kw": None, "window_hours": None,
        "day_rows": [{**r, "window_hours": 0 if i == 2 else None, "hours": [r]} for i, r in enumerate(rows)],
        "limitations": [{"code": "RENEWABLE_DAY_MISSING", "evidence_ids": []},
                        {"code": "CAPABILITY_MISSING", "evidence_ids": []},
                        {"code": "SOURCE_CLASS_UNKNOWN", "evidence_ids": []}]}


def test_headroom_is_the_weakest_eligible_hour() -> None:
    rest = [excluded(d) for d in DAYS[2:]]
    r = frozen_result([eligible(DAYS[0], 18, 20), eligible(DAYS[1], 12, 15), *rest], "MEASURED")
    assert (r["status"], r["headroom_kw"], r["eligible_days"], r["assessed_days"]) == (
        "SUPPORTED", {"low": "12", "high": "15"}, 2, 5)
    # Reversed day order gives the same result; rows stay in ascending local-day order.
    rev = frozen_result([*reversed(rest), eligible(DAYS[1], 12, 15), eligible(DAYS[0], 18, 20)], "MEASURED")
    assert rev == r and [x["local_day"] for x in r["day_rows"]] == [d.isoformat() for d in DAYS]
    # Each day's own bound is a decimal string; a float bound stays exact.
    assert r["day_rows"][0]["opportunity_kwh"] == {"low": "18", "high": "20"}
    frac = frozen_result([eligible(DAYS[0], 7.25, 9.5), eligible(DAYS[1], 12.0, 15), *rest], "MEASURED")
    assert frac["headroom_kw"] == {"low": "7.25", "high": "9.5"}
    zero = frozen_result([eligible(DAYS[0], 0, 1), eligible(DAYS[1], 12, 15), *rest], "MEASURED")
    assert zero["headroom_kw"] == {"low": "0", "high": "1"}


def test_zero_eligible_and_non_supported_store_null_headroom() -> None:
    none = frozen_result([excluded(d) for d in DAYS], "MEASURED")
    assert (none["status"], none["assessed_days"], none["eligible_days"], none["headroom_kw"]) == (
        "SUPPORTED", 5, 0, None)
    limited = [eligible(DAYS[0], 18, 20), eligible(DAYS[1], 12, 15), *[excluded(d) for d in DAYS[2:4]],
               head(DAYS[4], "LIMITED", None, ("COVERAGE_GAP",))]
    r = frozen_result(limited, "MEASURED")
    assert (r["status"], r["headroom_kw"], r["eligible_days"], r["assessed_days"]) == ("LIMITED", None, 2, 4)
    assert r["day_rows"][0]["opportunity_kwh"] == {"low": "18", "high": "20"}  # retained for inspection
    unknown = frozen_result([*limited[:4], head(DAYS[4], None)], "MEASURED")
    assert (unknown["status"], unknown["headroom_kw"]) == ("UNKNOWN", None)


def test_status_precedence() -> None:
    conflict = head(DAYS[1], "CONFLICT", None, ("CONFLICT",))
    # Missing + conflict: UNKNOWN, even with mixed provenance.
    assert frozen_result([head(DAYS[0], None), conflict, *[excluded(d) for d in DAYS[2:]]], "MIXED")[
        "status"] == "UNKNOWN"
    # Five present with LIMITED or CONFLICT: LIMITED.
    assert frozen_result([excluded(DAYS[0]), conflict, *[excluded(d) for d in DAYS[2:]]], "MEASURED")[
        "status"] == "LIMITED"
    assert frozen_result([head(DAYS[0], "LIMITED", None, ("PV_USE_MISSING",)),
                          *[excluded(d) for d in DAYS[1:]]], "MEASURED")["status"] == "LIMITED"
    # Five complete with MIXED/UNKNOWN selected provenance: LIMITED, with the one class limitation.
    complete = [eligible(DAYS[0], 18, 20), *[excluded(d) for d in DAYS[1:]]]
    for cls in ("MIXED", "UNKNOWN"):
        r = frozen_result(complete, cls)
        assert (r["status"], r["headroom_kw"]) == ("LIMITED", None)
        assert r["limitations"][-1] == {"code": f"SOURCE_CLASS_{cls}", "evidence_ids": []}
    # Five complete EXCLUDED with resolved provenance: SUPPORTED, 0/5.
    r = frozen_result([excluded(d) for d in DAYS], "AUTHORED_DEMONSTRATION")
    assert (r["status"], r["assessed_days"], r["eligible_days"]) == ("SUPPORTED", 5, 0)


def test_limitation_codes_ids_and_order() -> None:
    days = [eligible(DAYS[0], 18, 20, cited=(E[0],)),
            excluded(DAYS[1], "CHARGE_OBLIGATION_ACTIVE", "HEADROOM_NON_POSITIVE", cited=(E[2], E[1])),
            excluded(DAYS[2], "HEADROOM_NON_POSITIVE", cited=(E[3], E[1])),
            head(DAYS[3], None), excluded(DAYS[4], "CAPABILITY_MISSING", cited=(E[4],))]
    r = frozen_result(days, "MIXED")
    assert r["limitations"] == [
        {"code": "RENEWABLE_DAY_MISSING", "evidence_ids": []},
        {"code": "CAPABILITY_MISSING", "evidence_ids": [E[4]]},
        {"code": "HEADROOM_NON_POSITIVE", "evidence_ids": [E[1], E[2], E[3]]},
        {"code": "CHARGE_OBLIGATION_ACTIVE", "evidence_ids": [E[1], E[2]]},
        {"code": "SOURCE_CLASS_MIXED", "evidence_ids": []}]
    # Stored row constraints keep their W4-02 order; day IDs are sorted distinct.
    assert r["day_rows"][1]["constraints"] == ["CHARGE_OBLIGATION_ACTIVE", "HEADROOM_NON_POSITIVE"]
    assert r["day_rows"][1]["evidence_ids"] == [E[1], E[2]]
    codes = {x["code"] for x in r["limitations"]}
    assert not codes & {"RECOMPUTE_PENDING", "SOURCE_STALE", "SELECTION_CHANGED", "DAY_LIMITED", "DAY_CONFLICT"}
    # No selected day at all: no SOURCE_CLASS_* code (missing days are not an unknown selected class).
    empty = frozen_result([head(d, None) for d in DAYS], None)
    assert [x["code"] for x in empty["limitations"]] == ["RENEWABLE_DAY_MISSING"]
    assert (empty["assessed_days"], empty["eligible_days"]) == (0, 0)


@pytest.mark.parametrize("change", [
    {"rows": []}, {"rows": "two"}, {"day": "2026-10-07"}, {"from": "2026-10-06T08:00:00.000000Z"},
    {"decision": "EXCLUDED"}, {"constraints": ["NOT_A_CODE"]}, {"constraints": ["CONFLICT", "CONFLICT"]},
    {"evidence_ids": ["00000000-0000-4000-8000-0000000000ff"]}, {"evidence_ids": ["not-a-uuid"]},
    {"opportunity_kwh": None}, {"opportunity_kwh": {"low": -1, "high": 2}}, {"opportunity_kwh": {"low": 3, "high": 2}},
])
def test_integrity_mismatch_refuses_never_a_missing_day(change) -> None:
    good = eligible(DAYS[0], 18, 20, cited=(E[0],))
    body = dict(good.result["rows"][0])
    if "rows" in change:
        result = {**good.result, "rows": change["rows"]}
    else:
        result = {**good.result, "rows": [{**body, **change}]}
    bad = DayHead(**{**good.__dict__, "result": result})
    with pytest.raises(ProjectionIntegrityError):
        frozen_result([bad, *[excluded(d) for d in DAYS[1:]]], "MEASURED")
    shifted = DayHead(**{**good.__dict__, "revision_window": (good.window.start, good.window.start)})
    with pytest.raises(ProjectionIntegrityError):
        projection.day_row(shifted)


def test_selected_hours_pins_and_missing_day() -> None:
    pins = projection.selected_hours([eligible(DAYS[0], 18, 20, cited=(E[0],)), head(DAYS[1], None)])
    w = local_noon(DAYS[1], ZONE)
    assert pins[1] == {"local_day": "2026-10-07", "window_from": iso(w.start), "window_to": iso(w.end),
                       "selection_seq": None, "selection_at": None, "mini_revision_id": None, "evidence_ids": []}
    assert pins[0]["selection_seq"] == 1 and pins[0]["mini_revision_id"] == "r-6"
    assert pins[0]["evidence_ids"] == [E[0]]


def test_ch9_day_folds_its_daylight_hours() -> None:
    """CH9-R2 Q1/Q5 (L0): one busy hour among eligible hours keeps the day ELIGIBLE with `window_hours` reduced by
    one, that hour's row EXCLUDED with CHARGE_OBLIGATION_ACTIVE; the study headroom is over every eligible hour and
    `window_hours` is the fewest eligible hours on any eligible day. A missing hour makes its day missing."""
    from dataclasses import replace as _replace

    def at(day, hour, decision, bound=None, codes=()):
        h = head(day, decision, bound, codes)
        start = h.window.start + timedelta(hours=hour - 12)
        w = type(h.window)(start, start + timedelta(hours=1))
        row = {**h.result["rows"][0], "from": iso(w.start), "to": iso(w.end)}
        return _replace(h, window=w, selection_end=w.end, revision_window=(w.start, w.end),
                        result={**h.result, "rows": [row]})

    days = []
    for i, d in enumerate(DAYS):
        hours = [at(d, h, "ELIGIBLE", {"low": "10", "high": str(20 + h)}) for h in (10, 11, 12)]
        if i == 1:
            hours[1] = at(d, 11, "EXCLUDED", None, ("CHARGE_OBLIGATION_ACTIVE",))
        days += hours
    r = frozen_result(days, "MEASURED")
    assert r["status"] == "SUPPORTED" and r["eligible_days"] == 5 and r["assessed_days"] == 5
    assert [x["window_hours"] for x in r["day_rows"]] == [3, 2, 3, 3, 3] and r["window_hours"] == 2
    busy = r["day_rows"][1]
    assert busy["decision"] == "ELIGIBLE" and busy["constraints"] == ["CHARGE_OBLIGATION_ACTIVE"]
    assert [h["decision"] for h in busy["hours"]] == ["ELIGIBLE", "EXCLUDED", "ELIGIBLE"]
    assert busy["hours"][1]["constraints"] == ["CHARGE_OBLIGATION_ACTIVE"]
    assert busy["opportunity_kwh"] == {"low": "20", "high": "62"}  # hours 10 and 12: 10+10, 30+32
    assert r["headroom_kw"] == {"low": "10", "high": "30"}
    missing = frozen_result([*days[:3], _replace(days[3], selection_seq=None, mini_revision_id=None, decision=None,
                                                 evidence_ids=(), result=None), *days[4:]], "MEASURED")
    assert missing["status"] == "UNKNOWN" and missing["day_rows"][1]["decision"] is None
    assert missing["day_rows"][1]["window_hours"] is None and missing["window_hours"] is None
