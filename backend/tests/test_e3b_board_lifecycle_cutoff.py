"""D-E3b.1/2 (E4-C5, CH6b2-R2): the outcome board reads a Cold/EV Finding's thread lifecycle at the REQUEST cutoff
`k` (`lifecycle_cutoff`, as `/chain` and the Portfolio do), never at the evidence cutoff (the window's last reading).

No DB: a fake `threads.lookup` records its kwargs and shows ACTION_IN_HAND only when the read's `known_at` reaches the
event's known time (after the evidence cutoff), as the D-b predicate does. Visibility (`visible_at`, CH5a1-R2 R-1),
the state day and the board's evidence cutoff (`window.known_at`) do not move; a mini board's call is unchanged.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime, timedelta, timezone

import pytest

import test_ch5a1_board_contract as BC
from assetops_backend import read_scope
from assetops_backend.site_outcomes.read import SiteOutcomeBoardService

UTC = timezone.utc
#: The fake overviews' evidence cutoffs (`test_ch5a1_board_contract` ColdSite / EvSite `window.known_at`).
COLD_EVIDENCE = datetime(2026, 11, 1, 0, 0, tzinfo=UTC)
EV_EVIDENCE = datetime(2026, 10, 28, 0, 0, tzinfo=UTC)
K = BC.KNOWN  # 2026-11-03 12:00Z: the request cutoff, after both evidence cutoffs


class Threads:
    """The board thread port: records every call; ACTION_IN_HAND only when `known_at` reaches `event_at` (None =
    as known now, which sees it), else OPEN."""

    def __init__(self, event_at: datetime) -> None:
        self.calls: list[dict] = []
        self.event_at = event_at

    def lookup(self, tenant_id, finding_ids, action_ids, **kw):
        self.calls.append(kw)
        k = kw.get("known_at")
        state = "ACTION_IN_HAND" if k is None or k >= self.event_at else "OPEN"
        thread = {"id": "th-1", "occurrence_no": 1, "occurrences": 1, "segment_no": 1, "state": state,
                  "state_effective_day": None, "state_day": None}
        fs = {str(f).lower(): {**thread, "wire_keys": tuple(thread)} for f in finding_ids}
        return {"findings": fs, "actions": {}}

    def opportunity_threads(self, *a, **kw):  # the mini board's opportunity read (unchanged; not under test)
        return []


def _issue_threads(body: dict) -> list[dict]:
    """Each FINDING issue's `ref.thread` on the board's rows (the read COH-13 compares with the Portfolio)."""
    return [i["ref"]["thread"] for r in body["rows"] for i in r.get("issues") or []
            if i.get("kind") == "FINDING" and isinstance((i.get("ref") or {}).get("thread"), dict)]


def _board(case: str, known_at: datetime | None, event_at: datetime) -> tuple[dict, Threads]:
    threads = Threads(event_at)
    services = replace(BC.services(BC.Port(), []), threads=threads)
    site, window = BC.CASES[case]
    with read_scope.scope(f"test:e3b:{case}"):
        body = SiteOutcomeBoardService(services).board(site, known_at=known_at, **window)
    return body, threads


@pytest.mark.parametrize("case, evidence", [("cold_2026-10-31", COLD_EVIDENCE), ("ev_2026-10-27", EV_EVIDENCE)])
@pytest.mark.parametrize("request_known_at", [None, K])
def test_cold_ev_board_reads_the_lifecycle_at_the_request_cutoff(case, evidence, request_known_at):
    """(a) Cold and (b) EV: the evidence cutoff is earlier than the request; the lookup's `known_at` is the request
    value (None when live), `visible_at` stays the request, and the evidence cutoff stays the board's window cutoff."""
    event_at = evidence + timedelta(minutes=40)  # an Action agreed after the last reading (E3b: EV 09:40Z vs 09:00Z)
    body, threads = _board(case, request_known_at, event_at)
    (call,) = threads.calls
    assert call["known_at"] == request_known_at
    assert call["visible_at"] == request_known_at                       # R-1: occurrence visibility unchanged
    assert body["window"]["known_at"].startswith(evidence.strftime("%Y-%m-%dT%H:%M"))  # evidence cutoff unchanged
    assert isinstance(call["day"], date)                                # the state day is still the board day
    shown = _issue_threads(body)
    assert shown and {t["state"] for t in shown} == {"ACTION_IN_HAND"}, shown


@pytest.mark.parametrize("request_known_at", [K])
def test_mini_board_lookup_call_is_unchanged(request_known_at):
    """(c) A mini board's cutoff is already the request's: the lookup reads at it, with its opportunity extras."""
    body, threads = _board("kobo_2026-10-31", request_known_at, request_known_at)
    (call,) = threads.calls
    assert call["known_at"] == request_known_at and call["visible_at"] == request_known_at
    assert call["day"] == date(2026, 10, 31)
    assert "opportunity_window" in call and "site_id" in call
