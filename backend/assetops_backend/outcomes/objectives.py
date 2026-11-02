"""OUT-D U2: declared objectives and their verdict, policy `outcome-objectives/1` (build sheet OUT-D §3 U2, §4).

Pure. One measure per objective outcome fixes its kind, comparison, unit and target templates; the declaring caller
never supplies them. `judge` only compares values the composer passes (Decimal or int); it never parses prose and
never formats numbers (composers pass pre-formatted texts). Verdict codes stay on the wire and are never rendered."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

POLICY = "outcome-objectives/1"

MET, MISSED, NOT_JUDGED = "MET", "MISSED", "NOT_JUDGED"
#: WALK1-3b (build sheet Addendum 2 §A2.2): the month-to-date verdicts of a monthly measure (`judge_month`).
ON_PACE, BEHIND_PACE, TOO_EARLY = "ON_PACE", "BEHIND_PACE", "TOO_EARLY"
VERDICT_LABEL = {MET: "Met", MISSED: "Missed", NOT_JUDGED: "Not checked yet", ON_PACE: "On pace",
                 BEHIND_PACE: "Behind pace", TOO_EARLY: "Too early to judge"}
VERDICT_CHIP = {MET: {"label": "Met", "tone": "green"}, MISSED: {"label": "Missed", "tone": "amber"},
                NOT_JUDGED: {"label": "Not checked yet", "tone": "gray"},
                ON_PACE: {"label": "On pace", "tone": "green"}, BEHIND_PACE: {"label": "Behind pace", "tone": "amber"},
                TOO_EARLY: {"label": "Too early to judge", "tone": "gray"}}
#: WALK1-3b §A2.5 (owner ruling on D-W1-6): the checked-day minimum before a monthly target is judged for pace, when
#: the declared objective names none. A declaration may set 1 to 28 (28 is the shortest month).
DEFAULT_MIN_CHECKED_DAYS = 3
MIN_CHECKED_DAYS_RANGE = (1, 28)
CONTRIBUTOR_LABEL = "Declared objective"

VALUE, LEADING = "VALUE", "LEADING"
AT_MOST, AT_LEAST = "AT_MOST", "AT_LEAST"
BOARD_DAY, BOARD_WINDOW = "BOARD_DAY", "BOARD_WINDOW"
MONEY_UNIT = "currency/km"


@dataclass(frozen=True)
class Measure:
    key: str
    outcome: str
    kind: str              # VALUE | LEADING
    comparison: str        # AT_MOST | AT_LEAST
    unit: str
    window_rule: str       # BOARD_DAY (mini) | BOARD_WINDOW (cold, EV)
    target_zero: str       # target text when the target is zero
    target_any: str        # target text otherwise; "{t}" is the formatted target (money: "{t} {currency}")
    zero_only: bool = False  # a non-zero target is refused (CC-6)
    monthly: bool = False    # WALK1-3b: judged month to date (`judge_month`); only productive_use_kwh


def _m(key: str, outcome: str, kind: str, comparison: str, unit: str, window: str, zero: str,
       any_: str | None = None, zero_only: bool = False, monthly: bool = False) -> tuple[str, Measure]:
    return key, Measure(key, outcome, kind, comparison, unit, window, zero, any_ if any_ is not None else zero,
                        zero_only, monthly)


#: The six declarable measures (§4 copy). Architect ruling Q1 (2026-10-30, rev 6 per-outcome table): only
#: energy_cost_per_km is a VALUE measure and the only one with a currency; the other five are LEADING.
MEASURES: Mapping[str, Measure] = dict((
    _m("avoidable_generator_minutes", "MG-2", LEADING, AT_MOST, "min/day", BOARD_DAY,
       "Supply cost per kWh: no generator time longer than needed",
       "Supply cost per kWh: at most {t} min a day with the generator on longer than needed"),
    _m("productive_use_kwh", "MG-1", LEADING, AT_LEAST, "kWh/month", BOARD_DAY,
       "Productive electricity sales: at least {t} kWh sold for productive use a month", monthly=True),
    _m("unserved_critical_kwh", "MG-5", LEADING, AT_MOST, "kWh", BOARD_DAY,
       "Reliable service: all critical demand served",
       "Reliable service: at most {t} kWh of critical demand not served"),
    _m("backup_start_failures", "CC-6", LEADING, AT_MOST, "failures", BOARD_WINDOW,
       "Cooling continuity: every backup start succeeds by itself", zero_only=True),
    _m("interrupted_sessions", "EV-1", LEADING, AT_MOST, "sessions", BOARD_WINDOW,
       "Buses ready for service: no interrupted charging sessions",
       "Buses ready for service: at most {t} interrupted charging sessions"),
    _m("energy_cost_per_km", "EV-2", VALUE, AT_MOST, MONEY_UNIT, BOARD_WINDOW,
       "Energy cost per km: at most {t} per km", "Energy cost per km: at most {t} per km"),
))

#: CC-1 reads the existing chamber range (never stored); its internal measure is the open in-window excursion count.
CHAMBER_RANGE_MEASURE = "excursions"
CHAMBER_RANGE_TARGET = "Stock kept saleable: chamber held between {low} and {high}°C"


def target_text(measure: Measure, *, target_is_zero: bool, number: str, currency: str | None = None) -> str:
    """The target sentence; `number` is the composer's formatted target (money: currency appended)."""
    t = f"{number} {currency}" if currency else number
    template = measure.target_zero if target_is_zero and measure.unit != MONEY_UNIT else measure.target_any
    return template.replace("{t}", t)   # ruling L1: the target is always substituted, never a bare "{t}"


@dataclass(frozen=True)
class ObjectiveFact:
    outcome_key: str
    measure_key: str
    comparison: str
    target: Any
    target_is_zero: bool
    target_text: str
    source: str
    revision_id: str | None   # None = read from an existing Site policy (CC-1)
    source_note: str | None = None   # the declaration's note (wire data; CC-1 None)
    min_checked_days: int = DEFAULT_MIN_CHECKED_DAYS   # WALK1-3b: resolved (stored value or the default)


@dataclass(frozen=True)
class Reading:
    value: Any | None
    complete: bool
    actual_text: str | None
    #: WALK1-3b, monthly measures only: days in the month window with measured coverage, days elapsed, days in month.
    checked_days: int | None = None
    elapsed_days: int | None = None
    month_days: int | None = None


def judge(o: ObjectiveFact, r: Reading | None) -> str:
    """MET | MISSED | NOT_JUDGED. An AT_MOST miss is proven without a complete window; a MET needs one."""
    if r is None or r.value is None:
        return NOT_JUDGED
    if o.comparison == AT_MOST:
        if r.value > o.target:
            return MISSED
        return MET if r.complete else NOT_JUDGED
    if o.comparison == AT_LEAST:
        if r.value >= o.target:
            return MET
        return MISSED if r.complete else NOT_JUDGED
    return NOT_JUDGED


def judge_month(o: ObjectiveFact, r: Reading | None) -> str:
    """WALK1-3b §A2.2: an at-least monthly target judged month to date; first match wins.

    MET when the month-to-date value reaches the target (missing days can only add); MISSED only for a complete month
    with every day checked; TOO_EARLY below the objective's checked-day minimum; then ON_PACE when the average over the
    checked days reaches the daily rate the target needs, else BEHIND_PACE. Rates are compared, never a projected
    total. No reading, or no checked day, is NOT_JUDGED."""
    if r is None or r.value is None or not r.checked_days or not r.month_days or r.elapsed_days is None:
        return NOT_JUDGED
    if r.value >= o.target:
        return MET
    if r.elapsed_days == r.month_days and r.checked_days == r.month_days:
        return MISSED
    if r.checked_days < o.min_checked_days:
        return TOO_EARLY
    # avg >= need  <=>  value / c >= target / m  <=>  value * m >= target * c (exact, no rounding)
    return ON_PACE if r.value * r.month_days >= o.target * r.checked_days else BEHIND_PACE
