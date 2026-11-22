"""6c (`specs/6c-option-evaluator/spec.md` §3.3; D-P6.2, D-P6.3, D-P6.15, D-P6.21): the lever models. The only place a
factor or field name of a lever's model is written.

A setting-grid lever's option changes its leaves by a delta read from a replay study: for a simulation on the Site's
own record, the mean of the case's full months (no scaling by days); for a declared season, nothing (each change is
missing and names the simulation it needs). The matching of a study to a decision's options lives here too.
"""
from __future__ import annotations

import calendar
from collections.abc import Mapping
from decimal import Decimal, localcontext
from fractions import Fraction
from types import MappingProxyType

from assetops_backend.decisions.records import DecisionRow, OptionRow
from assetops_backend.decisions.study_input import SITE_RECORD, CaseInput, StudyInput, StudyRefused
from assetops_backend.structure.difference import LeafChange
from assetops_backend.structure.evaluate import _context
from assetops_backend.structure.levers import Lever

SETTING_GRID = "SETTING_GRID"
SETTING_GRID_CHANGES: Mapping[str, tuple[tuple[str, str, int], ...]] = MappingProxyType({
    # lever_id -> (changed leaf, study by-month field, sign)                       D-P6.3
    "generator_stop_reserve": (("candidate_l", "avoided_l_by_month", -1),
                               ("battery_throughput_kwh", "added_throughput_kwh_by_month", 1)),
})
SITE_MONTH_MISSING = ("SITE_MONTH_SIMULATION", "SIMULATION")                     # D-P6.2
ORIGIN_OF_INPUT = MappingProxyType({"RECORDED": "field-integrated", "EMULATED": "source-emulated",
                                    "SIMULATED": "demo-simulated"})
_EVIDENCE = "MODELLED"
_SOURCES = ("replay-study",)


def check_grid_changes(levers: Mapping[str, Lever], grid_changes: Mapping[str, tuple[tuple[str, str, int], ...]]
                       ) -> None:
    """The start-up assertion (D-P6.21): each entry's leaves are its lever's `changes`, in order."""
    for lever_id, entries in grid_changes.items():
        lever = levers.get(lever_id)
        if lever is None or tuple(leaf for leaf, _, _ in entries) != lever.changes:
            raise ValueError(f"SETTING_GRID_CHANGES does not match the lever {lever_id!r}")


def _fields(lever: Lever, grid_changes) -> tuple[str, ...]:
    return tuple(field for _, field, _ in grid_changes[lever.lever_id])


def full_months(case: CaseInput, fields: tuple[str, ...]) -> tuple[str, ...]:
    """Months whose entry, in every field, covers the calendar month; in the first field's file order."""
    out = []
    for entry in case.by_month[fields[0]] if fields else ():
        year, month = entry.month.split("-")
        days = calendar.monthrange(int(year), int(month))[1]
        if all(any(e.month == entry.month and e.days == days for e in case.by_month[f]) for f in fields):
            out.append(entry.month)
    return tuple(out)


def setting_changes(lever: Lever, case: CaseInput, study: StudyInput, *,
                    grid_changes=SETTING_GRID_CHANGES) -> Mapping[str, LeafChange]:
    origin = (ORIGIN_OF_INPUT[study.input_class],)
    entries = grid_changes[lever.lever_id]
    months = full_months(case, _fields(lever, grid_changes)) if study.frame == SITE_RECORD else ()
    out: dict[str, LeafChange] = {}
    for leaf, field, sign in entries:
        if not months:  # a declared season, or a Site record with no whole month: no amount reaches the month
            out[leaf] = LeafChange(None, _EVIDENCE, _SOURCES, origin, SITE_MONTH_MISSING)
            continue
        values = [e.value for e in case.by_month[field] if e.month in months]
        mean = sign * sum(values, Fraction(0)) / len(values)
        with localcontext(_context()):
            delta = Decimal(mean.numerator) / Decimal(mean.denominator)
        out[leaf] = LeafChange(delta, _EVIDENCE, _SOURCES, origin, None)
    return MappingProxyType(out)


def months_averaged(lever: Lever, study: StudyInput, *, grid_changes=SETTING_GRID_CHANGES) -> tuple[str, ...]:
    """The baseline's full months (SITE_RECORD); every case must have the same set, else STUDY_UNREADABLE.
    A declared season averages nothing."""
    if study.frame != SITE_RECORD:
        return ()
    fields = _fields(lever, grid_changes)
    months = full_months(study.baseline, fields)
    if any(full_months(case, fields) != months for case in study.cases.values()):
        raise StudyRefused("STUDY_UNREADABLE", "months")
    return months


def _same(settings: Mapping[str, Decimal], case: CaseInput) -> bool:
    return set(settings) == set(case.settings) and all(Fraction(settings[k]) == case.settings[k] for k in settings)


def match_cases(decision: DecisionRow, options: tuple[OptionRow, ...], study: StudyInput
                ) -> tuple[Mapping[str, CaseInput], tuple[str, ...]]:
    """Each SETTING_GRID option's case by option key, and the ignored cases (settings equal today's), or
    STUDY_BASELINE_MISMATCH then STUDY_GRID_MISMATCH."""
    if not _same(decision.current_settings, study.baseline):
        raise StudyRefused("STUDY_BASELINE_MISMATCH")
    grid_options = [o for o in options if o.generator == SETTING_GRID]
    by_key: dict[str, CaseInput] = {}
    for option in grid_options:
        case = study.cases.get(option.option_key)
        if case is None or not _same(option.settings, case):
            raise StudyRefused("STUDY_GRID_MISMATCH", option.option_key)
        by_key[option.option_key] = case
    ignored = []
    for case_id, case in study.cases.items():
        if case_id in by_key:
            continue
        if not _same(decision.current_settings, case):
            raise StudyRefused("STUDY_GRID_MISMATCH", case_id)
        ignored.append(case_id)
    return MappingProxyType(by_key), tuple(ignored)


__all__ = ["ORIGIN_OF_INPUT", "SETTING_GRID", "SETTING_GRID_CHANGES", "SITE_MONTH_MISSING", "check_grid_changes",
           "full_months", "match_cases", "months_averaged", "setting_changes"]
