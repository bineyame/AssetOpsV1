"""DD1b2-R6 O1 (L0): the Action Ref on the `/chain` and `/threads` wire.

A domain intent raised from an opportunity (the mill) has no Action page, so its Ref is the verdict page
(`DOMAIN_VERDICT`). A MINI_TRIAL and a Finding's domain intent (Cold/EV) keep their ACTION Ref, byte-equal to the
builder before the fix (`refs.action_ref(site, id)`).
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

from assetops_backend.chain import refs as R
from assetops_backend.chain import site_chain

SITE = "KOBO-001"
ACCEPTED = datetime(2026, 10, 26, 9, 0, tzinfo=timezone.utc)


def _action(action_id: str, kind: str, *, finding: str | None = None, opportunity: str | None = None) -> dict:
    return {"thread_id": "t-1", "action_id": action_id, "action_code": "ACT-000004", "kind": kind,
            "origin_finding_id": finding, "origin_opportunity_id": opportunity, "accepted_at": ACCEPTED}


def _wire(action: dict) -> dict:
    out = site_chain.actions_of({"actions": [action]}, ["t-1"], site=SITE, tz="Africa/Addis_Ababa", cutoff=None,
                                verification={})
    assert len(out) == 1
    return out[0]["ref"]


def test_mini_trial_from_a_finding_is_an_action_ref() -> None:
    ref = _wire(_action("a-1", "MINI_TRIAL", finding="f-1"))
    assert json.dumps(ref, sort_keys=True) == json.dumps(R.action_ref(SITE, "a-1"), sort_keys=True)
    assert R.href_for(ref) == "/sites/KOBO-001/actions/a-1"


def test_domain_intent_from_a_finding_is_unchanged() -> None:
    for site_kind in ("COLD-LAB-001", "EV-LAB-001"):
        a = _action("a-2", "DOMAIN_INTENT", finding="f-2")
        out = site_chain.actions_of({"actions": [a]}, ["t-1"], site=site_kind, tz="UTC", cutoff=None,
                                    verification={})
        assert json.dumps(out[0]["ref"], sort_keys=True) == json.dumps(R.action_ref(site_kind, "a-2"),
                                                                        sort_keys=True)
        assert out[0]["ref"]["kind"] == "ACTION"


def test_domain_intent_from_an_opportunity_is_the_verdict_page() -> None:
    ref = _wire(_action("a-3", "DOMAIN_INTENT", opportunity="opp-1"))
    assert ref == {"kind": "DOMAIN_VERDICT", "site": SITE, "id": "a-3"}
    assert R.href_for(ref) == "/sites/KOBO-001/domain-actions/a-3/verification"


def test_the_kind_is_registered() -> None:
    assert "DOMAIN_VERDICT" in R.KINDS
