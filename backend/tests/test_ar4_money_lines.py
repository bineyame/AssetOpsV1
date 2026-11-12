"""ANY-2 AR-4 MN-1/2/3 (no database): money lines with receipts, the `money.lines` kind and its price.revised rebuild.

Spec: `.agent/architect-answer-money-snapshot-2026-11-10.md` §6-§7; sequence rev 5 "AR-4 contract line"; D-ANY.8 step 3.
"""
from __future__ import annotations

import ast
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest

from assetops_backend.chain.adapters.file_chain_config import load_event_register
from assetops_backend.chain.events import Event, resolve
from assetops_backend.chain.measure_impls import ProductiveEnergy
from assetops_backend.chain.measures import MEASURES
from assetops_backend.chain.period_read import period_fp
from assetops_backend.chain.ports import DayCtx, SiteRef
from assetops_backend.chain.strategies.base import ContributionContext
from assetops_backend.chain.strategies.priced_energy import PricedEnergy
from assetops_backend.estate import money_rows as mr
from assetops_backend.financials.money_lines import (
    MoneyTotalRefused, potential_line, priced_line, refuse_totals, reproduces)

UTC = timezone.utc
ADDIS = "Africa/Addis_Ababa"
T, S = uuid4(), uuid4()
REV, REV2 = "11111111-1111-1111-1111-111111111111", "22222222-2222-2222-2222-222222222222"
D0 = date(2026, 11, 5)


def _sel(value: str, rev: str = REV, currency: str = "USD") -> dict:
    return {"state": "PRICED", "revision_id": rev, "price": {"value": value, "currency": currency}}


def _item(status: str = "SUPPORTED", low: str = "3.2", high: str = "4.75") -> dict:
    return {"site_code": "KOBO-001", "study": {"status": status, "headroom_kw": {"low": low, "high": high},
                                              "first_day": "2026-11-01", "last_day": "2026-11-05"}}


# --- MN-1: receipts on stored day money ----------------------------------------------------------------------------

def test_priced_line_rounds_the_unrounded_quantity_and_its_receipt_reproduces() -> None:
    line = priced_line(Decimal("80.0042"), "kWh", Decimal("0.25"), "USD", REV)
    assert line["amount"] == "20.00" and line["basis"] == "MEASURED"
    assert line["receipt"] == {"v": 1, "formula": "priced_energy@1", "qty": "80.0042", "unit": "kWh", "rate": "0.25",
                               "rate_unit": "USD/kWh", "rate_ref": REV, "rounding": "half_up_cent",
                               "segments": None, "fx": None}
    assert reproduces(line)
    # must-fail: a wrong rate, a wrong quantity or an edited amount does not reproduce
    assert not reproduces({**line, "receipt": {**line["receipt"], "rate": "0.26"}})
    assert not reproduces({**line, "receipt": {**line["receipt"], "qty": "81"}})
    assert not reproduces({**line, "amount": "20.01"})
    assert not reproduces({**line, "currency": "TZS"})  # the rate unit names another currency


def test_productive_day_money_keeps_its_amount_and_gains_basis_and_receipt() -> None:
    adapter = ProductiveEnergy(reader=None)
    ctx = DayCtx(T, S, "KOBO-001", "MINIGRID", ADDIS, D0, None, None, None)
    sub = "asset-1"
    adapter._put(ctx, sub, (_sel("0.25"), Decimal("80.0042")))
    money = adapter.money(ctx, sub, {"kwh": "80.004"})
    assert (money["amount"], money["currency"], money["assumption_revision_id"]) == ("20.00", "USD", REV)
    assert money["basis"] == "MEASURED" and money["receipt"]["qty"] == "80.0042" and reproduces(money)
    # the version bump: the adapter key and the catalogue name the same @2 (a new input_fp, so a rebuild appends)
    assert adapter.key == MEASURES["productive_kwh"].adapter == "mini.productive_energy@2"
    adapter._put(ctx, sub, ({"state": "UNPRICED"}, Decimal("1")))
    assert adapter.money(ctx, sub, {"kwh": "1.000"}) is None


# --- MN-2: the stored potential line ----------------------------------------------------------------------------

def _today_potential(low: str, high: str, price: str, currency: str = "USD") -> dict:
    rec = SimpleNamespace(node="potential", direction="UP")
    e = PricedEnergy().effect(ContributionContext(rec, headroom_kw=(Decimal(low), Decimal(high)),
                                                  evidence_status="SUPPORTED", price=Decimal(price), currency=currency))
    return {"low": str(e.money["low"]), "high": str(e.money["high"]), "currency": e.money["currency"]}


@pytest.mark.parametrize("low, high, price", [("3.2", "4.75", "0.25"), ("0", "12.125", "1.2708"),
                                              ("1.5", "1.5", "350")])
def test_potential_line_equals_todays_strategy_byte_for_byte(low: str, high: str, price: str) -> None:
    line = potential_line(Decimal(low), Decimal(high), Decimal(price), "USD", REV)
    assert {k: line[k] for k in ("low", "high", "currency")} == _today_potential(low, high, price)
    assert line["basis"] == "DECLARED" and line["receipt"]["rounding"] == "none" and reproduces(line)
    assert not reproduces({**line, "receipt": {**line["receipt"], "rate": "9"}})  # must-fail: wrong rate


def test_day_body_holds_a_line_only_where_todays_compose_shows_money() -> None:
    body = mr.day_body(S, D0, _item(), _sel("0.25"))
    assert [x["kind"] for x in body["lines"]] == ["potential"] and body["lines"][0]["low"] == "0.800"
    assert body["study"] == {"status": "SUPPORTED", "headroom_kw": {"low": "3.2", "high": "4.75"}}
    assert body["price"] == {"amount": "0.25", "currency": "USD", "revision_id": REV}
    assert mr.day_body(S, D0, _item(status="LIMITED"), _sel("0.25"))["lines"] == []
    assert mr.day_body(S, D0, _item(), {"state": "UNPRICED"})["lines"] == []
    assert mr.day_body(S, D0, None, _sel("0.25"))["lines"] == [] and mr.day_body(S, D0, None, None)["study"] is None


class _Snap:
    read_at = datetime(2026, 11, 12, 3, tzinfo=UTC)

    def __init__(self, items: list) -> None:
        self.items, self.calls = items, []

    def opportunity_threads(self, t, site_ids, lo, hi, k):
        self.calls.append((t, list(site_ids), lo, hi, k))
        return self.items


class _Estate:
    def __init__(self, snap: _Snap) -> None:
        self.snap = snap

    def read(self, work):
        return work(self.snap)


class _Prices:
    def __init__(self, by_rev: str, value: str) -> None:
        self.sel, self.calls = _sel(value, by_rev), []

    def series(self, t, s, key, *, valid_at, recorded_at):
        self.calls.append((key, valid_at, recorded_at))
        return {"selection": self.sel}


def test_builder_reads_the_boards_opportunity_days_and_the_price_valid_at_the_day_start() -> None:
    snap, prices = _Snap([{"site_code": "OTHER", "study": {}}, _item()]), _Prices(REV, "0.25")
    builder = mr.MoneyLinesKindBuilder(_Estate(snap), prices)
    site = SiteRef(T, S, "KOBO-001", "MINIGRID", ADDIS)
    ctx = DayCtx(T, S, "KOBO-001", "MINIGRID", ADDIS, D0, None, None, None)
    [frag] = builder.fragments(ctx, site)
    start = datetime(2026, 11, 4, 21, tzinfo=UTC)  # Addis midnight of D0
    assert (frag.period_start, frag.period_end, frag.local_day, frag.state) == (
        start, start + timedelta(days=1), D0, "PRICED")
    assert snap.calls == [(T, [S], start - timedelta(days=4), start + timedelta(days=1), snap.read_at)]
    assert prices.calls == [("productive_use_price_per_kwh", start, snap.read_at)]
    assert frag.inputs["rate_refs"] == [REV] and reproduces(frag.body["lines"][0])
    assert builder.fragments(ctx, SiteRef(T, S, "C", "COLDCHAIN", ADDIS)) == []
    # a saved price is a new rate_ref, so the rebuilt row has a new input fingerprint (a new revision)
    again = mr.MoneyLinesKindBuilder(_Estate(snap), _Prices(REV2, "0.30")).fragments(ctx, site)[0]
    assert period_fp(mr.KIND_MONEY, mr.BUILDER_VERSION, again.inputs, again.body) != period_fp(
        mr.KIND_MONEY, mr.BUILDER_VERSION, frag.inputs, frag.body)
    assert again.body["lines"][0]["receipt"]["rate_ref"] == REV2


# --- rev-5 contract: a saved price rebuilds money.lines from its valid date to today ------------------------------

def _price_event(valid: list) -> Event:
    now = datetime(2026, 11, 12, 3, tzinfo=UTC)
    return Event(uuid4(), "price.revised", 1, now, now, "test", T, S,
                 {"key": "productive_use_price_per_kwh", "valid": valid})


def test_price_revised_dirties_money_lines_from_the_valid_date_to_today() -> None:
    reg = load_event_register()
    assert reg.kinds["money.lines"].grain == "local_day"
    assert "productive_use_price_per_kwh" in reg.kinds["money.lines"].inputs.assumption_keys
    today = date(2026, 11, 12)
    open_marks = resolve(reg, _price_event(["2026-11-07T21:00:00Z", None]), site_type="MINIGRID", tz=ADDIS,
                         today=today)
    assert sorted(d for d, m in open_marks if m == "money.lines") == [date(2026, 11, 8) + timedelta(days=i)
                                                                      for i in range(5)]
    closed = resolve(reg, _price_event(["2026-11-07T21:00:00Z", "2026-11-09T21:00:00Z"]), site_type="MINIGRID",
                     tz=ADDIS, today=today)
    assert sorted(d for d, m in closed if m == "money.lines") == [date(2026, 11, 8), date(2026, 11, 9)]
    assert resolve(reg, _price_event(["2026-11-07T21:00:00Z", None]), site_type="COLDCHAIN", tz=ADDIS,
                   today=today) == []  # the kind is mini-grid only; a cold Site has no productive price measure
    other = Event(uuid4(), "price.revised", 1, datetime.now(UTC), datetime.now(UTC), "t", T, S,
                  {"key": "ev_gross_tariff_per_kwh", "valid": ["2026-11-07T21:00:00Z", None]})
    assert [m for _, m in resolve(reg, other, site_type="MINIGRID", tz=ADDIS, today=today)] == []


def test_the_drain_routes_money_lines_marks_to_the_period_builder() -> None:
    from assetops_backend.chain.composition import period_kind_builders, period_kind_versions

    builders = period_kind_builders(type("I", (), {"mini": None})())
    assert isinstance(builders["money.lines"], mr.MoneyLinesKindBuilder)
    assert period_kind_versions()["money.lines"] == mr.BUILDER_VERSION


# --- MN-3: no stored totals ---------------------------------------------------------------------------------------

@pytest.mark.parametrize("body", [
    {"day": "2026-11-05", "lines": [], "total": "5"},
    {"day": "2026-11-05", "lines": [{"currency": "USD", "site_id": "a"}, {"currency": "USD", "site_id": "b"}]},
    {"day": "2026-11-05", "lines": [{"currency": None}]},
    {"day": "2026-11-05", "nested": {"verified_total": "1"}},
])
def test_refuse_totals_refuses_cross_site_cross_currency_and_verified_totals(body: dict) -> None:
    with pytest.raises(MoneyTotalRefused):
        refuse_totals(body)


def test_refuse_totals_runs_at_build(monkeypatch) -> None:
    refuse_totals(mr.day_body(S, D0, _item(), _sel("0.25")))  # a real body passes
    monkeypatch.setattr(mr, "potential_line", lambda *a: {"low": "1", "high": "2", "currency": "USD",
                                                          "receipt": {}, "total": "3"})
    with pytest.raises(MoneyTotalRefused):
        mr.day_body(S, D0, _item(), _sel("0.25"))


MONEY_WRITERS = ("assetops_backend/estate/money_rows.py", "assetops_backend/financials/money_lines.py")


def _sums(path: Path) -> list[int]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return [n.lineno for n in ast.walk(tree) if isinstance(n, ast.Call) and getattr(n.func, "id", None) == "sum"]


def test_no_money_row_builder_sums(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    assert {p: _sums(root / p) for p in MONEY_WRITERS} == {p: [] for p in MONEY_WRITERS}
    bad = tmp_path / "bad.py"  # non-vacuous: the scan finds a sum
    bad.write_text("total = sum(x['amount'] for x in lines)\n", encoding="utf-8")
    assert _sums(bad) == [1]
