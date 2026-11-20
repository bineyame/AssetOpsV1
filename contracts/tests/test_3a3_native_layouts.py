"""3A3 (spec `specs/3A3-emulators-contract-test/spec.md` §2.2, §2.3, §5 "Contracts"): the native layout engine.

The goldens and their expected records are written by hand (`backend/tests/fixtures/3a3/`); nothing expected here is
produced by `read_layout` (W2).
"""

from __future__ import annotations

import csv
import io
import json
from dataclasses import replace
from pathlib import Path
from types import MappingProxyType

import pytest

from assetops_contracts.canonical import CanonicalRefused
from assetops_contracts.native import LAYOUTS, Column, check_layout, read_layout, render_layout

FIXTURES = Path(__file__).resolve().parents[2] / "backend" / "tests" / "fixtures" / "3a3"
IDS = ("billing-illustrative-1", "collections-illustrative-1", "expenses-illustrative-1", "budget-illustrative-1")
CTX = {"tenant_code": "acme", "produced_at": "2026-11-06T09:00:00+00:00", "provenance": "source-emulated"}


def golden(layout_id: str) -> bytes:
    return (FIXTURES / f"{layout_id}.csv").read_bytes()


def expected(layout_id: str) -> list[dict]:
    return json.loads((FIXTURES / f"{layout_id}.expected.json").read_text(encoding="utf-8"))


def grid(layout_id: str) -> list[list[str]]:
    return [row for row in csv.reader(io.StringIO(golden(layout_id).decode("utf-8"), newline=""))]


def write(rows: list[list[str]]) -> bytes:
    out = io.StringIO()
    csv.writer(out, lineterminator="\n").writerows(rows)
    return out.getvalue().encode("utf-8")


def read(layout_id: str, data: bytes):
    return read_layout(LAYOUTS[layout_id], data, **CTX)


def refused_file(layout_id: str, data: bytes) -> tuple[str, str]:
    with pytest.raises(CanonicalRefused) as raised:
        read(layout_id, data)
    return raised.value.code, raised.value.path


def test_layouts_are_exactly_the_four() -> None:
    assert tuple(LAYOUTS) == IDS


# --- 1. goldens ----------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("layout_id", IDS)
def test_1_golden_reads_to_expected_and_renders_back(layout_id: str) -> None:
    result = read(layout_id, golden(layout_id))
    layout = LAYOUTS[layout_id]
    assert result.obj == {"format_version": 1, "tenant_code": "acme", "source_type": layout.source_type,
                          "source_system": layout.source_system, "provenance": "source-emulated",
                          "produced_at": "2026-11-06T09:00:00+00:00", "records": expected(layout_id)}
    assert result.rows == (2, 3, 4)
    assert dict(result.refused) == {}
    assert render_layout(layout, expected(layout_id)) == golden(layout_id)


def test_1_provenance_is_told_not_fixed() -> None:
    result = read_layout(LAYOUTS["budget-illustrative-1"], golden("budget-illustrative-1"), tenant_code="acme",
                         produced_at="2026-11-06T09:00:00+00:00", provenance="observed-financial")
    assert result.obj["provenance"] == "observed-financial"


# --- 2. header, encoding and characters -----------------------------------------------------------------------------

def _header_variants() -> list[tuple[str, list[str]]]:
    header = grid("billing-illustrative-1")[0]
    return [("reordered", [header[1], header[0], *header[2:]]),
            ("renamed", [("kwh" if h == "kWh" else h) for h in header]),
            ("extra", [*header, "Note"]),
            ("missing", header[:-1])]


@pytest.mark.parametrize("name,header", _header_variants(), ids=[v[0] for v in _header_variants()])
def test_2_header_refused(name: str, header: list[str]) -> None:
    rows = grid("billing-illustrative-1")
    width = len(header)
    body = [(r + [""] * width)[:width] for r in rows[1:]]
    assert refused_file("billing-illustrative-1", write([header, *body])) == ("NATIVE_HEADER", "json")


def test_2_empty_file_is_header_refusal() -> None:
    assert refused_file("billing-illustrative-1", b"") == ("NATIVE_HEADER", "json")


def test_2_bom_accepted_and_bad_byte_refused() -> None:
    data = golden("billing-illustrative-1")
    assert read("billing-illustrative-1", b"\xef\xbb\xbf" + data).obj["records"] == expected("billing-illustrative-1")
    assert refused_file("billing-illustrative-1", data[:40] + b"\xff" + data[40:]) == ("NATIVE_ENCODING", "json")


@pytest.mark.parametrize("bad", ["KOBO\x00-001", "KOBO\x1f-001", "KOBO\x7f-001"], ids=["nul", "us", "del"])
def test_2_control_character_refuses_its_row_only(bad: str) -> None:
    rows = grid("billing-illustrative-1")
    rows[2][2] = bad  # row 3's Site
    result = read("billing-illustrative-1", write(rows))
    assert dict(result.refused) == {1: ("NATIVE_CHARACTER", "row.3")}
    assert result.obj["records"][1] == {"format_version": 1}
    assert [result.obj["records"][0], result.obj["records"][2]] == [expected("billing-illustrative-1")[i]
                                                                    for i in (0, 2)]


def test_2_tab_inside_quoted_cell_is_text() -> None:
    rows = grid("expenses-illustrative-1")
    data = golden("expenses-illustrative-1").replace(b",DN-311,", b',"DN\t311",')
    assert b'"DN\t311"' in data
    result = read("expenses-illustrative-1", data)
    assert dict(result.refused) == {}
    assert result.obj["records"][0]["body"]["document_ref"] == "DN\t311"


# --- 3. rows -------------------------------------------------------------------------------------------------------

def test_3_short_row_refused_alone() -> None:
    rows = grid("collections-illustrative-1")
    rows[2] = rows[2][:-1]
    result = read("collections-illustrative-1", write(rows))
    assert dict(result.refused) == {1: ("NATIVE_ROW", "row.3")}
    want = expected("collections-illustrative-1")
    assert [result.obj["records"][0], result.obj["records"][2]] == [want[0], want[2]]


def test_3_blank_row_skipped_rows_stay_physical() -> None:
    data = golden("collections-illustrative-1").split(b"\n")
    data.insert(2, b"")
    result = read("collections-illustrative-1", b"\n".join(data))
    assert result.rows == (2, 4, 5)
    assert result.obj["records"] == expected("collections-illustrative-1")


def test_3_quoted_cell_spanning_lines_takes_its_last_line() -> None:
    rows = grid("expenses-illustrative-1")
    rows[1][7] = "DN\n311"
    result = read("expenses-illustrative-1", write(rows))
    assert result.rows == (3, 4, 5)


# --- 4. map misses -------------------------------------------------------------------------------------------------

def test_4_map_miss_expenses_category() -> None:
    rows = grid("expenses-illustrative-1")
    rows[1][5] = "Fuel"
    result = read("expenses-illustrative-1", write(rows))
    assert dict(result.refused) == {0: ("NATIVE_VALUE", "record.body.category")}


def test_4_map_miss_budget_line() -> None:
    rows = grid("budget-illustrative-1")
    rows[1][4] = "marketing"
    result = read("budget-illustrative-1", write(rows))
    assert dict(result.refused) == {0: ("NATIVE_VALUE", "record.body.factor_id")}


# --- 5. rule C -----------------------------------------------------------------------------------------------------

def test_5_rule_c_quantity_only_with_litres() -> None:
    result = read("expenses-illustrative-1", golden("expenses-illustrative-1"))
    fuel, om = result.obj["records"][0], result.obj["records"][1]
    assert fuel["quantity"] == {"value": "400", "unit": "L"}
    assert "quantity" not in om


# --- 6. render -----------------------------------------------------------------------------------------------------

def _render_raises(layout_id: str, record: dict) -> str:
    with pytest.raises(ValueError) as raised:
        render_layout(LAYOUTS[layout_id], [record])
    return str(raised.value)


def test_6_render_refuses_other_constant() -> None:
    record = expected("billing-illustrative-1")[0]
    record["body"]["line_type"] = "FIXED"
    assert _render_raises("billing-illustrative-1", record) == "NATIVE_RENDER billing-illustrative-1 body.line_type"


def test_6_render_refuses_disagreeing_paths() -> None:
    record = expected("billing-illustrative-1")[0]
    record["body"]["account_ref"] = "C-9999"
    assert _render_raises("billing-illustrative-1", record) == "NATIVE_RENDER billing-illustrative-1 body.account_ref"


def test_6_render_refuses_non_string() -> None:
    record = expected("budget-illustrative-1")[0]
    record["body"]["value"] = 3420
    assert _render_raises("budget-illustrative-1", record) == "NATIVE_RENDER budget-illustrative-1 body.value"


def test_6_render_refuses_unmapped_value() -> None:
    record = expected("expenses-illustrative-1")[1]
    record["body"]["category"] = "REPAIR"
    assert _render_raises("expenses-illustrative-1", record) == "NATIVE_RENDER expenses-illustrative-1 body.category"


def test_6_maps_are_one_to_one_and_a_planted_map_fails() -> None:
    for layout in LAYOUTS.values():
        check_layout(layout)
    budget = LAYOUTS["budget-illustrative-1"]
    bad_line = Column("Line", ("body.line_ref", "body.factor_id"),
                      MappingProxyType({"body.factor_id": MappingProxyType({"diesel_cost": "fuel_cost",
                                                                            "diesel": "fuel_cost"})}))
    planted = replace(budget, columns=tuple(bad_line if c.header == "Line" else c for c in budget.columns))
    with pytest.raises(ValueError, match="^NATIVE_LAYOUT budget-illustrative-1 body.factor_id$"):
        check_layout(planted)
