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

# serve
.venv/Scripts/python.exe -m uvicorn assetops_backend.main:app --port 8000
```

The first migration enables `btree_gist`. A database role that cannot create
the extension fails the migration with a message naming the fix; there is no
fallback.

## Tests

The Compose service also creates `assetops_test`, a disposable database used
only by the Postgres tests. They drop its schema and run every migration from
zero; they never touch the developer database.

```sh
export ASSETOPS_TEST_DATABASE_URL=postgresql+psycopg://assetops:assetops-local-dev@127.0.0.1:55432/assetops_test
.venv/Scripts/python.exe -m pytest backend/tests/test_s1_foundation_postgres.py
```

Without `ASSETOPS_TEST_DATABASE_URL` those tests are reported as skipped, not
passed. They refuse to run against a database whose name does not end in
`_test`.
