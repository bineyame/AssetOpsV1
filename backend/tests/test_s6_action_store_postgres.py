"""S6-01a phase 1: Action store, `reserve-trial-1` recommendation/acceptance, demo OBSERVED and exact reads over
real persisted S4 Findings (PostgreSQL).

The Findings come from `s4-finding-cases-v1` steps run through ingestion, the S3 worker and the matcher (the S4
CaseRunner). F01/F02 cite Candidate segments whose accepted `battery_soc` readings are 80 % against a 20 % reserve,
so they are genuinely eligible; authored blocks at SOC exactly 30 % and 30.5 % prove the headroom boundary on
persisted evidence. Requires ASSETOPS_TEST_DATABASE_URL (backend/README-db.md).
"""

from __future__ import annotations

import threading
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest

from test_s4_finding_store_postgres import SPEC, URL, CaseRunner, _t, run_case  # noqa: F401

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from sqlalchemy import text
    from sqlalchemy.exc import DBAPIError, IntegrityError
    from test_s1_bindings_postgres import engine, store  # noqa: F401

    import pg_harness
    from assetops_backend.evidence.composition import build_source_provenance
    from assetops_backend.action_api import build_action_router
    from assetops_backend.actions.adapters.postgres_action_store import PostgresActionStore
    from assetops_backend.actions.capability import from_grants, no_capability
    from assetops_backend.actions.composition import finding_currentness
    from assetops_backend.actions.service import ActionService
    from assetops_backend.analytics.adapters.postgres_assessment_store import PostgresAssessmentStore
    from assetops_backend.analytics.adapters.postgres_finding_store import PostgresFindingStore
    from assetops_backend.analytics.dispatch_read import DispatchReadService
    from assetops_backend.analytics.finding_read import FindingReadService

CASES = {c["case_id"]: c for c in SPEC["cases"]}
ALL_COMMANDS = ["ACCEPT", "APPLY", "OBSERVE"]


def fixture_grants(runner, *, commands=ALL_COMMANDS, findings=None, site_id=None) -> dict:
    """A v2 grants document scoped to this run's tenant/Site IDs, naming its Findings as fixture records
    (phase-1 review M1). `findings` defaults to every Finding persisted when the harness is built."""
    if findings is None:
        findings = [f["id"] for f in runner.reload()["findings"]]
    return {"schema": "assetops.action-demo-grants", "version": 2, "fixture_id": "D-action-records-v1",
            "grants": [{"tenant_id": str(runner.tenant), "site_id": str(site_id or runner.site),
                        "site_code": "KOBO-001", "commands": list(commands),
                        "records": [{"manifest_id": f"test-record:{i}", "finding_id": str(f)}
                                    for i, f in enumerate(findings)]}]}
T_ACCEPT = datetime(2026, 11, 1, 0, 0, tzinfo=timezone.utc)
ACTION_TABLES = ("action", "action_basis_assessment", "action_basis_evidence", "action_event",
                 "action_policy_change", "action_policy_change_binding")


class Clock:
    def __init__(self, at: datetime) -> None:
        self.at = at

    def __call__(self) -> datetime:
        return self.at


class Harness:
    def __init__(self, runner, *, capability=None, access=None, command_access=None, gate_open=True) -> None:
        self.runner, self.clock = runner, Clock(T_ACCEPT)
        self.store = PostgresActionStore(URL)
        # S4-05b phase 2: the production stored resolver, read for the exact pinned origin FindingRevision.
        reads = FindingReadService(PostgresFindingStore(URL), DispatchReadService(PostgresAssessmentStore(URL)),
                                   build_source_provenance(URL))
        self.service = ActionService(self.store, finding_currentness(reads),
                                     from_grants(fixture_grants(runner)) if capability is None else capability,
                                     self.clock, source=reads.source_provenance)
        self.wrong_site = uuid4()
        scope = {"KOBO-001": ("KOBO-001", runner.tenant, runner.site),
                 "OTHER-001": ("OTHER-001", runner.tenant, self.wrong_site)}
        kwargs = {}
        if access is not None:
            kwargs["access"] = access
        if command_access is not None:
            kwargs["command_access"] = command_access
        app = FastAPI()
        app.include_router(build_action_router(self.service, scope.get, gate=lambda c, t, s: (
            gate_open, "test gate"), **kwargs))
        self.client = TestClient(app)

    def findings(self) -> dict[str, UUID]:
        """Anchor day -> Finding id."""
        rows = self.runner.reload()
        return {f["anchor_start"].date().isoformat(): f["id"] for f in rows["findings"]}

    def recommendation(self, finding_id, site="KOBO-001", **params):
        return self.client.get(f"/api/sites/{site}/findings/{finding_id}/recommendation", params=params)

    def accept(self, finding_id, proposal, site="KOBO-001", **over):
        body = {"revision_id": proposal["finding_revision_id"], "recommendation_key": proposal["recommendation_key"],
                "foundation_revision_id": proposal["foundation_revision_id"],
                "proposed_value": proposal["proposed_value"], "idempotency_key": "accept-0001", **over}
        return self.client.post(f"/api/sites/{site}/findings/{finding_id}/recommendation/accept", json=body)

    def observe(self, action_id, when: datetime, key: str, site="KOBO-001", **over):
        body = {"observation_code": "DEMO_REVIEW_NOTE", "occurred_at": when.isoformat(),
                "idempotency_key": key, **over}
        return self.client.post(f"/api/sites/{site}/actions/{action_id}/observations", json=body)

    def counts(self) -> dict[str, int]:
        with self.runner.engine.connect() as c:
            return {t: c.execute(text(f"SELECT count(*) FROM {t}")).scalar_one() for t in ACTION_TABLES}

    def close(self) -> None:
        pg_harness.dispose(self.store)


@pytest.fixture()
def runner(store, engine):  # noqa: F811
    owned = CaseRunner(store, engine)
    yield owned
    pg_harness.dispose(owned.findings)


def harness(runner, **kwargs) -> "Harness":
    return Harness(runner, **kwargs)


def authored_case(day: str, soc: str) -> dict:
    """F01's shape on another day with an authored SOC value (same ingestion path, same labelled spec rules)."""
    blocks = [{"from": f"{day}T08:00:00Z", "to": f"{day}T08:30:00Z", "pv": "40", "dis": "20", "soc": soc,
               "stop_before": True, "stop_after": True}]
    return {"steps": [{"do": "deliver", "decided": "2026-10-30T10:00:00Z", "blocks": blocks}, {"do": "assess"},
                      {"do": "match"}]}


def run_steps(runner, case: dict) -> None:
    for step in case["steps"]:
        runner.step(step)


class TestRecommendationAcceptAndReload:
    def test_eligible_accept_replay_conflict_snapshot_and_reload(self, runner) -> None:
        run_case(runner, CASES["F01"])
        run_case(runner, CASES["F02"])
        h = harness(runner)
        try:
            ids = h.findings()
            f01, f02 = ids["2026-10-06"], ids["2026-10-08"]
            before = h.recommendation(f01)
            assert before.status_code == 200, before.text
            rec = before.json()
            assert rec["state"] == "AVAILABLE" and rec["basis"] == "SERVED_FROM_PERSISTED_INPUTS"
            assert rec["accepted"] == [] and rec["live_status"] is None
            assert rec["system_demo_capability"]["allowed"] is True
            assert rec["system_demo_capability"]["fixture_id"] == "D-action-records-v1"
            p = rec["proposal"]
            assert (p["old_value"], p["proposed_value"], p["unit"]) == ("20", "15", "%")
            # The SOC numbers come from persisted accepted evidence the cited Candidate segments cite.
            soc_ids = {r["evidence_id"] for s in p["inputs"]["segments"] for r in s["soc_evidence"]}
            with runner.engine.connect() as c:
                rows = c.execute(text("SELECT id, role, normalized_value_text, asset_id FROM accepted_evidence "
                                      "WHERE id = ANY(CAST(:ids AS uuid[]))"), {"ids": sorted(soc_ids)}).all()
                battery = c.execute(text("SELECT id FROM asset WHERE site_id = :s AND asset_code = 'battery'"),
                                    {"s": runner.site}).scalar_one()
            assert soc_ids and {r.role for r in rows} == {"battery_soc"} and {r.normalized_value_text for r in rows} == {"80"}
            assert {r.asset_id for r in rows} == {battery} and p["asset_id"] == str(battery)

            first = h.accept(f01, p)
            assert first.status_code == 201, first.text
            made = first.json()
            action_id = made["action"]["action_id"]
            assert made["replayed"] is False and made["action"]["action_code"].startswith("ACT-")
            event = made["event"]
            assert event["kind"] == "ACCEPTED" and event["recorded_at"] == T_ACCEPT.isoformat()
            assert event["occurred_at"] == event["recorded_at"]
            assert event["actor"]["kind"] == "SYSTEM" and event["actor"]["id"].startswith("service:")
            assert event["actor"]["triggering"] == {"service": "assetops-backend/action-api", "job": None,
                                                    "command": "ACCEPT", "fixture": "D-action-records-v1"}
            counted = h.counts()
            assert counted["action"] == 1 and counted["action_event"] == 1 and counted["action_basis_evidence"] >= 1

            again = h.accept(f01, p)
            assert again.status_code == 200 and again.json()["replayed"] is True
            assert again.json()["action"]["action_id"] == action_id and again.json()["event"]["id"] == event["id"]
            for over in ({"idempotency_key": "accept-0002"}, {"proposed_value": "14"}):
                clash = h.accept(f01, p, **over)
                assert clash.status_code == 409 and clash.json()["detail"]["code"] == "ACTION_ACCEPTANCE_CONFLICT"
            assert h.counts() == counted

            # S6-02a (`D-2026-10-16-s6-verification`): the hold is battery-scoped, so a distinct Finding on the same
            # battery is refused while the first trial is unresolved - no Accept capability and a typed 409.
            held_read = h.recommendation(f02).json()
            assert held_read["state"] == "PRIOR_ACTION_UNRESOLVED" and held_read["proposal"] is None
            assert held_read["unavailable"]["blocking_action_id"] == action_id
            assert held_read["system_demo_capability"]["allowed"] is False
            second = h.accept(f02, {**p, "finding_revision_id": held_read["revision_id"], "recommendation_key": "1" * 64},
                              idempotency_key="accept-f02-01")
            assert second.status_code == 409, second.text
            assert second.json()["detail"]["code"] == "PRIOR_ACTION_UNRESOLVED"
            assert second.json()["detail"]["blocking_action_id"] == action_id
            assert h.counts() == counted

            # Accepted: the snapshot is the proposal, with a separately labelled live recomputation.
            after = h.recommendation(f01).json()
            assert after["state"] == "ACCEPTED" and after["basis"] == "ACCEPTED_SNAPSHOT"
            [accepted] = after["accepted"]
            assert accepted["action_id"] == action_id and accepted["links"]["api_action"].endswith(action_id)
            assert accepted["snapshot"]["proposed_value"] == "15"
            assert accepted["snapshot"]["recommendation_key"] == p["recommendation_key"]
            assert after["live_status"]["state"] == "AVAILABLE" and after["live_status"]["already_accepted"]

            # The Site reserve changes: the accepted proposal is unchanged; only the live status goes stale.
            runner.step({"do": "reserve", "value": 25, "effective_from": "2026-10-31T00:00:00Z",
                         "decided": "2026-10-30T20:00:00Z"})
            stale = h.recommendation(f01).json()
            assert stale["state"] == "ACCEPTED" and stale["accepted"][0]["snapshot"] == accepted["snapshot"]
            assert stale["accepted"][0]["snapshot_sha256"] == accepted["snapshot_sha256"]
            assert stale["live_status"]["state"] == "UNAVAILABLE"
            # The new Foundation revision makes the S3 window basis non-current until it is reassessed.
            assert stale["live_status"]["unavailable"]["code"] == "FINDING_NOT_CURRENT"
            runner.step({"do": "assess"})
            runner.step({"do": "match"})
            reassessed = h.recommendation(f01).json()
            fresh = h.recommendation(f02).json()
            # Reassessed on the new Foundation: the latest revision's live rule sees the changed reserve.
            assert reassessed["revision_id"] != p["finding_revision_id"] and reassessed["accepted"] == []
            # D-2026-10-15-s601-reopen: the earlier, unresolved Action is the reason and is never hidden by the
            # stale basis; the stale basis stays a separate live reason. No Accept capability is offered.
            assert reassessed["state"] == "PRIOR_ACTION_UNRESOLVED" and reassessed["proposal"] is None
            assert reassessed["unavailable"]["code"] == "PRIOR_ACTION_UNRESOLVED"
            assert reassessed["unavailable"]["blocking_action_id"] == action_id
            assert reassessed["unavailable"]["origin_finding_revision_id"] == p["finding_revision_id"]
            assert reassessed["live_status"]["unavailable"]["code"] == "FOUNDATION_BASIS_STALE"
            assert reassessed["system_demo_capability"]["allowed"] is False
            assert reassessed["system_demo_capability"]["unavailable_reason"].startswith("PRIOR_ACTION_UNRESOLVED")
            [prior] = reassessed["prior_actions"]["items"]
            assert prior["action_id"] == action_id and prior["origin"]["is_selected_revision"] is False
            assert prior["origin"]["finding_revision_id"] == p["finding_revision_id"]
            assert prior["application"]["state"] == "PENDING" and prior["outcome"]["state"] == "PENDING"
            assert prior["links"]["api_action"] == f"/api/sites/KOBO-001/actions/{action_id}"
            assert fresh["unavailable"]["code"] == "PRIOR_ACTION_UNRESOLVED"
            assert fresh["live_status"]["unavailable"]["code"] == "FOUNDATION_BASIS_STALE"
            # Accepting on the newer revision is refused with the typed reason; the live reason is separate.
            counted = h.counts()
            held = h.accept(f01, {**p, "finding_revision_id": reassessed["revision_id"],
                                  "recommendation_key": "0" * 64}, idempotency_key="accept-newer-01")
            assert held.status_code == 409, held.text
            detail = held.json()["detail"]
            assert detail["code"] == "PRIOR_ACTION_UNRESOLVED" and detail["blocking_action_id"] == action_id
            assert detail["origin_finding_revision_id"] == p["finding_revision_id"]
            assert detail["links"]["api_action"].endswith(action_id)
            assert detail["live_status"]["unavailable"]["code"] == "FOUNDATION_BASIS_STALE"
            assert h.counts() == counted
            pinned = h.recommendation(f01, revision_id=p["finding_revision_id"]).json()
            assert pinned["state"] == "ACCEPTED" and pinned["accepted"][0]["snapshot"] == accepted["snapshot"]
            assert pinned["live_status"]["unavailable"]["code"] == "FINDING_REVISION_NOT_LATEST"
            # ...and an identical accept still returns the original Action and event.
            replay = h.accept(f01, p)
            assert replay.status_code == 200 and replay.json()["event"]["id"] == event["id"]

            read = h.client.get(f"/api/sites/KOBO-001/actions/{action_id}")
            assert read.status_code == 200, read.text
            body = read.json()
            assert body["origin"]["finding_id"] == str(f01)
            assert body["origin"]["finding_revision_id"] == p["finding_revision_id"]
            assert body["latest_finding_revision"]["id"] == reassessed["revision_id"]
            assert body["latest_finding_revision"]["is_origin"] is False
            assert body["newer_revision_notice"]["latest_revision_id"] == reassessed["revision_id"]
            assert body["state"]["application"] == "PENDING" and body["state"]["outcome"]["state"] == "PENDING"
            assert body["accepted_recommendation"]["old_value"] == "20"
            assert body["accepted_recommendation"]["proposed_value"] == "15"
            assert {e["evidence_id"] for e in body["basis"]["evidence"]} == soc_ids
            assert body["basis"]["foundation_revision_id"] == p["foundation_revision_id"]
            assert body["system_demo_capability"]["apply"]["allowed"] is True
            assert body["selection"]["kind"] == "LATEST" and body["selection"]["cutoff_event_id"] == event["id"]
            assert body["links"]["origin_finding"].endswith(f"?revision_id={p['finding_revision_id']}")
            assert body["change"] is None
        finally:
            h.close()

    def test_concurrent_identical_accepts_make_one_action(self, runner) -> None:
        run_case(runner, CASES["F01"])
        h = harness(runner)
        try:
            f01 = h.findings()["2026-10-06"]
            p = h.recommendation(f01).json()["proposal"]
            out: list = []
            gate = threading.Barrier(4)

            def go() -> None:
                gate.wait()
                out.append(h.accept(f01, p))

            threads = [threading.Thread(target=go) for _ in range(4)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            assert sorted(r.status_code for r in out) == [200, 200, 200, 201]
            assert len({r.json()["action"]["action_id"] for r in out}) == 1
            assert h.counts()["action"] == 1 and h.counts()["action_event"] == 1
        finally:
            h.close()


class TestRuleOnPersistedEvidence:
    def test_soc_exactly_reserve_plus_ten_versus_just_above(self, runner) -> None:
        run_steps(runner, authored_case("2026-10-06", "30"))
        run_steps(runner, authored_case("2026-10-08", "30.5"))
        h = harness(runner)
        try:
            ids = h.findings()
            at = h.recommendation(ids["2026-10-06"]).json()
            assert at["state"] == "UNAVAILABLE" and at["unavailable"]["code"] == "SOC_NOT_ABOVE_HEADROOM"
            assert at["proposal"] is None and at["segments"][0]["selected_soc"]["value"] == "30"
            above = h.recommendation(ids["2026-10-08"]).json()
            assert above["state"] == "AVAILABLE" and above["proposal"]["proposed_value"] == "15"
            # An unavailable recommendation cannot be accepted; nothing is written.
            refused = h.accept(ids["2026-10-06"], {**above["proposal"],
                                                   "finding_revision_id": at["revision_id"]})
            assert refused.status_code == 422 and refused.json()["detail"]["code"] == "RECOMMENDATION_UNAVAILABLE"
            assert refused.json()["detail"]["unavailable"]["code"] == "SOC_NOT_ABOVE_HEADROOM"
            assert h.counts()["action"] == 0
        finally:
            h.close()

    def test_newer_revision_keeps_the_origin_pinned_and_closed_source_is_unavailable(self, runner) -> None:
        steps = CASES["F04"]["steps"]
        run_steps(runner, {"steps": steps[:3]})
        h = harness(runner)
        closed = harness(runner, gate_open=False)
        try:
            [finding] = h.findings().values()
            p = h.recommendation(finding).json()["proposal"]
            action_id = h.accept(finding, p).json()["action"]["action_id"]
            run_steps(runner, {"steps": steps[3:]})  # late acceptance: revision 2 (SUPPORT_CHANGED)
            revs = sorted((r for r in runner.reload()["revisions"] if r["finding_id"] == finding),
                          key=lambda r: r["revision_no"])
            assert [r["revision_no"] for r in revs] == [1, 2]
            assert str(revs[0]["id"]) == p["finding_revision_id"]
            old = h.recommendation(finding, revision_id=str(revs[0]["id"])).json()
            assert old["state"] == "ACCEPTED" and old["accepted"][0]["action_id"] == action_id
            assert old["live_status"]["unavailable"]["code"] == "FINDING_REVISION_NOT_LATEST"
            latest = h.recommendation(finding).json()
            # The live rule offers a new key on revision 2, but the unresolved Action on revision 1 holds it.
            assert latest["revision_id"] == str(revs[1]["id"]) and latest["state"] == "PRIOR_ACTION_UNRESOLVED"
            assert latest["live_status"]["state"] == "AVAILABLE" and latest["proposal"] is None
            newer = latest["live_status"]["proposal"]
            assert newer["recommendation_key"] != p["recommendation_key"]
            assert latest["prior_action_block"]["blocking_action_id"] == action_id
            assert latest["prior_action_block"]["origin_revision_no"] == 1
            assert latest["system_demo_capability"]["allowed"] is False
            [prior] = latest["prior_actions"]["items"]
            assert prior["origin"] == {"finding_id": str(finding), "finding_revision_id": str(revs[0]["id"]),
                                       "revision_no": 1, "is_selected_revision": False}
            assert old["prior_actions"]["items"][0]["origin"]["is_selected_revision"] is True
            assert old["prior_action_block"] is None and old["system_demo_capability"]["allowed"] is True
            before = h.counts()
            held = h.accept(finding, newer, idempotency_key="accept-rev2")
            assert held.status_code == 409 and held.json()["detail"]["code"] == "PRIOR_ACTION_UNRESOLVED"
            assert held.json()["detail"]["origin_finding_revision_id"] == str(revs[0]["id"])
            assert held.json()["detail"]["live_status"]["state"] == "AVAILABLE"
            assert h.counts() == before
            # An identical retry of the existing accepted key still returns its Action.
            again = h.accept(finding, p)
            assert again.status_code == 200 and again.json()["action"]["action_id"] == action_id
            body = h.client.get(f"/api/sites/KOBO-001/actions/{action_id}").json()
            assert body["origin"]["finding_revision_id"] == str(revs[0]["id"])
            assert body["latest_finding_revision"]["id"] == str(revs[1]["id"])
            assert body["latest_finding_revision"]["is_origin"] is False
            assert body["newer_revision_notice"]["latest_revision_id"] == str(revs[1]["id"])
            # S4-05b phase 2 (D-2026-10-16-s405b-label item 3): source state for the exact pinned origin revision
            # from the stored resolver, never the latest head or the date; these cases are unpublished -> UNKNOWN.
            assert "demonstration" not in body and "demonstration" not in latest
            assert body["source_provenance"]["finding_revision_id"] == str(revs[0]["id"])
            assert body["source_provenance"]["state"] == "UNKNOWN"
            assert body["source_provenance"]["reasons"][0]["code"] == "NO_POSITIVE_BINDING"
            assert latest["source_provenance"]["finding_revision_id"] == str(revs[1]["id"])
            assert old["source_provenance"]["finding_revision_id"] == str(revs[0]["id"])
            shut = closed.recommendation(finding).json()
            assert shut["source_open"] is False and shut["unavailable"]["code"] == "PRIOR_ACTION_UNRESOLVED"
            assert shut["live_status"]["unavailable"]["code"] == "FINDING_NOT_CURRENT"
        finally:
            h.close()
            closed.close()


class TestPriorActionAtomicRecheck:
    def test_simultaneous_accepts_on_two_revisions_make_one_unresolved_trial(self, runner) -> None:
        """D-2026-10-15-s601-reopen: the prior-Action guard runs again under the store's trial lock. Both accepts
        pass the service's unlocked pre-check (no Action exists yet); each guard then holds its transaction open,
        so without the lock both would insert."""
        import time

        from assetops_backend.actions.ports import ActionRefused
        from assetops_backend.actions.reserve_trial import sha

        steps = CASES["F04"]["steps"]
        run_steps(runner, {"steps": steps[:3]})
        h = harness(runner)
        try:
            [finding] = h.findings().values()
            p1 = h.recommendation(finding).json()["proposal"]
            run_steps(runner, {"steps": steps[3:]})
            p2 = h.recommendation(finding).json()["proposal"]
            assert p1["finding_revision_id"] != p2["finding_revision_id"]
            assert p1["recommendation_key"] != p2["recommendation_key"]
            out: list = []
            gate = threading.Barrier(2)

            def go(proposal: dict, key: str) -> None:
                strict = ActionService._prior_guard("KOBO-001", UUID(proposal["finding_revision_id"]),
                                                    type("E", (), {"available": True,
                                                                   "unavailable": lambda self: None})())

                def slow(prior: list) -> None:
                    strict(prior)
                    time.sleep(1.0)  # hold the transaction after the check, before the insert

                payload = {"command": "ACCEPT", "idempotency_key": key, "revision": proposal["finding_revision_id"]}
                gate.wait()
                try:
                    _a, _e, replayed = h.store.accept(runner.tenant, runner.site, proposal, payload_sha256=sha(payload),
                                                      payload=payload, idempotency_key=key, fixture_id="race",
                                                      recorded_at=T_ACCEPT, guard=slow)
                    out.append(("created", replayed))
                except ActionRefused as refused:
                    out.append((refused.code, refused.extra.get("blocking_action_id")))
                except Exception as error:  # noqa: BLE001 - surfaced by the assertion below
                    out.append(("error", repr(error)))

            threads = [threading.Thread(target=go, args=(p, k)) for p, k in ((p1, "race-accept-0001"), (p2, "race-accept-0002"))]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            assert sorted(o[0] for o in out) == ["PRIOR_ACTION_UNRESOLVED", "created"], out
            assert h.counts()["action"] == 1 and h.counts()["action_event"] == 1
        finally:
            h.close()


class TestRefusalsWriteNothing:
    def test_auth_scope_capability_404_and_invalid_bodies(self, runner) -> None:
        run_case(runner, CASES["F01"])
        h = harness(runner)
        anon = harness(runner, command_access=lambda r, c: 401)
        scoped = harness(runner, command_access=lambda r, c: 403)
        denied = harness(runner, capability=no_capability)
        partial = harness(runner, capability=from_grants(fixture_grants(runner, commands=["OBSERVE"])))
        try:
            f01 = h.findings()["2026-10-06"]
            p = h.recommendation(f01).json()["proposal"]
            assert anon.accept(f01, p).status_code == 401
            assert scoped.accept(f01, p).json()["detail"]["code"] == "SITE_SCOPE_FORBIDDEN"
            refused = denied.accept(f01, p)
            assert refused.status_code == 403 and refused.json()["detail"]["code"] == "SYSTEM_DEMO_CAPABILITY_DENIED"
            assert partial.accept(f01, p).status_code == 403
            view = denied.recommendation(f01).json()["system_demo_capability"]
            assert view["allowed"] is False and view["unavailable_reason"]
            # Wrong-Site and unknown IDs are 404.
            assert h.accept(f01, p, site="OTHER-001").status_code == 404
            assert h.recommendation(f01, site="OTHER-001").status_code == 404
            assert h.accept(uuid4(), p).status_code == 404
            assert h.accept(f01, p, revision_id=str(uuid4())).status_code == 404
            assert h.recommendation(f01, revision_id=str(uuid4())).status_code == 404
            assert h.client.get(f"/api/sites/OTHER-001/actions/{uuid4()}").status_code == 404
            assert h.client.get("/api/sites/NOPE-1/actions/" + str(uuid4())).status_code == 404
            # Malformed, mismatched or self-authorizing commands are typed 422.
            for over, code in (({"proposed_value": "10"}, "RECOMMENDATION_MISMATCH"),
                               ({"recommendation_key": "0" * 64}, "RECOMMENDATION_MISMATCH"),
                               ({"foundation_revision_id": str(uuid4())}, "RECOMMENDATION_MISMATCH"),
                               ({"proposed_value": "ten"}, "COMMAND_INVALID"),
                               ({"idempotency_key": "short"}, "COMMAND_INVALID"),
                               ({"extra": 1}, "COMMAND_INVALID"),
                               ({"actor_id": "alice"}, "CLIENT_AUTHORITY_FORBIDDEN"),
                               ({"system_demo_capability": True}, "CLIENT_AUTHORITY_FORBIDDEN")):
                got = h.accept(f01, p, **over)
                assert got.status_code == 422 and got.json()["detail"]["code"] == code, (over, got.text)
            assert set(h.counts().values()) == {0}
        finally:
            for x in (h, anon, scoped, denied, partial):
                x.close()


class TestObservedAndExactHistory:
    def test_backdated_observation_bounds_retry_and_server_order(self, runner) -> None:
        run_case(runner, CASES["F01"])
        h = harness(runner)
        try:
            f01 = h.findings()["2026-10-06"]
            p = h.recommendation(f01).json()["proposal"]
            action_id = h.accept(f01, p).json()["action"]["action_id"]
            base = f"/api/sites/KOBO-001/actions/{action_id}"
            h.clock.at = T_ACCEPT + timedelta(hours=2)
            # Bounds first: nothing is written for a refused observation.
            for when, code in ((T_ACCEPT - timedelta(seconds=1), "OBSERVATION_TIME_OUT_OF_BOUNDS"),
                               (T_ACCEPT + timedelta(hours=3), "OBSERVATION_IN_FUTURE")):
                got = h.observe(action_id, when, f"bad-{code}")
                assert got.status_code == 422 and got.json()["detail"]["code"] == code
            assert h.observe(action_id, T_ACCEPT, "bad-code-01", observation_code="NOTE").json()["detail"][
                "code"] == "OBSERVATION_CODE_INVALID"
            assert h.observe(action_id, T_ACCEPT, "naive-0001", occurred_at="2026-11-01T00:00:00").status_code == 422
            assert h.observe(uuid4(), T_ACCEPT, "unknown-01").status_code == 404
            assert h.observe(action_id, T_ACCEPT, "wrongsite1", site="OTHER-001").status_code == 404
            assert harness(runner, capability=no_capability).observe(action_id, T_ACCEPT, "denied-01").status_code == 403
            assert h.counts()["action_event"] == 1

            # A valid backdated OBSERVED: occurred one hour after acceptance, recorded two hours after.
            occurred = T_ACCEPT + timedelta(hours=1)
            first = h.observe(action_id, occurred, "observe-0001")
            assert first.status_code == 201, first.text
            observed = first.json()["event"]
            assert observed["kind"] == "OBSERVED" and observed["observation_code"] == "DEMO_REVIEW_NOTE"
            assert observed["occurred_at"] == occurred.isoformat()
            assert observed["recorded_at"] == h.clock.at.isoformat() and observed["occurred_before_recorded"]
            again = h.observe(action_id, occurred, "observe-0001")
            assert again.status_code == 200 and again.json()["event"]["id"] == observed["id"]
            clash = h.observe(action_id, occurred + timedelta(minutes=1), "observe-0001")
            assert clash.status_code == 409 and clash.json()["detail"]["code"] == "IDEMPOTENCY_KEY_CONFLICT"
            # A second note recorded at the same server instant (a tie), with an even earlier occurred_at.
            tied = h.observe(action_id, T_ACCEPT + timedelta(minutes=5), "observe-0002").json()["event"]
            assert tied["recorded_at"] == observed["recorded_at"]
            # Thirty days: an occurred_at 30 days + 1 s before server time is refused.
            h.clock.at = T_ACCEPT + timedelta(days=30, hours=1, seconds=1)
            far = h.observe(action_id, occurred, "observe-0003")
            assert far.status_code == 422 and far.json()["detail"]["code"] == "OBSERVATION_TIME_OUT_OF_BOUNDS"

            full = h.client.get(f"{base}/events").json()
            kinds = [e["kind"] for e in full["events"]]
            assert kinds == ["ACCEPTED", "OBSERVED", "OBSERVED"]
            ties = sorted([observed["id"], tied["id"]])
            assert [e["id"] for e in full["events"][1:]] == ties  # (recorded_at, id), not occurred_at
            assert full["state"]["application"] == "PENDING"  # state-neutral

            # Exact event: the ordered prefix through that event, even though its occurred_at is earlier.
            exact = h.client.get(f"{base}/events", params={"event_id": ties[0]}).json()
            assert [e["id"] for e in exact["events"]] == [full["events"][0]["id"], ties[0]]
            assert exact["selection"]["kind"] == "EVENT_ID" and exact["links"]["api_events"].endswith(
                f"?event_id={ties[0]}")
            # Recorded cutoff: every event recorded through the instant, both ties included.
            cut = h.client.get(f"{base}/events", params={"recorded_at": observed["recorded_at"]}).json()
            assert [e["id"] for e in cut["events"]] == [e["id"] for e in full["events"]]
            early = h.client.get(base, params={"recorded_at": (T_ACCEPT + timedelta(hours=1, minutes=59)).isoformat()})
            assert early.json()["selection"]["event_count"] == 1 and early.json()["state"]["application"] == "PENDING"
            assert "recorded_at=" in early.json()["links"]["api_events"]
            before = h.client.get(base, params={"recorded_at": (T_ACCEPT - timedelta(seconds=1)).isoformat()}).json()
            assert before["state"]["application"] == "NONE_AT_CUTOFF" and before["last_event"] is None
            # Both selectors: typed conflict on both reads, no silent precedence.
            both = {"event_id": ties[0], "recorded_at": observed["recorded_at"]}
            for path in (base, f"{base}/events"):
                got = h.client.get(path, params=both)
                assert got.status_code == 422 and got.json()["detail"]["code"] == "ACTION_SELECTOR_CONFLICT"
            assert h.client.get(base, params={"event_id": str(uuid4())}).status_code == 404
            assert h.client.get(base, params={"recorded_at": "yesterday"}).json()["detail"]["code"] == (
                "ACTION_SELECTOR_INVALID")
        finally:
            h.close()


class TestSchema:
    def test_rows_are_append_only_and_constrained(self, runner) -> None:
        run_case(runner, CASES["F01"])
        h = harness(runner)
        try:
            f01 = h.findings()["2026-10-06"]
            action_id = h.accept(f01, h.recommendation(f01).json()["proposal"]).json()["action"]["action_id"]
            for sql in ("UPDATE action SET proposed_value = 10 WHERE id = :a",
                        "DELETE FROM action_event WHERE action_id = :a",
                        "UPDATE action_event SET recorded_at = now() WHERE action_id = :a"):
                with pytest.raises(DBAPIError):
                    with runner.engine.begin() as c:
                        c.execute(text(sql), {"a": action_id})
            with runner.engine.connect() as c:
                row = c.execute(text("SELECT * FROM action WHERE id = :a"), {"a": action_id}).mappings().one()
            # A second ACCEPTED for the Action, a duplicate idempotency key and a non-trial value are refused.
            for sql in (
                "INSERT INTO action_event (id, tenant_id, site_id, action_id, kind, occurred_at, recorded_at, "
                "actor_kind, actor_id, source_channel, authorization_basis, triggering_service, triggering_command, "
                "triggering_fixture, idempotency_key, payload, payload_sha256) SELECT gen_random_uuid(), tenant_id, "
                "site_id, action_id, 'ACCEPTED', occurred_at, recorded_at, actor_kind, actor_id, source_channel, "
                "authorization_basis, triggering_service, triggering_command, triggering_fixture, 'another-key', "
                "payload, payload_sha256 FROM action_event WHERE action_id = :a",
                "INSERT INTO action_event (id, tenant_id, site_id, action_id, kind, occurred_at, recorded_at, "
                "actor_kind, actor_id, source_channel, authorization_basis, triggering_service, triggering_command, "
                "triggering_fixture, idempotency_key, payload, payload_sha256, observation_code) SELECT "
                "gen_random_uuid(), tenant_id, site_id, action_id, 'OBSERVED', occurred_at - interval '31 days', "
                "recorded_at, actor_kind, actor_id, source_channel, authorization_basis, triggering_service, "
                "'OBSERVE', triggering_fixture, 'observe-far', payload, payload_sha256, 'DEMO_REVIEW_NOTE' "
                "FROM action_event WHERE action_id = :a",
                "INSERT INTO action_event (id, tenant_id, site_id, action_id, kind, occurred_at, recorded_at, "
                "actor_kind, actor_id, source_channel, authorization_basis, triggering_service, triggering_command, "
                "triggering_fixture, idempotency_key, payload, payload_sha256) SELECT gen_random_uuid(), tenant_id, "
                "site_id, action_id, 'ACCEPTED', occurred_at - interval '1 hour', recorded_at, actor_kind, actor_id, "
                "source_channel, authorization_basis, triggering_service, triggering_command, triggering_fixture, "
                "'backdated-accept', payload, payload_sha256 FROM action_event WHERE action_id = :a",
            ):
                with pytest.raises(IntegrityError):
                    with runner.engine.begin() as c:
                        c.execute(text(sql), {"a": action_id})
            with pytest.raises(IntegrityError):
                with runner.engine.begin() as c:
                    c.execute(text(
                        "INSERT INTO action (id, tenant_id, site_id, action_no, action_code, recommendation_key, "
                        "acceptance_key, acceptance_payload_sha256, origin_finding_id, origin_finding_revision_id, "
                        "primary_assessment_revision_id, foundation_revision_id, asset_id, rule_id, rule_version, "
                        "field, unit, old_value, proposed_value, limitation_code, limitation_text, input_sha256, "
                        "snapshot, snapshot_sha256, created_at) VALUES (gen_random_uuid(), :t, :s, 999999, "
                        ":code, :k, :k, :k, :f, :r, :ar, :fo, :asset, 'reserve-trial-1', 1, "
                        "'reserve-state-of-charge', '%', 20, 15, 'X', 'x', :k, '{}', :k, now())"),
                        {"t": row["tenant_id"], "s": row["site_id"], "code": row["action_code"], "k": "f" * 64,
                         "f": row["origin_finding_id"], "r": row["origin_finding_revision_id"],
                         "ar": row["primary_assessment_revision_id"], "fo": row["foundation_revision_id"],
                         "asset": row["asset_id"]})  # duplicate tenant action_code
        finally:
            h.close()


def test_action_source_is_unverified_when_the_resolver_is_unwired_or_fails() -> None:
    """S4-05b phase 2: no resolver, or a failing one, gives Source unverified (UNKNOWN), never a positive class."""
    from assetops_backend.actions.service import ActionService

    t, s, r = uuid4(), uuid4(), uuid4()
    unwired = ActionService(None, lambda *a: None).source_provenance(t, s, r)
    assert (unwired["state"], unwired["reasons"][0]["code"], unwired["finding_revision_id"]) == (
        "UNKNOWN", "PROVENANCE_NOT_WIRED", str(r))

    def broken(*a):
        raise RuntimeError("down")

    failed = ActionService(None, lambda *a: None, source=broken).source_provenance(t, s, r)
    assert (failed["state"], failed["reasons"][0]["code"]) == ("UNKNOWN", "PROVENANCE_UNREADABLE")
    seen = []
    exact = ActionService(None, lambda *a: None, source=lambda *a: seen.append(a) or {"state": "AUTHORED_DEMONSTRATION"})
    assert exact.source_provenance(t, s, r)["state"] == "AUTHORED_DEMONSTRATION" and seen == [(t, s, r)]
