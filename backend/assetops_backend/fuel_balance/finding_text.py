"""DIESEL-K4a (`.agent/build-sheet-DIESEL-1.md` §9j.7, ruling DIESEL-1-R3j): the unexplained-fuel Finding's client
wording. Pure, no I/O.

Rules H1-H5 (§8.2); owner 2026-11-07: "'Unexplained fuel', never 'theft'". Numbers are formatted here, never in the
browser: litres to one decimal, half-even on the exact `Fraction`; money with `chain.vocabulary.money2` on the exact
amount; dates as the board's short day ("4 Oct"); times as Site-local 24 h `HH:MM`.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, localcontext
from fractions import Fraction
from typing import Any, Iterable, Mapping
from zoneinfo import ZoneInfo

from assetops_backend.actions.verification_rules import fmt, parse_exact
from assetops_backend.chain.vocabulary import money2

TITLE = "Unexplained fuel overnight"
CLAIM_LINE = ("About {lo}–{hi} L left the tank on the night of {date} (6 pm to noon) that the generator's "
              "modelled use and the recorded deliveries don't explain.")
GAP_LINE = "The tank sensor sent no readings {spans}."          # SPAN joined with ", and "
SPAN = "from {a} to {b}"
MONEY_LINE = ("Worth about {lo_m}–{hi_m} {cur} at your declared {p} {cur} per litre "
              "(a modelled range that includes the stated margin)")
UNPRICED_NO_PRICE = "Not available yet · no diesel price declared for this night"
UNPRICED_PRICE_CHANGES = "Not available yet · the declared diesel price changes during this night"   # PRICE_CONFLICT, PRICE_SPANS_WINDOW
UNPRICED_OTHER = "Not available yet · the declared diesel price could not be used for this night"   # any other reason
NOT_WHY = "This does not say why the fuel left the tank."
MARGIN_LINE = ("The range allows for the tank sensor's declared accuracy of {a} L at each reading, 10 % either way "
               "on the generator's modelled use, and 1 % on each recorded delivery.")
NO_LONGER = "A later check of this night no longer finds unexplained fuel."

#: Every K4a literal (the local wording guard and `test_out_b2_vocabulary.py` scan these).
LITERALS = (TITLE, CLAIM_LINE, GAP_LINE, SPAN, MONEY_LINE, UNPRICED_NO_PRICE, UNPRICED_PRICE_CHANGES, UNPRICED_OTHER,
            NOT_WHY, MARGIN_LINE, NO_LONGER)

SUPPORTED, NO_LONGER_SUPPORTED = "SUPPORTED", "NO_LONGER_SUPPORTED"
_PRICE_CHANGES = ("PRICE_CONFLICT", "PRICE_SPANS_WINDOW")


def litres1(value: Fraction) -> str:
    """One decimal, half-even on the exact value (`round` of a Fraction is half-even)."""
    return f"{Decimal(round(Fraction(value) * 10)) / 10:.1f}"


def _exact_decimal(value: Any) -> Decimal:
    """The exact amount as a Decimal: exact when it terminates, else 60 significant digits (a non-terminating value
    is never a two-place tie)."""
    f = parse_exact(value) if not isinstance(value, Fraction) else value
    if f is None:
        raise ValueError(f"not an exact amount: {value!r}")
    text = fmt(f)
    if "/" not in text:
        return Decimal(text)
    with localcontext() as ctx:
        ctx.prec = 60
        return Decimal(f.numerator) / Decimal(f.denominator)


def money(value: Any) -> str:
    return money2(_exact_decimal(value))


def short_day(d: date) -> str:
    return f"{d.day} {d:%b}"


def _hhmm(at: datetime, tz: str) -> str:
    return at.astimezone(ZoneInfo(tz)).strftime("%H:%M")


def gap_line(spans: Iterable[tuple[datetime, datetime]], tz: str) -> str:
    return GAP_LINE.format(spans=", and ".join(SPAN.format(a=_hhmm(a, tz), b=_hhmm(b, tz)) for a, b in spans))


def _plain_litres(value: Any) -> str:
    """The declared accuracy as declared (exact text, e.g. "10")."""
    f = parse_exact(value) if not isinstance(value, Fraction) else value
    return fmt(f) if f is not None else str(value)


def margin_line(accuracy_l: Any) -> str:
    return MARGIN_LINE.format(a=_plain_litres(accuracy_l))


def claim_line(low: Fraction, high: Fraction, night_date: date) -> str:
    return CLAIM_LINE.format(lo=litres1(low), hi=litres1(high), date=short_day(night_date))


def unpriced_line(reason: str | None) -> str:
    if reason == "NO_PRICE":
        return UNPRICED_NO_PRICE
    if reason in _PRICE_CHANGES:
        return UNPRICED_PRICE_CHANGES
    return UNPRICED_OTHER


def money_line(consequence: Mapping[str, Any] | None) -> str:
    """MONEY_LINE for a PRICED `fuel-residual-1` row, else the UNPRICED literal of its reason."""
    if consequence is None:
        return UNPRICED_OTHER
    if consequence.get("state") != "PRICED":
        return unpriced_line(consequence.get("price_reason"))
    cur = consequence["currency"]
    return MONEY_LINE.format(lo_m=money(consequence["amount_low"]), hi_m=money(consequence["amount_high"]), cur=cur,
                             p=money2(Decimal(str(consequence["price_value"]))))


def finding_lines(ff: Any, tz: str) -> dict[str, str | None]:
    """The Finding's client lines. SUPPORTED: claim, gap (only with a reporting gap), money, not_why, margin.
    NO_LONGER_SUPPORTED: title, no_longer, not_why only."""
    out: dict[str, str | None] = {"title": TITLE, "claim": None, "gap": None, "money": None, "not_why": NOT_WHY,
                                  "margin": None, "no_longer": None}
    if ff.lifecycle == NO_LONGER_SUPPORTED:
        out["no_longer"] = NO_LONGER
        return out
    w = ff.window
    out["claim"] = claim_line(w.residual_low, w.residual_high, w.night_date)
    if w.gap_minutes > 0:
        out["gap"] = gap_line(w.gap_spans, tz)
    out["money"] = money_line(ff.consequence)
    out["margin"] = margin_line(w.terms.get("accuracy_l"))
    return out
