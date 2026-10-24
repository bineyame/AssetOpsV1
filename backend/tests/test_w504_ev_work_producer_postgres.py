"""W5-04a V1b: fixture tests of the EV work walkthrough's native path (readiness rulings 34-37).

Ruling 36: the walkthrough child's `native_replay` runs the registered, unmodified `ev-interrupted` replay at
EV-LAB-001 over E through the existing gateway/central/Chain helpers; K0 and every ID then come from product reads.
These tests drive that child path in-process against `ASSETOPS_TEST_DATABASE_URL`: the native replay (gateway
stopped afterwards), the K0/window refusals, the positive Action/intent at current DB time listed under W, the
submitted INC/WR/record/links with the enforced clock order, and `drop` cleaning only owned processes and DBs.
"""

from __future__ import annotations

import json
import subprocess
import sys
import uuid
from datetime import timedelta
from pathlib import Path

import pytest

from test_s4_finding_store_postgres import URL

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import w504_ev_work_cases as P  # noqa: E402
import w504_ev_work_walkthrough as walk  # noqa: E402


@pytest.fixture()
def replayed(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", URL)
    return walk.native_replay(P.POSITIVE_SCENARIO, tmp_path / "chain", fresh=True)


def test_native_replay_and_k0_refusals(replayed) -> None:
    """The registered case, Site and E window with accepted envelopes; the replay gateway is stopped; K0 is the
    returned scenarios watermark equal to the sessions cutoff, and a disagreeing window or clock refuses."""
    assert (replayed["scenario_id"], replayed["case"], replayed["site_code"]) == (
        "ev-interrupted", "interrupted", "EV-LAB-001")
    assert replayed["evidence_window"] == {"from": "2026-10-06T08:00:00Z", "to": "2026-10-06T09:00:00Z"}
    assert replayed["dispositions"].get("ACCEPTED", 0) > 0 and replayed["worker_outcomes"] > 0
    assert not walk.pid_alive(replayed["gateway_pid"]), "the replay gateway outlived the child"
    app, _ = walk._clients(URL)
    get = walk._getter(app)
    selected = P.read_k0(get, P.SITE_CODE, P.E_START, P.E_END)
    _, scenarios = get(f"/api/sites/{P.SITE_CODE}/ev/financials/scenarios", walk._bounds(P.E_START, P.E_END))
    assert selected.k0 == P.instant(scenarios["window"]["committed_watermark"])
    assert P.E_END <= selected.k0, "evidence decided before the window closed"

    def tampered(field: str, value: str):
        def read(path, params):
            status, body = get(path, params)
            if path.endswith("/ev/sessions"):
                body = {**body, "window": {**body["window"], field: value}}
            return status, body
        return read

    later = P.iso(selected.k0 + timedelta(seconds=1))
    for field, value in (("known_at", later), ("to", later), ("from", P.iso(P.E_START - timedelta(hours=1)))):
        with pytest.raises(P.ProducerRefused):
            P.read_k0(tampered(field, value), P.SITE_CODE, P.E_START, P.E_END)


def test_declare_and_attest_use_current_work_window(replayed, tmp_path) -> None:
    """Ruling 35/37: the Action is raised at current DB time after K0, W is the current DB day containing K1, and the
    submitted INC/WR/record and links keep `K0 < K1 <= K2 <= K3 <= K4`, with every row listed under W and the WR
    narrative exactly the ruled literal."""
    built = walk._declare(URL, "positive", "fx", replayed)
    assert built["status"] == "ready"
    k0, k1 = P.instant(built["clocks"]["K0"]), P.instant(built["clocks"]["K1"])
    db_now = walk._db_now(URL)
    assert k0 < k1 <= db_now and db_now - k1 < timedelta(minutes=5)
    assert P.instant(built["action_posted"]["raised_at"]) > k0 + timedelta(days=1)  # not a 2026-10-06 work item
    w = built["work_window_W"]
    assert P.instant(w["from"]) <= k1 < P.instant(w["to"]) and built["evidence_window_E"]["from"] == P.iso(P.E_START)
    assert built["intent_posted"]["basis"]["finding_revision_id"] == built["selection"]["finding_revision_id"]
    assert (built["action_posted"]["title"], built["action_posted"]["owner_label"]) == (
        "Investigate connector 2", "Charging operations")
    submitted = walk._attest(URL, "fx", built)
    assert submitted["wr_narrative"] == "Inspect connector and witness a charging session"
    assert submitted["posted"]["request"]["narrative"] == "Inspect connector and witness a charging session"
    order = [x.split("=")[0] for x in submitted["clocks"]["order"]]
    assert order[:3] == ["K0", "K1", "K2"] and order.count("K3") == 3 and order.count("K4") == 2
    sw = submitted["work_window_W"]
    for name, at in sw["contains"].items():
        assert P.instant(sw["from"]) <= P.instant(at) < P.instant(sw["to"]), name


def test_worstcase_adds_four_long_actions_through_the_public_routes(replayed) -> None:
    """W5-04 V2b (re-review M1): the walkthrough `worstcase` mode posts ACT-000002..5 with 160-code-point title and
    owner and their intents after the declared Action, and the Work window W lists all five."""
    built = walk._declare(URL, "worstcase", "fx", replayed)
    worst = walk._worstcase(URL, "fx", built)
    assert [r["action_code"] for r in worst["actions"]] == ["ACT-000002", "ACT-000003", "ACT-000004", "ACT-000005"]
    assert all(r["title_code_points"] == r["owner_code_points"] == 160 and r["intent_id"] for r in worst["actions"])
    assert worst["index_total_count"] == 5
    assert walk.DB_MODES == ("positive", "zero", "worstcase", "unknown") and walk.PORTS["worstcase"] == 8983


def test_drop_stops_only_recorded_pids_and_drops_only_marker_dbs() -> None:
    """Cleanup of owned processes/DB: a recorded child PID is stopped and a marker-listed `w504a_*_test` DB dropped;
    a marker entry that is not a `w504a_*_test` name is never dropped."""
    import psycopg

    tag = uuid.uuid4().hex[:8]
    work = ROOT / "var" / f"w504a_fx_{tag}"
    w = walk.Walk(str(work), tag)
    db = f"w504a_fx_{tag}_test"
    with psycopg.connect(walk.PG_ADMIN, autocommit=True) as c:
        c.execute(f"CREATE DATABASE {db}")
    # A recorded server looks like ours (review L6: a PID is killed only while its command line matches); a second
    # recorded PID is an unrelated process (PID reuse) and must survive `drop`.
    ours = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(120)", "uvicorn", "serve_entry:app",
                             "--port", "55999"])
    sleeper = ours
    unrelated = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(120)"])
    try:
        work.mkdir(parents=True)
        (work / walk.MARKER).write_text(json.dumps({"tool": "w504a", "dbs": [db, "assetops_not_owned"]}),
                                        encoding="utf-8")
        (work / "pids.json").write_text(json.dumps({"api": {"pid": ours.pid, "port": 55999},
                                                              "reused": {"pid": unrelated.pid, "port": 55999}}), encoding="utf-8")
        assert w.drop() == 0
        ours.wait(timeout=30)
        assert ours.returncode is not None
        assert unrelated.poll() is None and walk.pid_alive(unrelated.pid), "drop killed an unrelated reused PID"
        with psycopg.connect(walk.PG_ADMIN, autocommit=True) as c:
            left = c.execute("SELECT datname FROM pg_database WHERE datname = %s", (db,)).fetchall()
        assert left == [] and not work.exists()
    finally:
        for process in (ours, unrelated):
            if process.poll() is None:
                process.kill()
        with psycopg.connect(walk.PG_ADMIN, autocommit=True) as c:
            c.execute(f"DROP DATABASE IF EXISTS {db} WITH (FORCE)")
