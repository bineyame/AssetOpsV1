"""OUT-B4 (B.7 #2, #3 as amended by addendum 4 #1; B.7 #4): the Site outcome board on the real producer fixtures.

- Kobo: the s602b `guardrail` case (`tools/s602b_test_scoped_cases.py build`, S4 F01/F02 + the S6-02a evaluator
  builders), served like its `pinned_app` (Action clock and estate read time pinned at the case's `pinned_at`, the
  same authored-window fakes). Day A 2026-10-06: F01 MOVES on Cost, checked as a safeguard on Protect, Cost
  NEEDS_ATTENTION, `must_not_harm` null. Day B 2026-11-02: the ACT-048 Must-not-harm line and verification link,
  ACT-048 on the Cost row, no "outside this view" item. The real `site_work_rows` rows carry every key the B2 fake
  (`test_out_b2_mini.py` ESTATE_F104 / ESTATE_A48) assumes.
- Cold: the w502 `positive` producer (`tools/w502_cold_work_walkthrough.py` BUILD child) over its work window.
- EV: the w504 `positive` case (`native_replay` + `_declare`, as `test_w504_ev_work_producer_postgres.py`).

Each build runs in this run's worker `*_test` database, re-cloned first. The Kobo and cold builders run as child
processes (as their walkthroughs do), with the run-routing variables stripped so they write that same database.
Row states are recorded in `ROW_STATES` and asserted against B.7 #2 where the ruling fixes them.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import pytest

import pg_harness
from test_s4_finding_store_postgres import URL

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

ROOT = Path(__file__).resolve().parents[2]
TESTS = ROOT / "backend" / "tests"
sys.path.insert(0, str(ROOT / "tools"))

FINDING_KEYS = {"finding_id", "finding_revision_id", "lifecycle", "source_provenance", "consequence", "_episode_end",
                "_mechanism"}
ACTION_KEYS = {"action_id", "source_finding_id", "source_finding_revision_id", "application_state",
               "resolution_state", "verification_outcome", "_raw"}
ACTION_RAW_KEYS = {"_selected_recorded_at", "_verification_window"}
SAFEGUARD = " · checked here as a safeguard"
OUTSIDE = " · linked finding outside this view"
MUST_NOT_HARM = ("Reliable service and battery and generator life are checked as safeguards when ACT-048 is "
                 "verified; a gain that harms them does not count")


def _child_env() -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if not k.startswith("ASSETOPS_TEST_")}
    parts = ["backend", "gateway", "simulator", "contracts", "host", "backend/tests"]
    env["PYTHONPATH"] = os.pathsep.join(str(ROOT / p) for p in parts)
    env["ASSETOPS_TEST_DATABASE_URL"] = env["DATABASE_URL"] = URL
    env["PYTHONUNBUFFERED"] = "1"
    return env


def _child(argv: list[str]) -> None:
    done = subprocess.run([sys.executable, *argv], cwd=str(TESTS), env=_child_env(), capture_output=True, text=True,
                          timeout=1800)
    assert done.returncode == 0, f"{argv[:2]} failed\n{done.stdout[-3000:]}\n{done.stderr[-3000:]}"


@pytest.fixture()
def app_env(monkeypatch):
    from assetops_backend.estate.scope import PORTFOLIO_CURSOR_KEY_ENV

    pg_harness.fresh_database()
    monkeypatch.setenv("DATABASE_URL", URL)
    monkeypatch.setenv(PORTFOLIO_CURSOR_KEY_ENV, "0" * 64)
    FAILURES.clear()
    _record_port_failures(monkeypatch)
    yield monkeypatch
    if FAILURES:
        print("\nOUT-B4 port failures:", json.dumps(sorted(set(FAILURES)), indent=1))


def _client():
    from fastapi.testclient import TestClient

    from assetops_backend.config import load_feature_flags
    from assetops_backend.main import create_app

    return TestClient(create_app(load_feature_flags()))


def _spy_work_rows(monkeypatch) -> list:
    from assetops_backend.estate.portfolio import EstatePortfolioService

    seen: list = []
    real = EstatePortfolioService.site_work_rows

    def spy(self, *a, **kw):
        out = real(self, *a, **kw)
        seen.append(out)
        return out

    monkeypatch.setattr(EstatePortfolioService, "site_work_rows", spy)
    return seen


FAILURES: list[str] = []


def _record_port_failures(monkeypatch) -> None:
    """Every refused or failed port with its error, into the printed record (the board itself only names it)."""
    from assetops_backend.site_outcomes import mini

    real = mini.Reads.call

    def call(self, name, fn, *args):
        try:
            return fn(*args)
        except Exception as error:  # noqa: BLE001 - recorded, then the real call's PARTIAL handling
            FAILURES.append(f"{name}: {type(error).__name__}: {str(error)[:200]}")
        return real(self, name, fn, *args)

    monkeypatch.setattr(mini.Reads, "call", call)


def _rows(body: dict) -> dict[str, dict]:
    return {r["category"]: r for r in body["rows"]}


def _items(row: dict) -> list[dict]:
    return [*row["issues"], *row["in_hand"], *row["earlier"], *row["options"]]


def _states(body: dict) -> list[str]:
    return [r["state"] for r in body["rows"]]


ROW_STATES: dict[str, object] = {}


def _pin_kobo(monkeypatch, spec: dict) -> None:
    """`tools/s602b_test_scoped_cases.pinned_app`, with monkeypatch so nothing leaks past this test."""
    import assetops_backend.actions.composition as composition
    import assetops_backend.main as main
    import test_s6_verification_evaluator_postgres as ev
    from assetops_backend.estate.adapters.postgres_estate_read import PostgresEstateRead
    from assetops_backend.estate.adapters.postgres_evidence_money_read import PostgresEvidenceMoneyRead

    pinned = datetime.fromisoformat(spec["pinned_at"])
    fake = spec["fake"]
    if fake is not None:
        class H:
            class service:
                verification_ports = None

        ev.complete_windows(monkeypatch, H, baseline_soc=fake["baseline_soc"], later_soc=fake["later_soc"],
                            inject=set(fake["inject"]))
        ports = H.service.verification_ports
        monkeypatch.setattr(composition, "verification_ports", lambda url: ports)
    real = main.build_action_service

    def pinned_service(*args, **kwargs):
        kwargs["clock"] = lambda: pinned
        return real(*args, **kwargs)

    monkeypatch.setattr(main, "build_action_service", pinned_service)
    for cls in (PostgresEstateRead, PostgresEvidenceMoneyRead):
        original = cls.__dict__["read"]

        def read(self, work, _original=original):
            def pinned_work(snap):
                snap.read_at = pinned
                return work(snap)

            return _original(self, pinned_work)

        monkeypatch.setattr(cls, "read", read)


def test_kobo_guardrail_two_board_days(app_env, tmp_path) -> None:
    monkeypatch = app_env
    # `build()` itself: the script's `main` refuses `*_test` only because it never resets one; this database was
    # re-cloned by `app_env`, so the builder writes into a fresh migrated copy.
    _child(["-c", "import sys; from pathlib import Path; sys.path.insert(0, sys.argv[3]); "
                  "import s602b_test_scoped_cases as s; s.build(sys.argv[1], Path(sys.argv[2]), 'guardrail')",
            URL, str(tmp_path), str(ROOT / "tools")])
    # the s602b walkthrough's step 5: the Performance comparison that releases the Finding reads, run in process
    # with its report in this test's folder, never the worktree's var/evidence (the w403 replay test pattern)
    from assetops_backend.evidence.adapters import json_evidence_store
    from assetops_backend.performance_migration import main as performance_migration

    monkeypatch.setattr(json_evidence_store, "EVIDENCE_STORE_ROOT", tmp_path / "evidence")
    assert performance_migration(["run", "--tenant", "demo", "--site", "KOBO-001"]) == 0
    spec = json.loads((tmp_path / "case-guardrail.json").read_text(encoding="utf-8"))
    _pin_kobo(monkeypatch, spec)
    seen = _spy_work_rows(monkeypatch)
    with _client() as c:
        a = c.get("/api/sites/KOBO-001/outcome-board?date=2026-10-06")
        started = time.perf_counter()
        b = c.get("/api/sites/KOBO-001/outcome-board?date=2026-11-02")
        ROW_STATES["kobo_day_b_seconds"] = round(time.perf_counter() - started, 2)
    assert a.status_code == 200, a.text
    assert b.status_code == 200, b.text
    a, b = a.json(), b.json()
    ROW_STATES["kobo_day_a"] = (a["read_state"], _states(a))
    ROW_STATES["kobo_day_b"] = (b["read_state"], _states(b))
    print("\nOUT-B4 row states:", json.dumps(ROW_STATES))

    # the real estate rows carry every key the B2 fake assumes (test_out_b2_mini.py ESTATE_F104 / ESTATE_A48)
    findings = [f for rows in seen if rows for f in rows["findings"]]
    actions = [x for rows in seen if rows for x in rows["actions"]]
    assert findings and actions, (len(findings), len(actions))
    for f in findings:
        assert FINDING_KEYS <= set(f), FINDING_KEYS - set(f)
    for x in actions:
        assert ACTION_KEYS <= set(x), ACTION_KEYS - set(x)
        assert ACTION_RAW_KEYS <= set(x["_raw"]), ACTION_RAW_KEYS - set(x["_raw"])

    # Day A (addendum 4 #1): F01 moves Cost and is checked on Protect; no Action yet, so no Must-not-harm line
    f01 = spec["findings"]["2026-10-06"]
    cost, protect = _rows(a)["OPTIMIZE_COST"], _rows(a)["PROTECT_ASSET"]
    moves = [i for i in cost["issues"] if i["role"] == "MOVES" and (i.get("ref") or {}).get("finding_id") == f01]
    assert moves, cost["issues"]
    checked = [i for i in protect["issues"] if (i.get("ref") or {}).get("finding_id") == f01]
    assert checked and all(i["text"].endswith(SAFEGUARD) for i in checked), protect["issues"]
    assert cost["state"] == "NEEDS_ATTENTION"
    assert cost["must_not_harm"] is None
    # B.7 #2 (Kobo pre-acceptance), on day A of the same case
    grow, _, protect_a, assure = _states(a)
    assert grow in ("OPPORTUNITY", "NO_OBJECTIVE") and (protect_a, assure) == ("NO_OBJECTIVE", "WATCH"), _states(a)

    # Day B: ACT-048's Must-not-harm line, its verification link, ACT-048 on Cost, nothing "outside this view"
    action_id = spec["action"]
    cost_b = _rows(b)["OPTIMIZE_COST"]
    assert cost_b["must_not_harm"]["text"] == MUST_NOT_HARM
    href = cost_b["must_not_harm"]["href"]
    assert href.startswith(f"/sites/KOBO-001/actions/{action_id}/verification?event_id="), href
    assert len(href.split("event_id=", 1)[1]) == 36, href
    act = [i for i in [*cost_b["in_hand"], *cost_b["earlier"]] if "ACT-048" in i["text"]]
    assert act, (cost_b["in_hand"], cost_b["earlier"])
    ROW_STATES["kobo_act048_column"] = "in_hand" if act[0] in cost_b["in_hand"] else "earlier"
    assert not [i for r in b["rows"] for i in _items(r) if i["text"].endswith(OUTSIDE)]
    if act[0] in cost_b["earlier"]:  # addendum 4 #1: the CHECKED safeguard Earlier entry on Protect
        assert any("ACT-048" in i["text"] for i in _rows(b)["PROTECT_ASSET"]["earlier"]), _rows(b)["PROTECT_ASSET"]
    print("OUT-B4 row states:", json.dumps(ROW_STATES))


def test_cold_w502_positive(app_env, tmp_path) -> None:
    import w502_cold_work_walkthrough as w502

    out = tmp_path / "positive"
    out.mkdir()
    _child(["-c", w502.BUILD, "positive", str(out)])
    doc = json.loads((out / "positive.json").read_text(encoding="utf-8"))
    assert doc["blocked"] is None, doc["blocked"]
    with _client() as c:
        r = c.get("/api/sites/COLD-LAB-001/outcome-board", params=doc["window"])
    assert r.status_code == 200, r.text
    body = r.json()
    ROW_STATES["cold"] = (body["read_state"], _states(body), body["window"])
    print("\nOUT-B4 row states:", json.dumps(ROW_STATES))
    grow, cost, protect, assure = _states(body)
    assert (grow, cost, protect) == ("NOT_MEASURED", "NOT_MEASURED", "NEEDS_ATTENTION"), _states(body)
    assert assure in ("WATCH", "NO_OBJECTIVE"), _states(body)
    # B.7 #4: the completed inspection is an Earlier intervention, not yet verified
    earlier = [i for r in body["rows"] for i in r["earlier"]]
    assert any(i.get("result_label") == "Not yet verified" for i in earlier), earlier
    assert body["window"]["known_at"] is not None  # addendum 4 #5: the overview's resolved cutoff


def test_ev_w504_positive(app_env, tmp_path) -> None:
    import w504_ev_work_cases as P
    import w504_ev_work_walkthrough as walk

    replayed = walk.native_replay(P.POSITIVE_SCENARIO, tmp_path / "chain", fresh=True)
    built = walk._declare(URL, "positive", "fx", replayed)
    assert built["status"] == "ready", built.get("status")
    window = {"from": built["evidence_window_E"]["from"], "to": built["evidence_window_E"]["to"]}
    with _client() as c:
        r = c.get("/api/sites/EV-LAB-001/outcome-board", params=window)
    assert r.status_code == 200, r.text
    body = r.json()
    ROW_STATES["ev"] = (body["read_state"], _states(body), body["window"])
    print("\nOUT-B4 row states:", json.dumps(ROW_STATES))
    assert _states(body) == ["WATCH", "NOT_MEASURED", "NEEDS_ATTENTION", "WATCH"], _states(body)
