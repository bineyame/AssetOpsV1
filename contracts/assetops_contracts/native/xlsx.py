"""3A6 (spec §2.3; D-3A6.9, D-3A6.13): a single-sheet XLSX workbook read as rows of text, standard library only.

`xlsx_rows` returns `(row number, cells)` pairs in sheet order. A numeric cell is an `XlsxNumber` (Excel's 15
significant digits, plain notation); a cell that cannot be read (an error or ISO-date cell, a value that is not a
finite decimal) is an `XlsxBad("")` marker, judged by `read_rows` only in a column that writes a path. A whole-file
problem raises `CanonicalRefused(NATIVE_WORKBOOK | NATIVE_SHEET, "json")`.
"""

from __future__ import annotations

import io
import re
import zipfile
import zlib
from decimal import ROUND_HALF_EVEN, Context, Decimal, InvalidOperation
from posixpath import join as _join, normpath as _normpath
from xml.etree import ElementTree

from assetops_contracts.canonical import CanonicalRefused

_MAIN = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
_REL = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
_PKG = "{http://schemas.openxmlformats.org/package/2006/relationships}"
_MEMBER_MAX = 16 * 1024 * 1024
_TOTAL_MAX = 64 * 1024 * 1024
_BOM = b"\xef\xbb\xbf"
_REF = re.compile(r"([A-Z]{1,3})([0-9]*)", re.ASCII)
_EXCEL = Context(prec=15, rounding=ROUND_HALF_EVEN)


class XlsxNumber(str):
    """A numeric cell's text (plain notation, at most 15 significant digits)."""


class XlsxBad(str):
    """A cell that cannot be read; its value is `""`."""


def _workbook_error() -> CanonicalRefused:
    return CanonicalRefused("NATIVE_WORKBOOK", "json")


def _number(v: str) -> str:
    try:
        d = Decimal(v.strip())
    except InvalidOperation:
        return XlsxBad("")
    if not d.is_finite():
        return XlsxBad("")
    plain = format(_EXCEL.plus(d).normalize(_EXCEL), "f")
    return XlsxNumber("0" if plain in ("-0", "0") else plain)


def _column_index(letters: str) -> int:
    n = 0
    for ch in letters:
        n = n * 26 + (ord(ch) - 64)
    return n - 1


_MAX_COLUMN = 16383  # Excel's XFD
_MAX_ROW = 1_048_576  # Excel's last row
_PAD_BUDGET = 2_000_000  # total padded cells `xlsx_rows` may build
# Fix round r3, the one work bound: every XML element the reader parses, in every member it reads, costs one unit
# (rows and cells are elements, so rows plus cells visited never pass it). Members are parsed by event with no tree
# kept, and every later loop runs over what the parse kept. A workbook past the bound is `NATIVE_WORKBOOK`.
_WORK_MAX = 500_000
_ROW, _C, _V, _F, _IS, _T, _R, _SI = (f"{_MAIN}{n}" for n in ("row", "c", "v", "f", "is", "t", "r", "si"))
_OTHER, _SHEETS, _IN_ROW, _IN_CELL, _IN_V, _IN_IS, _IN_RUN, _T_DIRECT, _T_RUN = range(9)  # element roles


class _Text:
    """`<si>`/`<is>` text: the node's first `<t>`, or its `<r><t>` runs concatenated."""

    __slots__ = ("direct", "runs")

    def __init__(self) -> None:
        self.direct: str | None = None
        self.runs: list[str] = []

    def value(self) -> str:
        return self.direct if self.direct is not None else "".join(self.runs)


class _Cell:
    """One `<c>`: its `r` and `t`, its first `<v>` text, whether it has an `<f>`, and its first `<is>` text."""

    __slots__ = ("ref", "t", "v", "formula", "inline", "text")

    def __init__(self, attrib: dict) -> None:
        self.ref, self.t = attrib.get("r") or "", attrib.get("t")
        self.v: str | None = None
        self.formula = False
        self.inline = False
        self.text = _Text()

    def value(self, shared: list[str]) -> str:
        t, v = self.t, self.v
        if v is None and self.formula:
            return XlsxBad("")  # a formula with no cached value
        if t == "s":
            try:
                return shared[int(v or "")]
            except (ValueError, IndexError):
                return XlsxBad("")
        if t == "inlineStr":
            return self.text.value() if self.inline else ""
        if t == "str":
            return v or ""
        if t == "b":
            return "TRUE" if (v or "").strip() == "1" else "FALSE"
        if t in (None, "n"):
            return "" if v is None else _number(v)
        return XlsxBad("")  # "e", "d" and anything else


_NONE = (_OTHER, None, None, False)


class _Target:
    """An `XMLParser` target, so no tree is built. Each open element is `[role, owner, text, collecting]`; `text`
    gathers the element's leading text (ElementTree's `.text`) until its first child starts."""

    def __init__(self, work: list[int]) -> None:
        self.work = work
        self.open: list[list] = []

    def start(self, tag: str, attrib: dict) -> None:
        self.work[0] -= 1
        if self.work[0] < 0:
            raise _workbook_error()
        parent = self.open[-1] if self.open else None
        if parent is not None:
            parent[3] = False
        self.open.append(list(self.role(tag, attrib, parent)))

    def data(self, text: str) -> None:
        if self.open and self.open[-1][3]:
            self.open[-1][2].append(text)

    def end(self, tag: str) -> None:
        self.ended(self.open.pop())

    def close(self) -> None:
        return None

    def role(self, tag: str, attrib: dict, parent: list | None) -> tuple:
        return _NONE

    def ended(self, entry: list) -> None:
        pass

    @staticmethod
    def text_role(tag: str, parent: list) -> tuple:
        """Inside an `<si>` or a cell's first `<is>`: its direct `<t>`, an `<r>`, an `<r>`'s `<t>`."""
        if parent[0] == _IN_IS and tag == _T:
            return _T_DIRECT, parent[1], [], True
        if parent[0] == _IN_IS and tag == _R:
            return _IN_RUN, parent[1], None, False
        if parent[0] == _IN_RUN and tag == _T:
            return _T_RUN, parent[1], [], True
        return _NONE

    @staticmethod
    def text_ended(entry: list) -> None:
        if entry[0] == _T_DIRECT and entry[1].direct is None:
            entry[1].direct = "".join(entry[2])
        elif entry[0] == _T_RUN:
            entry[1].runs.append("".join(entry[2]))


class _Workbook(_Target):
    def __init__(self, work: list[int]) -> None:
        super().__init__(work)
        self.pr: dict | None = None
        self.sheets = 0
        self.first: tuple[str | None, str | None] = (None, None)

    def role(self, tag: str, attrib: dict, parent: list | None) -> tuple:
        if len(self.open) == 1 and tag == f"{_MAIN}workbookPr" and self.pr is None:
            self.pr = dict(attrib)
        elif len(self.open) == 1 and tag == f"{_MAIN}sheets":
            return _SHEETS, None, None, False
        elif parent is not None and parent[0] == _SHEETS and tag == f"{_MAIN}sheet":
            self.sheets += 1
            if self.sheets == 1:
                self.first = (attrib.get("name"), attrib.get(f"{_REL}id"))
        return _NONE


class _Rels(_Target):
    def __init__(self, work: list[int], rid: str | None) -> None:
        super().__init__(work)
        self.rid, self.found, self.target = rid, False, None

    def role(self, tag: str, attrib: dict, parent: list | None) -> tuple:
        if len(self.open) == 1 and tag == f"{_PKG}Relationship" and not self.found and attrib.get("Id") == self.rid:
            self.found, self.target = True, attrib.get("Target")
        return _NONE


class _Shared(_Target):
    def __init__(self, work: list[int]) -> None:
        super().__init__(work)
        self.strings: list[str] = []

    def role(self, tag: str, attrib: dict, parent: list | None) -> tuple:
        if len(self.open) == 1 and tag == _SI:
            return _IN_IS, _Text(), None, False
        return _NONE if parent is None else self.text_role(tag, parent)

    def ended(self, entry: list) -> None:
        if entry[0] == _IN_IS and len(self.open) == 1:
            self.strings.append(entry[1].value())
        else:
            self.text_ended(entry)


class _Sheet(_Target):
    def __init__(self, work: list[int], shared: list[str]) -> None:
        super().__init__(work)
        self.shared = shared
        self.rows: list[tuple[int, dict[int, str]]] = []
        self.previous = 0

    def role(self, tag: str, attrib: dict, parent: list | None) -> tuple:
        if tag == _ROW:
            r = attrib.get("r")
            if r and not re.fullmatch(r"[0-9]+", r, re.ASCII):
                raise _workbook_error()
            number = int(r) if r else self.previous + 1  # a row without `r` follows the previous one (§2.3)
            if number <= self.previous or number > _MAX_ROW:
                raise _workbook_error()  # row numbers rise strictly, as the format requires (fix round r3)
            self.previous = number
            cells: dict[int, str] = {}
            self.rows.append((number, cells))
            return _IN_ROW, [cells, 0], None, False  # the row's cells and the index a cell without `r` takes
        if parent is None:
            return _NONE
        role = parent[0]
        if role == _IN_ROW and tag == _C:
            return _IN_CELL, _Cell(attrib), None, False
        if role == _IN_CELL:
            cell = parent[1]
            if tag == _V and cell.v is None:
                return _IN_V, cell, [], True
            if tag == _F:
                cell.formula = True
            elif tag == _IS and not cell.inline:
                cell.inline = True
                return _IN_IS, cell.text, None, False
            return _NONE
        return self.text_role(tag, parent)

    def ended(self, entry: list) -> None:
        role = entry[0]
        if role == _IN_CELL:
            cell, row = entry[1], self.open[-1][1]
            match = _REF.fullmatch(cell.ref)
            index = _column_index(match.group(1)) if match else row[1]
            if index > _MAX_COLUMN:
                raise _workbook_error()
            row[0][index] = cell.value(self.shared)
            row[1] = max(row[1], index + 1)  # one past the widest cell so far
        elif role == _IN_V:
            if entry[1].v is None:
                entry[1].v = "".join(entry[2])
        else:
            self.text_ended(entry)


def _parse(z: zipfile.ZipFile, name: str, target: _Target) -> _Target:
    raw = z.read(name)  # KeyError when missing
    if raw.startswith(_BOM):
        raw = raw[len(_BOM):]
    text = raw.decode("utf-8", errors="strict")
    del raw
    if "<!DOCTYPE" in text or "<!ENTITY" in text:
        raise _workbook_error()
    parser = ElementTree.XMLParser(target=target)
    parser.feed(text)
    parser.close()  # ParseError on an empty or unfinished document
    return target


def _read(data: bytes, sheet: str) -> list[tuple[int, dict[int, str]]]:
    z = zipfile.ZipFile(io.BytesIO(bytes(data)))
    infos = z.infolist()
    if any(i.file_size > _MEMBER_MAX for i in infos) or sum(i.file_size for i in infos) > _TOTAL_MAX:
        raise _workbook_error()
    work = [_WORK_MAX]
    workbook = _parse(z, "xl/workbook.xml", _Workbook(work))
    if workbook.pr is not None and (workbook.pr.get("date1904") or "").strip().lower() in ("1", "true"):
        raise _workbook_error()
    if workbook.sheets != 1 or workbook.first[0] != sheet:
        raise CanonicalRefused("NATIVE_SHEET", "json")
    target = _parse(z, "xl/_rels/workbook.xml.rels", _Rels(work, workbook.first[1])).target
    if not target:
        raise _workbook_error()
    path = target.lstrip("/") if target.startswith("/") else _normpath(_join("xl", target))
    shared: list[str] = []
    if "xl/sharedStrings.xml" in z.namelist():
        shared = _parse(z, "xl/sharedStrings.xml", _Shared(work)).strings
    return _parse(z, path, _Sheet(work, shared)).rows


def xlsx_sparse_rows(data: bytes, sheet: str) -> list[tuple[int, dict[int, str]]]:
    """Spec §2.3. Rows of the one sheet as `(r, {column index: cell})`; nothing is padded."""
    try:
        return _read(data, sheet)
    except (zipfile.BadZipFile, zipfile.LargeZipFile, zlib.error, NotImplementedError, RuntimeError, EOFError,
            KeyError, UnicodeDecodeError, ElementTree.ParseError):
        raise _workbook_error() from None


def xlsx_rows(data: bytes, sheet: str) -> list[tuple[int, list[str]]]:
    """Spec §2.3. Rows of the one sheet named `sheet`, as `(r, cells)`, padded to each row's last cell under a
    total budget (a workbook past it is `NATIVE_WORKBOOK`)."""
    out: list[tuple[int, list[str]]] = []
    total = 0
    for number, sparse in xlsx_sparse_rows(data, sheet):
        width = max(sparse) + 1 if sparse else 0
        total += width
        if total > _PAD_BUDGET:
            raise _workbook_error()
        out.append((number, [sparse.get(i, "") for i in range(width)]))
    return out
