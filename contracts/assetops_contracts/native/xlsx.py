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


class _Cell:
    """One `<c>` gathered while streaming: its `r`, `t`, first `<v>` text, a `<f>`, and its first `<is>` text."""

    __slots__ = ("ref", "t", "v", "formula", "inline", "text")  # `inline`: the first `<is>`, None until seen

    def __init__(self, c: ElementTree.Element) -> None:
        self.ref, self.t = c.get("r") or "", c.get("t")
        self.v: str | None = None
        self.formula = False
        self.inline: ElementTree.Element | None = None
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
            return self.text.value() if self.inline is not None else ""
        if t == "str":
            return v or ""
        if t == "b":
            return "TRUE" if (v or "").strip() == "1" else "FALSE"
        if t in (None, "n"):
            return "" if v is None else _number(v)
        return XlsxBad("")  # "e", "d" and anything else


_MAX_COLUMN = 16383  # Excel's XFD
_MAX_ROW = 1_048_576  # Excel's last row
_PAD_BUDGET = 2_000_000  # total padded cells `xlsx_rows` may build
# The one work bound (fix round r3): every XML element the reader parses, in every member it reads, costs one unit.
# Rows and cells are elements, so rows plus cells visited never exceed it, and every loop after the parse runs over
# what the parse kept. A workbook past it is `NATIVE_WORKBOOK`.
_WORK_MAX = 1_000_000
_FEED = 1 << 16
_ROW, _C, _V, _F, _IS, _T, _R, _SI = (f"{_MAIN}{n}" for n in ("row", "c", "v", "f", "is", "t", "r", "si"))


def _events(z: zipfile.ZipFile, name: str, work: list[int]):
    """`(event, element, open ancestors)` for each start and end of member `name`, parsed in slices. Each start
    costs one unit of `work[0]`; an ended element is dropped from its parent, so the parse keeps no tree."""
    raw = z.read(name)  # KeyError when missing
    if raw.startswith(_BOM):
        raw = raw[len(_BOM):]
    text = raw.decode("utf-8", errors="strict")
    del raw
    if "<!DOCTYPE" in text or "<!ENTITY" in text:
        raise _workbook_error()
    parser = ElementTree.XMLPullParser(("start", "end"))
    stack: list[ElementTree.Element] = []
    for i in range(0, len(text) + _FEED, _FEED):
        if i < len(text):
            parser.feed(text[i:i + _FEED])
        else:
            parser.close()  # ParseError on an empty or unfinished document
        for event, element in parser.read_events():
            if event == "start":
                work[0] -= 1
                if work[0] < 0:
                    raise _workbook_error()
                yield event, element, stack
                stack.append(element)
            else:
                stack.pop()
                yield event, element, stack
                if stack:
                    stack[-1].remove(element)  # its parent's only child: earlier ones went at their own end
                element.clear()


class _Text:
    """`<si>`/`<is>` text while streaming: the node's first `<t>`, or its `<r><t>` runs concatenated."""

    __slots__ = ("direct", "runs")

    def __init__(self) -> None:
        self.direct: str | None = None
        self.runs: list[str] = []

    def end(self, element: ElementTree.Element, stack: list, node: ElementTree.Element) -> None:
        if element.tag != _T:
            return
        if stack[-1] is node:
            if self.direct is None:
                self.direct = element.text or ""
        elif len(stack) >= 2 and stack[-2] is node and stack[-1].tag == _R:
            self.runs.append(element.text or "")

    def value(self) -> str:
        return self.direct if self.direct is not None else "".join(self.runs)


def _read(data: bytes, sheet: str) -> list[tuple[int, dict[int, str]]]:
    z = zipfile.ZipFile(io.BytesIO(bytes(data)))
    infos = z.infolist()
    if any(i.file_size > _MEMBER_MAX for i in infos) or sum(i.file_size for i in infos) > _TOTAL_MAX:
        raise _workbook_error()
    work = [_WORK_MAX]
    date1904: str | None = None
    seen_pr = False
    sheets: list[tuple[str | None, str | None]] = []
    count = 0
    for event, el, stack in _events(z, "xl/workbook.xml", work):
        if event == "end" and len(stack) == 1 and el.tag == f"{_MAIN}workbookPr" and not seen_pr:
            seen_pr, date1904 = True, el.get("date1904")
        elif (event == "end" and len(stack) == 2 and el.tag == f"{_MAIN}sheet"
              and stack[-1].tag == f"{_MAIN}sheets"):
            count += 1
            if not sheets:
                sheets.append((el.get("name"), el.get(f"{_REL}id")))
    if (date1904 or "").strip().lower() in ("1", "true"):
        raise _workbook_error()
    if count != 1 or sheets[0][0] != sheet:
        raise CanonicalRefused("NATIVE_SHEET", "json")
    rid = sheets[0][1]
    target: str | None = None
    found = False
    for event, el, stack in _events(z, "xl/_rels/workbook.xml.rels", work):
        if (event == "end" and not found and len(stack) == 1 and el.tag == f"{_PKG}Relationship"
                and el.get("Id") == rid):
            found, target = True, el.get("Target")
    if not target:
        raise _workbook_error()
    path = target.lstrip("/") if target.startswith("/") else _normpath(_join("xl", target))
    shared: list[str] = []
    if "xl/sharedStrings.xml" in z.namelist():
        text: _Text | None = None
        for event, el, stack in _events(z, "xl/sharedStrings.xml", work):
            depth = len(stack)
            if depth == 1 and el.tag == _SI:
                if event == "start":
                    text = _Text()
                else:
                    shared.append(text.value())
                    text = None
            elif event == "end" and text is not None and depth >= 2:
                text.end(el, stack, stack[1])
    out: list[tuple[int, dict[int, str]]] = []
    previous = 0
    rows: dict[int, tuple[dict[int, str], list[int]]] = {}  # an open row: its cells and its next column index
    cells_open: dict[int, _Cell] = {}  # an open cell, by id
    for event, el, stack in _events(z, path, work):
        tag = el.tag
        if tag == _ROW:
            if event == "start":
                r = el.get("r")
                if r and not re.fullmatch(r"[0-9]+", r, re.ASCII):
                    raise _workbook_error()
                number = int(r) if r else previous + 1  # a row without `r` follows the previous one (§2.3)
                if number <= previous or number > _MAX_ROW:
                    raise _workbook_error()  # row numbers rise strictly, as the format requires
                previous = number
                cells: dict[int, str] = {}
                rows[id(el)] = (cells, [0])
                out.append((number, cells))
            else:
                rows.pop(id(el), None)
            continue
        parent = stack[-1] if stack else None
        if tag == _C and parent is not None and id(parent) in rows:
            if event == "start":
                cells_open[id(el)] = _Cell(el)
                continue
            cell = cells_open.pop(id(el))
            row_cells, following = rows[id(parent)]
            match = _REF.fullmatch(cell.ref)
            index = _column_index(match.group(1)) if match else following[0]
            if index > _MAX_COLUMN:
                raise _workbook_error()
            row_cells[index] = cell.value(shared)
            following[0] = max(following[0], index + 1)  # the next index after the widest cell so far
            continue
        if not cells_open or parent is None:
            continue
        if event == "start":
            if tag == _IS and id(parent) in cells_open and cells_open[id(parent)].inline is None:
                cells_open[id(parent)].inline = el  # the first `<is>` is the cell's text
            continue
        if id(parent) in cells_open:
            cell = cells_open[id(parent)]
            if tag == _V and cell.v is None:
                cell.v = el.text or ""
            elif tag == _F:
                cell.formula = True
        elif tag == _T:
            for at in (-1, -2):  # `<is><t>` or `<is><r><t>`
                if len(stack) > -at and stack[at].tag == _IS:
                    owner = cells_open.get(id(stack[at - 1]))
                    if owner is not None and owner.inline is stack[at]:
                        owner.text.end(el, stack, stack[at])
                    break
    return out


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
