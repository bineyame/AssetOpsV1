"""`D-action-records` v1: the stored S6-01a demonstration walkthrough and its API contract fixture.

The loader runs real accepted records end to end: S4 cases F01 and F02 (Candidate segments whose accepted
`battery_soc` evidence is 80 % against a 20 % reserve, so `reserve-trial-1` is genuinely eligible) and one authored
block at SOC exactly 30 % (headroom boundary, ineligible) go through ingestion, the S3 worker and the matcher; every
Action command then goes through the real API over PostgreSQL. Nothing is hand-inserted.

The fixture grants (`fixture_grants`) are what makes the SYSTEM demonstration commands possible: a v2 grants document
for this run's tenant and Site IDs naming exactly these Findings by manifest record ID (phase-1 review M1).

`build(runner, make_harness)` returns `(contract, rows)`: the contract maps the `D-action-records` manifest IDs
(`recommendation:1#a`, `action-overview:1#a`, `action-execution:1#a`, `action-history:1#a`, `changes:1#a`) to
named request/response cases; `rows` is every row the walkthrough wrote to the Action tables plus the Foundation and
binding set revisions the change names. `backend/tests/fixtures/s6_action_api_contract.json` is one committed run;
`test_s6_action_records_postgres.py` rebuilds it and compares it field by field after `normalise`.
"""

from __future__ import annotations

import re
import threading
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

FIXTURE_ID = "D-action-records-v1"
SCHEMA = "assetops.s6-action-api-contract"
T_ACCEPT = datetime(2026, 11, 1, 0, 0, tzinfo=timezone.utc)
EFFECTIVE = T_ACCEPT + timedelta(days=1)
SERVED_CLOCK = datetime(2026, 10, 15, 12, 0, tzinfo=timezone.utc)  # the served walkthrough ran on the real clock
INELIGIBLE_DAY = "2026-10-12"
RECORDS = {"2026-10-06": "recommendation:1#a/eligible-F01", "2026-10-08": "recommendation:1#a/no-change-F02",
           INELIGIBLE_DAY: "recommendation:1#a/ineligible-soc-at-headroom"}
NOTES = {
    "ACTION_ACCEPTANCE_CONFLICT": "409 with `action_id`: this recommendation key was already accepted (by a "
                                  "different command or idempotency key). Treat as 'already accepted' and follow "
                                  "`action_id`; it is not a failure of the existing Action.",
    "ACTION_ALREADY_APPLIED": "409 on apply with a new key after APPLIED: nothing was attempted and no FAILED event "
                              "was written; `applied_event_id` names the APPLIED event.",
    "FAILED": "A FAILED event is an attempt only. The application stays PENDING (or APPLIED); an identical retry "
              "returns the stored FAILED event (`replayed: true`); a fresh idempotency key may attempt again.",
    "selectors": "`event_id` selects the exact event and its (recorded_at, id) prefix; `recorded_at` selects every "
                 "event recorded through that server instant. Both together: 422 ACTION_SELECTOR_CONFLICT.",
    "application_basis": "`application_basis.current_foundation_revision_id` is the Foundation revision covering "
                         "`covers_instant` (the read time), not the revision covering the command's `effective_from`, "
                         "which the server checks under the Site lock. A Foundation change dated between the two, or "
                         "recorded after the apply's server time (S1 FOUNDATION_CLOCK_BEHIND, `foundation_code`), "
                         "yields 409 ACTION_FOUNDATION_STALE + FAILED: re-read and retry with a new idempotency key.",
    "prior_actions": "D-2026-10-15-s601-reopen. Every recommendation read carries `prior_actions.items`: each Action "
                     "on the canonical Finding (any revision) with its own `origin.finding_revision_id`/`revision_no`, "
                     "`origin.is_selected_revision`, `application.state`, `outcome.state`, `unresolved` and "
                     "`links.action`. Never relabel an earlier Action as the selected revision's.",
    "PRIOR_ACTION_UNRESOLVED": "State and typed 409 on accept. While an earlier reserve-trial-1 Action on this Finding "
                               "is unresolved (application pending, including failed attempts, or applied with "
                               "verification pending), a new key is held: `state` = PRIOR_ACTION_UNRESOLVED, "
                               "`proposal` null, `prior_action_block` / `unavailable` name `blocking_action_id`, "
                               "`origin_finding_revision_id` and `links`; `system_demo_capability.allowed` is false. "
                               "The current-basis result is `live_status` (AVAILABLE on the recorded clock, "
                               "FOUNDATION_BASIS_STALE on the served clock): show it as a separate live reason, never "
                               "as an Accept. An identical retry of the existing accepted key still returns its Action.",
    "volatile":"IDs, digests and action codes differ per run; tests compare after replacing UUIDs, 64-hex digests "
                "and ACT-nnnnnn codes with placeholders.",
}

UUID_RE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
SHA_RE = re.compile(r"\b[0-9a-f]{64}\b")
CODE_RE = re.compile(r"ACT-[0-9]{6,}")


def normalise(value: Any) -> Any:
    if isinstance(value, dict):
        return {normalise(k): normalise(v) for k, v in value.items()}
    if isinstance(value, list):
        return [normalise(v) for v in value]
    if isinstance(value, str):
        return CODE_RE.sub("ACT-<n>", SHA_RE.sub("<sha256>", UUID_RE.sub("<uuid>", value)))
    return value


def authored_case(day: str, soc: str) -> dict:
    blocks = [{"from": f"{day}T08:00:00Z", "to": f"{day}T08:30:00Z", "pv": "40", "dis": "20", "soc": soc,
               "stop_before": True, "stop_after": True}]
    return {"steps": [{"do": "deliver", "decided": "2026-10-30T10:00:00Z", "blocks": blocks}, {"do": "assess"},
                      {"do": "match"}]}


def fixture_grants(tenant_id: Any, site_id: Any, findings: dict[str, Any]) -> dict:
    """The v2 grants document for this run: tenant/Site IDs and the manifest records (day -> Finding ID)."""
    return {"schema": "assetops.action-demo-grants", "version": 2, "fixture_id": FIXTURE_ID,
            "grants": [{"tenant_id": str(tenant_id), "site_id": str(site_id), "site_code": "KOBO-001",
                        "commands": ["ACCEPT", "APPLY", "OBSERVE"],
                        "records": [{"manifest_id": RECORDS[day], "finding_id": str(fid)}
                                    for day, fid in sorted(findings.items()) if day in RECORDS]}]}


def _case(response, method: str, path: str, body: dict | None = None) -> dict:
    out: dict[str, Any] = {"request": {"method": method, "path": path}, "status": response.status_code,
                           "body": response.json()}
    if body is not None:
        out["request"]["body"] = body
    return out


def build(runner, cases: dict, make_harness: Callable[..., Any]) -> tuple[dict, dict]:
    from sqlalchemy import text

    for case in (cases["F01"], cases["F02"], authored_case(INELIGIBLE_DAY, "30")):
        for step in case["steps"]:
            runner.step(step)
    findings = {f["anchor_start"].date().isoformat(): f["id"] for f in runner.reload()["findings"]}
    h, denied = make_harness(fixture_grants(runner.tenant, runner.site, findings)), make_harness(None)
    f01, f02, ineligible = findings["2026-10-06"], findings["2026-10-08"], findings[INELIGIBLE_DAY]
    base = "/api/sites/KOBO-001"

    def get(client, path, **params):
        response = client.get(path, params=params or None)
        query = "" if not params else "?" + "&".join(f"{k}={v}" for k, v in params.items())
        return _case(response, "GET", path + query)

    def post(client, path, body):
        return _case(client.post(path, json=body), "POST", path, body)

    try:
        h.clock.at = denied.clock.at = T_ACCEPT
        rec: dict[str, Any] = {}
        rec["pre_accept_available"] = get(h.client, f"{base}/findings/{f01}/recommendation")
        rec["pre_accept_unavailable"] = get(h.client, f"{base}/findings/{ineligible}/recommendation")
        rec["capability_denied"] = get(denied.client, f"{base}/findings/{f01}/recommendation")
        proposal = rec["pre_accept_available"]["body"]["proposal"]
        accept_body = {"revision_id": proposal["finding_revision_id"],
                       "recommendation_key": proposal["recommendation_key"],
                       "foundation_revision_id": proposal["foundation_revision_id"],
                       "proposed_value": proposal["proposed_value"], "idempotency_key": "fixture-accept-0001"}
        accept_path = f"{base}/findings/{f01}/recommendation/accept"
        rec["accept_created"] = post(h.client, accept_path, accept_body)
        rec["accept_replayed"] = post(h.client, accept_path, accept_body)
        rec["accept_conflict_already_accepted"] = post(h.client, accept_path,
                                                       {**accept_body, "idempotency_key": "fixture-accept-0002"})
        rec["accept_capability_denied"] = post(denied.client, accept_path, accept_body)
        action_id = rec["accept_created"]["body"]["action"]["action_id"]
        # A second Action (F02, the same 20 -> 15 trial), accepted while its basis is current.
        p2 = h.client.get(f"{base}/findings/{f02}/recommendation").json()["proposal"]
        second = h.client.post(f"{base}/findings/{f02}/recommendation/accept", json={
            "revision_id": p2["finding_revision_id"], "recommendation_key": p2["recommendation_key"],
            "foundation_revision_id": p2["foundation_revision_id"], "proposed_value": p2["proposed_value"],
            "idempotency_key": "fixture-accept-f02"}).json()["action"]["action_id"]
        action_path = f"{base}/actions/{action_id}"

        overview: dict[str, Any] = {"accepted_pending": get(h.client, action_path)}
        overview["capability_denied"] = get(denied.client, action_path)
        overview["wrong_site_404"] = get(h.client, f"/api/sites/OTHER-001/actions/{action_id}")
        expected = overview["accepted_pending"]["body"]["application_basis"]["current_foundation_revision_id"]

        execution: dict[str, Any] = {}
        h.clock.at = T_ACCEPT + timedelta(minutes=30)
        execution["observed_backdated"] = post(h.client, f"{action_path}/observations", {
            "observation_code": "DEMO_REVIEW_NOTE", "occurred_at": (T_ACCEPT + timedelta(minutes=10)).isoformat(),
            "idempotency_key": "fixture-observe-0001"})
        with runner.engine.connect() as c:
            older = str(c.execute(text("SELECT id FROM foundation_revision WHERE site_id = :s AND id <> :e "
                                       "ORDER BY version LIMIT 1"), {"s": runner.site, "e": expected}).scalar_one())
        apply_path = f"{action_path}/apply"

        def apply_body(key: str, **over) -> dict:
            return {"expected_foundation_revision_id": expected, "value": "15",
                    "effective_from": EFFECTIVE.isoformat(), "idempotency_key": key, **over}

        h.clock.at = T_ACCEPT + timedelta(hours=1)
        stale_body = apply_body("fixture-apply-stale", expected_foundation_revision_id=older)
        execution["apply_stale_failed"] = post(h.client, apply_path, stale_body)
        h.clock.at += timedelta(minutes=1)
        execution["apply_stale_retry_same_key"] = post(h.client, apply_path, stale_body)
        h.clock.at += timedelta(minutes=1)
        execution["apply_invalid_value_failed"] = post(h.client, apply_path, apply_body("fixture-apply-value",
                                                                                        value="14"))
        h.clock.at += timedelta(minutes=1)
        execution["apply_backdate_failed"] = post(h.client, apply_path, apply_body(
            "fixture-apply-early", effective_from=(T_ACCEPT - timedelta(hours=1)).isoformat()))
        execution["apply_wrong_site_404"] = post(h.client, f"/api/sites/OTHER-001/actions/{action_id}/apply",
                                                 apply_body("fixture-apply-other"))
        execution["apply_capability_denied"] = post(denied.client, apply_path, apply_body("fixture-apply-deny"))
        h.clock.at += timedelta(minutes=1)
        good = apply_body("fixture-apply-0001")
        out: list = []
        gate = threading.Barrier(3)

        def go() -> None:
            gate.wait()
            out.append(h.client.post(apply_path, json=good))

        threads = [threading.Thread(target=go) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        made = next(r for r in out if r.status_code == 201)
        execution["apply_applied"] = _case(made, "POST", apply_path, good)
        execution["apply_concurrent_identical"] = {
            "request": {"method": "POST", "path": apply_path, "body": good, "concurrency": 3},
            "statuses": sorted(r.status_code for r in out),
            "distinct_event_ids": len({r.json()["event"]["id"] for r in out})}
        h.clock.at += timedelta(minutes=1)
        execution["apply_identical_retry"] = post(h.client, apply_path, good)
        execution["apply_new_key_already_applied"] = post(h.client, apply_path, apply_body("fixture-apply-0002"))
        change = execution["apply_applied"]["body"]["change"]

        # The second Action (F02, the same 20 -> 15 trial) is now a no-change on the applied Foundation.
        h.clock.at += timedelta(minutes=1)
        execution["apply_no_change_failed"] = post(h.client, f"{base}/actions/{second}/apply", apply_body(
            "fixture-apply-f02", expected_foundation_revision_id=change["new_foundation_revision_id"]))

        # The applied reserve makes the F01 basis non-current; reassessment gives F01 a newer revision.
        runner.now = max(runner.now, h.clock.at)  # the worker's clock is after the applied change was recorded
        runner.step({"do": "assess"})
        runner.step({"do": "match"})
        h.clock.at += timedelta(minutes=1)
        overview["applied_pending_newer_revision"] = get(h.client, action_path)
        rec["accepted_snapshot_live_status"] = get(h.client, f"{base}/findings/{f01}/recommendation",
                                                   revision_id=proposal["finding_revision_id"])
        # D-2026-10-15-s601-reopen: the newer F01 revision names the earlier, unresolved Action on both clocks.
        # Recorded clock: the live rule is AVAILABLE (a new key), but the prior Action holds it.
        rec["latest_revision_after_apply"] = get(h.client, f"{base}/findings/{f01}/recommendation")
        newer = rec["latest_revision_after_apply"]["body"]["live_status"]["proposal"]
        held_body = {"revision_id": newer["finding_revision_id"], "recommendation_key": newer["recommendation_key"],
                     "foundation_revision_id": newer["foundation_revision_id"],
                     "proposed_value": newer["proposed_value"], "idempotency_key": "fixture-accept-newer"}
        rec["accept_newer_revision_prior_action_unresolved"] = post(h.client, accept_path, held_body)
        recorded_clock = h.clock.at
        h.clock.at = SERVED_CLOCK  # the served walkthrough's clock: the live basis reads FOUNDATION_BASIS_STALE
        rec["latest_revision_after_apply_served_clock_stale"] = get(h.client, f"{base}/findings/{f01}/recommendation")
        h.clock.at = recorded_clock

        events = h.client.get(f"{action_path}/events").json()["events"]
        accepted_event = next(e for e in events if e["kind"] == "ACCEPTED")
        observed = next(e for e in events if e["kind"] == "OBSERVED")
        history: dict[str, Any] = {"events_latest": get(h.client, f"{action_path}/events")}
        history["events_event_id_observed"] = get(h.client, f"{action_path}/events", event_id=observed["id"])
        history["events_recorded_at_observed"] = get(h.client, f"{action_path}/events",
                                                     recorded_at=observed["recorded_at"])
        history["action_event_id_accepted"] = get(h.client, action_path, event_id=accepted_event["id"])
        history["action_recorded_at_observed"] = get(h.client, action_path, recorded_at=observed["recorded_at"])
        history["action_selector_conflict"] = get(h.client, action_path, event_id=observed["id"],
                                                  recorded_at=observed["recorded_at"])
        history["events_selector_conflict"] = get(h.client, f"{action_path}/events", event_id=observed["id"],
                                                  recorded_at=observed["recorded_at"])
        history["unknown_event_404"] = get(h.client, action_path, event_id="00000000-0000-4000-8000-000000000000")

        changes = {"change": get(h.client, f"{base}/foundation/changes/{change['change_id']}"),
                   "wrong_site_404": get(h.client, f"/api/sites/OTHER-001/foundation/changes/{change['change_id']}")}

        contract = {"schema": SCHEMA, "version": 1, "fixture_id": FIXTURE_ID, "notes": NOTES,
                    "records": RECORDS, "manifest": {
                        "recommendation:1#a": rec, "action-overview:1#a": overview,
                        "action-execution:1#a": execution, "action-history:1#a": history, "changes:1#a": changes}}
        rows = written_rows(runner, change)
        return contract, rows
    finally:
        h.close()
        denied.close()


def written_rows(runner, change: dict) -> dict[str, list[dict]]:
    """Every Action-table row plus the Foundation and binding set revisions the change names."""
    from sqlalchemy import text

    out: dict[str, list[dict]] = {}
    with runner.engine.connect() as c:
        for table, order in (("action", "action_no"), ("action_basis_assessment", "segment_start"),
                             ("action_basis_evidence", "segment_start, evidence_id"),
                             ("action_event", "recorded_at, id"), ("action_policy_change", "recorded_at"),
                             ("action_policy_change_binding", "relation, binding_set_revision_id")):
            out[table] = [dict(r._mapping) for r in c.execute(text(f"SELECT * FROM {table} ORDER BY {order}"))]
        ids = [change[k] for k in ("expected_foundation_revision_id", "split_foundation_revision_id",
                                   "new_foundation_revision_id") if change[k]]
        out["foundation_revision"] = [dict(r._mapping) for r in c.execute(text(
            "SELECT id, version, origin, valid_from, valid_to, recorded_at, superseded_at, derived_from_revision_id "
            "FROM foundation_revision WHERE id = ANY(CAST(:ids AS uuid[])) ORDER BY version"), {"ids": ids})]
        sets = change["binding_set_revisions"]["superseded"] + change["binding_set_revisions"]["inserted"]
        out["signal_binding_set_revision"] = [dict(r._mapping) for r in c.execute(text(
            "SELECT id, version, foundation_revision_id, valid_from, valid_to, recorded_at, superseded_at "
            "FROM signal_binding_set_revision WHERE id = ANY(CAST(:ids AS uuid[])) ORDER BY recorded_at, version"),
            {"ids": sets})]
    return out
