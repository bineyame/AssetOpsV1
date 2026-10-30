"""OUT-B4 (B.7 #2, #3 as amended by addendum 4 #1; B.7 #4; addendum 5): the Site outcome board on the real producer
fixtures. Each case builds into its own `assetops_out_b_<x>_test` database (addendum 5 #2), dropped afterwards.

S2 comparison stood in for the test-scoped fixture, as `test_s5_overview_postgres`; not a migration result
(addendum 5 #1). `ImportedEvidenceReads.scope`, the scope `create_app` wires into the Overview route and the board,
is monkeypatched once to the S5 stand-in (`Imported.scope`, a passing comparison). Everything else is the real
stores and services. `test_kobo_guardrail_closed_s2_is_partial_unknown` keeps the honest closed case.

- Kobo `estate` (s602b `build(URL, tmp, "estate")`), board day 2026-10-21: the real `site_work_rows` Finding rows
  carry the keys the B2 fake (`test_out_b2_mini.py` ESTATE_F104) assumes; the B.7 #2 Kobo row states.
- Kobo `guardrail`, served like its `pinned_app`. Day A 2026-10-06: F01 MOVES on Cost, checked as a safeguard on
  Protect, Cost NEEDS_ATTENTION, `must_not_harm` null. Day B 2026-11-02: the Action-row keys (ESTATE_A48), the
  ACT-048 Must-not-harm line and verification link, ACT-048 on the Cost row, no "outside this view" item.
- Cold: the w502 `positive` producer (`tools/w502_cold_work_walkthrough.py` BUILD child) over its work window.
- EV: the w504 `positive` case (`native_replay` + `_declare`, as `test_w504_ev_work_producer_postgres.py`), in a
  child process so its registered replay helpers bind the case database.

The s602b builder is called as `build()` in a child: the script's `main` refuses `*_test` names only because it
never resets one, and the case database here is fresh. Builders run with the run-routing variables stripped, so
they write the case database. Evidence-store roots are this test's folders, never the worktree's `var/`. Row
states, failed ports, the KOBO `site_import.imported_at` and board read times are printed as `OUT-B4 record`.
"""
from __future__ import annotations

import contextlib
import json
import os
import subprocess
import sys
import time
from datetime import timedelta, datetime, timezone
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
DAY_A_TO = datetime(2026, 10, 7, tzinfo=timezone.utc)
FAILURES: list[str] = []
COMPS: list[list[str]] = []
LAST_PORTS: dict[str, dict] = {}
LAST_ERRORS: dict[str, list[str]] = {}
COMPLETED_REQUESTS: list[int] = []  # completed maintenance requests the work_index returned, per read
CATEGORIES = ["GROW_REVENUE", "OPTIMIZE_COST", "PROTECT_ASSET", "ASSURE_PERFORMANCE"]
PORTS: dict[str, object] = {}  # per board read: a summary of each mini port body (why an outcome is unsettled)


def _record(key: str, value: object) -> None:
    print(f"\nOUT-B4 record {key}:", json.dumps(value, default=str))


# ------------------------------------------------------------------ one database per case (addendum 5 #2)

@contextlib.contextmanager
def _case_db(case: str, slice_: str = "b"):
    """`assetops_out_<slice>_<case>_test` on the harness server: a clone of this run's migrated template when routed,
    else created blank and migrated. Dropped (FORCE) on exit. OUT-C passes `slice_="c"`."""
    from sqlalchemy import create_engine, text
    from sqlalchemy.engine import make_url
    from sqlalchemy.pool import NullPool

    name = f"assetops_out_{slice_}_{case}_test"
    base = make_url(os.environ.get(pg_harness.BASE_ENV) or URL)
    url = base.set(database=name).render_as_string(hide_password=False)
    engine = None
    if pg_harness.routed():
        admin, template = pg_harness._admin(), pg_harness._ensure_template()
    else:
        engine = create_engine(base.set(database="postgres"), poolclass=NullPool, isolation_level="AUTOCOMMIT")
        admin, template = engine.connect(), None
    drop = text(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
    admin.execute(drop)
    if template:
        pg_harness._create(name, template)
    else:
        from alembic import command

        admin.execute(text(f'CREATE DATABASE "{name}"'))
        command.upgrade(pg_harness._alembic(url), "head")
    try:
        yield url
    finally:
        admin.execute(drop)
        if engine is not None:
            admin.close()
            engine.dispose()


def _child_env(url: str) -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if not k.startswith("ASSETOPS_TEST_")}
    parts = ["backend", "gateway", "simulator", "contracts", "host", "backend/tests"]
    env["PYTHONPATH"] = os.pathsep.join(str(ROOT / p) for p in parts)
    env["ASSETOPS_TEST_DATABASE_URL"] = env["DATABASE_URL"] = url
    env["PYTHONUNBUFFERED"] = "1"
    return env


def _child(url: str, argv: list[str]) -> None:
    done = subprocess.run([sys.executable, *argv], cwd=str(TESTS), env=_child_env(url), capture_output=True,
                          text=True, timeout=1800)
    assert done.returncode == 0, f"{argv[:2]} failed\n{done.stdout[-3000:]}\n{done.stderr[-3000:]}"


def _evidence_root(monkeypatch, root: Path) -> None:
    """The evidence-store roots (the Performance comparison report, the legacy inventory) under this test's folder."""
    from assetops_backend.evidence.adapters import json_evidence_store, legacy_comparison_file

    monkeypatch.setattr(json_evidence_store, "EVIDENCE_STORE_ROOT", root)
    monkeypatch.setattr(legacy_comparison_file, "EVIDENCE_STORE_ROOT", root)


def _serve(monkeypatch, url: str, work: Path, *, s2_stand_in: bool = True) -> None:
    """The app environment for one case database: env, store roots, the S2 stand-in, the port and composer spies."""
    from assetops_backend.estate.scope import PORTFOLIO_CURSOR_KEY_ENV

    monkeypatch.setenv("DATABASE_URL", url)
    monkeypatch.setenv(PORTFOLIO_CURSOR_KEY_ENV, "0" * 64)
    _evidence_root(monkeypatch, work / "evidence")
    if s2_stand_in:  # addendum 5 #1: the S5 Overview Postgres test's stand-in, once, on the scope create_app uses
        import test_s5_overview_postgres as s5

        from assetops_backend.evidence.ledger_reads import ImportedEvidenceReads

        monkeypatch.setattr(ImportedEvidenceReads, "scope", lambda self, code: s5.Imported(s5.Gates()).scope(code))
    FAILURES.clear()
    COMPS.clear()
    _record_port_failures(monkeypatch)
    _spy_compositions(monkeypatch)


def _record_port_failures(monkeypatch) -> None:
    """Every refused or failed mini port with its error, into the printed record (the board only names it)."""
    from assetops_backend.site_outcomes import mini

    real = mini.Reads.call

    def call(self, name, fn, *args):
        def traced(*a):
            try:
                body = fn(*a)
            except Exception as error:
                FAILURES.append(f"{name}: {type(error).__name__}: {str(error)[:200]}")
                raise
            if name == "mini_overview":  # the settled base (mini.py: freshness CURRENT, assessment not CLOSED)
                PORTS[name] = {"freshness": (body.get("freshness") or {}).get("state"),
                               "assessment": (body.get("assessment") or {}).get("state")}
            elif name in ("cold_overview", "ev_overview") and isinstance(body, dict):
                PORTS[name] = {k: (body.get(k) or {}).get("state") for k in ("currentness", "freshness", "assessment",
                                                                           "readiness", "cooling") if k in body}
            elif name == "work_index" and a and a[0] == "maintenance" and isinstance(body, dict):
                COMPLETED_REQUESTS.append(sum(1 for r in body.get("rows") or () if r.get("state") == "COMPLETED"))
                PORTS.setdefault(name, []).append({"status": body.get("status"), "rows": len(body.get("rows") or ()),
                                                   "completed": COMPLETED_REQUESTS[-1]})
            elif isinstance(body, dict) and ("rows" in body or "items" in body):
                rows_ = body.get("rows") or body.get("items") or ()
                PORTS.setdefault(name, []).append({"status": body.get("status"), "rows": len(rows_),
                                                   "ids": [str(r.get("action_id")) for r in rows_ if isinstance(r, dict)],
                                                   "reasons": str(body.get("reasons"))[:160]})
            elif isinstance(body, str):
                PORTS[name] = body
            return body
        return real(self, name, traced, *args)

    monkeypatch.setattr(mini.Reads, "call", call)


def _spy_compositions(monkeypatch) -> None:
    """Each composer's `failed` list (the body carries only `read_state`)."""
    from assetops_backend.site_outcomes import cold, ev, mini

    for module in (mini, cold, ev):
        def compose(*a, _real=module.compose, **kw):
            comp = _real(*a, **kw)
            COMPS.append(list(comp.failed))
            return comp

        monkeypatch.setattr(module, "compose", compose)


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


def _client():
    from fastapi.testclient import TestClient

    from assetops_backend.config import load_feature_flags
    from assetops_backend.main import create_app

    return TestClient(create_app(load_feature_flags()))


def _board(c, code: str, key: str, **params) -> tuple[dict, list[str]]:
    """One board read, timed; returns the body and the composer's `failed` list."""
    COMPS.clear()
    PORTS.clear()
    COMPLETED_REQUESTS.clear()
    started = time.perf_counter()
    r = c.get(f"/api/sites/{code}/outcome-board", params=params)
    seconds = round(time.perf_counter() - started, 2)
    assert r.status_code == 200, r.text
    body = r.json()
    failed = COMPS[-1] if COMPS else None
    _record(key, {"read_state": body["read_state"], "states": _states(body), "window": body["window"],
                  "failed": failed, "port_errors": sorted(set(FAILURES)), "ports": dict(PORTS), "seconds": seconds})
    LAST_PORTS[key] = dict(PORTS)
    LAST_ERRORS[key] = sorted(set(FAILURES))
    FAILURES.clear()
    return body, failed


def _covering_day_params(lo: str, hi: str) -> dict[str, str]:
    """The covering UTC days of a board window (addendum 7): [floor(lo), ceil(hi)), as estate route params."""
    a = datetime.fromisoformat(lo.replace("Z", "+00:00")).astimezone(timezone.utc)
    b = datetime.fromisoformat(hi.replace("Z", "+00:00")).astimezone(timezone.utc)
    a = a.replace(hour=0, minute=0, second=0, microsecond=0)
    c = b.replace(hour=0, minute=0, second=0, microsecond=0)
    c = c if c == b else c + timedelta(days=1)
    return {"from": a.strftime("%Y-%m-%dT%H:%M:%SZ"), "to": c.strftime("%Y-%m-%dT%H:%M:%SZ")}


def _portfolio_evidence(c, code: str, days: dict[str, str]) -> tuple[str, str | None]:
    """The Portfolio's EVIDENCE cell for one Site over `days` (`GET /api/estate/portfolio`), or the route's refusal
    code. Also reads `GET /api/estate/evidence` over the same days and checks it agrees on a refusal."""
    ev = c.get("/api/estate/evidence", params=days)
    r = c.get("/api/estate/portfolio", params=days)
    if r.status_code != 200:
        assert ev.status_code == r.status_code, (ev.status_code, r.status_code, ev.text[:200], r.text[:200])
        return "REFUSED", str(r.json().get("detail", {}).get("code") if isinstance(r.json().get("detail"), dict)
                              else r.text[:120])
    cells = [x["state"] for o in r.json()["objectives"] if o["site_code"] == code
             for x in o["cells"] if x["key"] == "EVIDENCE"]
    assert len(cells) == 1, (code, r.text[:300])
    assert ev.status_code == 200, (ev.status_code, ev.text[:200])
    return "CELL", cells[0]


def _assert_readiness_equals_portfolio(c, key: str, code: str, board: dict) -> None:
    """M2 / addendum 7: the board's readiness port value equals the Portfolio cell over the covering UTC days."""
    days = _covering_day_params(board["window"]["from"], board["window"]["to"])
    kind, value = _portfolio_evidence(c, code, days)
    port = LAST_PORTS[key].get("evidence_readiness")
    _record(f"{key}_readiness_vs_portfolio", {"days": days, "portfolio": [kind, value], "board_port": port,
                                               "board_port_errors": LAST_ERRORS[key]})
    if kind == "CELL":
        assert port == value, (port, value)
    else:  # the Portfolio refused on whole days: the board's readiness read failed the same way (Assure UNKNOWN)
        assert port is None and any("evidence_readiness" in e for e in LAST_ERRORS[key]), (port, LAST_ERRORS[key])


def _rows(body: dict) -> dict[str, dict]:
    return {r["category"]: r for r in body["rows"]}


def _items(row: dict) -> list[dict]:
    return [*row["issues"], *row["in_hand"], *row["earlier"], *row["options"]]


def _states(body: dict) -> list[str]:
    return [r["state"] for r in body["rows"]]


# ------------------------------------------------------------------ Kobo (s602b builders)

def _build_kobo(url: str, work: Path, case: str) -> tuple[dict, list]:
    _child(url, ["-c", "import sys; from pathlib import Path; sys.path.insert(0, sys.argv[3]); "
                       "import s602b_test_scoped_cases as s; s.build(sys.argv[1], Path(sys.argv[2]), sys.argv[4])",
                 url, str(work), str(ROOT / "tools"), case])
    # the s602b walkthrough's step 5: the Performance comparison that releases the Finding reads, in process,
    # its report under this test's folder (the w403 replay test pattern)
    from sqlalchemy import create_engine, text
    from sqlalchemy.pool import NullPool

    from assetops_backend.performance_migration import main as performance_migration

    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("DATABASE_URL", url)
        _evidence_root(mp, work / "evidence")
        assert performance_migration(["run", "--tenant", "demo", "--site", "KOBO-001"]) == 0
    engine = create_engine(url, poolclass=NullPool)
    try:  # addendum 5 #2 (ii): the estate admits a Site only when its site_import precedes the request's `to`
        with engine.connect() as connection:
            imported = [r[0] for r in connection.execute(text(
                "SELECT i.imported_at FROM site_import i JOIN site s ON s.id = i.site_id "
                "WHERE s.site_code = 'KOBO-001' ORDER BY i.imported_at"))]
    finally:
        engine.dispose()
    _record(f"kobo_{case}_imported_at", imported)
    return json.loads((work / f"case-{case}.json").read_text(encoding="utf-8")), imported


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

        monkeypatch.setattr(ev, "URL", os.environ["DATABASE_URL"])  # its verification_ports(URL): the case DB
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


@pytest.fixture(scope="module")
def kobo_guardrail(tmp_path_factory):
    work = tmp_path_factory.mktemp("guardrail")
    with _case_db("guardrail") as url:
        spec, imported = _build_kobo(url, work, "guardrail")
        yield url, work, spec, imported


def test_kobo_guardrail_closed_s2_is_partial_unknown(kobo_guardrail, monkeypatch) -> None:
    """Addendum 5 #1: without the stand-in the fixture has no passing S2 comparison, so the mini overview port is
    refused and the board is PARTIAL with every outcome UNKNOWN (the gate reaches the board)."""
    url, work, spec, _ = kobo_guardrail
    _serve(monkeypatch, url, work, s2_stand_in=False)
    _pin_kobo(monkeypatch, spec)
    with _client() as c:
        body, failed = _board(c, "KOBO-001", "kobo_guardrail_day_a_closed", date="2026-10-06")
    assert body["read_state"] == "PARTIAL"
    assert "mini_overview" in failed, failed
    outcomes = {o["key"]: o["state"] for r in body["rows"] for o in r["outcomes"]}
    _record("kobo_guardrail_day_a_closed_outcomes", outcomes)
    assert set(_states(body)) == {"UNKNOWN"}, _states(body)
    assert outcomes and set(outcomes.values()) <= {"UNKNOWN", "NOT_MEASURED"}, outcomes
    assert "UNKNOWN" in outcomes.values(), outcomes


def test_kobo_guardrail_two_board_days(kobo_guardrail, monkeypatch) -> None:
    url, work, spec, imported = kobo_guardrail
    _serve(monkeypatch, url, work)
    _pin_kobo(monkeypatch, spec)
    seen = _spy_work_rows(monkeypatch)
    with _client() as c:
        a, failed_a = _board(c, "KOBO-001", "kobo_guardrail_day_a", date="2026-10-06")
        b, failed_b = _board(c, "KOBO-001", "kobo_guardrail_day_b", date="2026-11-02")

    # Addendum 6: the s602b fixtures are not current (overview STALE_PROJECTION, Finding index UNASSESSED), so the
    # Day A NEEDS_ATTENTION/F01 and Day B Must-not-harm assertions move to the combined-dataset acceptance.
    for body in (a, b):
        assert [r["category"] for r in body["rows"]] == CATEGORIES, [r["category"] for r in body["rows"]]
        measured = {o["key"]: o["state"] for r in body["rows"] for o in r["outcomes"]}
        assert measured and set(measured.values()) <= {"UNKNOWN", "NOT_MEASURED"}, measured
        assert "UNKNOWN" in measured.values(), measured
    _record("kobo_guardrail_read_states", {"a": [a["read_state"], failed_a], "b": [b["read_state"], failed_b]})
    if all(at >= DAY_A_TO for at in imported):  # addendum 5 #2 (ii): import-time artefact
        assert failed_a == ["estate"], failed_a
        assert a["read_state"] == "PARTIAL"

    # Parity: the product overview route's freshness is the board's mini overview body (same app)
    with _client() as c2:
        for day in ("2026-10-06", "2026-11-02"):
            r = c2.get("/api/sites/KOBO-001/overview", params={"date": day})
            assert r.status_code == 200, r.text
            _record(f"kobo_overview_route_{day}", r.json()["freshness"]["state"])
            parity = r.json()["freshness"]["state"]
            board_key = "kobo_guardrail_day_a" if day == "2026-10-06" else "kobo_guardrail_day_b"
            assert LAST_PORTS[board_key]["mini_overview"]["freshness"] == parity, (day, LAST_PORTS[board_key])

    # Day B: the real Action rows carry the keys the B2 fake assumes (ESTATE_A48), with `_raw` where progress reads it
    actions = [x for rows in seen[1:] if rows for x in rows["actions"]]
    assert actions, seen[1:]
    for x in actions:
        assert ACTION_KEYS <= set(x), ACTION_KEYS - set(x)
        assert ACTION_RAW_KEYS <= set(x["_raw"]), ACTION_RAW_KEYS - set(x["_raw"])
    # Day B: the Action index port itself returned ACT-048 (L1: asserted on the port, not on a JSON substring)
    index = LAST_PORTS["kobo_guardrail_day_b"]["action_index"]
    assert sum(p["rows"] for p in index) >= 1 and any(p["ids"] and spec["action"] in p["ids"] for p in index), index
    assert not [i for r in b["rows"] for i in _items(r) if i["text"].endswith(OUTSIDE)]


def test_kobo_estate_finding_rows_and_states(monkeypatch, tmp_path) -> None:
    """Addendum 5 #2: the `estate` case puts KOBO in estate scope with Finding rows on 2026-10-21 (F05, an
    UNCONFIRMED GENERATOR_SUPPORT_CANDIDATE, open primary, no Action): the real row keys and B.7 #2's states."""
    with _case_db("estate") as url:
        spec, _ = _build_kobo(url, tmp_path, "estate")
        _serve(monkeypatch, url, tmp_path)
        _pin_kobo(monkeypatch, spec)
        seen = _spy_work_rows(monkeypatch)
        with _client() as c:
            body, failed = _board(c, "KOBO-001", "kobo_estate_2026_10_21", date="2026-10-21")
    # Addendum 6: the estate Finding-row key check and the Cost/Assure states move to the combined-dataset
    # acceptance (estate 10-21 has no Finding rows while coverage is not current). Recorded states only.
    assert [r["category"] for r in body["rows"]] == CATEGORIES
    measured = {o["key"]: o["state"] for r in body["rows"] for o in r["outcomes"]}
    assert set(measured.values()) <= {"UNKNOWN", "NOT_MEASURED"}, measured
    _record("kobo_estate_read", {"read_state": body["read_state"], "failed": failed, "outcomes": measured})


# ------------------------------------------------------------------ cold and EV

def test_cold_w502_positive(monkeypatch, tmp_path) -> None:
    import w502_cold_work_walkthrough as w502

    out = tmp_path / "positive"
    out.mkdir()
    with _case_db("cold") as url:
        _child(url, ["-c", w502.BUILD, "positive", str(out)])
        doc = json.loads((out / "positive.json").read_text(encoding="utf-8"))
        assert doc["blocked"] is None, doc["blocked"]
        _serve(monkeypatch, url, tmp_path)
        with _client() as c:
            body, _ = _board(c, "COLD-LAB-001", "cold_w502_positive", **dict(zip(("from", "to"), doc["w501"]["window"])))
            _assert_readiness_equals_portfolio(c, "cold_w502_positive", "COLD-LAB-001", body)
    grow, cost, protect, assure = _states(body)  # B.7 #2 (addendum 6: window doc["w501"]["window"], no known_at)
    # OUT-C: CC-3 is measured (catalogue/2) and the authored repeat visits make cold Cost NEEDS_ATTENTION (review L1)
    assert (grow, cost, protect) == ("NOT_MEASURED", "NEEDS_ATTENTION", "NEEDS_ATTENTION"), _states(body)
    _record("cold_assure", assure)
    # B.7 #4 (L2, evaluated): "Not yet verified" is present exactly when a completed maintenance request is in the
    # work window (the work_index returned one) and no later related request makes it "Did not fix it".
    earlier = [i for r in body["rows"] for i in r["earlier"]]
    present = any(i.get("result_label") == "Not yet verified" for i in earlier)
    repeated = any(i.get("result_label") == "Did not fix it" for i in earlier)
    completed = sum(COMPLETED_REQUESTS)
    _record("cold_b7_4_not_yet_verified", {"present": present, "completed_requests_in_work_window": completed,
                                           "window": doc["w501"]["window"]})
    # OUT-C U3: with the authored repeat visits the earlier ones read "Did not fix it" and the latest one
    # "Not yet verified", so both are present.
    assert present and repeated and completed > 0, (present, repeated, completed)
    if present:
        assert body["window"]["known_at"] is not None  # addendum 4 #5: the overview's resolved cutoff


EV_BUILD = r'''
import json, sys
from pathlib import Path
sys.path.insert(0, sys.argv[2])
import w504_ev_work_cases as P
import w504_ev_work_walkthrough as walk
import os
tmp = Path(sys.argv[1])
replayed = walk.native_replay(P.POSITIVE_SCENARIO, tmp / "chain", fresh=True)
built = walk._declare(os.environ["DATABASE_URL"], "positive", "fx", replayed)
(tmp / "ev.json").write_text(json.dumps(built, default=str), encoding="utf-8")
'''


def test_ev_w504_positive(monkeypatch, tmp_path) -> None:
    with _case_db("ev") as url:
        _child(url, ["-c", EV_BUILD, str(tmp_path), str(ROOT / "tools")])
        built = json.loads((tmp_path / "ev.json").read_text(encoding="utf-8"))
        assert built["status"] == "ready", built.get("status")
        window = {"from": built["evidence_window_E"]["from"], "to": built["evidence_window_E"]["to"]}
        _serve(monkeypatch, url, tmp_path)
        with _client() as c:
            body, _ = _board(c, "EV-LAB-001", "ev_w504_positive", **window)
            # M2 / addendum 7: the board's readiness equals the Portfolio EVIDENCE cell over the covering UTC day
            _assert_readiness_equals_portfolio(c, "ev_w504_positive", "EV-LAB-001", body)
    _record("ev_assure_after_covering_days", _states(body))  # addendum 7: re-recorded, expectation not adjusted
    assert _states(body)[:3] == ["WATCH", "NOT_MEASURED", "NEEDS_ATTENTION"], _states(body)  # B.7 #2
