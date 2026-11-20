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


def _member(z: zipfile.ZipFile, name: str) -> ElementTree.Element:
    raw = z.read(name)  # KeyError when missing
    if raw.startswith(_BOM):
        raw = raw[len(_BOM):]
    text = raw.decode("utf-8", errors="strict")
    if "<!DOCTYPE" in text or "<!ENTITY" in text:
        raise _workbook_error()
    return ElementTree.fromstring(text)


def _text(node: ElementTree.Element | None) -> str:
    """`<si>`/`<is>` text: its `<t>`, or its `<r><t>` runs concatenated."""
    if node is None:
        return ""
    direct = node.find(f"{_MAIN}t")
    if direct is not None:
        return direct.text or ""
    return "".join(t.text or "" for r in node.findall(f"{_MAIN}r") for t in r.findall(f"{_MAIN}t"))


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


def _cell(c: ElementTree.Element, shared: list[str]) -> str:
    t = c.get("t")
    v_node = c.find(f"{_MAIN}v")
    v = None if v_node is None else (v_node.text or "")
    if t == "s":
        try:
            return shared[int(v or "")]
        except (ValueError, IndexError):
            return XlsxBad("")
    if t == "inlineStr":
        return _text(c.find(f"{_MAIN}is"))
    if t == "str":
        return v or ""
    if t == "b":
        return "TRUE" if (v or "").strip() == "1" else "FALSE"
    if t in (None, "n"):
        return "" if v is None else _number(v)
    return XlsxBad("")  # "e", "d" and anything else


def _read(data: bytes, sheet: str) -> list[tuple[int, list[str]]]:
    z = zipfile.ZipFile(io.BytesIO(bytes(data)))
    infos = z.infolist()
    if any(i.file_size > _MEMBER_MAX for i in infos) or sum(i.file_size for i in infos) > _TOTAL_MAX:
        raise _workbook_error()
    workbook = _member(z, "xl/workbook.xml")
    pr = workbook.find(f"{_MAIN}workbookPr")
    if pr is not None and (pr.get("date1904") or "").strip().lower() in ("1", "true"):
        raise _workbook_error()
    sheets = workbook.findall(f"{_MAIN}sheets/{_MAIN}sheet")
    if len(sheets) != 1 or sheets[0].get("name") != sheet:
        raise CanonicalRefused("NATIVE_SHEET", "json")
    rid = sheets[0].get(f"{_REL}id")
    rels = _member(z, "xl/_rels/workbook.xml.rels")
    target = next((r.get("Target") for r in rels.findall(f"{_PKG}Relationship") if r.get("Id") == rid), None)
    if not target:
        raise _workbook_error()
    path = target.lstrip("/") if target.startswith("/") else _normpath(_join("xl", target))
    shared: list[str] = []
    if "xl/sharedStrings.xml" in z.namelist():
        shared = [_text(si) for si in _member(z, "xl/sharedStrings.xml").findall(f"{_MAIN}si")]
    root = _member(z, path)
    out: list[tuple[int, list[str]]] = []
    previous = 0
    for row in root.iter(f"{_MAIN}row"):
        r = row.get("r")
        number = int(r) if r and r.isdigit() else previous + 1
        previous = number
        cells: list[str] = []
        for c in row.findall(f"{_MAIN}c"):
            match = _REF.fullmatch(c.get("r") or "")
            index = _column_index(match.group(1)) if match else len(cells)
            while len(cells) < index:
                cells.append("")
            value = _cell(c, shared)
            if index < len(cells):
                cells[index] = value
            else:
                cells.append(value)
        out.append((number, cells))
    return out


def xlsx_rows(data: bytes, sheet: str) -> list[tuple[int, list[str]]]:
    """Spec §2.3. Rows of the one sheet named `sheet`, as `(r, cells)`."""
    try:
        return _read(data, sheet)
    except (zipfile.BadZipFile, zipfile.LargeZipFile, zlib.error, NotImplementedError, RuntimeError, EOFError,
            KeyError, UnicodeDecodeError, ElementTree.ParseError):
        raise _workbook_error() from None
