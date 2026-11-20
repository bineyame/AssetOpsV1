"""3A3 (spec §4; D-3A3.5): the source contract cases. Not collected (no `test_` prefix).

A reader is registered in `READERS` only with a case here (test S2), and every case passes C1 to C10
(`test_3a3_source_contract.py`). `3A6` appends its profile cases to `CONTRACT_CASES`.

- `golden`, `expected`: the hand-written native file and its canonical records (`fixtures/3a3/`), never produced by
  `read_layout` (W2).
- `required_headers`: blanking each one's cell in row 2 refuses row 2 only, with 2a's code (C3).
- `amount_header`, `clock_header`/`bad_clock`, `revision_header`, `mapped` (header, value outside the map),
  `personal_raw` (raw customer or staff refs that must never be stored or answered).
- `field_for`: a blanked header mapped to the header 2a's first refusal names when they differ (a 2a ordering fact,
  each with its one-line reason).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "3a3"


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
    mapped: tuple[str, str] | None
    personal_raw: tuple[str, ...]
    field_for: Mapping[str, str] = MappingProxyType({})


def _files(layout_id: str) -> tuple[Path, Path]:
    return FIXTURES / f"{layout_id}.csv", FIXTURES / f"{layout_id}.expected.json"


CONTRACT_CASES: tuple[ContractCase, ...] = (
    ContractCase(
        "billing-illustrative-1", *_files("billing-illustrative-1"),
        required_headers=("Invoice no", "Revision", "Site", "Account", "Period start", "Period end", "Billing month",
                          "kWh", "Amount", "Currency", "Tariff"),
        amount_header="Amount", clock_header="Period start", bad_clock="01/10/2026", revision_header="Revision",
        mapped=None, personal_raw=("C-0412", "C-0413", "C-0901"),
    ),
    ContractCase(
        "collections-illustrative-1", *_files("collections-illustrative-1"),
        required_headers=("Transaction ID", "Site", "Paid at", "Month", "Payer", "Amount", "Currency", "Status"),
        amount_header="Amount", clock_header="Paid at", bad_clock="2026-10-30T19:00:00", revision_header=None,
        mapped=("Status", "Lost"), personal_raw=("C-0412", "C-0413", "C-0901"),
    ),
    ContractCase(
        "expenses-illustrative-1", *_files("expenses-illustrative-1"),
        required_headers=("Entry no", "Revision", "Site", "Date", "Month", "Category", "Supplier", "Document",
                          "Litres", "Amount", "Currency", "Status"),
        amount_header="Amount", clock_header="Date", bad_clock="2026-10-11T09:00:00", revision_header="Revision",
        mapped=("Category", "Fuel"), personal_raw=("payroll",),
    ),
    ContractCase(
        "budget-illustrative-1", *_files("budget-illustrative-1"),
        required_headers=("Line ID", "Revision", "Month", "Line", "Value", "Budget version"),
        amount_header="Value", clock_header="Month", bad_clock="Oct-2026", revision_header="Revision",
        mapped=("Line", "marketing"), personal_raw=(),
    ),
)
