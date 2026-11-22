"""DDR (spec §3.1, D-DDR.2, R9): writes `ddr-board-budget.xlsx`, the operator's board pack, by hand (never through the
reader, W2), and prints the SHA-256 of it and of `ddr-board-budget.profile.json` for the expectation file.

The sheet is 3A6's `build_workbook`; its zip is then rewritten so the bytes are stable: members in one fixed order,
each dated 2026-07-02 00:00:00, deflated at level 9, `create_system` 0, no extra fields. Every cell is text.
"""

from __future__ import annotations

import hashlib
import io
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "3a6"))
from make_budget_xlsx import build_workbook  # noqa: E402

SHEET = "Board pack FY26"
DATE = (2026, 7, 2, 0, 0, 0)
XLSX = HERE / "ddr-board-budget.xlsx"
PROFILE = HERE / "ddr-board-budget.profile.json"

#: Spec §3.1, rows 4 to 19: (Line ID, Site or None, Budget line, Amount as the board writes it).
LINES = [
    ("BB-01", "KOBO-001", "Revenue", "3,420.00"), ("BB-02", "KOBO-001", "Fuel", "875.00"),
    ("BB-03", "KOBO-001", "O&M", "600.00"), ("BB-04", "KOBO-001", "Salaries", "500.00"),
    ("BB-05", "KOBO-001", "Contribution", "1,445.00"),
    ("BB-06", "KISIWA-001", "Revenue", "4,125.00"), ("BB-07", "KISIWA-001", "Fuel", "2,990.00"),
    ("BB-08", "KISIWA-001", "O&M", "700.00"), ("BB-09", "KISIWA-001", "Salaries", "500.00"),
    ("BB-10", "KISIWA-001", "Contribution", "(60.00)"),
    ("BB-11", "MTO-001", "Revenue", "2,240.00"), ("BB-12", "MTO-001", "Fuel", "375.00"),
    ("BB-13", "MTO-001", "O&M", "500.00"), ("BB-14", "MTO-001", "Salaries", "450.00"),
    ("BB-15", "MTO-001", "Contribution", "915.00"),
    ("BB-16", None, "Salaries", "1,200.00"),
]


def _text(ref: str, value: str):
    return (ref, "inlineStr", value)


def rows():
    out = [(1, [_text("A1", "Lakeside Power – Board budget FY2026")]),
           (2, [_text("A2", "Approved 2 July 2026")]),
           (3, [_text(f"{c}3", h) for c, h in zip("ABCDEF", ("Line ID", "Site", "Period", "Budget line", "Amount",
                                                            "Ccy"))])]
    for n, (line_id, site, line, amount) in enumerate(LINES, start=4):
        cells = [_text(f"A{n}", line_id)]
        if site is not None:
            cells.append(_text(f"B{n}", site))
        cells += [_text(f"C{n}", "October 2026"), _text(f"D{n}", line), _text(f"E{n}", amount), _text(f"F{n}", "USD")]
        out.append((n, cells))
    return out


def workbook() -> bytes:
    """`build_workbook`'s members, rewritten in the same order with fixed, clock-free zip headers."""
    source = zipfile.ZipFile(io.BytesIO(build_workbook(rows(), sheet=SHEET)))
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as z:
        for member in source.infolist():
            info = zipfile.ZipInfo(member.filename, date_time=DATE)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 0
            info.extra = b""
            z.writestr(info, source.read(member.filename), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    return out.getvalue()


def main(out_dir: Path = HERE) -> Path:
    target = Path(out_dir) / XLSX.name
    target.write_bytes(workbook())
    print(f"xlsx_sha256 {hashlib.sha256(target.read_bytes()).hexdigest()}")
    print(f"profile_sha256 {hashlib.sha256(PROFILE.read_bytes()).hexdigest()}")
    return target


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else HERE)
