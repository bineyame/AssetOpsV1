"""CH-4 (build sheet CH-4 §2.2): the server-rendered words of opportunity threads, the seed of the AG-29
vocabulary layer. Every client-facing literal of an opportunity item comes from here. Pure: no I/O."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any, Mapping, Sequence

from assetops_backend.mini_decisions.scenario_rules import decimal_text

MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")

OPP_TITLE = {"PRODUCTIVE_USE_HEADROOM": "Daytime solar unused at {site}"}
OPP_SHORT = {"PRODUCTIVE_USE_HEADROOM": "{site} daytime solar"}
SEEN_LINE = "Seen on {e} of {a} well-observed days · {span}"
VALUE_LINE = "{lo}–{hi} kW over {h} on every eligible day"
VALUE_LINE_ONE = "{lo} kW over {h} on every eligible day"
LIMIT_MIXED = "Limited evidence: readings come from mixed sources, so the size is not worked out yet"
LIMIT_DAYS = "Limited evidence: {n} of the 5 study days lack a reading needed to size it"
LIMIT_UNKNOWN = "Not judged yet: {n} of the 5 study days have no reading"
EVIDENCE_LABEL = {"SUPPORTED": "Supported", "LIMITED": "Limited evidence", "UNKNOWN": "Not judged yet"}
#: MA-1 M4 timeline words; CH-5a2 reuses them for Finding threads.
THREAD_STATE_WORDS = {"OPEN": "Open", "ACTION_IN_HAND": "Action agreed", "CHANGE_APPLIED": "Change made",
                      "RESOLVED_MONITORING": "Checked and working, monitoring", "CLOSED": "Closed",
                      "RECURRED": "Seen again", "REOPENED": "Reopened", "WITHDRAWN": "No longer seen"}
OPP_NONE = "No opportunity found in this period"
MIXED_SOURCE_CODES = ("SOURCE_CLASS_MIXED", "SOURCE_CLASS_UNKNOWN")


def day_text(d: date) -> str:
    """`%-d %b` without the platform's strftime: "1 Nov"."""
    return f"{d.day} {MONTHS[d.month - 1]}"


def seen_line(eligible: int, assessed: int, first: date, last: date) -> str:
    span = day_text(first) if first == last else f"{day_text(first)}–{day_text(last)}"
    return SEEN_LINE.format(e=eligible, a=assessed, span=span)


def value_line(status: str | None, headroom: Mapping[str, Any] | None, window_hours: int | None) -> str | None:
    """CH-9 §2: the headroom over the study's `window_hours` (the fewest eligible daylight hours on any eligible
    day); no line without both."""
    if status != "SUPPORTED" or not headroom or not window_hours:
        return None
    lo, hi = decimal_text(Decimal(str(headroom["low"]))), decimal_text(Decimal(str(headroom["high"])))
    h = daylight_hours_text(int(window_hours))
    return VALUE_LINE_ONE.format(lo=lo, h=h) if lo == hi else VALUE_LINE.format(lo=lo, hi=hi, h=h)


def daylight_hours_text(n: int) -> str:
    """"1 daylight hour", "12 daylight hours"."""
    return f"{n} daylight hour" if n == 1 else f"{n} daylight hours"


def limit_line(status: str | None, limitation_codes: Sequence[str], decisions: Sequence[str | None]) -> str | None:
    if status == "LIMITED":
        if any(c in MIXED_SOURCE_CODES for c in limitation_codes):
            return LIMIT_MIXED
        return LIMIT_DAYS.format(n=sum(1 for d in decisions if d in ("LIMITED", "CONFLICT")))
    if status == "UNKNOWN":
        return LIMIT_UNKNOWN.format(n=sum(1 for d in decisions if d is None))
    return None


# ---- PC-1 claims (build sheet CH-6 §S.2; CH-5a2b builds the type and the count claims, §B13 R3 / §B14) ----------

COMPLETE_BASIS, CHECKED_DAYS_BASIS, NOT_KNOWN_BASIS = "COMPLETE", "CHECKED_DAYS", "NOT_KNOWN"
CLAIM_DAY_KEYS = ("complete", "partial", "low", "no_data", "pending", "expected")
NOT_KNOWN_TEXT = "Not known yet"
#: §B13 R3 texts: (COMPLETE one, COMPLETE many, CHECKED_DAYS n >= 1, CHECKED_DAYS n = 0).
COUNT_TEXT = {
    "count.open_threads": ("{n} open finding", "{n} open findings", "{n} open on the days checked",
                           "None open on the days checked"),
    "count.verified_results": ("{n} fix confirmed", "{n} fixes confirmed", "{n} confirmed on the days checked",
                               "None confirmed on the days checked"),
    "count.opportunities": ("{n} opportunity", "{n} opportunities", "{n} found on the days checked",
                            "None found on the days checked"),
}
#: B7 / R2: the source classes whose verified result is worded "on example data".
EXAMPLE_SOURCES = ("REGISTERED_SIMULATION", "AUTHORED_DEMONSTRATION")


def provenance_suffix(source_state: str | None) -> str:
    """B7 (DS-R1, COH-12): `" on example data"` for an example-data source class, else `""` (None included)."""
    return " on example data" if source_state in EXAMPLE_SOURCES else ""


@dataclass(frozen=True)
class Claim:
    key: str              # e.g. "count.open_threads", "money.estimated_income", "verdict.MG-1"
    value: Any            # int | Decimal string | verdict code | None
    basis: str            # "COMPLETE" | "CHECKED_DAYS" | "NOT_KNOWN"
    days: Mapping[str, int] | None   # {"complete", "partial", "low", "no_data", "pending", "expected"}
    text: str             # rendered once, here

    def to_json(self) -> dict[str, Any]:
        value = str(self.value) if isinstance(self.value, Decimal) else self.value
        return {"key": self.key, "value": value, "basis": self.basis,
                "days": None if self.days is None else dict(self.days), "text": self.text}


def _days_of(days: Any) -> Mapping[str, int] | None:
    if days is None:
        return None
    if isinstance(days, Mapping):
        return {k: int(days[k]) for k in CLAIM_DAY_KEYS}
    return {k: int(getattr(days, k)) for k in CLAIM_DAY_KEYS}


def count_basis(days: Any) -> str:
    """§S.2, the one basis rule: NOT_KNOWN when `days` is None, `expected == 0`, or every expected day is PENDING or
    NO_DATA; COMPLETE when `complete == expected`; else CHECKED_DAYS. `days` is a `GradeCounts` or its §S.2 subset."""
    d = _days_of(days)
    if d is None or d["expected"] == 0 or d["pending"] + d["no_data"] >= d["expected"]:
        return NOT_KNOWN_BASIS
    return COMPLETE_BASIS if d["complete"] == d["expected"] else CHECKED_DAYS_BASIS


def sum_days(per_site: Sequence[Any]) -> Mapping[str, int] | None:
    """The §S.2 subset summed over the Sites in scope; None when any Site's counts are None (the read failed)."""
    total = {k: 0 for k in CLAIM_DAY_KEYS}
    for days in per_site:
        d = _days_of(days)
        if d is None:
            return None
        for k in CLAIM_DAY_KEYS:
            total[k] += d[k]
    return total


def count_claim(key: str, value: int | None, days: Any) -> Claim:
    """A count claim (§B13 R3): a null value (the read failed) is NOT_KNOWN whatever the days."""
    d = _days_of(days)
    basis = NOT_KNOWN_BASIS if value is None else count_basis(d)
    one, many, checked, none = COUNT_TEXT[key]
    if basis == NOT_KNOWN_BASIS:
        text = NOT_KNOWN_TEXT
    elif basis == COMPLETE_BASIS:
        text = (one if value == 1 else many).format(n=value)
    else:
        text = checked.format(n=value) if value else none
    return Claim(key, value, basis, d, text)
