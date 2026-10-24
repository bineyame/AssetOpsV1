"""W5-04a V1b: DB-free unit tests of the EV work producer library `tools/w504_ev_work_cases.py`.

Readiness 29 (K0 route/clock cross-check on synthetic responses), 34-38 (registered E, current W, clock order,
the evidence-clock mapping) and the "EV producer, UI and registry" payload literals. No database, no server.
"""

from __future__ import annotations

import ast
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import w504_ev_work_cases as P  # noqa: E402

R = datetime(2026, 10, 24, 13, 5, 7, 123456, tzinfo=timezone.utc)
LO, HI = datetime(2026, 10, 6, 8, 0, tzinfo=timezone.utc), datetime(2026, 10, 6, 9, 0, tzinfo=timezone.utc)
K0 = "2026-10-06T09:00:00.25Z"
FINDING, REVISION = "aaaaaaaa-0000-4000-8000-000000000001", "aaaaaaaa-0000-4000-8000-000000000002"
SESSION, SESSION_REV = "bbbbbbbb-0000-4000-8000-000000000001", "bbbbbbbb-0000-4000-8000-000000000002"
OTHER = "bbbbbbbb-0000-4000-8000-000000000003"
E1, E2, E3 = ("cccccccc-0000-4000-8000-00000000000" + n for n in "123")


def window(**over) -> dict:
    return {"from": "2026-10-06T08:00:00Z", "to": "2026-10-06T09:00:00Z", "known_at": K0, **over}


def scenarios(**over) -> dict:
    return {"schema_version": "ev-scenarios-1", "window": {**window(), "committed_watermark": K0, **over}}


def sessions(**over) -> dict:
    return {"window": window(**over), "selected_source_provenance": {"evidence_ids": [E1.upper(), E2]},
            "items": [{"session_id": SESSION, "revision_id": SESSION_REV, "state": "OBSERVED_ABORT",
                       "fault_evidence_id": E2, "connector_asset_id": "dddddddd-0000-4000-8000-000000000001"},
                      {"session_id": OTHER, "revision_id": OTHER, "state": "COMPLETED", "fault_evidence_id": None,
                       "connector_asset_id": None}]}


def findings(**over) -> dict:
    return {"window": window(**over), "items": [
        {"finding_id": FINDING, "revision_id": REVISION, "session_id": SESSION, "lifecycle": "SUPPORTED",
         "source_provenance": {"evidence_ids": [E1, E2, E3]}}]}


def test_evidence_window_is_the_registered_one() -> None:
    assert (P.E_START, P.E_END) == (LO, HI)
    assert (P.SITE_CODE, P.POSITIVE_SCENARIO, P.UNKNOWN_SCENARIO) == ("EV-LAB-001", "ev-interrupted",
                                                                      "ev-missing-meter")
    marks = [HI, HI + timedelta(minutes=5)]
    assert P.evidence_clock_for(R, marks) == HI + timedelta(minutes=5)
    assert P.evidence_clock_for(HI + timedelta(minutes=1), marks) == HI
    with pytest.raises(P.ProducerRefused):
        P.evidence_clock_for(LO, marks)


def test_work_window_from_db_day() -> None:
    day = datetime(2026, 10, 24, tzinfo=timezone.utc)
    assert P.work_window(R) == (day, day + timedelta(days=1))
    with pytest.raises(P.ProducerRefused):
        P.work_window(datetime(2026, 10, 24))
    w = P.bounded_work_window(R, {"K1": R - timedelta(minutes=5), "incident.occurred_at": R - timedelta(minutes=3)})
    assert (w["from"], w["to"], w["recomputed"]) == (day, day + timedelta(days=1), False)
    # K1 written just before midnight, the cases just after: one bounded explicit window containing all three.
    late = datetime(2026, 10, 25, 0, 0, 30, tzinfo=timezone.utc)
    w = P.bounded_work_window(late, {"K1": late - timedelta(minutes=2), "incident.occurred_at": late,
                                     "maintenance.created_at": late})
    assert (w["from"], w["to"], w["recomputed"]) == (day, day + timedelta(days=2), True)
    for bad in ({"K1": R - timedelta(days=31)}, {"K1": R + timedelta(minutes=6)}, {}):
        with pytest.raises(P.ProducerRefused):
            P.bounded_work_window(R, bad)


def test_clock_order_is_enforced() -> None:
    k0 = P.instant(K0)
    k1, k2 = R, R + timedelta(seconds=1)
    k3, k4 = [R + timedelta(seconds=2), R + timedelta(seconds=3)], [R + timedelta(seconds=4)]
    order = P.clock_order(k0, k1, k2, k3, k4)
    assert [x.split("=")[0] for x in order] == ["K0", "K1", "K2", "K3", "K3", "K4"]
    assert P.clock_order(k0, k1, k1, [k1], [k1])  # equal returned clocks are allowed (<=)
    for args in ((k0, k0), (k0, k1, k1 - timedelta(microseconds=1)), (k0, k1, k2, [k1], [k2]),
                 (k0, k1, k2, [k4[0]], [k3[0]]), (k0, k1, None, k3), (k0, k1, k2, (), k4)):
        with pytest.raises(P.ProducerRefused):
            P.clock_order(*args)


def test_k0_cross_check_accepts_equal_clocks_after_normalization() -> None:
    k0 = P.cross_check_k0(scenarios(), sessions(known_at="2026-10-06T09:00:00.250000+00:00"), LO, HI)
    assert k0 == datetime(2026, 10, 6, 9, 0, 0, 250000, tzinfo=timezone.utc)


@pytest.mark.parametrize("scen,sess", [
    (dict(committed_watermark=None), {}),
    ({}, dict(known_at="2026-10-06T09:00:00Z")),
    (dict(known_at="2026-10-06T08:59:00Z"), {}),
    ({}, {"to": "2026-10-06T10:00:00Z"}),
    (dict(**{"from": "2026-10-06T07:00:00Z"}), {}),
    ({}, dict(known_at=None)),
])
def test_k0_cross_check_refuses_mismatched_window_or_clock(scen, sess) -> None:
    with pytest.raises(P.ProducerRefused):
        P.cross_check_k0(scenarios(**scen), sessions(**sess), LO, HI)


def test_k0_refuses_a_missing_window() -> None:
    with pytest.raises(P.ProducerRefused):
        P.cross_check_k0({"items": []}, sessions(), LO, HI)


def test_read_k0_uses_the_routes_and_the_same_window() -> None:
    calls = []

    def get(path, params):
        calls.append((path, dict(params)))
        body = {"/financials/scenarios": scenarios(), "/sessions": sessions(), "/findings": findings()}
        return 200, body[path.split("/ev", 1)[1]]

    selected = P.read_k0(get, "EV-LAB-001", LO, HI)
    bounds = {"from": "2026-10-06T08:00:00Z", "to": "2026-10-06T09:00:00Z"}
    assert calls == [("/api/sites/EV-LAB-001/ev/financials/scenarios", bounds),
                     ("/api/sites/EV-LAB-001/ev/sessions", bounds),
                     ("/api/sites/EV-LAB-001/ev/findings", {**bounds, "known_at": K0})]
    assert (selected.finding_revision_id, selected.session_id, selected.session_revision_id) == (
        REVISION, SESSION, SESSION_REV)
    assert selected.accepted_evidence_ids == sorted([E1, E2])  # cited by the Finding and the selected head
    assert selected.manifest()["k0"] == "2026-10-06T09:00:00.250000Z"


def test_select_positive_refusals() -> None:
    k0 = P.instant(K0)
    with pytest.raises(P.ProducerRefused):  # the Finding read is not the same cutoff
        P.select_positive(sessions(), findings(known_at="2026-10-06T09:05:00Z"), k0, LO, HI)
    other = findings()
    other["items"][0]["session_id"] = OTHER  # a completed session is not fault-ended
    with pytest.raises(P.ProducerRefused):
        P.select_positive(sessions(), other, k0, LO, HI)
    retired = findings()
    retired["items"][0]["lifecycle"] = "RETIRED"
    with pytest.raises(P.ProducerRefused):
        P.select_positive(sessions(), retired, k0, LO, HI)
    uncited = sessions()
    uncited["selected_source_provenance"] = None
    with pytest.raises(P.ProducerRefused):
        P.select_positive(uncited, findings(), k0, LO, HI)
    status = []
    with pytest.raises(P.ProducerRefused):
        P.read_k0(lambda path, params: status.append(path) or (503, {"error": {}}), "EV-LAB-001", LO, HI)
    assert len(status) == 1


def test_payload_literals() -> None:
    selected = P.read_k0(lambda path, params: (200, {"/financials/scenarios": scenarios(), "/sessions": sessions(),
                                                     "/findings": findings()}[path.split("/ev", 1)[1]]),
                         "EV-LAB-001", LO, HI)
    raised = R
    action = P.action_body(selected, raised, "k", db_now=R)
    assert {k: action[k] for k in ("domain", "title", "owner_label", "due_at")} == {
        "domain": "EV_CHARGING", "title": "Investigate connector 2", "owner_label": "Charging operations",
        "due_at": None}
    assert action["raised_at"] == "2026-10-24T13:05:07.123456Z"  # current DB time, not the 2026-10-06 clock
    with pytest.raises(P.ProducerRefused):
        P.action_body(selected, selected.k0, "k")
    for outside in (R - timedelta(days=30, seconds=1), R + timedelta(minutes=5, seconds=1)):
        with pytest.raises(P.ProducerRefused):  # the domain service's DB-time window
            P.action_body(selected, outside, "k", db_now=R)
    intent = P.intent_body(selected, REVISION, raised, "i", session_ids=[OTHER, SESSION.upper()])
    assert intent["basis"] == {"finding_revision_id": REVISION, "work_case_id": None, "work_record_id": None,
                               "accepted_evidence_ids": sorted([E1, E2]), "session_ids": sorted([SESSION, OTHER])}
    assert len(intent["criteria"]) == 3
    with pytest.raises(P.ProducerRefused):
        P.intent_body(selected, REVISION, raised, "i", session_ids=[OTHER])
    inc = P.incident_body("asset-1", LO, "a")
    assert (inc["kind"], inc["title"], inc["narrative"], inc["asset_id"]) == (
        "INCIDENT", "Charging session fault", "Connector fault ended a charging session; outcome remains unverified",
        "asset-1")
    wr, rec = P.request_body("asset-1", LO, "b"), P.record_body(LO, "c")
    assert (wr["kind"], wr["title"]) == ("MAINTENANCE_REQUEST", "Connector diagnostic inspection")
    assert (rec["activity"], rec["outcome_note"]) == (
        "Inspect connector and witness a charging session",
        "Inspection recorded; recurrence and availability remain unverified")
    assert wr["narrative"] == "Inspect connector and witness a charging session" == rec["activity"]  # ruling 37
    assert not hasattr(P, "WR_NARRATIVE_PENDING_RULING")
    times = P.submitted_case_times(R)
    assert all(R - timedelta(days=30) <= t <= R for t in times.values())
    assert times["incident"] < times["request"] < times["record"]


def _imports(tree) -> set[str]:
    imported = {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
    return imported | {n.module or "" for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}


TEST_ONLY = ("pg_harness", "ev_depth_cases", "scenario_cache", "run_fixtures", "fake_central", "gateway_process")


def _test_modules(names: set[str]) -> list[str]:
    return sorted(m for m in names if m.split(".")[0].startswith("test_") or m.split(".")[0] in TEST_ONLY)


def test_producer_imports_no_test_module() -> None:
    """The library never imports a test module (no `Chain`, no `test_*`, no harness)."""
    tree = ast.parse((ROOT / "tools" / "w504_ev_work_cases.py").read_text(encoding="utf-8"))
    assert not _test_modules(_imports(tree))


def test_walkthrough_test_imports_are_only_the_native_replay_child() -> None:
    """Ruling 36: the walkthrough's only test-helper imports are the two registered-replay helper modules, inside
    `native_replay` (the child's private `*_test` fixture adapter); nothing reads `decision_clock` as K0."""
    source = (ROOT / "tools" / "w504_ev_work_walkthrough.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    replay = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "native_replay")
    assert _test_modules(_imports(replay)) == ["test_w205b_ev_replay_postgres", "test_w206_ev_store_postgres"]
    outside = ast.Module(body=[n for n in tree.body if n is not replay], type_ignores=[])
    assert not _test_modules(_imports(outside))
    names = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)} | {
        n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    assert "decision_clock" not in names and "FIRST_DECISION" not in names


def test_zero_reads_state_the_zero_itself() -> None:
    """Review L4: complete zero needs empty rows AND `total_count == 0` and a null cursor on both W4 reads."""
    zero = {"rows": [], "total_count": 0, "next_cursor": None}
    assert P.zero_reads_complete(zero, dict(zero))
    for bad in ({**zero, "total_count": 1}, {**zero, "next_cursor": "c"}, {"rows": []},
                {**zero, "total_count": False}, {**zero, "rows": [{"id": "x"}]}):
        assert not P.zero_reads_complete(bad, dict(zero)) and not P.zero_reads_complete(dict(zero), bad), bad


def test_walkthrough_kills_only_its_own_recorded_server() -> None:
    """Review L6: a recorded PID is killed only while its command line is still our `uvicorn serve_entry:app` on the
    recorded port; a reused PID (any other process or port) never matches."""
    import w504_ev_work_walkthrough as W

    ours = "python.exe -m uvicorn serve_entry:app --host 127.0.0.1 --port 8123"
    assert W.is_recorded_server(ours, 8123) and W.is_recorded_server(ours + " --log-level info", 8123)
    for other in (None, "", "notepad.exe", "python.exe -m uvicorn other:app --port 8123",
                  ours.replace("8123", "81234"), ours.replace("8123", "8124")):
        assert not W.is_recorded_server(other, 8123), other
    calls = []
    real_cmd, real_run = W._command_line, W.subprocess.run
    W._command_line = lambda pid: "notepad.exe"
    W.subprocess.run = lambda *a, **k: calls.append(a)
    try:
        assert W._stop_owned({"pid": 4242, "port": 8123}) is False and calls == []
        W._command_line = lambda pid: ours
        assert W._stop_owned({"pid": 4242, "port": 8123}) is True and calls[0][0][:3] == ["taskkill", "/PID", "4242"]
    finally:
        W._command_line, W.subprocess.run = real_cmd, real_run
