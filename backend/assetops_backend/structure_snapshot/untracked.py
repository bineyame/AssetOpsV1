"""3B7a unit 1 (spec §2.4; D-3B7A.5): the valued leaves no month stamp covers.

A leaf rests on an untracked input when it has a value, is not an option-only neutral, is not the calendar, and any
of its sources is not a commercial record (readings, declared prices). `3B7b`'s triggers 1 and 4 will cover them.
"""
from __future__ import annotations

from assetops_backend.structure.evaluate import NEUTRAL
from assetops_backend.structure.read import SiteInputs
from assetops_backend.structure.registry import REGISTRIES

COMMERCIAL_SOURCE = "commercial:"


def untracked(inputs: SiteInputs) -> tuple[str, ...]:
    reg = REGISTRIES[inputs.structure_key]
    out = []
    for f in sorted(inputs.leaves):
        leaf = inputs.leaves[f]
        filled_by = reg.row(f).filled_by
        if leaf.value is None or leaf.evidence == NEUTRAL:
            continue
        if filled_by is not None and filled_by.family == "CALENDAR":
            continue
        if any(not source.startswith(COMMERCIAL_SOURCE) for source in leaf.sources):
            out.append(f)
    return tuple(out)


__all__ = ["untracked"]
