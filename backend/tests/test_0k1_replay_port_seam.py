"""0K1: the forward replay port's seam (spec §2.2, D-0K1.1). No database."""

from __future__ import annotations

import ast
from pathlib import Path

from assetops_backend.runs import replay_port
from assetops_backend.runs.execution_ports import LabExecutionPort

BACKEND = Path(__file__).resolve().parents[1]
PORT = BACKEND / "assetops_backend" / "runs" / "replay_port.py"


def test_the_port_imports_exactly_its_four_modules() -> None:
    assert Path(replay_port.__file__).resolve() == PORT.resolve()
    modules = set()
    for node in ast.walk(ast.parse(PORT.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            modules |= {alias.name for alias in node.names}
        elif isinstance(node, ast.ImportFrom):
            modules.add(node.module)
    assert modules == {"__future__", "typing", "assetops_backend.runs.models", "assetops_contracts.forward_replay"}


def test_the_port_has_one_method() -> None:
    public = {name for name in vars(replay_port.ForwardReplayPort) if not name.startswith("_")}
    assert public == {"forward_replay"}


def test_the_lab_port_is_unchanged() -> None:
    public = {name for name, value in vars(LabExecutionPort).items() if not name.startswith("_") and callable(value)}
    assert public == {"projection", "start", "step", "run_to_end", "registered_stage", "staged_envelopes", "history",
                      "advance_publication", "publication_schedule", "gateway_diagnostics", "release_registered",
                      "registered_delivery"}


def test_nothing_else_in_the_backend_names_the_replay() -> None:
    allowed = {PORT.resolve(), Path(__file__).resolve(),
               (BACKEND / "assetops_backend" / "runs" / "replay_study.py").resolve(),
               (BACKEND / "tests" / "test_0k2_replay_study.py").resolve(),
               (BACKEND / "assetops_backend" / "runs" / "headroom_replay.py").resolve(),
               (BACKEND / "tests" / "test_0m_headroom_replay.py").resolve(),
               (BACKEND / "assetops_backend" / "runs" / "replay_series.py").resolve(),
               (BACKEND / "tests" / "test_0k3_replay_series.py").resolve()}
    scanned = 0
    offenders = []
    for path in BACKEND.rglob("*"):
        if not path.is_file() or "__pycache__" in path.parts or path.suffix in (".pyc", ".pyo"):
            continue
        if any(part.startswith(".") for part in path.relative_to(BACKEND).parts):
            continue
        scanned += 1
        if path.resolve() in allowed:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if "forward_replay" in text:
            offenders.append(str(path.relative_to(BACKEND)))
    assert scanned > 100, "vacuous: the scan found almost nothing"
    assert offenders == []
