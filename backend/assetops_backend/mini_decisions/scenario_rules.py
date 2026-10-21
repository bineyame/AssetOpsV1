"""W4-03 unit 2a: pure Scenario assumption, decimal, currency and calculation rules.

`.agent/W4-03-build-spec.md`: original "Scenario" domain paragraph; closure 1 Q7-Q11 (closed assumption keys,
calculation enum, decimal strings); closure 2 N1 (tariff unit is `<ISO 4217 code>/kWh`, the literal
`ISO4217/kWh` is refused); closure 4 S8 (W4-02 physical numbers enter as `Decimal(str(value))`, normalized plain
strings) and S16 (a scenario pins all five study tuples; arithmetic counts only the ELIGIBLE rows).

Nothing here reads a database or a clock. The command (unit 2b) validates the authored assumptions with
`assumptions()`, passes the selected W4-02 day rows of its exact pins to `calculate()`, and stores the returned
immutable `calculation` with decimal strings. A read re-applies the eligibility/currentness gate at its cutoff and
may answer `WITHHELD` without changing the stored arithmetic.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Iterable, Mapping, Sequence

from assetops_backend.financials.assumptions import ISO_4217
from assetops_backend.mini_decisions.model import invalid

KINDS = ("STOP_SOC", "PRODUCTIVE_LOAD", "TARIFF_ONLY", "OTHER")
NO_CALCULATION, ENERGY_ONLY, GROSS_SCENARIO, WITHHELD = "NO_CALCULATION", "ENERGY_ONLY", "GROSS_SCENARIO", "WITHHELD"
CALCULATION_STATES = (NO_CALCULATION, ENERGY_ONLY, GROSS_SCENARIO, WITHHELD)
ELIGIBLE = "ELIGIBLE"
#: W4-02 complete (assessed) day decisions; LIMITED and CONFLICT days are incomplete guardrails.
ASSESSED = ("ELIGIBLE", "EXCLUDED")

#: Closed assumption keys per kind: (required, optional). Closure 1 Q7-Q11; no other keys or expressions.
KEYS: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    "STOP_SOC": (("stop_soc",), ()),
    "PRODUCTIVE_LOAD": (("proposed_kw", "duration_hours"), ("tariff_per_kwh",)),
    "TARIFF_ONLY": (("tariff_per_kwh",), ()),
    "OTHER": (("declared_value", "declared_unit"), ()),
}
SOURCE_MAX = 500
DECLARED_UNIT_MAX = 32

# Plain base-10 decimal text: optional sign, digits, optional fraction. No exponent, no blank, no binary float.
_DECIMAL = re.compile(r"^-?(0|[1-9][0-9]*)(\.[0-9]+)?$")
_TARIFF_UNIT = re.compile(r"^([A-Z]{3})/kWh$")

# Calculation reasons (stored with the calculation; null when an output is computed).
REASON_NOT_PRODUCTIVE_LOAD = "NOT_PRODUCTIVE_LOAD"
REASON_NO_PINNED_SELECTION = "NO_PINNED_SELECTION"
REASON_INCOMPLETE_STUDY = "INCOMPLETE_STUDY"
REASON_NO_ELIGIBLE_DAY = "NO_ELIGIBLE_DAY"
REASON_HEADROOM_BELOW_LOAD = "HEADROOM_BELOW_LOAD"


# ---- decimals -----------------------------------------------------------------------------------------------------

def decimal_text(value: Decimal) -> str:
    """Plain base-10 string without exponent or insignificant trailing zeros (S8: `18.0` -> `"18"`)."""
    if not value.is_finite():
        raise invalid()
    text = format(value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return "0" if text in ("-0", "") else text


def authored_decimal(value: Any) -> Decimal:
    """An authored decimal is a JSON string in plain base-10 form; a JSON number, exponent or blank is refused."""
    if not isinstance(value, str) or not _DECIMAL.match(value):
        raise invalid()
    try:
        return Decimal(value)
    except InvalidOperation:  # pragma: no cover - the pattern admits only valid literals
        raise invalid() from None


def physical_decimal(value: Any) -> Decimal:
    """S8: a W4-02 physical JSON number (`int|float`) or decimal string becomes `Decimal(str(value))`; never
    `Decimal(float)`. NaN, infinity, booleans and negatives are refused."""
    if isinstance(value, bool) or not isinstance(value, (int, float, str, Decimal)):
        raise invalid()
    try:
        number = Decimal(str(value))
    except InvalidOperation:
        raise invalid() from None
    if not number.is_finite() or number < 0:
        raise invalid()
    return number


def physical_range(value: Any) -> dict[str, str] | None:
    """A W4-02 `{low,high}` bound as normalized decimal strings; null stays null; `low > high` is refused."""
    if value is None:
        return None
    if not isinstance(value, Mapping) or set(value) != {"low", "high"}:
        raise invalid()
    low, high = physical_decimal(value["low"]), physical_decimal(value["high"])
    if low > high:
        raise invalid()
    return {"low": decimal_text(low), "high": decimal_text(high)}


# ---- assumptions --------------------------------------------------------------------------------------------------

def tariff_currency(unit: Any) -> str:
    """N1: `<uppercase ISO 4217 code>/kWh`, the prefix checked against the active code list. `ISO4217/kWh` and any
    unknown code are refused; no currency is inferred from Site locale."""
    match = _TARIFF_UNIT.match(unit) if isinstance(unit, str) else None
    if match is None or match.group(1) not in ISO_4217:
        raise invalid()
    return match.group(1)


def _source(value: Any) -> str:
    if not isinstance(value, str) or not 1 <= len(value.strip()) <= SOURCE_MAX:
        raise invalid()
    return value.strip()


def _assumption(key: str, item: Mapping[str, Any]) -> dict[str, Any]:
    value, unit = item["value"], item["unit"]
    if key == "stop_soc":
        number = authored_decimal(value)
        if unit != "%" or not Decimal(0) <= number <= Decimal(100):
            raise invalid()
    elif key == "proposed_kw":
        number = authored_decimal(value)
        if unit != "kW" or number <= 0:
            raise invalid()
    elif key == "duration_hours":
        number = authored_decimal(value)
        if unit != "h" or not Decimal(0) < number <= Decimal(1):
            raise invalid()
    elif key == "tariff_per_kwh":
        number = authored_decimal(value)
        tariff_currency(unit)
        if number <= 0:
            raise invalid()
    elif key == "declared_value":
        number = authored_decimal(value)
        if unit is not None:
            raise invalid()
    else:  # declared_unit: bounded text 1-32, carried as the value
        if unit is not None or not isinstance(value, str) or not 1 <= len(value.strip()) <= DECLARED_UNIT_MAX:
            raise invalid()
        return {"key": key, "value": value.strip(), "unit": None, "source": _source(item["source"])}
    return {"key": key, "value": decimal_text(number), "unit": unit, "source": _source(item["source"])}


def assumptions(kind: Any, items: Any) -> list[dict[str, Any]]:
    """Validate one revision's closed assumption set for `kind`; returns them canonical and sorted by key.

    Every item is exactly `{key,value,unit,source}`; each key at most once; the kind's required keys present and no
    other keys. Decimal values are canonical strings (`"10.0"` -> `"10"`). `eligible_days` is never authored."""
    if kind not in KINDS or not isinstance(items, list):
        raise invalid()
    required, optional = KEYS[kind]
    out: dict[str, dict[str, Any]] = {}
    for item in items:
        if not isinstance(item, dict) or set(item) != {"key", "value", "unit", "source"}:
            raise invalid()
        key = item["key"]
        if key not in required + optional or key in out:
            raise invalid()
        out[key] = _assumption(key, item)
    if not set(required) <= set(out):
        raise invalid()
    return [out[k] for k in sorted(out)]


def _value(items: Sequence[Mapping[str, Any]], key: str) -> Mapping[str, Any] | None:
    return next((a for a in items if a["key"] == key), None)


# ---- calculation --------------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class DayRow:
    """One pinned W4-02 renewable day row: its decision and, for an ELIGIBLE day, the one-hour headroom bound."""
    local_day: str
    decision: str
    opportunity_kwh: Mapping[str, Any] | None


def calculation(state: str, *, energy: Decimal | None = None, gross: Decimal | None = None,
                currency: str | None = None, reason: str | None = None) -> dict[str, Any]:
    return {"state": state, "energy_kwh": None if energy is None else decimal_text(energy),
            "gross_sales": None if gross is None else {"amount": decimal_text(gross), "currency": currency,
                                                        "basis": "SCENARIO"},
            "reason": reason}


def calculate(kind: str, items: Sequence[Mapping[str, Any]], days: Iterable[DayRow]) -> dict[str, Any]:
    """The stored scenario calculation (closure 1 Q7-Q11).

    Only PRODUCTIVE_LOAD calculates. Without pins there is no calculation. Any pinned day that is not a complete
    assessed W4-02 day (LIMITED, CONFLICT or unknown) withholds; zero ELIGIBLE days withholds; any ELIGIBLE day whose
    lower one-hour headroom is below `proposed_kw` withholds. Otherwise energy per eligible window is
    `proposed_kw x duration_hours` and, with an authored tariff, gross sales per window is energy x tariff, in exact
    Decimal arithmetic. EXCLUDED days are pinned and complete but never counted."""
    if kind != "PRODUCTIVE_LOAD":
        return calculation(NO_CALCULATION, reason=REASON_NOT_PRODUCTIVE_LOAD)
    rows = list(days)
    if not rows:
        return calculation(NO_CALCULATION, reason=REASON_NO_PINNED_SELECTION)
    if any(r.decision not in ASSESSED for r in rows):
        return calculation(WITHHELD, reason=REASON_INCOMPLETE_STUDY)
    eligible = [r for r in rows if r.decision == ELIGIBLE]
    if not eligible:
        return calculation(WITHHELD, reason=REASON_NO_ELIGIBLE_DAY)
    proposed = Decimal(_value(items, "proposed_kw")["value"])
    for row in eligible:
        bound = physical_range(row.opportunity_kwh)
        if bound is None:
            return calculation(WITHHELD, reason=REASON_INCOMPLETE_STUDY)
        if Decimal(bound["low"]) < proposed:
            return calculation(WITHHELD, reason=REASON_HEADROOM_BELOW_LOAD)
    energy = proposed * Decimal(_value(items, "duration_hours")["value"])
    tariff = _value(items, "tariff_per_kwh")
    if tariff is None:
        return calculation(ENERGY_ONLY, energy=energy)
    return calculation(GROSS_SCENARIO, energy=energy, gross=energy * Decimal(tariff["value"]),
                       currency=tariff_currency(tariff["unit"]))


def eligible_days(days: Iterable[DayRow]) -> int:
    """The derived W4-02 eligible-day count; never an authored assumption."""
    return sum(1 for d in days if d.decision == ELIGIBLE)
