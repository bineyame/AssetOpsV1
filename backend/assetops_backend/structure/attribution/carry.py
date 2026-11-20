"""5b unit 2 (spec §3.1; D-5B.7): a missing cost line carried at its own budget line, Estimated. Pure.

Only the leaves of `CARRY_AT_TARGET`, only when the actual was not received in a closed month from a connected source,
and only from a target that is its own budget line (`DECLARED`, `budget:` sources). An assumed target is never carried
(an assumption would stand in for a record); a heading is never carried (its gap would be zero by construction); an
open month is never carried (every record is still due).
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
from types import MappingProxyType

from assetops_backend.structure import registry as _registry
from assetops_backend.structure.evaluate import FactorValue, LeafValue, Missing
from assetops_backend.structure.read import SiteInputs

CARRY_AT_TARGET: Mapping[str, tuple[str, ...]] = MappingProxyType({"MINI_GRID": ("om", "staff")})
CARRIED_TEXT = "Not received: taken at its budget line for the month (estimate)"
NO_TARGET_LINE = "NO_TARGET_LINE"
_NOT_READ = ("NOT_CONNECTED", "NOT_CALCULATED_YET")


@dataclass(frozen=True)
class Carried:
    inputs: SiteInputs                     # the actual inputs with the carried leaves replaced
    carried: tuple[str, ...]               # registry order
    not_carried: Mapping[str, str]         # leaf -> reason, registry order


def _is_budget_line(t: FactorValue) -> bool:
    return (t.value is not None and t.evidence == "DECLARED" and bool(t.sources)
            and all(s.startswith("budget:") for s in t.sources))


def carry_at_target(inputs: SiteInputs, target: Mapping[str, FactorValue]) -> Carried:
    """Spec §3.1: each listed leaf with no actual value, judged in the spec's order (cause, note, target line)."""
    reg = _registry.REGISTRIES[inputs.structure_key]
    listed = CARRY_AT_TARGET.get(inputs.structure_key, ())
    leaves = dict(inputs.leaves)
    carried: list[str] = []
    not_carried: dict[str, str] = {}
    for row in reg.rows:
        f = row.factor_id
        if not row.is_leaf or f not in listed or leaves[f].value is not None:
            continue
        m = leaves[f].missing  # a leaf with no value always names its missing record (3B3 `_check_leaf`)
        if m.cause in _NOT_READ:
            not_carried[f] = m.cause
        elif m.note is not None:
            not_carried[f] = m.note
        elif not _is_budget_line(target[f]):
            not_carried[f] = NO_TARGET_LINE
        else:
            t = target[f]
            leaves[f] = LeafValue(t.value, "ESTIMATED", tuple(f"target:{s}" for s in t.sources), None,
                                  Missing(m.record_kind, m.source_family, "NOT_RECEIVED", "TARGET", (), m.record_words,
                                          CARRIED_TEXT, None),
                                  t.currency, t.origins)
            carried.append(f)
    if not carried:
        return Carried(inputs, (), MappingProxyType(not_carried))
    return Carried(replace(inputs, leaves=MappingProxyType(leaves)), tuple(carried), MappingProxyType(not_carried))


__all__ = ["CARRIED_TEXT", "CARRY_AT_TARGET", "NO_TARGET_LINE", "Carried", "carry_at_target"]
