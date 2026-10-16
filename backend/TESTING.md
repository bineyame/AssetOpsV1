# Backend testing guide

How to run the backend suite, when to run all of it, and how to prove a full
run was real. Database setup itself is in [README-db.md](README-db.md).

## When to run what

- **While building a phase:** run the focused files for the area you changed,
  plus adjacent integration tests. When an interface crosses into the host or
  gateway, also run those suites.
- **At the end of an ordinary slice:** one real-Postgres full backend suite,
  on the slice's final revision, with the JUnit zero-skip check below. Cite it
  in the review packet.
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
- Measurement knobs, off by default: `ASSETOPS_TEST_CLONE_STRATEGY`
  (`WAL_LOG` or `FILE_COPY`) and `ASSETOPS_TEST_SYNCHRONOUS_COMMIT` (applied with
  `ALTER DATABASE` to run-owned databases only). Server-wide settings are never
  changed by the tests.

## Commands (PowerShell, from the repository root)

```powershell
$env:ASSETOPS_TEST_DATABASE_URL = "postgresql+psycopg://assetops:assetops-local-dev@127.0.0.1:55432/assetops_test"
$py = ".venv\Scripts\python.exe"

# S1 Foundation and bindings
& $py -m pytest backend/tests/test_s1_foundation_postgres.py backend/tests/test_s1_bindings_postgres.py backend/tests/test_s1_cutover.py backend/tests/test_s1_bindings.py

# S2 ingestion and evidence
& $py -m pytest backend/tests/test_s2_evidence_ledger_postgres.py backend/tests/test_s2_gateway_access_postgres.py backend/tests/test_s2_site_evidence_postgres.py backend/tests/test_s2_registered_basis_postgres.py

# S3 dispatch
& $py -m pytest backend/tests/test_s3_dispatch_assessment_postgres.py backend/tests/test_s3_dispatch_read_postgres.py backend/tests/test_s3_demo_configuration.py

# S3-02a capability and claim-limit read
& $py -m pytest backend/tests/test_s3_capability_read_postgres.py backend/tests/test_s3_claim_limit_postgres.py

# S4 Finding and money
& $py -m pytest backend/tests/test_s4_finding_store_postgres.py backend/tests/test_s4_finding_read_postgres.py backend/tests/test_s4_finding_index_postgres.py backend/tests/test_s4_finding_evidence_history_postgres.py backend/tests/test_s4_assumptions_postgres.py backend/tests/test_s4_consequence_store_postgres.py backend/tests/test_s4_consequence_recompute_postgres.py backend/tests/test_s4_evidence_consequence_work_postgres.py backend/tests/test_s4_evidence_drain_postgres.py backend/tests/test_s4_power_demo_case_postgres.py backend/tests/test_s4_schedule_tick_postgres.py backend/tests/test_s4_schedule_health_postgres.py

# Complete suite - the normal full command (two workers), with JUnit for the zero-skip proof
& $py -m pytest backend/tests -n 2 --dist loadfile --no-loadscope-reorder -q --durations=30 --junitxml=.pytest-junit.xml

# Complete suite, serial (fallback; also what a serial re-check of one file uses)
& $py -m pytest backend/tests -q --durations=30 --junitxml=.pytest-junit.xml
```

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
powershell -NoProfile -ExecutionPolicy Bypass -File tools\keep-awake-during-tests.ps1
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

## Timing

Measured on this Windows host (Docker Desktop Postgres 16), serial, full
suite. Run-to-run variance is large (disk sync inside Docker Desktop), so
compare only back-to-back runs in a quiet window.

| Revision | Runs (wall) | Notes |
| --- | --- | --- |
| Before OPS-01 (in-place migrate per module, TRUNCATE per test) | 80.3 min, 41.4 min; peak 91 sessions | 2 timing-sensitive tick failures in the 80-min run; a third attempt reached 34% in 4 h while the machine slept |
| Serial template clone + DELETE cleanup (OPS-01 phase 1) | 30.8 min (back-to-back with the 41.4-min baseline); peak 22 sessions | template clone without DELETE cleanup: 41.4 min, one 23-min disk stall in a tick test |
| `-n 2 --dist loadfile` (OPS-01 phase 2, normal command) | 7.7 min, 8.4 min; peak 35 and 32 sessions | 2128 passed, 0 skipped, 0 failed both times; node IDs identical to serial collection |
| `-n 3 --dist loadfile` (OPS-01 phase 2, one run) | 6.5 min; peak 41 sessions | 2128 passed; not repeated, so not the default |

Expected `-n 2` full run: about 8-10 min; cap at 20 min. Expected serial full
run: about 30-45 min; cap at 90 min. Use `-n 2`, never `-n auto`: the suite is
disk-bound inside Docker Desktop, and each worker adds about 10-20 sessions
against `max_connections = 100`.

If a timing-sensitive test (S4 tick hung-stage and claims replay, health skew
and overlap race, drain 30 s deadline, work enqueue-lock poll) fails under
`-n 2`, do not retry it: record the node ID and its duration, rerun that file
serially as a separate invocation, and report both runs' JUnit counts.
