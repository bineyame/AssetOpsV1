"""ANY-2 AR-4 MN-1/2/3: money lines with receipts (architect answer money-snapshot 2026-11-10 §6-§7, D-MONEY.1-5).

Pure. One money line is an amount (or a low/high range) in ONE currency, its basis, and the receipt that reproduces
it: `{"v", "formula", "qty", "unit", "rate", "rate_unit", "rate_ref", "rounding", "segments", "fx"}`.

- MN-1: the stored day money of `productive_kwh` (`chain/measure_impls.py`) is a `priced_line`: the amount is the
  UNROUNDED quantity times the rate, rounded half-up to the cent; the receipt states that rounding.
- MN-2: the stored potential (`money.lines` kind, `estate/money_rows.py`) is a `potential_line`: the study's headroom
  low/high x 1 h x the price valid that day, unrounded, as `chain/strategies/priced_energy.py` computes it today.
- `reproduces(line)`: a rebuild from the receipt gives the stored amount exactly. A line that does not is a defect.
- MN-3 `refuse_totals(body)`: a stored money body holds per-Site lines only - never a total across Sites, across
  currencies or of verified results (A6, OWN-1104 R10, FUEL-1 A2). Totals stay a read-time roll-up.
"""
from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Mapping

RECEIPT_V = 1
FORMULA = "priced_energy@1"
CENT = Decimal("0.01")
ROUND_CENT = "half_up_cent"
UNROUNDED = "none"
ONE_HOUR = Decimal(1)
MEASURED, DECLARED = "MEASURED", "DECLARED"
#: MN-3: keys a stored money body never carries (a roll-up is computed at read, never stored).
TOTAL_KEYS = frozenset({"total", "totals", "sum", "estate_total", "portfolio_total", "grand_total", "verified_total",
                        "verified_amount", "converted", "reporting_amount"})


class MoneyTotalRefused(ValueError):
    """MN-3: a stored money body would hold a total (cross-Site, cross-currency or of verified results)."""


def _currency_ok(cur: Any) -> bool:
    return isinstance(cur, str) and len(cur) == 3 and cur.isalpha() and cur.isupper()


def receipt(qty: Any, unit: str, rate: Decimal, currency: str, rate_ref: Any, rounding: str) -> dict[str, Any]:
    """The receipt shape decided in §6; `segments` and `fx` stay null until BL-67."""
    return {"v": RECEIPT_V, "formula": FORMULA, "qty": qty, "unit": unit, "rate": f"{rate:f}",
            "rate_unit": f"{currency}/{unit}", "rate_ref": None if rate_ref is None else str(rate_ref).lower(),
            "rounding": rounding, "segments": None, "fx": None}


def priced_line(qty: Decimal, unit: str, rate: Decimal, currency: str, rate_ref: Any,
                basis: str = MEASURED) -> dict[str, Any]:
    """MN-1: `qty x rate` from the unrounded quantity, then half-up to the cent (`measure_impls.py`'s rule)."""
    amount = (qty * rate).quantize(CENT, rounding=ROUND_HALF_UP)
    return {"amount": f"{amount:f}", "currency": currency, "basis": basis,
            "receipt": receipt(f"{qty:f}", unit, rate, currency, rate_ref, ROUND_CENT)}


def potential_line(low_kw: Decimal, high_kw: Decimal, rate: Decimal, currency: str, rate_ref: Any) -> dict[str, Any]:
    """MN-2: headroom low/high kW x 1 h x the declared price, unrounded and stringified as `priced_energy._potential`
    and `OutcomeEvaluator._potential` give it today (`str(Decimal)`)."""
    low, high = low_kw * ONE_HOUR * rate, high_kw * ONE_HOUR * rate
    return {"low": str(low), "high": str(high), "currency": currency, "basis": DECLARED,
            "receipt": receipt({"low": str(low_kw), "high": str(high_kw)}, "kWh", rate, currency, rate_ref,
                               UNROUNDED)}


def reproduces(line: Mapping[str, Any]) -> bool:
    """A rebuild from the receipt gives the stored amount (or low and high) exactly, in the stated currency."""
    r = line.get("receipt") or {}
    try:
        rate = Decimal(str(r["rate"]))
        if r.get("v") != RECEIPT_V or r.get("rate_unit") != f"{line.get('currency')}/{r.get('unit')}":
            return False
        if "amount" in line:
            if r.get("rounding") != ROUND_CENT:
                return False
            rebuilt = (Decimal(str(r["qty"])) * rate).quantize(CENT, rounding=ROUND_HALF_UP)
            return f"{rebuilt:f}" == str(line["amount"])
        qty = r["qty"]
        return (r.get("rounding") == UNROUNDED
                and str(Decimal(str(qty["low"])) * ONE_HOUR * rate) == str(line["low"])
                and str(Decimal(str(qty["high"])) * ONE_HOUR * rate) == str(line["high"]))
    except (KeyError, TypeError, ArithmeticError, ValueError):
        return False


def refuse_totals(body: Any, where: str = "money body") -> None:
    """MN-3: raise `MoneyTotalRefused` when a stored body names a total key anywhere, or when a `lines` list mixes
    currencies or Sites (a stored line is one Site's, in one currency; nothing is summed at write)."""
    if isinstance(body, Mapping):
        bad = sorted(k for k in body if str(k).lower() in TOTAL_KEYS)
        if bad:
            raise MoneyTotalRefused(f"{where}: a stored money body holds no total ({', '.join(bad)})")
        lines = body.get("lines")
        if isinstance(lines, list):
            for line in lines:
                if not isinstance(line, Mapping) or not _currency_ok(line.get("currency")):
                    raise MoneyTotalRefused(f"{where}: every stored money line names its one currency")
            sites = {str(x.get("site_id")).lower() for x in lines if x.get("site_id") is not None}
            if len(sites) > 1:
                raise MoneyTotalRefused(f"{where}: a stored money body is one Site's lines")
        for k, v in body.items():
            refuse_totals(v, f"{where}.{k}")
    elif isinstance(body, list):
        for i, v in enumerate(body):
            refuse_totals(v, f"{where}[{i}]")


__all__ = ["DECLARED", "FORMULA", "MEASURED", "MoneyTotalRefused", "RECEIPT_V", "TOTAL_KEYS", "potential_line",
           "priced_line", "receipt", "refuse_totals", "reproduces"]
