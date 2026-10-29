"""Measure the per-call cost of backend/tests/phase_attribution.py (PERF-01).

    python tools/attribution-overhead.py

Times a no-op called raw and through the attribution wrapper while a test is "running", and the statement
listener's work per SQL statement. Multiply by a run's `wrapped_calls` and `statements` (the summary line of each
attribution-<worker>.jsonl) to get that run's instrumentation overhead; tools/attribution-report.py does this.
"""

from __future__ import annotations

import json
import sys
import tempfile
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend" / "tests"))
import phase_attribution as pa  # noqa: E402

N = 200_000


def noop(*args, **kwargs):
    return None


def main() -> None:
    with tempfile.TemporaryDirectory() as directory:
        recorder = pa.Recorder(directory, "bench")
        recorder.start_test()
        recorder.phase = "call"
        recorder.thread = threading.get_ident()
        wrapped = recorder.wrap(noop, "build", None, "bench.noop")
        start = time.perf_counter()
        for _ in range(N):
            noop(1, x=2)
        raw = time.perf_counter() - start
        start = time.perf_counter()
        for _ in range(N):
            wrapped(1, x=2)
        through = time.perf_counter() - start
        start = time.perf_counter()
        for _ in range(N):
            recorder.on_statement("INSERT INTO t VALUES (1)")
        listener = time.perf_counter() - start
        recorder.phase = None
        recorder.close()
    print(json.dumps({"wrapper_us_per_call": round((through - raw) / N * 1e6, 3),
                      "listener_us_per_statement": round(listener / N * 1e6, 3)}))


if __name__ == "__main__":
    main()
