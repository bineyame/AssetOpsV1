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
    history_payload,
)
from assetops_backend.sites_api import site_detail  # noqa: E402
from kobo import kobo_document, kobo_site  # noqa: E402
from test_generator_observation import CHANGED, draft, silenced  # noqa: E402
from test_lab_history import a_lab  # noqa: E402

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


if __name__ == "__main__":
    main()
