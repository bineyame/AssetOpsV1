"""CH-4 (build sheet CH-4 §2.2): the server-rendered words of opportunity threads, the seed of the AG-29
vocabulary layer. Every client-facing literal of an opportunity item comes from here. Pure: no I/O."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any, Mapping, Sequence

from assetops_backend.mini_decisions.scenario_rules import decimal_text

MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")

OPP_TITLE = {"PRODUCTIVE_USE_HEADROOM": "Daytime solar unused at {site}"}
OPP_SHORT = {"PRODUCTIVE_USE_HEADROOM": "{site} daytime solar"}
SEEN_LINE = "Seen on {e} of {a} well-observed days · {span}"
VALUE_LINE = "{lo}–{hi} kW at midday on every eligible day"
VALUE_LINE_ONE = "{lo} kW at midday on every eligible day"
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


def value_line(status: str | None, headroom: Mapping[str, Any] | None) -> str | None:
    if status != "SUPPORTED" or not headroom:
        return None
    lo, hi = decimal_text(Decimal(str(headroom["low"]))), decimal_text(Decimal(str(headroom["high"])))
    return VALUE_LINE_ONE.format(lo=lo) if lo == hi else VALUE_LINE.format(lo=lo, hi=hi)


def limit_line(status: str | None, limitation_codes: Sequence[str], decisions: Sequence[str | None]) -> str | None:
    if status == "LIMITED":
        if any(c in MIXED_SOURCE_CODES for c in limitation_codes):
            return LIMIT_MIXED
        return LIMIT_DAYS.format(n=sum(1 for d in decisions if d in ("LIMITED", "CONFLICT")))
    if status == "UNKNOWN":
        return LIMIT_UNKNOWN.format(n=sum(1 for d in decisions if d is None))
    return None
