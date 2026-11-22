"""DD4.2 (D-DD.63 "November"): the cold storage ledger extends to `as_of` by repeating 1-6 Oct's generated
admissions 31 days later, named batches excluded, with new refs, no November invoice, OUT rows after as_of unwritten."""
from __future__ import annotations

import csv
import io
from datetime import datetime, timedelta

from .books_support import built, files_by_name

COLD = "harvest-cold"


def _ledger_rows():
    files = files_by_name(built()[3])
    name = next(n for n in files if n.startswith(COLD) and "cold-storage-ledger" in n)
    return list(csv.DictReader(io.StringIO(files[name].data.decode("utf-8"))))


def test_november_admissions_repeat_1_to_6_october_shifted_31_days():
    rows = _ledger_rows()
    as_of = "2026-11-06"
    ins = [r for r in rows if r["Direction"] == "IN"]
    october = sorted((r["Site"], r["At"], r["Crates"]) for r in ins
                     if "2026-10-01" <= r["At"][:10] <= "2026-10-06" and not r["Batch"].startswith("B-"))
    november = sorted((r["Site"], r["At"], r["Crates"]) for r in ins if r["At"][:7] == "2026-11")
    assert october, "the fixture admits generated batches on 1-6 Oct"
    shifted = sorted((s, (datetime.fromisoformat(a) + timedelta(days=31)).isoformat(), c) for s, a, c in october)
    assert november == shifted
    refs = [r["Batch"] for r in ins]
    assert len(refs) == len(set(refs)), "November batches carry new refs"
    assert all(r["At"][:10] <= as_of for r in rows), "no movement after as_of is written"


def test_no_november_invoice():
    files = files_by_name(built()[3])
    name = next(n for n in files if n.startswith(COLD) and "cold-storage-invoicing" in n)
    rows = list(csv.DictReader(io.StringIO(files[name].data.decode("utf-8"))))
    assert rows and not [r for r in rows if r["Month"] == "2026-11"]
