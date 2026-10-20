"""W2-03 commit 4: the selected cold reads over the registered W2-02 replays (authenticated Batch V2 intake).

`.agent/W2-03-build-spec.md` "Commit 4 - selected reads" and the 2026-10-18 freshness amendment (probe recency at
the selected window's `to`). Each test opens a fresh W2-02 replay through `test_w203_cold_replay_postgres.opened`,
runs the cold worker and reads through the router with the real `ColdReadService`. Needs
`ASSETOPS_TEST_DATABASE_URL`; skipped (never passed) without it, except the pure currentness test.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from assetops_backend.analytics.cold_reads import currentness_state, encode_cursor, probe_fresh

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
needs_db = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from test_w202_cold_replay_postgres import chain  # noqa: F401 - the W2-02 replay fixture
    from test_w203_cold_replay_postgres import admit, opened, report_like, rows, run  # noqa: F401

    from assetops_backend.analytics.adapters.postgres_assessment_store import ColdReadService
    from assetops_backend.cold_assessment_api import build_cold_assessment_router

CODE = "COLD-READ"
W = "from=2026-10-06T19:00:00Z&to=2026-10-06T20:05:00Z"
TO = datetime(2026, 10, 6, 20, 5, tzinfo=timezone.utc)


def client(built, *, site_type="COLDCHAIN", tenant=None, access=None, disclosure=None, url=None) -> TestClient:
    site = SimpleNamespace(id=built.site_id, site_type=site_type)
    registry = SimpleNamespace(imported=lambda code: site if code == CODE else None,
                               tenant=lambda: SimpleNamespace(id=tenant or built.tenant_id))
    kw = {}
    if access is not None:
        kw["access"] = access
    if disclosure is not None:
        kw["disclosure"] = disclosure
    app = FastAPI()
    app.include_router(build_cold_assessment_router(registry, ColdReadService(url or URL), **kw))
    return TestClient(app)


def get(c: TestClient, path: str, status: int = 200) -> dict:
    response = c.get(f"/api/sites/{CODE}/cold/{path}")
    assert response.status_code == status, response.text
    return response.json()


def error(c: TestClient, path: str, status: int) -> str:
    body = get(c, path, status)
    assert set(body) == {"error"} and set(body["error"]) == {"code", "message"}, body
    return body["error"]["code"]


def test_currentness_precedence() -> None:
    """The amendment's precedence and the one freshness function, at the window's `to` (not the wall clock)."""
    late = datetime(2026, 10, 18, tzinfo=timezone.utc)
    probe = TO - timedelta(minutes=5)
    base = {"pending": False, "historical": False, "selected": True, "latest_probe_at": probe, "window_to": TO,
            "now": late}
    assert probe_fresh(probe, TO) and probe_fresh(TO - timedelta(minutes=10), TO)
    assert not probe_fresh(TO - timedelta(minutes=11), TO) and not probe_fresh(None, TO)
    assert currentness_state(**base) == "CURRENT"  # a 2026-10-06 replay viewed twelve days later
    assert currentness_state(**{**base, "latest_probe_at": TO - timedelta(minutes=25)}) == "STALE_SOURCE"
    assert currentness_state(**{**base, "pending": True, "historical": True}) == "PENDING_RECOMPUTE"
    assert currentness_state(**{**base, "historical": True}) == "HISTORICAL"  # even with a fresh probe
    assert currentness_state(**{**base, "selected": False}) == "UNKNOWN"
    assert currentness_state(**{**base, "latest_probe_at": None}) == "UNKNOWN"
    assert currentness_state(**{**base, "now": TO - timedelta(minutes=1)}) == "UNKNOWN"  # future `to`


@needs_db
def test_window_limit_and_paging(chain) -> None:  # noqa: F811
    built = opened("backup-failed", chain)
    run(built)
    c = client(built)
    temperature = get(c, f"temperature?{W}")
    assert temperature["currentness"]["state"] == "CURRENT"  # window-scoped: the 20:00 probe at `to` 20:05
    assert temperature["currentness"]["latest_relevant_evidence_at"] == "2026-10-06T20:00:00.000000Z"
    assert temperature["coverage"] == {"known_points": 13, "expected_points": 13, "ratio": "1"}
    assert len(temperature["points"]) == 13 and all(p["evidence_id"] and p["as_of"] for p in temperature["points"])
    [x] = temperature["excursions"]
    assert x["start_bounds"] == {"earliest": "2026-10-06T19:10:00.000000Z", "latest": "2026-10-06T19:15:00.000000Z"}
    assert x["duration_bounds"] == {"low": "45", "high": None} and x["episode_id"] and x["revision_id"]
    assert {e["reason"] for e in temperature["excluded"]} >= {"DOOR_EVENT"}
    assert temperature["policy"]["probe_asset_id"] and temperature["policy"]["as_of"]
    assert get(c, "temperature")["window"]["from"] == "2026-10-06T19:00:00.000000Z"  # default: latest selected
    backup = get(c, f"backup-chain?{W}")
    [ch] = backup["chains"]
    assert [s["kind"] for s in ch["steps"]][:3] == ["GRID", "START_REQUEST", "START_RESULT"]
    transfer = next(s for s in ch["steps"] if s["kind"] == "TRANSFER")
    assert (transfer["state"], transfer["at"], transfer["evidence_id"]) == ("MISSING", None, None)
    assert ch["result"] == "OBSERVED_FAILURE" and ch["episode_id"]
    # Paging: two cold Findings (exposure and start failure), ordered by (anchor_time, finding_id).
    first = get(c, f"findings?{W}&limit=1")
    assert len(first["items"]) == 1 and first["next_cursor"]
    second = get(c, f"findings?{W}&limit=1&cursor={first['next_cursor']}")
    assert len(second["items"]) == 1 and second["next_cursor"] is None
    items = first["items"] + second["items"]
    assert {i["kind"] for i in items} == {"EXCURSION", "START_RESPONSE"}
    assert get(c, f"findings?{W}")["items"] == items
    detail = get(c, f"findings/{items[0]['finding_id']}?{W}")
    assert detail["revisions"][0]["transition"] == "OPENED" and detail["episode_revision_id"]
    assert detail["links"]["analysis"]["assessment_revision_id"] == detail["assessment_revision_id"]
    assert all(link["href"] and "known_at=" in link["href"] for link in detail["links"]["evidence"])
    # Limits and the window contract.
    assert error(c, "findings?from=2026-09-01T00:00:00Z&to=2026-10-06T20:05:00Z", 422) == "COLD_WINDOW_TOO_LONG"
    assert error(c, "temperature?from=2026-10-06T20:05:00Z&to=2026-10-06T19:00:00Z", 422) == "COLD_WINDOW_INVALID"
    assert error(c, "temperature?from=2026-10-06T19:00:00Z", 422) == "COLD_WINDOW_INVALID"
    assert error(c, "temperature?from=2026-10-06T19:00:00%2B02:00&to=2026-10-06T20:05:00Z", 422) == \
        "COLD_TIME_INVALID"
    assert error(c, f"findings?{W}&limit=0", 422) == "COLD_LIMIT_INVALID"
    assert error(c, f"findings?{W}&limit=201", 422) == "COLD_LIMIT_INVALID"
    assert error(c, f"findings?{W}&cursor=not-a-cursor", 422) == "COLD_CURSOR_INVALID"
    stale = encode_cursor(TO, uuid4(), "0" * 64)
    assert error(c, f"findings?{W}&cursor={stale}", 409) == "COLD_CURSOR_BASIS_CHANGED"


@needs_db
def test_typed_errors_and_unknown_200(chain) -> None:  # noqa: F811
    built = opened("missing-probe", chain)
    run(built)
    c = client(built)
    temperature = get(c, f"temperature?{W}")
    assert temperature["coverage"]["known_points"] == 7
    assert not any(x["exposure_finding"] for x in temperature["excursions"])  # coverage 7/13: no exposure claim
    assert not [i for i in get(c, f"findings?{W}")["items"] if i["kind"] == "EXCURSION"]
    assert any(g["start"] == "2026-10-06T19:15:00.000000Z" for g in temperature["gaps"])
    # A valid window with no selected assessment: 200 UNKNOWN, null values, empty arrays.
    empty = "from=2026-10-05T19:00:00Z&to=2026-10-05T20:05:00Z"
    unknown = get(c, f"temperature?{empty}")
    assert unknown["currentness"]["state"] == "UNKNOWN" and unknown["policy"] is None
    assert unknown["points"] == [] and unknown["coverage"]["ratio"] is None and unknown["limitations"]
    assert get(c, f"backup-chain?{empty}")["chains"] == []
    listed = get(c, f"findings?{empty}")
    assert (listed["items"], listed["next_cursor"], listed["currentness"]["state"]) == ([], None, "UNKNOWN")
    assert error(c, f"temperature?{W}&at=2026-10-06T19:00:00Z", 422) == "COLD_PARAMETER_UNKNOWN"
    assert error(c, f"findings/{uuid4()}?{W}", 404) == "COLD_FINDING_NOT_FOUND"
    assert error(c, f"findings/not-a-uuid?{W}", 404) == "COLD_FINDING_NOT_FOUND"
    assert client(built).get(f"/api/sites/OTHER/cold/temperature?{W}").status_code == 404
    assert error(client(built, site_type="MINIGRID"), f"temperature?{W}", 404) == "SITE_NOT_FOUND"
    assert error(client(built, access=lambda r, code: 401), f"temperature?{W}", 401) == "UNAUTHENTICATED"
    down = client(built, url="postgresql+psycopg://nobody:x@127.0.0.1:1/none?connect_timeout=2")
    assert error(down, f"temperature?{W}", 503) == "COLD_READ_UNAVAILABLE"
    assert error(down, f"findings?{W}", 503) == "COLD_READ_UNAVAILABLE"


@needs_db
def test_tenant_source_gate(chain) -> None:  # noqa: F811
    built = opened("excursion", chain)
    run(built)
    c = client(built)
    temperature = get(c, f"temperature?{W}")
    provenance = temperature["source_provenance"]
    assert provenance["classification"] == "REGISTERED_SIMULATION" and provenance["source_ids"]
    assert provenance["basis_sha256"] and len(provenance["evidence_ids"]) >= 13
    assert error(client(built, access=lambda r, code: 403), f"temperature?{W}", 403) == "SITE_SCOPE_FORBIDDEN"
    assert error(client(built, disclosure=lambda code, t, s: False), f"findings?{W}", 403) == \
        "COLD_SOURCE_DISCLOSURE_FORBIDDEN"
    # Another tenant's scope sees nothing of this Site: every query is tenant-filtered.
    foreign = client(built, tenant=uuid4())
    assert get(foreign, f"temperature?{W}")["currentness"]["state"] == "UNKNOWN"
    assert get(foreign, f"findings?{W}")["items"] == []
    [finding] = [i for i in get(c, f"findings?{W}")["items"] if i["kind"] == "EXCURSION"]
    assert error(foreign, f"findings/{finding['finding_id']}?{W}", 404) == "COLD_FINDING_NOT_FOUND"
    # A mini-grid Finding read never answers for a cold Finding and vice versa: domain-filtered.
    assert rows(built, "SELECT count(*) AS n FROM finding WHERE site_id = :s AND domain = 'cold_chain'")[0]["n"] >= 1


@needs_db
def test_pending_historical_reload(chain) -> None:  # noqa: F811
    built = opened("late-reading", chain)
    run(built)
    c = client(built)
    before = get(c, f"temperature?{W}")
    assert before["coverage"]["known_points"] == 12 and before["currentness"]["state"] == "CURRENT"
    cutoff = before["window"]["known_at"]
    first_revision = before["currentness"]["watermark"]["assessment_revision_ids"]
    built.advance_late()
    pending = get(c, f"temperature?{W}")
    assert pending["currentness"]["state"] == "PENDING_RECOMPUTE" and pending["currentness"]["pending_since"]
    assert pending["coverage"]["known_points"] == 12  # the previous selected result, only as pending
    assert pending["currentness"]["watermark"]["assessment_revision_ids"] == first_revision
    run(built)
    after = get(c, f"temperature?{W}")
    assert after["coverage"]["known_points"] == 13 and after["currentness"]["state"] == "CURRENT"
    assert after["currentness"]["watermark"]["assessment_revision_ids"] != first_revision
    historical = get(c, f"temperature?{W}&known_at={cutoff}")
    assert historical["currentness"]["state"] == "HISTORICAL" and historical["coverage"]["known_points"] == 12
    assert historical["currentness"]["watermark"]["assessment_revision_ids"] == first_revision
    [finding] = [i for i in get(c, f"findings?{W}")["items"] if i["kind"] == "EXCURSION"]
    old = get(c, f"findings/{finding['finding_id']}?{W}&known_at={cutoff}")
    assert [r["transition"] for r in old["revisions"]] == ["OPENED"]
    now = get(c, f"findings/{finding['finding_id']}?{W}")
    assert [r["transition"] for r in now["revisions"]] == ["SUPPORT_CHANGED", "OPENED"]
    assert get(c, f"temperature?{W}") == after  # reload is stable
