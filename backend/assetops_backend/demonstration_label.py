"""S4-02b phase 2b: label the authored demonstration Finding in product reads.

Owner ruling `.agent/owner-S4-02b-money-demo-2026-10-14.md`: the `P01-power` case of
`conversions/s4-power-demo-cases-v1.json` is authored demonstration content and must be visibly labelled
as such beside ordinary Findings. Nothing in the evidence rows records that authorship (the case is posted
with the registered gateway credential, like every S4 case), so the label is derived from the spec's own
declaration: its Site code and its case days. The spec's days are tested clear of every S4 case day.

This is a presentation label only. It never changes a quantity, price, amount or currentness.
"""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any

SPEC_PATH = Path(__file__).resolve().parents[1] / "conversions" / "s4-power-demo-cases-v1.json"

LABEL = "Demonstration data"
STATEMENT = ("This finding comes from demonstration readings written by the AssetOps team to show a complete "
             "fuel-cost calculation. They are not measurements from a working generator.")


@lru_cache(maxsize=1)
def _declared() -> tuple[str, str, tuple[tuple[str, date], ...]]:
    try:
        spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return ("", "", ())
    return (spec["site_code"], spec["label"],
            tuple((c["case_id"], date.fromisoformat(c["day"])) for c in spec["cases"]))


def _instant(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def demonstration_case(site_code: str, start: Any, end: Any) -> dict[str, str] | None:
    """The declared demonstration case whose UTC day wholly holds `[start, end)` at this Site, else None."""
    code, spec_label, cases = _declared()
    lo, hi = _instant(start), _instant(end)
    if site_code != code or lo is None or hi is None:
        return None
    for case_id, day in cases:
        day_start = datetime(day.year, day.month, day.day, tzinfo=timezone.utc)
        if day_start <= lo and hi <= day_start + timedelta(days=1):
            return {"label": LABEL, "statement": STATEMENT, "case_id": case_id, "spec": spec_label}
    return None
