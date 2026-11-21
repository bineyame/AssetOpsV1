"""DS4 (spec `specs/DS4-template-ladder/spec.md` §4, B5; D-DS4.11, D-DS4.20): the telemetry pipeline on the bench
slice. Opt-in and slow; `world bench` runs it under a base database of its own:

    ASSETOPS_DS4_BENCH=1 tools/heavy-slot.sh --db -- pwsh -NoProfile -File tools/run-host-tests.ps1 -- \\
        backend/tests/test_ds4_bench_pipeline_postgres.py -s

DS3's seed relabelled `minigrid-roles-4` (so mini-domain jobs exist), cloned once; fourteen Kobo days (6 to 19
October) bulk-loaded; the Site enrolled; the mini-depth step (the worker's `run-pending --limit 500` until a pass
returns fewer than 500, at most 20 passes: D-DS4.29, as every product drain runs it first); then ticks (`tools/demo_combined.py`'s `TICK` plus `--no-prebuild`) until
`demo_combined_drain.step` says `done` or `fail`, or 200 ticks. Prints one `DS4_PIPELINE {json}` line. It asserts
nothing about time; a `fail` verdict is reported, not hidden. Both clones are dropped in `finally`.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import timedelta
from pathlib import Path

import pytest

import pg_harness

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
ROOT = Path(__file__).resolve().parents[2]
DAYS = 14
TICK_CAP = 200
PERF = "assetops.perf "
MINI_LIMIT = 500
MINI_PASS_CAP = 20

pytestmark = [
    pytest.mark.slow,
    pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)"),
    pytest.mark.skipif(os.environ.get("ASSETOPS_DS4_BENCH") != "1", reason="opt-in: set ASSETOPS_DS4_BENCH=1"),
]

if URL:
    if str(ROOT / "tools") not in sys.path:
        sys.path.insert(0, str(ROOT / "tools"))
    import demo_combined_drain as drain
    from demo_combined import PG_TARGET_ENV, TICK
    from test_ds3_bulk_load_postgres import DAY6, kobo_days, seed_database

    from assetops_backend.evidence.bulk_load import BulkEvidenceLoad
    from assetops_backend.evidence.composition import build_evidence_ledger


def child_env(url: str) -> dict[str, str]:
    """The tick and enrol children: this process's environment on `url`, without libpq target variables, a tenant
    slug, a key directory or the operator-data switch."""
    env = {k: v for k, v in os.environ.items() if k not in PG_TARGET_ENV}
    for k in ("ASSETOPS_TENANT_SLUG", "ASSETOPS_PSEUDONYM_KEY_DIR", "ASSETOPS_REAL_OPERATOR_DATA"):
        env.pop(k, None)
    env["DATABASE_URL"] = url
    return env


def perf_stages(stderr: str) -> dict[str, int]:
    """Per stage, the `elapsed_ms` summed over the Sites of the tick's `assetops.perf` line (none: empty)."""
    out: dict[str, int] = {}
    for line in (stderr or "").splitlines():
        if not line.startswith(PERF):
            continue
        doc = json.loads(line[len(PERF):])
        for site in doc.get("sites") or ():
            for stage, v in (site.get("stages") or {}).items():
                if isinstance(v, dict) and v.get("elapsed_ms") is not None:
                    out[stage] = out.get(stage, 0) + int(v["elapsed_ms"])
    return out


def mini_depth_step(env: dict[str, str]) -> dict:
    """The mini-depth jobs drained with the worker's own CLI, as `demo_combined.drain_mini` does. FAILED outcomes
    are counted, not raised; a pass with no parsable outcome list is a broken worker, not a measurement."""
    passes, jobs, by_status, stopped = 0, 0, {}, "PASS_CAP"
    while passes < MINI_PASS_CAP:
        done = subprocess.run([sys.executable, "-m", "assetops_backend.mini_depth.worker", "run-pending", "--limit",
                               str(MINI_LIMIT)], cwd=str(ROOT), env=env, capture_output=True, text=True)
        outcomes = None
        for line in reversed([x for x in done.stdout.splitlines() if x.startswith("[")]):
            try:
                outcomes = json.loads(line)
            except ValueError:
                continue
            break
        assert outcomes is not None, done.stderr[-500:]
        passes += 1
        jobs += len(outcomes)
        for o in outcomes:
            status = str(o.get("status"))
            by_status[status] = by_status.get(status, 0) + 1
        if len(outcomes) < MINI_LIMIT:
            stopped = "DRAINED"
            break
    return {"passes": passes, "jobs": jobs, "by_status": dict(sorted(by_status.items())), "stopped": stopped}


def cut(counts: dict) -> dict:
    return {code: {f: site[f] for f in drain.FIELDS} for code, site in counts.items()}


def test_pipeline_on_fourteen_kobo_days() -> None:
    seed, kit, _ = seed_database("ds4pseed", relabel=True)
    urls = [seed]
    try:
        pipe = pg_harness.clone_database("ds4ppipe", seed)
        urls.append(pipe)
        batches = kobo_days(kit, [DAY6 + timedelta(days=d) for d in range(DAYS)])
        ledger = build_evidence_ledger(pipe)
        start = time.perf_counter()
        loaded = BulkEvidenceLoad(ledger).load(batches)
        load_seconds = time.perf_counter() - start
        pg_harness.dispose(ledger)
        env = child_env(pipe)
        enrol = subprocess.run([sys.executable, "-m", "assetops_backend.scheduling.run", "enrol",
                                "--tenant-id", str(kit.principal.tenant_id), "--site-id", str(kit.principal.site_id),
                                "--by", "service:ds4-bench"], cwd=str(ROOT), env=env, capture_output=True, text=True)
        assert enrol.returncode == 0, enrol.stderr[-500:]
        t0 = time.perf_counter()
        mini = mini_depth_step(env)
        mini_seconds = time.perf_counter() - t0
        history: list[dict] = []
        first = drain.counts(pipe)
        n = drain.n_for(first)
        ticks, wall, stage_ms = 0, 0.0, {}
        verdict, reason = "fail", "tick cap"
        while ticks < TICK_CAP:
            t0 = time.perf_counter()
            done = subprocess.run([sys.executable, *TICK, "--no-prebuild"], cwd=str(ROOT), env=env,
                                  capture_output=True, text=True)
            wall += time.perf_counter() - t0
            ticks += 1
            for stage, ms in perf_stages(done.stderr).items():
                stage_ms[stage] = stage_ms.get(stage, 0) + ms
            history.append(drain.counts(pipe))
            state, why = drain.step(history, ticks, n)
            if state in ("done", "fail"):
                verdict, reason = state, why
                break
        result = {"site_days": DAYS, "batches": loaded.batches, "envelopes": loaded.envelopes,
                  "load_seconds": round(load_seconds, 3), "mini_depth_seconds": round(mini_seconds, 3),
                  "mini_depth": mini, "n": n, "start_counts": cut(first), "end_counts": cut(history[-1]),
                  "ticks": ticks, "tick_wall_seconds": round(wall, 3),
                  "stage_ms": dict(sorted(stage_ms.items())), "drain": {"verdict": verdict, "reason": reason}}
        print("\nDS4_PIPELINE " + json.dumps(result, sort_keys=True, separators=(",", ":")))
    finally:
        for url in reversed(urls):
            pg_harness.drop_database(url)
