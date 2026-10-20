"""W3-01 commit 2 (q5 ruling 3, W3-02 Q8): self-tests for the read-only estate guard integration.

Each test writes one throwaway module into `backend/assetops_backend/estate/` (a path no tracked file uses), runs the
configuration-persistence seam (rules 1-8) and deletes the module again; no tracked file is modified.

    python -m pytest tools/checks/test_estate_guard.py

- `test_pg_reader_import_allowed`: a `$pgReaders` module may import the driver and run a SELECT.
- `test_pg_reader_write_rejected`: the same reader with one INSERT fails rule 8's single-writer refusal.
- `test_domain_driver_import_rejected`: a driver import in the estate package above `adapters/` fails rule 2, which
  only applies because `estate` is a `$domains` entry.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ESTATE = "backend/assetops_backend/estate"
# The second `$pgReaders` path; W3-02 creates it, so W3-01 can use it as a reader probe without editing a real file.
READER = f"{ESTATE}/adapters/postgres_evidence_money_read.py"
ABOVE_ADAPTERS = f"{ESTATE}/_guard_probe_driver.py"

READER_SELECT = (
    '"""Guard probe: a read-only estate adapter."""\n\n'
    "from sqlalchemy import text\n\n"
    '_PROBE = text("SELECT id FROM action WHERE tenant_id = :t")\n'
)
READER_INSERT = READER_SELECT + '_PROBE_WRITE = text("INSERT INTO action (id, tenant_id) VALUES (:i, :t)")\n'
DOMAIN_DRIVER = '"""Guard probe: storage technology above the estate adapter layer."""\n\nimport sqlalchemy\n'


def run_seam() -> subprocess.CompletedProcess[str]:
    script = ('$ErrorActionPreference = "Stop"; . (Join-Path $PWD "tools/checks/_common.ps1"); '
              '. (Join-Path $PWD "tools/checks/configuration-persistence.ps1"); '
              '$f = @(Invoke-ConfigurationPersistenceCheck); '
              'if ($f.Count -gt 0) { $f | ForEach-Object { Write-Output "- $_" }; exit 1 }; Write-Output "passed"')
    env = dict(os.environ, ASSETOPS_GUARD_PYTHON=sys.executable)
    return subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
                          cwd=ROOT, capture_output=True, text=True, env=env)


def with_probe(path: str, body: str) -> subprocess.CompletedProcess[str]:
    file = ROOT / path
    assert not file.exists(), f"{path} exists; the probe would overwrite a real module"
    try:
        file.write_text(body, encoding="utf-8")
        return run_seam()
    finally:
        file.unlink(missing_ok=True)


def failures(out: subprocess.CompletedProcess[str]) -> list[str]:
    return [line for line in out.stdout.splitlines() if line.startswith("- ")]


def test_pg_reader_import_allowed() -> None:
    out = with_probe(READER, READER_SELECT)
    assert out.returncode == 0, "\n".join(failures(out)) or out.stderr
    # The committed reader really imports the driver, so the allowance is exercised by the real tree too.
    real = (ROOT / f"{ESTATE}/adapters/postgres_estate_read.py").read_text(encoding="utf-8")
    assert "from sqlalchemy" in real or "import sqlalchemy" in real


def test_pg_reader_write_rejected() -> None:
    out = with_probe(READER, READER_INSERT)
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
