"""Make the composition leaf importable to its own tests.

`host/` is not installed, because nothing imports it. pytest adds a conftest's
own directory to `sys.path`, so this file existing is what lets
`host/tests/*` import `execution_adapter` - and its docstring is what stops a
later reader deleting an apparently empty file.

It also redirects pytest's temporary base when the default is unwritable, for the
reason `backend/tests/conftest.py` records: a sandboxed agent whose write access
stops at the workspace cannot create `pytest-of-<user>`, and three reviews of
this repository could not run a suite because of it.
"""

from __future__ import annotations

import os
import secrets
import tempfile
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_BASE_TEMP = REPOSITORY_ROOT / ".pytest-basetemp"


def _heavy_slot_check():
    """T1 (spec §5.3): tools/heavy_slot_check.py, loaded by path (tools/ is not a package)."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("heavy_slot_check", REPOSITORY_ROOT / "tools" / "heavy_slot_check.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _is_writable(directory: Path) -> bool:
    try:
        directory.mkdir(parents=True, exist_ok=True)
        probe = directory / f".write-probe-{os.getpid()}"
        probe.touch()
        probe.unlink()
    except OSError:
        return False
    return True


def pytest_configure(config: pytest.Config) -> None:
    # ENV-1 (D-ENV1.13): first statement, before every early return; each process (xdist worker included) gets its
    # own parse-slot pools, so suites, workers and lanes never wait on each other's slots or on a running server's.
    os.environ["ASSETOPS_PARSE_SLOT_NAMESPACE"] = f"assetops-test-{os.getpid()}-{secrets.token_hex(4)}"
    # T1: a run with a database refuses to start outside the heavy-tool slot pool (xdist workers pass by ancestry).
    if os.environ.get("ASSETOPS_TEST_DATABASE_URL"): _heavy_slot_check().require("pytest with Postgres", exit_with=pytest.exit)
    # PERF-01 R5: the field acceptance tests replay at 60x real time; they belong to the slow tier.
    config.addinivalue_line("markers", "slow: deliberate real-clock tests, the PERF-01 slow tier")
    if config.option.basetemp is not None:
        return
    user = os.environ.get("USER") or os.environ.get("USERNAME") or "unknown"
    default = Path(tempfile.gettempdir()) / f"pytest-of-{user}"
    try:
        if _is_writable(default):
            return
    except OSError:
        pass
    if _is_writable(WORKSPACE_BASE_TEMP):
        config.option.basetemp = str(WORKSPACE_BASE_TEMP)
