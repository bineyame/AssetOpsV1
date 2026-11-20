"""3A4 (spec `specs/3A4-amounts-by-month/spec.md` §3, §4, §6; rulings D-3A4.1 to D-3A4.11): money by month over the
in-memory commercial store.

`MonthsMemoryStore` adds spec §2's three reads to 3A1's `MemoryCommercialStore` (3A1's file is not edited); every Site
is in `Africa/Nairobi`. The expected values are spec §4's hand-computed literals (W2), never computed by the code under
test.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Mapping
from uuid import UUID, uuid4

import pytest

from assetops_backend.commercial.model import RevisionRow
from assetops_backend.commercial.months import CommercialMonths, MonthKey, month_bounds
from assetops_backend.commercial.service import CommercialRecords
from assetops_backend.structure.sources import month_window
from test_3a1_commercial_service import BY, Clock, MemoryCommercialStore, _sort_key, encode, make_world

TREE = Path(__file__).resolve().parents[2]
FIXTURE = TREE / "backend" / "tests" / "fixtures" / "commercial_months_kobo.json"
READ_AT = datetime(2026, 11, 20, 8, 0, tzinfo=timezone.utc)
NAIROBI = "Africa/Nairobi"
E = "source-emulated"
RP, SA = "RECOGNITION_PERIOD", "SETTLED_AT"


class MonthsMemoryStore(MemoryCommercialStore):
    """3A1's in-memory store plus spec §2's reads: `known_at`, `intake_revisions` and `site_zones`."""

    def latest_revisions(self, tenant_id: UUID, *, site_id: UUID | None = None, kind: str | None = None,
                         recognition_period: str | None = None,
                         known_at: datetime | None = None) -> tuple[RevisionRow, ...]:
        latest: dict[UUID, RevisionRow] = {}
        for rev in self.revisions:  # D-3A4.7: the cutoff first, then latest per record, then the filters
            if rev.tenant_id != tenant_id or (known_at is not None and rev.recorded_at > known_at):
                continue
            if rev.record_id not in latest or rev.revision_no > latest[rev.record_id].revision_no:
                latest[rev.record_id] = rev
        rows = [r for r in latest.values()
                if (site_id is None or r.site_id == site_id) and (kind is None or r.kind == kind)
                and (recognition_period is None or r.recognition_period == recognition_period)]
        return tuple(sorted(rows, key=_sort_key))

    def intake_revisions(self, tenant_id: UUID,
                         intake_id: UUID) -> tuple[tuple[RevisionRow, RevisionRow | None], ...]:
        by_id = {r.id: r for r in self.revisions if r.tenant_id == tenant_id}
        mine = sorted((r for r in by_id.values() if r.intake_id == intake_id),
                      key=lambda r: (r.source_system.encode(), r.source_record_id.encode()))
        return tuple((r, by_id[r.supersedes_revision_id] if r.supersedes_revision_id else None) for r in mine)

    def site_zones(self, tenant_id: UUID) -> Mapping[UUID, str]:
        return {sid: NAIROBI for (tid, _code), sid in self.sites.items() if tid == tenant_id}


def steps() -> list[dict]:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))["steps"]


def ingest_at(w, at: str, batch: dict) -> UUID:
    w["clock"].now = datetime.fromisoformat(at)
    result = w["svc"].ingest(w["tid"], encode(batch), entered_by=BY)
    assert result.state == "STORED" and all(o.outcome in ("NEW", "REVISED") for o in result.outcomes), result
    return result.intake_id


def ingest_steps(w, count: int = 6) -> list[UUID]:
    return [ingest_at(w, s["at"], s["batch"]) for s in steps()[:count]]


def new_world(store_cls=MonthsMemoryStore) -> dict:
    store = store_cls()
    w = make_world(store)
    clock = Clock()
    return dict(w, store=store, clock=clock, svc=CommercialRecords(store, clock=clock),
                tid=w["tenants"]["lakeside-power"], kobo=w["sites"]["KOBO-001"],
                months=CommercialMonths(store, clock=lambda: READ_AT))


@pytest.fixture()
def world() -> dict:
    return new_world()


# --- the expected tables of spec §4 (hand-computed literals) -------------------------------------------------------

def L(kind, dims, measure, value, currency, unit, count=1, basis=RP, systems=(), provenance=E, note=None):
    return (kind, tuple(dims), measure, value, currency, unit, provenance, count, basis, tuple(systems), note)


def ch(line, cls):
    return (("line_type", line), ("tariff_class", cls))


def rc(status):
    return (("status", status), ("method", "MOBILE_MONEY"))


def ex(cat, status):
    return (("category", cat), ("status", status))


def bud(factor, line_ref=None, version="budget-2026-v1"):
    return (("factor_id", factor), ("version_ref", version), ("line_ref", line_ref))


ST = (("provider", "mobile-money"),)
KV, MM, LA, LB = ("kobo-vending",), ("kobo-mm",), ("lakeside-accounts",), ("lakeside-budget-2026",)
FIXED = L("CHARGE", ch("FIXED", None), "AMOUNT", "10.00", "USD", None, systems=KV)

OCT_AFTER_F = (
    L("CHARGE", ch("USAGE", None), "AMOUNT", "120.00", "USD", None, systems=KV),
    L("CHARGE", ch("USAGE", None), "QUANTITY", "400", None, "kWh", systems=KV),
    L("CHARGE", ch("USAGE", "PRODUCTIVE"), "AMOUNT", "300.00", "USD", None, systems=KV),
    L("CHARGE", ch("USAGE", "PRODUCTIVE"), "QUANTITY", "1000", None, "kWh", systems=KV),
    L("CHARGE", ch("USAGE", "STANDARD"), "AMOUNT", "75.50", "USD", None, systems=KV),
    L("CHARGE", ch("USAGE", "STANDARD"), "QUANTITY", "250", None, "kWh", systems=KV),
    L("RECEIPT", rc("COLLECTED"), "AMOUNT", "100.00", "USD", None, systems=KV),
    L("RECEIPT", rc("PAID_IN_TRANSIT"), "AMOUNT", "60.00", "USD", None, systems=KV),
    L("SETTLEMENT", ST, "AMOUNT", "100.00", "USD", None, basis=SA, systems=MM),
    L("EXPENSE", ex("FUEL", "INVOICED"), "AMOUNT", "275.00", "USD", None, systems=LA),
    L("EXPENSE", ex("FUEL", "INVOICED"), "QUANTITY", "220", None, "L", systems=LA),
    L("EXPENSE", ex("FUEL", "PAID"), "AMOUNT", "500.00", "USD", None, systems=LA),
    L("EXPENSE", ex("FUEL", "PAID"), "QUANTITY", "400", None, "L", systems=LA),
    L("EXPENSE", ex("OM", "INVOICED"), "AMOUNT", "95.00", "USD", None, systems=LA),
    L("EXPENSE", ex("OM", "PAID"), "AMOUNT", "180.00", "USD", None, systems=LA),
    L("EXPENSE", ex("REPAIR", "QUOTE"), "AMOUNT", "900.00", "USD", None, systems=LA),
    L("EXPENSE", ex("STAFF", "PAID"), "AMOUNT", "450.00", "USD", None, systems=LA),
    L("BUDGET_LINE", bud("diesel_l"), "DECLARED", "700", None, None, systems=LB),
    L("BUDGET_LINE", bud("diesel_price"), "DECLARED", "1.25", "USD", "MONEY/L", systems=LB),
)
OCT_RECEIVED_AFTER_F = (("kobo-mm", E, 1), ("kobo-vending", E, 5), ("lakeside-accounts", E, 6),
                        ("lakeside-budget-2026", E, 2))
#: The 5 November read: CHARGE FIXED first, FUEL INVOICED as first recorded, no OM INVOICED.
OCT_KNOWN_5NOV = ((FIXED,) + OCT_AFTER_F[:9]
                  + (L("EXPENSE", ex("FUEL", "INVOICED"), "AMOUNT", "262.50", "USD", None, systems=LA),
                     L("EXPENSE", ex("FUEL", "INVOICED"), "QUANTITY", "210", None, "L", systems=LA))
                  + OCT_AFTER_F[11:13] + OCT_AFTER_F[14:])
NOV_SETTLED = L("SETTLEMENT", ST, "AMOUNT", "60.00", "USD", None, basis=SA, systems=MM)


def shape(line) -> tuple:
    value = None if line.value is None else format(line.value, "f")
    return (line.kind, line.dims, line.measure, value, line.currency, line.unit, line.provenance, line.record_count,
            line.basis, line.source_systems, line.note)


def assert_lines(month, expected) -> None:
    assert len(month.lines) == len(expected)
    for got, want in zip(month.lines, expected):
        assert shape(got) == want
        assert isinstance(got.value, Decimal) and got.value == Decimal(want[3])
        if got.measure == "AMOUNT":
            assert got.unit is None and got.currency is not None
        if got.measure == "QUANTITY":
            assert got.currency is None and got.unit in ("kWh", "L")


def received(month) -> tuple:
    return tuple((r.source_system, r.provenance, r.record_count) for r in month.received)


# --- 1: the fixture's expected table, every field ------------------------------------------------------------------

def test_01_october_after_f_line_by_line(world) -> None:
    ingest_steps(world)
    month = world["months"].site_month(world["tid"], world["kobo"], "2026-10")
    assert_lines(month, OCT_AFTER_F)
    assert len(month.lines) == 19
    assert received(month) == OCT_RECEIVED_AFTER_F
    assert month.closed is True and month.known_at is None
    assert (month.tenant_id, month.site_id, month.period) == (world["tid"], world["kobo"], "2026-10")
    assert (month.stamp.site_id, month.stamp.period) == (world["kobo"], "2026-10")


# --- 2: known_at, November, the portfolio, stamps and months_touched -------------------------------------------------

def test_02_known_at_reads_the_month_as_known(world) -> None:
    ingest_steps(world)
    known = datetime(2026, 11, 5, tzinfo=timezone.utc)
    month = world["months"].site_month(world["tid"], world["kobo"], "2026-10", known_at=known)
    assert_lines(month, OCT_KNOWN_5NOV)
    assert len(month.lines) == 19
    assert received(month) == (("kobo-mm", E, 1), ("kobo-vending", E, 6), ("lakeside-accounts", E, 5),
                                ("lakeside-budget-2026", E, 2))
    assert month.closed is True and month.known_at == known
    early = world["months"].site_month(world["tid"], world["kobo"], "2026-10",
                                       known_at=datetime(2026, 10, 31, 20, 0, tzinfo=timezone.utc))
    assert early.closed is False and early.lines == () and early.received == ()


def test_02_november_and_the_portfolio(world) -> None:
    months, tid, kobo = world["months"], world["tid"], world["kobo"]
    ingest_steps(world, 4)
    after_d = months.site_month(tid, kobo, "2026-11")
    assert_lines(after_d, (NOV_SETTLED,))
    ingest_steps_from(world, 4)
    nov = months.site_month(tid, kobo, "2026-11")
    assert_lines(nov, (FIXED, NOV_SETTLED))
    assert nov.closed is False
    portfolio = months.portfolio_month(tid, "2026-10")
    assert portfolio.site_id is None and portfolio.closed is True
    assert_lines(portfolio, (L("BUDGET_LINE", bud("staff"), "DECLARED", "1200.00", "USD", "MONEY", systems=LB),))
    assert received(portfolio) == (("lakeside-budget-2026", E, 1),)


def ingest_steps_from(w, start: int) -> list[UUID]:
    return [ingest_at(w, s["at"], s["batch"]) for s in steps()[start:]]


def test_02_a_lone_correction_in_place_makes_the_stamp_stale(world) -> None:
    """3A4 review L1: same month, same record set; only the correction's new revision differs (3B7a relies on it)."""
    months, tid, kobo = world["months"], world["tid"], world["kobo"]
    ingest_steps(world, 4)
    stamp = months.site_month(tid, kobo, "2026-10").stamp
    assert months.stale(tid, [stamp]) == ()
    step = steps()[4]
    lone = dict(step["batch"], records=[r for r in step["batch"]["records"]
                                         if r["source_record_id"] == "KOBO-EX-FUEL-1028" and r["source_version"] == "2"])
    assert len(lone["records"]) == 1
    ingest_at(world, step["at"], lone)
    assert months.stale(tid, [stamp]) == (stamp,)


def test_02_stamps_go_stale_and_months_touched(world) -> None:
    months, tid, kobo = world["months"], world["tid"], world["kobo"]
    intakes = ingest_steps(world, 4)
    s10 = months.site_month(tid, kobo, "2026-10").stamp
    s11 = months.site_month(tid, kobo, "2026-11").stamp
    assert months.stale(tid, [s10, s11]) == ()
    intakes.append(ingest_at(world, steps()[4]["at"], steps()[4]["batch"]))
    assert months.stale(tid, [s10, s11]) == (s10,)
    s10e = months.site_month(tid, kobo, "2026-10").stamp
    intakes.append(ingest_at(world, steps()[5]["at"], steps()[5]["batch"]))
    assert months.stale(tid, [s10e, s11]) == (s10e, s11)
    assert months.stale(tid, [s11, s10e]) == (s11, s10e)  # input order
    oct_, nov = MonthKey(kobo, "2026-10"), MonthKey(kobo, "2026-11")
    assert months.months_touched(tid, intakes[1]) == (oct_, nov)  # B
    assert months.months_touched(tid, intakes[3]) == (MonthKey(None, "2026-10"), oct_)  # D
    assert months.months_touched(tid, intakes[4]) == (oct_,)  # E
    assert months.months_touched(tid, intakes[5]) == (oct_, nov)  # F: the month left, then the month entered


def test_02_the_digest_is_the_spec_formula(world) -> None:
    ingest_steps(world)
    month = world["months"].site_month(world["tid"], world["kobo"], "2026-11")
    placed = [r for r in world["store"].revisions
              if r.source_record_id in ("KOBO-CH-0004", "KOBO-ST-1031")
              and r.id in {x.id for x in world["store"].latest_revisions(world["tid"])}]
    assert len(placed) == 2
    head = f"{world['kobo']}|2026-11"
    body = "\n".join(sorted(f"{r.record_id}:{r.id}" for r in placed))
    assert month.stamp.digest == hashlib.sha256(f"{head}\n{body}".encode("utf-8")).hexdigest()
    assert re.fullmatch(r"[0-9a-f]{64}", month.stamp.digest)


# --- 3: the settlement boundary and the basis ----------------------------------------------------------------------

def test_03_settlement_falls_in_its_site_local_month(world) -> None:
    months, tid, kobo = world["months"], world["tid"], world["kobo"]
    ingest_steps(world)
    october = months.site_month(tid, kobo, "2026-10")
    assert [shape(x) for x in october.lines if x.kind == "SETTLEMENT"] == [OCT_AFTER_F[8]]
    ingest_at(world, "2026-11-08T09:00:00+00:00", {
        "format_version": 1, "tenant_code": "lakeside-power", "source_type": "mobile_money_statement",
        "source_system": "kobo-mm", "provenance": E, "produced_at": "2026-11-08T09:00:00+00:00",
        "records": [{"format_version": 1, "kind": "SETTLEMENT", "source_record_id": "KOBO-ST-1101",
                     "source_version": "1", "site_code": "KOBO-001",
                     "clocks": {"settled_at": "2026-11-05T10:00:00+03:00", "recognition_period": "2026-11"},
                     "amount": {"value": "40.00", "currency": "USD"},
                     "body": {"provider": "mobile-money", "batch_ref": "SB-1101", "receipts": ["KOBO-RC-0001"]}}]})
    november = months.site_month(tid, kobo, "2026-11")
    assert_lines(november, (FIXED, L("SETTLEMENT", ST, "AMOUNT", "40.00", "USD", None, basis=RP, systems=MM),
                            NOV_SETTLED))


# --- 4 to 8: small worlds -----------------------------------------------------------------------------------------

def _batch(records, *, source_type="expense_ledger", source_system="lakeside-accounts", provenance=E) -> dict:
    return {"format_version": 1, "tenant_code": "lakeside-power", "source_type": source_type,
            "source_system": source_system, "provenance": provenance, "produced_at": "2026-11-02T06:00:00+00:00",
            "records": records}


def _expense(rid, amount, *, category="OM", status="PAID", currency="USD", litres=None) -> dict:
    r = {"format_version": 1, "kind": "EXPENSE", "source_record_id": rid, "source_version": "1",
         "site_code": "KOBO-001", "clocks": {"occurred_at": "2026-10-14T11:00:00+03:00", "recognition_period": "2026-10"},
         "amount": {"value": amount, "currency": currency}, "status": status,
         "body": {"counterparty_ref": "SUP-X", "category": category, "document_ref": rid}}
    if litres:
        r["quantity"] = {"value": litres, "unit": "L"}
    return r


def _adjustment(rid, amount, reason) -> dict:
    return {"format_version": 1, "kind": "ADJUSTMENT", "source_record_id": rid, "source_version": "1",
            "site_code": "KOBO-001", "clocks": {"effective_from": "2026-10-01", "recognition_period": "2026-10"},
            "amount": {"value": amount, "currency": "USD"},
            "body": {"reason_code": reason, "authorised_by_ref": "P-X"}}


def _budget(rid, factor, value, *, line_ref=None, currency="USD") -> dict:
    body = {"factor_id": factor, "value": value, "version_ref": "budget-2026-v1"}
    if currency:
        body["currency"] = currency
    if line_ref:
        body["line_ref"] = line_ref
    return {"format_version": 1, "kind": "BUDGET_LINE", "source_record_id": rid, "source_version": "1",
            "site_code": "KOBO-001", "clocks": {"recognition_period": "2026-10"}, "body": body}


AT = "2026-11-02T06:00:00+00:00"


def _october(w):
    return w["months"].site_month(w["tid"], w["kobo"], "2026-10")


def test_04_currencies_are_kept_apart(world) -> None:
    ingest_at(world, AT, _batch([_expense("OM-USD", "180.00"), _expense("OM-KES", "23000.00", currency="KES")]))
    assert [shape(x) for x in _october(world).lines] == [
        L("EXPENSE", ex("OM", "PAID"), "AMOUNT", "23000.00", "KES", None, systems=LA),
        L("EXPENSE", ex("OM", "PAID"), "AMOUNT", "180.00", "USD", None, systems=LA)]


def test_05_origins_are_kept_apart_observed_first(world) -> None:
    ingest_at(world, AT, _batch([_expense("OM-EMU", "180.00")]))
    ingest_at(world, AT, _batch([_expense("OM-OBS", "200.00")], source_system="kobo-ledger",
                                provenance="observed-financial"))
    assert [shape(x) for x in _october(world).lines] == [
        L("EXPENSE", ex("OM", "PAID"), "AMOUNT", "200.00", "USD", None, systems=("kobo-ledger",),
          provenance="observed-financial"),
        L("EXPENSE", ex("OM", "PAID"), "AMOUNT", "180.00", "USD", None, systems=LA)]


def test_06_sums_are_exact_past_28_digits(world) -> None:
    ingest_at(world, AT, _batch([
        _adjustment("ADJ-1", "1000000000000.000000000000000001", "R-BIG"),
        _adjustment("ADJ-2", "0.000000000001", "R-BIG"),
        _adjustment("ADJ-3", "1000000000000", "R-MID"),
        _adjustment("ADJ-4", "0.000000000001", "R-MID"),
        _adjustment("ADJ-5", "5.00", "R-ZERO"),
        _adjustment("ADJ-6", "-5.00", "R-ZERO")]))
    lines = {x.dims: x for x in _october(world).lines}
    big = lines[(("reason_code", "R-BIG"),)]
    assert format(big.value, "f") == "1000000000000.000000000001000001"
    assert big.value == Decimal("1000000000000.000000000001000001") and big.record_count == 2
    assert format(lines[(("reason_code", "R-MID"),)].value, "f") == "1000000000000.000000000001"
    zero = lines[(("reason_code", "R-ZERO"),)]
    assert format(zero.value, "f") == "0.00" and zero.record_count == 2 and not zero.value.is_signed()


def test_07_no_record_no_line(world) -> None:
    ingest_steps(world)
    empty = world["months"].site_month(world["tid"], world["kobo"], "2026-09")
    assert empty.lines == () and empty.received == ()
    assert empty.stamp.digest == hashlib.sha256(f"{world['kobo']}|2026-09\n".encode("utf-8")).hexdigest()
    empty_portfolio = world["months"].portfolio_month(world["tid"], "2026-09")
    assert empty_portfolio.lines == () and empty_portfolio.stamp.digest == hashlib.sha256(b"-|2026-09\n").hexdigest()
    fuel_only = new_world()
    ingest_at(fuel_only, AT, _batch([_expense("FUEL-1", "500.00", category="FUEL", litres="400")]))
    assert [shape(x) for x in _october(fuel_only).lines] == [
        L("EXPENSE", ex("FUEL", "PAID"), "AMOUNT", "500.00", "USD", None, systems=LA),
        L("EXPENSE", ex("FUEL", "PAID"), "QUANTITY", "400", None, "L", systems=LA)]


def test_08_budget_lines_are_never_summed(world) -> None:
    ingest_at(world, AT, _batch([_budget("BUD-A", "diesel_price", "1.25"), _budget("BUD-B", "diesel_price", "1.30"),
                                 _budget("BUD-C", "staff", "600.00", line_ref="L1"),
                                 _budget("BUD-D", "staff", "650.00", line_ref="L2")],
                                source_type="budget_workbook", source_system="lakeside-budget-2026"))
    assert [shape(x) for x in _october(world).lines] == [
        L("BUDGET_LINE", bud("diesel_price"), "DECLARED", None, "USD", "MONEY/L", count=2, systems=LB,
          note="DUPLICATE_DECLARATION"),
        L("BUDGET_LINE", bud("staff", "L1"), "DECLARED", "600.00", "USD", "MONEY", systems=LB),
        L("BUDGET_LINE", bud("staff", "L2"), "DECLARED", "650.00", "USD", "MONEY", systems=LB)]


# --- 9 to 12 ------------------------------------------------------------------------------------------------------

def test_09_a_non_money_kind_changes_nothing(world) -> None:
    ingest_steps(world)
    before = _october(world)
    ingest_at(world, "2026-11-08T09:00:00+00:00", _batch([{
        "format_version": 1, "kind": "METER_ASSIGNMENT", "source_record_id": "MA-1", "source_version": "1",
        "site_code": "KOBO-001", "subject": {"kind": "METER", "ref": "M-1"},
        "clocks": {"effective_from": "2026-10-15"}, "body": {"meter_ref": "M-1", "customer_ref": "C-0001"}}],
        source_type="meter_register", source_system="kobo-meters"))
    assert any(r.kind == "METER_ASSIGNMENT" for r in world["store"].revisions)
    after = _october(world)
    assert after.lines == before.lines and after.stamp == before.stamp and after.received == before.received


@pytest.mark.parametrize("tz", ["Africa/Nairobi", "UTC", "America/New_York"])
def test_10_month_bounds_match_month_window(tz) -> None:
    for month in range(1, 13):
        period = f"2026-{month:02d}"
        assert month_bounds(period, tz) == month_window(period, tz)[:2], (tz, period)


@pytest.mark.parametrize("period", ["2026-13", "2026-00", "2026-1", "26-10", "2026-10 ", "2026/10",
                                    "２０２６-10", "2026-1٠", ""])
def test_11_a_bad_period_is_refused(world, period) -> None:
    with pytest.raises(ValueError):
        world["months"].site_month(world["tid"], world["kobo"], period)
    with pytest.raises(ValueError):
        world["months"].portfolio_month(world["tid"], period)


def test_11_an_unknown_site_is_a_lookup_error(world) -> None:
    with pytest.raises(LookupError):
        world["months"].site_month(world["tid"], uuid4(), "2026-10")
    with pytest.raises(LookupError):  # another tenant's Site
        world["months"].site_month(world["tid"], world["sites"]["COLD-THIKA"], "2026-10")


def test_12_no_float_and_no_structure_import() -> None:
    package = TREE / "backend" / "assetops_backend" / "commercial"
    assert "float(" not in (package / "months.py").read_text(encoding="utf-8")
    files = sorted(package.rglob("*.py"))
    assert len(files) >= 6
    for path in files:
        for line in path.read_text(encoding="utf-8").splitlines():
            assert not re.match(r"\s*(from|import)\s+\S*structure", line), (path, line)
