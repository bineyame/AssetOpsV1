r"""Regenerate the frontend's T025c chart fixtures from a real Lab execution.

Not a test (no `test_` prefix, so pytest does not collect it). Run from `host/`:

    ..\.venv\Scripts\python.exe tests\make_history_fixtures.py

It executes the policy-varied Kobo recipe (`kobo-mini-grid-stop-60`, mini-grid
v2, publication profile 4, 5-minute step) with the generator controller's
status silenced for 30 minutes from offset 60, steps a live session to offset
150, and writes the backend's own `history_payload` and `execution_payload` of
that prefix, with the Kobo Site detail the run froze (T025d). Nothing is edited after serialization, so every value a frontend
test asserts is one the backend produces.
"""

from __future__ import annotations

import copy
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

from assetops_backend.simulator_lab_api import (  # noqa: E402
    execution_payload,
    history_delta_payload,
    history_payload,
)
from assetops_backend.sites_api import site_detail  # noqa: E402
from kobo import kobo_document, kobo_site  # noqa: E402
from test_generator_observation import CHANGED, draft, silenced  # noqa: E402
from test_lab_history import a_lab  # noqa: E402
from test_lab_history_prefix import multi_window_edit  # noqa: E402
from test_mini_grid_v2 import PROLONGED  # noqa: E402
from test_mini_grid_v2 import draft as mini_grid_draft  # noqa: E402

OUT = HERE.parents[1] / "frontend" / "src" / "shell" / "__tests__"
SILENCE_FROM = 60
THROUGH = 150


def document():
    raw = silenced(kobo_document(CHANGED))
    raw = copy.deepcopy(raw)
    for entry in raw["timeline"]:
        if entry["event_id"] == "generator-status-gap":
            entry["offset_minutes"] = SILENCE_FROM
            entry["timing"]["duration_minutes"] = 30
    return raw


def main() -> None:
    run = draft(document=document())
    lab = a_lab(Path(tempfile.mkdtemp()))
    projection = lab.start(run)
    while projection.offset_minutes < THROUGH:
        projection = lab.step(
            run, boundaries=1, from_boundary=projection.boundaries_completed
        )
    assert projection.offset_minutes == THROUGH, projection.offset_minutes
    (OUT / "kobo-policy-history-prefix.json").write_text(
        json.dumps(history_payload(lab.history(run), run), separators=(",", ":")),
        encoding="utf-8",
    )
    # T025d: the Site the run froze, as the Site detail read serves it, so the
    # run-bound drawing is checked against the same Foundation the run used.
    (OUT / "kobo-site-detail.json").write_text(
        json.dumps(site_detail(kobo_site()), separators=(",", ":")),
        encoding="utf-8",
    )
    (OUT / "kobo-policy-execution-prefix.json").write_text(
        json.dumps(execution_payload(projection), separators=(",", ":")),
        encoding="utf-8",
    )
    prolonged_prefix()
    live_deltas()
    mid_step_deltas()
    multi_window_deltas()


def prolonged_prefix() -> None:
    """`kobo-mini-grid-history-prefix.json`: the prolonged recipe, 7 boundaries.

    T025c wrote this payload by hand-run script; T025d regenerates it here so
    the wire's later additions are the backend's own, never hand-edited.
    """
    run = mini_grid_draft(PROLONGED)
    lab = a_lab(Path(tempfile.mkdtemp()))
    projection = lab.start(run)
    while projection.boundaries_completed < 7:
        projection = lab.step(
            run, boundaries=1, from_boundary=projection.boundaries_completed
        )
    (OUT / "kobo-mini-grid-history-prefix.json").write_text(
        json.dumps(history_payload(lab.history(run), run), separators=(",", ":")),
        encoding="utf-8",
    )


def live_deltas() -> None:
    """`kobo-mini-grid-history-deltas.json`: live follow on the wire (T025e).

    The prolonged recipe's full read after start, the `since_boundary` delta
    read after each of 7 single steps, one delta covering all 7 at once, and
    the full read at the end - each exactly the route's answer - so the
    client's merge is tested against deltas the backend produces.
    """
    run = mini_grid_draft(PROLONGED)
    lab = a_lab(Path(tempfile.mkdtemp()))
    projection = lab.start(run)
    base = history_payload(lab.history(run), run)
    held = base["boundaries_recorded"]
    deltas = []
    for _ in range(7):
        projection = lab.step(
            run, boundaries=1, from_boundary=projection.boundaries_completed
        )
        history = lab.history(run)
        deltas.append(delta_read(history, held, run))
        held = len(history.boundaries)
    history = lab.history(run)
    document = {
        "base": base,
        "deltas": deltas,
        "jump": delta_read(history, base["boundaries_recorded"], run),
        "full": history_payload(history, run),
    }
    (OUT / "kobo-mini-grid-history-deltas.json").write_text(
        json.dumps(document, separators=(",", ":")), encoding="utf-8"
    )


def mid_step_deltas() -> None:
    """`kobo-fuel-mid-step-deltas.json`: a forcing window that opens mid-step.

    The fuel gate run with `generator-run-window` moved to offset 7, between
    the 5 and 10 boundaries, so its exposure is recorded by boundary 5 while
    its own offset lies after it (T025e R1 finding 1). The full read after
    start, the delta after each of 4 single steps, and a second base - the full
    read after the first step, which already holds that exposure - with the
    delta after the step that follows it.
    """
    from assetops_backend.runs.adapters.yaml_run_documents import read_run_record

    gate = HERE / "contract9_gate" / "runs" / "run-c9000000000000000000000000000102.yaml"
    text = gate.read_text(encoding="utf-8")
    moved = text.replace("    offset_minutes: 1080" + chr(10), "    offset_minutes: 7" + chr(10))
    assert moved != text
    scratch = Path(tempfile.mkdtemp()) / "mid-step-run.yaml"
    scratch.write_text(moved, encoding="utf-8")
    run = read_run_record(scratch)
    lab = a_lab(Path(tempfile.mkdtemp()))
    projection = lab.start(run)
    base = history_payload(lab.history(run), run)
    held = base["boundaries_recorded"]
    deltas = []
    rebased = None
    rebased_base = None
    for index in range(4):
        projection = lab.step(
            run, boundaries=1, from_boundary=projection.boundaries_completed
        )
        history = lab.history(run)
        if index == 2:
            rebased = {
                "base": rebased_base,
                "read": delta_read(history, len(rebased_boundaries), run),
            }
        deltas.append(delta_read(history, held, run))
        held = len(history.boundaries)
        if index == 1:
            rebased_base = history_payload(history, run)
            rebased_boundaries = history.boundaries
    history = lab.history(run)
    document = {
        "base": base,
        "deltas": deltas,
        "rebased": rebased,
        "full": history_payload(history, run),
    }
    (OUT / "kobo-fuel-mid-step-deltas.json").write_text(
        json.dumps(document, separators=(",", ":")), encoding="utf-8"
    )


def multi_window_deltas() -> None:
    """`kobo-mini-grid-multi-window-deltas.json`: several forcing addresses, one
    window opening mid-step at a non-last address (T025e R2, finding R1-1).

    The prolonged recipe with the mill's second demand window opening at 62.
    The kernel records exposures by `(address, from_offset)`, so the step
    holding 62 lists `load-mill@62` after `load-res@60`-style rows that start
    earlier. The full read after start, the delta after each of 14 single
    steps, and a second base - the full read after 12 steps - with the delta
    after the step that follows.
    """
    run = mini_grid_draft(PROLONGED, document_edit=multi_window_edit)
    lab = a_lab(Path(tempfile.mkdtemp()))
    projection = lab.start(run)
    base = history_payload(lab.history(run), run)
    held = base["boundaries_recorded"]
    deltas = []
    rebased_base = None
    rebased = None
    for index in range(14):
        projection = lab.step(
            run, boundaries=1, from_boundary=projection.boundaries_completed
        )
        history = lab.history(run)
        if index == 12:
            rebased = {"base": rebased_base, "read": delta_read(history, rebased_held, run)}
        deltas.append(delta_read(history, held, run))
        held = len(history.boundaries)
        if index == 11:
            rebased_base = history_payload(history, run)
            rebased_held = held
    history = lab.history(run)
    document = {
        "base": base,
        "deltas": deltas,
        "rebased": rebased,
        "full": history_payload(history, run),
    }
    (OUT / "kobo-mini-grid-multi-window-deltas.json").write_text(
        json.dumps(document, separators=(",", ":")), encoding="utf-8"
    )


def delta_read(history, since: int, run) -> dict:
    """The route's `?since_boundary=` answer, envelope and all."""
    return {
        "history": history_delta_payload(history, since, run),
        "delta": {"since_boundary": since, "through_boundary": len(history.boundaries)},
    }


if __name__ == "__main__":
    main()
