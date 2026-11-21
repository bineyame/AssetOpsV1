"""SC-1 (spec section 3.8 (2)): hand-written cases, one or more per variant of every structured statement.

Each module holds `CASES = [Case(key, variant, facts, english, evidence=None), ...]`. `english` (and `evidence`, the
expected list for a `served` statement; None for an `inline` one) are hand literals from spec sections 5 and 6, never
computed (W2). `tools/checks/statement_catalogue.py` proves coverage; `test_sc1_statements.py` T9 proves each renders.
"""
from __future__ import annotations

from typing import Any, NamedTuple


class Case(NamedTuple):
    key: str
    variant: str
    facts: dict[str, Any]
    english: str
    evidence: list[str] | None = None
