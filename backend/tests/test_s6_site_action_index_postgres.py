"""S6-03 Site Work Action index over PostgreSQL (`I-site-action-index-read`, `D-2026-10-16-a-action-index`).

`D-action-records` (`s6_action_records.build`, with the second Action accepted five minutes after the first) through
the real Action API, then `GET /api/sites/{site}/action-index`: two Actions at distinct creation times in
`created_at DESC` order, a later-recorded backdated observation selected by `(recorded_at, id)`, exact origin
FindingRevision and ActionEvent links, same-fence paging, a changed-fence cursor (including an event stamped before
the fence's recorded time), Site isolation, an independently counted zero window and the API refusals. Every listed
row's lifecycle equals Action detail at the same fence. The S6-02a part drives one Action to persisted RESOLVED and
then RESOLUTION_WITHDRAWN and checks the list shows each as the recorded event with detail's lifecycle.

`backend/tests/fixtures/s6_site_action_index_contract.json` holds one run's response bodies for the frontend tests
(`frontend/src/sites/__tests__/siteWorkActions.test.tsx`); each run checks its fresh bodies have the committed
field structure. Regenerate (one run, then commit):  ASSETOPS_WRITE_S603_CONTRACT=1 pytest <this file>

Requires ASSETOPS_TEST_DATABASE_URL (backend/README-db.md).
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import text

from s6_action_records import T_ACCEPT, build, fixture_grants
from test_s4_finding_store_postgres import URL, CaseRunner, run_case  # noqa: F401
from test_s6_action_store_postgres import CASES, runner  # noqa: F401

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from test_s1_bindings_postgres import engine, store  # noqa: F401
    from test_s6_action_records_postgres import make_harness
    from test_s6_verification_evaluator_postgres import (
        CLOSED,
        bound_plan,
        complete_windows,
        evaluate,
        late_reading,
        release_engines,  # noqa: F401  (autouse)
        verifying,
    )

    from assetops_backend.action_index_api import build_action_index_router
    from assetops_backend.actions.adapters.postgres_action_store import PostgresActionStore
    from assetops_backend.actions.site_index import ActionIndexService

UTC = timezone.utc
CONTRACT = Path(__file__).resolve().parent / "fixtures" / "s6_site_action_index_contract.json"
SITE = "/api/sites/KOBO-001"
POSITIVE = {"from": "2026-11-01T00:00:00Z", "to": "2026-11-02T00:00:00Z"}
ZERO = {"from": "2026-10-01T00:00:00Z", "to": "2026-11-01T00:00:00Z"}  # 31 days ending where the Actions begin


class Index:
    """The index route over the harness's own store and clock, on its own app (detail stays on `h.client`)."""

    def __init__(self, h, *, access=None, service: Any = "default") -> None:
        scope = {"KOBO-001": ("KOBO-001", h.runner.tenant, h.runner.site),
                 "OTHER-001": ("OTHER-001", h.runner.tenant, h.wrong_site)}
        app = FastAPI()
        kwargs = {} if access is None else {"access": access}
        app.include_router(build_action_index_router(
            ActionIndexService(h.store, clock=h.clock) if service == "default" else service, scope.get, **kwargs))
        self.client = TestClient(app)

    def get(self, site: str = "KOBO-001", **params):
        return self.client.get(f"/api/sites/{site}/action-index", params=params)


def same_fence_parity(h, body: dict) -> None:
    """Each row equals Action detail at the same fence: the latest read and the exact-event read."""
    for row in body["rows"]:
        path = f"{SITE}/actions/{row['action_id']}"
        latest = h.client.get(path).json()
        exact = h.client.get(path, params={"event_id": row["selected_event"]["id"]}).json()
        assert row["state"] == latest["state"] == exact["state"], row["action_code"]
        assert latest["selection"]["cutoff_event_id"] == row["selected_event"]["id"]
        assert latest["selection"]["total_event_count"] == row["event_count"]
        assert latest["last_event"]["kind"] == row["selected_event"]["kind"]
        assert row["origin"]["finding_revision_id"] == latest["origin"]["finding_revision_id"]
        assert row["origin"]["finding_id"] == latest["origin"]["finding_id"]
        assert exact["links"]["selected"] == row["links"]["selected_event"]
        assert latest["links"]["canonical"] == row["links"]["canonical"]
        assert latest["links"]["origin_finding"] == row["links"]["origin_finding"]


def shape(value: Any) -> Any:
    """The field structure of a body: dict keys recursively, the first list item's shape, scalar types."""
    if isinstance(value, dict):
        return {k: shape(v) for k, v in sorted(value.items())}
    if isinstance(value, list):
        return [shape(value[0])] if value else []
    return type(value).__name__ if value is not None else None


def contract(section: str, cases: dict[str, Any]) -> None:
    """Write this run's bodies (ASSETOPS_WRITE_S603_CONTRACT=1) or check them against the committed structure."""
    committed = json.loads(CONTRACT.read_text(encoding="utf-8")) if CONTRACT.is_file() else {}
    if os.environ.get("ASSETOPS_WRITE_S603_CONTRACT") == "1":
        committed[section] = cases
        committed["schema"] = "assetops.s6-site-action-index-contract"
        CONTRACT.write_text(json.dumps(committed, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return
    assert section in committed, f"{CONTRACT.name} has no {section!r}; regenerate it"
    for name, case in cases.items():
        assert shape(case) == shape(committed[section][name]), f"{section}.{name} drifted from {CONTRACT.name}"


def counted(runner, window: dict) -> int:
    """An independent count of persisted Actions created in the window (not through the index)."""
    with runner.engine.connect() as c:
        return c.execute(text("SELECT count(*) FROM action WHERE site_id = :s AND created_at >= :lo "
                              "AND created_at < :hi"),
                         {"s": runner.site, "lo": window["from"], "hi": window["to"]}).scalar_one()


def test_site_work_action_index_rows_paging_fence_zero_and_refusals(runner) -> None:
    build(runner, CASES, make_harness(runner), second_created_after=timedelta(minutes=5))
    findings = {f["anchor_start"].date().isoformat(): f["id"] for f in runner.reload()["findings"]}
    h = make_harness(runner)(fixture_grants(runner.tenant, runner.site, findings))
    index = Index(h)
    try:
        h.clock.at = T_ACCEPT + timedelta(hours=3)
        made = index.get(**POSITIVE)
        assert made.status_code == 200, made.text
        body = made.json()
        assert body["status"] == "CURRENT" and body["total_count"] == 2 == counted(runner, POSITIVE)
        assert body["window"] == {**POSITIVE, "bounds": "[from, to)", "membership": body["window"]["membership"]}
        assert body["display_timezone"] == "UTC" and body["read_at"] == "2026-11-01T03:00:00Z"
        second, first = body["rows"]
        assert first["created_at"] == "2026-11-01T00:00:00Z" and second["created_at"] == "2026-11-01T00:05:00Z"
        assert body["fence"]["max_created_at"] == second["created_at"] and body["fence"]["action_count"] == 2
        with runner.engine.connect() as c:
            assert body["fence"]["event_count"] == c.execute(text("SELECT count(*) FROM action_event")).scalar_one()
        for row in body["rows"]:
            assert row["key"] == {"tenant_id": str(runner.tenant), "site_id": str(runner.site),
                                  "action_id": row["action_id"]}
        assert first["origin"]["finding_id"] == str(findings["2026-10-06"])
        assert second["origin"]["finding_id"] == str(findings["2026-10-08"])
        assert first["selected_event"]["kind"] == "APPLIED" and first["state"]["application"] == "APPLIED"
        assert second["selected_event"]["kind"] == "FAILED" and second["state"]["application"] == "PENDING"
        assert "verification" not in first and first["state"]["outcome"]["state"] == "PENDING"
        assert first["links"]["origin_finding"] == (f"/sites/KOBO-001/findings/{first['origin']['finding_id']}"
                                                    f"?revision_id={first['origin']['finding_revision_id']}")
        same_fence_parity(h, body)

        cases: dict[str, Any] = {"positive": body}

        # Reload: same rows, fence and links.
        again = index.get(**POSITIVE).json()
        assert again["rows"] == body["rows"] and again["fence"] == body["fence"]

        # Paging on one fence.
        page1 = index.get(**POSITIVE, limit="1").json()
        assert [r["action_id"] for r in page1["rows"]] == [second["action_id"]] and page1["next_cursor"]
        page2 = index.get(**POSITIVE, limit="1", cursor=page1["next_cursor"]).json()
        assert [r["action_id"] for r in page2["rows"]] == [first["action_id"]] and page2["next_cursor"] is None
        assert page2["fence"]["token"] == page1["fence"]["token"] == body["fence"]["token"]
        cases.update(page1=page1, page2=page2)

        # A later observation that occurred before the Action existed: selected by recorded order, row stays put.
        h.clock.at = T_ACCEPT + timedelta(hours=4)
        observed = h.observe(first["action_id"], T_ACCEPT + timedelta(minutes=1), "s603-observe-backdated")
        assert observed.status_code == 201, observed.text
        changed = index.get(**POSITIVE, limit="1", cursor=page1["next_cursor"])
        assert changed.status_code == 409
        detail = changed.json()["detail"]
        assert detail["code"] == "ACTION_INDEX_BASIS_CHANGED" and detail["reason"] == "FENCE_CHANGED"
        assert detail["rows"] is None and detail["total_count"] is None
        cases["basis_changed"] = {"status": changed.status_code, "body": changed.json()}
        after = index.get(**POSITIVE).json()
        cases["after_backdated_observation"] = after
        assert [r["action_id"] for r in after["rows"]] == [second["action_id"], first["action_id"]]
        moved = after["rows"][1]
        assert moved["selected_event"]["id"] == observed.json()["event"]["id"]
        assert moved["selected_event"]["kind"] == "OBSERVED" and moved["selected_event"]["occurred_before_recorded"]
        assert moved["state"]["application"] == "APPLIED"  # a review note is state-neutral
        same_fence_parity(h, after)

        # An event committed later but stamped before the fence's latest recorded time still changes the fence.
        page1 = index.get(**POSITIVE, limit="1").json()
        h.clock.at = T_ACCEPT + timedelta(hours=3, minutes=30)
        older = h.observe(second["action_id"], T_ACCEPT + timedelta(minutes=10), "s603-observe-older-stamp")
        assert older.status_code == 201, older.text
        stale = index.get(**POSITIVE, limit="1", cursor=page1["next_cursor"])
        assert stale.status_code == 409 and stale.json()["detail"]["reason"] == "FENCE_CHANGED"
        assert index.get(**POSITIVE, limit="1").json()["fence"]["max_event_recorded_at"] == \
            page1["fence"]["max_event_recorded_at"]

        # Site isolation: another Site in scope lists none of KOBO's Actions; a KOBO cursor is not its page.
        other = index.get("OTHER-001", **POSITIVE)
        assert other.status_code == 200 and other.json()["total_count"] == 0
        crossed = index.get("OTHER-001", **POSITIVE, limit="1", cursor=page1["next_cursor"])
        assert crossed.status_code == 409 and crossed.json()["detail"]["reason"] == "SCOPE_CHANGED"
        assert index.get("UNKNOWN-001", **POSITIVE).status_code == 404

        # Independently assessed zero window, ending exactly where the first Action was created (`to` excluded).
        zero = index.get(**ZERO).json()
        assert counted(runner, ZERO) == 0
        assert zero["status"] == "CURRENT" and zero["total_count"] == 0 and zero["rows"] == []
        assert zero["fence"]["zero_rows"] is True and zero["fence"]["event_count"] == 0
        assert zero["zero_statement"].startswith("No persisted Action")
        cases.update(zero=zero, zero_window=ZERO, positive_window=POSITIVE)

        # Refusals carry no rows or count.
        for params, code in (({}, "WINDOW_REQUIRED"), ({"from": POSITIVE["from"]}, "WINDOW_REQUIRED"),
                             ({"from": "2026-10-01T00:00:00Z", "to": "2026-11-02T00:00:00Z"}, "INVALID_WINDOW"),
                             ({**POSITIVE, "from": "2026-11-01T00:00:00+03:00"}, "INVALID_WINDOW"),
                             ({**POSITIVE, "limit": "500"}, "INVALID_LIMIT"),
                             ({**POSITIVE, "cursor": "garbage"}, "INVALID_CURSOR")):
            refused = index.get(**params)
            assert refused.status_code == 422, params
            assert refused.json()["detail"]["code"] == code and refused.json()["detail"]["rows"] is None
            cases[f"refused_{code.lower()}"] = {"status": refused.status_code, "body": refused.json()}
        assert Index(h, access=lambda r, s: 401).get(**POSITIVE).status_code == 401
        assert Index(h, access=lambda r, s: 403).get(**POSITIVE).status_code == 403
        assert Index(h, service=None).get(**POSITIVE).json()["detail"]["code"] == "ACTION_STORE_UNAVAILABLE"
        down = PostgresActionStore("postgresql+psycopg://nobody:none@127.0.0.1:1/none")
        try:
            refused = Index(h, service=ActionIndexService(down)).get(**POSITIVE)
            assert refused.status_code == 503 and refused.json()["detail"]["code"] == "ACTION_STORE_UNAVAILABLE"
            assert refused.json()["detail"]["rows"] is None
            cases["store_unavailable"] = {"status": refused.status_code, "body": refused.json()}
        finally:
            down.dispose()
        contract("d_action_records", cases)
    finally:
        h.close()


def test_resolution_events_are_listed_as_recorded_with_detail_lifecycle(runner, monkeypatch) -> None:
    """S6-02a merged first: RESOLVED and RESOLUTION_WITHDRAWN are rows' recorded events, never a list verdict."""
    run_case(runner, CASES["F01"])
    run_case(runner, CASES["F02"])
    h = verifying(runner)
    index = Index(h)
    try:
        inject: set = set()
        complete_windows(monkeypatch, h, inject=inject)
        action_id, _, _ = bound_plan(runner, h)
        created = h.client.get(f"{SITE}/actions/{action_id}").json()["action"]["created_at"]
        day = datetime.fromisoformat(created).astimezone(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        window = {"from": day.isoformat().replace("+00:00", "Z"),
                  "to": (day + timedelta(days=1)).isoformat().replace("+00:00", "Z")}

        h.clock.at = CLOSED + timedelta(hours=1)
        assert evaluate(h, action_id, "s603-eval-0001").status_code == 201
        resolved = index.get(**window).json()
        [row] = [r for r in resolved["rows"] if r["action_id"] == action_id]
        assert row["selected_event"]["kind"] == "RESOLVED"
        assert row["state"]["resolution"]["state"] == "RESOLVED" and row["state"]["outcome"]["state"] == "VERIFIED"
        same_fence_parity(h, resolved)

        late = late_reading(runner, "2026-11-02T13:00:00Z")
        inject.update(late)
        h.clock.at = datetime(2026, 11, 2, 14, 0, tzinfo=UTC)
        assert evaluate(h, action_id, "s603-eval-0002").json()["withdrawn"] is True
        withdrawn = index.get(**window).json()
        [row] = [r for r in withdrawn["rows"] if r["action_id"] == action_id]
        assert row["selected_event"]["kind"] == "RESOLUTION_WITHDRAWN"
        assert row["state"]["resolution"]["state"] == "RESOLUTION_WITHDRAWN"
        assert row["state"]["outcome"]["state"] == "REASSESSMENT_PENDING"
        assert withdrawn["fence"]["token"] != resolved["fence"]["token"]
        same_fence_parity(h, withdrawn)
        contract("resolution", {"resolved": resolved, "withdrawn": withdrawn, "window": window})
    finally:
        h.close()
