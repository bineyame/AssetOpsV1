"""W2-03 commit 4: selected cold reads (`.agent/W2-03-build-spec.md` "Commit 4 - selected reads" and the
"freshness reference for commit 4" amendment).

The pure currentness, freshness and cursor rules live here; the Postgres snapshot read is
`analytics/adapters/postgres_assessment_store.py:ColdReadService`. One REPEATABLE READ snapshot per request: the committed disposition watermark captured first, the latest DEFAULT
selection per analytic whose window covers the request and whose run cutoff is at or before `known_at`, its
assessment revision, the episode revisions of that revision and the cold Findings (`domain='cold_chain'`) whose
latest revision was known at the cutoff. Read-only; nothing here inserts. A missing selection is a valid
`UNKNOWN` read with null values and empty arrays; an unreachable store raises `ColdReadUnavailable` (503).
"""

from __future__ import annotations

import base64
import binascii
import json
from datetime import datetime, timedelta
from uuid import UUID

from assetops_backend.analytics.assessment_inputs import iso

#: The probe recency limit of a CURRENT read.
PROBE_RECENCY = timedelta(minutes=10)
STATES = ("CURRENT", "PENDING_RECOMPUTE", "STALE_SOURCE", "HISTORICAL", "UNKNOWN")
MAX_WINDOW = timedelta(days=31)
DEFAULT_LIMIT, MAX_LIMIT = 50, 200
NO_SPOILAGE = "No spoilage, product-loss or failed-part determination is made."
PENDING_NOTE = ("Newer accepted evidence is waiting to be assessed; this is the previous selected result, "
                "not a current claim.")
HISTORICAL_NOTE = "Read at an earlier evidence cutoff; newer committed evidence exists."
NO_SELECTION_NOTE = "No selected cold assessment covers this window yet."
STALE_NOTE = "The latest usable probe reading is more than 10 minutes before the end of the window."
FUTURE_NOTE = "The window has not ended yet."
NO_PROBE_NOTE = "No usable probe reading in the selected window."


class ColdReadUnavailable(Exception):
    """The cold read store cannot be reached; the route answers 503, never an empty success."""


class ColdPinnedLineageUnavailable(ColdReadUnavailable):
    """An exact pinned episode/Finding/assessment lineage of a selected cold row cannot be read (estate 409)."""


class ColdCursorRefused(Exception):
    def __init__(self, status: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status, self.code = status, code


def probe_fresh(latest_probe_at: datetime | None, reference_at: datetime) -> bool:
    """The single probe-recency rule. `reference_at` is the selected half-open window's `to` boundary
    (Architect amendment 2026-10-18: window-scoped freshness, not live gateway contact or the wall clock)."""
    return latest_probe_at is not None and reference_at - latest_probe_at <= PROBE_RECENCY


def currentness_state(*, pending: bool, historical: bool, selected: bool, latest_probe_at: datetime | None,
                      window_to: datetime | None, now: datetime) -> str:
    """Amendment precedence: pending -> PENDING_RECOMPUTE; older explicit cutoff -> HISTORICAL; no settled
    selection, no qualifying probe or a future `to` -> UNKNOWN; stale probe at `to` -> STALE_SOURCE; else CURRENT."""
    if pending:
        return "PENDING_RECOMPUTE"
    if historical:
        return "HISTORICAL"
    if not selected or latest_probe_at is None or window_to is None or window_to > now:
        return "UNKNOWN"
    return "CURRENT" if probe_fresh(latest_probe_at, window_to) else "STALE_SOURCE"


def encode_cursor(anchor: datetime, finding_id: UUID, basis: str) -> str:
    raw = json.dumps({"basis": basis, "id": str(finding_id), "t": iso(anchor)}, sort_keys=True,
                     separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def decode_cursor(cursor: str, basis: str) -> tuple[datetime, UUID]:
    try:
        doc = json.loads(base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4)))
        anchor = datetime.fromisoformat(doc["t"].replace("Z", "+00:00"))
        finding_id = UUID(doc["id"])
        held = doc["basis"]
    except (ValueError, KeyError, TypeError, binascii.Error) as error:
        raise ColdCursorRefused(422, "COLD_CURSOR_INVALID", "The cursor is not a cold Finding cursor.") from error
    if held != basis:
        raise ColdCursorRefused(409, "COLD_CURSOR_BASIS_CHANGED",
                                "The selected basis changed since this cursor was issued; reload the first page.")
    return anchor, finding_id
