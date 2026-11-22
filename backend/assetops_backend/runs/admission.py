"""The admission rule for a generator setting (D-0K4.9; 0K4d spec §2.1). Pure; `6c` imports it.

A setting is admitted against no action, over the same days, when all four parts pass, in `ADMISSION_PARTS` order:
energy not served and reserve breaches are judged relative to the baseline (no worse than no action); most starts in
a local day and the longest run of local days without a full charge are judged against the rule's absolute limits,
unless the baseline itself fails that limit, when the part is judged against the baseline instead and says so
(`RELATIVE_BASELINE_FAILS`). No action is never rejected: `admit(b, b)` is always admitted.

The dawn margin (the worst 05:00 reading, its distance to the dawn limit, the dates below) is reported beside the result
as information and never admits or rejects. The rule reads only the study's replay outputs (W2): comparisons only, no
price, no fuel law. The two limits are assumed values; their words, basis and derivation are written by the tool that
prints them, never here (D-0K4.27, D-0K4.28). Every exception is a built-in one holding a code.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from assetops_backend.runs.replay_study import EVIDENCE_CLASS, INPUT_CLASSES, CaseOutcome

ADMISSION_PARTS = ("energy_not_served", "reserve_breaches", "starts", "full_charge")  # this order
JUDGED = frozenset({"RELATIVE", "ABSOLUTE", "RELATIVE_BASELINE_FAILS"})


@dataclass(frozen=True)
class AdmissionRule:
    max_starts_per_day: int = 6  # the maker's limit; GENERIC_DEFAULT until Kobo's generator sheet
    full_charge_every_days: int = 7  # LFP; GENERIC_DEFAULT until Kobo's battery sheet
    basis: str = "GENERIC_DEFAULT"

    def __post_init__(self) -> None:
        for limit in (self.max_starts_per_day, self.full_charge_every_days):
            if type(limit) is not int or limit < 1:
                raise ValueError("ADMISSION_RULE_INVALID")
        if not isinstance(self.basis, str):
            raise TypeError("ADMISSION_RULE_INVALID")


@dataclass(frozen=True)
class AdmissionPart:
    name: str
    case_value: Fraction
    baseline_value: Fraction
    limit: Fraction | None  # None for a relative part
    judged: str  # JUDGED
    passed: bool

    def __post_init__(self) -> None:
        if self.name not in ADMISSION_PARTS or self.judged not in JUDGED:
            raise ValueError("ADMISSION_PART_INVALID")


@dataclass(frozen=True)
class DawnInformation:
    """Information, never a gate (D-0K4.9)."""

    worst_soc_pct: Fraction
    margin_points: Fraction  # worst_soc_pct - the dawn limit
    days_below: int
    dates_below: tuple[str, ...]


@dataclass(frozen=True)
class Admission:
    case_id: str
    admitted: bool
    parts: tuple[AdmissionPart, ...]  # ADMISSION_PARTS order
    dawn: DawnInformation
    rule: AdmissionRule
    input_class: str  # copied from the case
    evidence_class: str = EVIDENCE_CLASS

    def __post_init__(self) -> None:
        if self.input_class not in INPUT_CLASSES or self.evidence_class != EVIDENCE_CLASS:
            raise ValueError("ADMISSION_LABELS_INVALID")
        if tuple(p.name for p in self.parts) != ADMISSION_PARTS:
            raise ValueError("ADMISSION_PART_INVALID")
        if self.admitted != all(p.passed for p in self.parts):
            raise ValueError("ADMISSION_PART_INVALID")


def _relative(name: str, case_value: Fraction, baseline_value: Fraction) -> AdmissionPart:
    return AdmissionPart(name, case_value, baseline_value, None, "RELATIVE", case_value <= baseline_value)


def _absolute(name: str, case_value: Fraction, baseline_value: Fraction, limit: Fraction) -> AdmissionPart:
    if baseline_value <= limit:
        return AdmissionPart(name, case_value, baseline_value, limit, "ABSOLUTE", case_value <= limit)
    return AdmissionPart(name, case_value, baseline_value, limit, "RELATIVE_BASELINE_FAILS",
                         case_value <= baseline_value)


def _dawn(case: CaseOutcome, dawn_limit_pct: Fraction) -> DawnInformation:
    if not case.dawn:
        raise ValueError("ADMISSION_DAWN_EMPTY")
    worst = min(reading.soc_pct for reading in case.dawn)
    below = tuple(sorted(reading.local_date for reading in case.dawn if reading.soc_pct < dawn_limit_pct))
    return DawnInformation(worst, worst - dawn_limit_pct, len(below), below)


def admit(baseline: CaseOutcome, case: CaseOutcome, rule: AdmissionRule = AdmissionRule(),
          dawn_limit_pct: Fraction = Fraction(35)) -> Admission:
    """The four parts of D-0K4.9 for `case` against `baseline` over the same days, and the dawn beside them."""
    if not isinstance(baseline, CaseOutcome) or not isinstance(case, CaseOutcome):
        raise TypeError("ADMISSION_INPUT_INVALID")
    if not isinstance(rule, AdmissionRule) or type(dawn_limit_pct) is not Fraction:
        raise TypeError("ADMISSION_INPUT_INVALID")
    if baseline.input_class != case.input_class:
        raise ValueError("ADMISSION_INPUT_CLASS_MISMATCH")
    parts = (
        _relative("energy_not_served", case.unserved_kwh, baseline.unserved_kwh),
        _relative("reserve_breaches", Fraction(case.reserve_breach_steps), Fraction(baseline.reserve_breach_steps)),
        _absolute("starts", Fraction(case.max_starts_in_a_day), Fraction(baseline.max_starts_in_a_day),
                  Fraction(rule.max_starts_per_day)),
        _absolute("full_charge", Fraction(case.longest_days_without_full_charge),
                  Fraction(baseline.longest_days_without_full_charge), Fraction(rule.full_charge_every_days - 1)),
    )
    return Admission(case_id=case.case_id, admitted=all(p.passed for p in parts), parts=parts,
                     dawn=_dawn(case, dawn_limit_pct), rule=rule, input_class=case.input_class)


__all__ = [
    "ADMISSION_PARTS",
    "JUDGED",
    "Admission",
    "AdmissionPart",
    "AdmissionRule",
    "DawnInformation",
    "admit",
]
