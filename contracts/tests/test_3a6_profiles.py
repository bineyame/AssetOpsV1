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
import zlib
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
    split_file,
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
    assert _bounded(_workbook(b"<row/>" * (_SMALL + 10)), 1.0, 30) == "NATIVE_TOO_LARGE"


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
    assert _bounded(data, 1.0, 30) == "NATIVE_TOO_LARGE"


def test_n3_r3_shared_strings_count_against_the_budget(monkeypatch) -> None:
    monkeypatch.setattr(_xlsx, "_WORK_MAX", _SMALL)
    sst = (b'<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
           + b"<si><t>a</t></si>" * (_SMALL // 2 + 10) + b"</sst>")
    assert _bounded(_workbook(members={"xl/sharedStrings.xml": sst}), 1.0, 30) == "NATIVE_TOO_LARGE"


def test_n3_r3_many_sheets_count_against_the_budget(monkeypatch) -> None:
    monkeypatch.setattr(_xlsx, "_WORK_MAX", _SMALL)
    book = zip_members(budget_bytes())["xl/workbook.xml"]
    at = book.index(b"</sheets>")
    book = book[:at] + b'<sheet name="z" sheetId="9" r:id="rId9"/>' * (_SMALL + 10) + book[at:]
    assert _bounded(_workbook(members={"xl/workbook.xml": book}), 1.0, 30) == "NATIVE_TOO_LARGE"


def test_n3_r3_many_members_are_listed_in_bounded_time() -> None:
    """The reader reads only four members. Since r5 (D-3A6.24, N10; a listed literal change from `ok 3`) a zip of
    more than 256 entries is refused from its end record before `zipfile` lists them: 20,000 empty members."""
    data = _workbook(members={f"xl/media/m{i}.bin": b"" for i in range(20_000)})
    assert _bounded(data, 1.5, 60) == "NATIVE_TOO_LARGE"


# --- N3 r4: bounds by resource (fix round r4, review N5, N6, N7) ------------------------------------------------
# Every resource an upload can consume has a bound enforced before the work: inflated member bytes (N5), characters
# delivered by cells (N6), and kept rows and cells on the CSV path as on the XLSX one (N7).

from assetops_contracts.native import layouts_v1 as _layouts  # noqa: E402
from assetops_contracts.canonical.records_v1 import MAX_RECORDS  # noqa: E402

_SHEET = "xl/worksheets/sheet1.xml"


def _size_lie(pad_mib: int) -> bytes:
    """The budget workbook whose sheet member declares the real sheet's size and CRC, but whose deflate stream goes
    on for `pad_mib` MiB of spaces (review N5). Written by hand, the stream a MiB at a time (about a kB a MiB)."""
    parts, central, offset = [], [], 0
    for name, raw in zip_members(budget_bytes()).items():
        deflate = zlib.compressobj(9, zlib.DEFLATED, -15)
        stream = [deflate.compress(raw)]
        if name == _SHEET:
            mib = b" " * 2**20
            stream += [deflate.compress(mib) for _ in range(pad_mib)]
        comp = b"".join(stream) + deflate.flush()
        crc, size, encoded = zlib.crc32(raw), len(raw), name.encode()
        parts.append(struct.pack("<4s5H3L2H", b"PK\x03\x04", 20, 0, 8, 0, 33, crc, len(comp), size,
                                 len(encoded), 0) + encoded + comp)
        central.append(struct.pack("<4s6H3L5H2L", b"PK\x01\x02", 20, 20, 0, 8, 0, 33, crc, len(comp), size,
                                   len(encoded), 0, 0, 0, 0, 0, offset) + encoded)
        offset += len(parts[-1])
    directory = b"".join(central)
    end = struct.pack("<4s4H2LH", b"PK\x05\x06", 0, 0, len(central), len(central), len(directory), offset, 0)
    return b"".join(parts) + directory + end


def test_n3_r4_a_member_whose_declared_size_lies_is_inflated_only_to_that_size() -> None:
    """Review N5: 200 MiB behind a declared few kB (a 200 kB upload took 422 MB at round 4). The member is inflated
    a chunk at a time and the read stops at the declared size, so the trailing stream is never inflated."""
    data = _size_lie(200)
    assert len(data) < 400_000
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        assert z.getinfo(_SHEET).file_size == len(zip_members(budget_bytes())[_SHEET])
    assert _bounded(data, 1.0, 30) == "ok 3"


def test_n3_r4_inflated_bytes_are_counted_against_the_member_and_total_caps(monkeypatch) -> None:
    """The caps hold on the bytes actually inflated: a member past the member cap, and members together past the
    total, are `NATIVE_TOO_LARGE` since r5, D-3A6.25 (caps lowered so the members stay small)."""
    real = len(zip_members(budget_bytes())[_SHEET])
    monkeypatch.setattr(_xlsx, "_MEMBER_MAX", real - 1)
    assert _outcome(budget_bytes()) == "NATIVE_TOO_LARGE"
    monkeypatch.setattr(_xlsx, "_MEMBER_MAX", 16 * 2**20)
    total = sum(len(v) for k, v in zip_members(budget_bytes()).items()
                if k in ("xl/workbook.xml", "xl/_rels/workbook.xml.rels", _SHEET))
    monkeypatch.setattr(_xlsx, "_TOTAL_MAX", total - 1)
    monkeypatch.setattr(zipfile.ZipFile, "infolist", lambda self: [])  # pass the declared-size pre-check
    assert _outcome(budget_bytes()) == "NATIVE_TOO_LARGE"
    monkeypatch.setattr(_xlsx, "_TOTAL_MAX", total)
    assert _outcome(budget_bytes()) == "ok 3"


def test_n3_r4_bzip2_and_lzma_members_are_workbook_refusals() -> None:
    for method in (zipfile.ZIP_BZIP2, zipfile.ZIP_LZMA):
        out = io.BytesIO()
        with zipfile.ZipFile(out, "w") as z:
            for name, raw in zip_members(budget_bytes()).items():
                z.writestr(name, raw, compress_type=method if name == _SHEET else zipfile.ZIP_DEFLATED)
        assert _outcome(out.getvalue()) == "NATIVE_WORKBOOK"


_SST_LONG = (b'<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><si><t>'
             + "\u00e9".encode() * 1_000_000 + b"</t></si></sst>")


def _shared_rows(count: int) -> bytes:
    """`count` rows whose written Currency cell is shared string 0 (review N6)."""
    return b"".join(b'<row r="%d"><c r="E%d" t="s"><v>0</v></c></row>' % (r, r) for r in range(10, 10 + count))


def test_n3_r4_a_shared_string_is_charged_on_every_reference() -> None:
    """Review N6: one 1,000,000-character shared string referenced from 1,000 rows (17.4 s for 100 rows at round
    4). Each reference charges its length to the 16 Mi-character budget, so the parse stops at the 17th row."""
    data = _workbook(_shared_rows(1_000), members={"xl/sharedStrings.xml": _SST_LONG})
    assert len(data) < 40_000
    assert _bounded(data, 1.0, 60) == "NATIVE_TOO_LARGE"


def test_n3_r4_delivered_characters_under_the_budget_read_as_before() -> None:
    data = _workbook(_shared_rows(10), members={"xl/sharedStrings.xml": _SST_LONG})
    assert _bounded(data, 2.0, 60) == "ok 13"  # 10 million characters, scanned once each


def test_n3_r4_inline_characters_count_against_the_same_budget(monkeypatch) -> None:
    monkeypatch.setattr(_xlsx, "_CHAR_MAX", 1_000)
    one = b'<row r="9"><c r="E9" t="inlineStr"><is><t>' + b"x" * 1_001 + b"</t></is></c></row>"
    assert _outcome(_workbook(one)) == "NATIVE_TOO_LARGE"
    monkeypatch.setattr(_xlsx, "_CHAR_MAX", 10_000)
    assert _outcome(_workbook(one)) == "ok 4"


def test_n3_r4_the_character_bound_is_the_stated_one() -> None:
    assert _xlsx._CHAR_MAX == 16 * 2**20 and _xlsx._MEMBER_MAX == 16 * 2**20 and _xlsx._TOTAL_MAX == 64 * 2**20


def test_n3_r4_the_invisible_class_is_the_per_character_rule() -> None:
    """The one-pass class flags exactly the code points the per-character rule flags."""
    pattern = _layouts._invisible_class()
    every = "".join(chr(cp) for cp in range(sys.maxunicode + 1))
    flagged = {m.start() for m in pattern.finditer(every)}
    assert flagged == {cp for cp in range(sys.maxunicode + 1) if _layouts._flagged(chr(cp))}
    assert 0x200B in flagged and 0x0D not in flagged and ord("A") not in flagged


def _kobo_head() -> bytes:
    return b"".join(kobo_bytes().splitlines(keepends=True)[:3])


def _kobo_outcome(data: bytes) -> str:
    try:
        return f"ok {len(read(profile(KOBO), data).obj['records'])}"
    except CanonicalRefused as refused:
        return refused.code


def _kobo_bounded(data: bytes, seconds: float, megabytes: float) -> str:
    import time
    import tracemalloc
    started = time.perf_counter()
    outcome = _kobo_outcome(data)
    elapsed = time.perf_counter() - started
    tracemalloc.start()
    try:
        assert _kobo_outcome(data) == outcome
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    assert elapsed < seconds and peak < megabytes * 1e6, (outcome, elapsed, peak)
    return outcome


def test_n3_r4_csv_rows_stop_one_past_the_batch_ceiling() -> None:
    """Review N7: 2 MiB of `x` rows (1,048,576 rows; 8 MiB took 11.8 s and 2.5 GB at round 4). The read keeps
    10,001 rows and stops; the batch refuses that count (`CANONICAL_RANGE batch.records`)."""
    data = _kobo_head() + b"x\n" * 2**20
    assert _kobo_bounded(data, 1.0, 40) == f"ok {MAX_RECORDS + 1}"


def test_n3_r4_csv_at_the_ceiling_reads_every_row() -> None:
    row = kobo_bytes().splitlines(keepends=True)[3]
    header, rows = split_file(compile_profile(profile(KOBO), 1), _kobo_head() + row * MAX_RECORDS)
    assert len(rows) == MAX_RECORDS and rows[-1][0] == 3 + MAX_RECORDS


def test_n3_r4_csv_wide_rows_keep_the_width_plus_one() -> None:
    """A row of 100,000 fields keeps the layout's width plus one cell (a count mismatch either way)."""
    wide = b";".join(b"%02d" % (i % 100) for i in range(100_000)) + b"\n"
    data = _kobo_head() + wide * 10
    assert len(data) < 8 * 2**20
    assert _kobo_bounded(data, 1.5, 50) == "ok 10"  # the decoded text and its reader buffer, about 30 MB
    _, rows = split_file(compile_profile(profile(KOBO), 1), data)
    assert {len(cells) for _, cells in rows} == {10}


def test_n3_r4_xlsx_rows_stop_one_past_the_batch_ceiling() -> None:
    """The same ceiling on the XLSX path: 100,000 non-empty rows stop at 10,001 kept (the work bound allows them)."""
    data = _workbook(b"".join(b'<row r="%d"><c r="E%d" t="b"/></row>' % (r, r) for r in range(10, 100_010)))
    assert _bounded(data, 1.5, 60) == f"ok {MAX_RECORDS + 1}"


# --- N3 r5: the last precision bounds under the envelope (fix round r5, D-3A6.24; review r5 N8, N9, N10) ----------
# Each probe follows review r5's; each is refused `NATIVE_TOO_LARGE`, bounded on time (plain run) and peak memory
# (traced run). The envelope (backend, spec §2.12) bounds the same files by the kernel; these keep them cheap.

_UPLOAD = 8 * 2**20


def _attrs(names) -> bytes:
    return b" ".join(b'%s=""' % n for n in names)


def _before_sheet_data(xml: bytes) -> bytes:
    m = zip_members(budget_bytes())
    sheet = m[_SHEET]
    at = sheet.index(b"<sheetData")
    m[_SHEET] = sheet[:at] + xml + sheet[at:]
    return _deflated(m)


def _n8_one_element() -> bytes:
    data = _before_sheet_data(b"<x " + _attrs(b"a%d" % i for i in range(1_450_000)) + b"/>")
    assert len(zip_members(data)[_SHEET]) < _xlsx._MEMBER_MAX
    return data


def _n8_spread() -> bytes:
    return _before_sheet_data(b"".join(b"<x " + _attrs(b"a%d" % (e * 14_500 + k) for k in range(14_500)) + b"/>"
                                       for e in range(100)))


def _n8_namespaced() -> bytes:
    return _before_sheet_data(b'<x xmlns:p="u" ' + _attrs(b"p:a%d" % i for i in range(1_000_000)) + b"/>")


def _n8_pr_and_sheet() -> bytes:
    attrs = _attrs(b"a%d" % i for i in range(1_450_000))
    m = zip_members(budget_bytes())
    m["xl/workbook.xml"] = m["xl/workbook.xml"].replace(b"<sheets", b"<workbookPr " + attrs + b"/><sheets", 1)
    sheet = m[_SHEET]
    at = sheet.index(b"<sheetData")
    m[_SHEET] = sheet[:at] + b"<x " + attrs + b"/>" + sheet[at:]
    return _deflated(m)


@pytest.mark.parametrize("build", [_n8_one_element, _n8_spread, _n8_namespaced, _n8_pr_and_sheet],
                         ids=["one element 1.45 M", "14,500 x 100", "1 M p:aN", "workbookPr and sheet"])
def test_n3_r5_b1_attribute_probes_are_too_large_in_bounded_time(build) -> None:
    data = build()
    assert len(data) < _UPLOAD
    assert _bounded(data, 1.0, 60) == "NATIVE_TOO_LARGE"


def test_n3_r5_b1_an_equals_run_past_4096_is_refused_and_one_at_4096_reads() -> None:
    def text_cell(n: int) -> bytes:
        return b'<row r="9"><c r="E9" t="inlineStr"><is><t>' + b"=" * n + b"</t></is></c></row>"
    assert _xlsx._ATTR_RUN_MAX == 4096
    assert _outcome(_workbook(text_cell(4_097))) == "NATIVE_TOO_LARGE"
    assert _outcome(_workbook(text_cell(4_096))) == "ok 4"  # the scan ran (more than 4,096 `=` in the member)
    assert zip_members(_workbook(text_cell(4_096)))[_SHEET].count(b"=") > 4096


def _names_in(data: bytes) -> set[str]:
    """The distinct attribute names of the four members the reader parses, counted by ElementTree here."""
    from xml.etree import ElementTree
    names: set[str] = set()
    m = zip_members(data)
    for member in ("xl/workbook.xml", "xl/_rels/workbook.xml.rels", "xl/sharedStrings.xml", _SHEET):
        if member in m:
            for _, element in ElementTree.iterparse(io.BytesIO(m[member])):
                names.update(element.attrib)
    return names


def test_n3_r5_b1_more_than_512_distinct_names_are_refused_and_512_read() -> None:
    assert _xlsx._ATTR_NAMES_MAX == 512
    base = len(_names_in(budget_bytes()))

    def spread(count: int) -> bytes:  # `count` new names over elements of 10
        new = [b"n%d" % i for i in range(count)]
        return _before_sheet_data(b"".join(b"<x " + _attrs(new[i:i + 10]) + b"/>" for i in range(0, count, 10)))
    assert len(_names_in(spread(512 - base))) == 512
    assert _outcome(spread(512 - base)) == "ok 3"
    assert _outcome(spread(513 - base)) == "NATIVE_TOO_LARGE"


def test_n3_r5_b1_legitimate_workbooks_read_as_without_the_scan(monkeypatch) -> None:
    """The lakeside fixture, and 10,000 rows (9,997 added) of 20 numeric cells (about 610,000 `=`, so the run scan
    runs), read as they do with the scan switched off."""
    rows = b"".join(b'<row r="%d">' % r + b"".join(b'<c r="%s%d" s="1" t="n"><v>%d</v></c>' % (bytes([65 + c]), r, c)
                                                  for c in range(20)) + b"</row>" for r in range(10, 10_007))
    wide = _workbook(rows)
    assert zip_members(wide)[_SHEET].count(b"=") > 600_000
    with_scan = [_outcome(budget_bytes()), _bounded(wide, 3.0, 120)]
    monkeypatch.setattr(_xlsx, "_ATTR_RUN_MAX", 10**9)
    monkeypatch.setattr(_xlsx, "_ATTR_NAMES_MAX", 10**9)
    assert with_scan == [_outcome(budget_bytes()), _outcome(wide)]
    assert with_scan[0] == "ok 3" and with_scan[1] == "ok 10000"


def test_n3_r5_b1_date1904_is_kept_alone() -> None:
    from xml.etree import ElementTree
    target = _xlsx._Workbook([10], set())
    parser = ElementTree.XMLParser(target=target)
    parser.feed('<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                '<workbookPr date1904="1" codeName="x"/><workbookPr date1904="0"/></workbook>')
    parser.close()
    assert target.date1904 == "1" and not hasattr(target, "pr")


def test_n3_r5_b2_csv_row_probes_are_too_large_in_bounded_time() -> None:
    one_line = _kobo_head() + b"\x80;" * (_UPLOAD // 2 - 2_000) + b"\n"  # cp1252: U+20AC each, one line
    quoted = _kobo_head() + (";".join(["ab"] * 30_000) + ';"\n";').encode() * 90 + b"x\n"  # one row, 90 lines
    for data in (one_line, quoted):
        assert len(data) < _UPLOAD
        assert _kobo_bounded(data, 0.5, 60) == "NATIVE_TOO_LARGE"
    with pytest.raises(CanonicalRefused) as refused:
        split_file(compile_profile(profile(KOBO), 1), quoted)
    # lines 4 on are 90,002 characters each: the 12th (line 15) takes the row past 1 Mi characters
    assert (refused.value.code, refused.value.path) == ("NATIVE_TOO_LARGE", "row.15")


def test_n3_r5_b2_a_row_of_exactly_the_cap_is_not_refused_by_it() -> None:
    assert _layouts._ROW_CHARS_MAX == 1_048_576
    head = _kobo_head()
    row = kobo_bytes().splitlines(keepends=True)[3].rstrip(b"\r\n")

    def of(chars: int) -> bytes:  # the row, then fields under csv's 128 Ki field limit, to `chars` with its CR LF
        fill = chars - len(row) - 2
        fields = [b"9" * 100_000] * (fill // 100_001) + [b"9" * (fill % 100_001 - 1)]
        return row + b";" + b";".join(fields) + b"\r\n"
    exact = of(_layouts._ROW_CHARS_MAX)
    assert len(exact.decode("cp1252")) == _layouts._ROW_CHARS_MAX
    assert _kobo_outcome(head + exact) == "ok 1"  # read; the row's extra cells refuse that row alone
    assert _kobo_outcome(head + of(_layouts._ROW_CHARS_MAX + 1)) == "NATIVE_TOO_LARGE"
    assert _kobo_outcome(kobo_bytes()) == "ok 4"


def test_n3_r5_b2_the_windowed_lines_are_stringio_lines() -> None:
    import random
    rnd = random.Random(2026)
    for _ in range(3_000):
        text = "".join(rnd.choice(["a", "bb", "\r", "\n", "\r\n", ";", '"']) for _ in range(rnd.randrange(60)))
        want = list(io.StringIO(text, newline=""))
        for window in (2, 3, 5, 8):
            if all(len(line) < window for line in want):
                assert list(_layouts._physical_lines(text, window)) == want, (text, window)


def _cd_entry(name: bytes, extra: bytes = b"") -> bytes:
    return struct.pack("<4s6H3L5H2L", b"PK\x01\x02", 20, 20, 0, 0, 0, 0, 0, 0, 0, len(name), len(extra), 0, 0, 0, 0,
                       0) + name + extra


def _with_entries(base: bytes, entries: list[bytes], *, zip64: bool = False) -> bytes:
    """`base` with `entries` appended to its central directory (review r5's builder); `zip64` writes the end as a
    zip64 end record and locator behind a sentinel end record, as `zipfile` reads one."""
    end = base.rindex(b"PK\x05\x06")
    count = struct.unpack("<H", base[end + 10:end + 12])[0]
    size, offset = struct.unpack("<LL", base[end + 12:end + 20])
    body, directory = base[:offset], base[offset:offset + size] + b"".join(entries)
    n = count + len(entries)
    if zip64:
        record = struct.pack("<4sQ2H2L4Q", b"PK\x06\x06", 44, 45, 45, 0, 0, n, n, len(directory), len(body))
        locator = struct.pack("<4sLQL", b"PK\x06\x07", 0, len(body) + len(directory), 1)
        return body + directory + record + locator + struct.pack("<4s4H2LH", b"PK\x05\x06", 0, 0, 0xFFFF, 0xFFFF,
                                                                 0xFFFFFFFF, 0xFFFFFFFF, 0)
    return body + directory + struct.pack("<4s4H2LH", b"PK\x05\x06", 0, 0, n, n, len(directory), len(body), 0)


def test_n3_r5_b3_quadratic_extra_fields_are_too_large_in_bounded_time() -> None:
    extra = b"\x99\x99\x00\x00" * (65_532 // 4)  # 16,383 empty extra records per entry
    data = _with_entries(budget_bytes(), [_cd_entry(b"q%d" % i, extra) for i in range(125)])
    assert len(data) < _UPLOAD
    import time
    started = time.perf_counter()
    assert _outcome(data) == "NATIVE_TOO_LARGE"
    assert time.perf_counter() - started < 0.2


def test_n3_r5_b3_the_entry_count_and_directory_size() -> None:
    assert (_xlsx._ZIP_ENTRIES_MAX, _xlsx._ZIP_DIRECTORY_MAX) == (256, 256 * 1024)
    base = budget_bytes()
    count = len(zip_members(base))
    assert _outcome(_with_entries(base, [_cd_entry(b"e%d" % i) for i in range(257)])) == "NATIVE_TOO_LARGE"
    assert _outcome(_with_entries(base, [_cd_entry(b"e%d" % i) for i in range(256 - count)])) != "NATIVE_TOO_LARGE"
    big_name = [_cd_entry(b"n" * 60_000 + b"%d" % i) for i in range(5)]  # 5 entries, a 300 kB directory
    assert _outcome(_with_entries(base, big_name)) == "NATIVE_TOO_LARGE"
    ten = rezip({**zip_members(base), **{f"xl/media/m{i}.bin": b"" for i in range(10 - count)}})
    assert len(zip_members(ten)) == 10 and _outcome(ten) == "ok 3"
    assert _outcome(b"PK\x03\x04 no end record") == "NATIVE_WORKBOOK"


def test_n3_r5_b3_the_zip64_end_record_is_read() -> None:
    base = budget_bytes()
    as_zip64 = _with_entries(base, [], zip64=True)
    with zipfile.ZipFile(io.BytesIO(as_zip64)) as z:  # `zipfile` reads it through the zip64 record
        assert len(z.infolist()) == len(zip_members(base))
    assert _outcome(as_zip64) == "ok 3"
    assert _outcome(_with_entries(base, [_cd_entry(b"e%d" % i) for i in range(257)], zip64=True)) == "NATIVE_TOO_LARGE"


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
