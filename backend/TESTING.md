# Backend testing guide

How to run the backend suite, when to run all of it, and how to prove a full
run was real. Database setup itself is in [README-db.md](README-db.md).

## When to run what

- **While building a phase:** run the focused files for the area you changed,
  plus adjacent integration tests. When an interface crosses into the host or
  gateway, also run those suites.
- **At the end of an ordinary slice (PERF-02, owner-approved C):** the backend
  tests the change can affect, in Docker, plus the related frontend tests and a
  type check. `python tools/select-tests.py --base main` prints both commands.
  It selects the whole suite by itself when the change touches migrations, the
  harness, conftest, shipped configuration or fixture data, the composition
  root, the runner or a dependency manifest. Cite its output and the run's JUnit
  zero-skip check in the review packet.
- **At every merge to main:** the full backend fast tier in Docker (build once,
  copy per test, below), the full frontend suite and check-all. Schema or shared
  plumbing merges add the slow tier.
- **Where (PERF-01, R2):** every full or merge run goes through the Docker
  runner, `tools\run-backend-suite-in-container.ps1` (below). The Windows host
  runs focused files only, through `tools\run-host-tests.ps1`, which refuses a
  suite sweep. A full run is the whole suite (`-Tier all`, the default), or the
  fast and slow tiers run back to back.
- **Reviewers** run the focused files relevant to their findings and cite the
  implementer's same-revision full evidence. A reviewer reruns the full suite
  only for a finding that needs it.
- **One full suite at a time on this machine.** Concurrent full runs were not
  attempted and are not proven safe; a full run is disk-bound, so a second one
  (or another Postgres-heavy agent) slows both and makes timing meaningless.
- OPS-01's baseline and comparison runs are the one documented exception to
  "one full suite per slice".
- `tools/check-all.ps1` is a separate required guard command; it does not run
  pytest, and pytest does not replace it.

## The test database

`ASSETOPS_TEST_DATABASE_URL` names a base database whose name ends in `_test`
(Compose creates `assetops_test`; agents may use a private one such as
`assetops_<task>_test`). Without it every Postgres module is reported as
**skipped**, and such a run is not valid full-suite proof.

The base database is used only as an administrative connection. At
configuration time `tests/conftest.py` calls `pg_harness.route()`, which
rewrites `ASSETOPS_TEST_DATABASE_URL` to a run-owned name before any test module
is imported:

```
<base without _test>_pt<run>_<tag>_test     tag = main (serial), gw0, gw1... (xdist workers), tpl (template)
```

On first use the harness migrates the template to head once, then every
Postgres module's `engine` fixture drops the run's worker database `WITH
(FORCE)` and clones it from the template (`CREATE DATABASE ... TEMPLATE`), and
asserts the clone is at the Alembic head. Each module therefore still starts on
a fresh, fully migrated schema; migration up/downgrade tests still run in place
on that module's clone. `store` fixtures yield and dispose their engine.

Between tests the S1 `store` fixture empties the same tables
`TRUNCATE foundation_revision, source, gateway, asset, site_import, site, tenant
CASCADE` would, but with `DELETE` under `session_replication_role = replica`
(`pg_harness.empty_tables`). TRUNCATE rebuilds every index and on PostgreSQL 16
each rebuild forces a data-file sync, which Docker Desktop makes slow and
erratic (measured 1.4 s quiet, 22-25 s under disk pressure, per test; DELETE
0.14 s). `test_pg_harness.py` proves the DELETE set equals the tables TRUNCATE
CASCADE reports. `ASSETOPS_TEST_CLEANUP=truncate` restores TRUNCATE.

- In parallel (`-n 2`) the xdist controller runs no tests. It makes the run
  id and passes it to each worker; each worker routes itself to
  `..._pt<run>_gw<N>_test` before it imports a test module. The first worker
  that needs the template builds it under an advisory lock and the others reuse
  it. Workers drop only their own database; the controller drops the template
  and anything else the run left (a crashed worker's database) at the end.
  Under `--dist loadfile` every module stays on one worker, so module-scoped
  fixtures behave as serially. With `--no-loadscope-reorder` modules are handed
  out in collection order, and workers move the two long S4 Finding modules
  (`conftest.START_FIRST`) to the front so they start first; serial order is
  unchanged.
- Parametrize IDs must not be random: xdist refuses to run when workers collect
  different node IDs (`Different tests were collected between gw0 and gw1`).
- Nothing is provisioned for `--collect-only`, for a selection without Postgres
  modules, or with the URL unset.
- At the end of the session the run drops its own databases. A killed run's
  databases are swept by the next run with the same base: it drops
  `<base>_pt*` databases only when their run holds no live session (each run
  keeps one lease session whose `application_name` is
  `assetops-test-run:<run>`).
- `ASSETOPS_TEST_TEMPLATE=0` turns routing off and restores the old behaviour
  (drop `public` and migrate in place per module). Use it only if cloning is
  unavailable; it is serial-only and slower.
- Measurement knob, off by default: `ASSETOPS_TEST_CLONE_STRATEGY`
  (`WAL_LOG` or `FILE_COPY`). Since OPS-04 every run-owned `*_test` database gets
  `ALTER DATABASE ... SET synchronous_commit = off`. Server-wide settings are never
  changed by the tests.
- PERF-01 (R3): the Docker runner uses a separate, test-only server by default,
  `postgres-test` in `docker-compose.test.yml` (container
  `assetopsv1-postgres-test-1`, volume `assetopsv1_assetops-test-pg`, no
  published port). It is started with `fsync=off`, `full_page_writes=off` and
  `synchronous_commit=off`, because its data is rebuilt by every run and is
  worth nothing after a crash. The development server `assetopsv1-postgres-1`
  and its databases are not touched by it; `-Server shared` runs against the
  development server's `assetops_test` as before. The tests still change no
  server-wide setting; the server is started that way.

## Commands (PowerShell, from the repository root)

Run the tools scripts directly from a PowerShell prompt that may run local
scripts. Never add an execution-policy override.

Focused files on the host (R9). The wrapper puts this worktree's packages first
on `PYTHONPATH`, checks that `assetops_backend`, `assetops_contracts`,
`assetops_simulator`, `assetops_gateway` and `assetops_field` import from this
worktree, and refuses otherwise (the shared venv's editable installs point at
another checkout). It defaults `ASSETOPS_TEST_DATABASE_URL` to the development
server's `assetops_test` and refuses a directory or empty target (R2):

```powershell
$env:ASSETOPS_TEST_PYTHON = "C:\Users\assef\Bineyame\AssetOpsV1-plan2\.venv\Scripts\python.exe"  # or -Interpreter

# S1 Foundation and bindings
tools\run-host-tests.ps1 -- backend/tests/test_s1_foundation_postgres.py backend/tests/test_s1_bindings_postgres.py backend/tests/test_s1_cutover.py backend/tests/test_s1_bindings.py

# S2 ingestion and evidence
tools\run-host-tests.ps1 -- backend/tests/test_s2_evidence_ledger_postgres.py backend/tests/test_s2_gateway_access_postgres.py backend/tests/test_s2_site_evidence_postgres.py backend/tests/test_s2_registered_basis_postgres.py

# S3 dispatch
tools\run-host-tests.ps1 -- backend/tests/test_s3_dispatch_assessment_postgres.py backend/tests/test_s3_dispatch_read_postgres.py backend/tests/test_s3_demo_configuration.py

# S3-02a capability and claim-limit read
tools\run-host-tests.ps1 -- backend/tests/test_s3_capability_read_postgres.py backend/tests/test_s3_claim_limit_postgres.py

# S4 Finding and money
tools\run-host-tests.ps1 -- backend/tests/test_s4_finding_store_postgres.py backend/tests/test_s4_finding_read_postgres.py backend/tests/test_s4_finding_index_postgres.py backend/tests/test_s4_finding_evidence_history_postgres.py backend/tests/test_s4_assumptions_postgres.py backend/tests/test_s4_consequence_store_postgres.py backend/tests/test_s4_consequence_recompute_postgres.py backend/tests/test_s4_evidence_consequence_work_postgres.py backend/tests/test_s4_evidence_drain_postgres.py backend/tests/test_s4_power_demo_case_postgres.py backend/tests/test_s4_schedule_tick_postgres.py backend/tests/test_s4_schedule_health_postgres.py
```

Pytest flags go after `--` (optional; it is dropped). From Git Bash use `powershell -NoProfile -File tools/run-host-tests.ps1 -- <file> -q` (the script has no common parameters, so `--`, `-q` and `-v` reach pytest); `ASSETOPS_HOST_DRY_RUN=1` prints the resolved targets and exits 3 without running anything; the interpreter is a named-only `-Interpreter` (default: the plan2 venv), so test files are never taken as the interpreter. Flag values such as `-k foo` are not test targets, and an absolute directory path is refused like a relative one. Focused files can also run in Docker, which avoids
the Windows port forward: `tools\run-backend-suite-in-container.ps1 -Targets
'backend/tests/test_x_postgres.py backend/tests/test_y.py'`.

Complete suite: only in Docker (next section). The host fallback
(`tools\run-host-tests.ps1 -AllowHostFull -- backend/tests -n 2 --dist loadfile
--no-loadscope-reorder -q --junitxml=.pytest-junit.xml`) is for a Docker outage
only, and its packet says why.

### Before a long full run

Start the keep-awake helper in a separate window (or as a background job). It
asks Windows not to idle-sleep while any pytest process runs, changes no power
settings, and exits after 20 idle minutes. It also holds the display on: on a Modern
Standby laptop the display idle timeout otherwise enters standby (System event
506, "Reason: Idle Timeout") even with the system-required flag, and a run that
crosses standby loses wall time it never computed (main-tick-cost: the four-Site
tick-cost test exhausted its 240 s tick budget and visited 3 Sites; the full
suite took 47 minutes). Check with
`Get-WinEvent -FilterHashtable @{LogName='System';Id=506,507}` before reading a
slow or budget-bound failure as a code regression. A machine that sleeps mid-run turns
a 40-minute suite into hours (seen in OPS-01: one run reached 34% in 4 h).

```powershell
tools\keep-awake-during-tests.ps1   # the Docker runner starts this itself
```

Cap every full run at twice its expected wall time (see Timing below). A run
past the cap is reported as a hang, with the node ID it is stuck on (from
`pg_stat_activity` and the pytest log), not waited on.

### Zero-skip proof (from JUnit, not the summary line)

```powershell
[xml]$j = Get-Content .pytest-junit.xml
$cases = $j.SelectNodes("//testcase")
$skipped = $j.SelectNodes("//testcase[skipped]")
$failed = $j.SelectNodes("//testcase[failure or error]")
"cases=$($cases.Count) skipped=$($skipped.Count) failed=$($failed.Count)"
$skipped | ForEach-Object { "$($_.classname)::$($_.name) - $($_.skipped.message)" }
```

A full run is valid proof only when `skipped` is 0 and `failed` is 0. A skip
whose message names `ASSETOPS_TEST_DATABASE_URL` means the database was unset.

## Full suite inside the Compose network (OPS-03)

```powershell
tools\run-backend-suite-in-container.ps1                 # whole suite, dedicated test server, workers from free memory
tools\run-backend-suite-in-container.ps1 -Tier fast      # everything but the slow tier
tools\run-backend-suite-in-container.ps1 -Tier slow      # the slow tier only
tools\run-backend-suite-in-container.ps1 -Workers 2 -CapMinutes 150 -Server shared
```

PERF-01 options and records:

- `-Server dedicated` (default) uses `postgres-test`; `shared` uses the
  development server as OPS-03 did.
- `-Tier all` (default), `fast` (`-m "not slow"`) or `slow` (`-m slow`).
- `-Workers 0` (default) picks 2-4 workers from the memory free at start (R10):
  the budget is the smaller of the VM's available memory and (Windows free
  memory above a 1.5 GB reserve, plus memory the VM already holds unused),
  less 400 MB fixed, at 450 MB per worker (the PERF-01 baseline peak was about
  384 MB of resident memory per worker). Below two workers it refuses to start
  (exit 3) and says to close programs or pass `-Workers`.
- `-Targets` runs named files or node IDs instead of `backend/tests`.
- Every run also writes `collected.txt` (the whole suite's `--collect-only`
  node IDs, whatever the tier), `phase-times.csv` (each test's set-up, call and
  teardown time, `tests/phase_timing.py`), `memory.csv` and `memory-peak.txt`
  (`tools/sample-test-memory.ps1`, every 5 s: Windows free memory, the VM
  process's working set, memory used inside the VM, runner and database
  container memory, runner processes and their resident sizes) and
  `run-options.txt` (memory at start and the options chosen). The container
  checks before pytest that every AssetOps package imports from `/workspace`.
- `python tools/summarize-test-run.py <run-dir> [--compare <baseline-dir>
  --extra <slow-tier-dir> --known-failure <id>]` writes `report.md`,
  `summary.json` and `passed.txt`, and checks a run against a baseline:
  identical collected IDs, identical JUnit pass list, zero skips.

The wrapper runs the same pytest command as the host (`-n <workers> --dist loadfile
--no-loadscope-reorder -q --durations=30`; workers from free memory, 4 by default) in the one-shot `backend-test-runner`
service (`docker-compose.test.yml`, image `python:3.12.7-slim-bookworm`,
profile `test`, no published ports) on the `assetopsv1` project network, so the
suite reaches Postgres as `postgres:5432` instead of through Docker Desktop's
Windows port forward. The worktree is bind-mounted at `/workspace`; the Linux
venv and pip cache live in the named volumes `assetops-test-venv` and
`assetops-test-pip-cache` and are reinstalled only when the Python version or a
`pyproject.toml` (backend, contracts, simulator, gateway) changes. The wrapper
checks the Postgres container's Compose project label, starts it only if absent
(`up -d --no-recreate --wait`; the runner itself starts with `--no-deps`),
never recreates, stops or removes it, holds keep-awake for its own PID, and
never prints the database URL or password.

Each attempt writes to its own `var/test-results/OPS-03/<run-id>/`:
`junit.xml` (use it in the zero-skip proof above in place of
`.pytest-junit.xml`), `console.log`, `wall-time.txt`, `connections.csv` and
`connections-peak.txt` (`pg_stat_activity` sampled every 5 s: server-wide,
client backends, and the runner container's own sessions). The pytest wall time
is capped at `-CapMinutes` (default: derived, twice the measured wall for the tier at 4 workers scaled by 4 / workers, 20-minute floor and 60-minute ceiling for named targets; 149 min for a full run at 4 workers; see Timing); a run
past the cap writes `timeout.txt` (non-idle `pg_stat_activity`, runner
processes, console tail), is killed, and exits 124. The exit code is pytest's
otherwise. `tools/check-all.ps1` still runs separately on Windows.

The host commands above remain the supported fallback. Node IDs are identical
in both: the owner-only credential test
(`test_s2_gateway_access_postgres.py::TestProvisioning::test_a_protected_dacl_that_grants_another_account_is_refused`)
checks a Windows DACL on Windows and, on Linux, that a `0644` file is refused
and a `0600` file accepted by `verify_owner_only`.

## Build once, copy per test (PERF-02)

The replay-chain fixtures used to rebuild the same few site set-ups hundreds of
times per run. `tests/setup_cache.py` wraps the builder steps after collection:
`Chain.open`, `start_release_upload`, `release_and_upload` and `advance_late` of
the cold and EV chains (`test_w202_cold_replay_postgres.py`,
`test_w205b_ev_replay_postgres.py`), and the W4 mini-grid `_setup`, `_ingest`
and `_reconcile` (`test_w402_reads_postgres.py`). The first time a step runs
with given inputs it builds live and is saved. Every later test with the same
inputs gets its own copy instead:

- **Database.** The worker database is replaced by
  `CREATE DATABASE ... TEMPLATE assetops_sc_<code>_<key>_test`.
- **Files.** The chain's tmp folder is copied, with its old absolute path
  rewritten.
- **Objects.** The chain's fields are unpickled, with new engines on the same
  URL.
- **Gateway.** The gateway child and the in-process central app start lazily
  from the copied state on first use, and settle their start-up upload first.
- **UUIDs.** The `hold_uuids` counter is set where the build left it.

The key covers:

- a fingerprint of the product source, migrations, shipped config, fixtures and
  the builder and helper test files;
- the step and its plain arguments;
- the UUID counter;
- for a step that does not start from a fresh database, a digest of the
  database it starts from.

The first W4 step of a test that wrote nothing itself, in a module whose
fixtures seed nothing, starts from a clean clone instead of other tests'
leftovers. The cache refuses a step, which then builds live as before, when:

- a monkeypatch other than the UUID counter is active;
- a repository function or class has been rebound by direct assignment;
- another session holds the worker database;
- an argument or the state does not pickle.

Not cached: `CaseRunner` shares the caller's live store, and a trial failed its
fences.

- `-Cache on` (default in Docker): saved set-ups live in the named volume
  `assetopsv1_assetops-test-setup-cache` and as `assetops_sc_*_test` databases
  on `postgres-test`. They are kept between runs (T2), and a run whose code
  fingerprint matches reuses them. `tools/sweep-setup-cache.py` (run by the
  runner) drops all but the newest three fingerprints.
- `-Cache off`: every step builds live, the PERF-01 path.
- `-Cache verify`: every step builds live. Each repeat is compared with the
  saved build: per-table row counts and content without time columns, and the
  UUID counter. Its separate cache (volume `..._setup-cache-verify`) must be
  built in verify mode.
- Each run writes `setup-cache/setup-cache-<worker>.jsonl` (op, hit, miss or
  live, reason, seconds). `python tools/setup-cache-report.py <run dir>`
  summarises it: hits, the measured copy cost, live reasons and the verify
  comparison.
- The collected node IDs now come from the run itself (`collected.txt`, after
  any tier filter). The separate collect-only pass is gone (T3).

## Slow tier (PERF-01, R5)

Tests marked `@pytest.mark.slow` wait on the real clock as their subject. They
are the slowest and the most load-sensitive tests, and a fast-tier run leaves
them out (`-m "not slow"`, a deselection, never a skip):

- `test_s4_schedule_health_postgres.py::TestTickCost::test_measure_a_real_child_tick_over_one_and_four_sites` (about 150 s)
- `test_s4_schedule_health_postgres.py::TestStaleWithoutJob::test_a_decision_after_the_db_cutoff_widening_a_pending_job_raises_s3_stale_no_job_until_requeued` (about 130 s; the 120 s stale wait)
- `test_s4_schedule_tick_postgres.py::TestKillableStagesAndServerTimeouts::test_a_hung_stage_is_killed_its_job_lease_is_exposed_and_a_db_stall_is_a_typed_timeout` (about 140 s)
- `host/tests/test_field_modbus_tcp_acceptance_postgres.py`, both TEL acceptance tests (60x real time, 9-12 min each; not part of the backend suite)

Until the revised policy takes effect (D4), a full backend run is `-Tier all`
or a `fast` run plus a `slow` run whose JUnit results together match the whole
suite.

## Timing

OPS-04: 4 workers, synchronous_commit off on test DBs, Postgres max_connections 200; re-measure.

Measured on this Windows host (Docker Desktop Postgres 16), serial, full
suite. Run-to-run variance is large (disk sync inside Docker Desktop), so
compare only back-to-back runs in a quiet window.

| Revision | Runs (wall) | Notes |
| --- | --- | --- |
| Before OPS-01 (in-place migrate per module, TRUNCATE per test) | 80.3 min, 41.4 min; peak 91 sessions | 2 timing-sensitive tick failures in the 80-min run; a third attempt reached 34% in 4 h while the machine slept |
| Serial template clone + DELETE cleanup (OPS-01 phase 1) | 30.8 min (back-to-back with the 41.4-min baseline); peak 22 sessions | template clone without DELETE cleanup: 41.4 min, one 23-min disk stall in a tick test |
| `-n 2 --dist loadfile` (OPS-01 phase 2, normal command) | 7.7 min, 8.4 min; peak 35 and 32 sessions | 2128 passed, 0 skipped, 0 failed both times; node IDs identical to serial collection |
| `-n 3 --dist loadfile` (OPS-01 phase 2, one run) | 6.5 min; peak 41 sessions | 2128 passed; not repeated, so not the default |
| W2-expanded suite, `-n 2 --dist loadfile --no-loadscope-reorder`, before the post-W2 follow-up (main `6c53b3c5`) | did not finish: 83% at the 30-min cap, then still in the W2 EV modules at a 60-min cap; peak 60 and 65 sessions | 3268 tests collected; four refusal tests each waited psycopg's 130 s default connect timeout on Windows, and every replay chain re-parsed all shipped scenario YAML |
| W2-expanded suite, same command, after the OPS-01 post-W2 follow-up | 57.7 min, 56.4 min; peak 62 and 67 sessions (68 and 73 server-wide) | 3268 passed, 0 skipped, 0 failed both times; node IDs identical to the before collection |
| Same suite and command in the Compose runner (OPS-03 wrapper, `python:3.12.7-slim-bookworm`) | 46.5 min, 49.7 min (pytest wall, two consecutive runs); peak 58 and 56 runner sessions (73 and 67 server-wide, other lanes included) | 3268 passed, 0 skipped, 0 failed both times; node IDs identical to the host collection; first run also installed the venv (about 15 min of slow downloads, cached afterwards) |

Expected container full run (`tools\run-backend-suite-in-container.ps1`): see
the PERF-01 timing rows below (74.2 min all tiers, 62.6 min fast tier at 4 workers); the default cap is derived from them. The remaining time is the
same product-path work listed below; removing the port forward saves about
8-10 min against the host run.

PERF-01 measurements (4135 tests, container runner, 4 workers unless stated):

| Run | Wall | Notes |
| --- | --- | --- |
| All tiers, shared server (baseline 20261028-183000-21e665) | 74.2 min | 4133 passed, the 2 known w303 failures, 0 skipped |
| Fast tier, test-only server (20261029-075935-ad347d) | 62.6 min | 4130 passed, the same 2 failures; slow tier run separately: 287 s, 3 passed |
| Fast tier, test-only server, 5 workers (20261029-101114-000eaf) | 57.2 min | -MaxWorkers 5 trial; the memory guard still chooses the count |

Default cap = 2 x measured wall x (4 / workers): 149 / 126 / 20 min for all / fast / slow tiers
at 4 workers, 198 / 167 min (all / fast) at 3 workers and 297 / 251 min at 2 workers. A run past the cap is a hang,
not a wait.

Expected `-n 2` full run (W2-expanded suite, 3268 tests): about 50-60 min; cap at
120 min. The remaining time is product-path work, chiefly the cold/EV replay
chains (about 30 s each, mostly evidence-ingest round trips at about 1.2 ms each
through Docker Desktop's port forward, against 0.17 ms inside the container) and
the deliberate 120 s wall-clock wait in the S4 schedule-health stale-no-job test.
Expected serial full run: not re-measured after W2; budget about twice the
`-n 2` time and cap at twice that.

A test that must see an unreachable database names `127.0.0.1:1` with
`?connect_timeout=2`: without it psycopg on Windows waits its 130 s default for
the refused connection. Replay-chain fixtures share one per-process scenario
catalogue (`tests/scenario_cache.py`); byte-pinned EV golden files are checked
out with LF (`.gitattributes`). Use the runner default (`-n 4` since OPS-04,
`-Workers` to override), never `-n auto`: each worker adds about 10-35 sessions,
against `max_connections = 200` (set in `docker-compose.yml`).

If a timing-sensitive test (S4 tick hung-stage and claims replay, health skew
and overlap race, drain 30 s deadline, work enqueue-lock poll) fails under
`-n 2`, do not retry it: record the node ID and its duration, rerun that file
serially as a separate invocation, and report both runs' JUnit counts.

## Recovery: Docker crash during a test-server run (PERF-01)

The test-only server (`assetopsv1-postgres-test-1`) runs with fsync off for speed. If Docker crashes or the machine
loses power while it is running, its data directory may be corrupt: stop the container and remove only the
`assetopsv1_assetops-test-pg` volume (`docker volume rm assetopsv1_assetops-test-pg`). It holds only disposable test
databases and is recreated by the next run. Never touch the development server's volume.
