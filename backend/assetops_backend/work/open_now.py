"""OPEN-NOW: the open requests and incidents a Work list response carries beside its windowed rows.

Same snapshot connection, same cutoff K and same Site scope as the list; no date filter. The window bounds below
are the widest instants the store accepts, so `eligible_cases` applies only its cutoff and Site predicates.
The sentence is written here, never composed by the page from raw codes.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterable, Mapping

from assetops_contracts.work_open_now import OPEN_STATES, OpenNowCounts

from assetops_backend.work import model as m

EARLIEST = datetime(1, 1, 1, tzinfo=timezone.utc)
LATEST = datetime(9999, 12, 31, tzinfo=timezone.utc)
_NOUNS = (("incidents", "incident", "incidents"), ("requests", "request", "requests"))
NOTHING_OPEN = "Nothing open now"


def site_open_now(rx: Any, known_at: datetime) -> OpenNowCounts:
    """One Site's open incidents and requests at K, whatever their dates (raises as `reduce_state` does)."""

    def count(kind: str) -> int:
        return sum(1 for case in rx.eligible_cases(kind, EARLIEST, LATEST, known_at)
                   if m.reduce_state(kind, rx.events(str(case["id"]).lower(), known_at)) in OPEN_STATES)

    return OpenNowCounts(incidents=count(m.INCIDENT), requests=count(m.REQUEST))


def open_now_line(counts: Mapping[str, Any]) -> str:
    """"Open now: 2 incidents, 1 request, whatever the dates"; a kind with none is left out; all zero reads
    "Nothing open now"."""
    parts = [f"{counts[key]} {one if counts[key] == 1 else many}" for key, one, many in _NOUNS if counts[key]]
    return f"Open now: {', '.join(parts)}, whatever the dates" if parts else NOTHING_OPEN


def open_now_wire(totals: Iterable[OpenNowCounts]) -> dict[str, int | str]:
    """The summed counts over the list's Sites, with their sentence."""
    total = OpenNowCounts(0, 0)
    for counts in totals:
        total = total + counts
    wire = total.wire("")
    return total.wire(open_now_line(wire))
