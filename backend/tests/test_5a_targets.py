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
LOADER = "loader:ds3"
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


def lakeside(count: int = 2) -> dict:
    w = new_world()
    w["intakes"] = [ingest(w, s["at"], s["entered_by"], s["batch"]) for s in steps()[:count]]
    w["reader"] = BudgetLineReader(w["months"], w["store"])
    return w


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
    w = lakeside()
    bl = site(w, "KOBO-001")
    assert bl.site_id == w["sites"]["KOBO-001"] and bl.period == OCT
    assert bl.version_ref == V1 and bl.problem is None
    assert tuple(line_tuple(line) for line in bl.lines) == KOBO_LINES
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
