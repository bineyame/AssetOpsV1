"""T2 (R9): select-tests names the neutral package tests (`neutral` key) for the files that can affect them."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def select(path: str) -> dict:
    out = subprocess.run([sys.executable, "tools/select-tests.py", "--files", path, "--json"], cwd=ROOT,
                         capture_output=True, text=True, check=True, encoding="utf-8").stdout
    result = json.loads(out)
    assert "neutral" in result, f"{path}: the JSON has no neutral key"
    return result


def test_simulator_path_is_neutral():
    assert select("simulator/assetops_simulator/world/history.py")["neutral"] is True


def test_contracts_path_is_neutral():
    assert select("contracts/assetops_contracts/control.py")["neutral"] is True


def test_world_history_cli_is_neutral_and_stays_full():
    result = select("tools/world_history.py")
    assert result["neutral"] is True
    assert result["mode"] == "full"


def test_backend_path_is_not_neutral():
    assert select("backend/assetops_backend/perf.py")["neutral"] is False


def test_markdown_under_simulator_is_not_neutral():
    assert select("simulator/README.md")["neutral"] is False
