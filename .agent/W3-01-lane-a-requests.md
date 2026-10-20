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

## Commit-2 Lane B core landed (2026-10-20): Lane A second same-branch handoff

1. **Guard domain** (q5 ruling 3, prerequisite r1 L3): add `@{ Name = "estate"; Package = "$backendRoot/estate";
   Composition = "$backendRoot/estate/composition.py"; Writer = $null; UserRootVar = $null; UserRootOwner = $null }`
   to `$domains` in `tools/checks/configuration-persistence.ps1`, plus `test_pg_reader_import_allowed`,
   `test_pg_reader_write_rejected`, `test_domain_driver_import_rejected`. This is the only check-all failure at the
   Lane B head: `Adapter import that resolves outside every known configuration domain in
   backend/assetops_backend/estate/composition.py:21`.
2. **Mount** in `main.py`: `build_estate_router(build_estate_index_service(database_url), registry_tenant(registry),
   authenticate=..., access=<the Finding route Access>, unavailable=(SiteStoreUnavailable,))` from
   `estate_api.py` / `estate/composition.py`. `build_estate_index_service(None)` returns None (router answers 503).
   Default `authenticate` admits (development, like `development_access`).

## Commit-3 Lane B estate roots landed (2026-10-20): Lane A third same-branch handoff

Lane B added only `frontend/src/estate/{estateClient.ts,estateShared.tsx,findingIndex.tsx,actionIndex.tsx,estate.css}`
and `frontend/src/estate/__tests__/{estateFixtures.ts,estateRoots.test.tsx}`. The pages are tested under a local
MemoryRouter. Lane A's integration, in the same reviewed merge as the five pages (spec commit 3 and Review closure B1/B2):

1. **Routes** (`frontend/src/App.tsx` and `frontend/src/shell/operatorSiteRoutes.ts`). Replace only the global `/findings`
   element (currently `<FindingsFrame analytics={siteAnalytics}/>`, `App.tsx:375-378`) with
   `<EstateFindingsPage lens="all" client={estateIndex}/>`. Add `/findings/cost`, `/findings/risks` and
   `/findings/opportunities` with `lens="cost"|"risks"|"opportunities"`, and add `/actions` with
   `<EstateActionsPage client={estateIndex}/>`. These must take precedence over the legacy
   `/findings/:siteId/:assessmentId[/:findingTab]` patterns. Legacy paths keep their handlers and tests, and `/api/findings`
   is unchanged. Path constants are `ESTATE_FINDING_LENS_PATHS` (`frontend/src/estate/findingIndex.tsx`) and
   `ESTATE_ACTIONS_PATH` (`frontend/src/estate/actionIndex.tsx`); reuse them or mirror them in `operatorSiteRoutes.ts`.
   Each page renders its own `PageHeader`, and needs the shell's `<main>`.
2. **Client prop**: add the optional App prop `estateIndex?: EstateClient`, defaulting to `createEstateClient()` from
   `frontend/src/estate/estateClient.ts`. Shell tests can then inject `fakeClient` from
   `frontend/src/estate/__tests__/estateFixtures.ts`.
3. **Rail**: in `OperatorShellLayout.tsx:55`, Actions becomes `{kind:"live", to:"/actions", label:"Actions", group:"WORK"}`.
   In `tools/checks/navigation-truthfulness.ps1` `Get-OperatorRailFailures` (expected list `:545-557`), change
   `unavailable|Actions|WORK|` to `live|Actions|WORK|/actions` atomically, together with its rail fixtures
   (`navigation-rail-fixtures.ps1`). Do not promote Incidents or Maintenance.
4. **Unchanged multisets**: the estate pages render no `UnavailableTab`/`UnavailableChip`, so keep the in-page
   unavailable multiset as it is. The Site `SiteFindingIndex.tsx:74-85` Cost/Risks/Opportunities chips stay.
5. **Registry**: add the paths `A-estate-index-scope`, `A-estate-action-summary`, `I-estate-finding-root`,
   `I-estate-action-root` and the owned panel paths for v69 `findings`, `findings-cost`, `findings-risks`,
   `findings-opportunities` and `actions`. Then run the registry checker.
6. **Shell tests** named in Review closure: `test_existing_findings_api_and_legacy_routes_unchanged`,
   `test_site_lens_chips_remain_unavailable` and `test_estate_route_precedence_and_actions_rail`.
