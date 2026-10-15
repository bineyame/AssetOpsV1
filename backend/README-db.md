# Product database (S1-01)

The persisted Foundation lives in PostgreSQL 16, run locally from the pinned
service in `docker-compose.yml` (`postgres:16.4-alpine`). Alembic migrations in
`backend/migrations` own every table; the application never creates schema.

`DATABASE_URL` is required on the product path. Nothing in the backend
defaults it: without it the product Sites index and Foundation routes answer
`503` (fail closed) rather than treating every Site as unimported.

## Local development values

The Compose file documents one **local development** default password
(`assetops-local-dev`, override with `ASSETOPS_PG_PASSWORD`) and publishes the
service on `127.0.0.1:55432` (override with `ASSETOPS_PG_PORT`). It is not a
credential for any shared environment.

```sh
# from the repository root
docker compose up -d postgres

# developer database
export DATABASE_URL=postgresql+psycopg://assetops:assetops-local-dev@127.0.0.1:55432/assetops
# PowerShell: $env:DATABASE_URL = "postgresql+psycopg://assetops:assetops-local-dev@127.0.0.1:55432/assetops"

# migrate (from backend/)
cd backend && ../.venv/Scripts/python.exe -m alembic upgrade head && cd ..

# one-shot import of the Kobo Site document (from the repository root)
.venv/Scripts/python.exe -m assetops_backend.sites.import_kobo \
  --source var/sites/kobo-001.yaml --tenant demo \
  --report .agent/S1-01-import-comparison.md

# S1-02: publish the first signal binding set (one atomic Foundation-plus-binding
# change; a rerun writes nothing). Decision D-2026-10-08-s1-bindings-roles-and-snapshot.
.venv/Scripts/python.exe -m assetops_backend.sites.convert_kobo_bindings   --fixture backend/conversions/kobo-001-bindings.json --tenant demo

# serve
.venv/Scripts/python.exe -m uvicorn assetops_backend.main:app --port 8000
```

The first migration enables `btree_gist`. A database role that cannot create
the extension fails the migration with a message naming the fix; there is no
fallback.

Migration 0003 (pinned snapshots) refuses to run over binding sets published
under 0002 alone, because their snapshot hash cannot be backfilled honestly.
That state exists only on a scratch database used during S1-02 development.
Recreate that database and rerun the conversion.

Migration 0004 stores each pinned snapshot's canonical bytes
(`snapshot_canonical`, NOT NULL, CHECKed against `snapshot_sha256`); the
download serves those bytes instead of rebuilding them from registration rows.
Over a database that already holds binding sets (for example a converted
developer database) it backfills each row with the v1 serializer, and writes the
bytes only when they reproduce the pinned hash. If a registration identity field
(Site code, gateway external ID or mode, source external ID) changed after
publication, the rebuilt bytes miss the hash and the migration refuses, naming
the rows; it never recomputes a published hash.

## Tests

The Compose service also creates `assetops_test`, a disposable database used
only by the Postgres tests as an administrative base: every Postgres module
starts on a freshly cloned, fully migrated run-owned database; they never touch
the developer database.

```sh
export ASSETOPS_TEST_DATABASE_URL=postgresql+psycopg://assetops:assetops-local-dev@127.0.0.1:55432/assetops_test
.venv/Scripts/python.exe -m pytest backend/tests/test_s1_foundation_postgres.py backend/tests/test_s1_bindings_postgres.py
```

Without `ASSETOPS_TEST_DATABASE_URL` those tests are reported as skipped, not
passed. They refuse to run against a database whose name does not end in
`_test`.

The URL names a *base* database: each run clones run-owned
`<base>_pt<run>_<tag>_test` databases from a once-migrated template and drops
them at the end. Focused commands, the full-suite command, the zero-skip check
and when to run which are in [TESTING.md](TESTING.md).

## Consequence recompute runner (S4-02c)

Financial consequence work (migration 0011/0012 triggers) is drained by a one-shot, bounded runner for one
explicitly named tenant and Site. It is not an all-Site iterator and serves only the configured development
tenant (`demo`); any other tenant is refused with exit code 2.

```sh
# from backend/, with DATABASE_URL set
python -m assetops_backend.recompute_consequences run --tenant demo --site KOBO-001 --limit 100
python -m assetops_backend.recompute_consequences pending --tenant demo --site KOBO-001
```

- **Schedule (retired by S4-02d):** the S4-02c one-timer-per-Site schedule (`assetops-consequence-runner@<site>.timer`
  or the `AssetOps consequence runner <site>` scheduled task) is replaced by the environment tick below, which
  drains each Site's consequence work by IDs at DB time. Remove every per-Site timer in the same change that installs
  the tick; a legacy timer left running holds the Site advisory lock and makes the tick report `CONSEQUENCE_CLAIMED`.
  The CLI stays for one-off operator recovery: `now` is the database clock by default, or `--now <ISO with offset>`
  as an explicit override; the summary line reports `now_source` (`database` or `override`).
- **Owner (one-off runs):** whoever operates the deployment's backend host.
- **Overlap:** the run takes a session advisory lock `financial_consequence_runner:<site>` on a dedicated
  connection; a second run for the same Site reports `"skipped": true` and exits 0.
- **Recovery:** nothing manual. A failed item records a typed FAILED attempt and stays pending; it is retried
  1, 2, 4, 8, 16 minutes after its last failure, then every 16 minutes, with no cap. A killed run's lock is
  released with its connection; the next tick resumes, and an append-then-crash replays the same consequence ID.
- **Hung runner (alarm, one-off CLI runs):** the CLI run is not bounded by a timeout (the S4-02d tick bounds its drain child). A run that hangs (rather than dies) keeps its
  connection and its Site claim, so every later tick prints `"skipped": true` and still exits 0, and "Do not
  start a new instance" hides it further. Repeated `skipped` across consecutive ticks for one Site is the alarm
  signal: find the holding session (`pg_locks` advisory lock on `financial_consequence_runner:<site>`, or the
  stuck process) and end it; its lock is released with its connection and the next tick resumes.
- **Permanent failures (retry volume):** a deterministic failure (for example `EVIDENCE_NOT_ACCEPTED`,
  `EVIDENCE_LOCATOR_NOT_IN_SITE` or a `RECOMPUTE_FAILED` code defect) fails on every retry and appends about 90
  FAILED attempts per day per row, indefinitely; there is no terminal state or alert. Watch `pending` for rows
  whose attempt count keeps growing and repair the cause. Past roughly 1600 such rows per Site at `--limit 100`
  they alone would fill each run's capacity (FIFO-by-eligibility still bounds new work's delay, but the backlog
  grows).
- **Output:** one JSON line per processed item, then a summary line with the Site scope and the `selected`,
  `appended`, `replayed`, `no_op`, `failed`, `deferred` and `backlog` counts. Exit 1 when any item failed.
- S3 `process-jobs` and S4 `match-findings` are not run by this CLI; the S4-02d tick runs all three stages.

## Analytic and Finding worker schedule (S4-02d)

One environment-owned tick runs, per selected Site: S3 `process-jobs` (Site-scoped), S4 `match-findings` only
when the matcher fence or version moved, then the consequence drain, each in a killable child with server-side
`statement_timeout`/`lock_timeout`. Claims, leases, back-off, heartbeat and every health threshold use database
time (`clock_timestamp()`); the scheduled S3 worker, matcher and drain receive DB time as their `now`.

**I3, scheduled ingestion (S4-07).** `ingestion_disposition.decided_at` is database time: each chunk takes one
`clock_timestamp()` after its batch row lock, inside the transaction that writes the dispositions and coalesces the
recompute job. A newly inserted job is due (`available_at`) and created at that instant; widening a PENDING job lifts
its `available_at` to at least that instant (its `created_at` is kept), so a scheduled lease whose DB-time cutoff
predates the decision cannot consume it. The ingestion host's clock stamps only the receipt fields
(`ingestion_batch.received_at`, `completed_at`); under clock skew a batch's `completed_at` may precede its last
`decided_at`. Against the scheduled tick, a committed accepted decision is either inside a run's cutoff or carried
by live S3 work for a later tick (proved in `tests/test_s4_evidence_decided_at_postgres.py`). Residuals: a manual
app-clock `process-jobs` run beside the tick can still mix clocks, so I3 is not claimed closed for manual CLIs (stop
the tick first, below); configuration `recorded_at` versus `reconcile` is a separate comparand. `S3_STALE_NO_JOB` and
`requeue --day` remain as defense in depth. The deterministic fixtures pin decisions through the ledger's test-only
`test_decision_clock_override`, which production composition never sets.

```sh
# from backend/, with DATABASE_URL set
python -m assetops_backend.scheduling.run tick --environment demo        # one bounded tick (JSON report)
python -m assetops_backend.scheduling.run health --environment demo      # read-only report; exit 1 on an alarm state
python -m assetops_backend.scheduling.run heads --environment demo       # raw schedule heads
python -m assetops_backend.scheduling.run upstream --environment demo --tenant-id T --site-id S \
    --start 2026-10-06T00:00:00Z --end 2026-10-07T00:00:00Z               # S5 seam read of one window
python -m assetops_backend.scheduling.run enrol --tenant-id T --site-id S --by NAME [--off]
```

### Installation gate (read before installing anything)

**Do not install or enable the tick on any owner-visible host, including the demo host, until
`I-late-reading-series-and-money-limit` is `resolved` in `frontend/docs/architecture/v69-dependency-registry-pilot.json`**
(`D-2026-10-14-s402d-schedule-storage-and-install-gate`). An automatic tick would otherwise move the known run-1
late reading to an apparently current, too-low amount on the S4-02b money panel. Check first:

```sh
python tools/schedule-install-gate.py --host-class demo      # exit 2 and the reason while the gate is closed
```

| Environment | Owner and identity | Cadence / gate |
| --- | --- | --- |
| Local development | Developer; local database credential | Optional one-minute tick on a private DB (`--host-class private`). |
| Demo host | Deployment operator; a dedicated schedule credential scoped to that database | One minute, only after the F1 node is resolved. |
| Isolated walkthrough DB | Walkthrough runner; isolated DB credential | Explicit `tick` invocations only; no timer. |
| Real-Site pilot | Pilot deployment operator; separately provisioned schedule credential | Not installed until `real_pilot_requires` and the pilot gates close. |

When the gate tool reports the host class open, install exactly one timer per environment:

- **systemd:** copy `backend/deploy/schedule/assetops-schedule-tick@.service` and `@.timer` to `/etc/systemd/system/`,
  set `WorkingDirectory` and the venv path, put `DATABASE_URL` (the schedule credential) in
  `/etc/assetops/schedule-tick.env`, then `systemctl daemon-reload && systemctl enable --now assetops-schedule-tick@<env>.timer` (the instance
  name is the `--environment`). Stop: `systemctl disable --now assetops-schedule-tick@<env>.timer`; restart: `enable --now` again.
- **Windows Task Scheduler:** `schtasks /Create /TN "AssetOps schedule tick <env>" /SC MINUTE /MO 1 /TR "<venv>\Scripts\python.exe -m assetops_backend.scheduling.run tick --environment <env>"`
  with "Do not start a new instance", start-in `backend/`, and `DATABASE_URL` in the task's environment.
- **Retire the per-Site consequence timer in the same change** (below): `systemctl disable --now
  assetops-consequence-runner@<site>.timer` for every Site, or `schtasks /Delete /TN "AssetOps consequence runner <site>" /F`.
  A legacy timer left running holds the drain's Site advisory lock, and the tick then records `CONSEQUENCE_CLAIMED`
  for that Site as a stage failure with back-off (an alarm, not a pass).

**Bounds (defaults, `TickLimits`):** at most 20 Sites, 10 S3 jobs and 50 consequence items per Site per tick; stage
bounds discover/S3/S4 120 s and consequence 60 s (the S3 bound stays under the five-minute S3 job lease);
`statement_timeout` 30 s and `lock_timeout` 5 s on every stage connection; back-off 60 s doubling to 960 s. A
tick visits Sites after a durable fair cursor; work beyond the bounds waits for later ticks.

**Measured cost (Windows dev host, phase 2):** a tick spends about 1 s per stage child start, so roughly 3-4 s per
Site visited plus a global `reconcile_all()` of ~0.2-0.3 s: 1 Site ~4-5 s, 4 Sites ~12.6 s. At one-minute cadence
`max_sites` 20 fits only on a host whose child start is well under a second; measure on the target host and lower
`--max-sites` (the cursor keeps the rotation fair) rather than shortening stage bounds.

### Health, alarms and recovery

`health` reports the environment and every Site as `STOPPED`, `FAILED`, `RETRY_DUE`, `BACKLOG`, `RUNNING` or
`IDLE` (worst first), with typed alarms; all ages are DB time. Default stop thresholds: environment heartbeat older
than 300 s (`HEARTBEAT_STALE`, `TICK_NEVER_COMPLETED`); a scheduled Site with no finished visit for 900 s
(`SITE_VISIT_STALE`). Only a completed tick advances the heartbeat; `last_started_at` is stamped when a tick takes
its claim (also one that returns `RETRY_DUE`) and is never read as liveness.

| Alarm | Meaning | Recovery |
| --- | --- | --- |
| `HEARTBEAT_STALE` / `TICK_NEVER_COMPLETED` | The timer is stopped, failing in discovery, or never ran. | Check the timer and `heads`; `last_failure_code` on the tick head names the cause. |
| `TICK_CLAIM_STALE` / `SITE_CLAIM_STALE` | A tick or Site claim outlived its lease (crashed holder). | None needed: the next tick takes the expired claim over; investigate the crashed host. |
| `SITE_CLAIM_SKIPS` | The Site claim was held across three ticks (hung holder). | Find the holder in `heads` (`claim_owner` = host:pid) and end it; its lease then expires. |
| `SITE_FAILING` | Three consecutive Site stage failures (`last_failure_stage/code/detail`). | Fix the named cause; back-off retries automatically. |
| `FENCE_MOVED_STREAK` | Three `FENCE_MOVED` S4 outcomes running (concurrent writes keep moving the fence). | Usually clears on the next quiet tick; persistent: inspect concurrent writers. |
| `MATCH_EVIDENCE_NOT_ACCEPTED` | Deterministic matcher defect: a cited evidence ID is not accepted in this Site. | Code/data defect; not retried into success. |
| `S3_JOB_FAILED` | A terminal FAILED S3 job (ID, window, `last_error`); `reconcile` will not re-enqueue it. | After fixing the cause: `python -m assetops_backend.analytics.assess_dispatch requeue --tenant-id T --site-id S --job-id J`; the new DEFAULT selection supersedes the failure. `assess` is not recovery. |
| `S3_STALE_NO_JOB` | A selected UTC day reads `STALE_PROJECTION` (for example `INPUT_BASIS_CHANGED`) and no live S3 job intersects it, so no tick will rebuild it (defense in depth since S4-07; see I3 above). | Once the DB clock has passed the late decision: `python -m assetops_backend.analytics.assess_dispatch requeue --tenant-id T --site-id S --day YYYY-MM-DD` (refused unless that day is STALE with no live job); the next tick rebuilds it. |
| `CONSEQUENCE_ATTEMPTS_GROWING` | Unsucceeded consequence work with 5+ attempts (no terminal cap; ~90/day). | Repair the cause; `recompute_consequences pending` lists the rows. |
| `STALE_NO_WORK` | A pre-0012 consequence head is STALE with no recorded work (Finding/revision IDs given). | Reported only; not backfilled by this slice. |
| `EXCLUDED_WITH_WORK` / `S4_BACKLOG_OUTSIDE_ACTIVE_SET` | A Site outside the active set still has work, or an unmatched selection the tick no longer visits. | Re-enrol (`enrol`) or resolve the work deliberately. |
| `CONSEQUENCE_CLAIMED` (stage code) | The drain's Site lock is held elsewhere, usually a legacy per-Site timer. | Retire the per-Site timer. |

**Manual Leg B commands:** `process-jobs`, `match-findings` and `recompute_consequences run` do not take the
schedule's Site claim. **Stop the tick (disable the timer) and confirm `heads` shows no Site claim before running
any of them by hand**, then re-enable it. The matcher fence still protects Finding writes, but S3/S4 serialisation
is only guaranteed between scheduled stages. A manual `process-jobs` also takes its knowledge cutoff from the
application clock, not DB time, so beside a running tick it can mix clocks with DB-time decisions (I3 manual residual).
