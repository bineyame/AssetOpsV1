"""OUT-D U4: declared objectives on the board (build sheet OUT-D §3 U4).

Shared by the three composers (`board.py` imports only `outcomes.*`, so the verdict and the contributor live
there). Stored objective rows (the objective store's `current` rows) become
`ObjectiveFact`s with their target sentence; each composer builds its own `Reading`s from the producer bodies it
already read (no reading parses prose). The verdict is judged only for a settled outcome. CC-1's objective is the
existing chamber range of the cold overview and is never stored (R584).
"""
from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from decimal import Decimal
from typing import Any

from assetops_backend.outcomes.catalogue import SITE_OUTCOMES
from assetops_backend.outcomes.objectives import (
    AT_MOST, CHAMBER_RANGE_MEASURE, CHAMBER_RANGE_TARGET, CONTRIBUTOR_LABEL, DEFAULT_MIN_CHECKED_DAYS, MEASURES, MET,
    MISSED, ObjectiveFact, target_text)

CHAMBER_RANGE_OUTCOME = "CC-1"
CHAMBER_RANGE_SOURCE = "DECLARED"
ASSURE_MET = "{met} of {n} declared objectives met"
ASSURE_UNCHECKED = " · {u} not checked yet"
#: Every fixed viewer string, for the vocabulary scan (with the measure templates of `outcomes/objectives.py`).
COPY = (CONTRIBUTOR_LABEL, ASSURE_MET.format(met=1, n=3), ASSURE_UNCHECKED.format(u=2),
        CHAMBER_RANGE_TARGET.format(low="2", high="8"))
_ORDER = {o.key: i for i, o in enumerate(SITE_OUTCOMES)}


def catalogue_index(outcome_key: str) -> int:
    return _ORDER.get(outcome_key, len(_ORDER))


def _decimal(value: Any) -> Decimal:
    return value if isinstance(value, Decimal) else Decimal(str(value))


def from_rows(rows: Sequence[Mapping[str, Any]] | None, fmt: Callable[[Any], str | None]) -> tuple[ObjectiveFact, ...]:
    """The stored objectives of this Site, in catalogue order. `fmt` is the composer's number formatter."""
    facts = []
    for r in rows or ():
        measure = MEASURES.get(str(r.get("measure_key")))
        if measure is None or measure.outcome != r.get("outcome_key"):
            continue
        target = _decimal(r["target"])
        text = target_text(measure, target_is_zero=target == 0, number=fmt(target) or "0",
                           currency=r.get("currency"))
        facts.append(ObjectiveFact(measure.outcome, measure.key, measure.comparison, target, target == 0, text,
                                   str(r.get("source")), None if r.get("id") is None else str(r["id"]),
                                   r.get("source_note"),
                                   # WALK1-3b §A2.5: NULL (or a row read before 0041) is the default minimum
                                   DEFAULT_MIN_CHECKED_DAYS if r.get("min_checked_days") is None
                                   else int(r["min_checked_days"])))
    return tuple(sorted(facts, key=lambda f: catalogue_index(f.outcome_key)))


def chamber_range(objective: Mapping[str, Any] | None, fmt: Callable[[Any], str | None]) -> ObjectiveFact | None:
    """CC-1 from the overview `objective {policy_low_deg_c, policy_high_deg_c}` block, when both bounds are set."""
    block = objective or {}
    low, high = block.get("policy_low_deg_c"), block.get("policy_high_deg_c")
    if low is None or high is None:
        return None
    return ObjectiveFact(CHAMBER_RANGE_OUTCOME, CHAMBER_RANGE_MEASURE, AT_MOST, Decimal(0), True,
                         CHAMBER_RANGE_TARGET.format(low=fmt(low), high=fmt(high)), CHAMBER_RANGE_SOURCE, None)


def assure_text(verdicts: Sequence[str | None]) -> str:
    """The mini Assure "Actual against plan" line over its declared objectives (at least one)."""
    met = sum(1 for v in verdicts if v == MET)
    unchecked = sum(1 for v in verdicts if v not in (MET, MISSED))
    return ASSURE_MET.format(met=met, n=len(verdicts)) + (ASSURE_UNCHECKED.format(u=unchecked) if unchecked else "")
