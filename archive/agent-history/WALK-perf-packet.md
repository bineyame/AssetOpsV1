> Finished; historical. Archived from .agent/WALK-perf-packet.md on 2026-11-18 (declutter step 4).
# WALK-perf packet (branch fix/WALK-perf, worktree /opt/assetecon/AssetOpsV1-walkperf)
Spec: .agent/WALK-perf-ruling-2026-11-14.md F1-F3. Commits: f6c67e34b (F1-F3 + tests), plus one guard follow-up.

## What changed
- F1 `backend/assetops_backend/site_overview/route.py` (~162-175): `gate()` + `basis_reason()` moved into `compose()`.
- F1 `backend/assetops_backend/finding_index_api.py` (~72-90): gate + 409 PERFORMANCE_CUTOVER_CLOSED + `except down` moved to top of `compose()`.
- F2 `backend/assetops_backend/finding_api.py`: `FINANCIALS_ROUTE`, `responses` param, handler body in `compose()`, `responses.serve(StoredRoute(...))`; `main.py:~591` passes `responses=responses`.
- F2 `backend/assetops_backend/chain/prebuild.py`: `financials_paths()`, fetched via `fetch` (INFRA-1 retries), de-duplicated per run, counted in `extra`.
- F2 `tools/chain_watermark_guard.py` `chain_paths`: adds the financials path of the first prebuilt KOBO Overview that names a `known_finding`.
- F3 `tools/demo_combined.py`: `prebuild_states()`, pure `warm_due()`, `WARM_REFRESH_SECONDS=1800`; `performance_and_prebuild` returns states (also `self.last_prebuild_states`); serve loop warms only when due (first tick / non-hit state / 30 min). A change seen while a warm is running is kept pending.
- Tests: new `backend/tests/test_walkperf_gate_in_compose.py` (10 tests: overview hit/miss gate; index hit + closed 409 unstored; financials hit skips gate+reads, key by finding/revision, closed 409 unstored, no-store path; financials_paths; prebuild retries/dedupe; warm_due table). Updated `test_infra1_degraded_store.py` pinned-board test for the extra financials fetch.

## Tests
- Targeted: new file + test_s5_overview_read, test_e4_prebuilt_routes_generator/source, test_sr83_guard_route_terms, test_sr83_store_term, test_infra1_degraded_store, test_ch5c2_clock_guard, test_s4_finding_api, test_s4_finding_index_reach, test_ch5c_store_off: 154 passed, 1 skipped (before the infra1 test fix; infra1 file rerun 26 passed).
- check-all (`pwsh tools/check-all.ps1`, needs a .venv/Scripts/python.exe shim on Linux, removed after): 21/21 PASS, 0 FAIL.
- chain_watermark_guard on clones of assetops_polish_up1copy_test and assetops_polish_vps1_test (scratch *_audit_test DBs, dropped): rc 0, unresolved [], untracked [], file_violations 0, clock_predicates 0. unlisted_modules `assetops_backend.infra` and `outcomes.price_action` (price_action is imported by finding_api already; not checked against main).

## Deviations / open
- Guard did NOT exercise the financials route: on both clones the only prebuilt KOBO Overview (2026-10-03) and index return 409 (gate closed), so there is no known_finding. I changed chain_paths to take the first KOBO Overview that names a Finding (spec said "first"); it needs a DB with an open gate to confirm no untracked input. Re-run on the walk DB clone (or a clone) before relying on W6.
- Existing test_infra1 pinned-board test edited (extra financials call and requests 3).
- No live serve, walk DB, or tree refresh done; deploy steps in the ruling remain for the coordinator.

## Fix round (review M1/M2)

- **M1 fixed.** `backend/tests/test_ch5c_response_store_postgres.py::test_walkperf_m1_financials_through_the_real_store_misses_after_a_price_row_write`: the real Finding router, real `ResponseStore`, watermark and change log, store forced on, on the run-owned clone of `assetops_test`. First read `stored`, second `hit` (same bytes), then an INSERT into `financial_assumption_revision` makes the next read `stored` with a different body. The Finding read is a stub whose title carries the price-row count, so "new body" is the price write showing through; the real consequence composition is not exercised.
- **M2 fixed.** `tools/chain_watermark_guard.py` result gains `"financials"`: `"exercised"` or `"not exercised: no KOBO Overview names a Finding"`; the summary line prints it. rc unchanged (0 when otherwise clean). The guard was not rerun (needs an open-gate DB).
- **Lows skipped.** L1 (record `prebuild_ms`/`non_200` at deploy: a deploy-time action, not code) and L2 (preference, review says not a gap).
- **Checks.** 4 touched test files: 35 passed. check-all: 21/21 guards passed (run with `-Python /opt/assetecon/AssetOpsV1/.venv/bin/python`).
