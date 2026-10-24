"""W5-04a V1b: DB-free unit tests of the EV work producer library `tools/w504_ev_work_cases.py`.

Readiness 29 (K0 route/clock cross-check on synthetic responses), 20/22 (Site identity, no subtitle), 21 (clocks and
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
LO, HI = datetime(2026, 10, 23, 8, 0, tzinfo=timezone.utc), datetime(2026, 10, 23, 9, 0, tzinfo=timezone.utc)
K0 = "2026-10-23T09:00:00.25Z"
FINDING, REVISION = "aaaaaaaa-0000-4000-8000-000000000001", "aaaaaaaa-0000-4000-8000-000000000002"
SESSION, SESSION_REV = "bbbbbbbb-0000-4000-8000-000000000001", "bbbbbbbb-0000-4000-8000-000000000002"
OTHER = "bbbbbbbb-0000-4000-8000-000000000003"
E1, E2, E3 = ("cccccccc-0000-4000-8000-00000000000" + n for n in "123")


def window(**over) -> dict:
    return {"from": "2026-10-23T08:00:00Z", "to": "2026-10-23T09:00:00Z", "known_at": K0, **over}


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


def test_clock_math_and_window() -> None:
    assert P.day_d(R) == datetime(2026, 10, 23, tzinfo=timezone.utc)
    assert P.shifted_window(R) == (LO, HI)
    assert P.BASE_WINDOW_START + P.target_delta(R) == LO
    midnight = datetime(2026, 10, 24, tzinfo=timezone.utc)
    assert P.shifted_window(midnight) == (LO, HI)
    with pytest.raises(P.ProducerRefused):
        P.day_d(datetime(2026, 10, 24))
    marks = [LO, HI, HI + timedelta(minutes=5)]
    assert P.evidence_clock_for(HI + timedelta(minutes=1), marks) == HI
    with pytest.raises(P.ProducerRefused):
        P.evidence_clock_for(LO - timedelta(seconds=1), marks)


def test_shifted_scenario_moves_every_instant_only() -> None:
    for scenario_id in (P.POSITIVE_SCENARIO, P.UNKNOWN_SCENARIO):
        base = P.registered_scenario(scenario_id)
        moved = P.shifted_scenario_document(base, P.target_delta(R))
        assert P.instant(moved["window"]["start"]) == LO and P.instant(moved["window"]["end"]) == HI
        delta = P.target_delta(R)
        for a, b in zip(base["forcing"], moved["forcing"]):
            assert P.instant(b["time"]) - P.instant(a["time"]) == delta
            assert {k: v for k, v in a.items() if k != "time"} == {k: v for k, v in b.items() if k != "time"}
        for a, b in zip(base["observations"], moved["observations"]):
            assert P.instant(b["time"]) - P.instant(a["time"]) == delta
        assert base["window"]["start"] == "2026-10-06T08:00:00Z"  # the registered input is not mutated
    assert P.registered_scenario(P.UNKNOWN_SCENARIO)["observations"], "the unknown vector has a DROP row"


def test_shifted_site_identity_and_foundation() -> None:
    base = P.registered_site_document()
    moved = P.shifted_site_document(base, P.target_delta(R), "RUN7")
    assert (moved["site_id"], moved["display_name"], moved["timezone"], moved["site_type"]) == (
        "EV-W504-DEPOT-RUN7", "Depot Charging Hub", "Etc/UTC", "EV_CHARGING")
    assert "subtitle" not in moved and "short_name" not in moved
    assert P.instant(moved["foundation"]["valid_from"]) - P.instant(base["foundation"]["valid_from"]) == \
        P.target_delta(R)
    assert moved["foundation"]["components"] == base["foundation"]["components"]
    assert P.connector_components(moved) and len(P.connector_components(moved)) == 2
    for bad in ("run7", "", "X" * 13, "A-B"):
        with pytest.raises(ValueError):
            P.site_code(bad)
    with pytest.raises(P.ProducerRefused):
        P.shifted_site_document({**base, "subtitle": "2 x 60 kW"}, P.target_delta(R), "RUN7")


def test_k0_cross_check_accepts_equal_clocks_after_normalization() -> None:
    k0 = P.cross_check_k0(scenarios(), sessions(known_at="2026-10-23T09:00:00.250000+00:00"), LO, HI)
    assert k0 == datetime(2026, 10, 23, 9, 0, 0, 250000, tzinfo=timezone.utc)


@pytest.mark.parametrize("scen,sess", [
    (dict(committed_watermark=None), {}),
    ({}, dict(known_at="2026-10-23T09:00:00Z")),
    (dict(known_at="2026-10-23T08:59:00Z"), {}),
    ({}, {"to": "2026-10-23T10:00:00Z"}),
    (dict(**{"from": "2026-10-23T07:00:00Z"}), {}),
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

    selected = P.read_k0(get, "EV-W504-DEPOT-RUN7", LO, HI)
    bounds = {"from": "2026-10-23T08:00:00Z", "to": "2026-10-23T09:00:00Z"}
    assert calls == [("/api/sites/EV-W504-DEPOT-RUN7/ev/financials/scenarios", bounds),
                     ("/api/sites/EV-W504-DEPOT-RUN7/ev/sessions", bounds),
                     ("/api/sites/EV-W504-DEPOT-RUN7/ev/findings", {**bounds, "known_at": K0})]
    assert (selected.finding_revision_id, selected.session_id, selected.session_revision_id) == (
        REVISION, SESSION, SESSION_REV)
    assert selected.accepted_evidence_ids == sorted([E1, E2])  # cited by the Finding and the selected head
    assert selected.manifest()["k0"] == "2026-10-23T09:00:00.250000Z"


def test_select_positive_refusals() -> None:
    k0 = P.instant(K0)
    with pytest.raises(P.ProducerRefused):  # the Finding read is not the same cutoff
        P.select_positive(sessions(), findings(known_at="2026-10-23T09:05:00Z"), k0, LO, HI)
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
        P.read_k0(lambda path, params: status.append(path) or (503, {"error": {}}), "EV-W504-DEPOT-RUN7", LO, HI)
    assert len(status) == 1


def test_payload_literals() -> None:
    selected = P.read_k0(lambda path, params: (200, {"/financials/scenarios": scenarios(), "/sessions": sessions(),
                                                     "/findings": findings()}[path.split("/ev", 1)[1]]),
                         "EV-W504-DEPOT-RUN7", LO, HI)
    raised = selected.k0 + timedelta(minutes=1)
    action = P.action_body(selected, raised, "k")
    assert {k: action[k] for k in ("domain", "title", "owner_label", "due_at")} == {
        "domain": "EV_CHARGING", "title": "Investigate connector 2", "owner_label": "Charging operations",
        "due_at": None}
    with pytest.raises(P.ProducerRefused):
        P.action_body(selected, selected.k0, "k")
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
    times = P.submitted_case_times(LO)
    assert all(LO <= t < HI for t in times.values())


def test_replay_is_blocked_on_merged_parser() -> None:
    with pytest.raises(P.ProducerBlocked, match="Q9"):
        P.replay_shifted(P.POSITIVE_SCENARIO, R, "RUN7")


def test_producer_imports_no_test_module() -> None:
    """The library never imports backend/tests (no `Chain`, no `test_*`, no harness)."""
    for name in ("w504_ev_work_cases.py", "w504_ev_work_walkthrough.py"):
        tree = ast.parse((ROOT / "tools" / name).read_text(encoding="utf-8"))
        imported = {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
        imported |= {n.module or "" for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
        bad = sorted(m for m in imported if m.split(".")[0].startswith("test_")
                     or m.split(".")[0] in ("pg_harness", "ev_depth_cases", "scenario_cache", "run_fixtures",
                                            "fake_central", "gateway_process"))
        assert not bad, (name, bad)
