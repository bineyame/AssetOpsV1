"""D-E4.2 (CH6b2-R2): the Portfolio reads a Cold/EV row's thread lifecycle at the request cutoff `k`, never at the
Site's evidence cutoff (its last reading). No DB: a fake `threads` port records its kwargs and shows an event only when
the read's `known_at` reaches the event's `cause_known_at`, as the D-b predicate does."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from assetops_backend.estate.portfolio import attach_threads, portfolio_row

UTC = timezone.utc
#: E4 DB case (EV): last reading 2026-11-03 09:00Z; ACTION_IN_HAND known at 09:40Z.
LAST_READING = datetime(2026, 11, 3, 9, 0, tzinfo=UTC)
IN_HAND_KNOWN = datetime(2026, 11, 3, 9, 40, tzinfo=UTC)
K = datetime(2026, 11, 7, 21, 0, tzinfo=UTC)  # the request cutoff, after both


class Req:
    to = datetime(2026, 11, 8, 0, 0, tzinfo=UTC)
    known_at = None


class Snap:
    """The estate snapshot's `threads` port: records every call; the row's state is ACTION_IN_HAND only when the read's
    `known_at` reaches the event's known time, else OPEN."""

    def __init__(self, event_at: datetime = IN_HAND_KNOWN) -> None:
        self.calls: list[dict] = []
        self.event_at = event_at

    def threads(self, t, fids, aids, **kw):
        self.calls.append({"fids": list(fids), "aids": list(aids), **kw})
        k = kw.get("known_at")
        state = "ACTION_IN_HAND" if k is not None and k >= self.event_at else "OPEN"
        return {"findings": {str(f).lower(): {"id": "th-1", "occurrences": 1, "state": state} for f in fids},
                "actions": {str(a).lower(): "th-1" for a in aids},
                "action_segments": {str(a).lower(): 1 for a in aids}}


def row(domain: str, mechanism: str) -> dict:
    code = {"MINIGRID": "KOBO-001", "COLDCHAIN": "COLD-001", "EV_CHARGING": "EV-001"}[domain]
    return {
        "_site": {"site_code": code, "site_code_key": code.lower()}, "site_id": "S1", "site_code": code,
        "site_name": "Site", "_domain": domain, "finding_id": "f-1", "finding_revision_id": "r-1",
        "finding_label": "x", "title": "x", "_mechanism": mechanism, "episode_start": None, "_episode_end": None,
        "lifecycle": "SUPPORTED", "lens_flags": [], "priority": None, "consequence": None,
        "source_provenance": {"state": "REGISTERED_SIMULATION"}, "_at": LAST_READING,
        "link_refs": {"site": {"kind": "SITE", "site": code},
                      "finding": {"kind": "FINDING", "site": code, "id": "f-1", "revision_id": "r-1"}}}


DOMAIN_ROWS = [("COLDCHAIN", "COLD_START_FAILURE"), ("EV_CHARGING", "EV_INTERRUPTION")]


@pytest.mark.parametrize("domain,mechanism", DOMAIN_ROWS)
def test_a_c_a_domain_row_is_read_at_the_request_cutoff_not_the_evidence_cutoff(domain, mechanism):
    snap, r = Snap(), row(domain, mechanism)
    attach_threads(snap, "t", [r], [], Req(), K, {r["site_code"]: LAST_READING})
    (kw,) = snap.calls
    assert kw["known_at"] == K and kw["known_at"] != LAST_READING
    assert kw["visible_at"] == K and kw["day_at"] == Req.to - timedelta(microseconds=1)  # unchanged
    assert r["_thread_cutoff"] == K


@pytest.mark.parametrize("domain,mechanism", DOMAIN_ROWS)
def test_b_c_an_action_in_hand_after_the_last_reading_reads_pending(domain, mechanism):
    """E4 EV case: last reading 09:00Z, ACTION_IN_HAND known 09:40Z; at k the row reads "Pending"."""
    snap, r = Snap(), row(domain, mechanism)
    attach_threads(snap, "t", [r], [], Req(), K, {r["site_code"]: LAST_READING})
    assert r["_thread"]["state"] == "ACTION_IN_HAND"
    assert portfolio_row(r, [])["workflow_label"] == "Pending"


def test_b_an_open_thread_still_reads_no_action_agreed():
    snap, r = Snap(event_at=K + timedelta(hours=1)), row("COLDCHAIN", "COLD_EXCURSION")
    attach_threads(snap, "t", [r], [], Req(), K, {r["site_code"]: LAST_READING})
    assert portfolio_row(r, [])["workflow_label"] == "No action agreed yet"


def test_d_a_mini_grid_row_call_is_unchanged():
    snap, r = Snap(), row("MINIGRID", "GENERATOR_SUPPORT_CANDIDATE")
    attach_threads(snap, "t", [r], [{"action_id": "A1"}], Req(), K, {"KOBO-001": None})
    (kw,) = snap.calls
    assert kw == {"fids": ["f-1"], "aids": ["A1"], "day_at": Req.to - timedelta(microseconds=1), "known_at": K,
                  "visible_at": K}


def test_rows_of_every_domain_are_read_as_one_group():
    snap = Snap()
    rows = [row("MINIGRID", "UNEXPLAINED_FUEL"), {**row("COLDCHAIN", "COLD_START_FAILURE"), "finding_id": "f-2"},
            {**row("EV_CHARGING", "EV_INTERRUPTION"), "finding_id": "f-3"}]
    attach_threads(snap, "t", rows, [{"action_id": "A1"}], Req(), K,
                   {"KOBO-001": None, "COLD-001": LAST_READING, "EV-001": LAST_READING})
    (kw,) = snap.calls
    assert sorted(kw["fids"]) == ["f-1", "f-2", "f-3"] and kw["known_at"] == K
