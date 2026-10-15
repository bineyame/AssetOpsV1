"""Test configuration shared by the backend suite.

Its only job is to keep pytest's temporary directories somewhere the current
process can actually write.

Why. `tmp_path` and `tmp_path_factory` default to a base under the user's temp
directory. That is fine on a developer machine and fails in a sandboxed one: a
Reviewer agent whose write access stops at the workspace gets
`PermissionError: [WinError 5] Access is denied` during fixture setup, on every
test that asks for a temp path. Three consecutive reviews of this repository
could not run the backend suite for that reason, so their verification of the
Implementer's numbers was missing. This file fixes the backend half only; the
frontend suite cannot run in that sandbox at all, for an unrelated reason
recorded in the Reviewer brief.

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

Its second job (OPS-01) is routing the real-Postgres tests to a run-owned
database before any test module is imported; see `pg_harness.py` and
`backend/TESTING.md`. `pytest_sessionfinish` drops what the run created.

Under pytest-xdist the controller runs no tests: it makes the run id, hands it
to each worker through `workerinput`, and drops the run's databases once every
worker is done. Each worker routes itself to its own database before it
collects, and takes its temp directory from the controller (xdist passes
`<controller basetemp>/<workerid>`), so the basetemp choice is controller-only.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

import pg_harness

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


def _default_basetemp() -> Path:
    """The directory pytest will actually use, not the temp root above it.

    pytest does not write into the temp root; it writes into a `pytest-of-<user>`
    directory inside it. That distinction is the whole problem: the temp root is
    writable by everyone, while `pytest-of-<user>` belongs to whichever process
    created it first and denies the other. Probing the root reports success and
    then pytest fails one level down, which is exactly how an earlier version of
    this file let the sandboxed suite regress from 304 passing to 89 errors.
    """
    user = os.environ.get("USER") or os.environ.get("USERNAME") or "unknown"
    return Path(tempfile.gettempdir()) / f"pytest-of-{user}"


RUN_KEY = "assetops_test_run"
PROVISIONED_KEY = "assetops_test_provisioned"

# Modules whose wall time dominates the suite and varies most (OPS-01 phase 1:
# 53-694 s and 91-950 s for one test each). Under `--dist loadfile
# --no-loadscope-reorder` the scheduler hands out modules in collection order,
# so a worker moves them to the front: they start first instead of last. Whole
# modules move, nothing is deselected, and serial order is unchanged.
START_FIRST = (
    "/test_s4_finding_evidence_history_postgres.py",
    "/test_s4_finding_read_postgres.py",
)


def _workerinput(config: pytest.Config) -> dict | None:
    return getattr(config, "workerinput", None)


def _is_xdist_controller(config: pytest.Config) -> bool:
    return _workerinput(config) is None and bool(getattr(config.option, "numprocesses", None))


def refuse_template_opt_out_under_xdist(config: pytest.Config) -> None:
    """`ASSETOPS_TEST_TEMPLATE=0` turns routing off, so every xdist worker would reset the one shared database
    under its neighbours. Refuse it before any worker exists (OPS-01 L1); serially the opt-out stays valid."""
    if os.environ.get(pg_harness.TEMPLATE_SWITCH, "1") != "0":
        return
    if _workerinput(config) is not None or _is_xdist_controller(config):
        raise pytest.UsageError(
            f"{pg_harness.TEMPLATE_SWITCH}=0 cannot be combined with pytest-xdist (-n): without per-worker database "
            "routing every worker would reset the same test database. Unset it, or run serially (-n 0).")


def pytest_configure(config: pytest.Config) -> None:
    refuse_template_opt_out_under_xdist(config)
    workerinput = _workerinput(config)
    if workerinput is not None:
        # Before collection: module-level `URL` constants read the routed name.
        pg_harness.route(tag=workerinput["workerid"], run=workerinput.get(RUN_KEY))
        return  # basetemp comes from the controller
    if _is_xdist_controller(config):
        config.stash[_RUN] = pg_harness.new_run_id()
    else:
        pg_harness.route()
    _choose_basetemp(config)


_RUN = pytest.StashKey[str]()
_DOWN = pytest.StashKey[list]()


@pytest.hookimpl(optionalhook=True)
def pytest_configure_node(node) -> None:
    node.workerinput[RUN_KEY] = node.config.stash[_RUN]


@pytest.hookimpl(optionalhook=True)
def pytest_testnodedown(node, error) -> None:
    output = getattr(node, "workeroutput", None) or {}
    node.config.stash.setdefault(_DOWN, []).append(output.get(PROVISIONED_KEY, True))


def pytest_collection_modifyitems(config: pytest.Config, items: list) -> None:
    if _workerinput(config) is None:
        return
    def first(item) -> int:
        path = item.nodeid.split("::", 1)[0].replace("\\", "/")
        return 0 if path.endswith(START_FIRST) else 1
    items.sort(key=first)  # stable: order within and between the other modules is unchanged


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    config = session.config
    workerinput = _workerinput(config)
    if workerinput is not None:
        config.workeroutput[PROVISIONED_KEY] = pg_harness.provisioned()
        pg_harness.cleanup()
        return
    if _RUN in config.stash:
        # A worker that died reported nothing; clean up for it too.
        if any(config.stash.get(_DOWN, [True])):
            pg_harness.cleanup_run(config.stash[_RUN])
        return
    pg_harness.cleanup()


def _choose_basetemp(config: pytest.Config) -> None:
    if config.option.basetemp is not None:
        return

    # The default works almost everywhere. Leaving it alone is what keeps the
    # developer machine from creating a directory the sandbox cannot own.
    try:
        if _is_writable(_default_basetemp()):
            return
    except OSError:
        pass

    if _is_writable(WORKSPACE_BASE_TEMP):
        config.option.basetemp = str(WORKSPACE_BASE_TEMP)
        return

    unique = REPOSITORY_ROOT / f".pytest-basetemp-{os.getpid()}"
    if _is_writable(unique):
        config.option.basetemp = str(unique)
