"""DS1a T1, T10: determinism across processes and the CLI (spec §10)."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

from .conftest import CLI, FIXTURE, GOLDEN, REPOSITORY_ROOT


def _run(args: list[str], cwd: Path, seed: str = "0") -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["PYTHONHASHSEED"] = seed
    env.pop("PYTHONPATH", None)  # the CLI sets its own path (P10)
    return subprocess.run([sys.executable, str(CLI), *args], cwd=cwd, env=env,
                          capture_output=True, text=True, check=False)


def test_t1_determinism_two_processes(tmp_path: Path) -> None:
    outs = []
    for seed in ("1", "2"):
        cwd = tmp_path / f"cwd{seed}"
        cwd.mkdir()
        out = cwd / "history.json"
        done = _run(["generate", "--manifest", str(FIXTURE), "--out", str(out)], cwd, seed)
        assert done.returncode == 0, done.stderr
        outs.append(out.read_bytes())
    assert outs[0] == outs[1]
    golden = json.loads(GOLDEN.read_text(encoding="utf-8"))
    assert hashlib.sha256(outs[0]).hexdigest() == golden["file_sha256"]


def test_t10_check_and_diff(tmp_path: Path) -> None:
    out = tmp_path / "history.json"
    assert _run(["generate", "--manifest", str(FIXTURE), "--out", str(out)], tmp_path).returncode == 0
    ok = _run(["check", "--manifest", str(FIXTURE), "--history", str(out)], tmp_path)
    assert ok.returncode == 0, ok.stdout + ok.stderr

    text = out.read_text(encoding="utf-8")
    # change the first digit of Thika's July crate_days, inside one scope block
    target = text.index('"Room B · Thika"')
    pos = text.index('"crate_days": ', target) + len('"crate_days": ')
    digit = text[pos]
    changed = text[:pos] + ("1" if digit != "1" else "2") + text[pos + 1:]
    out.write_text(changed, encoding="utf-8")
    bad = _run(["check", "--manifest", str(FIXTURE), "--history", str(out)], tmp_path)
    assert bad.returncode == 1
    assert bad.stdout.strip() == "DS1_CHECK_DIFF harvest-cold/Room B · Thika/2026-07", bad.stdout


def test_t10_view_command_and_json_manifest(tmp_path: Path) -> None:
    out = tmp_path / "view.json"
    done = _run(["view", "--manifest", str(FIXTURE), "--out", str(out)], tmp_path)
    assert done.returncode == 0, done.stderr
    assert out.read_bytes() == FIXTURE.read_bytes()  # the fixture is a view; viewing it is idempotent


def test_t10_yaml_manifest_accepted(tmp_path: Path) -> None:
    manifest = REPOSITORY_ROOT / "Docs" / "demo-sprint" / "product-direction-layer4" / "demo-site-scenario-manifest.yaml"
    out = tmp_path / "view.json"
    done = _run(["view", "--manifest", str(manifest), "--out", str(out)], tmp_path)
    assert done.returncode == 0, done.stderr
    assert json.loads(out.read_text(encoding="utf-8"))["accounting_period"] == "2026-10"
