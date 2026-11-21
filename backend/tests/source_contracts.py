"""3A3 (spec §4; D-3A3.5): the source contract cases. Not collected (no `test_` prefix).

A reader is registered in `READERS` only with a case here (test S2), and every case passes C1 to C10
(`test_3a3_source_contract.py`). `3A6` adds `PROFILE_CASES` (admitted source profiles; not in `READERS`).

- `golden`, `expected`: the hand-written native file and its canonical records (`fixtures/3a3/`), never produced by
  `read_layout` (W2).
- `required_headers`: blanking each one's cell in row 2 refuses row 2 only, with 2a's code (C3).
- `amount_header`, `clock_header`/`bad_clock`, `revision_header`, `coded` (header, a value outside its map: one per
  column that writes a coded path, checked by `assert_coded_probes` against `CODED_PATHS_EXPECTED`, never against
  the layout's maps; 3A6, D-3A6.6), `personal_raw` (raw customer or staff refs that must never be stored or answered).
- 3A6 (spec §2.10): the file's `encoding`, `delimiter`, `header_row` and `line_end`; `bad_number` (cell, code) and
  `bad_clock_code`; `versioning` (`"column"`, `"constant"` or `"digest"`); C6's `changed_amount`; `profile` (the
  profile file a profile case is admitted from before C1).
- `field_for`: a blanked header mapped to the header 2a's first refusal names when they differ (a 2a ordering fact,
  each with its one-line reason).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "3a3"
FIXTURES_3A6 = Path(__file__).resolve().parent / "fixtures" / "3a6"
#: Spec §2.10 (handshake R2): the twelve coded canonical paths, written here, never imported from the engine.
CODED_PATHS_EXPECTED = frozenset({"kind", "status", "subject.kind", "quantity.unit", "body.line_type",
                                  "body.tariff_class", "body.method", "body.category", "body.direction",
                                  "body.read_type", "body.contract_type", "body.factor_id"})


@dataclass(frozen=True)
class ContractCase:
    reader_id: str
    golden: Path
    expected: Path
    required_headers: tuple[str, ...]
    amount_header: str
    clock_header: str
    bad_clock: str
    revision_header: str | None
    coded: tuple[tuple[str, str], ...]
    personal_raw: tuple[str, ...]
    field_for: Mapping[str, str] = MappingProxyType({})
    encoding: str = "utf-8"
    delimiter: str = ","
    header_row: int = 1
    line_end: str = "\n"
    bad_number: tuple[str, str] = ("12,5", "CANONICAL_NUMBER")
    bad_clock_code: str = "CANONICAL_CLOCK"
    versioning: str = "column"  # "column" | "constant" | "digest"
    changed_amount: str = "999.00"
    profile: Path | None = None


def coded_headers(layout) -> set[str]:
    """The headers of the layout's columns that write any path of `CODED_PATHS_EXPECTED` (never `Column.maps`)."""
    return {c.header for c in layout.columns if any(p in CODED_PATHS_EXPECTED for p in c.paths)}


def assert_coded_probes(case: ContractCase, layout) -> None:
    """Every column writing a coded path has exactly one value-outside-the-map probe in the case."""
    declared = [h for h, _ in case.coded]
    if coded_headers(layout) != set(declared) or len(declared) != len(set(declared)):
        raise AssertionError(f"{case.reader_id}: coded headers {sorted(coded_headers(layout))}, "
                             f"probed {sorted(declared)}")


def _files(layout_id: str) -> tuple[Path, Path]:
    return FIXTURES / f"{layout_id}.csv", FIXTURES / f"{layout_id}.expected.json"


CONTRACT_CASES: tuple[ContractCase, ...] = (
    ContractCase(
        "billing-illustrative-1", *_files("billing-illustrative-1"),
        required_headers=("Invoice no", "Revision", "Site", "Account", "Period start", "Period end", "Billing month",
                          "kWh", "Amount", "Currency", "Tariff"),
        amount_header="Amount", clock_header="Period start", bad_clock="01/10/2026", revision_header="Revision",
        coded=(), personal_raw=("C-0412", "C-0413", "C-0901"),
    ),
    ContractCase(
        "collections-illustrative-1", *_files("collections-illustrative-1"),
        required_headers=("Transaction ID", "Site", "Paid at", "Month", "Payer", "Amount", "Currency", "Status"),
        amount_header="Amount", clock_header="Paid at", bad_clock="2026-10-30T19:00:00", revision_header=None,
        coded=(("Status", "Lost"),), personal_raw=("C-0412", "C-0413", "C-0901"), versioning="constant",
    ),
    ContractCase(
        "expenses-illustrative-1", *_files("expenses-illustrative-1"),
        required_headers=("Entry no", "Revision", "Site", "Date", "Month", "Category", "Supplier", "Document",
                          "Litres", "Amount", "Currency", "Status"),
        amount_header="Amount", clock_header="Date", bad_clock="2026-10-11T09:00:00", revision_header="Revision",
        coded=(("Category", "Fuel"), ("Status", "Draft")), personal_raw=("payroll",),
    ),
    ContractCase(
        "budget-illustrative-1", *_files("budget-illustrative-1"),
        required_headers=("Line ID", "Revision", "Month", "Line", "Value", "Budget version"),
        amount_header="Value", clock_header="Month", bad_clock="Oct-2026", revision_header="Revision",
        coded=(("Line", "marketing"),), personal_raw=(),
    ),
)

#: 3A6 (spec §2.10, §4.1): the admitted source profile case, appended to the suite's parametrisation.
PROFILE_CASES: tuple[ContractCase, ...] = (
    ContractCase(
        "profile.kobo-ledger-expenses.v1", FIXTURES_3A6 / "kobo-ledger-expenses.csv",
        FIXTURES_3A6 / "kobo-ledger-expenses.expected.json",
        required_headers=("Ref", "Txn Date", "Site", "Account", "Supplier", "Litres", "Net (USD)", "State"),
        amount_header="Net (USD)", clock_header="Txn Date", bad_clock="2026-10-11T09:00:00", revision_header=None,
        coded=(("Account", "Fuel"), ("State", "Draft")), personal_raw=("STAFF-07", "0712000001", "0712000777"),
        encoding="cp1252", delimiter=";", header_row=3, line_end="\r\n", bad_number=("12.5", "NATIVE_FORMAT"),
        bad_clock_code="NATIVE_FORMAT", versioning="digest", changed_amount="999,00",
        profile=FIXTURES_3A6 / "kobo-ledger-expenses.profile.json",
    ),
)
