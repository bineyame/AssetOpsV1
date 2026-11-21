"""3A6 (spec §2.3; D-3A6.9, D-3A6.13): a single-sheet XLSX workbook read as rows of text, standard library only.

`xlsx_rows` returns `(row number, cells)` pairs in sheet order. A numeric cell is an `XlsxNumber` (Excel's 15
significant digits, plain notation); a cell that cannot be read (an error or ISO-date cell, a value that is not a
finite decimal) is an `XlsxBad("")` marker, judged by `read_rows` only in a column that writes a path. A whole-file
problem raises `CanonicalRefused(NATIVE_WORKBOOK | NATIVE_SHEET, "json")`; a workbook past a resource bound raises
`CanonicalRefused(NATIVE_TOO_LARGE, "json")` (fix round r5, D-3A6.25).
"""

from __future__ import annotations

import io
import re
import struct
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
    """A format problem: not a workbook this reader can read."""
    return CanonicalRefused("NATIVE_WORKBOOK", "json")


def _too_large() -> CanonicalRefused:
    """Fix round r5 (D-3A6.25): past a resource bound; the file may be well formed but is too much to read."""
    return CanonicalRefused("NATIVE_TOO_LARGE", "json")


def _number(v: str) -> str:
    try:
        d = Decimal(v.strip())
    except InvalidOperation:
        return XlsxBad("")
    if not d.is_finite():
        return XlsxBad("")
    if d.is_zero():
        return XlsxNumber("0")
    if not -324 <= d.adjusted() <= 308:
        # fix round r3: past a double's range (Excel holds doubles); plain notation of `1E+999999` is a million
        # characters from eleven bytes, and `1E+9999999` overflows the context
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
# kept, and every later loop runs over what the parse kept. A workbook past the bound is `NATIVE_TOO_LARGE` (r5).
_WORK_MAX = 500_000
# Fix round r4 (review N5, N6): bounds on what the element count cannot see. Member bytes are counted as they are
# inflated (a member's declared size is the uploader's word), and the characters every cell delivers are charged to
# one workbook-wide budget, so a shared string referenced from every row costs its length each time.
_CHUNK = 64 * 1024
_CHAR_MAX = 16 * 1024 * 1024
# Fix round r5 (D-3A6.24), bounds the envelope (spec §2.12) holds anyway, kept so a common attack costs milliseconds:
# N8, attributes: XML forbids a raw `<` in an attribute value, so the `=` between two `<` bound one element's
# attributes; and the distinct attribute names of the workbook (expat keeps each in its name cache).
_ATTR_RUN_MAX = 4096
_ATTR_NAMES_MAX = 512
_RUN = re.compile(r"[^<]+")
# N10, the zip directory, read from its end record before `zipfile` decodes it (extra fields decode quadratically).
_ZIP_ENTRIES_MAX = 256
_ZIP_DIRECTORY_MAX = 256 * 1024
_EOCD, _EOCD64, _LOCATOR = b"PK\x05\x06", b"PK\x06\x06", b"PK\x06\x07"
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

    def __init__(self, work: list[int], names: set[str]) -> None:
        self.work = work
        self.names = names  # r5 (N8): the workbook's distinct attribute names, one set across the four parses
        self.open: list[list] = []

    def start(self, tag: str, attrib: dict) -> None:
        self.work[0] -= 1
        if self.work[0] < 0:
            raise _too_large()
        if attrib:
            self.names.update(attrib)
            if len(self.names) > _ATTR_NAMES_MAX:
                raise _too_large()
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
    def __init__(self, work: list[int], names: set[str]) -> None:
        super().__init__(work, names)
        self.pr_seen = False
        self.date1904: str | None = None  # r5 (N8): only this, not the element's whole attribute dict
        self.sheets = 0
        self.first: tuple[str | None, str | None] = (None, None)

    def role(self, tag: str, attrib: dict, parent: list | None) -> tuple:
        if len(self.open) == 1 and tag == f"{_MAIN}workbookPr" and not self.pr_seen:
            self.pr_seen, self.date1904 = True, attrib.get("date1904")
        elif len(self.open) == 1 and tag == f"{_MAIN}sheets":
            return _SHEETS, None, None, False
        elif parent is not None and parent[0] == _SHEETS and tag == f"{_MAIN}sheet":
            self.sheets += 1
            if self.sheets == 1:
                self.first = (attrib.get("name"), attrib.get(f"{_REL}id"))
        return _NONE


class _Rels(_Target):
    def __init__(self, work: list[int], names: set[str], rid: str | None) -> None:
        super().__init__(work, names)
        self.rid, self.found, self.target = rid, False, None

    def role(self, tag: str, attrib: dict, parent: list | None) -> tuple:
        if len(self.open) == 1 and tag == f"{_PKG}Relationship" and not self.found and attrib.get("Id") == self.rid:
            self.found, self.target = True, attrib.get("Target")
        return _NONE


class _Shared(_Target):
    def __init__(self, work: list[int], names: set[str]) -> None:
        super().__init__(work, names)
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
    def __init__(self, work: list[int], names: set[str], shared: list[str], after: int = 0,
                 keep: int | None = None) -> None:
        super().__init__(work, names)
        self.shared = shared
        self.rows: list[tuple[int, dict[int, str]]] = []
        self.previous = 0
        self.chars = _CHAR_MAX
        self.after, self.keep, self.kept = after, keep, 0

    def role(self, tag: str, attrib: dict, parent: list | None) -> tuple:
        if tag == _ROW:
            r = attrib.get("r")
            if r and (not re.fullmatch(r"[0-9]+", r, re.ASCII) or len(r.lstrip("0")) > 7):
                raise _workbook_error()  # past `_MAX_ROW` by its length, before `int` meets thousands of digits
            number = int(r) if r else self.previous + 1  # a row without `r` follows the previous one (§2.3)
            if number <= self.previous or number > _MAX_ROW:
                raise _workbook_error()  # row numbers rise strictly, as the format requires (fix round r3)
            self.previous = number
            cells: dict[int, str] = {}
            self.rows.append((number, cells))
            return _IN_ROW, [cells, 0, number], None, False  # cells, the index a cell without `r` takes, `r`
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
            value = cell.value(self.shared)
            self.chars -= len(value)  # fix round r4 (N6): every delivered character, a shared one each time
            if self.chars < 0:
                raise _too_large()
            row[0][index] = value
            row[1] = max(row[1], index + 1)  # one past the widest cell so far
        elif role == _IN_ROW:
            # fix round r4 (N7): past `keep` non-empty rows after row `after`, the parse stops (the caller's ceiling)
            cells, number = entry[1][0], entry[1][2]
            if self.keep is not None and number > self.after and any(v != "" for v in cells.values()):
                self.kept += 1
                if self.kept > self.keep:
                    raise _Enough
        elif role == _IN_V:
            if entry[1].v is None:
                entry[1].v = "".join(entry[2])
        else:
            self.text_ended(entry)


class _Enough(Exception):
    """The sheet parse has kept one row past the caller's ceiling."""


def _member(z: zipfile.ZipFile, name: str, left: list[int]) -> bytes:
    """Fix round r4 (N5): a member's bytes, inflated a chunk at a time and counted as they come, refused past the
    member cap or past what is left of the total; the declared size is not trusted."""
    info = z.getinfo(name)  # KeyError when missing
    if info.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
        raise _workbook_error()  # bzip2 and lzma inflate a whole read at once; Excel writes deflate only
    cap, size, chunks = min(_MEMBER_MAX, left[0]), 0, []
    with z.open(info) as f:
        while chunk := f.read(_CHUNK):  # `ZipExtFile.read(n)` gives the decompressor `n` as its output limit
            size += len(chunk)
            if size > cap:
                raise _too_large()
            chunks.append(chunk)
    left[0] -= size
    return b"".join(chunks)


def _parse(z: zipfile.ZipFile, name: str, target: _Target, left: list[int]) -> _Target:
    raw = _member(z, name, left)
    if raw.startswith(_BOM):
        raw = raw[len(_BOM):]
    text = raw.decode("utf-8", errors="strict")
    del raw
    if "<!DOCTYPE" in text or "<!ENTITY" in text:
        raise _workbook_error()
    if text.count("=") > _ATTR_RUN_MAX:  # r5 (N8): one linear scan, only when the member could hold such a run
        for run in _RUN.finditer(text):
            if text.count("=", run.start(), run.end()) > _ATTR_RUN_MAX:
                raise _too_large()
    parser = ElementTree.XMLParser(target=target)
    parser.feed(text)
    parser.close()  # ParseError on an empty or unfinished document
    return target


def _directory_check(data: bytes) -> None:
    """Fix round r5 (N10): before `zipfile` decodes the central directory, its size and entry count from the end
    record (found as `zipfile` finds it), and from the zip64 end record when a locator precedes it; a workbook has
    about 10 entries in about 1 KiB. No end record is `NATIVE_WORKBOOK`, as `zipfile` would refuse it."""
    tail = data[-65_557:]
    at = len(tail) - 22
    if not (at >= 0 and tail[at:at + 4] == _EOCD and tail[-2:] == b"\x00\x00"):
        at = tail.rfind(_EOCD)
        if at < 0 or len(tail) - at < 22:
            raise _workbook_error()
    entries, size = struct.unpack("<HL", tail[at + 10:at + 16])  # total entries, directory size
    candidates = []
    end = len(data) - len(tail) + at  # the end record's offset in the upload
    if end >= 20 and data[end - 20:end - 16] == _LOCATOR:  # `zipfile` then reads the zip64 record's values
        reloff = struct.unpack("<Q", data[end - 12:end - 4])[0]
        for start in {reloff, end - 20 - 56}:  # where `zipfile` looks for it: at the locator's offset, or just before
            record = data[start:start + 56] if 0 <= start < len(data) else b""
            if len(record) == 56 and record.startswith(_EOCD64):
                candidates.append(struct.unpack("<QQ", record[32:48]))  # total entries, directory size
    if not candidates:  # no zip64 record: the end record's own values (a sentinel there is refused as too large)
        candidates.append((entries, size))
    if any(n > _ZIP_ENTRIES_MAX or s > _ZIP_DIRECTORY_MAX for n, s in candidates):
        raise _too_large()


def _read(data: bytes, sheet: str, after: int = 0, keep: int | None = None) -> list[tuple[int, dict[int, str]]]:
    data = bytes(data)
    _directory_check(data)
    z = zipfile.ZipFile(io.BytesIO(data))
    infos = z.infolist()
    if any(i.file_size > _MEMBER_MAX for i in infos) or sum(i.file_size for i in infos) > _TOTAL_MAX:
        raise _too_large()
    work, left, names = [_WORK_MAX], [_TOTAL_MAX], set()
    workbook = _parse(z, "xl/workbook.xml", _Workbook(work, names), left)
    if (workbook.date1904 or "").strip().lower() in ("1", "true"):
        raise _workbook_error()
    if workbook.sheets != 1 or workbook.first[0] != sheet:
        raise CanonicalRefused("NATIVE_SHEET", "json")
    target = _parse(z, "xl/_rels/workbook.xml.rels", _Rels(work, names, workbook.first[1]), left).target
    if not target:
        raise _workbook_error()
    path = target.lstrip("/") if target.startswith("/") else _normpath(_join("xl", target))
    shared: list[str] = []
    if "xl/sharedStrings.xml" in z.namelist():
        shared = _parse(z, "xl/sharedStrings.xml", _Shared(work, names), left).strings
    rows = _Sheet(work, names, shared, after, keep)
    try:
        _parse(z, path, rows, left)
    except _Enough:
        pass  # the rows so far end with the one past the ceiling
    return rows.rows


def xlsx_sparse_rows(data: bytes, sheet: str, *, after: int = 0,
                     keep: int | None = None) -> list[tuple[int, dict[int, str]]]:
    """Spec §2.3. Rows of the one sheet as `(r, {column index: cell})`; nothing is padded. With `keep`, the read
    stops at the first row past `keep` non-empty rows numbered above `after` (that row is the last one returned)."""
    try:
        return _read(data, sheet, after, keep)
    except (zipfile.BadZipFile, zipfile.LargeZipFile, zlib.error, NotImplementedError, RuntimeError, EOFError,
            KeyError, UnicodeDecodeError, ElementTree.ParseError):
        raise _workbook_error() from None


def xlsx_rows(data: bytes, sheet: str) -> list[tuple[int, list[str]]]:
    """Spec §2.3. Rows of the one sheet named `sheet`, as `(r, cells)`, padded to each row's last cell under a
    total budget (a workbook past it is `NATIVE_TOO_LARGE`)."""
    out: list[tuple[int, list[str]]] = []
    total = 0
    for number, sparse in xlsx_sparse_rows(data, sheet):
        width = max(sparse) + 1 if sparse else 0
        total += width
        if total > _PAD_BUDGET:
            raise _too_large()
        out.append((number, [sparse.get(i, "") for i in range(width)]))
    return out
