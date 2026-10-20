"""W2-06 commit 4: the pure rules of the selected EV session and Finding reads (`.agent/W2-06-build-spec.md`
"Commit 4: selected reads and refusal dry-read" and "Run 5 rulings (r5)" "Commits 4 and 5").

The Postgres snapshot read is `analytics/adapters/postgres_ev_reads.py:EvReadService`: one REPEATABLE READ
transaction captures the committed disposition watermark, the selected `ev-session/1` assessment revision of the
exact window at the cutoff, its `session_revision_ids`, their links, the Finding revisions of that assessment and
the overlapping PENDING/LEASED/FAILED `ev_charging` jobs. Read-only. A missing selection is a 200 `UNKNOWN` read
with null counts and empty arrays; an unreachable store raises `EvReadUnavailable` (503).
"""

from __future__ import annotations

import base64
import binascii
import json
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Iterable
from uuid import UUID

from assetops_backend.analytics.assessment_inputs import iso

MAX_WINDOW = timedelta(days=31)
DEFAULT_LIMIT, MAX_LIMIT = 50, 200
STATES = ("CURRENT", "PENDING_RECOMPUTE", "STALE_SOURCE", "HISTORICAL", "UNKNOWN")
COUNT_KEYS = ("started", "completed", "observed_abort", "incomplete", "contradictory", "orphan",
              "confirmed_delivery", "fault_aborted")
NO_SELECTION_NOTE = "No selected EV session assessment covers this window yet."
PENDING_NOTE = "New evidence is being assessed. The previous result may change."
HISTORICAL_NOTE = "This result reflects records known at the selected cutoff."


class EvReadUnavailable(Exception):
    """The EV read store cannot be reached; the route answers 503, never an empty success."""


class EvPinnedLineageUnavailable(EvReadUnavailable):
    """An exact pinned session/Finding/assessment lineage of a selected EV row cannot be read (estate 409)."""


class EvReadRefused(Exception):
    """A typed refusal raised inside the snapshot (cursor, cutoff)."""

    def __init__(self, status: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status, self.code = status, code


def currentness_state(*, selected: bool, pending: bool, historical: bool) -> str:
    """No selected basis -> UNKNOWN; an explicit earlier cutoff -> HISTORICAL (its stored basis cannot change);
    overlapping PENDING/LEASED/FAILED work -> PENDING_RECOMPUTE; else CURRENT."""
    if not selected:
        return "UNKNOWN"
    if historical:
        return "HISTORICAL"
    return "PENDING_RECOMPUTE" if pending else "CURRENT"


def energy_complete(state: str, supported_kwh: Decimal | None, unknown_meter_seconds: int | None) -> bool | None:
    """The read boolean of the Coverage rule: null for CONTRADICTORY, false for INCOMPLETE, else true only with a
    supported sum and no uncovered second."""
    if state == "CONTRADICTORY":
        return None
    if state == "INCOMPLETE":
        return False
    return supported_kwh is not None and unknown_meter_seconds == 0


def completeness(state: str, unknown_meter_seconds: int | None, evidence: Iterable[tuple[str | None, str, str | None]],
                 intervals: Iterable[tuple[str, str | None]]) -> dict[str, bool]:
    """r8 M2: the four booleans from the exact selected revision's uses only. `evidence` is `(record_kind, use,
    reason)` of its `ev_session_evidence` rows and `intervals` `(use, reason)` of its `ev_meter_interval` rows; a
    SUPPORT row is `use='SUPPORT' AND reason IS NULL`. Reason codes explain a missing chip but never create one.
    A SUPPORT row has passed the R4 clock gate, so `clock` needs a SUPPORT START and no linked CLOCK_UNATTESTED
    exclusion."""
    events, meters = list(evidence), list(intervals)
    support = {kind for kind, use, reason in events if use == "SUPPORT" and reason is None}
    start = "EV_SESSION_START" in support
    unattested = any(reason == "CLOCK_UNATTESTED" for _k, _u, reason in events)         or any(reason == "CLOCK_UNATTESTED" for _u, reason in meters)
    return {"start": start,
            "terminal": bool(support & {"EV_SESSION_END", "EV_SESSION_ABORT"}),
            "meter": any(use == "SUPPORT" and reason is None for use, reason in meters)
            and unknown_meter_seconds == 0 and state != "CONTRADICTORY",
            "clock": start and not unattested}


def encode_cursor(lo: datetime, hi: datetime, known: datetime, basis: str, last_time: datetime,
                  last_id: UUID) -> str:
    raw = json.dumps([iso(lo), iso(hi), iso(known), basis, iso(last_time), str(last_id).lower()],
                     separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def decode_cursor(cursor: str) -> tuple[list[str], datetime, UUID]:
    """The six canonical members, the last row's time and ID; anything else is 422 `EV_CURSOR_INVALID`."""
    try:
        doc: Any = json.loads(base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4)))
        if not isinstance(doc, list) or len(doc) != 6 or not all(isinstance(x, str) for x in doc):
            raise ValueError("shape")
        last_time = datetime.fromisoformat(doc[4].replace("Z", "+00:00"))
        last_id = UUID(doc[5])
        if encode_cursor(*(datetime.fromisoformat(x.replace("Z", "+00:00")) for x in doc[:3]), doc[3],
                         last_time, last_id) != cursor:
            raise ValueError("not canonical")
    except (ValueError, TypeError, binascii.Error, UnicodeDecodeError) as error:
        raise EvReadRefused(422, "EV_CURSOR_INVALID", "The cursor is not an EV read cursor.") from error
    return doc, last_time, last_id


def check_cursor(doc: list[str], lo: datetime, hi: datetime, known: datetime, basis: str | None) -> None:
    if doc[:4] != [iso(lo), iso(hi), iso(known), basis]:
        raise EvReadRefused(409, "EV_CURSOR_BASIS_CHANGED",
                            "The selected window, cutoff or basis changed since this cursor was issued; "
                            "reload the first page.")
