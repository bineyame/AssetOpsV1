"""3A6 (spec §4.2): writes `lakeside-budget.xlsx` by hand, standard library only (never through the reader, W2).

Every zip entry is dated 1980-01-01 00:00:00 and stored (`ZIP_STORED`), so the bytes are stable across zlib builds;
test X0 compares the committed workbook with `build_workbook(GOLDEN_ROWS)`.
"""

from __future__ import annotations

import io
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr

_DATE = (1980, 1, 1, 0, 0, 0)
_CONTENT_TYPES = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
    '<Default Extension="xml" ContentType="application/xml"/>'
    '<Override PartName="/xl/workbook.xml" '
    'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
    '<Override PartName="/xl/worksheets/sheet1.xml" '
    'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
    '</Types>')
_RELS = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" '
    'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
    'Target="xl/workbook.xml"/></Relationships>')
_WORKBOOK_RELS = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" '
    'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
    'Target="worksheets/sheet1.xml"/></Relationships>')

GOLDEN_ROWS = [
    (1, [("A1", "inlineStr", "Site"), ("B1", "inlineStr", "Month"), ("C1", "inlineStr", "Line"),
         ("D1", "inlineStr", "Amount"), ("E1", "inlineStr", "Currency")]),
    (2, [("A2", "inlineStr", "KOBO-001"), ("B2", "inlineStr", "Oct-2026"), ("C2", "inlineStr", "Revenue"),
         ("D2", None, "3420"), ("E2", "inlineStr", "USD")]),
    (3, [("A3", "inlineStr", "KOBO-001"), ("B3", "inlineStr", "Oct-2026"), ("C3", "inlineStr", "Diesel"),
         ("D3", None, "874.99999999999989"), ("E3", "inlineStr", "USD")]),
    (4, [("A4", "inlineStr", "KOBO-001"), ("B4", None, "46296"), ("C4", "inlineStr", "kWh sold"),
         ("D4", None, "8550")]),
]


def _workbook(sheet: str) -> str:
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            f'<sheets><sheet name={quoteattr(sheet)} sheetId="1" r:id="rId1"/></sheets></workbook>')


def _cell(ref: str, t: str | None, v: str) -> str:
    if t is None:
        return f'<c r="{ref}"><v>{escape(v)}</v></c>'
    if t == "inlineStr":
        return f'<c r="{ref}" t="inlineStr"><is><t>{escape(v)}</t></is></c>'
    return f'<c r="{ref}" t="{t}"><v>{escape(v)}</v></c>'


def _sheet(rows) -> str:
    body = "".join(f'<row r="{r}">' + "".join(_cell(*c) for c in cells) + "</row>" for r, cells in rows)
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            f'<sheetData>{body}</sheetData></worksheet>')


def build_workbook(rows, *, sheet: str = "Budget 2026") -> bytes:
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_STORED) as z:
        for name, text in (("[Content_Types].xml", _CONTENT_TYPES), ("_rels/.rels", _RELS),
                           ("xl/workbook.xml", _workbook(sheet)), ("xl/_rels/workbook.xml.rels", _WORKBOOK_RELS),
                           ("xl/worksheets/sheet1.xml", _sheet(rows))):
            info = zipfile.ZipInfo(name, date_time=_DATE)
            info.compress_type = zipfile.ZIP_STORED
            z.writestr(info, text.encode("utf-8"))
    return out.getvalue()


def main() -> None:
    (Path(__file__).resolve().parent / "lakeside-budget.xlsx").write_bytes(build_workbook(GOLDEN_ROWS))


if __name__ == "__main__":
    main()
