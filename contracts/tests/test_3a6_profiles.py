"""3A6 (spec `specs/3A6-source-profiles/spec.md` §2.1 to §2.4, §4, §6 "Contracts" N1 to N9): source profiles.

The fixtures, their expected records, the digests and every literal below are written by hand from the spec; none is
produced by `read_rows`, `compile_profile` or a helper they share (W2).
"""

from __future__ import annotations

import copy
import csv
import io
import json
import struct
import sys
import zipfile
from dataclasses import replace
from pathlib import Path
from types import MappingProxyType

import pytest

from assetops_contracts.canonical import CanonicalRefused
from assetops_contracts.native import (
    CODED_PATHS,
    LAYOUTS,
    Column,
    Layout,
    ProfileInvalid,
    TransformFailed,
    ValueRules,
    check_layout,
    compile_profile,
    read_layout,
    render_layout,
)
from assetops_contracts.native.xlsx import XlsxNumber

ROOT = Path(__file__).resolve().parents[2]
F3 = ROOT / "backend" / "tests" / "fixtures" / "3a3"
F6 = ROOT / "backend" / "tests" / "fixtures" / "3a6"
sys.path.insert(0, str(F6))
import make_budget_xlsx as mk  # noqa: E402

CTX = {"tenant_code": "acme", "produced_at": "2026-11-06T09:00:00+00:00", "provenance": "source-emulated"}
KOBO, BUDGET = "kobo-ledger-expenses", "lakeside-budget"


def profile(name: str) -> dict:
    return json.loads((F6 / f"{name}.profile.json").read_text(encoding="utf-8"))


def expected(name: str) -> list[dict]:
    return json.loads((F6 / f"{name}.expected.json").read_text(encoding="utf-8"))


def kobo_bytes() -> bytes:
    return (F6 / f"{KOBO}.csv").read_bytes()


def read(obj: dict, data: bytes):
    return read_layout(compile_profile(obj, 1), data, **CTX)


def kobo_grid() -> list[list[str]]:
    return list(csv.reader(io.StringIO(kobo_bytes().decode("cp1252"), newline=""), delimiter=";"))


def kobo_write(rows: list[list[str]]) -> bytes:
    out = io.StringIO()
    csv.writer(out, delimiter=";", lineterminator="\r\n").writerows(rows)
    return out.getvalue().encode("cp1252")


def refused_file(obj: dict, data: bytes) -> str:
    with pytest.raises(CanonicalRefused) as raised:
        read(obj, data)
    return raised.value.code


# --- N1 the illustrative layouts do not move ---------------------------------------------------------------------

@pytest.mark.parametrize("layout_id", tuple(LAYOUTS))
def test_n1_illustrative_goldens_read_and_render_as_before(layout_id: str) -> None:
    data = (F3 / f"{layout_id}.csv").read_bytes()
    result = read_layout(LAYOUTS[layout_id], data, **CTX)
    assert result.obj["records"] == json.loads((F3 / f"{layout_id}.expected.json").read_text(encoding="utf-8"))
    assert not result.refused
    assert render_layout(LAYOUTS[layout_id], result.obj["records"]) == data
    check_layout(LAYOUTS[layout_id])


# --- N2 the kobo CSV ---------------------------------------------------------------------------------------------

def test_n2_kobo_reads_to_its_expected_records() -> None:
    result = read(profile(KOBO), kobo_bytes())
    assert result.obj["records"] == expected(KOBO)
    assert result.rows == (4, 5, 6, 7)
    assert not result.refused
    assert result.obj["source_type"] == "expense_ledger"
    assert result.obj["source_system"] == "lakeside-purchases-ledger"
    text = json.dumps(result.obj)
    assert "0712000001" not in text and "0712000777" not in text


def test_n2_kobo_declared_utf8_is_an_encoding_refusal() -> None:
    obj = profile(KOBO)
    obj["file"]["encoding"] = "utf-8"
    assert refused_file(obj, kobo_bytes()) == "NATIVE_ENCODING"


# --- N3 the budget workbook --------------------------------------------------------------------------------------

def budget_bytes() -> bytes:
    return (F6 / f"{BUDGET}.xlsx").read_bytes()


def rows_with(r: int, ref: str, cell: tuple | None) -> list:
    rows = copy.deepcopy(mk.GOLDEN_ROWS)
    for number, cells in rows:
        if number == r:
            cells[:] = [c for c in cells if c[0] != ref] + ([cell] if cell else [])
    return rows


def zip_members(data: bytes) -> dict[str, bytes]:
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        return {i.filename: z.read(i.filename) for i in z.infolist()}


def rezip(members: dict[str, bytes]) -> bytes:
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_STORED) as z:
        for name, raw in members.items():
            z.writestr(zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0)), raw)
    return out.getvalue()


def patched(member: str, old: bytes, new: bytes) -> bytes:
    members = zip_members(budget_bytes())
    assert old in members[member]
    members[member] = members[member].replace(old, new, 1)
    return rezip(members)


def headers_patch(data: bytes, name: str, local: tuple[int, int], central: tuple[int, int]) -> bytes:
    """Sets a 2-byte field of `name`'s local header (offset, OR mask) and of its central directory entry."""
    buf = bytearray(data)
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        info = z.getinfo(name)
    at = info.header_offset + local[0]
    struct.pack_into("<H", buf, at, local[1] | (struct.unpack_from("<H", buf, at)[0] if local[0] == 6 else 0))
    pos = buf.find(b"PK\x01\x02")
    while pos != -1:
        name_len = struct.unpack_from("<H", buf, pos + 28)[0]
        if bytes(buf[pos + 46:pos + 46 + name_len]) == name.encode():
            at = pos + central[0]
            struct.pack_into("<H", buf, at, central[1] | (struct.unpack_from("<H", buf, at)[0] if central[0] == 8 else 0))
        pos = buf.find(b"PK\x01\x02", pos + 4)
    return bytes(buf)


def test_n3_x0_committed_workbook_is_the_hand_built_one() -> None:
    assert budget_bytes() == mk.build_workbook(mk.GOLDEN_ROWS)


def test_n3_budget_reads_to_its_expected_records() -> None:
    result = read(profile(BUDGET), budget_bytes())
    assert result.obj["records"] == expected(BUDGET)
    assert result.rows == (2, 3, 4)
    assert not result.refused


@pytest.mark.parametrize("name, data", [
    ("second sheet", lambda: patched("xl/workbook.xml", b"</sheets>",
                                     b'<sheet name="Other" sheetId="2" r:id="rId2"/></sheets>')),
    ("renamed", lambda: mk.build_workbook(mk.GOLDEN_ROWS, sheet="Budget")),
])
def test_n3_sheet_refusals(name: str, data) -> None:
    assert refused_file(profile(BUDGET), data()) == "NATIVE_SHEET"


@pytest.mark.parametrize("name, data", [
    ("date1904", lambda: patched("xl/workbook.xml", b"<sheets>", b'<workbookPr date1904="1"/><sheets>')),
    ("doctype", lambda: patched("xl/worksheets/sheet1.xml", b"<worksheet ", b"<!DOCTYPE x><worksheet ")),
    ("not a zip", lambda: b"not a zip"),
    ("crc", lambda: (lambda d: d[:d.index(b"<sheetData>") + 3] + bytes([d[d.index(b"<sheetData>") + 3] ^ 1])
                     + d[d.index(b"<sheetData>") + 4:])(budget_bytes())),
    ("method 99", lambda: headers_patch(budget_bytes(), "xl/worksheets/sheet1.xml", (8, 99), (10, 99))),
    ("encrypted", lambda: headers_patch(budget_bytes(), "xl/worksheets/sheet1.xml", (6, 1), (8, 1))),
    ("utf-16", lambda: (lambda m: rezip({**m, "xl/worksheets/sheet1.xml":
                                          m["xl/worksheets/sheet1.xml"].decode("utf-8").encode("utf-16")}))(
        zip_members(budget_bytes()))),
])
def test_n3_workbook_refusals(name: str, data) -> None:
    assert refused_file(profile(BUDGET), data()) == "NATIVE_WORKBOOK"


@pytest.mark.parametrize("cell", [("D3", "e", "#DIV/0!"), ("D3", None, "NaN"), ("D3", None, "Infinity")])
def test_n3_unreadable_amount_refuses_its_row_alone(cell: tuple) -> None:
    result = read(profile(BUDGET), mk.build_workbook(rows_with(3, "D3", cell)))
    assert dict(result.refused) == {1: ("NATIVE_FORMAT", "record.body.value")}
    assert result.obj["records"][0] == expected(BUDGET)[0]
    assert result.obj["records"][2] == expected(BUDGET)[2]


def test_n3_dropped_note_column_is_never_judged() -> None:
    rows = copy.deepcopy(mk.GOLDEN_ROWS)
    rows[0][1].append(("F1", "inlineStr", "Note"))
    rows[1][1].append(("F2", "e", "#N/A"))
    rows[2][1].append(("F3", "inlineStr", "see\u200bnote"))
    obj = profile(BUDGET)
    obj["columns"].append({"header": "Note", "paths": []})
    result = read(obj, mk.build_workbook(rows))
    assert not result.refused
    assert result.obj["records"] == expected(BUDGET)


def _sheet_with(rows_xml: bytes) -> bytes:
    members = zip_members(budget_bytes())
    sheet = members["xl/worksheets/sheet1.xml"]
    a, b = sheet.index(b"</row>") + len(b"</row>"), sheet.index(b"</sheetData>")
    members["xl/worksheets/sheet1.xml"] = sheet[:a] + sheet[a:b] + rows_xml + sheet[b:]
    return rezip(members)


def test_n3_far_right_cells_are_read_in_bounded_memory_and_time() -> None:
    """F1: a tiny workbook with a cell at XFD on thousands of rows must not be padded to 16,384 cells a row."""
    import time
    import tracemalloc
    far = b"".join(b'<row r="%d"><c r="XFD%d" t="inlineStr"><is><t>x</t></is></c></row>' % (n, n)
                   for n in range(500, 2500))
    data = _sheet_with(far)
    assert len(data) < 400_000
    tracemalloc.start()
    started = time.perf_counter()
    result = read(profile(BUDGET), data)
    elapsed = time.perf_counter() - started
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    assert peak < 20_000_000 and elapsed < 3.0, (peak, elapsed)
    assert len(result.refused) == 2000  # each far cell is a count mismatch, refused for its row alone
    assert {code for code, _ in result.refused.values()} == {"NATIVE_ROW"}


def test_n3_column_past_xfd_is_a_workbook_refusal() -> None:
    data = _sheet_with(b'<row r="900"><c r="XFE900" t="inlineStr"><is><t>x</t></is></c></row>')
    assert refused_file(profile(BUDGET), data) == "NATIVE_WORKBOOK"


def test_n3_formula_without_cached_value_refuses_its_row() -> None:
    members = zip_members(budget_bytes())
    sheet = members["xl/worksheets/sheet1.xml"].decode("utf-8")
    import re as _re
    m = _re.search(r'<c r="D3"[^>]*>.*?</c>', sheet)
    assert m
    members["xl/worksheets/sheet1.xml"] = sheet.replace(m.group(0), '<c r="D3"><f>SUM(B1:B9)</f></c>').encode("utf-8")
    result = read(profile(BUDGET), rezip(members))
    assert dict(result.refused) == {1: ("NATIVE_FORMAT", "record.body.value")}


def test_n3_unicode_digit_row_number_is_a_workbook_refusal() -> None:
    members = zip_members(budget_bytes())
    sheet = members["xl/worksheets/sheet1.xml"]
    assert b'<row r="3"' in sheet
    members["xl/worksheets/sheet1.xml"] = sheet.replace(b'<row r="3"', '<row r="\u00b2"'.encode("utf-8"), 1)
    assert refused_file(profile(BUDGET), rezip(members)) == "NATIVE_WORKBOOK"


# --- N4 transforms -----------------------------------------------------------------------------------------------

from assetops_contracts.native import transform  # noqa: E402

COMMA = ValueRules(decimal_mark=",", thousands_mark=".", date_format="DD/MM/YYYY", time_format="HH:MM",
                   timezone="Africa/Nairobi")


@pytest.mark.parametrize("type_, cell, values, scale, out", [
    ("number", "1.200,00", COMMA, None, "1200.00"),
    ("number", "-5,5", COMMA, None, "-5.5"),
    ("number", "(12,50)", replace(COMMA, negative="parentheses"), None, "-12.50"),
    ("number", "0012", COMMA, None, "12"),
    ("number", "12500", ValueRules(), "0.001", "12.500"),
    ("date", "5/1/2026", COMMA, None, "2026-01-05"),
    ("date", XlsxNumber("61"), COMMA, None, "1900-03-01"),
    ("date", XlsxNumber("73050"), COMMA, None, "2099-12-31"),
    ("date", XlsxNumber("46296"), COMMA, None, "2026-10-01"),
    ("month", XlsxNumber("202610"), ValueRules(month_format="YYYYMM"), None, "2026-10"),
    ("month", "202610", ValueRules(month_format="YYYYMM"), None, "2026-10"),
    ("datetime", "11/10/2026 09:00", COMMA, None, "2026-10-11T09:00:00+03:00"),
    ("datetime", "2026-10-11T06:00:00Z", COMMA, None, "2026-10-11T06:00:00Z"),
    ("datetime", XlsxNumber("46296.5"), ValueRules(), None, "2026-10-01T12:00:00+00:00"),
    ("month", "Oct-2026", ValueRules(month_format="Mon-YYYY"), None, "2026-10"),
    ("month", "October 2026", ValueRules(month_format="Month YYYY"), None, "2026-10"),
    ("month_of", "2026-10-31T22:30:00+00:00", COMMA, None, "2026-11"),
])
def test_n4_transform_literals(type_, cell, values, scale, out) -> None:
    assert transform(type_, cell, values, scale=scale) == out


@pytest.mark.parametrize("type_, cell, values", [
    ("number", "1.20,00", COMMA),
    ("number", " 500,00", COMMA),
    ("number", "12.5", COMMA),
    ("date", "31/02/2026", COMMA),
    ("date", XlsxNumber("60"), COMMA),
    ("date", XlsxNumber("73051"), COMMA),
    ("date", XlsxNumber("2958466"), COMMA),
    ("month", XlsxNumber("202610"), ValueRules(month_format="Mon-YYYY")),
    ("month", "oct-2026", ValueRules(month_format="Mon-YYYY")),
])
def test_n4_transform_failures(type_, cell, values) -> None:
    with pytest.raises(TransformFailed):
        transform(type_, cell, values)


# --- N5 invisible characters -------------------------------------------------------------------------------------

def billing_rows() -> list[list[str]]:
    return list(csv.reader(io.StringIO((F3 / "billing-illustrative-1.csv").read_text(encoding="utf-8"), newline="")))


def billing_write(rows: list[list[str]]) -> bytes:
    out = io.StringIO()
    csv.writer(out, lineterminator="\n").writerows(rows)
    return out.getvalue().encode("utf-8")


@pytest.mark.parametrize("ch", ["\u0085", "\u200b", "\ufeff", "\u2028", "\u00ad"])
def test_n5_invisible_character_refuses_its_row_alone(ch: str) -> None:
    rows = billing_rows()
    rows[1][3] = rows[1][3] + ch
    result = read_layout(LAYOUTS["billing-illustrative-1"], billing_write(rows), **CTX)
    assert dict(result.refused) == {0: ("NATIVE_CHARACTER", "row.2")}


def test_n5_tab_inside_quoted_cell_is_text() -> None:
    rows = billing_rows()
    rows[1][10] = "T\t1"
    result = read_layout(LAYOUTS["billing-illustrative-1"], billing_write(rows), **CTX)
    assert not result.refused


def test_n5_dropped_phone_column_is_not_checked() -> None:
    # cp1252 has no U+200B, so the same export is written (and declared) UTF-8 for this case.
    grid = kobo_grid()
    grid[3][5] = grid[3][5] + "\u200b"
    obj = profile(KOBO)
    obj["file"]["encoding"] = "utf-8"
    out = io.StringIO()
    csv.writer(out, delimiter=";", lineterminator="\r\n").writerows(grid)
    result = read(obj, out.getvalue().encode("utf-8"))
    assert not result.refused
    assert result.obj["records"] == expected(KOBO)


# --- N6 join and digest ------------------------------------------------------------------------------------------

def test_n6_blank_join_part_writes_no_record_id() -> None:
    result = read(profile(BUDGET), mk.build_workbook(rows_with(2, "C2", None)))
    assert "source_record_id" not in result.obj["records"][0]
    assert result.obj["records"][1]["source_record_id"] == "KOBO-001:2026-10:Diesel"


def test_n6_colon_in_a_join_part_refuses_its_row() -> None:
    result = read(profile(BUDGET), mk.build_workbook(rows_with(2, "A2", ("A2", "inlineStr", "KOBO:001"))))
    assert dict(result.refused) == {0: ("NATIVE_FORMAT", "record.source_record_id")}


def test_n6_digests_are_the_hand_literals() -> None:
    budget = read(profile(BUDGET), budget_bytes()).obj["records"]
    assert [r["source_version"] for r in budget] == ["r8b6cdd540fa7c49a", "r4bc1868e230b8ed3", "rff4a97f304aa3280"]
    kobo = read(profile(KOBO), kobo_bytes()).obj["records"]
    assert [r["source_version"] for r in kobo] == ["r7a74ac02930cf9bd", "rb02e46e3dd180e63", "r45ba3a14daa3c051",
                                                   "rf609c71589ac443d"]
    grid = kobo_grid()
    grid[3][8] = "Paid"
    assert read(profile(KOBO), kobo_write(grid)).obj["records"][0]["source_version"] == "r16fd22096444d702"
    grid = kobo_grid()
    grid[3][7] = "999,00"
    assert read(profile(KOBO), kobo_write(grid)).obj["records"][0]["source_version"] == "r6e38c75df75107a7"


def test_n6_changed_amount_changes_only_its_digest() -> None:
    before = [r["source_version"] for r in read(profile(BUDGET), budget_bytes()).obj["records"]]
    after = [r["source_version"] for r in read(profile(BUDGET), mk.build_workbook(
        rows_with(2, "D2", ("D2", None, "3421")))).obj["records"]]
    assert after[0] != before[0] and after[1:] == before[1:]


# --- N7 profile validation ---------------------------------------------------------------------------------------

def _set(obj: dict, dotted: str, value) -> None:
    parts = dotted.split(".")
    target = obj
    for part in parts[:-1]:
        target = target[int(part)] if isinstance(target, list) else target[part]
    if isinstance(target, list):
        target[int(parts[-1])] = value
    else:
        target[parts[-1]] = value


N7 = [
    ("unknown key", lambda o: o.update(extra=1), "extra"),
    ("schema_version 2", lambda o: o.update(schema_version=2), "schema_version"),
    ("map on counterparty", lambda o: _set(o, "columns.4.paths.0.map", {"a": "b"}), "columns.4.paths.0.map"),
    ("category unmapped", lambda o: o["columns"][3]["paths"][0].pop("map"), "columns.3.paths.0.map"),
    ("two site_code writers", lambda o: _set(o, "columns.4.paths.0.path", "site_code"), "columns.4.paths.0.path"),
    ("join with a record id column", lambda o: o.update(record_id_join=["Site", "Supplier"]), "record_id_join"),
    ("illustrative system", lambda o: o.update(source_system="illustrative-x"), "source_system"),
    ("marks equal", lambda o: _set(o, "values.thousands_mark", ","), "values.thousands_mark"),
    ("zone", lambda o: _set(o, "values.timezone", "Mars/Base"), "values.timezone"),
    ("scale on text", lambda o: _set(o, "columns.0.paths.0.scale", "2"), "columns.0.paths.0.scale"),
    ("version column without one", lambda o: o.update(version={"from": "column"}), "version"),
    ("constant version with status", lambda o: o.update(version={"from": "constant", "value": "1"}), "version"),
    ("one column", lambda o: o.update(columns=o["columns"][:1]), "columns"),
    ("scale 0", lambda o: _set(o, "columns.6.paths.0.scale", "0"), "columns.6.paths.0.scale"),
    ("scale -1", lambda o: _set(o, "columns.6.paths.0.scale", "-1"), "columns.6.paths.0.scale"),
    ("scale 1e3", lambda o: _set(o, "columns.6.paths.0.scale", "1e3"), "columns.6.paths.0.scale"),
]


@pytest.mark.parametrize("name, mutate, where", N7, ids=[n for n, _, _ in N7])
def test_n7_invalid_profiles_name_the_key(name, mutate, where) -> None:
    obj = profile(KOBO)
    mutate(obj)
    with pytest.raises(ProfileInvalid) as raised:
        compile_profile(obj, 1)
    assert str(raised.value) == f"PROFILE_INVALID {where}"


def test_n7_fixture_profiles_compile() -> None:
    assert compile_profile(profile(KOBO), 1).id == "profile.kobo-ledger-expenses.v1"
    assert compile_profile(profile(BUDGET), 7).id == "profile.lakeside-budget.v7"


# --- N8 render refusal and the coded rule ------------------------------------------------------------------------

def test_n8_render_refuses_a_compiled_profile() -> None:
    with pytest.raises(ValueError) as raised:
        render_layout(compile_profile(profile(KOBO), 1), expected(KOBO))
    assert str(raised.value) == "NATIVE_RENDER profile.kobo-ledger-expenses.v1 profile"


def test_n8_unmapped_coded_path_fails_check_layout() -> None:
    planted = replace(LAYOUTS["collections-illustrative-1"], id="planted-1",
                      columns=LAYOUTS["collections-illustrative-1"].columns + (Column("Method", ("body.method",)),))
    with pytest.raises(ValueError) as raised:
        check_layout(planted)
    assert str(raised.value) == "NATIVE_LAYOUT planted-1 body.method"
    mapped_text = Layout(id="planted-2", source_type="expense_ledger", source_system="x",
                         columns=(Column("Ref", ("source_record_id", "body.document_ref"),
                                         MappingProxyType({"body.document_ref": MappingProxyType({"a": "b"})})),),
                         constants=MappingProxyType({}))
    with pytest.raises(ValueError):
        check_layout(mapped_text)


# --- N9 the coded paths, written out -----------------------------------------------------------------------------

def test_n9_coded_paths_are_the_twelve() -> None:
    assert CODED_PATHS == frozenset({"kind", "status", "subject.kind", "quantity.unit", "body.line_type",
                                     "body.tariff_class", "body.method", "body.category", "body.direction",
                                     "body.read_type", "body.contract_type", "body.factor_id"})
