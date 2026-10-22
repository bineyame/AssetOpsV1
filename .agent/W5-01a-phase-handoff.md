# W5-01a C1 handoff — PARTIAL (Cooling built; Health held on an Architect question)

Branch `task/W5-01a-cold-selected-depth` from main `68b88dae`. Build commit `703807cf`.

## What was built

- `backend/assetops_backend/cold_site_api.py`: nested `opened`/`served` extracted to importable `build_cold_gate(registry, reads, access, disclosure)` and `cold_served(work)`; same refusal order, codes and messages. `build_cold_site_router` now uses them.
- `backend/assetops_backend/analytics/cold_depth.py`: `ColdDepthReadService.cooling(...)` on one `ColdReadService.within` connection: `selection_on` snapshot, `known_at > watermark` 422 `COLD_TIME_INVALID`, `envelope_on(...)["source_provenance"]` (EXC+START revision-ID selection), `accepted_on` for the exact selected IDs (door/grid event kind + source time). `recovery_state` from the W2 `COOLING_RESPONSE` capability (`ColdSiteReadService._capabilities`), restart/return/durations null, `comparison_state` `CONTEXT_MISSING`, five context rows. `door_pairs` pairs each OPEN with the next strictly later CLOSE.
- `backend/assetops_backend/cold_depth_api.py`: `GET /api/sites/{site_code}/cold/cooling` (WINDOW_KEYS, no 409). Mounted in `main.py` after the W2-04 cold Site router.
- Tests: `backend/tests/test_w501_cold_depth_router.py` (`test_cold_depth_gate_and_links`, `test_door_pairs`), `backend/tests/test_w501_cold_depth_postgres.py` (`test_cooling_first_steps_and_context` backup-failed: door Observed 60 s, power Observed, exact IDs/provenance/watermark, links, wrong Site 404, foreign tenant empty, disclosure 403, down store 503, future known_at 422; `test_late_reading_pending_then_historical` first cutoff, PENDING/LEASED/FAILED job, saved before-late `known_at` HISTORICAL, final cutoff; `test_stale_probe_window` enqueued 19:00-20:30 window gives STALE_SOURCE; `test_missing_probe_and_empty`; `test_no_w2_case_has_numeric_comparison` all six W2 cases).

## Response shape chosen (reviewer: confirm or rule)

`{schema_version, site_id, window{from,to,known_at,committed_watermark}, selection{state, assessment_revision_ids, accepted_evidence_ids, source_provenance}, cooling{recovery_state, selected_points[{role,source_time,evidence_ids}], observed_restart_at, observed_return_to_policy_at, duration_lower_seconds, duration_upper_seconds, comparison_state, context[{label,state,evidence_ids,duration_seconds}]}, links{temperature,backup,evidence,health}}`. These were not literal in the card:
1. The page payload key is `cooling`.
2. The context row keys are `label/state/evidence_ids/duration_seconds`, with state `Observed`/`Unknown`.
3. When several door pairs match, `duration_seconds` is their sum.
4. A point is dropped when its step evidence ID is not an accepted ledger record (the "missing selected ID" case).
5. `accepted_evidence_ids` is the union of the selected revisions' stored `evidence_ids`.
6. The spec's "`cooling_recovery.state`" does not exist in code. It is read as the W2 `COOLING_RESPONSE` capability state (`cold_site_reads.py:520-526`), which has exactly the LIMITED/CONTRADICTORY/UNAVAILABLE set.

## Held: Health read (`/cold/health`, `test_health_not_configured`). Not built. Question for the Architect

The card requires an "effective configured `asset_id`" per Health row from the "selected Foundation" and a NOT_CONFIGURED state from "a test-scoped selected Foundation without that asset". It does not say which read supplies it, so the following are open:
- **Source read.** `ColdReadService.basis_revisions_on` (`analytics/adapters/postgres_assessment_store.py:2443`) returns Foundation revision IDs and windows but not their content. The only cold Foundation projection is `sites/cold_foundation.py:260 cold_foundation_document`, which is reached through `cold_foundation_api.py:104` on a different store, not the snapshot connection. Which read, on the REPEATABLE READ connection, gives the Foundation content and asset IDs?
- **Per-row asset.** Should the generator come from `ColdStartPolicy.generator_asset_id` in the selected START result, or from Foundation components? Should the probe come from `ColdPolicy.probe_asset_id` or from room `probe_ids`? Should the compressor come from room `compressor_ids` (`cold_foundation.py:317`)?
- **Edge cases.** What applies with multiple rooms or compressors, or with no selected assessment? Is that NOT_CONFIGURED or UNKNOWN?
- **Payload keys.** What are the Health payload keys: a row list or keyed by asset kind?

## Test results (private DB `assetops_w501a_test`, dropped)

- C1 and adjacent tests: `pytest test_w501_cold_depth_router.py test_w501_cold_depth_postgres.py test_w204_cold_reads.py test_w203_cold_reads_postgres.py test_w202_cold_replay_postgres.py` → **51 passed** in 391 s.
- `tools/check-all.ps1`: **All 11 guards passed.**
- No frontend was touched, so tsc was not run.
- No processes are left running.

## Next

C1 per-unit review of the Cooling part (`703807cf`). The Architect rules on the Health questions above, then a follow-up C1 run adds `/cold/health` and `test_health_not_configured` before C2 starts.

## Run — C1 follow-up (Health + Q2/Q6/Q8–Q12), 2026-10-22

Commits `5d10d0e8` (build + tests) and `e7d8afad` (Health test reads the Foundation's two probe components). Files touched: only the card's list (`cold_depth.py`, `cold_depth_api.py`, `cold_site_reads.py`, `postgres_assessment_store.py`, the two C1 test files). `main.py` needed no change (`/health` is on the already-mounted depth router).

- Built: `ColdReadService.foundation_on` (Q7); pure `cold_depth.health_rows` + `GET /cold/health` with `{health:{foundation_revision_id, rows}}`; Cooling `policy_high_deg_c` (Q2); public `cold_site_reads.cooling_response_state` used by `_capabilities` and `cold_depth._recovery_state` (Q6, `ColdSiteReadService` no longer imported); `door_pairs` keeps the held OPEN over a zero-elapsed CLOSE, with the 3 named cases (Q8); replay `== "CURRENT"` (Q9); `links.health` GET 200 (Q11); vacuous `"36"` assertion removed and six-case Health check added (Q12). New tests: `test_cooling_response_state`, `test_health_rows`, `test_health_failed_start_and_probe`, `test_health_not_configured`.
- Focused command (card's, incl. `test_w301_provenance_dto_postgres.py`), private DB `assetops_w501c1f_test` on 127.0.0.1:55432: **62 passed, 0 failed, 0 skipped**, 820 s, on `e7d8afad`. DB dropped afterwards (0 remain). No processes left running.
- `tools/check-all.ps1`: **All 11 guards passed.** Full backend suite not run (per dispatch).

### Open question for the Architect (Q-H1)

The registered cold Foundation (`backend/tests/fixtures/w2/cold-lab-001.yaml`) declares **two** `TEMPERATURE_PROBE` components, `probe-1` (chamber) and `ambient-1`, each with an asset row. In `test_health_not_configured` the card says the first GET gives `asset_id`s "equal to the scoped asset rows of the Foundation's generator, compressor and probe codes". With no selection there is no policy, so the C1 Health table's rule ("else the only asset when `len(assets) == 1`; else null") gives a **null** Temperature sensing `asset_id`. The test currently asserts the table result (probe `asset_id` null, both probe assets listed in `assets`) and marks it as this open question. Should the table pick the chamber probe (for example by bound `chamber_temperature` role) or does null stand? In the backup-failed replay the excursion policy `probe_asset_id` resolves it to the chamber probe as specified.

## Run — Q13 `chamber_probe_asset_id`, 2026-10-22

`ColdReadService.foundation_on` returns `chamber_probe_asset_id` (single SIGNAL-edge-from-COLD_ROOM probe, else null); `health_rows` passes it as the third `asset_id` candidate; `test_health_not_configured` asserts `probe-1` and codes `['ambient-1','probe-1']`; `test_health_rows` has the three Q13 cases. Card's focused command: **62 passed**, 747 s, private DB `assetops_w501q13_test` (dropped, 0 remain). `tools/check-all.ps1`: all 11 guards passed. No processes left running.

## Run — C2, 2026-10-22 — PARTIAL (client built; page held on Architect questions Q-C2-1..4)

Built (only C2-listed files): `frontend/src/sites/ColdDepthClient.ts` (both DTO types; `getCooling`/`getHealth`; exact order-insensitive key sets at top, `window`, `selection`, `links`, `cooling`, point and context rows; C1 value sets incl. `cold-depth-1`, the five `STATES`, `LIMITED/CONTRADICTORY/UNKNOWN`, always-null time/duration fields, `CONTEXT_MISSING`, five labels in order, `Observed/Unknown`, `[]` when Unknown, integer `duration_seconds` only on observed door row; malformed 200 → `unavailable`; Health checks envelope only, C3 adds payload validation; `coolingCardLabels(policy_high_deg_c)`). `frontend/src/sites/__tests__/coldDepth.test.tsx::cooling_dto_and_labels` (client half, 4 tests): **4 passed**. `tsc -b`: clean. `tools/check-all.ps1`: **all 11 guards passed**. No backend run, no DB created, no process started. Captures not taken (page not built).

Not built, held: `ColdCooling.tsx`, the route/subtab/`coldUiHref` wiring, the nav guard + rail fixture change, the page tests (`cooling_state_copy`, page half of `cooling_dto_and_labels`) and the five captures. Questions (the spec does not decide; I did not choose):

- **Q-C2-1 (file list vs code).** The card says add required `cooling` to `ColdSiteRoutes` (`coldSiteViews.tsx:65-75`) with `routes.cooling = /sites/{code}/performance/cooling`. The only builder of that object is `coldSiteRoutes()` in `frontend/src/shell/coldSiteRoutes.tsx:21-33`, which is not in the C2 (or C3) list; a required key breaks `tsc` there. Rule: (a) add `shell/coldSiteRoutes.tsx` to C2's list for one line `cooling: sitePerformanceHref(siteId, "cooling")` (C3 then adds `health` the same way), or (b) something else?
- **Q-C2-2 (`Context normalization` table).** The ledger names the five rows but not the columns or cells. v69 uses `Factor` / `Evidence` / `Match` with a Matched/Limited/Unknown badge. Rule the headers, and the cell text: is the third column `state` verbatim (`Observed`/`Unknown`) under a `Match` heading (which may read as a matched comparison), and what does the Evidence cell show for the door row (duration format: `60 s`? `1 min`?), the power row (record IDs?), and an Unknown row?
- **Q-C2-3 (`Recovery curves` panel).** Rule 5 (`shell-overflow.ps1`) lets only the listed graphics modules draw svg; `assessmentGraphics.tsx` is not in C2's list and has no point/recovery chart, so this panel cannot draw a chart. Rule the non-chart rendering of `selected_points` (e.g. a `DataTable` with which columns; role words for `compressor_state`/`chamber_temperature`; time format), or allow an `assessmentGraphics.tsx` edit.
- **Q-C2-4 (non-current status).** "CURRENT leaves the recovery state label intact; pending/historical/stale show their state notice and suppress a current-positive comparison label." None of `Comparison limited|contradictory|unknown` is positive. Do PENDING_RECOMPUTE/HISTORICAL/STALE_SOURCE (and selection UNKNOWN) keep the matrix badge + `Confidence: …` + subtitle and add the state notice below the status bar, or is the badge replaced (by what text)?

Also noted for the C2 re-run (not questions): the rail-fixture re-anchor needs a new positive assertion in `navigation-truthfulness.ps1` (no existing check fails when a live cold branch is deleted), and the live 403 capture needs a served API whose disclosure check denies (or a foreign-Site request) — the producer for that is to be traced at build time.

## Run — C2 build (readiness pass 3 rulings), 2026-10-22

Commits `06c8c3cc` (page, wiring, guards, tests) and the evidence commit after it. Files are only the C2 list: `ColdDepthClient.ts`, `ColdCooling.tsx`, `coldDepth.test.tsx`, `App.tsx`, `SiteAnalyticsFrames.tsx`, `ColdAssessmentViews.tsx`, `coldSiteViews.tsx` (four `export`s, `cooling` route and `bases` entry), `shell/coldSiteRoutes.tsx`, `ui/V69Layout.tsx` (`cooling` description), and the two nav guard files. `operatorSiteRoutes.ts` needed no change, because `sitePerformanceHref(id, "cooling")` already matches.

- **Built.** `ColdCooling` sits inside `ColdPerformanceFrame` when `view === "cooling"`, which then makes no W2 reads.
  - Above the page: the selected window bar, then the `Cooling comparison` StatusBar (matrix badge, `Confidence:` badge, subtitle, `Inspect recovery basis →`). For non-CURRENT states an amber notice follows directly.
  - Body: four cards, a `panel-pair` with `Recovery curves` (DataTable Step/Time (UTC)/Evidence, or the empty sentence) and `Context normalization` (DataTable Factor/Evidence/Status), the bounded notice, and `Next best evidence`.
  - Refusal: the requested window bar (hidden on 422), then `Cold depth unavailable`, the exact `code message`, and a `Retry` button that re-reads the same URL.
  - Copy: the loading sentence is the ruled `<p className="prose">`; the unreachable and malformed sentences are as ruled.
- **Tests.** `coldDepth.test.tsx` passed 25/25 across `cooling_dto_and_labels` (client + page), `cooling_state_copy`, `cooling_panels` and `cooling_nav_and_routes`. `tsc -b` is clean.
  - The Cooling loading sentence is not in `test/settled.ts` `LOADING` (that file is not on the list), so the page tests settle with `settledScreen()` and then wait for that sentence to go.
- **Guards.** `tools/check-all.ps1` passed all 11 guards, including the two new rail fixtures.
  - Real-tree mutation, reverted with `git checkout`: removing `<ColdCooling` and removing `data-performance-subtab="cooling"` each gave exactly 1 failure, `The live cold Cooling subtab or page branch is missing`. The unmutated tree gave 0.
- **Captures.** In `.agent/W5-01a-C2-evidence/` (`capture.mjs`, `evidence.json`, 10 app PNGs + 2 mock PNGs) at 1440x1000/390x900. Method: the shared capture method on private `assetops_w501cap_test` (`ASSETOPS_TEST_TEMPLATE=0`), seeded by a throwaway seed test (`opened(case, chain)` + `run(built)`), API `lab_app` on 9791, Vite 6191, own headless Chrome on CDP 9792.
  - `limited`: backup-failed, W, CURRENT, clock `committed_watermark` 09:05:33.920042Z.
  - `empty`: missing-probe over the 2026-10-05 window, UNKNOWN. At W, missing-probe has two points, so it is not empty; this follows C1 `test_missing_probe_and_empty`.
  - `pending`: late-reading after `advance_late()`, PENDING_RECOMPUTE, watermark 09:11:10.304666Z.
  - `historical`: after the worker, `known_at=W0` 09:10:50.508596Z, HISTORICAL.
  - `refused`: `from` later than `to`, 422 `COLD_WINDOW_INVALID`.
  - Results: every capture has `scrollWidth <= clientWidth`, no block over the cooling caps, 0 ellipsized elements, and panel titles equal to the mock. The worst blocks are 1440 status 43 / cards 124 / panels 402 / notice 43 / next 191 / page 1263, and 390 status 99 / cards 261 / context 442 / notice 80 / next 208 / page 2025. The refusal block is 140 at both widths.
  - The 390 refused shot shows a tall dark band above the page (the shell header on a short page). It is outside C2's files; noted for review.
  - Cleanup: the DB was dropped (0 `w501` DBs remain), the seed file was deleted, and the API, Vite and Chrome were stopped.
- **One blocker (question, not chosen).** `frontend/src/sites/__tests__/coldRoutes.test.tsx:409-410` (W2-03 q3) still asserts `"Cooling · Not available yet"` in the cold Performance row and no `a[href*="cooling"]`. Those 2 cases now fail (the other 58 files in `src/shell`, `coldRoutes`, `coldSiteViews` and `coldFoundation` pass). The file is not on the C2 list. Proposed edit: drop the two Performance rows from that `it.each` (Cooling is covered by `coldDepth.test.tsx::cooling_nav_and_routes`), and narrow the `a[href*="cooling"]` assertion to `recommendation`. It needs a ruling to add the file.
- **Interpretation to confirm.** The ledger says heading `Cooling`. The page keeps the frame's v69 `SitePageHeader` (Site name h1, as the mock and the Temperature/Backup siblings do), with `Cooling` as the breadcrumb end and the current subtab.

### Run — C2 Q-C2-5 edit, 2026-10-22

Applied Q-C2-5 exactly in `frontend/src/sites/__tests__/coldRoutes.test.tsx`: removed the two Performance rows, made the link count `toHaveLength(0)` and narrowed the selector to `'a[href*="recommendation"]'`. Q-C2-6 and Q-C2-7 were confirmed, so nothing changed for them. The blocker above is closed.
- `coldRoutes`, `coldDepth`, `coldSiteViews`, `coldFoundation` and `src/shell` (60 files): **60 passed, 1372 tests**.
- `tsc -b` is clean, and `tools/check-all.ps1` passed **all 11 guards**.
- No process or DB was started in this run.
