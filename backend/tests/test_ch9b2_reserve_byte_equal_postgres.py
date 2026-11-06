"""CH-9b2 L2 (build sheet CH-9b R1, CH9b2-R Q8): `reserve-trial-1` bodies and rows are byte-equal after 0052.

The golden `fixtures/ch9b2_reserve_trial_golden.json` was captured from the unchanged code at `1bc73ce7e` (main
`92f95effb`, migration 0051) with `CH9B2_CAPTURE=1`, before the family registry and 0052 existed. This module then
asserts, at 0052 with the registry, that the S6 VERIFIED path (F01/F02, freeze, bind, evaluate) returns the same
plan, outcome, history, evidence, Action and events bodies, and that the raw `verification_plan`,
`verification_evaluation_request`, `verification_outcome` and `verification_metric` rows (their 0019 columns) are
the same. Only UUIDs, SHA-256 digests and Action codes are masked (`s6_action_records.normalise`); every clock in the
path is the test's fixed Action clock. The new 0052 columns are NULL on every reserve row.

`test_proof_can_fail` plants one changed value in a body and one in a row; the comparison must see each.
"""

from __future__ import annotations

import json
import os
from datetime import timedelta
from pathlib import Path

import pytest

from test_s4_finding_store_postgres import URL, run_case  # noqa: F401

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from s6_action_records import normalise
    from test_s1_bindings_postgres import engine, store  # noqa: F401
    from test_s6_action_store_postgres import CASES, harness, runner  # noqa: F401
    from test_s6_verification_plan_postgres import base, release_engines, verifying  # noqa: F401
    from test_s6_verification_evaluator_postgres import CLOSED, bound_plan, complete_windows, evaluate, rows

GOLDEN = Path(__file__).resolve().parent / "fixtures" / "ch9b2_reserve_trial_golden.json"

# The 0019 columns of each table (literal here, independent of the store's column constants).
TABLE_COLUMNS = {
    "verification_plan": (
        "id, tenant_id, site_id, action_id, plan_version, supersedes_plan_id, origin_finding_revision_id, "
        "applied_event_id, change_id, old_foundation_revision_id, new_foundation_revision_id, battery_asset_id, "
        "field, rule_id, effective_from, baseline_start, baseline_end, later_start, later_end, "
        "baseline_candidate_seconds, baseline_selection, baseline_evidence_ids, basis, target, guardrails, bands, "
        "coverage, later_selection_rule, plan_sha256, actor_kind, actor_id, source_channel, authorization_basis, "
        "triggering_service, triggering_fixture, idempotency_key, payload, payload_sha256, recorded_at"),
    "verification_evaluation_request": (
        "id, tenant_id, site_id, action_id, plan_id, actor_kind, actor_id, source_channel, authorization_basis, "
        "triggering_service, triggering_fixture, idempotency_key, payload, payload_sha256, recorded_at"),
    "verification_outcome": (
        "id, tenant_id, site_id, action_id, plan_id, selection_binding_id, evaluation_request_id, "
        "supersedes_outcome_id, outcome, reasons, basis, basis_sha256, details, actor_kind, actor_id, "
        "triggering_job, idempotency_key, recorded_at"),
    "verification_metric": (
        "outcome_id, tenant_id, site_id, metric_key, window_name, state, value_text, threshold_text, unit, reason, "
        "evidence_ids"),
}
ORDER = {"verification_metric": "metric_key, window_name"}
#: 0052's new columns; NULL on every reserve-trial row.
NEW_COLUMNS = {"verification_plan": ("domain_action_id", "origin_opportunity_revision_id", "applied_work_event_id"),
               "verification_evaluation_request": ("domain_action_id",),
               "verification_outcome": ("domain_action_id",)}


def _plain(value):
    return json.loads(json.dumps(value, sort_keys=True, default=str))


def capture(runner, h, monkeypatch) -> dict:
    complete_windows(monkeypatch, h)
    action_id, plan, _ = bound_plan(runner, h)
    h.clock.at = CLOSED + timedelta(hours=1)
    made = evaluate(h, action_id, "eval-0001")
    assert made.status_code == 201, made.text
    assert made.json()["outcome"]["outcome"] == "VERIFIED"
    bodies = {"evaluate": made.json()}
    for name, path in (("plan", "/plan"), ("outcome", "/outcome"), ("history", "/history"),
                       ("evidence", "/evidence")):
        got = h.client.get(f"{base(action_id)}{path}")
        assert got.status_code == 200, got.text
        bodies[name] = got.json()
    bodies["action"] = h.client.get(f"/api/sites/KOBO-001/actions/{action_id}").json()
    bodies["events"] = h.client.get(f"/api/sites/KOBO-001/actions/{action_id}/events").json()
    tables = {}
    for table, columns in TABLE_COLUMNS.items():
        got = rows(runner, f"SELECT {columns} FROM {table} ORDER BY {ORDER.get(table, 'recorded_at, id')}")
        tables[table] = [dict(r._mapping) for r in got]
    return normalise(_plain({"bodies": bodies, "rows": tables}))


def differences(got: dict, want: dict) -> list[str]:
    out = []
    for group in ("bodies", "rows"):
        for key in sorted(set(got[group]) | set(want[group])):
            if got[group].get(key) != want[group].get(key):
                out.append(f"{group}.{key}")
    return out


def _null_new_columns(runner) -> None:
    for table, columns in NEW_COLUMNS.items():
        got = rows(runner, f"SELECT count(*) FROM {table} WHERE " + " OR ".join(f"{c} IS NOT NULL" for c in columns))
        assert got[0][0] == 0, table


def test_reserve_trial_bodies_and_rows_are_byte_equal(runner, monkeypatch) -> None:
    run_case(runner, CASES["F01"])
    run_case(runner, CASES["F02"])
    h = verifying(runner)
    try:
        got = capture(runner, h, monkeypatch)
        _null_new_columns(runner)
    finally:
        h.close()
    if os.environ.get("CH9B2_CAPTURE") == "1":
        GOLDEN.write_text(json.dumps(got, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        pytest.skip("golden captured")
    want = json.loads(GOLDEN.read_text(encoding="utf-8"))
    assert differences(got, want) == []
    assert got == want


def test_proof_can_fail() -> None:
    want = json.loads(GOLDEN.read_text(encoding="utf-8"))
    planted = json.loads(json.dumps(want))
    planted["bodies"]["plan"]["plan"]["domain_action_id"] = None
    assert differences(planted, want) == ["bodies.plan"]
    planted = json.loads(json.dumps(want))
    planted["rows"]["verification_outcome"][0]["outcome"] = "INCONCLUSIVE"
    assert differences(planted, want) == ["rows.verification_outcome"]
