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
- **One full suite at a time on this machine.** Concurrent full runs are not
  yet proven safe (OPS-01 phase 2 measures this). Other Postgres-heavy agents
  slow a run by about 2x and make its timing meaningless.
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
<base without _test>_pt<run>_<tag>_test     tag = main (serial), tpl (template)
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

# S4 Finding and money
& $py -m pytest backend/tests/test_s4_finding_store_postgres.py backend/tests/test_s4_finding_read_postgres.py backend/tests/test_s4_finding_evidence_history_postgres.py backend/tests/test_s4_assumptions_postgres.py backend/tests/test_s4_consequence_store_postgres.py backend/tests/test_s4_consequence_recompute_postgres.py backend/tests/test_s4_evidence_consequence_work_postgres.py backend/tests/test_s4_evidence_drain_postgres.py backend/tests/test_s4_power_demo_case_postgres.py backend/tests/test_s4_schedule_tick_postgres.py backend/tests/test_s4_schedule_health_postgres.py

# Complete suite, with JUnit for the zero-skip proof
& $py -m pytest backend/tests -q --durations=30 --junitxml=.pytest-junit.xml
```

### Before a long full run

Start the keep-awake helper in a separate window (or as a background job). It
asks Windows not to idle-sleep while any pytest process runs, changes no power
settings, and exits after 20 idle minutes. A machine that sleeps mid-run turns
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
| Before OPS-01 (in-place migrate per module) | see OPS-01 phase-1 handoff | baseline |
| Serial template clone (OPS-01 phase 1) | see OPS-01 phase-1 handoff | |
