"""T025e AC1-AC2: a live history only ever grows at its end.

The live-follow read (`since_boundary`) sends only the rows of each append
family recorded after the client's last boundary, and the client appends them
to what it holds. That is sound only if the capture at a later boundary m,
restricted to time keys at or before an earlier boundary k, is exactly the
capture at k - row by row and in order - and every row past k's time sits
after that prefix. A family that failed this would have to be sent whole on
every read; none may be patched on the client.

The property is checked between every pair of consecutive boundaries of two
fixture live sessions, which by transitivity covers every k < m. Between them
the fixtures exercise every append family: a controlled mini-grid (intervals,
discrete transitions) and a fuel run with a reporting gap, a windowed removal
and a bounded delivery (suppressed attempts, applied events, a bounded
transition). The time keys are the backend's own table, so this guard binds
the selection the route actually makes.
"""

from __future__ import annotations

from bisect import bisect_right
from pathlib import Path

import pytest

from assetops_backend.runs.adapters.yaml_run_documents import read_run_record
from assetops_backend.simulator_lab_api import (
    HISTORY_APPEND_FAMILY_KEYS,
    HISTORY_STATIC_FAMILIES,
    HISTORY_STEP_OWNED_FAMILIES,
    history_delta_payload,
    history_payload,
)
from lab_execution import HostLabExecution, YamlExecutionArtifacts, project
from source_stages import JsonSourceStages

from test_mini_grid_v2 import PROLONGED, draft

GATE_RUNS = Path(__file__).resolve().parent / "contract9_gate" / "runs"
FUEL_WITH_GAP = GATE_RUNS / "run-c9000000000000000000000000000102.yaml"
FIXTURES = (
    "mini-grid",
    "fuel-with-gap",
    "fuel-mid-step-window",
    "mini-grid-multi-window",
)


def multi_window_edit(document) -> None:
    """R2 (R1-1): the mill's second demand window opens at 62, mid-step, at an
    address that sorts between other forcing addresses (the kernel records
    exposures by address, then `from_offset`)."""
    for entry in document["timeline"]:
        if entry["event_id"] == "mill-demand-1":
            entry["timing"]["duration_minutes"] = 62
        if entry["event_id"] == "mill-demand-2":
            entry["offset_minutes"] = 62
            entry["timing"]["duration_minutes"] = 58



def a_run(name: str, scratch_dir: Path):
    if name == "mini-grid":
        return draft(PROLONGED)
    if name == "mini-grid-multi-window":
        return draft(PROLONGED, document_edit=multi_window_edit)
    if name == "fuel-mid-step-window":
        # R1 finding 1: the generator window opens at 1082, between the 1080
        # and 1085 boundaries, so its exposure is recorded by boundary 1080
        # while its own offset lies after it.
        text = FUEL_WITH_GAP.read_text(encoding="utf-8")
        moved = text.replace("    offset_minutes: 1080" + chr(10), "    offset_minutes: 1082" + chr(10))
        assert moved != text
        scratch = scratch_dir / "mid-step-run.yaml"
        scratch.write_text(moved, encoding="utf-8")
        try:
            return read_run_record(scratch)
        finally:
            scratch.unlink()
    return read_run_record(FUEL_WITH_GAP)


def a_lab(root: Path) -> HostLabExecution:
    return HostLabExecution(
        artifacts=YamlExecutionArtifacts(root),
        stages=JsonSourceStages(root / "stages"),
    )


def key_of(family: str, boundaries=()):
    """The offset of the boundary that records a row of `family`.

    Step-owned families are recorded by the last boundary at or before their
    own offset, read from the later capture's boundaries.
    """
    attribute = HISTORY_APPEND_FAMILY_KEYS[family]
    if family in HISTORY_STEP_OWNED_FAMILIES:
        offsets = [b.offset_minutes for b in boundaries]
        return lambda row: offsets[max(bisect_right(offsets, getattr(row, attribute)) - 1, 0)]
    return lambda row: getattr(row, attribute)


def live_captures(run, root: Path):
    """Every capture of one live session, one per boundary, start to end.

    Advanced on the execution handle directly: the prefix property is about
    `capture`, and going through `step` would restage the whole series each
    boundary for nothing this test reads.
    """
    lab = a_lab(root)
    lab.start(run)
    session = lab._sessions[run.run_id]
    execution = session.execution
    captures = [lab._captured(session, project(session))]
    while not execution.is_terminal:
        execution.advance(1)
        captures.append(lab._captured(session, project(session)))
    return run, captures


@pytest.fixture(scope="module", params=FIXTURES)
def session(request, tmp_path_factory):
    return live_captures(
        a_run(request.param, tmp_path_factory.mktemp(f"run-{request.param}")),
        tmp_path_factory.mktemp(f"prefix-{request.param}"),
    )


@pytest.mark.parametrize("family", sorted(HISTORY_APPEND_FAMILY_KEYS))
def test_each_append_family_grows_only_at_its_end(session, family) -> None:
    _, captures = session
    assert len(captures) > 2
    for earlier, later in zip(captures, captures[1:]):
        key = key_of(family, later.boundaries)
        # None before the first boundary is recorded: nothing is held yet.
        through = earlier.recorded_through_offset
        held = (lambda row: False) if through is None else (lambda row: key(row) <= through)
        before = getattr(earlier, family)
        after = getattr(later, family)
        restricted = tuple(row for row in after if held(row))
        assert restricted == before, (family, through)
        assert after[: len(before)] == before, (family, through)
        assert not any(held(row) for row in after[len(before) :]), (family, through)


def test_the_fixtures_exercise_every_append_family(tmp_path_factory) -> None:
    """Non-vacuity: between them the two sessions record a row of each family."""
    seen: set[str] = set()
    for name in FIXTURES:
        run = a_run(name, tmp_path_factory.mktemp(f"run-{name}"))
        lab = a_lab(tmp_path_factory.mktemp(f"coverage-{name}"))
        lab.start(run)
        lab.run_to_end(run)
        history = lab.history(run)
        seen |= {f for f in HISTORY_APPEND_FAMILY_KEYS if getattr(history, f)}
    assert seen == set(HISTORY_APPEND_FAMILY_KEYS)


def test_folding_every_delta_reproduces_the_full_read(session) -> None:
    """AC1 composed: the delta read at each boundary, appended in order to the
    first full read, is the full read at the end - every append family row for
    row, and the whole-sent fields as the last delta states them."""
    run, captures = session
    held = history_payload(captures[0], run)
    for capture in captures[1:]:
        since = held["boundaries_recorded"]
        delta = history_delta_payload(capture, since, run)
        assert delta["history_digest"] is None
        assert delta["drawing_context"] is None
        for family in set(HISTORY_STATIC_FAMILIES) - {"drawing_context"}:
            assert delta[family] == [], family
        for family in HISTORY_APPEND_FAMILY_KEYS:
            held[family] = held[family] + delta[family]
        for key, value in delta.items():
            if key not in HISTORY_APPEND_FAMILY_KEYS and key not in HISTORY_STATIC_FAMILIES:
                held[key] = value
    full = history_payload(captures[-1], run)
    assert held == full


def test_a_mid_step_window_is_recorded_by_the_step_it_lies_in(tmp_path_factory) -> None:
    """The fixture is non-vacuous: an exposure's offset is not a boundary's."""
    run, captures = live_captures(
        a_run("fuel-mid-step-window", tmp_path_factory.mktemp("mid-run")),
        tmp_path_factory.mktemp("mid-step"),
    )
    last = captures[-1]
    offsets = {b.offset_minutes for b in last.boundaries}
    mid = [e for e in last.exposures if e.from_offset not in offsets]
    assert mid, "no exposure opens between boundaries"
    # Boundary 1080 already holds the exposure that opens at 1082.
    at_1080 = next(c for c in captures if c.recorded_through_offset == 1080)
    assert any(e.from_offset == 1082 for e in at_1080.exposures)


def test_a_delta_from_any_full_read_base_folds_to_the_full_read(session) -> None:
    """No duplicate and no gap whichever boundary a full read based the
    client at: the 49-versus-50 case of the T025e review."""
    run, captures = session
    full = history_payload(captures[-1], run)
    last = len(captures) - 1
    bases = sorted({*range(0, last, 10), *range(max(last - 3, 0), last)} | {
        i for i, c in enumerate(captures) if c.recorded_through_offset in (1075, 1080, 1085)
    })
    for k in bases:
        held = history_payload(captures[k], run)
        delta = history_delta_payload(captures[-1], held["boundaries_recorded"], run)
        for family in HISTORY_APPEND_FAMILY_KEYS:
            held[family] = held[family] + delta[family]
        for name, value in delta.items():
            if name not in HISTORY_APPEND_FAMILY_KEYS and name not in HISTORY_STATIC_FAMILIES:
                held[name] = value
        assert held == full, k


def test_a_delta_read_of_a_persisted_run_changes_no_byte(tmp_path) -> None:
    run = a_run("fuel-with-gap", tmp_path)
    lab = a_lab(tmp_path)
    lab.start(run)
    lab.run_to_end(run)
    path = tmp_path / f"{run.run_id}.yaml"
    before = path.read_bytes()

    reloaded = a_lab(tmp_path).history(run)
    assert reloaded.source == "PERSISTED", reloaded.notes
    assert reloaded.history_digest is not None
    delta = history_delta_payload(reloaded, 10, run)

    assert delta["history_digest"] is None
    assert delta["boundaries"][0]["step_index"] == 10
    assert path.read_bytes() == before
