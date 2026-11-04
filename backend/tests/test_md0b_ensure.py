"""MD0b-R (build sheet MD-0 section 19): `ensure` builds the main template by default and the close template only on
demand, says so when the close test is not selected, and the drain runs in its own build part. Pure: no database."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("mechanism_dataset_tool", ROOT / "tools" / "mechanism_dataset.py")
tool = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tool)

BASE = json.dumps({"variants": {"close": {"a": 1}}, "x": 1})


@pytest.mark.parametrize("path", [
    "backend/assetops_backend/chain/lifecycle.py", "backend/assetops_backend/chain/lifecycle_run.py",
    "backend/assetops_backend/chain/threads.py", "backend/assetops_backend/chain/adapters/postgres_thread_store.py",
    "config/chain/thread-lifecycle-v1.json", "backend/tests/mechanism_dataset.py", "tools/mechanism_dataset.py"])
def test_each_close_input_selects_the_close_template(path: str) -> None:
    assert tool.close_needed([path], BASE, BASE) == [path]


@pytest.mark.parametrize("path", [
    "backend/assetops_backend/chain/read.py", "backend/assetops_backend/chain/adapters/postgres_chain_read.py",
    "frontend/src/App.tsx", "tools/checks/chain_coherence.py", "config/chain/coverage-policy-v1.json"])
def test_other_paths_do_not(path: str) -> None:
    assert tool.close_needed([path], BASE, BASE) == []


def test_the_fixture_selects_it_only_when_variants_close_changed() -> None:
    fx = [tool.FIXTURE]
    assert tool.close_needed(fx, BASE, json.dumps({"variants": {"close": {"a": 1}}, "x": 2})) == []
    assert tool.close_needed(fx, BASE, json.dumps({"variants": {"close": {"a": 2}}, "x": 1})) != []
    assert tool.close_needed(fx, None, BASE) != []  # no base to compare: treated as changed


def _ensure(monkeypatch, capsys, close, paths, matches=()):
    built = []
    monkeypatch.setattr(tool, "_match", lambda ds="states": ("tpl" if ds in matches else None, [], False))
    monkeypatch.setattr(tool, "slice_inputs", lambda *a: (paths, BASE, BASE))

    def build(ds, budget, resume):
        built.append(ds)
        matches_list.append(ds)
        return 0

    matches_list = list(matches)
    monkeypatch.setattr(tool, "_match", lambda ds="states": ("tpl" if ds in matches_list else None, [], False))
    monkeypatch.setattr(tool, "build", build)
    assert tool.ensure(close) == 0
    return built, capsys.readouterr().out


def test_ensure_builds_only_main_and_says_the_close_test_is_not_selected(monkeypatch, capsys) -> None:
    built, out = _ensure(monkeypatch, capsys, "auto", ["frontend/src/App.tsx"])
    assert built == ["states"]
    assert '"ensure": "close not selected"' in out and tool.CLOSE_TEST in out  # explicit, never silent


def test_ensure_builds_close_when_the_slice_touches_a_close_input(monkeypatch, capsys) -> None:
    built, out = _ensure(monkeypatch, capsys, "auto", ["config/chain/thread-lifecycle-v1.json"])
    assert built == ["states", "close"] and "close not selected" not in out


def test_ensure_builds_close_on_request_and_when_the_diff_is_unreadable(monkeypatch, capsys) -> None:
    assert _ensure(monkeypatch, capsys, "yes", [])[0] == ["states", "close"]
    built, out = _ensure(monkeypatch, capsys, "auto", None)
    assert built == ["states", "close"] and "cannot be read" in out


def test_ensure_reuses_a_matching_close_template_and_selects_its_test(monkeypatch, capsys) -> None:
    built, out = _ensure(monkeypatch, capsys, "auto", ["frontend/src/App.tsx"], matches=["close"])
    assert built == ["states"] and "close not selected" not in out


def test_the_deselected_node_is_the_real_close_test_and_the_runner_deselects_it() -> None:
    path, name = tool.CLOSE_TEST.split("::")
    assert f"def {name}(" in (ROOT / path).read_text(encoding="utf-8")
    assert tool.CLOSE_TEST in (ROOT / "tools" / "run-backend-suite-in-container.sh").read_text(encoding="utf-8")


def test_the_drain_estimate_is_its_own_and_never_the_ordinary_steps() -> None:
    steps = ["begin", "D1", "D2", "drain_mini"]
    assert tool._estimate({"begin": 5, "D1": 40, "drain_mini": 400}, steps, "D2") == 40  # drain excluded
    assert tool._estimate({"begin": 5, "D1": 40, "drain_mini": 400}, steps, "drain_mini") == 400
    assert tool._estimate({}, steps, "begin") == 60.0
