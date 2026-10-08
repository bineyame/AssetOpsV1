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
