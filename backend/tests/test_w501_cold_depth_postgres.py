"""W5-01 C1: the selected cold Cooling depth read over the registered W2-02 replays
(`.agent/W5-01-build-spec.md` "Shared selected read and guards", "C1" and its derivation table).

Each test opens a fresh W2-02 replay (`test_w203_cold_replay_postgres.opened`), runs the cold worker and reads
`/cold/cooling` through the real gate and `ColdReadService`. Current reads omit `known_at` and use the committed
watermark (wall-clock `decided_at`); the historical read passes the exact `known_at` saved before
`advance_late()`. Needs `ASSETOPS_TEST_DATABASE_URL`; skipped (never passed) without it.
"""

from __future__ import annotations

import hashlib
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
    from test_w202_cold_replay_postgres import CASES, canonical_json, chain  # noqa: F401 - the W2-02 replay fixture
    from test_w203_cold_replay_postgres import opened, rows, run

    from assetops_backend.analytics import cold
    from assetops_backend.analytics.adapters.postgres_assessment_store import ColdReadService
    from assetops_backend.analytics.cold_depth import CONTEXT_ROWS, HEALTH_ROW_KEYS, ColdDepthReadService
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


def get(c: TestClient, query: str, status: int = 200, route: str = "cooling") -> dict:
    response = c.get(f"/api/sites/{CODE}/cold/{route}?{query}")
    assert response.status_code == status, response.text
    return response.json()


def error(c: TestClient, query: str, status: int, route: str = "cooling") -> str:
    body = get(c, query, status, route)
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
    assert body["selection"]["state"] == "CURRENT"
    assert_exact_selection(built, body)
    cooling = body["cooling"]
    assert cooling["recovery_state"] == "LIMITED"
    [exc] = [r for r in selected_revisions(built, body) if r["analytic_id"] == cold.EXCURSION_ANALYTIC]
    assert cooling["policy_high_deg_c"] == exc["result"]["policy"]["policy_high"] is not None
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
    # Q11: the health link resolves.
    health = c.get(body["links"]["health"])
    assert health.status_code == 200, health.text
    assert health.json()["schema_version"] == "cold-depth-1"
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
    assert "+17" not in json.dumps(body["cooling"])
    health = get(client(built), W, route="health")["health"]
    assert all(r["condition_state"] != "NOT_CONFIGURED" for r in health["rows"])
    assert health["foundation_revision_id"] == str(built.run.registered_basis.foundation_revision_id).lower()


# --- /cold/health (C1 Health read) -----------------------------------------------------------------------------

def foundation_assets(built, revision_id: str) -> dict[str, list[str]]:
    """component_type -> the scoped asset row IDs of the Foundation revision's components of that type, in
    `asset_code` order."""
    [rev] = rows(built, "SELECT content FROM foundation_revision WHERE site_id = :s AND id = CAST(:f AS uuid)",
                 f=revision_id)
    assets = {(r["asset_code"], r["asset_type"]): str(r["id"]).lower()
              for r in rows(built, "SELECT id, asset_code, asset_type FROM asset WHERE site_id = :s")}
    out: dict[str, list[tuple[str, str]]] = {}
    for comp in rev["content"]["components"]:
        kind = comp["component_type"]
        if kind in ("GENERATOR", "COMPRESSOR", "TEMPERATURE_PROBE"):
            out.setdefault(kind, []).append((comp["component_id"], assets[(comp["component_id"], kind)]))
    assert set(out) == {"GENERATOR", "COMPRESSOR", "TEMPERATURE_PROBE"}
    return {kind: [a for _, a in sorted(pairs)] for kind, pairs in out.items()}


def assert_health_head(body: dict) -> None:
    assert list(body) == ["schema_version", "site_id", "window", "selection", "health", "links"]
    assert list(body["health"]) == ["foundation_revision_id", "rows"]
    assert [r["kind"] for r in body["health"]["rows"]] == ["BACKUP_GENERATOR", "COOLING_PLANT",
                                                            "TEMPERATURE_SENSING"]
    assert all(tuple(r) == HEALTH_ROW_KEYS for r in body["health"]["rows"])


@needs_db
def test_health_failed_start_and_probe(chain) -> None:  # noqa: F811
    built = opened("backup-failed", chain)
    run(built)
    c = client(built)
    body = get(c, W, route="health")
    assert_health_head(body)
    assert body["schema_version"] == "cold-depth-1" and body["site_id"] == str(built.site_id)
    mark = watermark(built)
    assert body["window"]["known_at"] == body["window"]["committed_watermark"] == mark
    assert_exact_selection(built, body)
    foundation = str(built.run.registered_basis.foundation_revision_id).lower()
    assert body["health"]["foundation_revision_id"] == foundation
    assets = foundation_assets(built, foundation)
    gen, plant, sensing = body["health"]["rows"]
    # Generator: the stored START result's failed-chain OBSERVED request/result/generator IDs, ledger-present.
    [start] = [r for r in selected_revisions(built, body) if r["analytic_id"] == cold.START_RESPONSE_ANALYTIC]
    cited = [e for ch in start["result"]["chains"] if ch["result"] == "OBSERVED_FAILURE" for x in ch["steps"]
             if x["step"] in ("START_REQUEST", "START_RESULT", "GENERATOR") and x["state"] == "OBSERVED"
             for e in x["evidence_ids"]]
    ledger = rows(built, "SELECT id, role, source_id FROM accepted_evidence WHERE site_id = :s "
                         "AND id = ANY(CAST(:ids AS uuid[]))", ids=body["selection"]["accepted_evidence_ids"])
    present = {str(r["id"]).lower(): r for r in ledger}
    expected = _plain_ids(e for e in cited if str(e).lower() in present)
    assert expected
    assert (gen["condition_state"], gen["observation"], gen["limitation"]) == (
        "NEEDS_INVESTIGATION", "Automatic start failed", "Failed automatic start observed; part not diagnosed")
    assert gen["evidence_ids"] == expected
    assert [gen["asset_id"]] == [str(start["result"]["policy"]["generator_asset_id"]).lower()] == \
        assets["GENERATOR"]
    assert gen["next_evidence"] == "Witness an automatic-start test"
    # Cooling plant: condition unknown on the single compressor asset.
    assert (plant["condition_state"], plant["observation"]) == ("UNKNOWN", "Condition unknown")
    assert [plant["asset_id"]] == [a["asset_id"] for a in plant["assets"]] == assets["COMPRESSOR"]
    assert set(plant["evidence_ids"]) <= set(present)
    # Temperature sensing: one distinct accepted probe source is LIMITED.
    assert (sensing["condition_state"], sensing["observation"], sensing["limitation"]) == (
        "LIMITED", "Single-point observation", "One accepted probe does not establish room-wide coverage")
    assert sensing["evidence_ids"] and set(sensing["evidence_ids"]) <= set(present)
    assert {present[i]["role"] for i in sensing["evidence_ids"]} == {cold.PROBE_ROLE}
    assert len({present[i]["source_id"] for i in sensing["evidence_ids"]}) == 1
    # The Foundation declares two probes (chamber and ambient); the selected excursion policy names the asset.
    [exc] = [r for r in selected_revisions(built, body) if r["analytic_id"] == cold.EXCURSION_ANALYTIC]
    assert [a["asset_id"] for a in sensing["assets"]] == assets["TEMPERATURE_PROBE"]
    assert sensing["asset_id"] == str(exc["result"]["policy"]["probe_asset_id"]).lower()
    assert sensing["asset_id"] in assets["TEMPERATURE_PROBE"]
    # Site-code links preserving from/to/known_at.
    for row, suffix in ((gen, "backup-chain"), (plant, "cooling"), (sensing, "evidence")):
        href = row["link"].replace("%3A", ":")
        assert href.startswith(f"/api/sites/{CODE}/cold/{suffix}?from=2026-10-06T19:00:00.000000Z")
        assert f"known_at={mark}" in href and str(built.site_id) not in href
    assert body["links"]["backup"] == gen["link"] and body["links"]["evidence"] == sensing["link"]
    # Wrong Site, foreign tenant, disclosure, down store, future known_at.
    assert c.get(f"/api/sites/OTHER/cold/health?{W}").status_code == 404
    foreign = get(client(built, tenant=uuid4()), W, route="health")
    assert foreign["health"]["foundation_revision_id"] is None
    assert all((r["condition_state"], r["asset_id"], r["evidence_ids"]) == ("UNKNOWN", None, [])
               for r in foreign["health"]["rows"])
    assert error(client(built, disclosure=lambda code, t, s: False), W, 403, "health") == \
        "COLD_SOURCE_DISCLOSURE_FORBIDDEN"
    assert error(client(built, url=DOWN), W, 503, "health") == "COLD_READ_UNAVAILABLE"
    assert error(c, f"{W}&known_at=2999-01-01T00:00:00Z", 422, "health") == "COLD_TIME_INVALID"


@needs_db
def test_health_not_configured(chain) -> None:  # noqa: F811
    built = opened("normal", chain)  # no run: no selection
    c = client(built)
    first = get(c, W, route="health")
    assert_health_head(first)
    assert first["selection"]["assessment_revision_ids"] == []
    original = str(built.run.registered_basis.foundation_revision_id).lower()
    assert first["health"]["foundation_revision_id"] == original
    assets = foundation_assets(built, original)
    gen, plant, sensing = first["health"]["rows"]
    assert [r["condition_state"] for r in first["health"]["rows"]] == ["UNKNOWN", "UNKNOWN", "UNKNOWN"]
    assert [gen["asset_id"]] == assets["GENERATOR"] and [plant["asset_id"]] == assets["COMPRESSOR"]
    # Q13: no selection, two probes declared; the topology's SIGNAL edge from the COLD_ROOM names `probe-1`.
    assert [a["asset_id"] for a in sensing["assets"]] == assets["TEMPERATURE_PROBE"]
    assert [a["asset_code"] for a in sensing["assets"]] == ["ambient-1", "probe-1"]
    probe_1 = next(a["asset_id"] for a in sensing["assets"] if a["asset_code"] == "probe-1")
    assert sensing["asset_id"] == probe_1
    [orig] = rows(built, "SELECT * FROM foundation_revision WHERE site_id = :s AND id = CAST(:f AS uuid)",
                  f=original)
    [top] = rows(built, "SELECT max(version) AS v FROM foundation_revision WHERE site_id = :s")
    content = {k: v for k, v in orig["content"].items() if k != "topology"}
    content["components"] = [x for x in content["components"]
                             if x["component_type"] not in ("GENERATOR", "COMPRESSOR", "TEMPERATURE_PROBE")]
    new_id = uuid4()
    with built.engine.begin() as conn:
        at = conn.execute(text("SELECT CAST(:r AS timestamptz) + interval '1 microsecond'"),
                          {"r": orig["recorded_at"]}).scalar_one()
        assert at <= _instant(first["window"]["committed_watermark"])
        conn.execute(text("UPDATE foundation_revision SET superseded_at = :at WHERE id = :orig"),
                     {"at": at, "orig": orig["id"]})
        conn.execute(text(
            "INSERT INTO foundation_revision (id, tenant_id, site_id, version, valid_from, valid_to, recorded_at, "
            "superseded_at, schema_version, content, content_sha256, origin, derived_from_revision_id, change_note) "
            "VALUES (:id, :t, :s, :v, :vf, :vt, :at, NULL, :sv, CAST(:content AS jsonb), :sha, 'PUBLISH', :orig, "
            ":note)"),
            {"id": new_id, "t": orig["tenant_id"], "s": orig["site_id"], "v": top["v"] + 1,
             "vf": orig["valid_from"], "vt": orig["valid_to"], "at": at, "sv": orig["schema_version"],
             "content": json.dumps(content), "sha": hashlib.sha256(canonical_json(content).encode()).hexdigest(),
             "orig": orig["id"], "note": "W5-01 C1 test-scoped Foundation without health assets"})
    second = get(c, W, route="health")
    assert_health_head(second)
    assert second["health"]["foundation_revision_id"] == str(new_id)
    literals = [("Not configured", "No backup generator is declared in the selected Foundation"),
                ("Not configured", "No cooling plant is declared in the selected Foundation"),
                ("Not configured", "No temperature probe is declared in the selected Foundation")]
    assert [(r["observation"], r["limitation"]) for r in second["health"]["rows"]] == literals
    assert all((r["condition_state"], r["asset_id"], r["assets"], r["evidence_ids"], r["link"]) ==
               ("NOT_CONFIGURED", None, [], [], None) for r in second["health"]["rows"])
