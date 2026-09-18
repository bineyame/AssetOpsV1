"""Test configuration shared by the backend suite.

Its only job is to keep pytest's temporary directories somewhere the current
process can actually write.

Why. `tmp_path` and `tmp_path_factory` default to a base under the user's temp
directory. That is fine on a developer machine and fails in a sandboxed one: a
Reviewer agent whose write access stops at the workspace gets
`PermissionError: [WinError 5] Access is denied` during fixture setup, on every
test that asks for a temp path. Three consecutive reviews of this repository
could not run the backend suite for that reason, so their verification of the
Implementer's numbers was missing.

The default is left alone whenever it works, which matters more than it looks.
An earlier version of this file always redirected the base into the
repository, and that broke the suite in a new way: the directory ends up owned
by whichever process created it first, and the other one is then denied. The
developer run would lock out the sandboxed run, the sandboxed run would lock
out the developer, and each would look like a fresh permissions bug. So the
redirect now happens only when the default is unusable, which means the
developer machine never creates the directory the sandbox needs to own.

The workspace path is derived from this file's location rather than from the
working directory, because the suite is run both from the repository root
(`pytest backend/tests`) and from `backend/`, and a relative path would mean
two different places. If even that is not writable - a leftover owned by
another identity - a process-unique sibling is used instead, because failing to
find a temp directory should never be the reason a suite cannot run.

An explicit `--basetemp` on the command line always wins.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
WORKSPACE_BASE_TEMP = REPOSITORY_ROOT / ".pytest-basetemp"


def _is_writable(directory: Path) -> bool:
    """Whether this process can actually create a file in `directory`."""
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

    # The default works almost everywhere. Leaving it alone is what keeps the
    # developer machine from creating a directory the sandbox cannot own.
    try:
        default_root = Path(tempfile.gettempdir())
    except OSError:
        default_root = None

    if default_root is not None and _is_writable(default_root):
        return

    if _is_writable(WORKSPACE_BASE_TEMP):
        config.option.basetemp = str(WORKSPACE_BASE_TEMP)
        return

    unique = REPOSITORY_ROOT / f".pytest-basetemp-{os.getpid()}"
    if _is_writable(unique):
        config.option.basetemp = str(unique)
