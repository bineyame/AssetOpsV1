"""CH-5a2a L1 (build sheet Part B §B10 item 2): the `outcome-chain-1` bodies of the three `/chain` routes, served by
`chain_api.build_chain_router` over the CH-5a1 fixture `ChainReader` (`test_ch5a1_board_contract`), equal their
stored goldens. These are the CH-6 and CH-5b starting goldens.

Cases: SiteChain Kobo 31 Oct and 1 Nov, Cold 31 Oct, EV 27 Oct, the EstateChain week (25 Oct - 1 Nov UTC), and the
Kobo generator thread. The fixture port adds `site_threads`: one Kobo generator thread (two Finding occurrences, an
OPEN then an ACTION_IN_HAND event known on 1 Nov, the linked mini Action a1) and one headroom opportunity thread.

Regenerate with `ASSETOPS_REGEN_CH5A2_GOLDENS=1` only for an intended, reviewed change.
"""
from __future__ import annotations

import json
import os
from contextlib import contextmanager
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import test_ch5a1_board_contract as BC
from assetops_backend import read_scope
from assetops_backend.chain.composition import chain_policy_versions
from assetops_backend.chain_api import build_chain_router
from assetops_backend.site_outcomes.read import SiteOutcomeBoardService

GOLDEN = Path(__file__).parent / "fixtures" / "ch5a2_chain_contract"
REGEN = os.environ.get("ASSETOPS_REGEN_CH5A2_GOLDENS") == "1"
T1 = "00000000-0000-4000-8000-0000000000f1"   # the Kobo generator thread
T2 = "00000000-0000-4000-8000-0000000000f2"   # the Kobo headroom opportunity thread
OTHER = "00000000-0000-4000-8000-0000000000f9"
GEN, HEAD = "GENERATOR_SUPPORT_CANDIDATE", "PRODUCTIVE_USE_HEADROOM"


def _occ(tid, mech, no, fid, oid, opp_no, start, end):
    return {"thread_id": tid, "mechanism": mech, "subject_ref": "asset-1", "occurrence_no": no, "finding_id": fid,
            "opportunity_id": oid, "opportunity_no": opp_no, "episode_start": start, "episode_end": end}


def _event(tid, seq, state, kind, cause, day, recorded, known=None):
    return {"thread_id": tid, "seq": seq, "state": state, "cause_kind": kind, "cause_id": cause,
            "effective_day": day, "recorded_at": recorded, "cause_known_at": known}


THREAD_ROWS = {BC.KOBO.site_id: {
    "occurrences": (_occ(T1, GEN, 1, "f1", None, None, BC.at(31, 6), BC.at(31, 7)),
                    _occ(T1, GEN, 2, "f2", None, None, BC.at(1, 5, month=11), BC.at(1, 6, month=11)),
                    _occ(T2, HEAD, 1, None, "o1", 3, BC.at(26, 21), BC.at(30, 21))),
    "events": (_event(T1, 1, "OPEN", "OCCURRENCE", "f1", date(2026, 10, 31), BC.at(31, 8)),
               _event(T1, 2, "ACTION_IN_HAND", "ACTION_EVENT", "e1", date(2026, 11, 1), BC.at(1, 9, month=11)),
               _event(T2, 1, "OPEN", "OCCURRENCE", "o1", date(2026, 10, 27), BC.at(31, 1))),
    "actions": ({"action_id": "a1", "action_code": "ACT-000001", "kind": "MINI_TRIAL", "thread_id": T1,
                 "origin_finding_id": "f1", "accepted_at": BC.at(1, 8, month=11)},)}}


class Port(BC.Port):
    def site_threads(self, tenant_id, site_id, known_at):
        # MB-1-R Q1: no DOMAIN_INTENT row here, so no `outcome` / `outcome_recorded_at` keys are needed.
        self.calls.append(("site_threads", (site_id,)))
        return THREAD_ROWS.get(site_id, {"occurrences": (), "events": (), "actions": ()})

    def evidence_cutoff(self, tenant_id, site_id, known_at):  # CH-5a2b: no disposition -> the request's cutoff
        self.calls.append(("evidence_cutoff", (site_id,)))
        return None


class Registry:
    SITES = {s.site_code: s for s in (BC.KOBO, BC.COLD, BC.EV)}

    def tenant(self):
        return BC.TENANT

    def imported(self, code):
        s = self.SITES.get(code)
        return None if s is None else SimpleNamespace(tenant_id=s.tenant_id, id=s.site_id, site_code=s.site_code,
                                                      name=s.site_name, site_type=s.site_type, timezone=s.timezone)


class EstateScope:
    def site_list(self, tenant, parsed, admit):
        return {"sites": [{"site_code": c} for c in Registry.SITES if admit(c)]}


class Threads:  # the board service's thread port: only the estate route's opportunity read is used here
    def opportunity_threads(self, tenant_id, site_ids, from_, to, k):
        # CH9-R4 F2: the item carries its study, which the Kobo board's Grow headline now reads (mirrors B2.DEPTH).
        r = BC.B2.DEPTH["renewable"]
        return [{"site_code": BC.KOBO.site_code, "thread_id": T2, "title": "Daytime solar unused at Kobo",
                 "study": {"headroom_kw": r["headroom_kw"], "eligible_days": r["eligible_days"],
                           "assessed_days": r["assessed_days"]}}]

    def lookup(self, tenant_id, finding_ids, action_ids, **kw):
        from assetops_backend.chain.lookup import thread_lookup
        return {**thread_lookup([]), "opportunities": []}


def client(port: Port | None = None, seen: list | None = None) -> TestClient:
    from dataclasses import replace
    port = port or Port()
    services = replace(BC.services(port, []), threads=Threads())
    app = FastAPI()
    app.include_router(build_chain_router(SiteOutcomeBoardService(services), Registry(), estate=EstateScope(),
                                          tenant=lambda: BC.TENANT, policy_versions=chain_policy_versions))
    return TestClient(app)


CASES = {
    "site_kobo_2026-10-31": ("/api/sites/KOBO-001/chain", {"date": "2026-10-31"}),
    "site_kobo_2026-11-01": ("/api/sites/KOBO-001/chain", {"date": "2026-11-01"}),
    "site_cold_2026-10-31": ("/api/sites/COLD-LAB-001/chain", {"from": "2026-10-30T21:00:00Z",
                                                               "to": "2026-10-31T21:00:00Z"}),
    "site_ev_2026-10-27": ("/api/sites/EV-LAB-001/chain", {"from": "2026-10-27T08:00:00Z",
                                                           "to": "2026-10-27T16:00:00Z"}),
    "estate_week_2026-10-25": ("/api/estate/chain", {"from": "2026-10-25T00:00:00Z", "to": "2026-11-01T00:00:00Z"}),
    "thread_kobo_generator": (f"/api/sites/KOBO-001/threads/{T1}", {}),
}


def _get(name: str) -> dict[str, Any]:
    path, params = CASES[name]
    r = client().get(path, params={**params, "known_at": "2026-11-03T12:00:00Z"})
    assert r.status_code == 200, r.text
    return r.json()


@pytest.mark.parametrize("name", sorted(CASES))
def test_chain_body_equals_its_golden(name: str) -> None:
    body = _get(name)
    path = GOLDEN / f"{name}.json"
    if REGEN:
        GOLDEN.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(body, indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    assert body == json.loads(path.read_text(encoding="utf-8"))


def test_site_chain_shape_and_board_agreement() -> None:
    body = _get("site_kobo_2026-11-01")
    assert body["schema_version"] == "outcome-chain-1"
    assert body["site"] == {"code": "KOBO-001", "tz": BC.ADDIS, "domain": "MINIGRID"}
    assert [d["day"] for d in body["days"]] == ["2026-11-01"]
    assert body["days"][0]["grade"] == "PENDING" and body["days"][0]["measures"]["avoidable_gen_min"] == "PENDING"
    board = client().get("/api/sites/KOBO-001/chain", params={"date": "2026-11-01"}).json()
    assert [o["category"] for o in body["outcomes"]] == [o["category"] for o in board["outcomes"]]
    gen = next(t for t in body["threads"] if t["id"] == T1)
    # read on 1 Nov (the board's window day) from the events visible at the cutoff
    assert (gen["state"], gen["since"], gen["lens"]) == ("ACTION_IN_HAND", "2026-11-01", ["COST"])
    assert gen["state_label"] == "Action agreed" and gen["ref"] == {"kind": "THREAD", "site": "KOBO-001", "id": T1}
    assert [o["finding_id"] for o in gen["occurrences"]] == ["f1", "f2"]
    assert body["actions"] == [{"id": "a1", "code": "ACT-000001", "kind": "MINI_TRIAL", "thread": T1,
                                "segment_no": 1, "verification": "PENDING",
                                "ref": {"kind": "ACTION", "site": "KOBO-001", "id": "a1"}}]
    assert set(body["policy_versions"]) == {"coverage", "register", "lifecycle", "status"}


def test_the_31_oct_chain_reads_the_thread_before_its_action() -> None:
    gen = next(t for t in _get("site_kobo_2026-10-31")["threads"] if t["id"] == T1)
    assert (gen["state"], gen["since"]) == ("OPEN", "2026-10-31")


def test_known_at_hides_a_later_event() -> None:
    r = client().get(f"/api/sites/KOBO-001/threads/{T1}", params={"known_at": "2026-11-01T00:00:00Z"})
    body = r.json()["thread"]
    assert [e["seq"] for e in body["events"]] == [1] and body["state"] == "OPEN"


def test_estate_chain_counts_are_claims_and_money_is_never_summed() -> None:
    """CH-5a2b (§B14 Q7): T1 (a Finding occurrence on 31 Oct, OPEN on the window day) counts; T2 is
    opportunity-only, so it is an opportunity item, never a thread."""
    body = _get("estate_week_2026-10-25")
    counts = body["counts"]
    assert set(counts) == {"count.open_threads", "count.verified_results", "count.opportunities",
                           "count.sites_disrupted"}   # CH6b2-R Q2: additive
    assert counts["count.open_threads"]["value"] == 1 and counts["count.verified_results"]["value"] == 0
    # CH6b2-R Q2: T1 is the generator thread (primary Optimize), so no Site is disrupted; the Protect and Assure
    # cards carry the same claims as `counts` (one computation, CH6b2-R Q1).
    assert counts["count.sites_disrupted"]["value"] == 0
    assert body["cards"]["PROTECT_ASSET"]["claim"] == counts["count.sites_disrupted"]
    assert body["cards"]["ASSURE_PERFORMANCE"]["claim"] == counts["count.verified_results"]
    assert counts["count.opportunities"]["value"] == 1
    assert all(set(c) == {"key", "value", "basis", "days", "text"} for c in counts.values())
    assert len({json.dumps(c["days"], sort_keys=True) for c in counts.values()}) == 1
    # OWN-1104 R10 (replaced): `money_total` is the `money.estate_income` claim over the Sites' income earnings
    # (CH-6b1, `portfolio_parts`); here no income claim has a value, so it is NOT_KNOWN and names each such Site.
    total = body["money_total"]
    assert (total["key"], total["value"], total["basis"]) == ("money.estate_income", None, "NOT_KNOWN")
    assert total["lines"] == ["Kobo: not known yet", "Depot: not known yet"] and total["text"] == "Not known yet"
    kobo = next(s for s in body["sites"] if s["code"] == "KOBO-001")
    assert kobo["days"]["requested"] == 7 and kobo["threads"] == {"open": 0, "in_hand": 1, "verified": 0,
                                                                      "verified_actions": 0}
    # CH6b3-R3: T1's ACTION_IN_HAND is effective on 1 Nov (after the window) and known by k: the claim reads it now.
    assert [o["thread_id"] for o in kobo["opportunities"]] == [T2]
    assert set(kobo["rows"]) == {"GROW_REVENUE", "OPTIMIZE_COST", "PROTECT_ASSET", "ASSURE_PERFORMANCE"}


@pytest.mark.parametrize("path,params,status,code", [
    ("/api/sites/COLD-LAB-001/chain", {"from": "2026-09-01T00:00:00Z", "to": "2026-10-31T00:00:00Z"}, 422,
     "INVALID_WINDOW"),
    ("/api/sites/KOBO-001/chain", {"date": "2026-10-31", "known_at": "yesterday"}, 422, "INVALID_WINDOW"),
    ("/api/sites/NOPE-001/chain", {}, 404, "SITE_NOT_FOUND"),
    (f"/api/sites/COLD-LAB-001/threads/{T1}", {}, 404, "THREAD_NOT_FOUND"),
    (f"/api/sites/KOBO-001/threads/{OTHER}", {}, 404, "THREAD_NOT_FOUND"),
    ("/api/sites/KOBO-001/threads/not-a-uuid", {}, 404, "THREAD_NOT_FOUND"),
])
def test_refusals(path, params, status, code) -> None:
    r = client().get(path, params=params)
    assert r.status_code == status, r.text
    assert r.json()["detail"]["code"] == code


@pytest.mark.parametrize("name", sorted(CASES))
def test_each_route_reads_each_key_at_most_once(name: str, monkeypatch) -> None:
    seen: list = []
    real = read_scope.scope

    @contextmanager
    def spy(route):
        with real(route) as sc:
            seen.append(sc)
            yield sc

    monkeypatch.setattr(read_scope, "scope", spy)
    _get(name)
    assert seen and any(n.startswith("chain.") for n in seen[0].names()), seen
    assert seen[0].max_per_key() == 1, seen[0].repeated()


LIFE = {  # cold/EV threads whose lifecycle is known after the evidence cutoff but by k (CH6b2-R3, M-R2-1)
    BC.COLD.site_id: ("cold-1", "COLD_START_FAILURE", BC.at(31, 2), BC.at(31, 3), BC.at(30, 21), BC.at(31, 21)),
    BC.EV.site_id: ("ev-1", "EV_INTERRUPTION", BC.at(27, 10), BC.at(27, 11), BC.at(27, 8), BC.at(27, 16)),
}
THREAD_IDS = {BC.COLD.site_id: "00000000-0000-4000-8000-0000000000c9", BC.EV.site_id: "00000000-0000-4000-8000-0000000000e9"}
EVIDENCE = BC.at(31, 17, 5)          # R7's evidence cutoff: before the Finding and its lifecycle are known
OPEN_KNOWN, HAND_KNOWN = BC.at(2, 9, month=11), BC.at(2, 10, month=11)   # after EVIDENCE, before k (3 Nov 12:00)


class LifecyclePort(Port):
    def site_threads(self, tenant_id, site_id, known_at):
        # MB-1-R Q1: no DOMAIN_INTENT row here, so no `outcome` / `outcome_recorded_at` keys are needed.
        if site_id not in LIFE:
            return super().site_threads(tenant_id, site_id, known_at)
        fid, mech, start, end, _, _ = LIFE[site_id]
        tid = THREAD_IDS[site_id]
        events = [_event(tid, 1, "OPEN", "OCCURRENCE", fid, start.date(), OPEN_KNOWN, OPEN_KNOWN),
                  _event(tid, 2, "ACTION_IN_HAND", "ACTION_EVENT", "e1", start.date(), HAND_KNOWN, HAND_KNOWN)]
        return {"occurrences": (_occ(tid, mech, 1, fid, None, None, start, end),),
                "events": tuple(e for e in events if known_at is None or e["cause_known_at"] <= known_at),
                "actions": ()}

    def evidence_cutoff(self, tenant_id, site_id, known_at):
        return EVIDENCE if site_id in LIFE else None


@pytest.mark.parametrize("site", [BC.COLD, BC.EV])
@pytest.mark.parametrize("known_at", ["2026-11-03T12:00:00Z", "2026-11-02T09:30:00Z"])
def test_thread_detail_shows_the_chain_rows_state_and_events(site, known_at) -> None:
    """CH6b2-R3 (M-R2-1): the cold/EV thread detail reads its lifecycle at `lifecycle_cutoff(k)`, like the Site chain
    (and so the card): an OPEN known after the evidence cutoff but by k shows the same state and events in both."""
    tid = THREAD_IDS[site.site_id]
    *_, lo, hi = LIFE[site.site_id]
    c = client(LifecyclePort())
    params = {"from": lo.isoformat().replace("+00:00", "Z"), "to": hi.isoformat().replace("+00:00", "Z"),
              "known_at": known_at}
    chain = c.get(f"/api/sites/{site.site_code}/chain", params=params)
    detail = c.get(f"/api/sites/{site.site_code}/threads/{tid}", params={"known_at": known_at})
    assert chain.status_code == 200 and detail.status_code == 200, (chain.text, detail.text)
    row = next(t for t in chain.json()["threads"] if t["id"] == tid)
    got = detail.json()["thread"]
    assert row["state"] is not None and got["state"] == row["state"]
    assert got["since"] == row["since"] and got["state_label"] == row["state_label"]
    shown = [e["state"] for e in got["events"]]
    assert shown == (["OPEN", "ACTION_IN_HAND"] if known_at.startswith("2026-11-03") else ["OPEN"])
    assert got["state"] == ("ACTION_IN_HAND" if known_at.startswith("2026-11-03") else "OPEN")
