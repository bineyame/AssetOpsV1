"""DDR (`specs/DDR-rehearsal/spec.md` §2; D-DDR.1, D-DDR.3, D-DDR.11): checks that each rehearsal step left its record.

    python -m assetops_backend.rehearsal_check --tenant SLUG --month YYYY-MM [--expect PATH]

Read-only. Each gate reads the store its step writes, never another gate's result (D-DDR.3). Output is codes and
facts only (D-DDR.11): one JSON line per gate on stdout; exit 0 when all pass, else 4 with `DDR_GATE_FAILED G<n> <CODE>`
on stderr for the first failure; exit 2 with the refusal code alone before any read. No key path or key content is
printed (D-DS4.19).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Callable, Sequence

DEFAULT_EXPECT = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "ddr" / "lakeside-2026-10.expect.json"
GATES = ("G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8", "G9", "G10")
STEPS = {"G1": "S1", "G2": "S2", "G3": "S4", "G4": "S4", "G5": "S5", "G6": "S6", "G7": "S8", "G8": "S9", "G9": None,
         "G10": "S11"}
_MONTH = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


class Fail(Exception):
    """A gate's first failing condition: its §2.4 code and facts."""

    def __init__(self, code: str, **facts: Any) -> None:
        super().__init__(code)
        self.code = code
        self.facts = facts


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m assetops_backend.rehearsal_check",
                                     description="Check that each rehearsal step left its record.")
    parser.add_argument("--tenant", required=True, help="the tenant's slug")
    parser.add_argument("--month", required=True, help="the month, YYYY-MM")
    parser.add_argument("--expect", default=str(DEFAULT_EXPECT), help="the expectation file (JSON)")
    return parser
