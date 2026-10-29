"""S6-01a: the `D-action-records` walkthrough over PostgreSQL and its committed API contract fixture.

Rebuilds `D-action-records` (`s6_action_records.build`) on a fresh database through the real API, checks the
domain facts and every written row, then compares the responses field by field with the committed
`backend/tests/fixtures/s6_action_api_contract.json` after normalising per-run IDs, digests and action codes.
S6-01b's frontend tests load that same file, so a drift in any field fails here first.

Regenerate the fixture (one run, then commit it):   ASSETOPS_WRITE_S6_CONTRACT=1 pytest <this file>
Dump every written row for a walkthrough review:    ASSETOPS_S6_WALKTHROUGH_OUT=<path.json> pytest <this file>
Requires ASSETOPS_TEST_DATABASE_URL (backend/README-db.md).
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from s6_action_records import EFFECTIVE, FIXTURE_ID, build, normalise
from test_s4_finding_store_postgres import URL, CaseRunner  # noqa: F401
from test_s6_action_store_postgres import CASES, runner  # noqa: F401

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from test_s1_bindings_postgres import engine, store  # noqa: F401
    from test_s6_action_apply_postgres import Registry
    from test_s6_action_store_postgres import Harness

    from assetops_backend.actions.capability import from_grants, no_capability
    from assetops_backend.actions.composition import foundation_publish

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "s6_action_api_contract.json"


def make_harness(runner):
    def make(document):
        h = Harness(runner, capability=no_capability if document is None else from_grants(document))
        h.service.publish = foundation_publish(Registry(runner))
        return h
    return make


def test_d_action_records_walkthrough_and_contract(runner) -> None:
    contract, rows = build(runner, CASES, make_harness(runner))
    m = contract["manifest"]
    rec, overview, execution = m["recommendation:1#a"], m["action-overview:1#a"], m["action-execution:1#a"]
    history, changes = m["action-history:1#a"], m["changes:1#a"]

    # Recommendation: eligible and ineligible served from persisted inputs; capability scoped to the record.
    assert rec["pre_accept_available"]["body"]["state"] == "AVAILABLE"
    assert rec["pre_accept_available"]["body"]["system_demo_capability"]["manifest_id"] == \
        "recommendation:1#a/eligible-F01"
    assert rec["pre_accept_unavailable"]["body"]["unavailable"]["code"] == "SOC_NOT_ABOVE_HEADROOM"
    # W3-01 Run 3 q3: the recommendation keeps its pinned origin Finding's W1 block (not an Action set; the estate
    # Action set is W3 commit 2). The production Finding composition adds the public keys to that same block.
    from assetops_backend.analytics.composition import build_finding_read_service

    origin_body = rec["pre_accept_available"]["body"]
    origin_source = origin_body["source_provenance"]
    assert origin_source["finding_revision_id"] == origin_body["revision_id"]
    composed = build_finding_read_service(URL).source_provenance(runner.tenant, runner.site, origin_body["revision_id"])
    assert set(origin_source) - {"reasons"} <= set(composed) and composed["state"] == origin_source["state"]
    assert {"classification", "evidence_ids", "basis_sha256", "detail"} <= set(composed)
    assert composed["evidence_ids"] == sorted(origin_source["accepted_evidence_ids"])
    assert rec["capability_denied"]["body"]["system_demo_capability"]["allowed"] is False
    assert [rec[k]["status"] for k in ("accept_created", "accept_replayed", "accept_conflict_already_accepted",
                                       "accept_capability_denied")] == [201, 200, 409, 403]
    conflict = rec["accept_conflict_already_accepted"]["body"]["detail"]
    assert conflict["code"] == "ACTION_ACCEPTANCE_CONFLICT"
    action_id = rec["accept_created"]["body"]["action"]["action_id"]
    assert conflict["action_id"] == action_id
    snapshot = rec["accepted_snapshot_live_status"]["body"]
    assert snapshot["state"] == "ACCEPTED" and snapshot["accepted"][0]["action_id"] == action_id
    assert snapshot["live_status"]["state"] == "UNAVAILABLE"
    assert snapshot["money_consequence"]["label"] == "Consequence"
    assert snapshot["prior_action_block"] is None
    assert snapshot["prior_actions"]["items"][0]["origin"]["is_selected_revision"] is True

    # D-2026-10-15-s601-reopen: the newer F01 revision names the earlier Action (applied, verification pending) on
    # the recorded clock (live AVAILABLE) and on the served clock (live FOUNDATION_BASIS_STALE); no Accept.
    origin_revision = rec["pre_accept_available"]["body"]["revision_id"]
    for name, live in (("latest_revision_after_apply", None),
                       ("latest_revision_after_apply_served_clock_stale", "FOUNDATION_BASIS_STALE")):
        body = rec[name]["body"]
        assert body["revision_id"] != origin_revision, name
        assert body["state"] == "PRIOR_ACTION_UNRESOLVED" and body["proposal"] is None, name
        assert body["unavailable"]["blocking_action_id"] == action_id, name
        assert body["unavailable"]["origin_finding_revision_id"] == origin_revision, name
        assert body["system_demo_capability"]["allowed"] is False, name
        assert body["live_status"]["state"] == ("AVAILABLE" if live is None else "UNAVAILABLE"), name
        assert (body["live_status"]["unavailable"] or {}).get("code") == live, name
        [prior] = body["prior_actions"]["items"]
        assert prior["action_id"] == action_id and prior["origin"]["finding_revision_id"] == origin_revision
        assert prior["origin"]["is_selected_revision"] is False and prior["unresolved"] is True
        assert (prior["application"]["state"], prior["outcome"]["state"]) == ("APPLIED", "PENDING")
        assert prior["links"]["action"] == f"/sites/KOBO-001/actions/{action_id}"
    held = rec["accept_newer_revision_prior_action_unresolved"]
    assert held["status"] == 409 and held["body"]["detail"]["code"] == "PRIOR_ACTION_UNRESOLVED"
    assert held["body"]["detail"]["blocking_action_id"] == action_id
    assert held["body"]["detail"]["origin_finding_revision_id"] == origin_revision
    assert held["body"]["detail"]["live_status"]["state"] == "AVAILABLE"

    # Execution: OBSERVED backdated; FAILED cases; one APPLIED under concurrency; retry and already-applied.
    observed = execution["observed_backdated"]["body"]["event"]
    assert observed["kind"] == "OBSERVED" and observed["occurred_before_recorded"] is True
    expect = {"apply_stale_failed": (409, "ACTION_FOUNDATION_STALE"),
              "apply_stale_retry_same_key": (409, "ACTION_FOUNDATION_STALE"),
              "apply_invalid_value_failed": (422, "ACTION_VALUE_INVALID"),
              "apply_backdate_failed": (422, "ACTION_EFFECTIVE_TIME_INVALID"),
              "apply_new_key_already_applied": (409, "ACTION_ALREADY_APPLIED"),
              "apply_no_change_failed": (422, "ACTION_NO_CHANGE"),
              "apply_capability_denied": (403, "SYSTEM_DEMO_CAPABILITY_DENIED")}
    for name, (status, code) in expect.items():
        assert (execution[name]["status"], execution[name]["body"]["detail"]["code"]) == (status, code), name
    assert execution["apply_stale_retry_same_key"]["body"]["detail"]["event"]["id"] == \
        execution["apply_stale_failed"]["body"]["detail"]["event"]["id"]
    assert execution["apply_wrong_site_404"]["status"] == 404
    assert execution["apply_concurrent_identical"]["statuses"] == [200, 200, 201]
    assert execution["apply_concurrent_identical"]["distinct_event_ids"] == 1
    applied = execution["apply_applied"]["body"]
    change = applied["change"]
    assert execution["apply_identical_retry"]["body"]["event"]["id"] == applied["event"]["id"]
    assert change["effective_from"] == EFFECTIVE.isoformat() and (change["old_value"], change["new_value"]) == (
        "20", "15")

    # Overview: pending, then applied beside the newer FindingRevision; outcome stays pending.
    assert overview["accepted_pending"]["body"]["state"]["application"] == "PENDING"
    after = overview["applied_pending_newer_revision"]["body"]
    assert after["state"]["application"] == "APPLIED" and after["state"]["failed_attempts"] == 3
    assert after["state"]["outcome"]["state"] == "PENDING" and after["change"] == change
    assert after["newer_revision_notice"] is not None and after["latest_finding_revision"]["is_origin"] is False
    assert overview["capability_denied"]["body"]["system_demo_capability"]["apply"]["allowed"] is False
    # OUT-A3 (ruled default 1): the Action read carries the reserve-trial mechanism's categories on the mini grid.
    from assetops_backend.outcomes.outcome_map import categories_for

    assert overview["accepted_pending"]["body"]["categories"] == categories_for(
        "FINDING:GENERATOR_SUPPORT_CANDIDATE", "mini_grid")
    assert overview["wrong_site_404"]["status"] == 404

    # History: server order despite OBSERVED's earlier occurred_at; exact event; cutoff; conflict.
    kinds = [e["kind"] for e in history["events_latest"]["body"]["events"]]
    assert kinds == ["ACCEPTED", "OBSERVED", "FAILED", "FAILED", "FAILED", "APPLIED"]
    assert [e["kind"] for e in history["events_event_id_observed"]["body"]["events"]] == ["ACCEPTED", "OBSERVED"]
    assert history["events_recorded_at_observed"]["body"]["events"] == \
        history["events_event_id_observed"]["body"]["events"]
    assert history["action_event_id_accepted"]["body"]["change"] is None
    assert history["action_recorded_at_observed"]["body"]["state"]["application"] == "PENDING"
    for name in ("action_selector_conflict", "events_selector_conflict"):
        assert (history[name]["status"], history[name]["body"]["detail"]["code"]) == (422, "ACTION_SELECTOR_CONFLICT")
    assert history["unknown_event_404"]["status"] == 404
    assert changes["change"]["body"]["change"] == change and changes["wrong_site_404"]["status"] == 404

    # Every written row agrees with the API: one Action per accepted Finding, the six F01 events, one artifact.
    assert len(rows["action"]) == 2  # the held newer-revision accept wrote nothing
    assert rec["accept_created"]["body"]["action"]["action_code"] in {r["action_code"] for r in rows["action"]}
    f01_events = [r for r in rows["action_event"] if str(r["action_id"]) == action_id]
    assert [r["kind"] for r in f01_events] == kinds
    assert [str(r["id"]) for r in f01_events] == [e["id"] for e in history["events_latest"]["body"]["events"]]
    [artifact] = rows["action_policy_change"]
    assert str(artifact["id"]) == change["change_id"] and str(artifact["applied_event_id"]) == applied["event"]["id"]
    assert {str(r["id"]) for r in rows["foundation_revision"]} == {
        change["expected_foundation_revision_id"], change["split_foundation_revision_id"],
        change["new_foundation_revision_id"]}
    assert {(str(r["binding_set_revision_id"]), r["relation"]) for r in rows["action_policy_change_binding"]} == {
        *((b, "SUPERSEDED") for b in change["binding_set_revisions"]["superseded"]),
        *((b, "INSERTED") for b in change["binding_set_revisions"]["inserted"])}
    assert all(r["triggering_fixture"] == FIXTURE_ID and r["actor_kind"] == "SYSTEM" for r in rows["action_event"])

    out = os.environ.get("ASSETOPS_S6_WALKTHROUGH_OUT")
    if out:
        Path(out).write_text(json.dumps({"contract": contract, "rows": rows}, indent=1, default=str), encoding="utf-8")
    if os.environ.get("ASSETOPS_WRITE_S6_CONTRACT"):
        FIXTURE.write_text(json.dumps(contract, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    committed = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert normalise(json.loads(json.dumps(contract))) == normalise(committed)
