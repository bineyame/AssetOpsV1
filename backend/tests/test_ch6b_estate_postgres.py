"""CH-6b1 L2m (build sheet CH-6 §B5 item 3 bullets 1, 2 and 5; CH6b1-R Q4-Q6) on `mechanism_db()`, window D7-D13.

The MD-0 mechanism Site is Kobo only (Africa/Addis_Ababa), so the Cold 7/7 and EV D9 bullets are L0
(`test_ch6b_estate_chain.py`) and a Known Deviation here (CH6b1-R Q6). Every figure is recomputed from the stored
`site_day_snapshot` rows, never a literal: Kobo `days` 6 of 7 (GAP-K7), its income earnings = the stored day money of
the counted days, `money_total` = that one Site's claim, and `/api/estate/chain` = `/api/estate/outcome-summary` through
the one function. After `late_fill(KOBO-001, D7)` and its consume: 7 of 7, the earnings grow by D7's stored money, and
a `known_at` before the fill still reads 6 of 7."""
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


def _read(c, path: str, params: dict) -> dict:
    r = c.get(path, params=params)
    assert r.status_code == 200, r.text
    return r.json()


def _check(engine, m, chain: dict, summary: dict, complete: int) -> Decimal:
    """The bullets on one (chain, summary) pair; returns Kobo's earnings amount."""
    from assetops_backend.chain.vocabulary import estate_income, money2
    from assetops_backend.site_outcomes.read import portfolio_parts

    (kobo,) = chain["sites"]
    assert (kobo["days"]["complete"], kobo["days"]["expected"]) == (complete, 7), kobo["days"]
    d7, d13 = md.day(SPEC, 7), md.day(SPEC, 13)
    days, money = _stored_money(engine, m["site_id"], d7, d13)
    earn = kobo["earnings"]["estimated_income"]
    assert days >= 3 and Decimal(earn["value"]["amount"]) == money, (earn, money)   # recomputed, non-empty
    assert earn["days"]["complete"] + earn["days"]["partial"] == days and earn["days"]["expected"] == 7, earn
    # every node of every row is over the same 7 window days as the Site's `days` (Q1)
    for cat, row in kobo["rows"].items():
        for node in (row["nodes"] or {}).values():
            if node and node.get("days") and node["key"] != "verdict.MG-1":   # MG-1 is month-to-date (R5)
                assert node["days"]["expected"] == 7, (cat, node)
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
    before = _check(engine, m, chain, summary, 6)
    assert chain["money_total"]["basis"] == "CHECKED_DAYS"       # 6 of 7: the "At least" form
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
    after = _check(engine, m, after_chain, after_summary, 7)
    _, d7_money = _stored_money(engine, m["site_id"], md.day(SPEC, 7), md.day(SPEC, 7))
    assert d7_money > 0 and after == before + d7_money, (before, after, d7_money)
    (k_old,) = old_chain["sites"]
    assert (k_old["days"]["complete"], k_old["days"]["expected"]) == (6, 7), k_old["days"]
    assert Decimal(k_old["earnings"]["estimated_income"]["value"]["amount"]) == before
