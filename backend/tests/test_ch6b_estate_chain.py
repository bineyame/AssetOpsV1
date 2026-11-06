"""CH-6b1 L0 (build sheet CH-6 §B5 item 1, R14, OWN-1104 R10 replaced, CH6b1-R): the EstateChain composition over a
fixture ChainRequest. No database.

Three Sites in two time zones over one UTC-midnight week [25 Oct, 1 Nov): Kobo (mini, Addis), the Cold lab (Addis)
and the EV depot (UTC, one expected Tuesday). Every node is judged over the Site's `window_days` (Q1), the row state
keeps CH3-R (mini on `window_day`, cold/EV over the whole window), counts are summed, the income total follows Q5,
and the one snapshot read seeds exactly the per-Site reads (Q3)."""
from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import UUID

import pytest

sys.path.insert(0, str(Path(__file__).parent))
import test_ch5a1_board_contract as BC  # noqa: E402

from assetops_backend import read_scope  # noqa: E402
from assetops_backend.chain import vocabulary as v  # noqa: E402
from assetops_backend.chain.claims import claim_days, estate_count_claims  # noqa: E402
from assetops_backend.chain.measures import measures_for  # noqa: E402
from assetops_backend.chain.read import board_day, local_days, window_days  # noqa: E402
from assetops_backend.site_outcomes import read  # noqa: E402
from assetops_backend.site_outcomes.read import SiteOutcomeBoardService, portfolio_parts  # noqa: E402

UTC = timezone.utc
LO, HI = datetime(2026, 10, 25, tzinfo=UTC), datetime(2026, 11, 1, tzinfo=UTC)
KOBO, COLD, EV = BC.KOBO, BC.COLD, BC.EV  # Addis, Addis, Etc/UTC
TUESDAY = date(2026, 10, 27)
GAP = date(2026, 10, 28)   # Kobo's one NO_DATA day in the window


@dataclass(frozen=True)
class Row:  # the `SnapshotRow` fields the reader, the evaluator and the seeding filter read
    site_id: UUID
    local_day: date
    measure: str
    subject_kind: str
    subject_ref: str
    grade: str
    evidence_class: str = "MEASURED"
    value: dict | None = None
    money: dict | None = None


def _site_rows(site, days, grade_of, money_of) -> list[Row]:
    out = []
    for d in days:
        for spec in measures_for(site.site_type):
            subject = "SITE" if spec.subject_kind == "SITE" else "asset-1"
            g = grade_of(d, spec.key)
            m = money_of(d, spec.key) if g in ("COMPLETE", "PARTIAL") else None
            out.append(Row(site.site_id, d, spec.key, spec.subject_kind, subject, g,
                           value=None if m is None else {"kwh": "2.5"}, money=m))
    return out


def _kobo_grade(d, m):
    return "NO_DATA" if d == GAP else "COMPLETE"


def _kobo_money(d, m):  # 1.0025 USD a day: six counted days = 6.015 -> 6.02 (half even)
    return {"amount": "1.0025", "currency": "USD"} if m == "productive_kwh" else None


def _ev_grade(d, m):
    return "COMPLETE" if d == TUESDAY else "NOT_EXPECTED"


def _ev_money(d, m):  # one counted day = 0.015 -> 0.02 (half even)
    return {"amount": "0.015", "currency": "USD"} if m == "charging_kwh" else None


KOBO_DAYS = [date(2026, 10, 1) + timedelta(days=i) for i in range(32)]   # 1 Oct .. 1 Nov (1 Nov outside the week)
WEEK8 = [date(2026, 10, 25) + timedelta(days=i) for i in range(8)]       # 25 Oct .. 1 Nov
SNAPSHOTS = {
    KOBO.site_id: _site_rows(KOBO, KOBO_DAYS, _kobo_grade, _kobo_money),
    COLD.site_id: _site_rows(COLD, WEEK8, lambda d, m: "COMPLETE", lambda d, m: None),
    EV.site_id: _site_rows(EV, WEEK8, _ev_grade, _ev_money),
}


def _ORDER(r: Row) -> tuple:
    return (str(r.site_id), r.measure, r.local_day, r.subject_kind, r.subject_ref)


class Port(BC.Port):
    def snapshots(self, tenant_id, site_id, lo, hi, measures, known_at):
        self.calls.append(("snapshots", (site_id, lo, hi, tuple(measures))))
        rows = [r for r in SNAPSHOTS.get(site_id, []) if lo <= r.local_day <= hi and r.measure in measures]
        return sorted(rows, key=_ORDER)   # the store's ORDER BY (site, measure, day, subject)

    def placement_facts(self, tenant_id, site_id, revision_ids, known_at):
        return {}


class ManyPort(Port):
    def snapshots_many(self, tenant_id, site_ids, lo, hi, measures, known_at):
        self.calls.append(("snapshots_many", (tuple(site_ids), lo, hi, tuple(measures))))
        rows = [r for s in site_ids for r in SNAPSHOTS.get(s, []) if lo <= r.local_day <= hi and r.measure in measures]
        return sorted(rows, key=_ORDER)


def _summary(port, known_at=None, sites=(KOBO, COLD, EV)):
    svc = SiteOutcomeBoardService(BC.services(port, []))
    with read_scope.scope("test:ch6b1") as sc:
        body = svc.summary(list(sites), LO, HI, known_at)
        req = svc.s.chain_reader.request(BC.TENANT, known_at)
        days = {s.site_code: claim_days(req, s, LO, HI) for s in sites}
    return svc, body, sc, days


@pytest.fixture(scope="module")
def run():
    return _summary(ManyPort())


# ---------------------------------------------------------------- Q1: one window frame per Site, two time zones

def test_addis_week_is_eight_local_days_but_seven_window_days():
    """The frame difference the rule exists for (non-vacuity of the next test)."""
    assert len(local_days(LO, HI, BC.ADDIS)) == 8 and len(window_days(LO, HI, BC.ADDIS)) == 7
    assert window_days(LO, HI, BC.ADDIS) == window_days(LO, HI, "Etc/UTC")


def test_every_node_and_the_site_days_cover_the_same_day_set(monkeypatch):
    windows: dict[str, tuple[date, date]] = {}
    real = read.site_nodes

    def spy(inp, keys):
        windows.setdefault(inp.site_code, inp.window)
        return real(inp, keys)

    monkeypatch.setattr(read, "site_nodes", spy)
    _, body, _, days = _summary(ManyPort())
    for site in (KOBO, COLD, EV):
        wd = window_days(LO, HI, site.timezone)
        assert windows[site.site_code] == (wd[0], wd[-1]), site.site_code
        assert days[site.site_code].requested == len(wd) == 7
    by = {s["site_code"]: s for s in body["sites"]}
    for code, site_days in days.items():
        for row in by[code]["rows"]:
            for node in (row["nodes"] or {}).values():
                if node and node.get("days"):
                    assert node["days"]["expected"] == site_days.expected, (code, row["category"], node)


def test_kobo_six_of_seven_cold_seven_of_seven_ev_one_tuesday(run):
    _, body, _, days = run
    assert (days["KOBO-001"].complete, days["KOBO-001"].expected, days["KOBO-001"].no_data) == (6, 7, 1)
    assert (days["COLD-LAB-001"].complete, days["COLD-LAB-001"].expected) == (7, 7)
    assert (days["EV-LAB-001"].complete, days["EV-LAB-001"].expected) == (1, 1)  # NOT_EXPECTED days not in m
    by = {s["site_code"]: s for s in body["sites"]}
    kobo = by["KOBO-001"]["earnings"]["estimated_income"]
    assert kobo["value"]["amount"] == str(Decimal("1.0025") * 6) and kobo["days"]["complete"] == 6
    assert kobo["days"]["expected"] == 7 and kobo["basis"] == "CHECKED_DAYS"   # 1 Nov (Addis day 8) is not counted
    ev = by["EV-LAB-001"]["earnings"]["estimated_charging_income"]
    assert ev["value"]["amount"] == "0.015" and (ev["days"]["complete"], ev["days"]["expected"]) == (1, 1)
    assert by["COLD-LAB-001"]["earnings"] == {}


def test_row_state_mini_on_the_last_local_day_cold_ev_over_the_whole_window(run):
    _, body, _, _ = run
    by = {s["site_code"]: s for s in body["sites"]}
    lo, hi = board_day(date(2026, 10, 31), BC.ADDIS)
    assert by["KOBO-001"]["window_basis"] == "DAY"
    assert (by["KOBO-001"]["window"]["from"], by["KOBO-001"]["window"]["to"]) == (read.wire(lo), read.wire(hi))
    for code in ("COLD-LAB-001", "EV-LAB-001"):
        assert by[code]["window_basis"] == "PERIOD"
        assert (by[code]["window"]["from"], by[code]["window"]["to"]) == (read.wire(LO), read.wire(HI))


# ---------------------------------------------------------------- counts summed; Q4 one function

def test_counts_are_summed_over_the_sites(run):
    svc, _, _, days = run
    with read_scope.scope("test:counts"):
        req = svc.s.chain_reader.request(BC.TENANT, None)
        # the fixture port has no thread rows (AttributeError = an unavailable thread read): the days still count
        counted = estate_count_claims(req, [KOBO, COLD, EV], LO, HI, [], (read.PortUnavailable, AttributeError))
    summed = v.sum_days(list(days.values()))
    assert all(c.days == summed for c in counted.claims.values())
    assert summed["expected"] == 7 + 7 + 1 and summed["complete"] == 6 + 7 + 1


def test_one_function_builds_sites_and_the_total(run):
    _, body, _, _ = run
    parts, total = portfolio_parts(body["sites"])
    assert total == body["money_total"]
    for s in body["sites"]:
        p = parts[s["site_code"]]
        assert p["earnings"] == s["earnings"]
        assert set(p["rows"]) == {r["category"] for r in s["rows"]}
        for r in s["rows"]:
            assert p["rows"][r["category"]] == {"state": r["state"], "state_label": r["state_label"],
                                                "lead": r["lead_outcome"], "nodes": r["nodes"]}


def test_server_filled_parts_are_never_earnings(run):
    _, body, _, _ = run
    for s in body["sites"]:
        assert all(c["key"] in read.INCOME_KEYS for c in (s["earnings"] or {}).values())


# ---------------------------------------------------------------- Q5 the income total

def test_money_total_rounds_each_site_then_sums(run):
    _, body, _, _ = run
    total = body["money_total"]
    # 6.015 -> 6.02 and 0.015 -> 0.02: the shown lines add to 6.04; the raw sum 6.030 would show 6.03
    assert total["value"] == {"amount": "6.04", "currency": "USD"} and total["basis"] == "CHECKED_DAYS"
    assert total["text"] == "At least 6.04 USD estimated income, from checked days · not billed or collected"
    assert total["lines"] == ["Kobo: 6.02 USD over 6 of 7 days checked", "Depot: 0.02 USD over 1 of 1 days checked"]
    assert total["days"]["expected"] == 8 and total["days"]["complete"] == 7


def _claim(amount=None, cur="USD", complete=3, expected=3, partial=0, basis=None):
    days = {"complete": complete, "partial": partial, "low": 0, "no_data": expected - complete - partial,
            "pending": 0, "expected": expected}
    value = None if amount is None else {"amount": amount, "currency": cur}
    return {"key": "money.estimated_income", "value": value, "days": days,
            "basis": basis or v.count_basis(days)}


def test_complete_form_and_partly_checked_line():
    t = v.estate_income([("A", _claim("1.00")), ("B", _claim("2.50"))])
    assert t["text"] == "Estimated income from checked days: 3.50 USD · not billed or collected"
    assert t["basis"] == "COMPLETE" and t["lines"] == ["A: 1.00 USD over 3 of 3 days checked",
                                                        "B: 2.50 USD over 3 of 3 days checked"]
    t = v.estate_income([("A", _claim("1.00", complete=2, partial=1))])
    assert t["lines"] == ["A: 1.00 USD over 2 of 3 days checked · 1 partly checked"]
    assert t["text"].startswith("At least 1.00 USD")


def test_a_not_known_site_is_named_excluded_and_makes_the_total_a_lower_bound():
    t = v.estate_income([("A", _claim("1.00")), ("B", _claim(None, complete=0, basis="NOT_KNOWN"))])
    assert t["value"] == {"amount": "1.00", "currency": "USD"} and t["basis"] == "CHECKED_DAYS"
    assert t["text"].startswith("At least 1.00 USD estimated income") and t["lines"][1] == "B: not known yet"
    assert t["days"]["expected"] == 3   # only the contributor's days


def test_mixed_currency_has_no_value_but_keeps_the_lines():
    t = v.estate_income([("A", _claim("1.00")), ("B", _claim("2.00", cur="EUR"))])
    assert t["value"] is None and t["text"] == v.node_text("money.currency_mixed") and len(t["lines"]) == 2


def test_no_contributor_is_not_known_and_no_record_is_not_named():
    assert v.estate_income([]) == {"key": "money.estate_income", "value": None, "basis": "NOT_KNOWN",
                                   "days": None, "text": "Not known yet", "lines": []}
    t = v.estate_income([("B", _claim(None, complete=0))])
    assert t["text"] == "Not known yet" and t["lines"] == ["B: not known yet"]


# ---------------------------------------------------------------- Q3 one snapshot read

def test_one_statement_seeds_exactly_the_per_site_reads():
    many = ManyPort()
    _, seeded, sc, _ = _summary(many)
    names = [n for n, _ in many.calls if n.startswith("snapshots")]
    assert names == ["snapshots_many"], names   # no per-Site snapshot statement ran
    assert sc.names().get("chain.day_many") == 1 and "chain.day" not in sc.names()
    plain = Port()
    _, unseeded, _, _ = _summary(plain)
    # two ranges per Site read per Site; the EV depot (UTC) has one range for both, so 5 distinct keys
    assert [n for n, _ in plain.calls].count("snapshots") == 5
    assert seeded == unseeded


def test_seeded_rows_equal_the_per_site_rows():
    svc = SiteOutcomeBoardService(BC.services(ManyPort(), []))
    specs = svc.snapshot_specs([KOBO, COLD, EV], LO, HI)
    assert len(specs) == 6 and len({(s, k, d) for s, k, d in specs}) == 5   # EV (UTC): one range for both
    with read_scope.scope("seeded"):
        req = svc.s.chain_reader.request(BC.TENANT, None)
        assert req.seed_days(specs) == 5
        seeded = [req.day(s, k, d).rows for s, k, d in specs]
    with read_scope.scope("plain"):
        req = SiteOutcomeBoardService(BC.services(Port(), [])).s.chain_reader.request(BC.TENANT, None)
        plain = [tuple(req.day(s, k, d).rows) for s, k, d in specs]
    assert [tuple(x) for x in seeded] == plain and all(plain)


def test_a_port_without_the_batch_falls_back_and_is_counted(monkeypatch):
    seen: list[str] = []
    real = read.perf.record
    monkeypatch.setattr(read.perf, "record", lambda name, ms: (seen.append(name), real(name, ms)))
    _summary(Port())
    assert seen.count("summary.seed_fallback") == 1
    seen.clear()
    _summary(ManyPort())
    assert "summary.seed_fallback" not in seen


# ---------------------------------------------------------------- CH6b1-R2: a one-day judgement names its day

ONE_DAY_KPI = {"key": "verdict.MG-5", "value": "MET", "basis": "COMPLETE", "text": "x",
               "days": {"expected": 1, "complete": 1, "partial": 0, "low": 0, "no_data": 0, "not_expected": 0}}


@pytest.mark.parametrize("tz,lo,hi", [
    ("Africa/Addis_Ababa", datetime(2026, 10, 24, 21, tzinfo=UTC), datetime(2026, 10, 31, 21, tzinfo=UTC)),
    ("Etc/UTC", datetime(2026, 10, 25, tzinfo=UTC), datetime(2026, 11, 1, tzinfo=UTC)),
])
def test_reading_verdict_without_a_kpi_record_names_its_last_window_day(tz, lo, hi):
    from assetops_backend.outcomes.objectives import ObjectiveFact
    from assetops_backend.site_outcomes.board import SiteFacts, row_nodes
    obj = (ObjectiveFact("MG-5", "m", ">=", 1, False, "t", "S", None),)
    wd = window_days(lo, hi, tz)
    assert len(wd) > 1
    facts = SiteFacts(domain="solar", site_code="S", objectives=obj, nodes={"MG-5": {"kpi": ONE_DAY_KPI}}, day=wd[-1], one_day=False)
    line = row_nodes(facts, ["MG-5"], "MG-5", "ON_TRACK", [("MG-5", "ON_TRACK")])["nodes"]["kpi"]["days_line"]
    assert line == f"{v.day_text(wd[-1])} · 1 of 1 day checked"
    assert line != "1 of 1 days checked"
    one = SiteFacts(domain="solar", site_code="S", objectives=obj, nodes={"MG-5": {"kpi": ONE_DAY_KPI}}, day=wd[-1], one_day=True)
    assert row_nodes(one, ["MG-5"], "MG-5", "ON_TRACK", [("MG-5", "ON_TRACK")])["nodes"]["kpi"]["days_line"] \
        == "1 of 1 days checked"   # a one-day board keeps the unchanged line
