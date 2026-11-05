"""CH-9b1 L0 (build sheet CH-9b, CH9b1-R): the typed Action origin, the opportunity-origin thread link, the MINI
closed creation body, and the mill Action's ACTION_ACCEPTED -> ACTION_APPLIED on its opportunity thread."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest

from assetops_backend.chain import threads as th
from assetops_backend.chain.lifecycle_run import run_lifecycle
from assetops_backend.work import domain_action as d

UTC = timezone.utc
ADDIS = "Africa/Addis_Ababa"
T, S = uuid4(), uuid4()


def _opportunity_row(eligible: set[int]) -> dict:
    first = date(2026, 10, 27)
    return {"tenant_id": T, "site_id": S, "site_tz": ADDIS, "opportunity_id": uuid4(), "first_day": first,
            "last_day": first + timedelta(days=4), "created_at": datetime(2026, 11, 3, 9, tzinfo=UTC),
            "revision_id": uuid4(), "eligible_days": len(eligible),
            "day_rows": [{"local_day": (first + timedelta(days=i)).isoformat(),
                          "decision": "ELIGIBLE" if i in eligible else "EXCLUDED"} for i in range(5)]}


# --- the typed origin ---------------------------------------------------------------------------------------------

def test_origin_of_reads_exactly_one_pair():
    f, o = uuid4(), uuid4()
    assert th.Origin.of({"id": "a", "origin_finding_id": str(f)}) == th.Origin(th.ORIGIN_FINDING, f)
    assert th.Origin.of({"id": "a", "origin_finding_id": None, "origin_opportunity_id": o}) == \
        th.Origin(th.ORIGIN_OPPORTUNITY, o)
    with pytest.raises(ValueError):
        th.Origin.of({"id": "a", "origin_finding_id": f, "origin_opportunity_id": o})
    with pytest.raises(ValueError):
        th.Origin.of({"id": "a", "origin_finding_id": None, "origin_opportunity_id": None})
    assert th.Origin(th.ORIGIN_OPPORTUNITY, o).columns() == {"origin_finding_id": None, "origin_opportunity_id": o}


def test_opportunity_link_and_mini_trial_is_finding_only():
    port = th.MemoryThreads()
    reg = th.ThreadRegistry(port)
    src = th.opportunity_source(_opportunity_row({1, 2, 3}))
    action = uuid4()
    origin = th.Origin(th.ORIGIN_OPPORTUNITY, src.opportunity_id)
    assert reg.link_action("DOMAIN_INTENT", action, origin) == th.PENDING_PLACEMENT
    reg.place_all([src])
    with pytest.raises(ValueError):
        reg.link_action("MINI_TRIAL", uuid4(), origin)
    assert reg.link_action("DOMAIN_INTENT", action, origin) == th.LINKED
    (link,) = port.links.values()
    assert link["origin_finding_id"] is None and link["origin_opportunity_id"] == src.opportunity_id
    # link_all reads the origin pair off the chain_action row
    assert reg.link_all([{"kind": "DOMAIN_INTENT", "id": action, "origin_finding_id": None,
                          "origin_opportunity_id": src.opportunity_id}]).counts == {th.ALREADY_LINKED: 1}


# --- the closed creation body -------------------------------------------------------------------------------------

def _body(**over) -> dict:
    base = {"title": "Run the mill at midday", "owner_label": None, "due_at": None,
            "raised_at": "2026-11-04T09:00:00Z", "actor": {"kind": "SERVICE", "id": "story", "attestation": "x"},
            "idempotency_key": "mill-action-0001"}
    return {**base, **over}


def test_mini_body_takes_the_opportunity_pair_only():
    o, r = str(uuid4()), str(uuid4())
    got = d.action_body(_body(domain="MINI", origin_opportunity_id=o, origin_opportunity_revision_id=r))
    assert got["domain"] == "MINI" and got["origin_opportunity_id"] == o and got["origin_opportunity_revision_id"] == r
    assert "origin_finding_id" not in got
    with pytest.raises(d.DomainIntentRefused) as e:  # a Finding pair on a MINI body is outside its closed shape
        d.action_body(_body(domain="MINI", origin_finding_id=o, origin_finding_revision_id=r))
    assert e.value.message == d.MINI_MESSAGES["DOMAIN_INTENT_INVALID"]


def test_cold_body_normalizes_exactly_as_before():
    f, r = str(uuid4()), str(uuid4())
    got = d.action_body(_body(domain="COLDCHAIN", origin_finding_id=f, origin_finding_revision_id=r))
    assert list(got) == ["domain", "origin_finding_id", "origin_finding_revision_id", "title", "owner_label",
                         "due_at", "raised_at", "idempotency_key"]
    with pytest.raises(d.DomainIntentRefused):
        d.action_body(_body(domain="COLDCHAIN", origin_opportunity_id=f, origin_opportunity_revision_id=r))
    assert d.spec_of("MINI") is d.MINI_SPEC and "MINI" not in d.DOMAINS  # MINI declares no intent


# --- lifecycle: ACCEPTED from the row, APPLIED from the case COMPLETE ----------------------------------------------

class _Reader:
    def __init__(self, inputs: dict) -> None:
        self.inputs = inputs

    def lifecycle_inputs(self, tenant_id: UUID, site_id: UUID) -> dict:
        return self.inputs


def test_mill_action_accepted_then_applied_and_not_withdrawn():
    port = th.MemoryThreads()
    reg = th.ThreadRegistry(port)
    row = _opportunity_row({1, 2, 3})
    src = th.opportunity_source(row)
    reg.place_all([src])
    action = uuid4()
    reg.link_action("DOMAIN_INTENT", action, th.Origin(th.ORIGIN_OPPORTUNITY, src.opportunity_id))
    raised = datetime(2026, 11, 4, 9, tzinfo=UTC)
    completed = datetime(2026, 11, 6, 12, tzinfo=UTC)
    inputs = {"tz": ADDIS, "now": datetime(2026, 11, 7, tzinfo=UTC), "site_type": "MINIGRID",
              "action_events": [], "outcomes": [], "snapshots": [], "finding_lifecycle": {},
              "domain_actions": [{"id": action, "recorded_at": raised}],
              "case_completions": [{"id": uuid4(), "action_id": action, "occurred_at": completed,
                                    "recorded_at": completed + timedelta(minutes=5)}],
              # CH-4 R6: the head now has 0 eligible days, but the linked Action keeps the thread supported
              "opportunity_heads": {str(src.opportunity_id).lower(): {
                  "revision_id": str(uuid4()), "created_at": completed, "eligible_days": 0}}}
    report = run_lifecycle(_Reader(inputs), port, T, S)
    states = [e["state"] for _, e in sorted(port.events.items(), key=lambda kv: kv[0][1])]
    assert states == ["OPEN", "ACTION_IN_HAND", "CHANGE_APPLIED"], report
    applied = [e for e in port.events.values() if e["state"] == "CHANGE_APPLIED"][0]
    assert applied["cause_kind"] == "DOMAIN_CASE" and applied["effective_day"] == date(2026, 11, 6)
    # without the link the same inputs withdraw the opportunity (R6 holds; the link is what protects it)
    bare = th.MemoryThreads()
    th.ThreadRegistry(bare).place_all([src])
    run_lifecycle(_Reader(inputs), bare, T, S)
    assert "WITHDRAWN" in [e["state"] for e in bare.events.values()]
