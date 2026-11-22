"""6c (`specs/6c-option-evaluator/spec.md` §3.5, §4; D-P6.20 to D-P6.31): the evaluation run. The analyst values every
option of a decision against no action and the run is written through 6a's store.

Steps E0 to E7 run in order and the first that fails refuses. Every check of the study file comes before the month's
figures are read, so a bad file never reads the structure. Every call writes a new run: a valuation is dated.
"""
from __future__ import annotations

import dataclasses
from collections.abc import Callable, Mapping
from datetime import datetime
from os import PathLike
from types import MappingProxyType
from typing import Any
from uuid import UUID, uuid4

from assetops_backend.decisions.evaluate import EVALUATOR_VERSION, OptionInput, evaluate_options, fraction_text
from assetops_backend.decisions.models import (NO_ACTION, SETTING_GRID, SETTING_GRID_CHANGES, check_grid_changes,
                                               match_cases, months_averaged, setting_changes, stated_changes)
from assetops_backend.decisions.records import (COMMANDS, STATED_OPTIONS, DecisionRefused, DecisionRow, DecisionStore,
                                                OneOffRow, OptionRecordRow, OptionRow, RunRow, StoreUnavailable, _now,
                                                admit_person)
from assetops_backend.decisions.study_input import SITE_RECORD, CaseInput, StudyInput, StudyRefused, read_study
from assetops_backend.runs.admission import DAWN_LIMIT_PCT, AdmissionPart, AdmissionRule, judge
from assetops_backend.structure.check import StructureError
from assetops_backend.structure.evaluate import LeafValue
from assetops_backend.structure.levers import LEVERS, Lever
from assetops_backend.structure.registry import REGISTRIES


def dawn_record(case: CaseInput, days: int) -> dict[str, Any]:
    """§3.5: the dawn readings beside a setting, information only (D-0K4.9)."""
    return {"worst_soc_pct": fraction_text(case.worst_dawn_soc_pct),
            "margin_points": fraction_text(case.worst_dawn_soc_pct - DAWN_LIMIT_PCT),
            "days_below": case.dawn_days_below, "new_days_below": list(case.new_dawn_days_below), "days": days}


def recompute_admission(study: StudyInput) -> Mapping[str, tuple[AdmissionPart, ...]]:
    """§3.5: the rule judged again on every case, in the study's own frame; it must agree with the file's admission
    and the file's limits with the rule's, else STUDY_ADMISSION_MISMATCH."""
    rule = AdmissionRule()
    out: dict[str, tuple[AdmissionPart, ...]] = {}
    for case_id, case in study.cases.items():
        parts = judge(study.baseline.measures, case.measures, rule)
        admitted, first, file_parts = case.file_admission
        if (admitted != all(p.passed for p in parts)
                or first != next((p.name for p in parts if not p.passed), None)
                or file_parts != tuple((p.name, p.passed) for p in parts)
                or dict(case.file_limits) != {p.name: p.limit for p in parts if p.limit is not None}):
            raise StudyRefused("STUDY_ADMISSION_MISMATCH", case_id)
        out[case_id] = parts
    return out


def option_inputs(options: tuple[OptionRow, ...], lever: Lever, study: StudyInput | None,
                  by_key: Mapping[str, CaseInput], admissions: Mapping[str, tuple[AdmissionPart, ...]],
                  one_offs: Mapping[UUID, OneOffRow], *, base: Mapping[str, LeafValue] | None = None,
                  records: Mapping[tuple[UUID, str], OptionRecordRow] = MappingProxyType({}),
                  grid_changes=SETTING_GRID_CHANGES) -> tuple[OptionInput, ...]:
    """§3.5: each option's leaf changes, admission, dawn and one-off; no action has none."""
    out = []
    for option in options:
        if option.generator == NO_ACTION:
            out.append(OptionInput(option, None, None, None, None))
            continue
        if option.generator == STATED_OPTIONS:  # 6h (spec §4.1)
            if base is None:
                raise RuntimeError("6h: a STATED_OPTIONS option needs the base")  # a caller fault, never a refusal
            out.append(OptionInput(option, stated_changes(lever, option, base, records), None, None,
                                   one_offs.get(option.id)))
            continue
        if option.generator != SETTING_GRID:  # D-P6.38: no model, no figure (E3 refuses before this is reached)
            raise DecisionRefused("LEVER_UNKNOWN")
        case = by_key[option.option_key]
        out.append(OptionInput(option, setting_changes(lever, case, study, grid_changes=grid_changes),
                               admissions[case.case_id], dawn_record(case, study.days), one_offs.get(option.id)))
    return tuple(out)


class EvaluationService:
    def __init__(self, store: DecisionStore, accounts, structure_read, *, clock: Callable[[], datetime],
                 new_id: Callable[[], UUID] = uuid4, levers: Mapping[str, Lever] = LEVERS, registries=REGISTRIES,
                 grid_changes=SETTING_GRID_CHANGES, read_bytes: Callable[[str | PathLike], bytes]) -> None:
        check_grid_changes(levers, grid_changes)  # D-P6.21: the start-up assertion
        self._store = store
        self._accounts = accounts
        self._read = structure_read
        self._clock = clock
        self._new_id = new_id
        self._levers = levers
        self._registries = registries
        self._grid_changes = grid_changes
        self._read_bytes = read_bytes

    def _call(self, fn, *args):
        try:
            return fn(*args)
        except StoreUnavailable:
            raise DecisionRefused("DECISIONS_UNAVAILABLE") from None

    def evaluate(self, *, tenant_slug: str, as_email: str, decision_id: UUID, study_path: str | PathLike | None) -> RunRow:
        tenant_id, person, role = admit_person(self._accounts, COMMANDS["evaluate"], tenant_slug, as_email)  # E0
        found = self._call(self._store.decision, tenant_id, decision_id)  # E1
        if found is None:
            raise DecisionRefused("DECISION_NOT_FOUND")
        decision, options = found
        lever = self._levers.get(decision.lever_id)
        if lever is None:
            raise DecisionRefused("LEVER_UNKNOWN")
        if lever.generator == SETTING_GRID and study_path is None:  # E2: a SETTING_GRID lever needs its study
            raise DecisionRefused("STUDY_REQUIRED")
        if lever.generator == STATED_OPTIONS and study_path is not None:  # 6h E2: a stated lever reads no study
            raise DecisionRefused("STUDY_NOT_FOR_LEVER")
        modelled = (NO_ACTION, SETTING_GRID, STATED_OPTIONS)  # E3, D-P6.38: a generator with no model refuses before anything is read
        if lever.generator not in modelled or any(o.generator not in modelled for o in options):
            raise DecisionRefused("LEVER_UNKNOWN")
        stated = lever.generator == STATED_OPTIONS
        if study_path is None and not stated:
            raise DecisionRefused("STUDY_REQUIRED")
        study: StudyInput | None = None
        months: tuple[str, ...] = ()
        by_key: Mapping[str, CaseInput] = {}
        admissions: Mapping[str, tuple[AdmissionPart, ...]] = {}
        ignored: tuple[str, ...] = ()
        try:  # E3
            site = None
            if not stated:
                study = read_study(study_path, self._read_bytes)
            site = self._call(self._store.site_by_id, tenant_id, decision.site_id)
            if site is None:
                raise DecisionRefused("DECISIONS_UNAVAILABLE")
            if study is not None:
                months = self._months(decision, lever, study, tenant_slug, site.site_code)
                by_key, ignored = match_cases(decision, options, study)
                admissions = recompute_admission(study)
        except StudyRefused as refused:
            raise DecisionRefused(refused.code) from None
        now = _now(self._clock)  # E4: one clock read
        registry = self._registries[decision.structure_key]
        try:
            base = self._read.site_inputs(site, decision.period, now).leaves
        except (StructureError, StoreUnavailable):  # D-P6.41: a declared failure; anything else is a fault and propagates
            raise DecisionRefused("STRUCTURE_UNAVAILABLE") from None
        one_offs = self._call(self._store.latest_one_offs, tenant_id, decision.id)  # E5
        records = self._call(self._store.latest_option_records, tenant_id, decision.id)
        inputs = option_inputs(options, lever, study, by_key, admissions, one_offs, base=base, records=records,
                               grid_changes=self._grid_changes)
        try:  # E6
            outcome, rows = evaluate_options(registry, base, decision, lever, inputs)
        except StructureError:
            raise DecisionRefused("STRUCTURE_UNAVAILABLE") from None
        identity = (None if study is None else
                    {**study.identity, "ignored_cases": list(ignored), "months_averaged": list(months)})
        run = RunRow(self._new_id(), tenant_id, decision.id, EVALUATOR_VERSION, outcome,
                     None if study is None else study.sha256, identity, now,
                     person.person_id, role, True, now,
                     tuple(_with_id(row, self._new_id()) for row in rows))
        return self._call(self._store.add_run, run)  # E7: a refused record is RECORD_INVALID (D-P6.30, D-P6.31)

    def option_keys(self, run: RunRow) -> Mapping[UUID, str]:
        """Each option's key by its id, for the command's line."""
        found = self._call(self._store.decision, run.tenant_id, run.decision_id)
        return {} if found is None else {o.id: o.option_key for o in found[1]}

    def _months(self, decision: DecisionRow, lever: Lever, study: StudyInput, tenant_slug: str,
                site_code: str) -> tuple[str, ...]:
        """SITE_RECORD: the frame is this tenant's and Site's, then the decision's month is a full month."""
        if study.frame != SITE_RECORD:
            return ()
        if study.frame_tenant != tenant_slug or study.frame_site_code != site_code:
            raise StudyRefused("STUDY_FRAME_MISMATCH")
        months = months_averaged(lever, study, grid_changes=self._grid_changes)
        if decision.period not in months:
            raise StudyRefused("STUDY_MONTH_NOT_COVERED")
        return months


def _with_id(row, new: UUID):
    return dataclasses.replace(row, id=new)


__all__ = ["EvaluationService", "dawn_record", "option_inputs", "recompute_admission"]
