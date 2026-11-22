"""6c (`specs/6c-option-evaluator/spec.md` §3.1; D-P6.2, D-P6.27): one replay study file, read. Pure: the file's bytes are
read by the injected adapter.

`read_study(path)` reads only the keys the evaluator needs: the header's identity, the frame (a simulation on the
Site's own record, or a declared season), and per case its settings, its monthly amounts, the four measures the
admission rule judges, the file's own admission and the dawn readings. A number is read from its `exact` fraction only.
Every refusal is a code (`StudyRefused`).
"""
from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from fractions import Fraction
from os import PathLike
from types import MappingProxyType
from typing import Any

from assetops_backend.runs.admission import AdmissionMeasures
from assetops_backend.runs.replay_study import EVIDENCE_CLASS, INPUT_CLASSES

FRAMES = ("SITE_RECORD", "DECLARED_SEASON")
SITE_RECORD, DECLARED_SEASON = FRAMES
CALIBRATED = "CALIBRATED"
BY_MONTH_FIELDS = ("avoided_l_by_month", "added_throughput_kwh_by_month")
SETTING_KEYS = ("stop_soc_pct", "reserve_soc_pct")
_MONTH = re.compile(r"[0-9]{4}-(0[1-9]|1[0-2])", re.ASCII)

#: §3.1's one key-to-type table. `exact`: a `{"exact": "n/d"}` object; `exact_or_null` likewise or null; `int`: a JSON
#: integer; `str`; `strs`: a list of strings; `dates`: a list of date strings; `str_map`: an object of string values;
#: `by_month`: a list of `{month, days, value}` entries; `bool`; `str_or_null`; `object`; `list`.
_HEADER = MappingProxyType({
    "input_class": "str", "evidence_class": "str", "commit": "str", "model": "str", "season": "str",
    "season_inputs_digest": "str", "trajectory_digests": "str_map", "assumptions": "strs", "admission_rule": "strs",
    "status": "str", "window_start": "str", "days": "int", "baseline": "object", "cases": "list"})
_CASE = MappingProxyType({
    "case_id": "str", "stop_soc_pct": "exact", "reserve_soc_pct": "exact", "avoided_l_by_month": "by_month",
    "added_throughput_kwh_by_month": "by_month", "unserved_kwh": "exact", "reserve_breach_steps": "int",
    "max_starts_in_a_day": "int", "longest_days_without_full_charge": "int", "worst_dawn_soc_pct": "exact",
    "dawn_days_below": "int", "new_dawn_days_below": "dates"})
_ADMISSION = MappingProxyType({"admitted": "bool", "first_failing_part": "str_or_null", "parts": "list"})
_PART = MappingProxyType({"name": "str", "passed": "bool", "limit": "exact_or_null"})
_ENTRY = MappingProxyType({"month": "str", "days": "int", "value": "exact"})


class StudyRefused(Exception):
    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(code if not detail else f"{code} ({detail})")
        self.code = code


@dataclass(frozen=True)
class MonthAmount:
    month: str
    days: int
    value: Fraction


@dataclass(frozen=True)
class CaseInput:
    case_id: str
    settings: Mapping[str, Fraction]
    by_month: Mapping[str, tuple[MonthAmount, ...]]
    measures: AdmissionMeasures
    file_admission: tuple[bool, str | None, tuple[tuple[str, bool], ...]]
    file_limits: Mapping[str, Fraction]
    worst_dawn_soc_pct: Fraction
    dawn_days_below: int
    new_dawn_days_below: tuple[str, ...]


@dataclass(frozen=True)
class StudyInput:
    sha256: str
    identity: Mapping[str, Any]
    input_class: str
    days: int
    frame: str
    frame_tenant: str | None
    frame_site_code: str | None
    baseline: CaseInput
    cases: Mapping[str, CaseInput]


def _unreadable(detail: str) -> StudyRefused:
    return StudyRefused("STUDY_UNREADABLE", detail)


def _is_int(v: object) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def _exact(v: object, where: str) -> Fraction:
    if not isinstance(v, dict) or not isinstance(v.get("exact"), str):
        raise _unreadable(where)
    num, sep, den = v["exact"].partition("/")
    try:
        return Fraction(int(num), int(den)) if sep else Fraction(int(num))
    except (ValueError, ZeroDivisionError):
        raise _unreadable(where) from None


def _typed(obj: object, table: Mapping[str, str], where: str) -> dict[str, Any]:
    """Each key of `table` read and checked against its type; a missing key or a wrong type is unreadable."""
    if not isinstance(obj, dict):
        raise _unreadable(where)
    out: dict[str, Any] = {}
    for key, kind in table.items():
        if key not in obj:
            raise _unreadable(f"{where}.{key}")
        v, at = obj[key], f"{where}.{key}"
        if kind == "exact":
            out[key] = _exact(v, at)
        elif kind == "exact_or_null":
            out[key] = None if v is None else _exact(v, at)
        elif kind == "int":
            if not _is_int(v):
                raise _unreadable(at)
            out[key] = v
        elif kind == "str":
            if not isinstance(v, str):
                raise _unreadable(at)
            out[key] = v
        elif kind == "str_or_null":
            if v is not None and not isinstance(v, str):
                raise _unreadable(at)
            out[key] = v
        elif kind == "bool":
            if not isinstance(v, bool):
                raise _unreadable(at)
            out[key] = v
        elif kind in ("strs", "dates"):
            if not isinstance(v, list) or not all(isinstance(x, str) for x in v):
                raise _unreadable(at)
            out[key] = tuple(v)
        elif kind == "str_map":
            if not isinstance(v, dict) or not all(isinstance(x, str) for x in v.values()):
                raise _unreadable(at)
            out[key] = v
        elif kind == "by_month":
            if not isinstance(v, list):
                raise _unreadable(at)
            entries = tuple(_typed(e, _ENTRY, at) for e in v)
            if any(_MONTH.fullmatch(e["month"]) is None for e in entries) \
                    or len({e["month"] for e in entries}) != len(entries):
                raise _unreadable(at)
            out[key] = tuple(MonthAmount(e["month"], e["days"], e["value"]) for e in entries)
        elif kind == "object":
            if not isinstance(v, dict):
                raise _unreadable(at)
            out[key] = v
        elif kind == "list":
            if not isinstance(v, list):
                raise _unreadable(at)
            out[key] = v
        else:  # pragma: no cover - the table is literal
            raise _unreadable(at)
    return out


def _case(obj: object, where: str, with_admission: bool) -> CaseInput:
    c = _typed(obj, _CASE, where)
    admitted: bool = True
    first: str | None = None
    parts: tuple[tuple[str, bool], ...] = ()
    limits: dict[str, Fraction] = {}
    if with_admission:
        a = _typed(obj.get("admission"), _ADMISSION, f"{where}.admission")
        read = tuple(_typed(p, _PART, f"{where}.admission.parts") for p in a["parts"])
        admitted, first = a["admitted"], a["first_failing_part"]
        parts = tuple((p["name"], p["passed"]) for p in read)
        limits = {p["name"]: p["limit"] for p in read if p["limit"] is not None}
    return CaseInput(
        c["case_id"], MappingProxyType({k: c[k] for k in SETTING_KEYS}),
        MappingProxyType({k: c[k] for k in BY_MONTH_FIELDS}),
        AdmissionMeasures(c["unserved_kwh"], c["reserve_breach_steps"], c["max_starts_in_a_day"],
                          c["longest_days_without_full_charge"]),
        (admitted, first, parts), MappingProxyType(limits), c["worst_dawn_soc_pct"], c["dawn_days_below"],
        c["new_dawn_days_below"])


def read_study(path: str | PathLike, read_bytes: Callable[[str | PathLike], bytes]) -> StudyInput:
    """The study at `path`, its bytes read by the injected `read_bytes` (the adapter `read_study_bytes`), or
    `StudyRefused`: STUDY_UNREADABLE, STUDY_NOT_CALIBRATED, STUDY_LABELS_INVALID."""
    try:
        raw = read_bytes(path)
        doc = json.loads(raw)
    except (OSError, ValueError, TypeError):
        raise _unreadable("file") from None
    head = _typed(doc, _HEADER, "study")
    frame_obj = doc.get("frame")
    if "frame" in doc and not isinstance(frame_obj, dict):
        raise _unreadable("study.frame")
    frame, tenant, site_code = DECLARED_SEASON, None, None
    if isinstance(frame_obj, dict) and frame_obj.get("kind") == SITE_RECORD:
        tenant, site_code = frame_obj.get("tenant"), frame_obj.get("site_code")
        if not isinstance(tenant, str) or not isinstance(site_code, str):
            raise _unreadable("study.frame")
        frame = SITE_RECORD
    baseline = _case(head["baseline"], "baseline", False)
    cases: dict[str, CaseInput] = {}
    for i, obj in enumerate(head["cases"]):
        case = _case(obj, f"cases[{i}]", True)
        if case.case_id in cases or case.case_id == baseline.case_id:
            raise _unreadable(f"cases[{i}].case_id")
        cases[case.case_id] = case
    if head["status"] != CALIBRATED:
        raise StudyRefused("STUDY_NOT_CALIBRATED")
    if head["input_class"] not in INPUT_CLASSES or head["evidence_class"] != EVIDENCE_CLASS:
        raise StudyRefused("STUDY_LABELS_INVALID")
    identity = {k: head[k] for k in _HEADER if k not in ("baseline", "cases")}
    identity = {k: list(v) if isinstance(v, tuple) else v for k, v in identity.items()}
    identity["frame"] = {"kind": frame, "tenant": tenant, "site_code": site_code}
    return StudyInput(hashlib.sha256(raw).hexdigest(), MappingProxyType(identity), head["input_class"], head["days"],
                      frame, tenant, site_code, baseline, MappingProxyType(cases))


__all__ = ["BY_MONTH_FIELDS", "DECLARED_SEASON", "FRAMES", "SITE_RECORD", "CaseInput", "MonthAmount", "StudyInput",
           "StudyRefused", "read_study"]
