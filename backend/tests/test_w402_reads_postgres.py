"""W4-02 unit 5: the historical mini-depth reads over Postgres (`D-2026-10-20-w4-02-buildspec` closure 1 Q4, Q6,
Q7, Q14, Q18, Q31; q6 rulings 1 and 5).

The authored MG-W402-001 cases are accepted in process, selected by the worker's explicit `reconcile` backfill, and
read through `MiniDepthRead` (and once through the router). No read writes: the stored revision JSON is compared
before and after the stale case.
"""

from __future__ import annotations

import json
import os
from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import UUID

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from sqlalchemy import text
    from test_s1_bindings_postgres import Clock, engine, store  # noqa: F401
    from test_s2_evidence_ledger_postgres import enable
    from test_w402_authored_v4_postgres import cases, ingestion, install, principal, snapshot

    from assetops_backend.evidence.adapters.postgres_evidence_ledger import link_rows_on
    from assetops_backend.mini_depth import projection
    from assetops_backend.mini_depth.inputs import load_hour_inputs, local_noon
    from assetops_backend.mini_depth.read import MiniDepthRead, MiniReadRefused
    from assetops_backend.mini_depth.store import PostgresMiniDepthStore
    from assetops_backend.mini_depth.worker import MiniDepthWorker
    from assetops_backend.mini_depth_api import build_mini_depth_router

ZONE = "Africa/Nairobi"
CODE = "MG-W402-001"
DAYS = [date(2026, 10, d) for d in range(6, 11)]


def _midnight(day: date) -> datetime:
    return datetime(day.year, day.month, day.day, tzinfo=timezone.utc) - timedelta(hours=3)  # Nairobi is UTC+3


def _ingest(engine, installed, variants=("positive",)) -> None:
    doc, sha = snapshot(engine, installed.binding_set.id)
    spec, service = cases.load_spec(), ingestion()
    for variant in variants:
        for b in cases.build_batches(spec, doc, sha, variant):
            service.submit(principal(doc), b.body.encode("utf-8"))


def _reconcile(engine, days) -> None:
    worker = MiniDepthWorker(None, PostgresMiniDepthStore(engine))
    for day in days:
        noon = local_noon(day, ZONE)
        assert all(o.status == "DONE" for o in worker.reconcile(CODE, noon.start, noon.end))


def _setup(store, engine):
    installed = install(store)
    enable(engine, installed.result.site.id)
    return installed, installed.result.site.tenant_id, installed.result.site.id


def _read(engine, t, s, domain, lo, hi, known_at=None, **options):
    reader = MiniDepthRead(engine, link_rows_on, **options)
    return reader.read(tenant_id=t, site_id=s, site_code=CODE, domain=domain, lo=lo, hi=hi, known_at=known_at)


def test_renewable_composes_five_selected_days(store, engine) -> None:
    installed, t, s = _setup(store, engine)
    _ingest(engine, installed)
    _reconcile(engine, DAYS)
    body = _read(engine, t, s, "renewable", _midnight(DAYS[0]), _midnight(DAYS[-1] + timedelta(days=1)))
    windows = body["currentness"]["windows"]
    # q9 ruling 7: renewable has no top-level basis and no numeric retained margin anywhere in its wire.
    assert body["basis"] is None and "retained" not in json.dumps(body).lower()
    assert body["site"] == {"id": str(s), "code": CODE, "timezone": ZONE}
    assert [w["local_day"] for w in windows] == [d.isoformat() for d in DAYS]
    assert all(isinstance(w["selection_id"], int) and w["state"] == "CURRENT" for w in windows), windows
    assert body["currentness"]["state"] == "CURRENT" and body["currentness"]["job_state"] == "SETTLED"
    decisions = [r["decision"] for r in body["rows"]]
    assert len(decisions) == 5 and set(decisions) <= {"ELIGIBLE", "EXCLUDED"}, decisions
    assert body["cards"]["assessed_days"] == 5
    assert body["cards"]["eligible_days"] == decisions.count("ELIGIBLE")
    selected = body["selected_source_provenance"]
    assert body["source_provenance"] == selected and body["pending_source_provenance"] is None
    assert selected["basis_sha256"].startswith("sha256:") and selected["evidence_ids"]
    assert "detail" not in selected
    if selected["classification"] in ("UNKNOWN", "MIXED"):
        assert body["status"] == "LIMITED"
        assert f"SOURCE_CLASS_{selected['classification']}" in [x["code"] for x in body["limitations"]]
    else:
        assert body["status"] == "SUPPORTED"

    # Replace one day's selection with a LIMITED hour (a later cutoff, so a new revision): the page is LIMITED.
    mini = PostgresMiniDepthStore(engine)
    with mini.snapshot() as c:
        inputs = load_hour_inputs(c, t, s, local_noon(DAYS[2], ZONE), mini.clock(c))
        revision = projection.project("renewable", inputs)
        result = dict(revision.result)
        result["hour"] = {**result["hour"], "decision": "LIMITED"}
        result["rows"] = [{**r, "decision": "LIMITED", "constraints": ["COVERAGE_GAP"], "opportunity_kwh": None}
                          for r in result["rows"]]
        mini.append_selection(replace(revision, result=result), job_id=None, backfill=True, connection=c)
    limited = _read(engine, t, s, "renewable", _midnight(DAYS[0]), _midnight(DAYS[-1] + timedelta(days=1)))
    assert limited["status"] == "LIMITED" and limited["cards"]["assessed_days"] == 4
    assert "COVERAGE_GAP" in [x["code"] for x in limited["limitations"]]

    # A requested day without any selection: UNKNOWN, with no five-day recurrence denominator.
    missing = _read(engine, t, s, "renewable", _midnight(DAYS[1]), _midnight(DAYS[-1] + timedelta(days=2)))
    assert missing["status"] == "UNKNOWN" and missing["currentness"]["state"] == "UNKNOWN"
    last = missing["currentness"]["windows"][-1]
    assert last["local_day"] == "2026-10-11" and last["selection_id"] is None and last["state"] == "UNKNOWN"
    assert len(missing["rows"]) == 4 and missing["cards"]["assessed_days"] == 3


def test_published_authored_batches_select_authored_demonstration(store, engine, tmp_path, capsys) -> None:  # noqa: F811
    """Final review L3: every exact authored Batch V2 of the positive variant is registered and published with the
    server-side authored-publication command (fixture `assetops.w4-mini-depth-cases` v1) before it is ingested. The
    selected public reads are then classified `AUTHORED_DEMONSTRATION` and, jointly, keep their positive claims:
    the Service hour SUPPORTED and the Renewable five days SUPPORTED with at least one ELIGIBLE day."""
    from assetops_backend.evidence.adapters.postgres_evidence_ledger import PostgresEvidenceLedger
    from assetops_backend.evidence.composition import build_authored_fixture_specs
    from assetops_backend.publish_source import main as publish_source_main

    installed, t, s = _setup(store, engine)
    doc, sha = snapshot(engine, installed.binding_set.id)
    spec, service, specs = cases.load_spec(), ingestion(), build_authored_fixture_specs()
    batches = cases.build_batches(spec, doc, sha, "positive")
    assert batches
    for i, b in enumerate(batches):
        path = tmp_path / f"batch-{i}.json"
        path.write_text(b.body, encoding="utf-8")
        args = ["--site", CODE, "--fixture-id", "assetops.w4-mini-depth-cases", "--fixture-version", "1",
                "--batch-file", str(path)]
        assert publish_source_main(args, ledger=PostgresEvidenceLedger(URL), specs=specs) == 0
        assert " published: publication " in capsys.readouterr().out
        service.submit(principal(doc), b.body.encode("utf-8"))
    with engine.connect() as c:
        assert c.execute(text("SELECT count(*) FROM evidence_publication WHERE site_id = :s"),
                         {"s": s}).scalar_one() == len(batches)
    _reconcile(engine, DAYS)

    renewable = _read(engine, t, s, "renewable", _midnight(DAYS[0]), _midnight(DAYS[-1] + timedelta(days=1)))
    assert renewable["selected_source_provenance"]["classification"] == "AUTHORED_DEMONSTRATION"
    assert renewable["source_provenance"]["classification"] == "AUTHORED_DEMONSTRATION"
    assert renewable["status"] == "SUPPORTED" and renewable["currentness"]["state"] == "CURRENT"
    assert renewable["cards"]["eligible_days"] >= 1 and "ELIGIBLE" in [r["decision"] for r in renewable["rows"]]
    assert not [x for x in renewable["limitations"] if x["code"].startswith("SOURCE_CLASS_")]

    noon = local_noon(DAYS[2], ZONE)
    supported = _read(engine, t, s, "service", noon.start, noon.end)
    assert supported["selected_source_provenance"]["classification"] == "AUTHORED_DEMONSTRATION"
    assert supported["status"] == "SUPPORTED" and supported["currentness"]["state"] == "CURRENT"
    assert not [x for x in supported["limitations"] if x["code"].startswith("SOURCE_CLASS_")]


def test_stale_pending_and_historical_currentness(store, engine) -> None:
    installed, t, s = _setup(store, engine)
    day = DAYS[1]
    noon = local_noon(day, ZONE)
    _reconcile(engine, [day])  # selected before any evidence exists
    before = _read(engine, t, s, "service", noon.start, noon.end)
    assert before["currentness"]["state"] == "CURRENT" and before["status"] == "UNKNOWN"
    assert before["source_provenance"]["basis_sha256"] is not None  # an empty cited set, but a selected revision
    with engine.connect() as c:
        stored = c.execute(text("SELECT result FROM mini_depth_revision WHERE id = :r"),
                           {"r": UUID(before["currentness"]["windows"][0]["assessment_revision_id"])}).scalar_one()

    # q6 ruling 5: newly eligible accepted rows make the old selection read STALE_SOURCE; its JSON is unchanged.
    _ingest(engine, installed)
    stale = _read(engine, t, s, "service", noon.start, noon.end)
    assert stale["currentness"]["state"] == "STALE_SOURCE"
    assert stale["currentness"]["windows"][0]["selection_id"] == before["currentness"]["windows"][0]["selection_id"]
    assert "SOURCE_STALE" in [x["code"] for x in stale["limitations"]] and stale["status"] != "SUPPORTED"
    with engine.connect() as c:
        assert c.execute(text("SELECT result FROM mini_depth_revision WHERE id = :r"),
                         {"r": UUID(before["currentness"]["windows"][0]["assessment_revision_id"])}
                         ).scalar_one() == stored

    # Reselection clears it; a later live job makes it PENDING_RECOMPUTE with a pending provenance block.
    _reconcile(engine, [day])
    current = _read(engine, t, s, "service", noon.start, noon.end)
    assert current["currentness"]["state"] == "CURRENT" and current["rows"]
    with engine.begin() as c:
        c.execute(text("SELECT mini_enqueue_hour(:t, :s, 'mini_service', :lo, :hi, NULL, clock_timestamp())"),
                  {"t": t, "s": s, "lo": noon.start, "hi": noon.end})
    pending = _read(engine, t, s, "service", noon.start, noon.end)
    assert pending["currentness"]["state"] == "PENDING_RECOMPUTE"
    assert pending["currentness"]["job_state"] == "PENDING"
    assert pending["pending_source_provenance"]["basis_sha256"] is None
    assert pending["source_provenance"] == pending["pending_source_provenance"]
    assert pending["selected_source_provenance"] == current["selected_source_provenance"]
    assert "RECOMPUTE_PENDING" in [x["code"] for x in pending["limitations"]]

    # Q14/Q31: the head at an explicit cutoff, the equality boundary and a future cutoff.
    with engine.connect() as c:
        selected_at, cutoff = c.execute(text(
            "SELECT s.selected_at, r.knowledge_cutoff FROM mini_depth_selection s JOIN mini_depth_revision r "
            "ON r.id = s.revision_id WHERE s.seq = :q"),
            {"q": current["currentness"]["windows"][0]["selection_id"]}).one()
    historical = _read(engine, t, s, "service", noon.start, noon.end, known_at=selected_at)
    assert historical["currentness"]["state"] == "HISTORICAL"
    assert historical["currentness"]["windows"][0]["selection_id"] == current["currentness"]["windows"][0][
        "selection_id"]
    equal = _read(engine, t, s, "service", noon.start, noon.end, known_at=selected_at,
                  test_read_clock_override=lambda: selected_at)
    assert equal["currentness"]["state"] == "CURRENT"
    earlier = _read(engine, t, s, "service", noon.start, noon.end, known_at=cutoff - timedelta(microseconds=1))
    assert earlier["currentness"]["windows"][0]["selection_id"] != current["currentness"]["windows"][0][
        "selection_id"]
    with pytest.raises(MiniReadRefused) as refused:
        _read(engine, t, s, "service", noon.start, noon.end, known_at=selected_at + timedelta(microseconds=1),
              test_read_clock_override=lambda: selected_at)
    assert refused.value.code == "INVALID_KNOWN_AT"


def test_router_reads_minigrid_and_refuses_windows(store, engine) -> None:
    installed, t, s = _setup(store, engine)
    _ingest(engine, installed)
    _reconcile(engine, [DAYS[2]])
    site = SimpleNamespace(id=s, site_code=CODE, site_type="MINIGRID", timezone=ZONE)
    registry = SimpleNamespace(tenant=lambda: SimpleNamespace(id=t),
                               imported=lambda code: site if code.lower() == CODE.lower() else None)
    app = FastAPI()
    app.include_router(build_mini_depth_router(MiniDepthRead(engine, link_rows_on), registry))  # type: ignore[arg-type]
    client = TestClient(app)
    noon = local_noon(DAYS[2], ZONE)
    z = lambda at: at.strftime("%Y-%m-%dT%H:%M:%S.%fZ")  # noqa: E731
    for domain in ("service", "fuel", "backup"):
        response = client.get(f"/api/sites/{CODE}/performance/mini/{domain}",
                              params={"from": z(noon.start), "to": z(noon.end)})
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["domain"] == domain and body["currentness"]["windows"][0]["selection_id"] is not None
        assert body["window"]["from"] == z(noon.start) and body["links"]["evidence"] == f"/sites/{CODE}/evidence"
        assert body["basis"] is not None and body["links"]["actions"] == "/actions"
        assert body["links"]["dispatch"] == f"/sites/{CODE}/performance/dispatch?day={noon.start.date().isoformat()}"
    fuel = client.get(f"/api/sites/{CODE}/performance/mini/fuel",
                      params={"from": z(noon.start), "to": z(noon.end)}).json()
    assert [r["term"] for r in fuel["rows"]] == ["OPENING", "DELIVERIES", "USE", "CLOSING", "RESIDUAL"]
    assert fuel["cards"]["residual_l"] is None and fuel["basis"]["generator_power_evidence_ids"] is not None
    offset = noon.start.astimezone(timezone(timedelta(hours=3))).isoformat()
    assert client.get(f"/api/sites/{CODE}/performance/mini/service",
                      params={"from": offset, "to": z(noon.end)}).status_code == 200
    bad = [("service", noon.start + timedelta(minutes=30), noon.end + timedelta(minutes=30)),
           ("service", noon.start, noon.end + timedelta(hours=1)),
           ("renewable", noon.start, noon.end),
           ("renewable", _midnight(DAYS[0]), _midnight(DAYS[0] + timedelta(days=6)))]
    for domain, lo, hi in bad:
        response = client.get(f"/api/sites/{CODE}/performance/mini/{domain}", params={"from": z(lo), "to": z(hi)})
        assert response.status_code == 422 and response.json()["detail"]["code"] == "INVALID_WINDOW", (domain, lo)
    future = client.get(f"/api/sites/{CODE}/performance/mini/service",
                        params={"from": z(noon.start), "to": z(noon.end), "known_at": "2999-01-01T00:00:00Z"})
    assert future.status_code == 422 and future.json()["detail"]["code"] == "INVALID_KNOWN_AT"


def _replica(engine, *statements, **params) -> None:
    """Test-only configuration edits: the replica role skips the append-only and enqueue triggers, so a read sees a
    changed basis with no recompute work (q9 ruling 3)."""
    with engine.begin() as c:
        c.execute(text("SET LOCAL session_replication_role = replica"))
        for sql in statements:
            c.execute(text(sql), params)


def _counts(engine, s) -> tuple:
    with engine.connect() as c:
        return tuple(c.execute(text(f"SELECT count(*) FROM {table} WHERE site_id = :s"), {"s": s}).scalar_one()
                     for table in ("mini_depth_revision", "mini_depth_selection", "mini_depth_revision_evidence",
                                   "recompute_job"))


def _now(engine):
    with engine.connect() as c:
        return c.execute(text("SELECT clock_timestamp()")).scalar_one()


def test_q9_2_cutoff_visible_jobs(store, engine) -> None:
    installed, t, s = _setup(store, engine)
    _ingest(engine, installed)
    day, other = DAYS[1], DAYS[3]
    noon = local_noon(day, ZONE)
    _reconcile(engine, [day])
    p = {"t": t, "s": s, "lo": noon.start, "hi": noon.end}
    enqueue = text("SELECT mini_enqueue_hour(:t, :s, 'mini_service', :lo, :hi, NULL, clock_timestamp())")
    with engine.begin() as c:
        c.execute(enqueue, p)
    job = text("SELECT available_at FROM recompute_job WHERE site_id = :s AND domain = 'mini_service' "
               "AND window_start = :lo AND status = 'PENDING'")
    with engine.connect() as c:
        t1 = c.execute(job, p).scalar_one()
    equal = _read(engine, t, s, "service", noon.start, noon.end, known_at=t1)
    assert equal["currentness"]["state"] == "PENDING_RECOMPUTE" and equal["currentness"]["job_state"] == "PENDING"
    before = _read(engine, t, s, "service", noon.start, noon.end, known_at=t1 - timedelta(microseconds=1))
    assert before["currentness"]["state"] == "HISTORICAL" and before["currentness"]["job_state"] == "SETTLED"

    # Lifting the old PENDING row's `available_at` past k makes it invisible at k (not `created_at <= k`).
    with engine.begin() as c:
        c.execute(enqueue, p)
    with engine.connect() as c:
        t2 = c.execute(job, p).scalar_one()
    assert t2 > t1
    lifted = _read(engine, t, s, "service", noon.start, noon.end, known_at=t1)
    assert lifted["currentness"]["state"] == "HISTORICAL" and lifted["currentness"]["job_state"] == "SETTLED"
    assert _read(engine, t, s, "service", noon.start, noon.end)["currentness"]["job_state"] == "PENDING"

    # Another hour's selection does not clear it; a later selection of that exact hour does.
    _reconcile(engine, [other])
    assert _read(engine, t, s, "service", noon.start, noon.end)["currentness"]["state"] == "PENDING_RECOMPUTE"
    _reconcile(engine, [day])
    cleared = _read(engine, t, s, "service", noon.start, noon.end)
    assert cleared["currentness"]["state"] == "CURRENT" and cleared["currentness"]["job_state"] == "SETTLED"
    assert cleared["pending_source_provenance"] is None


def test_q9_3_read_only_stale_source(store, engine) -> None:
    installed, t, s = _setup(store, engine)
    _ingest(engine, installed)
    noon = local_noon(DAYS[1], ZONE)
    _reconcile(engine, [DAYS[1]])
    assert _read(engine, t, s, "service", noon.start, noon.end)["currentness"]["state"] == "CURRENT"
    k0, counts = _now(engine), _counts(engine, s)
    f = {"s": s}

    def state(known_at=None) -> str:
        body = _read(engine, t, s, "service", noon.start, noon.end, known_at=known_at)
        if body["currentness"]["state"] == "STALE_SOURCE":
            assert body["status"] != "SUPPORTED" and "SOURCE_STALE" in [x["code"] for x in body["limitations"]]
        return body["currentness"]["state"]

    # An ambiguous covering Foundation (two visible at the cutoff) reads STALE_SOURCE; the old cutoff is unchanged.
    _replica(engine, "CREATE TEMP TABLE f_copy ON COMMIT DROP AS SELECT * FROM foundation_revision "
                     "WHERE site_id = :s AND superseded_at IS NULL",
             "UPDATE f_copy SET id = gen_random_uuid(), version = version + 1000, recorded_at = clock_timestamp(), "
             "superseded_at = '2999-01-01Z', origin = 'PUBLISH'",
             "INSERT INTO foundation_revision SELECT * FROM f_copy", **f)
    assert state() == "STALE_SOURCE" and state(k0) == "HISTORICAL"
    assert _counts(engine, s) == counts

    # A changed Foundation (one covering revision, a different ID) reads STALE_SOURCE.
    _replica(engine, "UPDATE foundation_revision SET superseded_at = clock_timestamp() WHERE site_id = :s "
                     "AND superseded_at IS NULL",
             "UPDATE foundation_revision SET superseded_at = NULL WHERE site_id = :s "
             "AND superseded_at = '2999-01-01Z'", **f)
    assert state() == "STALE_SOURCE" and state(k0) == "HISTORICAL"
    assert _counts(engine, s) == counts

    # A missing covering binding set (configuration no longer yields one basis) reads STALE_SOURCE.
    _replica(engine, "UPDATE signal_binding_set_revision SET superseded_at = clock_timestamp() WHERE site_id = :s "
                     "AND superseded_at IS NULL", **f)
    assert state() == "STALE_SOURCE" and state(k0) == "HISTORICAL"
    assert _counts(engine, s) == counts
