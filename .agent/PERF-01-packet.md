# PERF-01 review packet: phase 0 (baseline) and phase 1 (quick wins)

Branch `task/PERF-01-baseline-quick-wins` from main 504ae5f1. Builder: the Architect (Claude), under the owner's
approval in `.agent/owner-perf-approval-2026-10-28.md`. No product code and no assertion changed.

## Commits

- d5f39708 phase 0: `tools/sample-test-memory.ps1` (memory every 5 s), `backend/tests/phase_timing.py` (per-test
  set-up/call/teardown CSV, registered from `conftest.py` only when `ASSETOPS_TEST_PHASE_TIMES` is set),
  `collected.txt` per run, `-Targets` for focused Docker runs, `tools/summarize-test-run.py` (report + baseline compare).
- 9b391cd6 phase 1:
  - R2: the Docker runner is the full-run path. `tools/run-host-tests.ps1` refuses a directory or empty target.
  - R3: `postgres-test` service in `docker-compose.test.yml`: fsync, full_page_writes and synchronous_commit off; its own
    volume `assetopsv1_assetops-test-pg`; no published port. The runner uses it by default (`-Server shared` = the old
    behaviour). `assetopsv1-postgres-1` is not touched.
  - R5: `@pytest.mark.slow` on 3 backend tests (TestTickCost, TestStaleWithoutJob, the hung-stage test) and the 2 TEL
    acceptance tests. The marker is registered in both conftests, so the venv marker hash is unchanged. `-Tier
    all|fast|slow`; the default stays `all` until D4.
  - R7: `pool: "threads"` in `frontend/vite.config.ts`.
  - R9: `tools/run-host-tests.ps1` sets PYTHONPATH to the worktree, checks the import origin of 5 packages and refuses
    a stale one. The container `.sh` makes the same check against `/workspace`.
  - R10: `-Workers 0` picks 2-4 workers from the memory free at start (450 MB per worker, 400 MB fixed, a 1.5 GB
    Windows reserve, and memory the VM already holds counted in). It refuses with exit 3 below 2 workers. The
    memory peak is recorded per run.
  - Keep-awake and the sampler start without `-ExecutionPolicy Bypass`; they inherit the caller's policy.
- 100092a4 docs: `backend/TESTING.md` (commands, the dedicated server, the slow tier, the run records) and the
  `.ai/ROLE_CONFIG.md` full-suite line.

## Results (var/test-results/OPS-03/)

| Run | Wall | Summed test s | Result | Peak sessions | Peak memory |
| --- | ---: | ---: | --- | ---: | --- |
| Baseline 20261028-183000-21e665 (shared server, all tiers, 4 workers) | 74.2 min (4451 s) | 17,204 | 4133 passed, 2 failed (the known w303 pair), 0 skipped; 4135 collected | 87 runner / 93 server | VM used 2381 MB, vmmem working set 3423 MB, runner RSS sum 1536 MB (max 372 MB), Postgres 811 MB, min Windows free 2429 MB |
| Phase 1, attempt 1 20261028-194930-211b2c | void | - | the lid closed at 20:40 (event 506, "Reason: Lid"), Modern Standby until 01:46, and the run hit its 130-min cap. Only the 2 known failures up to then | - | - |
| Phase 1, run 1 20261029-020406-17c9e5 (dedicated server, fast tier, 4 workers) | 71.7 min (4301 s) | 16,478 | 4130 passed, the same 2 known failures, 0 skipped; 4135 collected | 106 runner / 113 server | VM used 2474 MB, vmmem 3301 MB, RSS sum 1511 MB (max 385 MB), Postgres 706 MB, min Windows free 2680 MB |

The count: 4135 collected on main. The 28 Oct CC-M gate's 4138 included `test_cc_schema_postgres.py` (3 tests), which
exists only on the CC-M branch. The 4135 IDs are the same in the baseline and in run 1. Run 1 has 4132 JUnit cases:
the 3 slow tests are deselected, not skipped. The compare shows that the pass lists differ by exactly those 3.

## Proof status: incomplete, by instruction

- Done: identical collected IDs (4135); identical pass list apart from the 3 deselected slow tests; zero skips.
- Not done: proof run 2 was cancelled by the coordinator (owner's new target). The slow tier was not run separately.
  The frontend forks-versus-threads count was not run.

## Deviations

- Per-test phase timing is a plugin (CSV), not `--durations=0`. It records the same data in a machine-readable form.
- The runner's keep-awake launch no longer passes `-ExecutionPolicy Bypass` (rule in force).
- Finding: the pytest set-up share is 19%, not 85-95%. Most replay builds run inside the test body (`chain.build(...)`),
  so pytest counts them as call time. Build cost has to be measured inside the build functions.
- Finding: R3 saved about 2% of CPU (16,478 against 17,204 summed seconds, of which about 420 s is the deselected
  slow tests). The plan estimated 10-25%. Disk sync is not the bottleneck inside Docker.
- Finding: under `--dist loadfile` the largest file sets a floor. `test_w403_opportunity_read_postgres.py` alone takes
  708 s, and the last 8% of every run takes about 20 min.

## Measured attribution run (owner 2026-10-29: "i want the actual run to be timed and actual time attributed")

Instrumentation: `backend/tests/phase_attribution.py` (commit e7a8bcd5). It is off unless `ASSETOPS_TEST_ATTRIBUTION`
is set, which the runner does under `-Attribution`. It does not change any test body, fixture or assertion.
Overhead (`tools/attribution-overhead.py`): 0.88 us per wrapped call and 1.3 us per SQL statement. The full run made
133k wrapped calls and 3.27M statements, about 4.4 s of 14,520 s (0.03%).

Runs:
- 20261029-075935-ad347d: fast tier, 4 workers, pytest wall 3759 s (62.6 min). 4130 passed, the 2 known failures.
- 20261029-090322-b2ebc7: slow tier, 287 s, 3 passed.
- Frontend: threads 203 s warm (326 s cold), forks 265 s.

Report: `var/test-results/PERF-01-attribution/attribution-report.md` and `attribution.json`, also committed.

**Phase-1 proof now passes.** The fast run and the slow run together match the baseline: the same 4135 collected
IDs, identical cases, an identical pass list (the 2 known w303 failures in both) and 0 skips. This is the second full
fast run with the same pass list (after 20261029-020406).

**Frontend.** Under threads: 3451 passed and 3 failed. The 3 failures are `w1f4VerificationStructure.test.tsx`, and
they also fail under forks on this main, so they are found, not caused. Forks had 1 extra flaky failure, in
`s404SiteFindingIndex`.

| part (fast tier, 4132 tests) | s | % of measured |
| --- | ---: | ---: |
| DB create/clone/drop + migrations | 653 | 4.5 |
| Site/Foundation install + credentials | 255 | 1.8 |
| gateway subprocess start/stop | 667 | 4.6 |
| replay / ingest / seed (site build) | 10,072 | 69.4 |
| app / router / TestClient | 208 | 1.4 |
| other child processes | 51 | 0.4 |
| other fixture set-up | 181 | 1.2 |
| test's own work (remainder of call) | 2,287 | 15.7 |
| teardown | 145 | 1.0 |
| **total = measured** | **14,520** | 100 (unattributed 0.0 s) |

- Workers were busy 97% of the span. Idle inside the span was 240 s, and the tail per worker was 0-85 s. The
  earlier "20-minute tail" claim was wrong: the last 8% are heavy tests, not idle workers.
- Outside the span: 69 s of xdist start and collection, plus 83 s of collect-only before pytest.
- World time (db + install + gateway + build) is 11,648 s, 80.2% of the total.
- 624 tests do a root site build: 736 root builds. They form 107 distinct root builds and 121 distinct per-test
  set-ups; 40 set-ups cover 90% of the world time.
- Building each distinct set-up once costs 2,635 s (the largest is 149 s).
- Read-only after the build: 78 of the 624 building tests (2,022 s of world time). 546 write in their check phase,
  mostly product derivation run by the test itself (mini_opportunity_evidence, mini_depth, finding evidence,
  ingestion).
- Memory peak: VM used 2453 MB, vmmem 3147 MB, runner RSS sum 1480 MB (370 MB per worker; the largest process
  336 MB), Postgres 677 MB, min Windows free 3273 MB.

## Profiles and the 5-worker trial (owner 2026-10-29: "yes to the performance point")

### Site-build profiles (`var/test-results/PERF-01-profiles/`)

Method: py-spy 0.4.0 at 100 Hz (`--threads --subprocesses`) on one test per family, run in the Docker runner on
`postgres-test`. The tools are `tools/profile-tests-in-container.ps1` with `docker-compose.profile.yml` (SYS_PTRACE,
runner only), and `tools/profile-summary.py`. Each family has an on-CPU run and an idle-included wall run.

| family (test) | test wall | on-CPU: test thread / in-process app / gateway | where the test thread's wall goes |
| --- | ---: | --- | --- |
| EV complete (w206_ev_store) | 21.3 s | 4.5 / 3.4 / 2.3 s | gateway IPC wait 58%, YAML 15%*, DB driver 11%, gateway start 7% |
| cold backup-failed (w502_domain_intent) | 22.1 s | 2.6 / 3.4 / 1.7 s | gateway IPC wait 49%, YAML 14%*, DB driver 14%, gateway start 11% |
| mini W4 set-up + ingest + reconcile (w403_job_isolation) | 45.3 s | 16.8 / 0.4 / 0 s | DB driver 61% (6.9 s on CPU, the rest waiting on Postgres), SQLAlchemy 17%, envelope parse/validate 5% |
| portfolio (w303 scope snapshot) | about 50 s (wall view incomplete, see note) | 7.8 / 8.6 / 7.3 s | gateway IPC, DB driver, YAML*, 3 gateway starts |

\* YAML is the scenario catalogue. It is read once per test process (`tests/scenario_cache.py`), so in a full run it
is paid once per worker, not once per build. The same goes for imports. They are excluded from the per-build
figures below.

Note: in the portfolio wall run, py-spy lost most main-thread samples under 4 gateway children, so only its on-CPU
figures are used.

Per-build hotspots in a full run:
- **Ingest round trip (EV and cold).** The test thread waits on the gateway while the gateway uploads over TLS to
  the in-process central app, which ingests row by row (`ledger_service.submit` -> `postgres_evidence_ledger.work /
  decide_chunk / _persist`). About 13.7k SQL statements per EV build.
- **Gateway start.** 1.6-2.5 s per gateway.
- **TLS in the gateway uploader.** `ssl.create_default_context` on every post: 1.1-1.3 s of CPU per build, plus
  handshakes.
- **Mini ingest.** In-process and Postgres-bound: about 21 s waiting on the server, plus `mini_depth.append_selection`
  at 4.8 s.
- **No sleeps or polling.** Sleep is at most 0.1 s per build.

### 5-worker trial (`var/test-results/PERF-01-workers5/`, run 20261029-101114-000eaf)

The memory guard allowed 5 (budget 2478 MB at 450 MB per worker), so 6 was not tried.

| | 4 workers (20261029-075935) | 5 workers |
| --- | ---: | ---: |
| pytest wall | 3759 s (62.6 min) | 3435 s (57.2 min, -8.6%) |
| summed test time | 14,520 s | 16,203 s (+11.6% per test) |
| idle in span | 240 s | 611 s |
| VM CPU (8 logical) | not sampled | mean 60%, p90 68%, max 71%, never 90% |
| host CPU | not sampled | mean 76%, p90 90%, max 100% (Chrome was open) |
| runner / Postgres cores | - | 2.7 / 1.6 mean, 4.1 / 3.0 max |
| peak VM used / vmmem | 2453 / 3147 MB | 2738 / 3553 MB |
| min Windows free | 3273 MB | 2747 MB |
| result | 4130 passed + 2 known | 4130 passed + 2 known |

The CPU is an i7-1065G7: 4 physical cores, 8 threads, 15 W. VM CPU levelling off at 60-70% of 8 logical CPUs, with
every test 11.6% slower, means the physical cores are saturated. A fifth worker buys 8.6%, and a sixth would buy
little or nothing on this laptop.
