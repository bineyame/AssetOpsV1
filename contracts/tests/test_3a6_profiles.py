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


def test_n3_far_right_header_cell_is_refused_in_bounded_memory_and_time() -> None:
    """N1: a header cell at XFD must refuse the header before any data row is padded to 16,384 cells."""
    import time
    import tracemalloc
    members = zip_members(budget_bytes())
    sheet = members["xl/worksheets/sheet1.xml"]
    a = sheet.index(b"</row>")
    members["xl/worksheets/sheet1.xml"] = sheet[:a] + b'<c r="XFD1" t="inlineStr"><is><t>x</t></is></c>' + sheet[a:]
    data = _sheet_with_members(members, b"".join(
        b'<row r="%d"><c r="A%d" t="inlineStr"><is><t>x</t></is></c></row>' % (n, n) for n in range(500, 2500)))
    tracemalloc.start()
    started = time.perf_counter()
    code = refused_file(profile(BUDGET), data)
    elapsed = time.perf_counter() - started
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    assert code == "NATIVE_HEADER"
    assert peak < 20_000_000 and elapsed < 3.0, (peak, elapsed)


def _sheet_with_members(members: dict, rows_xml: bytes) -> bytes:
    sheet = members["xl/worksheets/sheet1.xml"]
    b = sheet.index(b"</sheetData>")
    members["xl/worksheets/sheet1.xml"] = sheet[:b] + rows_xml + sheet[b:]
    return rezip(members)


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


# --- N3 r3: one work bound for the workbook (fix round r3, review N4) ---------------------------------------------
# Adversarial workbooks, each small once deflated, each bounded on time and on peak memory. Builders follow the
# reviewer's round 3 probes. `_WORK_MAX` is the reader's one budget (XML elements parsed across the members read).

from assetops_contracts.native import xlsx as _xlsx  # noqa: E402

_ONE = b'<row r="%d"><c r="A%d" t="inlineStr"><is><t>x</t></is></c></row>'


def _deflated(members: dict[str, bytes]) -> bytes:
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for name, raw in members.items():
            z.writestr(name, raw)
    return out.getvalue()


def _workbook(rows_xml: bytes = b"", header_extra: bytes = b"", members: dict[str, bytes] | None = None) -> bytes:
    """The budget workbook with `header_extra` inside its header row, `rows_xml` after its rows, `members` added or
    replaced."""
    m = zip_members(budget_bytes())
    sheet = m["xl/worksheets/sheet1.xml"]
    a = sheet.index(b"</row>")
    sheet = sheet[:a] + header_extra + sheet[a:]
    b = sheet.index(b"</sheetData>")
    m["xl/worksheets/sheet1.xml"] = sheet[:b] + rows_xml + sheet[b:]
    m.update(members or {})
    return _deflated(m)


def _outcome(data: bytes) -> str:
    try:
        return f"ok {len(read(profile(BUDGET), data).obj['records'])}"
    except CanonicalRefused as refused:
        return refused.code


def _bounded(data: bytes, seconds: float, megabytes: float) -> str:
    """The read's outcome, after one plain run bounded on time and one traced run bounded on peak memory."""
    import time
    import tracemalloc
    started = time.perf_counter()
    outcome = _outcome(data)
    elapsed = time.perf_counter() - started
    tracemalloc.start()
    try:
        assert _outcome(data) == outcome
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    assert elapsed < seconds and peak < megabytes * 1e6, (outcome, elapsed, peak)
    return outcome


def test_n3_r3_duplicate_header_rows_are_a_workbook_refusal_in_bounded_time() -> None:
    """N4: thousands of rows numbered 1 with a cell at XFD must not rebuild the header once each."""
    data = _workbook(b'<row r="1"><c r="XFD1"><v>1</v></c></row>' * 5000)
    assert len(data) < 20_000
    assert _bounded(data, 1.0, 20) == "NATIVE_WORKBOOK"


def test_n3_r3_duplicate_data_rows_are_a_workbook_refusal() -> None:
    assert _bounded(_workbook(b'<row r="500"><c r="A500"><v>1</v></c></row>' * 5000), 1.0, 20) == "NATIVE_WORKBOOK"


def test_n3_r3_decreasing_row_numbers_are_a_workbook_refusal() -> None:
    assert _bounded(_workbook(b"".join(_ONE % (n, n) for n in range(5500, 500, -1))), 1.0, 20) == "NATIVE_WORKBOOK"


def test_n3_r3_row_zero_and_rows_past_excel_are_workbook_refusals() -> None:
    assert _outcome(_workbook(b'<row r="1048577"><c r="A1048577"><v>1</v></c></row>')) == "NATIVE_WORKBOOK"
    m = zip_members(budget_bytes())
    sheet = m["xl/worksheets/sheet1.xml"]
    m["xl/worksheets/sheet1.xml"] = sheet.replace(b'<row r="1"', b'<row r="0"', 1)
    assert _outcome(_deflated(m)) == "NATIVE_WORKBOOK"


def test_n3_r3_a_row_number_of_thousands_of_digits_is_a_workbook_refusal() -> None:
    """`int` refuses strings past 4,300 digits with a `ValueError`; the reader refuses first."""
    digits = "9" * 5000
    rows = f'<row r="{digits}"><c r="A{digits}"><v>1</v></c></row>'.encode()
    assert _outcome(_workbook(rows)) == "NATIVE_WORKBOOK"


@pytest.mark.parametrize("value", ["1E+999999", "1E-999999", "1E+9999999", "-1E+400"])
def test_n3_r3_a_number_past_a_double_is_unreadable_not_expanded(value: str) -> None:
    """A short exponent must not become a million-character cell (or an `Overflow`): the cell is unreadable and
    refuses its row alone, in bounded time and memory."""
    rows = b"".join(b'<row r="%d"><c r="A%d" t="inlineStr"><is><t>x</t></is></c><c r="D%d"><v>%s</v></c></row>'
                    % (n, n, n, value.encode()) for n in range(5, 2005))
    data = _workbook(rows)
    assert _bounded(data, 1.5, 40) == "ok 2003"
    result = read(profile(BUDGET), data)
    assert len(result.refused) == 2000


def test_n3_r3_numbers_inside_a_double_read_as_before() -> None:
    from assetops_contracts.native.xlsx import _number
    assert [_number(v) for v in ("0E+999999", "1E+308", "4.9E-324", "874.99999999999989", "-0")] == [
        "0", "1" + "0" * 308, "0." + "0" * 323 + "49", "875", "0"]


def test_n3_r3_rows_without_r_follow_the_previous_row() -> None:
    """§2.3: a `<row>` without `r` takes the previous row's number plus one, so it rises by itself; a numbered row
    after it must still rise past it."""
    from assetops_contracts.native.xlsx import xlsx_sparse_rows
    rows = xlsx_sparse_rows(_workbook(b'<row><c r="A5"><v>1</v></c></row><row/><row r="9"/>'), "Budget 2026")
    assert [n for n, _ in rows][-3:] == [5, 6, 9]
    assert _outcome(_workbook(b'<row><c r="A5"><v>1</v></c></row><row r="5"/>')) == "NATIVE_WORKBOOK"


def test_n3_r3_far_header_cell_is_compared_without_padding() -> None:
    """The header is the layout's width plus a check for non-empty cells past it: an empty far cell keeps a valid
    header, a far value refuses it, as before."""
    assert _outcome(_workbook(header_extra=b'<c r="XFD1"/>')) == "ok 3"
    assert _outcome(_workbook(header_extra=b'<c r="XFD1" t="inlineStr"><is><t></t></is></c>')) == "ok 3"
    assert _outcome(_workbook(header_extra=b'<c r="XFD1" t="inlineStr"><is><t>x</t></is></c>')) == "NATIVE_HEADER"
    assert _outcome(_workbook(header_extra=b'<c r="F1" t="inlineStr"><is><t>Extra</t></is></c>')) == "NATIVE_HEADER"


# Past-the-bound cases run with the bound lowered to `_SMALL` so the traced run stays short; the time and memory
# they need scale with the bound, and the near-member-cap case below runs at the real one.
_SMALL = 100_000


def test_n3_r3_the_bound_is_the_stated_one() -> None:
    assert _xlsx._WORK_MAX == 500_000


def test_n3_r3_many_empty_rows_under_the_bound_read_as_before() -> None:
    data = _workbook(b"<row/>" * 100_000)
    assert len(data) < 20_000
    assert _bounded(data, 1.5, 40) == "ok 3"


def test_n3_r3_empty_rows_past_the_bound_are_refused(monkeypatch) -> None:
    monkeypatch.setattr(_xlsx, "_WORK_MAX", _SMALL)
    assert _bounded(_workbook(b"<row/>" * (_SMALL + 10)), 1.0, 30) == "NATIVE_WORKBOOK"


def test_n3_r3_near_member_cap_sheet_is_refused_in_bounded_time_and_memory() -> None:
    """The reviewer's P5 at the real bound: a sheet member just under 16 MiB of one-cell rows (263 MB and 11 s at
    round 3). Since r4 the row ceiling stops the parse first: one kept row past `MAX_RECORDS` (10,001 records, which
    the batch refuses as `CANONICAL_RANGE`); the work bound alone stopped it after 100,000 rows."""
    target, parts, size, r = _xlsx._MEMBER_MAX - 10_000, [], 0, 500
    while size < target:
        parts.append(_ONE % (r, r))
        size, r = size + len(parts[-1]), r + 1
    data = _workbook(b"".join(parts[:-1]))
    assert max(len(v) for v in zip_members(data).values()) > _xlsx._MEMBER_MAX - 20_000
    assert len(data) < 8 * 2**20  # under the upload cap
    assert _bounded(data, 3.0, 120) == "ok 10001"


def test_n3_r3_cells_without_r_take_the_next_index_in_linear_time() -> None:
    """A cell without `r` takes the index after the widest cell so far; finding it must not rescan the row."""
    data = _workbook(b"".join(b"<row>" + b"<c><v>1</v></c>" * 16_000 + b"</row>" for _ in range(2)))
    assert _bounded(data, 1.5, 40) == "ok 5"  # each long row is a count mismatch, refused for its row alone


def test_n3_r3_repeated_cell_references_count_against_the_budget(monkeypatch) -> None:
    monkeypatch.setattr(_xlsx, "_WORK_MAX", _SMALL)
    data = _workbook(b'<row r="600">' + b'<c r="A600"><v>1</v></c>' * (_SMALL // 2 + 10) + b"</row>")
    assert _bounded(data, 1.0, 30) == "NATIVE_WORKBOOK"


def test_n3_r3_shared_strings_count_against_the_budget(monkeypatch) -> None:
    monkeypatch.setattr(_xlsx, "_WORK_MAX", _SMALL)
    sst = (b'<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
           + b"<si><t>a</t></si>" * (_SMALL // 2 + 10) + b"</sst>")
    assert _bounded(_workbook(members={"xl/sharedStrings.xml": sst}), 1.0, 30) == "NATIVE_WORKBOOK"


def test_n3_r3_many_sheets_count_against_the_budget(monkeypatch) -> None:
    monkeypatch.setattr(_xlsx, "_WORK_MAX", _SMALL)
    book = zip_members(budget_bytes())["xl/workbook.xml"]
    at = book.index(b"</sheets>")
    book = book[:at] + b'<sheet name="z" sheetId="9" r:id="rId9"/>' * (_SMALL + 10) + book[at:]
    assert _bounded(_workbook(members={"xl/workbook.xml": book}), 1.0, 30) == "NATIVE_WORKBOOK"


def test_n3_r3_many_members_are_listed_in_bounded_time() -> None:
    """The reader lists the members (sizes, names) and reads only four: 20,000 empty members cost the listing."""
    data = _workbook(members={f"xl/media/m{i}.bin": b"" for i in range(20_000)})
    assert _bounded(data, 1.5, 60) == "ok 3"


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
