"""W2-05b commit 2: the `ev-charger/1` pack (build spec Q2, Q3, Q13, Q14; technical design section 3).

Six-case numerics from the shipped documents, the total state/forcing table cell by cell, round-robin fair
allocation in 1 kW quanta, exact energy, zero-allocation pauses and the invalid-state and repeated-event guards.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from datetime import datetime, time, timedelta, timezone
from fractions import Fraction
from pathlib import Path

import pytest
import yaml

from assetops_simulator.packs.errors import PhysicallyUnacceptable
from assetops_simulator.packs.ev_charger import (
    DEFAULT_PARAMETERS, ConnectorState, EvChargerPack, EvForcingRow, EvState, run_window, scoped_session_id,
)

SCENARIOS = Path(__file__).resolve().parents[2] / "config" / "scenarios"
T0 = datetime(2026, 10, 6, 8, 0, tzinfo=timezone.utc)
END = T0 + timedelta(hours=1)
SHA = "a" * 64
S1 = scoped_session_id(SHA, "session-1")
S2 = scoped_session_id(SHA, "session-2")


def at(minute: int) -> datetime:
    return T0 + timedelta(minutes=minute)


def hm(moment: datetime) -> str:
    return moment.strftime("%H:%M")


def document_forcing(case: str) -> tuple[str, tuple[EvForcingRow, ...]]:
    text = (SCENARIOS / f"ev-{case}.yaml").read_text(encoding="utf-8")
    document = yaml.safe_load(text)
    digest = hashlib.sha256(json.dumps(document, sort_keys=True, separators=(",", ":"),
                                       ensure_ascii=False).encode("utf-8")).hexdigest()
    rows = tuple(
        EvForcingRow(datetime.strptime(r["time"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc),
                     r["kind"], r["connector"], r["value"])
        for r in document["forcing"]
    )
    return digest, rows


def run_case(case: str):
    digest, rows = document_forcing(case)
    return digest, run_window(EvChargerPack(DEFAULT_PARAMETERS, scenario_sha256=digest),
                              start=T0, end=END, forcing=rows)


def events(run) -> list[tuple[str, str, str]]:
    return [(hm(e.at), e.connector, e.kind) for e in run.events]


def energy(run) -> dict[str, Fraction]:
    return {c.connector: c.energy_kwh for c in run.final.connectors}


# --- six cases ---------------------------------------------------------------------------------------

COMPLETE_EVENTS = [("08:01", "c1", "START"), ("08:31", "c1", "END")]
EXPECTED = {
    "complete": (COMPLETE_EVENTS, {"c1": Fraction(30), "c2": Fraction(0)}),
    "interrupted": ([("08:01", "c1", "START"), ("08:16", "c1", "FAULT"), ("08:16", "c1", "ABORT")],
                    {"c1": Fraction(15), "c2": Fraction(0)}),
    "fault": ([("08:00", "c1", "FAULT"), ("08:05", "c1", "CLEAR"), ("08:11", "c2", "START"),
               ("08:21", "c2", "END")], {"c1": Fraction(0), "c2": Fraction(10)}),
    # The observation profile changes only public reports; the world is the complete session.
    "missing-meter": (COMPLETE_EVENTS, {"c1": Fraction(30), "c2": Fraction(0)}),
    "late-record": (COMPLETE_EVENTS, {"c1": Fraction(30), "c2": Fraction(0)}),
    "contradictory": (COMPLETE_EVENTS, {"c1": Fraction(30), "c2": Fraction(0)}),
}


@pytest.mark.parametrize("case", list(EXPECTED))
def test_each_case_yields_the_design_events_and_exact_energy(case: str) -> None:
    digest, run = run_case(case)
    want_events, want_energy = EXPECTED[case]
    assert events(run) == want_events
    assert energy(run) == want_energy
    assert len(run.documents) == 61
    assert run.documents[0]["boundary"] == "2026-10-06T08:00:00Z"
    assert run.documents[-1]["boundary"] == "2026-10-06T09:00:00Z"
    starts = [e.session_id for e in run.events if e.kind == "START"]
    terminals = [e.session_id for e in run.events if e.kind in ("END", "ABORT")]
    assert len(starts) == len(set(starts)) and len(terminals) == len(set(terminals))
    assert all(s == scoped_session_id(digest, "session-1" if e.connector == "c1" else "session-2")
               for e in run.events for s in [e.session_id] if s is not None)


def test_fault_before_start_creates_no_abort_and_clear_returns_plugged_with_the_session() -> None:
    digest, run = run_case("fault")
    s1 = scoped_session_id(digest, "session-1")
    c1 = [(hm(e.at), e.kind, e.session_id) for e in run.events if e.connector == "c1"]
    assert c1 == [("08:00", "FAULT", s1), ("08:05", "CLEAR", s1)]
    final = run.final.connector("c1")
    assert (final.state, final.session_id, final.started, final.fault) == ("PLUGGED", s1, False, False)
    assert run.final.connector("c2").state == "UNPLUGGED"


def test_complete_minute_documents_show_authorization_then_one_minute_charge() -> None:
    _, run = run_case("complete")
    by_time = {d["boundary"][11:16]: d for d in run.documents}

    def c1(minute: str) -> dict:
        return by_time[minute]["connectors"][0]

    assert (c1("08:00")["state"], c1("08:00")["allocated_kw"]) == ("AUTHORIZING", "0")
    assert (c1("08:01")["state"], c1("08:01")["allocated_kw"], c1("08:01")["requested_kw"]) == (
        "CHARGING", "60", "60")
    assert (c1("08:30")["state"], c1("08:30")["energy_kwh"]) == ("CHARGING", "29")
    assert (c1("08:31")["state"], c1("08:31")["energy_kwh"], c1("08:31")["session_id"]) == (
        "UNPLUGGED", "30", None)
    assert by_time["08:01"]["site_import_kw"] == "60" and by_time["08:01"]["site_available_kw"] == "80"
    assert by_time["09:00"]["connectors"][0]["energy_kwh"] == "30"
    assert [d["forcing_ordinal"] for d in run.documents[:3]] == [1, 2, 2]


def test_the_digest_is_deterministic_and_private_labels_never_leave_the_pack() -> None:
    _, first = run_case("complete")
    _, again = run_case("complete")
    assert first.content_digest() == again.content_digest()
    assert first.content_digest() != run_case("interrupted")[1].content_digest()
    assert "session-1" not in json.dumps(list(first.documents)) + repr(first.events)


def test_the_scoped_session_token_is_hashed_once() -> None:
    expected = "ev-" + hashlib.sha256(
        json.dumps([SHA, "session", "session-1"], separators=(",", ":")).encode("utf-8")).hexdigest()
    assert S1 == expected and S1 != S2


# --- allocation --------------------------------------------------------------------------------------


def charging(connector: str, session: str, request: str = "60") -> ConnectorState:
    return ConnectorState(connector, state="CHARGING", session_id=session, started=True,
                          request_kw=Fraction(request))


def both_charging(request1: str = "60", request2: str = "60", **state_fields) -> EvState:
    state = EvState.initial(T0)
    state = state.with_connector(charging("c1", S1, request1)).with_connector(charging("c2", S2, request2))
    return replace(state, started_sessions=frozenset({S1, S2}), plugs=2, **state_fields)


def pack(**overrides) -> EvChargerPack:
    grid = overrides.pop("grid_available", True)
    return EvChargerPack(replace(DEFAULT_PARAMETERS, **overrides), scenario_sha256=SHA, grid_available=grid)


def allocated(minute) -> tuple[Fraction, Fraction]:
    return tuple(c.allocated_kw for c in minute.after.connectors)  # type: ignore[return-value]


def test_two_connectors_share_the_site_limit_fairly() -> None:
    minute = pack().step(both_charging())
    assert allocated(minute) == (Fraction(40), Fraction(40))
    assert minute.document["site_import_kw"] == "80"
    assert minute.after.connector("c1").energy_kwh == Fraction(2, 3)


def test_the_round_robin_pointer_persists_across_minutes() -> None:
    p = pack(site_limit_kw=Fraction(79))
    first = p.step(both_charging())
    second = p.step(first.after)
    assert allocated(first) == (Fraction(40), Fraction(39))
    assert allocated(second) == (Fraction(39), Fraction(40))
    assert sum(allocated(first)) == sum(allocated(second)) == 79


def test_allocation_is_bounded_by_request_and_rating() -> None:
    assert allocated(pack().step(both_charging("10", "60"))) == (Fraction(10), Fraction(60))
    assert allocated(pack(connector_rating_kw=Fraction(30)).step(both_charging())) == (Fraction(30), Fraction(30))
    assert allocated(pack(charger_rating_kw=Fraction(25)).step(both_charging())) == (Fraction(25), Fraction(25))
    assert allocated(pack(base_load_kw=Fraction(50)).step(both_charging())) == (Fraction(15), Fraction(15))
    assert allocated(pack(base_load_kw=Fraction(90)).step(both_charging())) == (Fraction(0), Fraction(0))


@pytest.mark.parametrize("make_pack, state", [
    (lambda: pack(), lambda: both_charging("0", "0")),
    (lambda: pack(grid_available=False), lambda: both_charging()),
    (lambda: pack(enabled_from=time(9, 0), enabled_to=time(16, 0)), lambda: both_charging()),
])
def test_a_zero_allocation_pauses_charging_without_a_terminal(make_pack, state) -> None:
    minute = make_pack().step(state())
    assert allocated(minute) == (Fraction(0), Fraction(0))
    assert minute.events == ()
    assert [c.state for c in minute.after.connectors] == ["CHARGING", "CHARGING"]
    assert all(c.session_id is not None for c in minute.after.connectors)


# --- the total state/forcing table (Q13) -------------------------------------------------------------


def connector_in(state_name: str, *, with_session: bool = True) -> tuple[ConnectorState, EvState]:
    base = EvState.initial(T0)
    if state_name == "UNPLUGGED":
        return base.connector("c1"), replace(base, plugs=1)
    if state_name == "PLUGGED":
        c = ConnectorState("c1", state="PLUGGED", session_id=S1, request_kw=Fraction(7))
    elif state_name == "AUTHORIZING":
        c = ConnectorState("c1", state="AUTHORIZING", session_id=S1, authorized_at=T0 - timedelta(minutes=5),
                           request_kw=Fraction(7))
    elif state_name == "CHARGING":
        c = charging("c1", S1, "7")
    else:
        c = ConnectorState("c1", state="FAULTED", session_id=S1 if with_session else None, fault=True)
    state = replace(base.with_connector(c), plugs=1,
                    started_sessions=frozenset({S1}) if state_name == "CHARGING" else frozenset())
    return c, state


def apply(state: EvState, kind: str, value: str, connector: str = "c1"):
    """Apply one forcing at a later boundary so an AUTHORIZING setup is not completed by the same minute."""
    later = replace(state, minute=T0 + timedelta(minutes=10))
    return pack().step(later, (EvForcingRow(later.minute, kind, connector, value),))


VALUES = {"PLUG": "session-2", "AUTHORIZE ACCEPT": "ACCEPT", "AUTHORIZE DENY": "DENY", "REQUEST_KW": "9",
          "FAULT": "LATCH", "CLEAR": "CLEAR", "UNPLUG": "END"}
REFUSED = "refuse"
# (state, column) -> (state after the boundary, session kept?, request after, events) or REFUSED.
TABLE = {
    ("UNPLUGGED", "PLUG"): ("PLUGGED", "new", 0, []),
    ("UNPLUGGED", "AUTHORIZE ACCEPT"): REFUSED, ("UNPLUGGED", "AUTHORIZE DENY"): REFUSED,
    ("UNPLUGGED", "REQUEST_KW"): REFUSED,
    ("UNPLUGGED", "FAULT"): ("FAULTED", None, 0, ["FAULT"]),
    ("UNPLUGGED", "CLEAR"): REFUSED,
    ("UNPLUGGED", "UNPLUG"): ("UNPLUGGED", None, 0, []),
    ("PLUGGED", "PLUG"): REFUSED,
    ("PLUGGED", "AUTHORIZE ACCEPT"): ("AUTHORIZING", S1, 7, []),
    ("PLUGGED", "AUTHORIZE DENY"): ("PLUGGED", S1, 0, []),
    ("PLUGGED", "REQUEST_KW"): ("PLUGGED", S1, 9, []),
    ("PLUGGED", "FAULT"): ("FAULTED", S1, 0, ["FAULT"]),
    ("PLUGGED", "CLEAR"): REFUSED,
    ("PLUGGED", "UNPLUG"): ("UNPLUGGED", None, 0, []),
    ("AUTHORIZING", "PLUG"): REFUSED,
    ("AUTHORIZING", "AUTHORIZE ACCEPT"): REFUSED, ("AUTHORIZING", "AUTHORIZE DENY"): REFUSED,
    # The setup authorized at an earlier boundary, so this boundary also completes it (START).
    ("AUTHORIZING", "REQUEST_KW"): ("CHARGING", S1, 9, ["START"]),
    ("AUTHORIZING", "FAULT"): ("FAULTED", S1, 0, ["FAULT"]),
    ("AUTHORIZING", "CLEAR"): REFUSED,
    ("AUTHORIZING", "UNPLUG"): ("UNPLUGGED", None, 0, []),
    ("CHARGING", "PLUG"): REFUSED,
    ("CHARGING", "AUTHORIZE ACCEPT"): REFUSED, ("CHARGING", "AUTHORIZE DENY"): REFUSED,
    ("CHARGING", "REQUEST_KW"): ("CHARGING", S1, 9, []),
    ("CHARGING", "FAULT"): ("FAULTED", None, 0, ["FAULT", "ABORT"]),
    ("CHARGING", "CLEAR"): REFUSED,
    ("CHARGING", "UNPLUG"): ("UNPLUGGED", None, 0, ["END"]),
    ("FAULTED", "PLUG"): REFUSED,
    ("FAULTED", "AUTHORIZE ACCEPT"): REFUSED, ("FAULTED", "AUTHORIZE DENY"): REFUSED,
    ("FAULTED", "REQUEST_KW"): REFUSED,
    ("FAULTED", "FAULT"): ("FAULTED", S1, 0, []),
    ("FAULTED", "CLEAR"): ("PLUGGED", S1, 0, ["CLEAR"]),
    ("FAULTED", "UNPLUG"): REFUSED,
}


@pytest.mark.parametrize("cell", list(TABLE), ids=[f"{s}-{c}" for s, c in TABLE])
def test_every_table_cell(cell) -> None:
    state_name, column = cell
    kind = column.split(" ")[0]
    _, state = connector_in(state_name)
    expected = TABLE[cell]
    if expected == REFUSED:
        with pytest.raises(PhysicallyUnacceptable):
            apply(state, kind, VALUES[column])
        return
    want_state, want_session, want_request, want_events = expected
    minute = apply(state, kind, VALUES[column])
    after = minute.after.connector("c1")
    assert after.state == want_state
    if want_session == "new":
        assert after.session_id == S2
    else:
        assert after.session_id == want_session
    assert after.request_kw == want_request
    assert [e.kind for e in minute.events] == want_events
    assert after.fault == (want_state == "FAULTED")


def test_clear_of_a_faulted_connector_without_a_session_returns_unplugged() -> None:
    _, state = connector_in("FAULTED", with_session=False)
    minute = apply(state, "CLEAR", "CLEAR")
    after = minute.after.connector("c1")
    assert (after.state, after.session_id, after.fault) == ("UNPLUGGED", None, False)
    assert [(e.kind, e.session_id) for e in minute.events] == [("CLEAR", None)]


def test_a_started_fault_then_clear_returns_unplugged_and_a_new_plug_is_a_new_session() -> None:
    _, state = connector_in("CHARGING")
    faulted = apply(state, "FAULT", "LATCH").after
    cleared = apply(faulted, "CLEAR", "CLEAR").after
    assert (cleared.connector("c1").state, cleared.connector("c1").session_id) == ("UNPLUGGED", None)
    replugged = apply(cleared, "PLUG", "session-2").after
    assert replugged.connector("c1").session_id == S2


def test_authorization_completes_at_the_next_boundary_and_is_suppressed_by_unplug_or_fault() -> None:
    p = pack()
    state = EvState.initial(T0)
    plugged = p.step(state, (EvForcingRow(T0, "PLUG", "c1", "session-1"),
                             EvForcingRow(T0, "AUTHORIZE", "c1", "ACCEPT")))
    assert plugged.events == () and plugged.after.connector("c1").state == "AUTHORIZING"
    started = p.step(plugged.after)
    assert [e.kind for e in started.events] == ["START"]
    for kind, value in (("UNPLUG", "END"), ("FAULT", "LATCH")):
        suppressed = p.step(plugged.after, (EvForcingRow(at(1), kind, "c1", value),))
        assert "START" not in [e.kind for e in suppressed.events]


def test_same_minute_plug_then_fault_keeps_the_unstarted_session() -> None:
    minute = pack().step(EvState.initial(T0), (EvForcingRow(T0, "PLUG", "c1", "session-1"),
                                               EvForcingRow(T0, "FAULT", "c1", "LATCH")))
    c1 = minute.after.connector("c1")
    assert (c1.state, c1.session_id, c1.started) == ("FAULTED", S1, False)
    assert [(e.kind, e.session_id) for e in minute.events] == [("FAULT", S1)]


# --- guards ------------------------------------------------------------------------------------------


@pytest.mark.parametrize("bad", [
    ConnectorState("c1", state="CHARGING", session_id=None, started=True),
    ConnectorState("c1", state="PLUGGED", session_id=None),
    ConnectorState("c1", state="UNPLUGGED", session_id=S1),
    ConnectorState("c1", state="PLUGGED", session_id=S1, fault=True),
    ConnectorState("c1", state="GRID_PAUSED", session_id=S1),
    ConnectorState("c3"),
    ConnectorState("c1", state="PLUGGED", session_id=S1, allocated_kw=Fraction(1)),
    ConnectorState("c1", energy_kwh=Fraction(-1)),
])
def test_an_invalid_connector_state_is_refused(bad: ConnectorState) -> None:
    with pytest.raises(PhysicallyUnacceptable):
        bad.check()


def test_start_twice_and_a_second_terminal_are_refused() -> None:
    _, authorizing = connector_in("AUTHORIZING")
    with pytest.raises(PhysicallyUnacceptable, match="START twice"):
        pack().step(replace(authorizing, started_sessions=frozenset({S1})))
    _, charging_state = connector_in("CHARGING")
    with pytest.raises(PhysicallyUnacceptable, match="already has a terminal"):
        apply(replace(charging_state, terminal_sessions=frozenset({S1})), "UNPLUG", "END")


def test_plug_labels_follow_order_without_reuse_or_a_third_plug() -> None:
    with pytest.raises(PhysicallyUnacceptable):
        pack().step(EvState.initial(T0), (EvForcingRow(T0, "PLUG", "c1", "session-2"),))
    with pytest.raises(PhysicallyUnacceptable):
        pack().step(replace(EvState.initial(T0), plugs=2), (EvForcingRow(T0, "PLUG", "c1", "session-1"),))


@pytest.mark.parametrize("rows", [
    (EvForcingRow(T0, "AUTHORIZE", "c1", "ACCEPT"), EvForcingRow(T0, "PLUG", "c1", "session-1")),
    (EvForcingRow(T0, "PLUG", "c2", "session-1"), EvForcingRow(T0, "PLUG", "c1", "session-2")),
    (EvForcingRow(T0, "PLUG", "c1", "session-1"), EvForcingRow(T0, "PLUG", "c1", "session-1")),
    (EvForcingRow(T0, "GRID_LOSS", "c1", "LOST"),),
    (EvForcingRow(T0, "PLUG", "c3", "session-1"),),
    (EvForcingRow(at(1), "PLUG", "c1", "session-1"),),
])
def test_unordered_repeated_foreign_or_mistimed_forcing_is_refused(rows) -> None:
    with pytest.raises(PhysicallyUnacceptable):
        pack().step(EvState.initial(T0), rows)


def test_window_forcing_must_be_inside_minute_aligned_and_monotone() -> None:
    for rows in (
        (EvForcingRow(END, "PLUG", "c1", "session-1"),),
        (EvForcingRow(T0 + timedelta(seconds=30), "PLUG", "c1", "session-1"),),
        (EvForcingRow(at(5), "PLUG", "c1", "session-1"), EvForcingRow(at(1), "AUTHORIZE", "c1", "ACCEPT")),
    ):
        with pytest.raises(PhysicallyUnacceptable):
            run_window(pack(), start=T0, end=END, forcing=rows)


def test_the_closing_boundary_is_a_snapshot() -> None:
    state = both_charging()
    closing = pack().step(state, transition=False)
    assert closing.events == () and allocated(closing) == (Fraction(0), Fraction(0))
    assert closing.after.minute == T0
    with pytest.raises(PhysicallyUnacceptable):
        pack().step(state, (EvForcingRow(T0, "UNPLUG", "c1", "END"),), transition=False)
