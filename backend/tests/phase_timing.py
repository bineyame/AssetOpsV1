"""Per-test set-up / call / teardown timing to a CSV file (PERF-01 phase 0).

JUnit records one time per test. The build-and-test performance plan needs the
set-up share of every file measured, not estimated, so this plugin writes one
row per test phase: `nodeid,when,duration_s,outcome,worker`. It is the
machine-readable form of `--durations=0`.

It is off unless `ASSETOPS_TEST_PHASE_TIMES` names an output file, and it is
registered only in the process that receives every report: the xdist
controller, or the single process of a serial run. It reads reports only and
changes no test, fixture or outcome.
"""

from __future__ import annotations

import csv
import os

ENV = "ASSETOPS_TEST_PHASE_TIMES"


class PhaseTimes:
    def __init__(self, path: str) -> None:
        self._file = open(path, "w", newline="", encoding="utf-8")
        self._writer = csv.writer(self._file)
        self._writer.writerow(["nodeid", "when", "duration_s", "outcome", "worker"])

    def pytest_runtest_logreport(self, report) -> None:
        worker = getattr(getattr(report, "node", None), "gateway", None)
        worker = getattr(worker, "id", "") if worker is not None else ""
        self._writer.writerow([report.nodeid, report.when, f"{report.duration:.3f}", report.outcome, worker])
        self._file.flush()

    def pytest_sessionfinish(self) -> None:
        self._file.close()


def register(config) -> None:
    path = os.environ.get(ENV)
    if path and not config.pluginmanager.has_plugin("assetops-phase-times"):
        config.pluginmanager.register(PhaseTimes(path), "assetops-phase-times")
