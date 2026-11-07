"""CH-6b1 L2m (build sheet CH-6 §B5 item 3 bullets 1, 2 and 5; CH6b1-R Q4-Q6) on `mechanism_db()`, window D7-D13.

The MD-0 mechanism Site is Kobo only (Africa/Addis_Ababa), so the Cold 7/7 and EV D9 bullets are L0
(`test_ch6b_estate_chain.py`) and a Known Deviation here (CH6b1-R Q6). Every figure is recomputed from the stored
`site_day_snapshot` rows, never a literal: Kobo `days` (GAP-K7 NO_DATA; the `states` template also lacks D8-D9, KD-3),
its income earnings = the stored day money of the counted days, `money_total` = that one Site's claim, and
`/api/estate/chain` = `/api/estate/outcome-summary` through the one function. After `late_fill(KOBO-001, D7)` and its
consume: one more checked day, the earnings grow by D7's stored money, and a `known_at` before the fill reads the
earlier days and money."""
from __future__ import annotations

import uuid
from datetime import datetime, time, timedelta, timezone
from decimal import Decimal

import pytest
from sqlalchemy import text

from test_s4_finding_store_postgres import URL

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from test_md0_mechanism_postgres import mech  # noqa: F401  (the clone + derive fixture)

    import mechanism_dataset as md
    import test_out_b4_board_postgres as b4

SPEC = md.load() if URL else None
COUNTED = ("COMPLETE", "PARTIAL")
#: (known_at, the Site's recomputed days over every Kobo measure, the recomputed productive_kwh days) per `_check`
_record_days: list = []


def _utc(d) -> str:
    return datetime.combine(d, time(0), tzinfo=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _stored_money(engine, site_id, lo, hi) -> tuple[int, Decimal]:
    """(counted days, Σ stored day money) of the latest `productive_kwh` rows over [lo, hi]."""
    with engine.connect() as c:
        rows = c.execute(text(
            "SELECT DISTINCT ON (local_day, subject_kind, subject_ref) local_day, grade, money "
            "FROM site_day_snapshot WHERE site_id = :s AND measure = 'productive_kwh' "
            "AND local_day BETWEEN :lo AND :hi ORDER BY local_day, subject_kind, subject_ref, revision DESC"),
            {"s": site_id, "lo": lo, "hi": hi}).mappings().all()
    counted = [r for r in rows if r["grade"] in COUNTED and r["money"] and r["money"].get("amount") is not None]
    return len(counted), sum((Decimal(str(r["money"]["amount"])) for r in counted), Decimal(0))


def _stored_days(engine, site_id, lo, hi, measures, known_at=None) -> dict:
    """The Site's `days` recomputed from the stored latest rows of `measures` (at `known_at`), by the `counts` rule."""
    from assetops_backend.chain.reader import counts

    with engine.connect() as c:
        rows = c.execute(text(
            "SELECT DISTINCT ON (measure, local_day, subject_kind, subject_ref) local_day, measure, subject_ref, grade "
            "FROM site_day_snapshot WHERE site_id = :s AND measure = ANY(:m) AND local_day BETWEEN :lo AND :hi "
            "AND (CAST(:k AS timestamptz) IS NULL OR computed_at <= :k) "
            "ORDER BY measure, local_day, subject_kind, subject_ref, revision DESC"),
            {"s": site_id, "m": list(measures), "lo": lo, "hi": hi, "k": known_at}).mappings().all()
    g = counts([type("R", (), dict(r))() for r in rows], lo, hi, list(measures))
    return {"complete": g.complete, "expected": g.expected, "partial": g.partial, "no_data": g.no_data}


def _read(c, path: str, params: dict) -> dict:
    r = c.get(path, params=params)
    assert r.status_code == 200, r.text
    return r.json()


def _check(engine, m, chain: dict, summary: dict, known_at=None) -> Decimal:
    """The bullets on one (chain, summary) pair; returns Kobo's earnings amount."""
    from assetops_backend.chain.measures import measures_for
    from assetops_backend.chain.vocabulary import estate_income, money2
    from assetops_backend.site_outcomes.read import portfolio_parts

    (kobo,) = chain["sites"]
    d7, d13 = md.day(SPEC, 7), md.day(SPEC, 13)
    want = _stored_days(engine, m["site_id"], d7, d13, [x.key for x in measures_for("MINIGRID")], known_at)
    assert {k: kobo["days"][k] for k in want} == want and want["expected"] == 7, (kobo["days"], want)
    _record_days.append((known_at, want, _stored_days(engine, m["site_id"], d7, d13, ["productive_kwh"], known_at)))
    days, money = _stored_money(engine, m["site_id"], d7, d13)
    earn = kobo["earnings"]["estimated_income"]
    assert days >= 3 and Decimal(earn["value"]["amount"]) == money, (earn, money)   # recomputed, non-empty
    assert earn["days"]["complete"] + earn["days"]["partial"] == days and earn["days"]["expected"] == 7, earn
    # CH6b1-R4 SPAN (the Q1 check): a node with no span is over the same 7 window days as the Site's `days`; a node
    # that carries a `span` (earnings over the window, MG-1 month to date, the mini MG-2 reading of the board day)
    # has `days` equal to that span's day count. The window-wide and the narrower sets are asserted non-empty below.
    from datetime import date as _date
    judged = spanned = 0
    for cat, row in kobo["rows"].items():
        for node in (row["nodes"] or {}).values():
            if node and node.get("days"):
                sp = node.get("span")
                if sp:
                    n = (_date.fromisoformat(sp["last"]) - _date.fromisoformat(sp["first"])).days + 1
                    assert node["days"]["expected"] == n, (cat, node)
                    spanned += n != 7
                    judged += n == 7
                else:
                    assert node["days"]["expected"] == 7, (cat, node)
                    judged += 1
    assert judged >= 1 and spanned >= 1, kobo["rows"]   # neither set is empty (income earnings; the MG-2 day)
    total = chain["money_total"]
    name = summary["sites"][0]["site_name"] or kobo["code"]
    assert total == estate_income([(name, earn)]), total
    assert total["value"]["amount"] == money2(money) and total["lines"][0].startswith(f"{name}: "), total
    # summary = EstateChain through the one function (Q4)
    parts, money_total = portfolio_parts(summary["sites"])
    assert money_total == total == summary["money_total"]
    assert parts[kobo["code"]]["rows"] == kobo["rows"] and parts[kobo["code"]]["earnings"] == kobo["earnings"]
    return Decimal(earn["value"]["amount"])


def test_kobo_week_days_earnings_total_and_summary_equal_chain(mech, monkeypatch, tmp_path) -> None:  # noqa: F811
    engine, m = mech
    url = engine.url.render_as_string(hide_password=False)
    b4._settle_chain(url, "KOBO-001")
    b4._serve(monkeypatch, url, tmp_path)
    window = {"from": _utc(md.day(SPEC, 7)), "to": _utc(md.day(SPEC, 14))}
    with engine.connect() as c:
        k_before = c.execute(text("SELECT clock_timestamp()")).scalar_one()
    with b4._client() as c:
        chain = _read(c, "/api/estate/chain", window)
        summary = _read(c, "/api/estate/outcome-summary", window)
    before = _check(engine, m, chain, summary)
    assert chain["money_total"]["basis"] == "CHECKED_DAYS"       # GAP-K7 in the window: the "At least" form
    assert chain["money_total"]["text"].startswith("At least ")
    # the late fill of the GAP-K7 day D7, consumed as the product worker does
    out = md.late_fill(url, "KOBO-001", 7)
    md.drain_mini(url)
    md.derive(url, uuid.UUID(out["tenant_id"]), uuid.UUID(out["site_id"]))
    b4._settle_chain(url, "KOBO-001")
    with b4._client() as c:
        after_chain = _read(c, "/api/estate/chain", window)
        after_summary = _read(c, "/api/estate/outcome-summary", window)
        old = {**window, "known_at": k_before.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")}
        old_chain = _read(c, "/api/estate/chain", old)
    after = _check(engine, m, after_chain, after_summary)
    _, d7_money = _stored_money(engine, m["site_id"], md.day(SPEC, 7), md.day(SPEC, 7))
    assert d7_money > 0 and after == before + d7_money, (before, after, d7_money)
    # the fill of GAP-K7 adds exactly D7 to the income days (§B5 item 3 bullet 1). Known Deviation (packet KD-3): the
    # `states` template holds D1-D5 and D10-D14 only, so D8 and D9 are NO_DATA too and the week reads 4 -> 5 of 7,
    # not the full day set's 6 -> 7; the expectation is the recomputed stored count, never a literal.
    (_, site_before, prod_before), (_, site_after, prod_after) = _record_days
    assert prod_after["complete"] == prod_before["complete"] + 1 and prod_after["expected"] == 7, _record_days
    assert site_after["complete"] == site_before["complete"] + 1, _record_days
    (k_old,) = old_chain["sites"]
    d7, d13 = md.day(SPEC, 7), md.day(SPEC, 13)
    from assetops_backend.chain.measures import measures_for
    want_old = _stored_days(engine, m["site_id"], d7, d13, [x.key for x in measures_for("MINIGRID")], k_before)
    assert {k: k_old["days"][k] for k in want_old} == _record_days[0][1] == want_old, (k_old["days"], want_old)
    assert Decimal(k_old["earnings"]["estimated_income"]["value"]["amount"]) == before
    print("CH6B1_DAYS", _record_days, "old", want_old, "money", before, after)


def test_mg1_judged_on_checked_days_and_estate_optimize_row_equals_the_d13_board(mech, monkeypatch, tmp_path) -> None:  # noqa: F811
    """CH-6b3 (§B5 item 3, the remaining bullets; `late_fill` + `known_at` is BL-08). MG-1's verdict on the week card is
    `judge_month` over the stored month-to-date rows, recomputed here on >= 3 COMPLETE days. The Optimize bullet is
    restated (CH6b3-R2, packet KD-3b): the estate row equals the D13 board's row; on `mechanism_db()` the Performance
    gate is closed, so the verdict itself is proved on the drained clone and by CO-1 and CO-1b."""
    import json
    from pathlib import Path

    from assetops_backend.chain.strategies.graded_verdict import day_grades
    from assetops_backend.outcomes.objectives import ObjectiveFact, Reading, judge_month

    engine, m = mech
    url = engine.url.render_as_string(hide_password=False)
    b4._settle_chain(url, "KOBO-001")
    b4._serve(monkeypatch, url, tmp_path)
    d13 = md.day(SPEC, 13)
    window = {"from": _utc(md.day(SPEC, 7)), "to": _utc(md.day(SPEC, 14))}
    with b4._client() as c:
        chain = _read(c, "/api/estate/chain", window)
        board = _read(c, "/api/sites/KOBO-001/outcome-board", {"date": d13.isoformat()})
        site = _read(c, "/api/sites/KOBO-001/chain", {"date": d13.isoformat()})
    (kobo,) = chain["sites"]

    kpi = kobo["rows"]["GROW_REVENUE"]["nodes"]["kpi"]
    first = d13.replace(day=1)
    assert kpi["key"] == "verdict.MG-1" and kpi["span"] == {"first": first.isoformat(), "last": d13.isoformat()}, kpi
    with engine.connect() as c:
        rows = c.execute(text(
            "SELECT DISTINCT ON (local_day, subject_kind, subject_ref) local_day, measure, subject_ref, grade, value "
            "FROM site_day_snapshot WHERE site_id = :s AND measure = 'productive_kwh' "
            "AND local_day BETWEEN :lo AND :hi ORDER BY local_day, subject_kind, subject_ref, revision DESC"),
            {"s": m["site_id"], "lo": first, "hi": d13}).mappings().all()
    typed = [type("R", (), dict(r))() for r in rows]
    grades = day_grades(typed)
    checked = sum(1 for g in grades.values() if g == "COMPLETE")
    counted = {d for d, g in grades.items() if g in COUNTED}
    value = sum((Decimal(str(r.value["kwh"])) for r in typed
                 if r.local_day in counted and r.grade in COUNTED and r.value and r.value.get("kwh") is not None),
                Decimal(0))
    assert checked >= 3, grades   # the bullet: judged on at least three COMPLETE days of stored rows
    assert kpi["days"]["complete"] == checked, (kpi, grades)
    source = Path(__file__).resolve().parents[1] / "conversions" / "demo-objectives.json"
    declared = next(o for o in json.loads(source.read_text(encoding="utf-8"))["objectives"]
                    if o["site_code"] == "KOBO-001" and o["outcome_key"] == "MG-1")
    fact = ObjectiveFact("MG-1", declared["measure_key"], "AT_LEAST", Decimal(declared["target"]), False, "", "DECLARED",
                         None, **({"min_checked_days": declared["min_checked_days"]}
                                  if declared.get("min_checked_days") else {}))
    reading = Reading(value, False, None, checked, (d13 - first).days + 1, 31)
    assert kpi["value"] == judge_month(fact, reading), (kpi, value, checked)

    # The estate row agrees with the D13 board. On `mechanism_db()` no Performance comparison report exists, so the
    # Performance gate is closed and every Kobo row reads UNKNOWN (CH6b3-R2). The verdict is proved on the drained
    # clone and by CO-1 and CO-1b.
    row = next(r for r in board["rows"] if r["category"] == "OPTIMIZE_COST")
    assert kobo["rows"]["OPTIMIZE_COST"]["state"] == row["state"], (kobo["rows"]["OPTIMIZE_COST"], row["state"])
    print("CH6B3_L2M", kpi["value"], value, checked, row["state"], row["thread_lines"],
          [t.get("state") for t in site["threads"]])
