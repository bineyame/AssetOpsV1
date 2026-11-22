"""6c (`specs/6c-option-evaluator/spec.md` §3.4; D-P6.5, D-P6.14 to D-P6.19, D-P6.25, D-P6.29): each option of a
decision valued against doing nothing, by one rule, through the structure. Pure.

value = the outcome's monthly change under the option (the structure folded with the option's leaf changes, minus no
action, on the same leaves) x the horizon, less the option's one-off. No structure and no factor is named here: the
outcome is `difference.OUTCOME_FACTOR` and every effect carries its own factor. The dawn readings are stored beside a
setting and never enter a rule.
"""
from __future__ import annotations

import dataclasses
from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal, localcontext
from fractions import Fraction
from typing import Any
from uuid import UUID

from assetops_backend.decisions.records import (SOURCE_CLASSES, DecisionRow, EffectRow, EvaluationRow, MissingInput,
                                                OneOffRow, OptionRow)
from assetops_backend.runs.admission import AdmissionPart
from assetops_backend.structure.difference import OUTCOME_FACTOR, Delta, LeafChange, difference
from assetops_backend.structure.evaluate import FactorValue, LeafValue, _context, evaluate
from assetops_backend.structure.levers import Lever
from assetops_backend.structure.registry import Registry

EVALUATOR_VERSION = "option-evaluator-1"
TIE = Decimal("0.9")                       # within 10 % of the best value (D-P6.16; D-0K4.29 keeps the 10 % as 6c's)
_ASSUMED = ("TARGET", "ASSUMPTION")
_CURRENCY, _ZERO_DENOMINATOR = "currency", "ZERO_DENOMINATOR"
_SIMULATED_ORIGIN, _EMULATED_ORIGIN = "demo-simulated", "source-emulated"
_SIMULATED, _EMULATED, _RECORDED = "SIMULATED", "EMULATED", "RECORDED"
_PENDING_ID = UUID(int=0)                  # every row's id is filled by the caller


@dataclass(frozen=True)
class OptionInput:
    option: OptionRow
    changes: Mapping[str, LeafChange] | None        # None for no action
    admission: tuple[AdmissionPart, ...] | None     # None: no admission rule for this generator
    dawn: Mapping[str, Any] | None
    one_off: OneOffRow | None


def fraction_text(value: Fraction) -> str:
    """D-P6.27: a fraction as "n/d" in lowest terms."""
    return f"{value.numerator}/{value.denominator}"


def admission_record(parts: tuple[AdmissionPart, ...]) -> dict[str, Any]:
    first = next((p.name for p in parts if not p.passed), None)
    return {"admitted": first is None, "first_failing_part": first, "parts": [
        {"name": p.name, "case_value": fraction_text(p.case_value), "baseline_value": fraction_text(p.baseline_value),
         "limit": None if p.limit is None else fraction_text(p.limit), "judged": p.judged, "passed": p.passed}
        for p in parts]}


def _leaf_input(name: str, changes: Mapping[str, LeafChange], base: Mapping[str, LeafValue]) -> MissingInput | None:
    change = changes.get(name)
    if change is not None and change.delta is None and change.missing is not None:
        return MissingInput(change.missing[0], change.missing[1], name)
    leaf = base.get(name)
    if leaf is not None and leaf.missing is not None:
        return MissingInput(leaf.missing.record_kind, leaf.missing.source_family, name)
    return None


def _missing_inputs(registry: Registry, names: tuple[str, ...], zero: tuple[str, ...],
                    changes: Mapping[str, LeafChange], base: Mapping[str, LeafValue],
                    v0: Mapping[str, FactorValue]) -> tuple[MissingInput, ...]:
    """D-P6.37: each missing name resolved to the record or cause it lacks, from a closed list; a name outside the
    list is a code defect and raises."""
    order = {r.factor_id: i for i, r in enumerate(registry.rows)}
    out: list[MissingInput] = []

    def add(item: MissingInput) -> None:
        if item not in out:
            out.append(item)

    for name in names:
        if name == _CURRENCY:
            add(MissingInput("CURRENCY_MISMATCH", "STRUCTURE", None))
            continue
        found = _leaf_input(name, changes, base)
        if found is not None:
            add(found)
            continue
        fv = v0.get(name)
        if name in zero or (fv is not None and fv.missing is not None
                            and fv.missing.record_kind.startswith(_ZERO_DENOMINATOR)):
            add(MissingInput(_ZERO_DENOMINATOR, "STRUCTURE", name))
            continue
        resolved = [] if fv is None else [_leaf_input(n, changes, base) for n in
                                          sorted(fv.missing_leaves, key=lambda n: order.get(n, len(order)))]
        if not resolved or None in resolved:
            raise RuntimeError(f"6c: the missing name {name!r} resolves to no record and no cause")
        for item in resolved:
            add(item)
    return tuple(out)


def _source_class(origins: tuple[str, ...]) -> str:
    if _SIMULATED_ORIGIN in origins:
        return _SIMULATED
    if _EMULATED_ORIGIN in origins:
        return _EMULATED
    return _RECORDED


@dataclass
class _Valued:
    row: EvaluationRow
    admitted: bool
    distance: Decimal


def _value_option(registry: Registry, base: Mapping[str, LeafValue], v0: Mapping[str, FactorValue],
                  decision: DecisionRow, lever: Lever | None, item: OptionInput) -> _Valued:
    changes = item.changes or {}
    result: Mapping[str, Delta] = difference(registry, base, changes)
    out = result[OUTCOME_FACTOR]
    monthly, currency = out.change, out.currency
    with localcontext(_context()):  # D-P6.41: nothing is quantised, so the product runs at the structure's precision
        horizon = None if monthly is None else monthly * decision.horizon_months
    missing = list(_missing_inputs(registry, out.missing_leaves, out.zero_denominators, changes, base, v0))
    one_off = item.one_off
    if one_off is None:
        missing.append(MissingInput("ONE_OFF", "DECISION", None))
    else:
        if monthly is not None and monthly == 0 and currency is None:  # D-P6.29
            currency = one_off.currency
        if currency is not None and one_off.currency != currency:
            missing.append(MissingInput("ONE_OFF_CURRENCY", "DECISION", None))
    with localcontext(_context()):
        value = None if missing or horizon is None else horizon - one_off.amount
    if value is not None and value == 0:
        value = value.copy_abs()
    effects = tuple(EffectRow(d.factor_id, i, d.change, str(d.unit), _effect_currency(d, currency),
                              _missing_inputs(registry, d.missing_leaves, d.zero_denominators, changes, base, v0))
                    for i, d in enumerate(result.values()))
    assumed = set()  # D-P6.36: used leaves carried as a target or assumption, and what a used node rests on
    for name in out.used:
        leaf = base.get(name)
        if leaf is not None and leaf.missing is not None and leaf.missing.carried_as in _ASSUMED:
            assumed.add(name)
        if name in v0:
            assumed.update(v0[name].assumed_leaves)
    order = {r.factor_id: i for i, r in enumerate(registry.rows)}
    assumed = sorted(assumed, key=lambda n: order.get(n, len(order)))
    admission = None if item.admission is None else admission_record(item.admission)
    admitted = admission is None or admission["admitted"]
    distance = Decimal(0)
    if lever is not None:
        for axis in lever.axes:
            distance += abs(item.option.settings[axis.name] - decision.current_settings[axis.name])
    row = EvaluationRow(_PENDING_ID, item.option.id, "", None, None, monthly, horizon,
                        None if one_off is None else one_off.id, value, currency, _source_class(out.origins),
                        out.evidence, tuple(missing), tuple(assumed), admission,
                        None if item.dawn is None else dict(item.dawn), effects)
    return _Valued(row, admitted, distance)


def _effect_currency(delta: Delta, option_currency: str | None) -> str | None:
    """D-P6.34: a money effect that is exactly 0 and read no money value takes the option row's currency."""
    if delta.currency is None and delta.unit.is_money and delta.change is not None and delta.change == 0:
        return option_currency
    return delta.currency


def _at_grid_edge(lever: Lever | None, decision: DecisionRow, option: OptionRow) -> bool:
    if lever is None:
        return False
    for axis in lever.axes:
        setting, current = option.settings[axis.name], decision.current_settings[axis.name]
        if setting < current and setting == min(axis.values):
            return True
        if setting > current and setting == max(axis.values):
            return True
    return False


def evaluate_options(registry: Registry, base: Mapping[str, LeafValue], decision: DecisionRow,
                     lever: Lever | None, inputs: tuple[OptionInput, ...]) -> tuple[str, tuple[EvaluationRow, ...]]:
    """(run outcome, one EvaluationRow per option in position order); every row's id is the caller's to fill."""
    ordered = sorted(inputs, key=lambda i: i.option.position)
    v0 = evaluate(registry, base) if any(i.changes is not None for i in ordered) else {}
    valued: dict[UUID, _Valued] = {}
    for item in ordered:
        if item.changes is not None:
            valued[item.option.id] = _value_option(registry, base, v0, decision, lever, item)
    rows: dict[UUID, EvaluationRow] = {}
    candidates: list[tuple[OptionRow, _Valued]] = []
    incomplete = False
    for item in ordered:
        v = valued.get(item.option.id)
        if v is None:
            continue
        r = v.row
        if not v.admitted:  # R1
            first = r.admission["first_failing_part"]
            rows[item.option.id] = dataclasses.replace(r, disposition="REJECTED",
                                                       reason_code=f"NOT_ADMITTED_{first.upper()}")
        elif r.value is None:  # R2
            rows[item.option.id] = dataclasses.replace(r, disposition="DEFERRED", reason_code="VALUE_NOT_AVAILABLE")
            incomplete = True
        elif r.value < 0:  # R3
            rows[item.option.id] = dataclasses.replace(r, disposition="DEFERRED",
                                                       reason_code="NOT_WORTH_MORE_THAN_NO_ACTION")
        elif r.value == 0:
            rows[item.option.id] = dataclasses.replace(r, disposition="DEFERRED",
                                                       reason_code="WORTH_THE_SAME_AS_NO_ACTION")
        else:  # R4
            candidates.append((item.option, v))
    others = [item for item in ordered if item.changes is not None]
    if all(rows.get(item.option.id) is not None and rows[item.option.id].disposition == "REJECTED"
           for item in others):
        outcome = "NOTHING_ADMITTED"
    elif incomplete:
        outcome = "RANKING_INCOMPLETE"
        for option, v in candidates:
            rows[option.id] = dataclasses.replace(v.row, disposition="ACCEPTABLE", reason_code="RANKING_INCOMPLETE")
    elif not candidates:
        outcome = "NO_ACTION_BEST"
    else:
        outcome = "RECOMMENDED"
        best = max(v.row.value for _, v in candidates)
        near = [(o, v) for o, v in candidates if v.row.value >= best * TIE]
        chosen, chosen_v = min(near, key=lambda ov: (ov[1].distance, -ov[1].row.value, ov[0].option_key))
        rows[chosen.id] = dataclasses.replace(
            chosen_v.row, disposition="RECOMMENDED", rank=1,
            reason_code="AT_GRID_EDGE" if _at_grid_edge(lever, decision, chosen) else None)
        rest = sorted(((o, v) for o, v in candidates if o.id != chosen.id),
                      key=lambda ov: (-ov[1].row.value, ov[0].option_key))
        rank = 1
        for option, v in rest:
            rank += 1
            rows[option.id] = dataclasses.replace(v.row, disposition="ACCEPTABLE", rank=rank)
    classes = [rows[o].source_class for o in rows]
    for item in ordered:  # R0
        if item.changes is None:
            rows[item.option.id] = EvaluationRow(
                _PENDING_ID, item.option.id, "COMPARISON", None, None, Decimal(0), Decimal(0), None, Decimal(0), None,
                min(classes, key=SOURCE_CLASSES.index) if classes else _RECORDED, "DERIVED", (), (), None, None, ())
    return outcome, tuple(rows[item.option.id] for item in ordered)


__all__ = ["EVALUATOR_VERSION", "TIE", "OptionInput", "admission_record", "evaluate_options", "fraction_text"]
