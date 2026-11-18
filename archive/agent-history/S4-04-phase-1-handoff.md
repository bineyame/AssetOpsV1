# S4-04 phase 1 handoff - Site Finding index read

Branch `task/S4-04-site-finding-index` (base main `f8a131e3`). Phase 1 commits: `ae526aae` (code + tests), then the TESTING.md line. Not merged; packet status unchanged (`active`); phase-1 review pending.

## What landed
- `GET /api/sites/{site_code}/finding-index?domain=mini-grid-dispatch&from=&to=&limit=&cursor=`
  - `backend/assetops_backend/finding_index_api.py` (router `build_finding_index_router`). Check order: 401/403/404/503 -> typed 422 (`UNSUPPORTED_DOMAIN`, `INVALID_WINDOW`, `INVALID_LIMIT`, `INVALID_CURSOR`) -> gate 409 `PERFORMANCE_CUTOVER_CLOSED` -> read (409 `INDEX_CONTINUITY_LIMIT`, 409 `INDEX_BASIS_CHANGED` with `reason` SCOPE_CHANGED / BASIS_NOT_CURRENT / SELECTION_CHANGED and `instruction`). No refusal carries status, rows or count.
  - Mounted in `main.py` beside the Finding router (same `registry.ledger_scope`, `performance_gate`).
- Service `backend/assetops_backend/analytics/finding_index.py`: `parse_request`, `discover` (fixed point, `INDEX_CONTINUITY_LIMIT = 62`), `sort_key` (same rule as S5-01 `choose`), `FindingIndexService.read`. Composition `build_finding_index_service` in `analytics/composition.py`.
- Store reads (SELECT only) appended to `analytics/adapters/postgres_finding_store.py`: `index_snapshot` (latest revision per Finding of domain/analytic + merge/split/recurrence links + per-window max selection seq + latest pass + writer fence, one REPEATABLE READ tx) and `index_lineage` (page citations, evidence IDs, run configuration). `findings_over` untouched.
- Status: `CURRENT` only when every inspected day is S3 CURRENT, S4 pass `selection_seq >=` that day's seq, and the writer fence is unchanged after the S3 reads. Otherwise worst of FAILED > STALE_PROJECTION > PENDING (incl. MATCH_PENDING) > UNASSESSED, rows `[]`, `total_count` null, `rows_statement` explains (no snapshot).
- Rows: key, canonical ID, exact `finding_revision_id`, episode, lifecycle/transition, assessment/run/model/cohort, cited evidence + configuration, limitations, relations (merged_from, recurs_after, recurred_by, split_from, split_parts), links (`selected_revision` `/sites/{code}/findings/{id}?revision_id=`, canonical, api_selected_revision, api_history), `amount` UNAVAILABLE.

## Tests (`backend/tests/test_s4_finding_index_postgres.py`, 9 tests, ~40 s)
Scope/validation/gate; independent assessed-empty CURRENT with S3/S4 watermarks, boundary touch, wrong window/Site/tenant, PENDING-before-match, dirty/leased/failed no-snapshot; 3-day bridge chain (beyond one neighbour), dirty/failed neighbour 2 days out, cap via injected limit 2 plus pure 62-day test; positive F01-F08 fixture: order, cursor pages, merge/split/recurrence, closed (NO_LONGER_SUPPORTED) and UNCONFIRMED rows, exact pinned link, S5-01 card parity on 2026-10-15; UUID-tie parity vs `choose`; late revision -> cursor 409 and old pinned link still 200; fence moved -> STALE.
Run: new + store/read/schedule-health/finding_api/health files: 49 passed in 388 s. `tools/check-architecture.ps1` passed. Mutations (each caught, reverted): CURRENT-only rows gate, closed-gate 409, continuity cap.

## Deviations / open for review
- Bridge reachability uses stored canonical episodes within 20 min of a UTC edge (the matcher's `margin_ok` dependency), not a re-run of raw-evidence bridging; an unmatched cross-midnight candidate is already blocked by MATCH_PENDING.
- 62-day cap proven by a pure test and by an injected cap of 2 on real data (a 62-midnight real fixture is too slow).
- UUID-tie and moving-fence proofs are unit-level (no real-data tie; race injected by a fake store).
- Selection token includes the Site-wide latest match pass and the full intersecting row set, so any new pass on the Site restarts cursors (conservative).
- A cursor presented while the index is not CURRENT gets 409 `BASIS_NOT_CURRENT`, not a 200 non-current body.
- `display_timezone` is `UTC` (no Site timezone reaches this scope seam).
- Copy (for the W1 plain-language task): `rows_statement`, `KNOWLEDGE_AT` label, 409 messages are engineering wording.

## Phase 2 next
Typed client + Site Findings UI (`frontend/src/sites/FindingsIndexes.tsx`, `siteAnalyticsClient.ts`, routes at `App.tsx:248-255`, `operatorSiteRoutes.ts:135-139`), URL-persisted scope, states incl. continuity-limit Unknown and cursor restart; `tools/s404_finding_index_walkthrough.py`, `tools/s404-finding-index-evidence.mjs`; frontend tests; one full real-Postgres suite at final revision; review packet.

Env notes: private DB `assetops_s404p1_test` (base) exists on 127.0.0.1:55432; PYTHONPATH = worktree `backend;contracts;gateway;simulator`.
