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
only by the Postgres tests. They drop its schema and run every migration from
zero; they never touch the developer database.

```sh
export ASSETOPS_TEST_DATABASE_URL=postgresql+psycopg://assetops:assetops-local-dev@127.0.0.1:55432/assetops_test
.venv/Scripts/python.exe -m pytest backend/tests/test_s1_foundation_postgres.py backend/tests/test_s1_bindings_postgres.py
```

Without `ASSETOPS_TEST_DATABASE_URL` those tests are reported as skipped, not
passed. They refuse to run against a database whose name does not end in
`_test`.

## Consequence recompute runner (S4-02c)

Financial consequence work (migration 0011/0012 triggers) is drained by a one-shot, bounded runner for one
explicitly named tenant and Site. It is not an all-Site iterator and serves only the configured development
tenant (`demo`); any other tenant is refused with exit code 2.

```sh
# from backend/, with DATABASE_URL set
python -m assetops_backend.recompute_consequences run --tenant demo --site KOBO-001 --limit 100
python -m assetops_backend.recompute_consequences pending --tenant demo --site KOBO-001
```

- **Schedule:** an external timer runs it every minute, one task per Site. Windows Task Scheduler:
  `schtasks /Create /TN "AssetOps consequence runner KOBO-001" /SC MINUTE /MO 1 /TR "<venv>\Scripts\python.exe -m assetops_backend.recompute_consequences run --tenant demo --site KOBO-001 --limit 100"`
  with "Do not start a new instance" and a start-in directory of `backend/`. systemd: a `Type=oneshot`
  `assetops-consequence-runner@.service` (`ExecStart=<venv>/bin/python -m assetops_backend.recompute_consequences run --tenant demo --site %i --limit 100`,
  `EnvironmentFile` holding `DATABASE_URL`) and a matching `.timer` with `OnCalendar=*-*-* *:*:00`.
- **Owner:** whoever operates the deployment's backend host.
- **Overlap:** the run takes a session advisory lock `financial_consequence_runner:<site>` on a dedicated
  connection; a second run for the same Site reports `"skipped": true` and exits 0.
- **Recovery:** nothing manual. A failed item records a typed FAILED attempt and stays pending; it is retried
  1, 2, 4, 8, 16 minutes after its last failure, then every 16 minutes, with no cap. A killed run's lock is
  released with its connection; the next tick resumes, and an append-then-crash replays the same consequence ID.
- **Hung runner (alarm):** the run is not bounded by a timeout. A run that hangs (rather than dies) keeps its
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
- S3 `process-jobs` and S4 `match-findings` are not scheduled by this runner (packet risk R1).
