"""CH-5c CH5c-R6 (L0/L1, no database): the tick child and the serve child of `tools/demo_combined.py` share one
environment, so the tick's pre-built rows carry the server's `code_version`.

The work folder is `tmp_path`, holding the `story.json` that prepare would write (the tick reads it).
The children are captured (no process starts for them); each captured environment's `code_version()` is computed
in a fresh child interpreter over this worktree's backend, so the comparison is the one a real tick and a real
server would make. The keyless control proves the comparison can fail: the cursor keys move `code_version`.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

import demo_combined as tool  # noqa: E402

from assetops_backend.chain.watermark import SERVE_KEYS  # noqa: E402

VERSION = "from assetops_backend.chain.composition import code_version; print(code_version())"


class _Child:
    pid = 0

    def wait(self, timeout=None):  # noqa: ARG002
        return 0


def _captured_envs(tmp_path, monkeypatch) -> dict[str, dict[str, str]]:
    demo = tool.Demo("assetops_demo3_parity_test", "var/demo3_parity")
    demo.work, demo.tree = tmp_path, tmp_path / "tree"
    (tmp_path / "story.json").write_text(json.dumps({"sites": list(tool.SITES)}), encoding="utf-8")
    (tmp_path / "keys.json").write_text(json.dumps({k: os.urandom(32).hex() for k in tool.KEY_NAMES}),
                                        encoding="utf-8")
    seen: dict[str, dict[str, str]] = {}
    demo.read_site_mark = lambda site: None  # E4-C4: no database here; no mark means the run is due

    def popen(argv, **kw):
        seen["tick" if "tick" in argv else "serve" if "uvicorn" in argv else str(argv[1:3])] = dict(kw["env"])
        return _Child()

    with monkeypatch.context() as patch:  # only the demo's children are captured; `_version` starts real ones
        patch.setattr(tool.subprocess, "Popen", popen)
        demo.tick()
    seen["serve_env"] = demo.serve_env()  # the serve child's environment (`Demo.serve` passes exactly this)
    return seen


def _version(env: dict[str, str]) -> str:
    child = dict(env)
    child["PYTHONPATH"] = os.pathsep.join(str(REPO / p) for p in ("backend", "contracts", "tools"))
    out = subprocess.run([sys.executable, "-c", VERSION], env=child, capture_output=True, text=True, timeout=120,
                         cwd=str(REPO))
    assert out.returncode == 0, out.stderr[-2000:]
    return out.stdout.strip()


def test_serve_keys_are_the_demo_cursor_keys() -> None:
    assert tuple(tool.KEY_NAMES) == SERVE_KEYS


def test_the_tick_child_and_the_serve_child_compute_one_code_version(tmp_path, monkeypatch) -> None:
    envs = _captured_envs(tmp_path, monkeypatch)
    tick, serve = envs["tick"], envs["serve_env"]
    assert all(tick.get(k) for k in tool.KEY_NAMES)
    assert {k: tick.get(k) for k in tool.KEY_NAMES} == {k: serve.get(k) for k in tool.KEY_NAMES}
    tick_version = _version(tick)
    assert tick_version == _version(serve)
    keyless = {k: v for k, v in tick.items() if k not in tool.KEY_NAMES}
    assert _version(keyless) != tick_version  # control: a keyless tick would never be hit by the server


def test_the_serve_child_is_started_with_the_serve_env() -> None:
    import inspect

    assert "env=self.serve_env()" in inspect.getsource(tool.Demo.serve)
