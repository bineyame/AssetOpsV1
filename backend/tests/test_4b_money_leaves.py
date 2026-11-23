"""4b2: the money leaves from records (spec `specs/4b-money-leaves/spec.md` §3 to §5, tests 1 to 13; D-4B.3 to D-4B.9,
D-4B.12 to D-4B.15, D-4B.18). No database.

The world is 3A4's `new_world` (imported, never edited); batches are ingested with `ingest_at`'s pattern but each
step's own `entered_by`. Expected values are spec §4's hand-computed literals (W2), never computed by the code under
test. Run with `DATABASE_URL` and `ASSETOPS_TEST_DATABASE_URL` unset.
"""

from __future__ import annotations

import copy
import decimal
import json
from datetime import datetime, timezone
from decimal import Context, Decimal
from pathlib import Path
from types import SimpleNamespace
from uuid import UUID

import pytest

from assetops_backend.chain.ports import SiteRef
from assetops_backend.structure.evaluate import weakest_origin
from assetops_backend.structure.read import StructureRead, site_count
from assetops_backend.structure.sources import ProductLeafSource, ReadContext
from test_3a1_commercial_service import encode
from test_3a4_commercial_months import READ_AT, ingest_steps, new_world

TREE = Path(__file__).resolve().parents[2]
FIXTURE = TREE / "backend" / "tests" / "fixtures" / "money_leaves_lakeside.json"
PACK = TREE / "Docs" / "demo-sprint" / "product-direction-layer4" / "derived-values.json"
NAIROBI = "Africa/Nairobi"
E, OF, UNKNOWN = "source-emulated", "observed-financial", "unknown"
KV, LF, GEN, KB, LA = ("commercial:kobo-vending", "commercial:lakeside-fuel", "commercial:assetops-world-generator",
                       "commercial:kisiwa-billing", "commercial:lakeside-accounts")
NEUTRAL = "option-only neutral"
PRICE_ID = UUID("4b000000-0000-4000-8000-000000000001")
CHARGE_WORDS = "Billing export: the month's charges"
RECEIPT_WORDS = "Receipts for the month, with their payment status"
FUEL_WORDS = "Fuel invoices for the month"
CR = "COMMERCIAL_RECORD"

#: Test 10's own literal of spec §3.4's "Names when absent" column (W2): (record_kind, source_family, words).
READ_AS = {
    "revenue": ("CHARGE", CR, CHARGE_WORDS),
    "fuel_bought": ("EXPENSE (FUEL)", CR, FUEL_WORDS),  # DD3d.4 (D-DD.163): the invoices are a leaf, not a node
    "om": ("EXPENSE (OM)", CR, "Service contractor invoice"),
    "staff": ("EXPENSE (STAFF)", CR, "Payroll summary"),
    "productive_kwh": ("CHARGE (productive tariff class)", CR, None),
    "in_transit": ("RECEIPT", CR, RECEIPT_WORDS),
    "outstanding": {"CHARGE": ("CHARGE", CR, CHARGE_WORDS), "RECEIPT": ("RECEIPT", CR, None)},
    "diesel_price": ("EXPENSE (FUEL)", CR, None),
}
#: Test 10's own literal state tables (W2; spec §3.2).
STATE_TABLE = {
    "PROVIDED": {"period_days", "unserved_critical_kwh", "productive_kwh", "in_transit", "outstanding", "om",
                 "staff", "necessary_l", "candidate_l", "unexplained_l",  # 4d: the three litre leaves
                 "delivered_kwh", "technical_loss_kwh", "unexplained_loss_kwh", "adjustments_kwh", "unmapped_kwh",
                 "tariff"},  # 4a: energy-to-cash@1
    "ASSUMED": {"productive_tariff"},
    "HELD_NOT_CALCULATED": {"reduced_days",
                            "hours_per_day", "customer_hours_interrupted", "field_visits", "dawn_days_below"},
    "NOT_CONNECTED": {"wear_rate", "major_assets", "liability", "standby_kw", "lost_unit_kw"},
    "OPTION_ONLY": {"extra_l", "battery_throughput_kwh", "collection_cost"},
    "PROVIDED_ELSE_ASSUMED": {"diesel_price"},
}
STATED_TABLE = {"MINI_GRID": {"revenue": "PROVIDED",
                              "metered_kwh": "PROVIDED", "billed_kwh": "PROVIDED"}}  # 4a: the stated kWh nodes; DD3d.4: fuel cost is not stated
#: 4a: read without the energy source, the stated kWh nodes have nothing to read and no expression value, so each
#: names itself among the missing (registry v4, D-4A.1).
MTO_MISSING = ("adjustments_kwh", "billed_kwh", "candidate_l", "delivered_kwh", "metered_kwh",
               "necessary_l", "productive_kwh", "productive_tariff", "revenue", "tariff", "technical_loss_kwh",
               "unexplained_l", "unexplained_loss_kwh", "unmapped_kwh")
REVENUE_NINE = ("adjustments_kwh", "billed_kwh", "delivered_kwh", "metered_kwh", "productive_kwh",
                "productive_tariff", "revenue", "tariff", "technical_loss_kwh", "unexplained_loss_kwh", "unmapped_kwh")
#: 4a: what the two stated kWh nodes name when absent (their `stated_by`).
ENERGY_READ_AS = {
    "metered_kwh": ("CUSTOMER_METER_READ", CR, "Customer meter reads for the month"),
    "billed_kwh": ("CHARGE (USAGE kWh)", CR, "Billing export: the month's billed kWh"),
}


# ---------------------------------------------------------------- the world and the reader


def fixture_steps() -> list[dict]:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))["steps"]


def ingest(w, at: str, batch: dict, entered_by: str = "service:test-4b"):
    w["clock"].now = datetime.fromisoformat(at)
    result = w["svc"].ingest(w["tid"], encode(batch), entered_by=entered_by)
    assert result.state == "STORED" and all(o.outcome in ("NEW", "REVISED") for o in result.outcomes), result
    return result


def ingest_fixture(w, steps: list[dict] | None = None) -> dict:
    for step in steps if steps is not None else fixture_steps():
        ingest(w, step["at"], step["batch"], step["entered_by"])
    return w


def money_world(steps: list[dict] | None = None) -> dict:
    return ingest_fixture(new_world(), steps)


def window_price(tenant, site, key, start, end, known_at):
    if key == "diesel_price_per_litre":
        return SimpleNamespace(state="PRICED", value=Decimal("1.30"), currency="USD", revision_id=PRICE_ID,
                               reason=None)
    return SimpleNamespace(state="NO_PRICE", value=None, currency=None, revision_id=None, reason="NO_PRICE")


def fallback() -> ProductLeafSource:
    return ProductLeafSource(SimpleNamespace(latest=lambda *a, **k: ()), window_price, lambda: READ_AT)


class Recording:
    """Wraps the provider and keeps every value it returns for the 4b table's factors (test 10)."""

    def __init__(self, inner) -> None:
        self.inner, self.seen = inner, []

    def leaf(self, ctx, factor_id):
        got = self.inner.leaf(ctx, factor_id)
        if factor_id in READ_AS:
            self.seen.append((factor_id, got))
        return got

    def stated(self, ctx, factor_id):
        got = self.inner.stated(ctx, factor_id)
        self.seen.append((factor_id, got))
        return got


def reader(w) -> tuple[StructureRead, Recording]:
    from assetops_backend.structure.money import CommercialLeafSource

    rec = Recording(CommercialLeafSource(w["months"], w["store"], fallback()))
    rec.w = w
    return StructureRead(rec, stated=rec), rec


LITRES = ("candidate_l", "necessary_l", "unexplained_l")


def bought(rec: Recording, code: str, month: str = "2026-10", known_at=None):
    """The month's fuel invoices (the `fuel_bought` leaf, D-DD.163): the money a figure never takes for fuel cost."""
    from assetops_backend.structure.sources import ReadContext

    return rec.inner._judge(ReadContext(site(rec.w, code), month, known_at), "fuel_bought")


def assert_fuel_not_available(v: dict, rec: Recording, code: str, month: str = "2026-10", also: tuple = ()) -> None:
    """D-DD.177: a world that states fuel by invoices and holds no litres serves no fuel cost, cost to serve or
    contribution, names the litre leaves, and never serves the invoice total in their place."""
    total = bought(rec, code, month).value
    for node in ("fuel_cost", "cost_to_serve", "contribution"):
        got = v[node]
        assert got.value is None and got.evidence == "NOT_AVAILABLE" and not got.stated, node
        assert set(LITRES) <= set(got.missing_leaves), node
        assert set(also) <= set(got.missing_leaves) or node == "fuel_cost", node
        assert total is None or got.value != total, node


def site(w, code: str) -> SiteRef:
    return SiteRef(w["tid"], w["sites"][code], code, "MINIGRID", NAIROBI)


def assert_read_as(rec: Recording) -> int:
    """Every absent value the provider built names its `READ_AS` record (D-4B.13); returns how many it checked."""
    checked = 0
    for factor_id, got in rec.seen:
        if got.value is not None:
            continue
        m = got.missing
        want = READ_AS[factor_id] if factor_id in READ_AS else ENERGY_READ_AS[factor_id]  # 4a
        if isinstance(want, dict):
            kind = m.note.split(":", 1)[1] if m.note and m.note.startswith("NEEDS:") else "RECEIPT"
            want = want[kind]
        assert (m.record_kind, m.source_family, m.record_words) == want, (factor_id, m)
        checked += 1
    return checked


def gap(value) -> tuple:
    m = value.missing
    return (m.record_kind, m.source_family, m.cause, m.record_words, m.note)


def text(v: Decimal) -> str:
    return format(v, "f")


def expense(rid, site_code, at, amount, litres, status, category, currency="USD", period="2026-10") -> dict:
    record = {"format_version": 1, "kind": "EXPENSE", "source_record_id": rid, "source_version": "1",
              "site_code": site_code, "clocks": {"occurred_at": at, "recognition_period": period},
              "amount": {"value": amount, "currency": currency}, "status": status,
              "body": {"counterparty_ref": "SUP-F", "category": category, "document_ref": rid}}
    if litres is not None:
        record["quantity"] = {"value": litres, "unit": "L"}
    return record


def envelope(step: int, records: list[dict]) -> dict:
    batch = copy.deepcopy(fixture_steps()[step]["batch"])
    batch["records"] = records
    return batch


def accounts(records: list[dict]) -> dict:
    """Batch D's envelope (`lakeside-accounts`, `source-emulated`) with other records."""
    return envelope(3, records)


LATER = "2026-11-06T10:00:00+00:00"


# ---------------------------------------------------------------- test 1: the §4.1 Site tables


def check_kobo_october(w) -> Recording:
    read, rec = reader(w)
    v = read.site(site(w, "KOBO-001"), "2026-10").values
    expect = {  # factor: (text, currency, evidence, sources, origins)
        "revenue": ("3458.00", "USD", "RECORDED", (KV,), (E,)),
        "diesel_price": ("1.25", "USD", "DERIVED", (LF,), (OF,)),
        "om": ("600.00", "USD", "RECORDED", (GEN,), (E,)),
        "staff": ("500.00", "USD", "RECORDED", (GEN,), (E,)),
        "productive_kwh": ("0", None, "RECORDED", (KV,), (E,)),
        "in_transit": ("0", "USD", "RECORDED", (KV,), (E,)),
        "outstanding": ("278.00", "USD", "DERIVED", (KV,), (E,)),
        "collected": ("3180.00", "USD", "DERIVED", (KV,), (E,)),
    }
    for factor_id, (value, currency, evidence, sources, origins) in expect.items():
        got = v[factor_id]
        assert (text(got.value), got.value, got.currency, got.evidence, got.sources, got.origins) == (
            value, Decimal(value), currency, evidence, sources, origins), factor_id
        assert got.missing is None, factor_id
    assert v["revenue"].stated and v["revenue"].computed is None
    assert v["fuel_cost"].stated is False and v["fuel_cost"].detail_missing == LITRES
    assert_fuel_not_available(v, rec, "KOBO-001")
    assert (text(bought(rec, "KOBO-001").value), bought(rec, "KOBO-001").evidence) == ("792.50", "RECORDED")
    assert v["contribution"].detail_missing == tuple(sorted(v["revenue"].detail_missing + LITRES))
    assert v["contribution"].missing_leaves == LITRES
    assert weakest_origin(v["revenue"].origins) == E
    return rec


def check_kisiwa_october(w) -> Recording:
    read, rec = reader(w)
    v = read.site(site(w, "KISIWA-001"), "2026-10").values
    expect = {
        "revenue": ("4070.00", "USD", "RECORDED", (KB,), (E,)),
        "staff": ("500.00", "USD", "RECORDED", (GEN,), (E,)),
        "outstanding": ("270.00", "USD", "DERIVED", (KB,), (E,)),
        "collected": ("3800.00", "USD", "DERIVED", (KB,), (E,)),
        "in_transit": ("0", "USD", "RECORDED", (KB,), (E,)),
        "productive_kwh": ("0", None, "RECORDED", (KB,), (E,)),
    }
    for factor_id, (value, currency, evidence, sources, origins) in expect.items():
        got = v[factor_id]
        assert (text(got.value), got.currency, got.evidence, got.sources, got.origins) == (
            value, currency, evidence, sources, origins), factor_id
    price = v["diesel_price"]
    assert price.value == Decimal("1.30") and (price.evidence, price.sources, price.origins) == (
        "DERIVED", (LA,), (E,))
    assert price.missing is None  # the invoices' price, not the fallback's labelled 1.30
    om = v["om"]
    assert om.value is None and om.evidence == "NOT_AVAILABLE"
    assert (om.missing.record_kind, om.missing.source_family, om.missing.cause, om.missing.carried_as,
            om.missing.blocks, om.missing.record_words, om.missing.assumption, om.missing.note) == (
        "EXPENSE (OM)", CR, "NOT_RECEIVED", None, ("cost_to_serve", "contribution"), "Service contractor invoice",
        None, None)
    assert_fuel_not_available(v, rec, "KISIWA-001", also=("om",))
    assert text(bought(rec, "KISIWA-001").value) == "1173.90"
    for node in ("cost_to_serve", "contribution"):
        assert v[node].value is None and v[node].missing_leaves == ("candidate_l", "necessary_l", "om",
                                                                    "unexplained_l"), node
    return rec


def check_mto_october(w) -> Recording:
    read, rec = reader(w)
    v = read.site(site(w, "MTO-001"), "2026-10").values
    for factor_id, value in (("om", "500.00"), ("staff", "450.00")):
        got = v[factor_id]
        assert (text(got.value), got.currency, got.evidence, got.sources, got.origins) == (
            value, "USD", "RECORDED", (GEN,), (E,)), factor_id
    assert v["revenue"].value is None
    assert gap(v["revenue"]) == ("CHARGE", CR, "NOT_CONNECTED", CHARGE_WORDS, None)
    assert v["fuel_cost"].value is None and v["fuel_cost"].missing_leaves == LITRES
    assert bought(rec, "MTO-001").value is None  # no invoice, no litres: nothing to say, never a zero
    assert gap(bought(rec, "MTO-001")) == ("EXPENSE (FUEL)", CR, "NOT_RECEIVED", FUEL_WORDS, None)
    price = v["diesel_price"]
    assert (price.value, price.evidence, price.missing.carried_as, price.sources, price.origins) == (
        Decimal("1.30"), "ESTIMATED", "ASSUMPTION", (f"assumption:{PRICE_ID}",), (UNKNOWN,))
    assert v["productive_kwh"].value is None
    assert gap(v["productive_kwh"]) == ("CHARGE (productive tariff class)", CR, "NOT_CONNECTED", None, None)
    assert v["in_transit"].value is None
    assert gap(v["in_transit"]) == ("RECEIPT", CR, "NOT_CONNECTED", RECEIPT_WORDS, None)
    assert v["outstanding"].value is None
    assert gap(v["outstanding"]) == ("CHARGE", CR, "NOT_CONNECTED", CHARGE_WORDS, "NEEDS:CHARGE")
    assert v["contribution"].value is None and v["contribution"].missing_leaves == MTO_MISSING
    return rec


def test_1_october_site_tables():
    w = money_world()
    check_kobo_october(w)
    check_kisiwa_october(w)
    check_mto_october(w)


# ---------------------------------------------------------------- test 2: the open month (D-4B.4, D-4B.14)


def november_reads() -> tuple[dict, dict, list[Recording]]:
    w = money_world()
    read, rec1 = reader(w)
    first = read.site(site(w, "KOBO-001"), "2026-11").values
    ingest(w, LATER, envelope(1, [expense("KOBO-EX-FUEL-1105", "KOBO-001", "2026-11-05T11:00:00+03:00", "130.00",
                                          "100", "PAID", "FUEL", period="2026-11")]))
    read2, rec2 = reader(w)
    second = read2.site(site(w, "KOBO-001"), "2026-11").values
    return first, second, [rec1, rec2]


def test_2_november_is_open():
    first, second, (_, rec2) = november_reads()
    revenue = first["revenue"]
    assert revenue.value is None
    m = revenue.missing
    assert (m.record_kind, m.source_family, m.cause, m.carried_as, m.blocks, m.record_words, m.note) == (
        "CHARGE", CR, "NOT_RECEIVED", None, ("collected", "contribution"), CHARGE_WORDS, "MONTH_OPEN")
    assert first["om"].value is None
    assert gap(first["om"]) == ("EXPENSE (OM)", CR, "NOT_RECEIVED", "Service contractor invoice", "MONTH_OPEN")
    price = first["diesel_price"]
    assert (price.value, price.evidence) == (Decimal("1.30"), "ESTIMATED")  # no November fuel invoice yet
    # (ii) a November fuel invoice exists: no price and no fuel cost while the month is open, never the fallback's.
    for factor_id, words, got in (("diesel_price", None, second["diesel_price"]),
                                  ("fuel_bought", FUEL_WORDS, bought(rec2, "KOBO-001", "2026-11"))):
        assert got.value is None and got.evidence == "NOT_AVAILABLE", factor_id
        assert gap(got) == ("EXPENSE (FUEL)", CR, "NOT_RECEIVED", words, "MONTH_OPEN"), factor_id
    assert second["fuel_cost"].value is None  # D-DD.177: not the invoice


# ---------------------------------------------------------------- test 3: the portfolio ("k of n sites")


def check_portfolio(w) -> None:
    read, _ = reader(w)
    sites = [site(w, code) for code in ("KOBO-001", "KISIWA-001", "MTO-001")]
    p = read.portfolio(w["tid"], sites, "2026-10")
    expect = {
        "revenue": ("7528.00", 2, (("MTO-001", REVENUE_NINE),)),
        # D-DD.177: no litres in the world, so no site states a fuel cost; each names its litre leaves (was 1,966.40 of 2)
        "fuel_cost": (None, 0, tuple((c, LITRES) for c in ("KOBO-001", "KISIWA-001", "MTO-001"))),
        "om": ("1100.00", 2, (("KISIWA-001", ("om",)),)),
        "staff": ("1450.00", 3, ()),
        "outstanding": ("548.00", 2, (("MTO-001", ("outstanding",)),)),
        "collected": ("6980.00", 2, (("MTO-001", tuple(sorted(REVENUE_NINE + ("in_transit", "outstanding")))),)),
        "contribution": (None, 0, (("KOBO-001", LITRES), ("KISIWA-001", ("candidate_l", "necessary_l", "om", "unexplained_l")),
                                   ("MTO-001", MTO_MISSING))),
    }
    for factor_id, (value, k, out) in expect.items():
        got = p.composition.values[factor_id].value
        assert (got.value is None) if value is None else text(got.value) == value, factor_id
        count = site_count(p, factor_id)
        assert (count.k, count.n, count.out) == (k, 3, out), factor_id
    contribution = p.composition.values["contribution"].value
    assert contribution.value is None and contribution.evidence == "NOT_AVAILABLE"


def test_3_portfolio():
    check_portfolio(money_world())


# ---------------------------------------------------------------- test 4: 3A4's fixture, reused (§4.2)


def test_4_3a4_fixture():
    w = new_world()
    ingest_steps(w)
    read, _ = reader(w)
    kobo = site(w, "KOBO-001")
    v = read.site(kobo, "2026-10").values
    after_f = {"revenue": "495.50", "in_transit": "60.00", "outstanding": "335.50", "collected": "100.00",
               "productive_kwh": "1000", "om": "275.00", "staff": "450.00"}
    assert {f: text(v[f].value) for f in after_f} == after_f
    assert_fuel_not_available(v, _, "KOBO-001")  # D-DD.177: no litres, so no fuel cost, cost to serve, contribution
    assert text(bought(_, "KOBO-001").value) == "775.00"
    assert v["diesel_price"].value == Decimal("1.25") and v["diesel_price"].evidence == "DERIVED"
    early = read.site(kobo, "2026-10", known_at=datetime(2026, 11, 5, tzinfo=timezone.utc)).values
    known = {"revenue": "505.50", "outstanding": "345.50", "collected": "100.00",
             "om": "180.00"}
    assert {f: text(early[f].value) for f in known} == known
    assert text(bought(_, "KOBO-001", known_at=datetime(2026, 11, 5, tzinfo=timezone.utc)).value) == "762.50"
    assert early["contribution"].value is None  # D-DD.177
    assert early["diesel_price"].value == Decimal("1.25")


# ---------------------------------------------------------------- test 5: DS1b parity of batch E
# In `simulator/tests/world/test_4b_fixture_parity.py`: the dependency-direction guard bans a backend import of
# `assetops_simulator` (Known Deviation, packet-4b2.md).


# ---------------------------------------------------------------- test 6: currencies apart


def currency_reads() -> tuple[dict, dict, list[Recording]]:
    w = money_world()
    ingest(w, LATER, accounts([expense("KOBO-EX-OM-KES", "KOBO-001", "2026-10-12T11:00:00+03:00", "1000.00", None,
                                       "PAID", "OM", currency="KES")]))
    read, rec1 = reader(w)
    om_kes = read.site(site(w, "KOBO-001"), "2026-10").values
    w2 = money_world()
    ingest(w2, LATER, envelope(1, [expense("KOBO-EX-FUEL-KES", "KOBO-001", "2026-10-12T11:00:00+03:00", "13000.00",
                                           "100", "PAID", "FUEL", currency="KES")]))
    read2, rec2 = reader(w2)
    fuel_kes = read2.site(site(w2, "KOBO-001"), "2026-10").values
    return om_kes, fuel_kes, [rec1, rec2]


def test_6_currencies_apart():
    om_kes, fuel_kes, _ = currency_reads()
    assert om_kes["om"].value is None
    assert gap(om_kes["om"]) == ("EXPENSE (OM)", CR, "NOT_CALCULATED_YET", "Service contractor invoice",
                                 "CURRENCY_MISMATCH:KES,USD")
    for factor_id, words in (("fuel_bought", FUEL_WORDS), ("diesel_price", None)):
        got = bought(_[1], "KOBO-001") if factor_id == "fuel_bought" else fuel_kes[factor_id]
        assert got.value is None and got.evidence == "NOT_AVAILABLE", factor_id  # not the fallback's 1.30
        assert gap(got) == ("EXPENSE (FUEL)", CR, "NOT_CALCULATED_YET", words, "CURRENCY_MISMATCH:KES,USD"), \
            factor_id


def test_6_recorded_zero_checks_currency_r9():
    """R9: Kobo's `in_transit` is a recorded zero (all receipts COLLECTED); a KES receipt of the month still mixes."""
    w = money_world()
    kes = {"format_version": 1, "kind": "RECEIPT", "source_record_id": "KOBO-RC-KES", "source_version": "1",
           "site_code": "KOBO-001",
           "clocks": {"occurred_at": "2026-10-26T10:00:00+03:00", "recognition_period": "2026-10"},
           "amount": {"value": "500.00", "currency": "KES"}, "status": "COLLECTED",
           "body": {"payer_ref": "C-1001", "method": "MOBILE_MONEY"}}
    ingest(w, LATER, envelope(0, [kes]))
    read, _ = reader(w)
    got = read.site(site(w, "KOBO-001"), "2026-10").values["in_transit"]
    assert got.value is None
    assert gap(got) == ("RECEIPT", CR, "NOT_CALCULATED_YET", RECEIPT_WORDS, "CURRENCY_MISMATCH:KES,USD")


# ---------------------------------------------------------------- test 7: connected against received (D-4B.5)


def without(rid: str) -> list[dict]:
    steps = copy.deepcopy(fixture_steps())
    for step in steps:
        step["batch"]["records"] = [r for r in step["batch"]["records"] if r["source_record_id"] != rid]
    return steps


def connected_reads() -> tuple[dict, dict, dict, list[Recording]]:
    w = money_world(without("KISIWA-RC-1001"))
    read_a, rec_a = reader(w)
    a = read_a.site(site(w, "KISIWA-001"), "2026-10").values
    september = copy.deepcopy(fixture_steps()[2]["batch"])
    september["records"] = [{"format_version": 1, "kind": "RECEIPT", "source_record_id": "KISIWA-RC-0901",
                             "source_version": "1", "site_code": "KISIWA-001",
                             "clocks": {"occurred_at": "2026-09-28T10:00:00+03:00", "recognition_period": "2026-09"},
                             "amount": {"value": "100.00", "currency": "USD"}, "status": "COLLECTED",
                             "body": {"payer_ref": "C-2001", "method": "CASH"}}]
    ingest(w, LATER, september)
    read_b, rec_b = reader(w)
    b = read_b.site(site(w, "KISIWA-001"), "2026-10").values
    w_c = money_world()
    read_c, rec_c = reader(w_c)
    c = read_c.site(site(w_c, "MTO-001"), "2026-10").values
    return a, b, c, [rec_a, rec_b, rec_c]


def test_7_connected_against_received_and_the_record_named():
    a, b, c, _ = connected_reads()
    for values in (a, b, c):
        assert values["outstanding"].value is None and values["in_transit"].value is None
    assert gap(a["outstanding"]) == ("RECEIPT", CR, "NOT_CONNECTED", None, "NEEDS:RECEIPT")
    assert gap(a["in_transit"]) == ("RECEIPT", CR, "NOT_CONNECTED", RECEIPT_WORDS, None)
    assert gap(b["outstanding"]) == ("RECEIPT", CR, "NOT_RECEIVED", None, "NEEDS:RECEIPT")
    assert gap(b["in_transit"]) == ("RECEIPT", CR, "NOT_RECEIVED", RECEIPT_WORDS, None)
    assert gap(c["outstanding"]) == ("CHARGE", CR, "NOT_CONNECTED", CHARGE_WORDS, "NEEDS:CHARGE")
    assert gap(c["in_transit"]) == ("RECEIPT", CR, "NOT_CONNECTED", RECEIPT_WORDS, None)
    assert text(a["revenue"].value) == "4070.00"  # the charges are still read


# ---------------------------------------------------------------- test 8: a quote is never a cost (D-4B.3)


def test_8_a_quote_revised_to_an_invoice_becomes_cost():
    w = money_world()
    quote = copy.deepcopy(fixture_steps()[1]["batch"]["records"][2])
    assert quote["source_record_id"] == "KOBO-EX-FUEL-Q1025" and quote["status"] == "QUOTE"
    quote.update(source_version="2", status="INVOICED")
    ingest(w, LATER, envelope(1, [quote]))
    read, rec = reader(w)
    v = read.site(site(w, "KOBO-001"), "2026-10").values
    assert text(bought(rec, "KOBO-001").value) == "1152.50" and v["fuel_cost"].value is None
    with decimal.localcontext(Context(prec=34, rounding=decimal.ROUND_HALF_EVEN)):
        expected = Decimal("1152.50") / Decimal("934")
    assert v["diesel_price"].value == expected


# ---------------------------------------------------------------- test 9: a late record is seen (D-4B.12)


def test_9_a_late_record_is_seen_through_one_read():
    w = money_world()
    read, _ = reader(w)
    kobo = site(w, "KOBO-001")
    assert text(read.site(kobo, "2026-10").values["om"].value) == "600.00"
    ingest(w, LATER, accounts([expense("KOBO-EX-OM-1030", "KOBO-001", "2026-10-30T11:00:00+03:00", "50.00", None,
                                       "PAID", "OM")]))
    assert text(read.site(kobo, "2026-10").values["om"].value) == "650.00"


def test_9_one_month_read_and_one_kinds_read_per_site_read():
    from assetops_backend.structure.money import CommercialLeafSource

    w = money_world()
    calls = {"site_month": 0, "latest_revisions": 0}

    class Months:
        def site_month(self, *a, **k):
            calls["site_month"] += 1
            return w["months"].site_month(*a, **k)

    class Store:
        def latest_revisions(self, *a, **k):
            calls["latest_revisions"] += 1
            return w["store"].latest_revisions(*a, **k)

    source = CommercialLeafSource(Months(), Store(), fallback())
    read = StructureRead(source, stated=source)
    read.site(site(w, "KOBO-001"), "2026-10")
    assert calls == {"site_month": 1, "latest_revisions": 1}
    read.site(site(w, "KOBO-001"), "2026-10")
    assert calls == {"site_month": 2, "latest_revisions": 2}  # nothing reused across reads


# ---------------------------------------------------------------- test 10: states and READ_AS


def test_10_state_tables_are_the_spec_tables():
    from assetops_backend.structure.sources import SOURCE_STATE, STATED_STATE, STATES

    assert STATES[-1] == "PROVIDED_ELSE_ASSUMED" and len(STATES) == 6
    states = SOURCE_STATE["MINI_GRID"]
    assert {s: {f for f, x in states.items() if x == s} for s in STATE_TABLE} == STATE_TABLE
    assert len(states) == 31
    assert {k: dict(v) for k, v in STATED_STATE.items()} == STATED_TABLE


def test_10_every_absent_value_names_its_read_as_record():
    from assetops_backend.structure import money

    recs = [check_kobo_october(money_world()), check_kisiwa_october(money_world()),
            check_mto_october(money_world())]
    recs += november_reads()[2] + currency_reads()[2] + connected_reads()[3] + [zero_litres_read()[1]]
    assert sum(assert_read_as(rec) for rec in recs) >= 20
    # The module's own mapping agrees with the test's literal.
    for factor_id, want in READ_AS.items():
        got = money.READ_AS[factor_id]
        if isinstance(want, dict):
            assert {k: (fb.kind, fb.family, fb.words) for k, fb in got.items()} == want
        else:
            assert (got.kind, got.family, got.words) == want, factor_id


# ---------------------------------------------------------------- test 11: exact sums


def test_11a_no_float_and_no_structure_import_under_commercial():
    money_py = (TREE / "backend" / "assetops_backend" / "structure" / "money.py").read_text(encoding="utf-8")
    assert "float(" not in money_py
    for path in (TREE / "backend" / "assetops_backend" / "commercial").rglob("*.py"):
        body = path.read_text(encoding="utf-8")
        assert "assetops_backend.structure" not in body and "from ..structure" not in body, path


def test_11b_sums_ignore_the_ambient_context():
    w = money_world()
    read, rec = reader(w)
    with decimal.localcontext(Context(prec=3)):
        v = read.site(site(w, "KOBO-001"), "2026-10").values
        total = bought(rec, "KOBO-001").value
    assert (text(v["revenue"].value), text(total), text(v["outstanding"].value)) == (
        "3458.00", "792.50", "278.00")
    assert v["diesel_price"].value == Decimal("1.25")


# ---------------------------------------------------------------- test 12: zero litres (D-4B.15)


def zero_litres_read() -> tuple[dict, Recording]:
    w = money_world()
    ingest(w, LATER, accounts([expense("MTO-EX-FUEL-1015", "MTO-001", "2026-10-15T11:00:00+03:00", "40.00", "0",
                                       "PAID", "FUEL")]))
    read, rec = reader(w)
    return read.site(site(w, "MTO-001"), "2026-10").values, rec


def test_12_zero_litres_give_no_price():
    v, rec = zero_litres_read()
    assert text(bought(rec, "MTO-001").value) == "40.00" and v["fuel_cost"].value is None
    price = v["diesel_price"]
    assert price.value is None and price.evidence == "NOT_AVAILABLE"  # not the fallback's 1.30
    assert gap(price) == ("EXPENSE (FUEL)", CR, "NOT_CALCULATED_YET", None, "ZERO_DENOMINATOR:fuel_litres")


# ---------------------------------------------------------------- test 13: composition disposal


def _store(name, log):
    return SimpleNamespace(dispose=lambda: log.append(name))


def test_13_earlier_stores_are_disposed_when_the_commercial_builder_raises(monkeypatch):
    import assetops_backend.chain.composition as chain_composition
    import assetops_backend.commercial.composition as commercial_composition
    import assetops_backend.financials.composition as fin_composition
    from assetops_backend.structure.composition import build_structure_read

    log: list[str] = []
    monkeypatch.setattr(chain_composition, "build_snapshot_store", lambda url: _store("snapshots", log))
    monkeypatch.setattr(fin_composition, "build_window_price_selection",
                        lambda url: SimpleNamespace(select=window_price, dispose=lambda: log.append("prices")))

    def boom(url):
        raise RuntimeError("commercial builder failed")

    monkeypatch.setattr(commercial_composition, "build_commercial_reads", boom)
    with pytest.raises(RuntimeError, match="commercial builder failed"):
        build_structure_read("postgresql://x")
    assert sorted(log) == ["prices", "snapshots"]


def test_13_dispose_disposes_each_store_once(monkeypatch):
    import assetops_backend.chain.composition as chain_composition
    import assetops_backend.commercial.composition as commercial_composition
    import assetops_backend.financials.composition as fin_composition
    from assetops_backend.structure.composition import build_structure_read
    from assetops_backend.structure.money import CommercialLeafSource

    log: list[str] = []
    w = money_world()
    monkeypatch.setattr(chain_composition, "build_snapshot_store", lambda url: _store("snapshots", log))
    monkeypatch.setattr(fin_composition, "build_window_price_selection",
                        lambda url: SimpleNamespace(select=window_price, dispose=lambda: log.append("prices")))
    monkeypatch.setattr(commercial_composition, "build_commercial_reads",
                        lambda url: SimpleNamespace(months=w["months"], store=w["store"],
                                                    dispose=lambda: log.append("commercial")))
    service = build_structure_read("postgresql://x")
    assert log == []
    # 4a (spec §4.3): the energy source sits in front of the commercial source and serves the stated nodes too.
    from assetops_backend.structure.energy.source import EnergyLeafSource
    assert isinstance(service.read._sources, EnergyLeafSource) and service.read._stated is service.read._sources
    assert isinstance(service.read._sources._fallback, CommercialLeafSource)
    service.dispose()
    assert sorted(log) == ["commercial", "prices", "snapshots"]
