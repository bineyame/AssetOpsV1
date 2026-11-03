"""CH-3 §5 (OD-3 / AG-24): the money rule. A trial or Action is credited money only when its stored cost check is
MODELLED_IMPROVEMENT with a priced, positive amount and its verification outcome is VERIFIED. Everything else is
"modelled, not saved". Pure; read by the Site board and the Portfolio."""

from __future__ import annotations

from decimal import ROUND_HALF_EVEN, Decimal
from fractions import Fraction
from typing import Any, Mapping

#: The Portfolio's recovered-value text when nothing is credited.
MONEY_NOT_CREDITED = "No money credited · modelled, not saved"


def _amount(value: Any) -> Fraction | None:
    """The stored amount (an exact fraction such as "1/24", or a decimal), or None when absent or unreadable."""
    try:
        return None if value is None else Fraction(str(value))
    except (ValueError, ZeroDivisionError):
        return None


def credited(cost_check: Mapping[str, Any] | None, outcome: str | None) -> tuple[Fraction, str] | None:
    """(amount, currency) when the rule credits money, else None. The amount is the stored nominal change."""
    if cost_check is None or outcome != "VERIFIED" or cost_check.get("state") != "MODELLED_IMPROVEMENT":
        return None
    amount, currency = _amount(cost_check.get("nominal")), cost_check.get("currency")
    if amount is None or amount <= 0 or not currency:
        return None
    return amount, str(currency)


def recovered_value(items: list[tuple[Mapping[str, Any] | None, str | None]]) -> dict[str, Any]:
    """Sum of credited amounts per currency (never added across currencies), or the not-credited text."""
    totals: dict[str, Fraction] = {}
    for cost_check, outcome in items:
        got = credited(cost_check, outcome)
        if got is not None:
            totals[got[1]] = totals.get(got[1], Fraction(0)) + got[0]
    if not totals:
        return {"state": "NOT_CREDITED", "text": MONEY_NOT_CREDITED, "amounts": []}
    return {"state": "CREDITED", "text": None,
            "amounts": [{"currency": c, "amount": _wire(totals[c])} for c in sorted(totals)]}


def _wire(value: Fraction) -> str:
    """Three decimals, half-even (the board's per-kWh rounding)."""
    q = (Decimal(value.numerator) / Decimal(value.denominator)).quantize(Decimal("0.001"), ROUND_HALF_EVEN)
    return str(q)
