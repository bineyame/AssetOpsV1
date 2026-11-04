"""CH-5a1 L0 (CH5a1-R2 R-1): occurrence visibility is transaction time, bounded only by the request's `known_at`.

`source_known_at` is the revision's `created_at` (0045 / CH3-R D-b). On the polish clone it is the build's wall
clock (2 Nov 18:42Z) while the Cold evidence cutoff is story time (31 Oct 17:05Z). Comparing the two hid every
Cold/EV thread (COH-10 x7, COH-11 x2). The fakes below apply the SQL predicate of `chain/lookup.py` `LOOKUP`
(`:kv IS NULL OR coalesce(source_known_at, joined_at) <= :kv`) to the bound each caller hands the port, so a caller
that passes the story cutoff as the visibility bound fails here. The story cutoff still reaches the port as the
*state* bound (`known_at`).
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone

import pytest

import test_ch5a1_board_contract as BC
from assetops_backend import read_scope
from assetops_backend.estate.portfolio import attach_threads
from assetops_backend.site_outcomes.read import SiteOutcomeBoardService

UTC = timezone.utc
STORY_CUTOFF = datetime(2026, 10, 31, 17, 5, tzinfo=UTC)   # Cold evidence cutoff (story / valid time)
CREATED = datetime(2026, 11, 2, 18, 42, tzinfo=UTC)        # the revision's created_at = source_known_at
LATER = datetime(2026, 11, 3, 12, tzinfo=UTC)              # a request known_at after created_at
EARLIER = datetime(2026, 11, 2, 0, tzinfo=UTC)             # a request known_at before created_at


def _visible(visible_at: datetime | None) -> bool:
    """`LOOKUP`'s occurrence predicate for one occurrence created at `CREATED`."""
    return visible_at is None or CREATED <= visible_at


class Threads:
    """The board thread port (`PostgresThreadSources.lookup`) over one stored occurrence per listed Finding."""

    def __init__(self) -> None:
        self.calls: list[dict] = []

    def lookup(self, tenant_id, finding_ids, action_ids, *, day=None, known_at=None, visible_at=None, **extra):
        self.calls.append({"known_at": known_at, "visible_at": visible_at})
        fs = {str(f).lower(): {"id": "th-1", "occurrence_no": 1, "occurrences": 1, "segment_no": 1,
                               "state": "OPEN", "state_effective_day": None, "state_day": None}
              for f in finding_ids if _visible(visible_at)}
        return {"findings": fs, "actions": {}}


def _cold_board(known_at: datetime | None) -> tuple[dict, Threads]:
    port, never, threads = BC.Port(), [], Threads()
    services = BC.services(port, never)
    services = replace(services, threads=threads)
    site, window = BC.CASES["cold_2026-10-31"]
    with read_scope.scope("test:r1"):
        body = SiteOutcomeBoardService(services).board(site, known_at=known_at, **window)
    return body, threads


@pytest.mark.parametrize("request_known_at", [None, LATER])
def test_board_shows_an_occurrence_created_after_the_story_cutoff(request_known_at):
    """Live, or a request `known_at` after `created_at`: the thread shows although `created_at` is after the
    Cold story cutoff; the state is still read at the board's own cutoff, not at the request's."""
    body, threads = _cold_board(request_known_at)
    (call,) = threads.calls
    assert call["visible_at"] == request_known_at
    assert call["known_at"] is not None and call["known_at"] != call["visible_at"]
    shown = [f for f in _findings(body) if f is not None]
    assert shown, body["rows"]


def test_board_hides_an_occurrence_created_after_an_explicit_earlier_known_at():
    body, threads = _cold_board(EARLIER)
    assert threads.calls[0]["visible_at"] == EARLIER
    assert _findings(body) and all(f is None for f in _findings(body))


def _findings(body: dict) -> list:
    """Each Finding item's `thread` on the board's rows (the wire puts Findings under each row's `findings`)."""
    out = []

    def walk(v):
        if isinstance(v, dict):
            if "finding_id" in v and "thread" in v:
                out.append(v["thread"])
            for x in v.values():
                walk(x)
        elif isinstance(v, list):
            for x in v:
                walk(x)

    walk(body)
    return out


class Snap:
    """The estate snapshot's `threads` (Portfolio), with the same predicate on `visible_at`."""

    def __init__(self) -> None:
        self.calls: list[dict] = []

    def threads(self, t, fids, aids, **kw):
        self.calls.append(kw)
        return {"findings": {f: {"id": "th-1", "occurrences": 1} for f in fids if _visible(kw.get("visible_at"))},
                "actions": {}}


class Req:
    to = datetime(2026, 11, 1, 21, tzinfo=UTC)
    known_at = None


@pytest.mark.parametrize("envelope_k,shown", [(LATER, True), (EARLIER, False)])
def test_portfolio_cold_row_visibility_follows_the_envelope_not_the_story_cutoff(envelope_k, shown):
    snap, row = Snap(), {"finding_id": "f1", "_cutoff": STORY_CUTOFF}
    attach_threads(snap, "t", [row], [], Req(), envelope_k)
    (kw,) = snap.calls
    assert kw["known_at"] == STORY_CUTOFF and kw["visible_at"] == envelope_k
    assert (row["_thread"] is not None) is shown
