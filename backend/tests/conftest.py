"""Test configuration shared by the backend suite.

Its only job is to keep pytest's temporary directories inside the repository.

Why. `tmp_path` and `tmp_path_factory` default to a base under the user's
temp directory, which is fine on a developer machine and fails in a sandboxed
one: a Reviewer agent running with write access limited to the workspace gets
`PermissionError: [WinError 5] Access is denied` during fixture setup, on every
test that asks for a temp path. Three consecutive reviews of this repository
could not run the backend suite for that reason, so their verification of the
Implementer's numbers was missing.

The base is derived from this file's own location rather than from the working
directory, because the suite is run both from the repository root
(`pytest backend/tests`) and from `backend/`, and a relative `--basetemp` would
mean two different places.

An explicit `--basetemp` on the command line still wins, so this changes what
happens by default and takes nothing away.
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
BASE_TEMP = REPOSITORY_ROOT / ".pytest-basetemp"


def pytest_configure(config: pytest.Config) -> None:
    if config.option.basetemp is not None:
        return

    BASE_TEMP.mkdir(parents=True, exist_ok=True)
    config.option.basetemp = str(BASE_TEMP)
