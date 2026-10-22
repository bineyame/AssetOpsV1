"""W5-01 C1: the selected cold Cooling depth read over the registered W2-02 replays
(`.agent/W5-01-build-spec.md` "Shared selected read and guards", "C1" and its derivation table).

Each test opens a fresh W2-02 replay (`test_w203_cold_replay_postgres.opened`), runs the cold worker and reads
`/cold/cooling` through the real gate and `ColdReadService`. Current reads omit `known_at` and use the committed
watermark (wall-clock `decided_at`); the historical read passes the exact `known_at` saved before
`advance_late()`. Needs `ASSETOPS_TEST_DATABASE_URL`; skipped (never passed) without it.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
needs_db = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from sqlalchemy import text
    from test_w202_cold_replay_postgres import CASES, chain  # noqa: F401 - the W2-02 replay fixture
    from test_w203_cold_replay_postgres import opened, rows, run

    from assetops_backend.analytics import cold
    from assetops_backend.analytics.adapters.postgres_assessment_store import ColdReadService
    from assetops_backend.analytics.cold_depth import CONTEXT_ROWS, ColdDepthReadService
    from assetops_backend.analytics.cold_reads import STATES
    from assetops_backend.cold_depth_api import build_cold_depth_router
    from assetops_backend.evidence.composition import build_link_rows_reader

CODE = "COLD-READ"
W = "from=2026-10-06T19:00:00Z&to=2026-10-06T20:05:00Z"
STALE = "from=2026-10-06T19:00:00Z&to=2026-10-06T20:30:00Z"
EMPTY = "from=2026-10-05T19:00:00Z&to=2026-10-05T20:05:00Z"
NULLS = ("observed_restart_at", "observed_return_to_policy_at", "duration_lower_seconds", "duration_upper_seconds")
DOWN = "postgresql+psycopg://nobody:x@127.0.0.1:1/none?connect_timeout=2"


def _registry(built, site_type="COLDCHAIN", tenant=None):
    site = SimpleNamespace(id=built.site_id, site_type=site_type)
    return SimpleNamespace(imported=lambda code: site if code == CODE else None,
                           tenant=lambda: SimpleNamespace(id=tenant or built.tenant_id))


def service(url=None) -> "ColdReadService":
    return ColdReadService(url or URL, link_rows=build_link_rows_reader())


def client(built, *, url=None, tenant=None, disclosure=None) -> TestClient:
    kw = {} if disclosure is None else {"disclosure": disclosure}
    app = FastAPI()
    app.include_router(build_cold_depth_router(_registry(built, tenant=tenant),
                                               ColdDepthReadService(service(url)), **kw))
    return TestClient(app)


def get(c: TestClient, query: str, status: int = 200) -> dict:
    response = c.get(f"/api/sites/{CODE}/cold/cooling?{query}")
    assert response.status_code == status, response.text
    return response.json()


def error(c: TestClient, query: str, status: int) -> str:
    body = get(c, query, status)
    assert set(body) == {"error"} and set(body["error"]) == {"code", "message"}, body
    return body["error"]["code"]


def _instant(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _plain_ids(values) -> list[str]:
    return sorted({str(v).lower() for v in values})


def selected_revisions(built, body: dict) -> list[dict]:
    ids = body["selection"]["assessment_revision_ids"]
    return [dict(r) for r in rows(built, "SELECT id, analytic_id, result, evidence_ids FROM assessment_revision "
                                         "WHERE site_id = :s AND id = ANY(CAST(:ids AS uuid[]))", ids=ids)]


def watermark(built) -> str:
    [r] = rows(built, "SELECT max(decided_at) AS m FROM ingestion_disposition WHERE site_id = :s")
    return cold.plain(r["m"])


def assert_exact_selection(built, body: dict) -> None:
    """The envelope names the exact selected W2-03 revisions, their full deduplicated cited set and the W2-03
    envelope's `source_provenance` for those revisions, on the committed watermark."""
    revisions = selected_revisions(built, body)
    assert len(revisions) == len(body["selection"]["assessment_revision_ids"]) >= 1
    cited = _plain_ids(e for r in revisions for e in (r["evidence_ids"] if isinstance(r["evidence_ids"], list)
                                                         else json.loads(r["evidence_ids"])))
    assert body["selection"]["accepted_evidence_ids"] == cited
    window = {k: _instant(body["window"][k]) for k in ("from", "to", "known_at")}
    reads = service()
    expected = reads.within(lambda c: reads.envelope_on(c, reads.selection_on(
        c, built.tenant_id, built.site_id, CODE, window["from"], window["to"], window["known_at"]),
        (cold.EXCURSION_ANALYTIC, cold.START_RESPONSE_ANALYTIC))["source_provenance"])
    reads.dispose()
    assert body["selection"]["source_provenance"] == expected
    assert set(body["selection"]["source_provenance"]["evidence_ids"]) <= set(cited)


def assert_no_comparison(body: dict) -> None:
    cooling = body["cooling"]
    assert [cooling[k] for k in NULLS] == [None, None, None, None]
    assert cooling["comparison_state"] == "CONTEXT_MISSING"
    assert [r["label"] for r in cooling["context"]] == list(CONTEXT_ROWS)
    for label in ("Ambient temperature", "Loading / batch", "Defrost"):
        [row] = [r for r in cooling["context"] if r["label"] == label]
        assert (row["state"], row["evidence_ids"], row["duration_seconds"]) == ("Unknown", [], None)


@needs_db
def test_cooling_first_steps_and_context(chain) -> None:  # noqa: F811
    built = opened("backup-failed", chain)
    run(built)
    c = client(built)
    body = get(c, W)
    assert list(body) == ["schema_version", "site_id", "window", "selection", "cooling", "links"]
    assert body["schema_version"] == "cold-depth-1" and body["site_id"] == str(built.site_id)
    mark = watermark(built)
    assert body["window"] == {"from": "2026-10-06T19:00:00.000000Z", "to": "2026-10-06T20:05:00.000000Z",
                              "known_at": mark, "committed_watermark": mark}
    assert body["selection"]["state"] in STATES
    assert_exact_selection(built, body)
    cooling = body["cooling"]
    assert cooling["recovery_state"] == "LIMITED"
    assert_no_comparison(body)
    # selected_points: exactly the selected start chain's observed COMPRESSOR/PROBE first steps.
    [start] = [r for r in selected_revisions(built, body) if r["analytic_id"] == cold.START_RESPONSE_ANALYTIC]
    expected = sorted(({"role": {"COMPRESSOR": cold.COMPRESSOR_ROLE, "PROBE": cold.PROBE_ROLE}[s["step"]],
                        "source_time": s["at"], "evidence_ids": _plain_ids(s["evidence_ids"])}
                       for ch in start["result"]["chains"] for s in ch["steps"]
                       if s["step"] in ("COMPRESSOR", "PROBE") and s["state"] == "OBSERVED"),
                      key=lambda p: (p["source_time"], p["role"], p["evidence_ids"]))
    assert cooling["selected_points"] == expected
    for point in cooling["selected_points"]:
        assert set(point["evidence_ids"]) <= set(body["selection"]["accepted_evidence_ids"])
    # Context: door pair 19:10 -> 19:11 is Observed (60 s); power is Observed from the selected grid rows.
    selected = body["selection"]["accepted_evidence_ids"]
    ledger = rows(built, "SELECT id, role, record_kind, source_time FROM accepted_evidence WHERE site_id = :s "
                         "AND id = ANY(CAST(:ids AS uuid[]))", ids=selected)
    doors = sorted((r for r in ledger if r["role"] == cold.DOOR_ROLE), key=lambda r: r["source_time"])
    assert [r["record_kind"] for r in doors] == ["DOOR_OPEN", "DOOR_CLOSE"]
    context = {r["label"]: r for r in cooling["context"]}
    assert (context["Door-open duration"]["state"], context["Door-open duration"]["duration_seconds"]) == \
        ("Observed", 60)
    assert context["Door-open duration"]["evidence_ids"] == _plain_ids(r["id"] for r in doors)
    grid = _plain_ids(r["id"] for r in ledger if r["role"] == cold.GRID_EVENT_ROLE)
    assert grid and context["Power availability"] == {"label": "Power availability", "state": "Observed",
                                                      "evidence_ids": grid, "duration_seconds": None}
    # Site-code API links preserving from/to/known_at.
    assert set(body["links"]) == {"temperature", "backup", "evidence", "health"}
    for key, suffix in (("temperature", "temperature"), ("backup", "backup-chain"), ("evidence", "evidence"),
                        ("health", "health")):
        href = body["links"][key].replace("%3A", ":")
        assert href.startswith(f"/api/sites/{CODE}/cold/{suffix}?from=2026-10-06T19:00:00.000000Z")
        assert f"known_at={mark}" in href and str(built.site_id) not in href
    # Wrong Site, foreign tenant, disclosure and a down store.
    assert c.get(f"/api/sites/OTHER/cold/cooling?{W}").status_code == 404
    foreign = get(client(built, tenant=uuid4()), W)
    assert foreign["selection"]["assessment_revision_ids"] == [] and foreign["cooling"]["selected_points"] == []
    assert error(client(built, disclosure=lambda code, t, s: False), W, 403) == "COLD_SOURCE_DISCLOSURE_FORBIDDEN"
    assert error(client(built, url=DOWN), W, 503) == "COLD_READ_UNAVAILABLE"
    assert error(c, f"{W}&known_at=2999-01-01T00:00:00Z", 422) == "COLD_TIME_INVALID"


@needs_db
def test_late_reading_pending_then_historical(chain) -> None:  # noqa: F811
    built = opened("late-reading", chain)
    run(built)
    c = client(built)
    before = get(c, W)  # the first cutoff
    assert before["selection"]["state"] == "CURRENT"
    saved = before["window"]["known_at"]
    assert saved == before["window"]["committed_watermark"] == watermark(built)
    assert_exact_selection(built, before)
    assert_no_comparison(before)
    built.advance_late()
    pending = get(c, W)
    assert pending["selection"]["state"] == "PENDING_RECOMPUTE"
    assert pending["selection"]["assessment_revision_ids"] == before["selection"]["assessment_revision_ids"]
    assert pending["window"]["committed_watermark"] > saved
    assert_no_comparison(pending)
    jobs = [r["id"] for r in rows(built, "SELECT id FROM recompute_job WHERE site_id = :s AND status = 'PENDING'")]
    assert jobs
    for status in ("LEASED", "FAILED", "PENDING"):
        with built.engine.begin() as conn:
            conn.execute(text("UPDATE recompute_job SET status = :st WHERE id = ANY(CAST(:ids AS uuid[]))"),
                         {"st": status, "ids": [str(j) for j in jobs]})
        assert get(c, W)["selection"]["state"] == "PENDING_RECOMPUTE", status
    historical = get(c, f"{W}&known_at={saved}")
    assert historical["selection"]["state"] == "HISTORICAL"
    assert historical["window"]["known_at"] == saved
    assert historical["selection"]["assessment_revision_ids"] == before["selection"]["assessment_revision_ids"]
    assert historical["selection"]["accepted_evidence_ids"] == before["selection"]["accepted_evidence_ids"]
    assert historical["cooling"] == before["cooling"]
    assert saved in historical["links"]["temperature"].replace("%3A", ":")
    run(built)  # the final cutoff: a new selected assessment over the late reading
    final = get(c, W)
    assert final["selection"]["state"] == "CURRENT"
    assert final["window"]["known_at"] == final["window"]["committed_watermark"] > saved
    assert final["selection"]["assessment_revision_ids"] != before["selection"]["assessment_revision_ids"]
    assert set(before["selection"]["accepted_evidence_ids"]) < set(final["selection"]["accepted_evidence_ids"])
    assert_exact_selection(built, final)
    assert_no_comparison(final)


@needs_db
def test_missing_probe_and_empty(chain) -> None:  # noqa: F811
    built = opened("missing-probe", chain)
    run(built)
    c = client(built)
    body = get(c, W)
    assert_exact_selection(built, body)
    assert_no_comparison(body)
    empty = get(c, EMPTY)
    assert empty["selection"]["state"] == "UNKNOWN"
    assert (empty["selection"]["assessment_revision_ids"], empty["selection"]["accepted_evidence_ids"]) == ([], [])
    assert empty["cooling"]["recovery_state"] == "UNKNOWN" and empty["cooling"]["selected_points"] == []
    assert all(r["state"] == "Unknown" and r["evidence_ids"] == [] for r in empty["cooling"]["context"])
    assert_no_comparison(empty)


@needs_db
def test_stale_probe_window(chain) -> None:  # noqa: F811
    """A direct stale-source producer: the worker assesses an enqueued window ending 30 minutes after the replay's
    last accepted probe, so the selected probe is stale at that window's `to` (probe recency 10 minutes)."""
    built = opened("normal", chain)
    run(built)
    with built.engine.begin() as conn:
        conn.execute(text(
            "INSERT INTO recompute_job (id, tenant_id, site_id, domain, window_start, window_end, status, "
            "available_at, created_at) VALUES (:j, :t, :s, 'cold_chain', '2026-10-06T19:00:00Z', "
            "'2026-10-06T20:30:00Z', 'PENDING', now(), now())"),
            {"j": uuid4(), "t": built.tenant_id, "s": built.site_id})
    run(built)
    body = get(client(built), STALE)
    assert body["selection"]["state"] == "STALE_SOURCE"
    assert body["window"]["known_at"] == body["window"]["committed_watermark"] == watermark(built)
    assert_exact_selection(built, body)
    assert_no_comparison(body)
    assert body["cooling"]["recovery_state"] == "LIMITED"


@needs_db
@pytest.mark.parametrize("case", CASES if URL else ())
def test_no_w2_case_has_numeric_comparison(chain, case) -> None:  # noqa: F811
    built = opened(case, chain)
    run(built)
    body = get(client(built), W)
    assert body["cooling"]["recovery_state"] in ("LIMITED", "CONTRADICTORY", "UNKNOWN")
    assert_no_comparison(body)
    blob = json.dumps(body["cooling"])
    assert "36" not in json.dumps([body["cooling"][k] for k in NULLS]) and "+17" not in blob
