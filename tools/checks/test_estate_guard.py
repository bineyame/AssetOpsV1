"""W3-01 commit 2 (q5 ruling 3, c2 r1 q11-A 2): self-tests for the read-only estate guard integration.

Each test copies the guard inputs (`tools/`, `backend/assetops_backend/`, `config/`, `contracts/`) into a private
temporary directory, edits the copy, and runs the configuration-persistence seam (rules 1-8) there; the tracked
workspace is never written. `tools/check-all.ps1` runs this file as a required step.

    python -m pytest tools/checks/test_estate_guard.py

- `test_pg_reader_import_allowed`: the real `$pgReaders` module (`estate/adapters/postgres_estate_read.py`) imports
  the driver and reads, and the seam passes; the same driver import in an unlisted adapter module is refused.
- `test_pg_reader_write_rejected`: the same reader with one INSERT fails rule 8's single-writer refusal.
- `test_domain_driver_import_rejected`: a driver import in the estate package above `adapters/` fails rule 2, which
  only applies because `estate` is a `$domains` entry.
W3-02 adds its own reader path to `$pgReaders` with its own reviewed file and guard test.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

NL = chr(10)
ROOT = Path(__file__).resolve().parents[2]
ESTATE = "backend/assetops_backend/estate"
READER = f"{ESTATE}/adapters/postgres_estate_read.py"
UNLISTED = f"{ESTATE}/adapters/_guard_probe_unlisted_read.py"
ABOVE_ADAPTERS = f"{ESTATE}/_guard_probe_driver.py"
GUARD_INPUTS = ("tools", "backend/assetops_backend", "backend/migrations", "config", "contracts", ".gitignore")

READER_SELECT = (
    '"""Guard probe: a read-only estate adapter."""\n\n'
    "from sqlalchemy import text\n\n"
    '_PROBE = text("SELECT id FROM action WHERE tenant_id = :t")\n'
)
READER_INSERT = '\n_PROBE_WRITE = text("INSERT INTO action (id, tenant_id) VALUES (:i, :t)")\n'
DOMAIN_DRIVER = '"""Guard probe: storage technology above the estate adapter layer."""\n\nimport sqlalchemy\n'


def run_seam(cwd: Path) -> subprocess.CompletedProcess[str]:
    script = ('$ErrorActionPreference = "Stop"; . (Join-Path $PWD "tools/checks/_common.ps1"); '
              '. (Join-Path $PWD "tools/checks/configuration-persistence.ps1"); '
              '$f = @(Invoke-ConfigurationPersistenceCheck); '
              'if ($f.Count -gt 0) { $f | ForEach-Object { Write-Output "- $_" }; exit 1 }; Write-Output "passed"')
    env = dict(os.environ, ASSETOPS_GUARD_PYTHON=sys.executable)
    return subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
                          cwd=cwd, capture_output=True, text=True, env=env)


def isolated_copy(edit) -> subprocess.CompletedProcess[str]:
    """Run the seam over a temporary copy of the guard inputs after `edit(copy_root)`."""
    with tempfile.TemporaryDirectory(prefix="estate-guard-") as tmp:
        copy = Path(tmp)
        for name in GUARD_INPUTS:
            source = ROOT / name
            if source.is_file():
                shutil.copy2(source, copy / name)
            elif source.exists():
                shutil.copytree(source, copy / name, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        edit(copy)
        return run_seam(copy)


def with_probe(path: str, body: str) -> subprocess.CompletedProcess[str]:
    def edit(copy: Path) -> None:
        file = copy / path
        assert not file.exists(), f"{path} exists in the copy"
        file.write_text(body, encoding="utf-8")
    return isolated_copy(edit)


def failures(out: subprocess.CompletedProcess[str]) -> list[str]:
    return [line for line in out.stdout.splitlines() if line.startswith("- ")]


def test_pg_reader_import_allowed() -> None:
    out = isolated_copy(lambda copy: None)  # the real reader, unmodified, imports the driver and reads
    assert out.returncode == 0, NL.join(failures(out)) or out.stderr
    real = (ROOT / READER).read_text(encoding="utf-8")
    assert "from sqlalchemy" in real or "import sqlalchemy" in real
    refused = with_probe(UNLISTED, READER_SELECT)  # the allowance is the listed path, not the adapter layer
    assert refused.returncode == 1 and any(
        "Database driver imported outside" in line and UNLISTED in line for line in failures(refused)), refused.stdout


def test_pg_reader_write_rejected() -> None:
    def edit(copy: Path) -> None:
        file = copy / READER
        file.write_text(file.read_text(encoding="utf-8") + READER_INSERT, encoding="utf-8")
    out = isolated_copy(edit)
    found = failures(out)
    assert out.returncode == 1
    assert any(f"A second product database writer in {READER}:" in line for line in found), found
    assert not any("Database driver imported outside" in line and READER in line for line in found), found


def test_domain_driver_import_rejected() -> None:
    out = with_probe(ABOVE_ADAPTERS, DOMAIN_DRIVER)
    found = failures(out)
    assert out.returncode == 1
    assert any(f"Storage technology above the adapter layer in {ABOVE_ADAPTERS}:" in line for line in found), found
    assert any(f"Database driver imported outside" in line and ABOVE_ADAPTERS in line for line in found), found


# W5-02a K1b (ruling A5/B3): the read-only domain Action index adapter is a listed `$pgReaders` module - its driver
# import is admitted, and one INSERT in it still fails rule 8's single-writer refusal.
DOMAIN_READER = "backend/assetops_backend/work/adapters/postgres_domain_action_index.py"
DOMAIN_READER_INSERT = '\n_PROBE_WRITE = text("INSERT INTO domain_action (id, tenant_id) VALUES (:i, :t)")\n'


def test_domain_action_index_reader_allowed_and_write_rejected() -> None:
    real = (ROOT / DOMAIN_READER).read_text(encoding="utf-8")
    assert "from sqlalchemy" in real

    def edit(copy: Path) -> None:
        file = copy / DOMAIN_READER
        file.write_text(file.read_text(encoding="utf-8") + DOMAIN_READER_INSERT, encoding="utf-8")
    out = isolated_copy(edit)
    found = failures(out)
    assert out.returncode == 1
    assert any(f"A second product database writer in {DOMAIN_READER}:" in line for line in found), found
    assert not any("Database driver imported outside" in line and DOMAIN_READER in line for line in found), found
