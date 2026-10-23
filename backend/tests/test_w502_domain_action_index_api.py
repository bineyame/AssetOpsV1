"""W5-02a K1b: `GET /api/sites/{site_code}/domain-work/action-index` - gate, B3 refusal order and literals, wire.

`.agent/W5-02-build-spec.md` "Site Action index", K1b index line and the Architect pre-flight ruling B3: 401/403/404/503
from the shared W4 gate, then 422 `INVALID_WINDOW`, `INVALID_LIMIT`, `INVALID_KNOWN_AT`, `INVALID_CURSOR` in that
order with the exact W4 literals, and 409 `WORK_BASIS_CHANGED` for a valid changed-basis cursor. No refusal carries a
count. The data path uses the ordinary cold replay fixture. Requires ASSETOPS_TEST_DATABASE_URL naming a `*_test`
database.
"""

from __future__ import annotations

from datetime import timedelta

import pytest

from test_s4_finding_store_postgres import URL

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from fastapi.testclient import TestClient
    from test_w202_cold_replay_postgres import chain  # noqa: F401
    from test_w502_domain_intent_api import Api
    from test_w502_domain_intent_postgres import COLD, action_body, cold, iso, now_utc  # noqa: F401

    from assetops_backend.main import create_app
    from assetops_backend.work import domain_action_index as x
    from assetops_backend.work.model import MESSAGES
    from assetops_backend.work.site_index import encode_cursor as w4_cursor

PATH = "/action-index"


def refused(response, status: int, code: str) -> None:
    assert response.status_code == status, response.text
    assert response.json() == {"detail": {"code": code, "message": MESSAGES[code]}}, response.text


def test_literals_are_the_w4_ones() -> None:
    assert (MESSAGES["INVALID_WINDOW"], MESSAGES["INVALID_LIMIT"], MESSAGES["INVALID_KNOWN_AT"],
            MESSAGES["INVALID_CURSOR"], MESSAGES["WORK_BASIS_CHANGED"]) == (
        "The window may span at most 31 days.", "`limit` must be an integer from 1 to 100.",
        "'known_at' must be one UTC instant no later than the read time.", "The cursor is not a work-list cursor.",
        "The work list changed; request page one without a cursor.")
    assert (x.PAGE_DEFAULT, x.PAGE_MAX) == (5, 100)


def test_create_app_mounts_the_reads() -> None:
    client = TestClient(create_app())
    for path in (PATH, "/actions/00000000-0000-0000-0000-000000000000"):
        r = client.get(f"/api/sites/NOPE-404/domain-work{path}")
        assert (r.status_code, r.json()["detail"]["code"]) in ((404, "SITE_NOT_FOUND"),
                                                               (503, "WORK_STORE_UNAVAILABLE")), r.text


def test_gate_refusal_order_and_wire(cold) -> None:
    bad = {"from": "x", "limit": "0", "known_at": "y", "cursor": "z"}
    for status, code, message in ((401, "UNAUTHENTICATED", "Sign in to read work."),
                                  (403, "SITE_SCOPE_FORBIDDEN", f"No access to Site '{COLD}'.")):
        api = Api(cold.t, cold.s, access=lambda r, c, v=status: v)
        try:
            r = api.get(PATH, **bad)
            assert r.status_code == status and r.json() == {"detail": {"code": code, "message": message}}, r.text
        finally:
            api.close()
    api = Api(cold.t, cold.s, reads=False)
    try:
        r = api.get(PATH, code="NOPE-001", **bad)
        assert (r.status_code, r.json()["detail"]["code"]) == (404, "SITE_NOT_FOUND")
        refused(api.get(PATH, **bad), 503, "WORK_STORE_UNAVAILABLE")
    finally:
        api.close()

    api = Api(cold.t, cold.s)
    try:
        db_now = now_utc(cold.engine)
        lo, hi = iso(db_now - timedelta(days=1)), iso(db_now + timedelta(hours=1))
        future = iso(db_now + timedelta(days=2))
        # B3 order: window, limit, known_at (shape, then not after the read time), cursor.
        refused(api.get(PATH, **bad), 422, "INVALID_WINDOW")
        for window in ({"to": hi}, {"from": lo}, {"from": hi, "to": lo}, {"from": "2026-01-01T00:00:00", "to": hi},
                       {"from": iso(db_now - timedelta(days=32)), "to": hi}):
            refused(api.get(PATH, **window), 422, "INVALID_WINDOW")
        refused(api.get(PATH, **{**bad, "from": lo, "to": hi}), 422, "INVALID_LIMIT")
        for limit in ("0", "101", "five", "2.5"):
            refused(api.get(PATH, **{"from": lo, "to": hi, "limit": limit}), 422, "INVALID_LIMIT")
        refused(api.get(PATH, **{**bad, "from": lo, "to": hi, "limit": "5"}), 422, "INVALID_KNOWN_AT")
        refused(api.get(PATH, **{**bad, "from": lo, "to": hi, "limit": "5", "known_at": future}), 422,
                "INVALID_KNOWN_AT")
        refused(api.client.get(f"/api/sites/{COLD}/domain-work{PATH}",
                               params=[("from", lo), ("to", hi), ("known_at", lo), ("known_at", lo)]),
                422, "INVALID_KNOWN_AT")
        refused(api.get(PATH, **{**bad, "from": lo, "to": hi, "limit": "5", "known_at": lo}), 422, "INVALID_CURSOR")
        w4 = w4_cursor({"v": 1, "tenant_id": str(cold.t), "site_id": str(cold.s), "kind": "incidents", "from": lo,
                        "to": hi, "known_at": lo, "selection_token": "sha256:" + "0" * 64,
                        "after": [lo, "00000000-0000-0000-0000-000000000000"]})
        refused(api.get(PATH, **{"from": lo, "to": hi, "cursor": w4}), 422, "INVALID_CURSOR")  # a W4 cursor

        for n in range(6):
            r = api.post("", action_body(cold, f"w502-api-index-{n:02d}",
                                         raised_at=iso(db_now - timedelta(minutes=5 * (n + 1)))))
            assert r.status_code == 201, r.text
        r = api.get(PATH, **{"from": lo, "to": hi})
        assert r.status_code == 200, r.text
        body = r.json()
        assert set(body) == {"schema_version", "site_code", "window", "known_at", "status", "coverage",
                             "total_count", "all_due_dates_unset", "rows", "next_cursor", "selection_token"}
        assert (body["total_count"], len(body["rows"]), body["all_due_dates_unset"]) == (6, 5, True)
        assert body["schema_version"] == "site-domain-action-index-1" and body["site_code"] == COLD
        page2 = api.get(PATH, **{"from": lo, "to": hi, "cursor": body["next_cursor"]}).json()
        assert len(page2["rows"]) == 1 and page2["next_cursor"] is None
        payload = x.decode_cursor(body["next_cursor"])
        assert payload["kind"] == "site-domain-action-index" and payload["v"] == 1
        stale = x.encode_cursor({**payload, "selection_token": "sha256:" + "f" * 64})
        refused(api.get(PATH, **{"from": lo, "to": hi, "cursor": stale}), 409, "WORK_BASIS_CHANGED")
    finally:
        api.close()
