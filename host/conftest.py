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
import tempfile
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_BASE_TEMP = REPOSITORY_ROOT / ".pytest-basetemp"


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
