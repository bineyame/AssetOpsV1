"""5a (spec `specs/5a-targets/spec.md` rev 2; rulings D-5A.1 to D-5A.15): the target side, read from budget lines.

Unit 1 (spec §2): `BudgetLineReader`, tests 1 and 2 (test 10 stopped: `mid-build-questions.md` Q1). The world is 3A4's `new_world` (imported, never edited);
every expected value is spec §5's hand-written literal (W2), never computed by the code under test.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from uuid import UUID

import pytest

from assetops_backend.structure.targets.lines import BudgetLineReader, BudgetLines, TargetLine, UnusedLine
from test_3a1_commercial_service import encode
from test_3a4_commercial_months import new_world

TREE = Path(__file__).resolve().parents[2]
FIXTURE = TREE / "backend" / "tests" / "fixtures" / "targets_lakeside.json"
MG = "MINI_GRID"
OCT = "2026-10"
V1, V2 = "budget-2026-v1", "budget-2026-v2"
E = "source-emulated"
GEN, BUD = "assetops-world-generator", "lakeside-budget-2026"
LOADER = "service:ds3-loader"
PERSON_1 = "person:5a000000-0000-4000-8000-000000000001"
PERSON_2 = "person:5a000000-0000-4000-8000-000000000002"
PERSON_1_ID = UUID("5a000000-0000-4000-8000-000000000001")
STEP_1_AT = datetime(2026, 11, 6, 9, 0, tzinfo=timezone.utc)
STEP_2_AT = datetime(2026, 11, 7, 9, 0, tzinfo=timezone.utc)
STEP_3_AT = "2026-11-08T09:00:00+00:00"


# --- the world -----------------------------------------------------------------------------------------------------

def steps() -> list[dict]:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))["steps"]


def ingest(w, at: str, entered_by: str, batch: dict, outcomes=("NEW", "REVISED")) -> UUID:
    w["clock"].now = datetime.fromisoformat(at)
    result = w["svc"].ingest(w["tid"], encode(batch), entered_by=entered_by)
    assert result.state == "STORED" and all(o.outcome in outcomes for o in result.outcomes), result
    return result.intake_id


def load(w: dict, count: int = 2, batches: list[dict] | None = None, names: dict[str, str] | None = None) -> dict:
    """The fixture's first `count` steps into any world (in memory, or Postgres for the `--db` file). `names` maps a
    step's `entered_by` to another (the Postgres workaround of mid-build Q2)."""
    chosen = steps()[:count]
    batches = batches or [s["batch"] for s in chosen]
    names = names or {}
    w["intakes"] = [ingest(w, s["at"], names.get(s["entered_by"], s["entered_by"]), b)
                    for s, b in zip(chosen, batches)]
    w["reader"] = BudgetLineReader(w["months"], w["store"])
    return w


def lakeside(count: int = 2) -> dict:
    return load(new_world(), count)


def site(w, code: str, **kw) -> BudgetLines:
    return w["reader"].site(w["tid"], w["sites"][code], OCT, structure_key=MG, **kw)


def budget_line(site_code: str | None, rid: str, factor: str, value: str, *, version: str = V1,
                line_ref: str | None = None, currency: str | None = "USD", source_version: str = "1") -> dict:
    record = {"format_version": 1, "kind": "BUDGET_LINE", "source_record_id": rid, "source_version": source_version}
    if site_code is not None:
        record["site_code"] = site_code
    record["clocks"] = {"recognition_period": OCT}
    body = {"factor_id": factor, "value": value, "version_ref": version, "line_ref": line_ref or factor}
    if currency is not None:
        body["currency"] = currency
    record["body"] = body
    return record


def budget_batch(records: list[dict], source_system: str = BUD) -> dict:
    return {"format_version": 1, "tenant_code": "lakeside-power", "source_type": "budget_workbook",
            "source_system": source_system, "provenance": E, "produced_at": "2026-11-08T09:00:00+03:00",
            "records": records}


def revision_of(w, source_record_id: str):
    rows = [r for r in w["store"].latest_revisions(w["tid"]) if r.source_record_id == source_record_id]
    assert len(rows) == 1, source_record_id
    return rows[0]


def line_tuple(line: TargetLine) -> tuple:
    return (line.factor_id, line.value, line.currency, line.unit, line.version_ref, line.line_ref, line.provenance,
            line.source_system, line.declared_by, line.person_id, line.declared_at, line.place)


# --- test 1: Kobo's budget lines and their declarers (spec §2, §5; D-5A.1 to D-5A.4, D-5A.14) ---------------------

KOBO_LINES = (
    ("contribution", Decimal("1445.00"), "USD", None, V1, "contribution", E, BUD, PERSON_1, PERSON_1_ID, STEP_2_AT,
     "NODE"),
    ("fuel_cost", Decimal("875.00"), "USD", None, V1, "fuel_cost", E, BUD, PERSON_1, PERSON_1_ID, STEP_2_AT, "NODE"),
    ("om", Decimal("600.00"), "USD", "MONEY", V1, "om", E, GEN, LOADER, None, STEP_1_AT, "LEAF"),
    ("revenue", Decimal("3420.00"), "USD", None, V1, "revenue", E, BUD, PERSON_1, PERSON_1_ID, STEP_2_AT, "NODE"),
    ("staff", Decimal("500.00"), "USD", "MONEY", V1, "staff", E, GEN, LOADER, None, STEP_1_AT, "LEAF"),
)
KOBO_IDS = {"contribution": "BUD-2026-10:KOBO-001:contribution", "fuel_cost": "BUD-2026-10:KOBO-001:fuel_cost",
            "om": "gen:KOBO-001:2026-10:plan:om", "revenue": "BUD-2026-10:KOBO-001:revenue",
            "staff": "gen:KOBO-001:2026-10:plan:staff"}


def test_1a_kobo_budget_lines_field_by_field() -> None:
    check_1a(lakeside())


def check_1a(w: dict, loader: str = LOADER) -> None:
    """`loader` is the step-1 name; the Postgres file passes its workaround name (mid-build Q2)."""
    bl = site(w, "KOBO-001")
    assert bl.site_id == w["sites"]["KOBO-001"] and bl.period == OCT
    assert bl.version_ref == V1 and bl.problem is None
    expected = tuple(tuple(loader if x == LOADER else x for x in row) for row in KOBO_LINES)
    assert tuple(line_tuple(line) for line in bl.lines) == expected
    for line in bl.lines:
        rev = revision_of(w, KOBO_IDS[line.factor_id])
        assert (line.revision_id, line.intake_id) == (rev.id, rev.intake_id)
    assert {line.factor_id: line.intake_id for line in bl.lines}["om"] == w["intakes"][0]
    assert {line.factor_id: line.intake_id for line in bl.lines}["revenue"] == w["intakes"][1]
    assert bl.unused == (UnusedLine("diesel_cost", V1, "diesel_cost", "NOT_A_FACTOR", (BUD,)),)
    assert dict(bl.blocked) == {}
    assert bl.stamp == w["months"].site_month(w["tid"], w["sites"]["KOBO-001"], OCT).stamp
    assert all(type(line.value) is Decimal for line in bl.lines)


def test_1b_an_unchanged_reupload_does_not_redeclare() -> None:  # D-5A.14, plant V14
    w = lakeside()
    ingest(w, STEP_3_AT, PERSON_2, steps()[0]["batch"], outcomes=("UNCHANGED",))
    om = {line.factor_id: line for line in site(w, "KOBO-001").lines}["om"]
    assert (om.declared_by, om.person_id, om.declared_at) == (LOADER, None, STEP_1_AT)


# --- test 2: rules 1 to 4 of spec §2, one case each ----------------------------------------------------------------

def test_2a_two_versions_govern_nothing() -> None:  # rule 1, D-5A.1, plant V2
    w = lakeside()
    ingest(w, STEP_3_AT, PERSON_1, budget_batch([
        budget_line("MTO-001", "BUD-2026-10:MTO-001:revenue-v2", "revenue", "2300.00", version=V2)]))
    bl = site(w, "MTO-001")
    assert bl.problem == "BUDGET_VERSIONS:budget-2026-v1,budget-2026-v2"
    assert bl.version_ref is None and bl.lines == ()
    assert dict(bl.blocked) == {"om": "BUDGET_VERSIONS", "staff": "BUDGET_VERSIONS", "revenue": "BUDGET_VERSIONS",
                                "fuel_cost": "BUDGET_VERSIONS", "contribution": "BUDGET_VERSIONS"}
    assert bl.unused == (
        UnusedLine("contribution", V1, "contribution", "BUDGET_VERSIONS", (BUD,)),
        UnusedLine("fuel_cost", V1, "fuel_cost", "BUDGET_VERSIONS", (BUD,)),
        UnusedLine("om", V1, "om", "BUDGET_VERSIONS", (GEN,)),
        UnusedLine("revenue", V1, "revenue", "BUDGET_VERSIONS", (BUD,)),
        UnusedLine("revenue", V2, "revenue", "BUDGET_VERSIONS", (BUD,)),
        UnusedLine("staff", V1, "staff", "BUDGET_VERSIONS", (GEN,)),
    )
    assert site(w, "KOBO-001").version_ref == V1  # the other Sites keep their one version


def test_2a_a_non_factor_in_a_second_version_still_blocks() -> None:  # rule 1 before rule 2 (handshake R7)
    w = lakeside()
    ingest(w, STEP_3_AT, PERSON_1, budget_batch([
        budget_line("KOBO-001", "BUD-2026-10:KOBO-001:diesel_cost-v2", "diesel_cost", "900.00", version=V2)]))
    bl = site(w, "KOBO-001")
    assert bl.problem == "BUDGET_VERSIONS:budget-2026-v1,budget-2026-v2" and bl.lines == ()
    assert set(bl.blocked) == {"contribution", "fuel_cost", "om", "revenue", "staff"}  # never `diesel_cost`
    assert {u.reason for u in bl.unused} == {"BUDGET_VERSIONS"} and len(bl.unused) == 7


def test_2b_two_lines_for_one_factor_are_never_summed() -> None:  # rule 3, D-5A.3, plant V1
    w = lakeside()
    ingest(w, STEP_3_AT, PERSON_1, budget_batch([
        budget_line("KOBO-001", "BUD-2026-10:KOBO-001:om-extra", "om", "50.00", line_ref="om-extra")]))
    bl = site(w, "KOBO-001")
    assert dict(bl.blocked) == {"om": "DUPLICATE_DECLARATION"}
    assert [line.factor_id for line in bl.lines] == ["contribution", "fuel_cost", "revenue", "staff"]
    assert bl.unused == (
        UnusedLine("diesel_cost", V1, "diesel_cost", "NOT_A_FACTOR", (BUD,)),
        UnusedLine("om", V1, "om", "DUPLICATE_DECLARATION", (GEN,)),
        UnusedLine("om", V1, "om-extra", "DUPLICATE_DECLARATION", (BUD,)),
    )


def test_2b_a_3a4_duplicate_declaration_is_blocked() -> None:  # rule 3: one line whose value is None
    w = lakeside()
    ingest(w, STEP_3_AT, PERSON_1, budget_batch([
        budget_line("KOBO-001", "BUD-2026-10:KOBO-001:om", "om", "650.00")]))  # same key as DS1b's om line
    bl = site(w, "KOBO-001")
    assert dict(bl.blocked) == {"om": "DUPLICATE_DECLARATION"}
    assert "om" not in [line.factor_id for line in bl.lines]
    assert [u for u in bl.unused if u.factor_id == "om"] == [
        UnusedLine("om", V1, "om", "DUPLICATE_DECLARATION", (GEN, BUD))]


def test_2c_a_money_line_without_currency() -> None:  # rule 4
    w = lakeside()
    ingest(w, STEP_3_AT, PERSON_1, budget_batch([
        budget_line("KOBO-001", "BUD-2026-10:KOBO-001:revenue", "revenue", "3420.00", currency=None,
                    source_version="2")]))
    bl = site(w, "KOBO-001")
    assert dict(bl.blocked) == {"revenue": "CURRENCY_MISSING"}
    assert "revenue" not in [line.factor_id for line in bl.lines]
    assert UnusedLine("revenue", V1, "revenue", "CURRENCY_MISSING", (BUD,)) in bl.unused


def test_2c_a_quantity_line_with_a_currency() -> None:  # rule 4
    w = lakeside()
    ingest(w, STEP_3_AT, PERSON_1, budget_batch([
        budget_line("KOBO-001", "BUD-2026-10:KOBO-001:diesel_l", "diesel_l", "700")]))  # a node: canonical allows it
    bl = site(w, "KOBO-001")
    assert dict(bl.blocked) == {"diesel_l": "CURRENCY_ON_QUANTITY"}
    assert UnusedLine("diesel_l", V1, "diesel_l", "CURRENCY_ON_QUANTITY", (BUD,)) in bl.unused


def test_2d_the_portfolio_read() -> None:
    w = lakeside()
    bl = w["reader"].portfolio(w["tid"], OCT, structure_key=MG)
    assert bl.site_id is None and bl.period == OCT and bl.version_ref == V1 and bl.problem is None
    assert tuple(line_tuple(line) for line in bl.lines) == (
        ("staff", Decimal("1200.00"), "USD", "MONEY", V1, "staff", E, BUD, PERSON_1, PERSON_1_ID, STEP_2_AT, "LEAF"),)
    assert bl.lines[0].revision_id == revision_of(w, "BUD-2026-10:PORTFOLIO:staff").id
    assert bl.unused == () and dict(bl.blocked) == {}
    assert bl.stamp == w["months"].portfolio_month(w["tid"], OCT).stamp


def test_2_known_at_before_step_2() -> None:  # the cutoff reaches the declarer join too
    w = lakeside()
    bl = site(w, "KOBO-001", known_at=datetime(2026, 11, 6, 12, 0, tzinfo=timezone.utc))
    assert [(line.factor_id, line.declared_by) for line in bl.lines] == [("om", LOADER), ("staff", LOADER)]
    assert bl.unused == ()


def test_2_known_at_declarer_join_honours_the_cutoff() -> None:  # review r1 F1: the join carries no value
    w = lakeside()
    ingest(w, STEP_3_AT, PERSON_2, budget_batch([
        budget_line("KOBO-001", "gen:KOBO-001:2026-10:plan:om", "om", "650.00", source_version="2")],
        source_system=GEN))
    rev1 = [r for r in w["store"].latest_revisions(w["tid"], known_at=datetime(2026, 11, 7, 12, 0, tzinfo=timezone.utc))
            if r.source_record_id == "gen:KOBO-001:2026-10:plan:om"]
    assert len(rev1) == 1
    before = {line.factor_id: line for line in
              site(w, "KOBO-001", known_at=datetime(2026, 11, 7, 12, 0, tzinfo=timezone.utc)).lines}["om"]
    assert (before.value, before.declared_by, before.person_id, before.declared_at) == (
        Decimal("600.00"), LOADER, None, STEP_1_AT)
    assert before.revision_id == rev1[0].id and before.intake_id == w["intakes"][0]
    after = {line.factor_id: line for line in site(w, "KOBO-001").lines}["om"]
    assert (after.value, after.declared_by) == (Decimal("650.00"), PERSON_2)
    assert after.revision_id != before.revision_id


def test_2_a_person_id_only_when_the_whole_name_is_one() -> None:  # review r1 residual: fullmatch, not search
    w = lakeside()
    odd = "imported-by " + PERSON_1
    ingest(w, STEP_3_AT, odd, budget_batch([
        budget_line("KOBO-001", "gen:KOBO-001:2026-10:plan:om", "om", "650.00", source_version="2")],
        source_system=GEN))
    om = {line.factor_id: line for line in site(w, "KOBO-001").lines}["om"]
    assert (om.declared_by, om.person_id) == (odd, None)


def test_2_an_intake_that_is_gone_is_a_bug() -> None:  # spec §2 (P1): `None` raises
    w = lakeside()
    w["store"].intakes[:] = [i for i in w["store"].intakes if i.id != w["intakes"][0]]
    with pytest.raises(RuntimeError, match="budget line without its intake"):
        site(w, "KOBO-001")


# === units 2 and 3 (spec §3, §4, §5, §6 tests 3 to 9 and 11) =========================================================

import dataclasses  # noqa: E402

from assetops_backend.chain.ports import SiteRef  # noqa: E402
from assetops_backend.structure.check import StructureError  # noqa: E402
from assetops_backend.structure.evaluate import ORIGIN_UNKNOWN, LeafValue, Missing, blocks_of  # noqa: E402
from assetops_backend.structure.read import StructureRead, site_count  # noqa: E402
from assetops_backend.structure.registry import REGISTRIES, FactorRow, FilledBy, Registry  # noqa: E402
from assetops_backend.structure.sources import ASSUMPTION_WORDS  # noqa: E402
from assetops_backend.structure.targets import rules as target_rules  # noqa: E402
from assetops_backend.structure.targets.read import TargetCheck, TargetRead  # noqa: E402
from assetops_contracts.canonical.units import KWH, MONEY  # noqa: E402

REG = REGISTRIES[MG]
TZ = "Africa/Nairobi"
USD = "USD"
CODES = ("KOBO-001", "KISIWA-001", "MTO-001")
#: Spec §3.1's literals, byte for byte (W2): the module's are compared with these, never the other way round.
WORDS = "Budget line for the month"
LEAK_T = "No target line: taken at zero (assumption)"
AT_ACTUAL_T = "No target line: taken at this month's actual, so no gap is put on it (assumption)"
MAIN_T = "No target line: the rest of the heading's target, on its main factor (assumption)"
D = Decimal


def absent_m(cause: str, note: str | None) -> Missing:
    return Missing("BUDGET_LINE", "COMMERCIAL_RECORD", cause, None, (), WORDS, None, note)


def assumed_m(text: str) -> Missing:
    return Missing("BUDGET_LINE", "COMMERCIAL_RECORD", "NOT_RECEIVED", "ASSUMPTION", (), WORDS, text, None)


# --- the actual side: spec §5's FakeActual ----------------------------------------------------------------------------

_ACTUAL = {  # per Site: om (Kisiwa absent), staff, diesel_price
    "KOBO-001": ("600.00", "500.00", "1.25"),
    "KISIWA-001": (None, "500.00", "1.30"),
    "MTO-001": ("500.00", "450.00", "1.25"),
}


def _actual_absent(leaf: str, cause: str = "NOT_CONNECTED") -> LeafValue:
    fb = REG.row(leaf).filled_by
    return LeafValue(None, "NOT_AVAILABLE", (), None, Missing(fb.kind, fb.family, cause, None, (), fb.words, None),
                     None)


def actual_assumed(leaf: str, value: str) -> LeafValue:
    """3B3's ASSUMED form (sources.py `_price`): ESTIMATED, carried as ASSUMPTION, USD, origin unknown."""
    fb = REG.row(leaf).filled_by
    return LeafValue(D(value), "ESTIMATED", ("assumption:price",), None,
                     Missing(fb.kind, fb.family, "NOT_CONNECTED", "ASSUMPTION", (), fb.words, ASSUMPTION_WORDS.get(
                         leaf, "Declared price"), None), USD, (ORIGIN_UNKNOWN,))


class FakeActual:
    def __init__(self, overrides: dict[str, dict[str, LeafValue]] | None = None) -> None:
        self.overrides = overrides or {}

    def leaf(self, ctx, factor_id: str) -> LeafValue:
        code = ctx.site.site_code
        if factor_id in self.overrides.get(code, {}):
            return self.overrides[code][factor_id]
        row = REG.row(factor_id)
        om, staff, price = _ACTUAL[code]
        if row.absent == "OPTION_ONLY":
            return LeafValue(row.neutral, "NEUTRAL", ("option-only neutral",), None, None, None)
        if factor_id == "period_days":
            return LeafValue(D("31"), "DERIVED", ("calendar",), None, None, None)
        if factor_id == "productive_kwh":
            return LeafValue(D("0"), "RECORDED", ("charge",), None, None, None, (E,))
        if factor_id == "diesel_price":
            return actual_assumed("diesel_price", price)
        if factor_id in ("om", "staff"):
            value = om if factor_id == "om" else staff
            if value is None:
                return _actual_absent(factor_id, "NOT_RECEIVED")
            return LeafValue(D(value), "RECORDED", (f"expense:{factor_id}",), None, None, USD, (E,))
        return _actual_absent(factor_id)


def refs(w: dict) -> dict[str, SiteRef]:
    return {c: SiteRef(w["tid"], w["sites"][c], c, "MINIGRID", TZ) for c in CODES}


def targets(w: dict, overrides=None) -> TargetRead:
    return TargetRead(w["reader"], StructureRead(FakeActual(overrides)))


def read_site(w: dict, code: str, overrides=None, **kw):
    return targets(w, overrides).site(refs(w)[code], OCT, **kw)


def read_portfolio(w: dict, overrides=None, **kw):
    r = refs(w)
    return targets(w, overrides).portfolio(w["tid"], [r[c] for c in CODES], OCT, **kw)


# --- spec §5's tables (hand-computed literals) ------------------------------------------------------------------------

A_ = lambda text: ("A", text)  # noqa: E731 - an assumption with its words
X_ = lambda note, cause="NOT_RECEIVED": ("X", cause, note)  # noqa: E731 - absent, with its cause and note

#: Kobo's 31 leaves: (value, evidence, sources or None when a line's, currency, missing).
KOBO_LEAVES = {
    "delivered_kwh": (None, "NOT_AVAILABLE", (), None, X_("MAIN_FACTOR_UNSOLVED:revenue")),
    "technical_loss_kwh": (D("0"), "ESTIMATED", ("assumption:zero",), None, A_(LEAK_T)),
    "unexplained_loss_kwh": (D("0"), "ESTIMATED", ("assumption:zero",), None, A_(LEAK_T)),
    "adjustments_kwh": (D("0"), "ESTIMATED", ("assumption:zero",), None, A_(LEAK_T)),
    "unmapped_kwh": (D("0"), "ESTIMATED", ("assumption:zero",), None, A_(LEAK_T)),
    "tariff": (None, "NOT_AVAILABLE", (), None, X_("ACTUAL_NOT_AVAILABLE")),
    "productive_kwh": (D("0"), "ESTIMATED", ("assumption:at-actual",), None, A_(AT_ACTUAL_T)),
    "productive_tariff": (None, "NOT_AVAILABLE", (), None, X_("ACTUAL_NOT_AVAILABLE")),
    "in_transit": (D("0"), "ESTIMATED", ("assumption:zero",), USD, A_(LEAK_T)),
    "outstanding": (D("0"), "ESTIMATED", ("assumption:zero",), USD, A_(LEAK_T)),
    "necessary_l": (D("700"), "ESTIMATED", ("assumption:main-factor:fuel_cost",), None, A_(MAIN_T)),
    "candidate_l": (D("0"), "ESTIMATED", ("assumption:zero",), None, A_(LEAK_T)),
    "unexplained_l": (D("0"), "ESTIMATED", ("assumption:zero",), None, A_(LEAK_T)),
    "extra_l": (D("0"), "NEUTRAL", ("option-only neutral",), None, None),
    "diesel_price": (D("1.25"), "ESTIMATED", ("assumption:at-actual",), USD, A_(AT_ACTUAL_T)),
    "battery_throughput_kwh": (D("0"), "NEUTRAL", ("option-only neutral",), None, None),
    "wear_rate": (None, "NOT_AVAILABLE", (), None, X_("ACTUAL_NOT_AVAILABLE")),
    "om": (D("600.00"), "DECLARED", None, USD, None),
    "staff": (D("500.00"), "DECLARED", None, USD, None),
    "collection_cost": (D("0"), "NEUTRAL", ("option-only neutral",), None, None),
    "reduced_days": (D("0"), "ESTIMATED", ("assumption:zero",), None, A_(LEAK_T)),
    "hours_per_day": (None, "NOT_AVAILABLE", (), None, X_("ACTUAL_NOT_AVAILABLE")),
    "major_assets": (None, "NOT_AVAILABLE", (), None, X_("ACTUAL_NOT_AVAILABLE")),
    "unserved_critical_kwh": (D("0"), "ESTIMATED", ("assumption:zero",), None, A_(LEAK_T)),
    "customer_hours_interrupted": (D("0"), "ESTIMATED", ("assumption:zero",), None, A_(LEAK_T)),
    "field_visits": (D("0"), "ESTIMATED", ("assumption:zero",), None, A_(LEAK_T)),
    "liability": (D("0"), "ESTIMATED", ("assumption:zero",), USD, A_(LEAK_T)),
    "period_days": (D("31"), "DERIVED", ("calendar",), None, None),
    "standby_kw": (None, "NOT_AVAILABLE", (), None, X_("ACTUAL_NOT_AVAILABLE")),
    "lost_unit_kw": (None, "NOT_AVAILABLE", (), None, X_("ACTUAL_NOT_AVAILABLE")),
    "dawn_days_below": (D("0"), "ESTIMATED", ("assumption:zero",), None, A_(LEAK_T)),
}
SITE_LEAVES = {
    "KOBO-001": KOBO_LEAVES,
    "KISIWA-001": {**KOBO_LEAVES, "om": (D("700.00"), "DECLARED", None, USD, None),
                   "necessary_l": (D("2300"),) + KOBO_LEAVES["necessary_l"][1:],
                   "diesel_price": (D("1.30"),) + KOBO_LEAVES["diesel_price"][1:]},
    "MTO-001": {**KOBO_LEAVES, "om": (D("500.00"), "DECLARED", None, USD, None),
                "staff": (D("450.00"), "DECLARED", None, USD, None),
                "necessary_l": (D("300"),) + KOBO_LEAVES["necessary_l"][1:]},
}
#: Nodes: (value as text or None, evidence, assumed_leaves, stated, computed as text or None).
SITE_NODES = {
    "KOBO-001": {
        "revenue": ("3420.00", "DECLARED", (), True, None),
        "fuel_cost": ("875.00", "DECLARED", (), True, "875.00"),
        "diesel_l": ("700", "ESTIMATED", ("candidate_l", "necessary_l", "unexplained_l"), False, None),
        "collected": ("3420.00", "ESTIMATED", ("in_transit", "outstanding"), False, None),
        "cost_to_serve": ("1975.00", "DECLARED", (), False, None),
        "contribution": ("1445.00", "DECLARED", (), False, None),
    },
    "KISIWA-001": {
        "revenue": ("4125.00", "DECLARED", (), True, None),
        "fuel_cost": ("2990.00", "DECLARED", (), True, "2990.00"),
        "diesel_l": ("2300", "ESTIMATED", ("candidate_l", "necessary_l", "unexplained_l"), False, None),
        "collected": ("4125.00", "ESTIMATED", ("in_transit", "outstanding"), False, None),
        "cost_to_serve": ("4190.00", "DECLARED", (), False, None),
        "contribution": ("-65.00", "DECLARED", (), False, None),
    },
    "MTO-001": {
        "revenue": ("2240.00", "DECLARED", (), True, None),
        "fuel_cost": ("375.00", "DECLARED", (), True, "375.00"),
        "diesel_l": ("300", "ESTIMATED", ("candidate_l", "necessary_l", "unexplained_l"), False, None),
        "collected": ("2240.00", "ESTIMATED", ("in_transit", "outstanding"), False, None),
        "cost_to_serve": ("1325.00", "DECLARED", (), False, None),
        "contribution": ("915.00", "DECLARED", (), False, None),
    },
}
SITE_CHECKS = {
    "KOBO-001": (TargetCheck("contribution", D("1445.00"), D("1445.00"), USD, True),),
    "KISIWA-001": (TargetCheck("contribution", D("-60.00"), D("-65.00"), USD, False),),
    "MTO-001": (TargetCheck("contribution", D("915.00"), D("915.00"), USD, True),),
}
STATED_IDS = {"KOBO-001": "BUD-2026-10:KOBO-001:", "KISIWA-001": "BUD-2026-10:KISIWA-001:",
              "MTO-001": "BUD-2026-10:MTO-001:"}


def assert_missing(fv, expected) -> None:
    """The `Missing` of a target, field by field; `blocks` are the evaluator's (P6)."""
    if expected is None:
        assert fv.missing is None, fv
        return
    m = absent_m(expected[1], expected[2]) if expected[0] == "X" else assumed_m(expected[1])
    assert dataclasses.replace(fv.missing, blocks=()) == m, (fv.factor_id, fv.missing)
    assert fv.missing.blocks == blocks_of(REG, (fv.factor_id,))


def check_site_tables(w: dict, code: str) -> None:
    """Spec §5's table for one Site, every named field (test 3(a))."""
    st = read_site(w, code)
    v = st.structure.values
    assert (st.structure.site_code, st.structure.month, st.structure.structure_key, st.structure.structure_version) \
        == (code, OCT, MG, REG.version)
    assert st.currency == USD and st.lines.version_ref == V1
    for leaf, (value, evidence, sources, currency, missing) in SITE_LEAVES[code].items():
        fv = v[leaf]
        assert (fv.value, fv.evidence, fv.currency) == (value, evidence, currency), (code, leaf, fv)
        assert value is None or type(fv.value) is Decimal
        if sources is None:  # a line's own target names its revision and its record provenance
            gen = f"gen:{code}:2026-10:plan:{leaf}"
            assert fv.sources == (f"budget:{revision_of(w, gen).id}",) and fv.origins == (E,), (code, leaf)
        else:
            assert fv.sources == sources, (code, leaf, fv.sources)
        assert_missing(fv, missing)
    for node, (value, evidence, assumed, stated, computed) in SITE_NODES[code].items():
        fv = v[node]
        assert fv.value == D(value) and format(fv.value, "f") == value, (code, node, fv.value)
        assert (fv.evidence, fv.assumed_leaves, fv.stated, fv.currency) == \
            (evidence, assumed, stated, None if node == "diesel_l" else USD), (code, node, fv)
        if computed is not None:
            assert fv.computed == D(computed) and fv.detail_missing == (), (code, node)
    for heading in ("revenue", "fuel_cost"):  # a stated heading names its own line
        assert v[heading].sources == (f"budget:{revision_of(w, STATED_IDS[code] + heading).id}",)
        assert v[heading].missing is None and v[heading].origins == (E,)
    assert v["revenue"].detail_missing == ("delivered_kwh", "productive_tariff", "tariff")
    assert v["contribution"].missing_leaves == () and v["contribution"].origins == (E,)
    assert st.checks == SITE_CHECKS[code]


def test_3a_kobo_kisiwa_mto_targets() -> None:  # spec §5; plants V3, V4, V5, V6, V10, V11
    w = lakeside()
    for code in CODES:
        check_site_tables(w, code)


def test_3a_kobo_lines_and_declarers_on_the_target_read() -> None:
    w = lakeside()
    st = read_site(w, "KOBO-001")
    assert [line.factor_id for line in st.lines.lines] == ["contribution", "fuel_cost", "om", "revenue", "staff"]
    assert st.lines.unused == (UnusedLine("diesel_cost", V1, "diesel_cost", "NOT_A_FACTOR", (BUD,)),)


def test_3a_origins_of_assumptions() -> None:  # D-4B.18: every valued assumption names an origin; unknown weakest
    w = lakeside()
    v = read_site(w, "KOBO-001").structure.values
    assert v["in_transit"].origins == (ORIGIN_UNKNOWN,)  # a zero rests on no record
    assert v["diesel_price"].origins == (ORIGIN_UNKNOWN,)  # the actual's own (a declared price)
    assert v["productive_kwh"].origins == (E,)  # the actual's own (a record)
    assert v["necessary_l"].origins == (E, ORIGIN_UNKNOWN)  # its heading's line and diesel_price
    assert v["collected"].origins == (E, ORIGIN_UNKNOWN)
    assert v["period_days"].origins == () and v["extra_l"].origins == ()


def test_3b_a_cost_without_a_line_is_taken_at_its_actual() -> None:  # D-5A.15, plant V10
    batch = json.loads(json.dumps(steps()[0]["batch"]))
    batch["records"] = [r for r in batch["records"] if r["source_record_id"] != "gen:MTO-001:2026-10:plan:staff"]
    w = load(new_world(), 2, [batch, steps()[1]["batch"]])
    st = read_site(w, "MTO-001")
    v = st.structure.values
    assert (v["staff"].value, v["staff"].evidence, v["staff"].sources, v["staff"].currency) == \
        (D("450.00"), "ESTIMATED", ("assumption:at-actual",), USD)
    assert_missing(v["staff"], A_(AT_ACTUAL_T))
    assert v["staff"].origins == (E,)
    assert (v["cost_to_serve"].value, v["cost_to_serve"].evidence) == (D("1325.00"), "ESTIMATED")
    assert (v["contribution"].value, v["contribution"].evidence) == (D("915.00"), "ESTIMATED")
    assert v["contribution"].assumed_leaves == ("staff",)
    assert st.checks == SITE_CHECKS["MTO-001"]


def test_3_refusals() -> None:
    w = lakeside()
    cold = SiteRef(w["tid"], w["sites"]["KOBO-001"], "KOBO-001", "COLDCHAIN", TZ)
    with pytest.raises(StructureError) as e:
        targets(w).site(cold, OCT)
    assert (e.value.code, e.value.factor_id) == ("STRUCTURE_KEY_NOT_READ", "KOBO-001")
    with pytest.raises(ValueError) as bad:
        targets(w).site(refs(w)["KOBO-001"], "2026-13")
    assert not isinstance(bad.value, StructureError)


# --- test 4: the rules are the spec's table ---------------------------------------------------------------------------

RULE_TABLE = {
    "LEAK_ZERO": ("technical_loss_kwh", "unexplained_loss_kwh", "adjustments_kwh", "unmapped_kwh", "in_transit",
                  "outstanding", "candidate_l", "unexplained_l", "reduced_days", "unserved_critical_kwh",
                  "customer_hours_interrupted", "field_visits", "liability", "dawn_days_below"),
    "AT_ACTUAL": ("tariff", "productive_kwh", "productive_tariff", "diesel_price", "wear_rate", "om", "staff",
                  "hours_per_day", "major_assets", "standby_kw", "lost_unit_kw"),
    "MAIN": ("delivered_kwh", "necessary_l"),
    "OPTION": ("extra_l", "battery_throughput_kwh", "collection_cost"),
    "CALENDAR": ("period_days",),
}


def test_4_the_rule_table() -> None:
    expected = {leaf: rule for rule, leaves in RULE_TABLE.items() for leaf in leaves}
    assert dict(target_rules.TARGET_RULE[MG]) == expected
    assert {k: dict(v) for k, v in target_rules.MAIN_OF.items()} == {
        MG: {"delivered_kwh": ("billed_kwh", "revenue"), "necessary_l": ("fuel_cost",)}}
    leaves = {r.factor_id for r in REG.rows if r.is_leaf}
    assert len(leaves) == 31 and set(expected) == leaves and len(expected) == 31
    assert set(RULE_TABLE["OPTION"]) == {r.factor_id for r in REG.rows if r.absent == "OPTION_ONLY"}
    assert set(RULE_TABLE["CALENDAR"]) == {r.factor_id for r in REG.rows if r.absent == "NEVER_EMPTY"}
    for leaf, headings in target_rules.MAIN_OF[MG].items():
        for heading in headings:
            assert REG.row(heading).stated_by is not None and heading in blocks_of(REG, (leaf,))
    assert target_rules.RULES == ("LEAK_ZERO", "AT_ACTUAL", "MAIN", "OPTION", "CALENDAR")
    assert (target_rules.TARGET_KIND, target_rules.TARGET_FAMILY, target_rules.TARGET_WORDS) == \
        ("BUDGET_LINE", "COMMERCIAL_RECORD", WORDS)
    assert (target_rules.LEAK_TEXT, target_rules.AT_ACTUAL_TEXT, target_rules.MAIN_TEXT) == (LEAK_T, AT_ACTUAL_T, MAIN_T)


# --- test 5: the main solve -------------------------------------------------------------------------------------------

PRICED = {"KOBO-001": {"tariff": actual_assumed("tariff", "0.40"),
                       "productive_tariff": actual_assumed("productive_tariff", "0.30")}}


def test_5a_delivered_kwh_is_solved_when_the_prices_are_known() -> None:
    w = lakeside()
    v = read_site(w, "KOBO-001", PRICED).structure.values
    assert (v["delivered_kwh"].value, v["delivered_kwh"].evidence) == (D("8550"), "ESTIMATED")
    assert v["delivered_kwh"].sources == ("assumption:main-factor:revenue",)
    assert_missing(v["delivered_kwh"], A_(MAIN_T))
    assert v["revenue"].computed == D("3420.00") and v["revenue"].value == D("3420.00")


def _toy(expression: str) -> Registry:
    """A planted two-leaf registry, built without `check`."""
    rows = (FactorRow("x", None, KWH, None, FilledBy("READING", "x", None), "MISSING", None, composes="SUM"),
            FactorRow("p", None, MONEY / KWH, None, FilledBy("DECLARED", "p", None), "MISSING", None,
                      composes="NONE"),
            FactorRow("y", expression, MONEY, None, None, None, None, composes="SUM",
                      stated_by=FilledBy("COMMERCIAL_RECORD", "CHARGE", None)))
    return Registry("TOY", 1, rows)


def _toy_leaves(p: str) -> dict[str, LeafValue]:
    return {"x": LeafValue(None, "NOT_AVAILABLE", (), None,
                           Missing("x", "READING", "NOT_RECEIVED", None, (), None, None), None),
            "p": LeafValue(D(p), "DECLARED", ("p",), None, None, USD, (E,))}


def test_5b_a_nonlinear_heading_is_not_solved() -> None:  # plant V8
    assert target_rules.solve_main(_toy("x * x * p"), _toy_leaves("0.40"), "y", "x", D("10")) == \
        (None, "MAIN_FACTOR_NONLINEAR:y")


def test_5c_a_zero_slope_is_not_solved() -> None:  # plant V8
    assert target_rules.solve_main(_toy("x * p"), _toy_leaves("0"), "y", "x", D("10")) == \
        (None, "MAIN_FACTOR_ZERO_SLOPE:y")


def test_5_control_a_linear_heading_is_solved_exactly() -> None:
    assert target_rules.solve_main(_toy("x * p"), _toy_leaves("0.40"), "y", "x", D("10")) == (D("25"), None)


# --- test 6: the portfolio ---------------------------------------------------------------------------------------------

PACK = TREE / "Docs" / "demo-sprint" / "product-direction-layer4" / "derived-values.json"
PORTFOLIO = {  # factor: (value, evidence)
    "contribution": ("2295.00", "DECLARED"), "revenue": ("9785.00", "DECLARED"), "fuel_cost": ("4240.00", "DECLARED"),
    "om": ("1800.00", "DECLARED"), "staff": ("1450.00", "DECLARED"), "cost_to_serve": ("7490.00", "DECLARED"),
    "diesel_l": ("3300", "ESTIMATED"), "necessary_l": ("3300", "ESTIMATED"), "collected": ("9785.00", "ESTIMATED"),
}


def check_portfolio(w: dict) -> None:
    pt = read_portfolio(w)
    values = pt.structure.composition.values
    assert tuple(pt.sites) == CODES and pt.structure.sites == CODES
    for factor, (value, evidence) in PORTFOLIO.items():
        fv = values[factor].value
        assert fv.value == D(value) and format(fv.value, "f") == value, (factor, fv.value)
        assert fv.evidence == evidence, (factor, fv.evidence)
        count = site_count(pt.structure, factor)
        assert (count.k, count.n, count.out) == (3, 3, ()), factor
    assert values["contribution"].value.origins == (E,)
    sums = json.loads(PACK.read_text(encoding="utf-8"))["portfolio"]["lakeside-power"]["plan"]["sums"]
    cent = D("0.01")
    for factor in PORTFOLIO:
        assert D(str(sums[factor])).quantize(cent) == values[factor].value.value.quantize(cent), factor
    pl = pt.portfolio_lines
    assert [(line.factor_id, line.value, line.person_id) for line in pl.lines] == [("staff", D("1200.00"),
                                                                                    PERSON_1_ID)]


def test_6_the_portfolio_is_2295_3_of_3() -> None:  # plants V5, V6, V7
    check_portfolio(lakeside())


def test_6_refusals_and_other_types() -> None:
    w = lakeside()
    r = refs(w)
    for tenant, asked in ((w["tid"], [r["KOBO-001"], r["KOBO-001"]]),
                          (w["tenants"]["harvest-cold"], [r["KOBO-001"]])):
        with pytest.raises(StructureError) as e:
            targets(w).portfolio(tenant, asked, OCT)
        assert (e.value.code, e.value.factor_id) == ("STRUCTURE_COMPOSE", "KOBO-001")
    with pytest.raises(ValueError) as bad:
        targets(w).portfolio(w["tid"], [r["KOBO-001"]], "2026-1")
    assert not isinstance(bad.value, StructureError)
    cold = SiteRef(w["tid"], w["sites"]["KISIWA-001"], "KISIWA-001", "COLDCHAIN", TZ)
    pt = targets(w).portfolio(w["tid"], [r["KOBO-001"], cold], OCT)
    assert tuple(pt.sites) == ("KOBO-001",)
    assert dict(pt.structure.composition.sites_excluded) == {"KISIWA-001": ("STRUCTURE_OTHER_KEY",)}
    count = site_count(pt.structure, "contribution")
    assert (count.k, count.n, count.out) == (1, 2, (("KISIWA-001", ("STRUCTURE_OTHER_KEY",)),))


# --- tests 7 to 9 -----------------------------------------------------------------------------------------------------

def _second_version(w: dict) -> None:
    ingest(w, STEP_3_AT, PERSON_1, budget_batch([
        budget_line("MTO-001", "BUD-2026-10:MTO-001:revenue-v2", "revenue", "2300.00", version=V2)]))


def test_7_k_of_n_with_a_gap() -> None:  # plants V2, V13
    w = lakeside()
    _second_version(w)
    pt = read_portfolio(w)
    fv = pt.structure.composition.values["contribution"].value
    assert fv.value == D("1380.00") and format(fv.value, "f") == "1380.00" and fv.evidence == "DECLARED"
    count = site_count(pt.structure, "contribution")
    assert (count.k, count.n) == (2, 3)
    assert count.out == (("MTO-001", ("billed_kwh", "delivered_kwh", "fuel_cost", "metered_kwh", "necessary_l", "om",
                                      "productive_tariff", "revenue", "staff", "tariff")),)  # 4a: stated kWh nodes
    mto = pt.sites["MTO-001"].structure.values
    for factor in ("om", "staff", "revenue", "fuel_cost"):
        assert mto[factor].value is None
        assert dataclasses.replace(mto[factor].missing, blocks=()) == absent_m("NOT_CALCULATED_YET",
                                                                               "BUDGET_VERSIONS"), factor
    assert pt.sites["MTO-001"].checks == ()


def _om_extra(w: dict) -> None:
    ingest(w, STEP_3_AT, PERSON_1, budget_batch([
        budget_line("KOBO-001", "BUD-2026-10:KOBO-001:om-extra", "om", "50.00", line_ref="om-extra")]))


def test_8a_a_blocked_leaf_is_unknown_never_zero() -> None:  # plants V1, V11, V12
    w = lakeside()
    _om_extra(w)
    v = read_site(w, "KOBO-001").structure.values
    assert (v["om"].value, v["om"].evidence) == (None, "NOT_AVAILABLE")
    assert_missing(v["om"], X_("DUPLICATE_DECLARATION", "NOT_CALCULATED_YET"))
    assert v["contribution"].value is None and v["contribution"].missing_leaves == ("om",)
    assert v["cost_to_serve"].value is None


def test_8d_two_currencies_leave_the_money_leaks_unknown() -> None:  # D-5A.10, review r1 F1
    w = lakeside()
    ingest(w, STEP_3_AT, PERSON_1, budget_batch([
        budget_line("KOBO-001", "BUD-2026-10:KOBO-001:fuel_cost", "fuel_cost", "875.00", currency="EUR",
                    source_version="2")]))
    st = read_site(w, "KOBO-001")
    assert st.currency is None
    v = st.structure.values
    for leaf in ("in_transit", "outstanding", "liability"):
        assert v[leaf].value is None, leaf
        assert_missing(v[leaf], X_("TARGET_CURRENCY_UNKNOWN"))
    assert (v["technical_loss_kwh"].value, v["technical_loss_kwh"].evidence) == (D("0"), "ESTIMATED")


def test_8b_no_actual_price_leaves_the_main_factor_unsolved() -> None:  # plant V11
    w = lakeside()
    v = read_site(w, "KOBO-001", {"KOBO-001": {"diesel_price": _actual_absent("diesel_price")}}).structure.values
    assert_missing(v["diesel_price"], X_("ACTUAL_NOT_AVAILABLE"))
    assert v["necessary_l"].value is None
    assert_missing(v["necessary_l"], X_("MAIN_FACTOR_UNSOLVED:fuel_cost"))
    assert v["fuel_cost"].value == D("875.00") and v["fuel_cost"].evidence == "DECLARED"


def test_8c_a_blocked_heading_stays_absent() -> None:  # D-5A.13, plant V15
    w = lakeside()
    ingest(w, STEP_3_AT, PERSON_1, budget_batch([
        budget_line("KOBO-001", "BUD-2026-10:KOBO-001:delivered_kwh", "delivered_kwh", "8550", currency=None)]))
    v = read_site(w, "KOBO-001", PRICED).structure.values
    assert v["revenue"].value == D("3420.00") and v["revenue"].computed is not None  # control
    assert v["delivered_kwh"].evidence == "DECLARED"
    ingest(w, "2026-11-09T09:00:00+00:00", PERSON_1, budget_batch([
        budget_line("KOBO-001", "BUD-2026-10:KOBO-001:revenue-extra", "revenue", "100.00", line_ref="revenue-extra")]))
    v = read_site(w, "KOBO-001", PRICED).structure.values
    assert v["revenue"].value is None and v["revenue"].computed is None
    assert v["revenue"].missing.cause == "NOT_CALCULATED_YET"
    assert v["revenue"].missing.note == "DUPLICATE_DECLARATION"


def test_9_known_at_before_step_2() -> None:
    w = lakeside()
    st = read_site(w, "KOBO-001", known_at=datetime(2026, 11, 6, 12, 0, tzinfo=timezone.utc))
    v = st.structure.values
    assert [line.factor_id for line in st.lines.lines] == ["om", "staff"]
    assert v["om"].value == D("600.00") and v["staff"].value == D("500.00")
    for factor in ("revenue", "fuel_cost", "contribution"):
        assert v[factor].value is None, factor
    assert st.checks == ()


# --- test 11 and the composition ---------------------------------------------------------------------------------------

PACKAGE = TREE / "backend" / "assetops_backend" / "structure" / "targets"


def test_11_no_float_under_targets() -> None:
    files = sorted(PACKAGE.glob("*.py"))
    assert {f.name for f in files} == {"__init__.py", "lines.py", "rules.py", "read.py", "composition.py"}
    for f in files:
        assert "float(" not in f.read_text(encoding="utf-8"), f


def test_composition_disposes_the_first_when_the_second_fails(monkeypatch) -> None:
    import assetops_backend.commercial.composition as commercial
    import assetops_backend.structure.composition as structure
    from assetops_backend.structure.targets.composition import build_target_read

    disposed: list[str] = []
    monkeypatch.setattr(structure, "build_structure_read",
                        lambda url: structure.StructureReadService(None, lambda: disposed.append("actual")))

    def boom(url):
        raise RuntimeError("second")

    monkeypatch.setattr(commercial, "build_commercial_reads", boom)
    with pytest.raises(RuntimeError, match="second"):
        build_target_read("postgresql://unused")
    assert disposed == ["actual"]
