"""Measure registry of the day-snapshot chain (CH-1a §3).

CH-1b moves these declarations into the catalogue's ``measures:`` section
unchanged. No outcome link (OL-1, plan §2.4): a ``MeasureSpec`` names no
outcome id, node or strategy; which outcome a measure feeds is declared only
in ``outcomes/outcome_map.py`` ``CONTRIBUTIONS`` (CH-6).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .policy import PERIOD_OPERATING_HOURS
from .ports import DayCtx, InputSet

CATALOGUE_VERSION = 1  # until CH-1b's catalogue file


class MeasureAdapter(Protocol):
    key: str  # e.g. "mini.productive_energy@1"

    def inputs(self, ctx: DayCtx, subject_ref: str) -> InputSet: ...

    def measure(self, ctx: DayCtx, subject_ref: str, inputs: InputSet) -> dict | None: ...

    def money(self, ctx: DayCtx, subject_ref: str, value: dict) -> dict | None: ...

    def subjects(self, ctx: DayCtx) -> list[str]: ...


@dataclass(frozen=True)
class MeasureSpec:
    key: str
    site_type: str
    subject_kind: str
    evidence_class: str
    period: str
    threshold: float | None
    adapter: str


MEASURES: dict[str, MeasureSpec] = {
    "productive_kwh": MeasureSpec(
        "productive_kwh", "MINIGRID", "ASSET", "MEASURED", PERIOD_OPERATING_HOURS, 0.8,
        "mini.productive_energy@1"),
    # CH-9 (§9 R5, CH9-R2 Q2): the day's measured daylight hours inside the declared operating hours; any
    # missing hour leaves the day PARTIAL. Replaces the one-noon-hour `noon_headroom_kw`.
    "daylight_headroom_kw": MeasureSpec(
        "daylight_headroom_kw", "MINIGRID", "SITE", "MEASURED", PERIOD_OPERATING_HOURS, 1.0,
        "mini.daylight_headroom@1"),
    # CH-9 §9 R9 (CH9-R2 Q7): critical demand served over the whole declared day, from the stored hourly
    # `mini_service` heads; an operating hour with no head is uncovered. MG-5 reads it.
    "critical_served": MeasureSpec(
        "critical_served", "MINIGRID", "SITE", "MEASURED", PERIOD_OPERATING_HOURS, 0.8,
        "mini.critical_served@1"),
    "avoidable_gen_min": MeasureSpec(
        "avoidable_gen_min", "MINIGRID", "ASSET", "MEASURED", PERIOD_OPERATING_HOURS, 0.8,
        "mini.dispatch_minutes@1"),
    "chamber_temp_c": MeasureSpec(
        "chamber_temp_c", "COLDCHAIN", "ASSET", "MEASURED", PERIOD_OPERATING_HOURS, 0.8,
        "cold.chamber_temperature@1"),
    "backup_start_chain": MeasureSpec(
        "backup_start_chain", "COLDCHAIN", "ASSET", "MEASURED", PERIOD_OPERATING_HOURS, 1.0,
        "cold.backup_start_chain@1"),
    "charging_kwh": MeasureSpec(
        "charging_kwh", "EV_CHARGING", "SITE", "MEASURED", PERIOD_OPERATING_HOURS, 0.8,
        "ev.charging_energy@1"),
}


def measures_for(site_type: str) -> list[MeasureSpec]:
    return [m for m in MEASURES.values() if m.site_type == site_type]
