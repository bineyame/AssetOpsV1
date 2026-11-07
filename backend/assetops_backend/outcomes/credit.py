"""CH-3 §5 (OD-3 / AG-24): the money rule. A trial or Action is credited money only when its stored cost check is
MODELLED_IMPROVEMENT with a stored, priced, positive total and its verification outcome is VERIFIED. Everything else
is "modelled, not saved". Pure; read by the Portfolio.

Fix round 2: the `outcomes` package imports only `__future__`, `collections.abc`, `dataclasses` and `typing`
(`test_out_a1_outcome_map.test_outcomes_package_is_pure`), so an amount is an exact `(numerator, denominator)` pair of
ints here, not a `Fraction` or `Decimal`."""

from __future__ import annotations

from typing import Any, Mapping

#: An exact non-negative-denominator rational: (numerator, denominator), reduced, denominator > 0.
Amount = tuple[int, int]

#: The Portfolio's recovered-value text when nothing is credited.
MONEY_NOT_CREDITED = "No money credited · modelled, not saved"


def _gcd(a: int, b: int) -> int:
    a, b = abs(a), abs(b)
    while b:
        a, b = b, a % b
    return a


def _reduced(n: int, d: int) -> Amount:
    if d < 0:
        n, d = -n, -d
    g = _gcd(n, d) or 1
    return n // g, d // g


def _int(text: str) -> int | None:
    return int(text) if text.isdigit() and text.isascii() else None


def _amount(value: Any) -> Amount | None:
    """The stored amount (an exact fraction such as "1/24", or a decimal such as "-20.5"), or None when absent or
    unreadable."""
    if value is None:
        return None
    text = str(value).strip()
    sign = -1 if text.startswith("-") else 1
    text = text[1:] if text[:1] in "+-" and text else text
    if "/" in text:
        a, _, b = text.partition("/")
        n, d = _int(a), _int(b)
        return None if n is None or not d else _reduced(sign * n, d)
    whole, dot, frac = text.partition(".")
    n, f = _int(whole or "0"), _int(frac) if frac else 0
    if n is None or f is None or (dot and not frac and not whole):
        return None
    return _reduced(sign * (n * 10 ** len(frac) + f), 10 ** len(frac))


def credited(cost_check: Mapping[str, Any] | None, outcome: str | None) -> tuple[Amount, str] | None:
    """(amount, currency) when the rule credits money, else None.

    CH3-R (money unit): an amount is credited only from a stored, priced TOTAL (`priced_total`: amount, currency
    and the basis it covers). A per-kWh rate (the cost check's `nominal`, `change_per_demand_kwh`) is never summed
    or shown as money; it appears only as a rate with its unit, labelled modelled (the board's COST_CHANGE line).
    FUEL-1 A2: a `trial-fuel-comparison/2` MODELLED_IMPROVEMENT stores the priced total of its trial hour."""
    if cost_check is None or outcome != "VERIFIED" or cost_check.get("state") != "MODELLED_IMPROVEMENT":
        return None
    total = cost_check.get("priced_total")
    if not isinstance(total, Mapping) or not total.get("basis"):
        return None
    amount, currency = _amount(total.get("amount")), total.get("currency")
    if amount is None or amount[0] <= 0 or not currency:
        return None
    return amount, str(currency)


def recovered_value(items: list[tuple[Mapping[str, Any] | None, str | None]]) -> dict[str, Any]:
    """FUEL-1 A2 (owner: there is never a combined savings total): one item per credited result, each with its own
    amount, currency and basis, keyed by the cost check's verification outcome id, in input order. Never summed,
    within or across currencies. Two credited items with the same key fail loud. Nothing credited reads the
    not-credited text."""
    out: list[dict[str, Any]] = []
    for cost_check, outcome in items:
        got = credited(cost_check, outcome)
        if got is None:
            continue
        key = str(cost_check.get("outcome_id") or "")
        if not key:
            raise ValueError("a credited cost check has no outcome id to key its value line")
        if any(item["key"] == key for item in out):
            raise ValueError(f"two credited results share the key {key!r}")
        out.append({"key": key, "currency": got[1], "amount": _wire(got[0]),
                    "basis": str(cost_check["priced_total"]["basis"])})
    if not out:
        return {"state": "NOT_CREDITED", "text": MONEY_NOT_CREDITED, "items": []}
    return {"state": "CREDITED", "text": None, "items": out}


def _wire(value: Amount) -> str:
    """Three decimals, half-even."""
    n, d = value
    sign = "-" if n < 0 else ""
    q, r = divmod(abs(n) * 1000, d)
    if 2 * r > d or (2 * r == d and q % 2 == 1):
        q += 1
    return f"{sign}{q // 1000}.{q % 1000:03d}"
