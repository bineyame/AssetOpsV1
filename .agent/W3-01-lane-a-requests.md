# W3-01 Lane A requests (Lane B commit-2 run, 2026-10-20)

Lane B does not edit these Lane A files. Each is needed by W3-01 commit 2 (estate read/API).

1. **`tools/checks/configuration-persistence.ps1` read-only adapter allowance** (W3-02 Q8 shape, needed now by
   W3-01): add `$pgReaders = @("$backendRoot/estate/adapters/postgres_estate_read.py",
   "$backendRoot/estate/adapters/postgres_evidence_money_read.py")`; at the driver-import rule (`:822-830`) treat a
   `$pgReaders` path like a writer for the import, but keep it out of `$pgWriters`, `$pgWritesSeen` and the >=1-write
   anti-vacuity rule; any write-shaped clause in a reader fails. If adapter isolation needs it, add an `estate`
   entry to `$domains` with `Composition = "$backendRoot/estate/composition.py"`, `Writer = $null`. Guard self-tests
   per W3-02 Q8: `test_pg_reader_import_allowed`, `test_pg_reader_write_rejected`, `test_domain_driver_import_rejected`.
   Also the dependency-direction allowance from W3-01 S22-S24 (top-level `estate` may import read ports; adapters
   import no UI/API) if `tools/checks/dependency-direction.ps1` needs one.
2. **`backend/assetops_backend/main.py`**: mount `estate_api.build_estate_router(...)` (`GET /api/estate/scope`,
   `/api/estate/findings`, `/api/estate/actions`) from `estate/composition.py` after commit 2 lands. Exact builder
   signature will be in the commit-2 handoff.
3. **Pending q5 item 1**: if ruled Lane A, connection-taking variants of
   `postgres_finding_store.index_snapshot/fence/index_lineage`, `DispatchReadService.window` (as-of `known_at`) and
   `postgres_action_store.site_window`, each taking the caller's REPEATABLE READ `Connection`, with focused tests.
