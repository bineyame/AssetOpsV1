# Owner authorization - test databases (2026-10-18)

Owner, verbatim: "yes, allow creating and dropping the test databases"

Scope: agents working on AssetOps may CREATE and DROP private test databases named `assetops_*_test` / `*_test` (including tool-created capture/fixture databases such as `assetops_w204cap_test`) in the local Docker Postgres container `assetopsv1-postgres-1` (127.0.0.1:55432), via `docker exec ... createdb/dropdb`, `psql ... drop database ... with (force)`, the repo's test fixtures and walkthrough/capture `prepare`/`drop` tools, and pytest's run-owned databases. Not authorized: dropping or altering non-test databases (e.g. `assetops`, `assetops_test` template use is read-only unless a tool owns it).
Permission rules added in the owner's project settings (`.claude/settings.local.json`). Agents cite this file if a permission check asks.
