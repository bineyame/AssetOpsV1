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

## Run — C3, 2026-10-22 — PARTIAL (body built; frame composition held on Q-C3-1..4)

Commit `a374e2d8`. Files are only from the C3 list: `ColdDepthClient.ts`, new `ColdHealthDepth.tsx`, new `__tests__/coldHealthDepth.test.tsx`, `shell/coldSiteRoutes.tsx`, `coldSiteViews.tsx`, `ColdFoundationViews.tsx`, `v69-dependency-registry-pilot.json`, `v69-screen-ledger.json`.

- **Built.**
  - Client: `isColdHealthRead` validates exact `health`/row/asset key sets, the three kinds in order, each row's `(kind, condition_state, observation, limitation)` against `HEALTH_ROW_LITERALS` (the C1 table) and the kind's `next_evidence`.
  - `ColdHealthDepth`: `SelectedWindowBar`, the non-CURRENT state notice, three cards (label linked via `coldUiHref(row.link)`, value by state, note = `limitation`, amber only for `Needs attention` as the mock), `Condition and evidence` (`DataTable`, Asset cell rule, empty sentence rule), then the amber condition notice. The condition sentence is the single constant `HEALTH_CONDITION_NOTICE` in `ColdHealthDepth.tsx`. Loading, refusal (`RequestedWindowBar` + code/message + `Retry`), unreachable and malformed copy as ruled; constants reused from `ColdCooling.tsx`.
  - `health: siteHealthHref(siteId)` in `coldSiteRoutes`, `health: string` in `ColdSiteRoutes`, `health: routes.health` in `coldUiHref`. `ColdFoundationViews.tsx:646` link is `{healthHref}#site-health-sources-heading`.
  - Registry: the two `I-W5-cold-depth-*` nodes (after `D-cold-domain`), the four panel rows (appended), and `registry_dependencies` on the `cooling` and `cold-health` ledger screens, all exactly as the spec JSON. `check_v69_dependency_registry.cjs` passes.
- **Tests.** `coldHealthDepth.test.tsx` (`health_dto_rendering`, `condition_matrix`, `health_states_and_loading`): **15 passed**. `tsc -b` clean. Adjacent `coldDepth`, `coldRoutes`, `coldSiteViews`, `coldFoundation`, `siteHealthBoundary`, `src/shell` (61 files): **1400 passed, 1 failed** — the expected Q-C3-3 case below. check-all: see the result line at the end of this entry.
- **Not built, held:** `SiteHealthFrames.tsx`/`App.tsx` COLDCHAIN composition, the `siteHealthBoundary.test.tsx`/`coldSiteViews.test.tsx` composition and link tests, and the five captures. No DB, server or Chrome was started.

Questions (the spec does not decide; I did not choose):

- **Q-C3-1 (file list vs code).** The card keeps "the shared S7 `Data sources · data quality, not equipment condition` panel below `Condition and evidence` using the existing `SiteHealth.tsx` gateway read", with the condition notice "directly below `Condition and evidence` (above the S7 Data sources panel)". In code, that panel cannot be rendered alone: `SiteHealth` (`sites/SiteHealth.tsx:300-345`) renders, in one component, the S7 `ConditionStrip` (battery status line), the `Physical asset condition` panel (battery entry read), the Data sources panel (`SourcesBody` is private) and a blue S7 notice. `SiteHealth.tsx` is not on C3's list. Rule: (a) add `SiteHealth.tsx` to C3's list to export the Data sources panel alone (same heading ID `site-health-sources-heading`, same `getSourceHealth` read, same refusal), which the cold frame renders after the condition notice; and say whether the cold page keeps or drops the S7 status strip, the `Physical asset condition` battery panel and the blue S7 notice; or (b) render the whole `SiteHealth` below the condition notice (then the notice is not directly above the Data sources panel, and the battery strip/panel appear on the cold page); or (c) something else.
- **Q-C3-2 (heading).** The ledger says heading `Health`. The existing `SiteHealthFrame` uses `SitePageHeader` (Site name h1, as the v6.9 `cold-health` screen title), with `Health` as the breadcrumb end and current tab. Confirm as Q-C2-6 did for Cooling (no change), or rule a `Health` h1.
- **Q-C3-3 (C2 test vs C3 card).** `frontend/src/sites/__tests__/coldDepth.test.tsx:454-459` (C2 `cooling_nav_and_routes`) asserts `coldUiHref(.../cold/health?…)` is null "until C3". C3's `health: routes.health` makes it `/sites/COLD-001/health?…`, so it now fails. The file is not on C3's list. Proposed edit: change line 459 to expect `` `/sites/${SITE_CODE}/health?${Q}` `` and drop "health stays unmapped until C3" from the test name. Needs a ruling to add the file.
- **Q-C3-4 (link test location).** The `Health › Data sources →` link lives in the cold Foundation readiness view, whose fixtures and App render are in `coldFoundation.test.tsx` (not on C3's list). `coldSiteViews.test.tsx` (on the list) renders none of the Foundation. Rule: add `coldFoundation.test.tsx` to the list for one href assertion (`/sites/{code}/health#site-health-sources-heading`), or build that render in `coldSiteViews.test.tsx`.
- **check-all** (on `a374e2d8`): **All 11 guards passed.**

### Run — C2 rebuild delta (Codex retrospective Q-C2-2/Q-C2-3), 2026-10-22

Commits `b84b9373` (delta) and `f6350739` (390 cap fix), plus the evidence commit after them. Files touched are only the C2 files the delta names: `ColdCooling.tsx`, new `coldDepthGraphics.tsx`, `ui/primitives.css`, `tools/checks/shell-overflow.ps1` and `coldDepth.test.tsx`. No C3 file was touched.
- **Q-C2-2.** The `Context normalization` third heading is `Match`. Every cell is a neutral `Not established` badge (`CONTEXT_MISSING`), and the Evidence column is unchanged. No `Matched` is rendered.
- **Q-C2-3.** `Recovery curves` renders `CoolingObservationGraphic` (`coldDepthGraphics.tsx`).
  - Lanes are `Compressor running` and `Chamber temperature`, across the selected window with 15-min UTC ticks. Each selected point is an unconnected mark labelled `HH:MM:SS` with a `<title>`. There is no °C axis, no path and no curve. With no points the frame is drawn empty.
  - Below the graphic are `No accepted recovery sequence in this window.` and then the selected-point `DataTable` (only when points exist).
  - Rule 5 registers the module as the svg owner. It must render `.cold-depth-graphic__scroll`, and that selector must declare `overflow-x: auto` in `primitives.css` (check 1f). The existing checks are kept.
  - Non-vacuity, each mutation reverted: dropping `overflow-x`, renaming the region class, or adding an `<svg>` in `ColdCooling.tsx` each gave exactly 1 failure; the clean tree gave 0.
- **390 cap fix.** At 390 the Match badge (`white-space: nowrap`) squeezed the Evidence column, and Context normalization measured 513 > 500 in empty/pending/historical. A scoped `@media (max-width: 480px) .cold-cooling-context .data-table .badge { white-space: normal; }` fixed it, using the panel `className="cold-cooling-context"`.
- **Stale assertion updated.** `coldDepth.test.tsx::cooling_nav_and_routes` expected `/cold/health` to be unmapped, but C3 (on this branch) now maps it to `/sites/{code}/health`. I updated that assertion.
- **Tests.**
  - `coldDepth.test.tsx`: 25/25 passed. `cooling_panels` asserts the single svg inside its region, the two lane labels, the mark label and title, no path/polyline/polygon, no °C/36/42/+17%, the `Match` heading, five `Not established` cells, no `Matched`, and the empty-frame case.
  - Adjacent tests (`coldRoutes`, `coldDepth`, `coldSiteViews`, `coldFoundation`, `coldHealthDepth`, `siteHealthBoundary`, `src/shell`): **62 files, 1416 tests passed**.
  - `tsc -b` is clean. `tools/check-all.ps1` passed **all 11 guards** on the final code.
- **Recaptures** at `f6350739`, same method (private `assetops_w501cap_test`, throwaway seed, `lab_app` 9791, Vite 6191, CDP 9792): `cooling-limited` (CURRENT, watermark 10:35:02.861732Z), `cooling-empty` (UNKNOWN, 2026-10-05 window), `cooling-pending` (PENDING_RECOMPUTE, 10:38:58.734216Z) and `cooling-historical` (`known_at=W0` 10:38:48.674434Z) at 1440/390. `cooling-refused` is unaffected and kept.
  - Every capture: no horizontal overflow, panel titles equal to the mock, 0 ellipsized, no block over the caps.
  - Recovery curves is 417 at 1440 and 464 at 390. Context normalization is at most 478 at 390 (cap 500). Page height is at most 1278 at 1440 and 2222 at 390.
  - At 390 the graphic's 480 px minimum scrolls inside its region.
  - Against the v69 `cooling` mock: same panel slot and order, graphic at the panel top, then the source table. The mock's two °C curves and its legend are deliberately absent.
  - Cleanup: the DB was dropped (0 `w501` DBs remain), the seed file was removed, and the API, Vite and Chrome were stopped.

## Run — C3 completion (rulings Q-C3-1..4), 2026-10-22 — BUILT; one cap question (Q-C3-5)

Commit `56231727` (code) plus the evidence commit after it. Files are only the C3 list as amended by the rulings.
- **Q-C3-1.** `SiteHealth.tsx` exports `SiteHealthSources({siteId, client, selectedGateway})`. It uses the same `health:${siteId}` read, heading ID, description, `SourcesBody` and `HealthGap`, and shows `Loading the site's gateway contact.` inside the panel. A private `SourcesPanel` is shared with `SiteHealth`, so non-cold rendering is unchanged.
- **Cold frame.** `SiteHealthFrames.tsx` routes COLDCHAIN only to `ColdHealthDepth` followed by `SiteHealthSources`, inside `HealthLinksContext`. `SiteHealth` is not mounted there. `App.tsx` passes `coldDepth`.
- **Q-C3-2.** No change: the Site-name h1 stays.
- **Q-C3-3.** `coldDepth.test.tsx`: the test is renamed to the literal, and the assertion already matched. This also closes C2b review Low 1.
- **Q-C3-4.** `coldFoundation.test.tsx`: the literal test was added inside the "cold Foundation routes" suite.
- **Registry.** The `cooling:1` and `cooling:2` reasons now describe the selected unconnected marks with no comparable curve, and the `Not established` Match cells (C2b review residual). These are my words; the review gave no literal.
- **New and updated tests.**
  - `coldHealthDepth.test.tsx` adds the composed App-route test. It checks the Site-name h1, the Health tab, and the order cards → `Condition and evidence` → condition notice → Data sources. It also checks there is no battery read, no `Physical asset condition`, no blue notice and no `[data-health-site]`.
  - `siteHealthBoundary.test.tsx`: a mini-grid Site keeps the S7 strip, battery panel, sources panel and blue notice, and never calls cold depth.
  - `coldSiteViews.test.tsx`: `routes.health` and the `/cold/health` mapping.
- **Results.** Focused plus adjacent (`coldHealthDepth`, `coldDepth`, `coldRoutes`, `coldSiteViews`, `coldFoundation`, `siteHealthBoundary`, `src/shell`): **62 files, 1419 tests passed**. `tsc -b` is clean. The check-all result is at the end of this entry.
- **Captures.** In `.agent/W5-01a-C3-evidence/` (`capture.mjs`, `evidence.json`, 10 app PNGs + 2 mock PNGs, 1440x1000/390x900).
  - Method: private `assetops_w501c3cap_test` (`ASSETOPS_TEST_TEMPLATE=0`), a throwaway seed test (`opened(case, chain)` + `run(built)`), `lab_app` on 9791, Vite 6191, own headless Chrome (CDP 9801+). Each clock is the returned `committed_watermark`.
  - `failed-start`: backup-failed, CURRENT, 11:41:01.762054Z. Rows are NEEDS_INVESTIGATION / UNKNOWN / LIMITED.
  - `unknown`: backup-failed on the 2026-10-05 window, UNKNOWN; all rows UNKNOWN with 0 IDs, and the empty sentence is shown.
  - `pending`: late-reading after `advance_late()`, PENDING_RECOMPUTE, 11:36:22.429718Z (W0 11:36:02.149606Z).
  - `historical`: a second late-reading sequence, `known_at=W0` 11:42:50.572554Z, HISTORICAL. Pending and historical came from two separate seeds; each followed the ordered sequence with its own W0.
  - `refused`: `from>to`, 422 `COLD_WINDOW_INVALID`, refusal 140.
  - Every capture: no horizontal overflow, 0 ellipsized. Panel titles equal the mock's once the labelled Data sources deviation is excluded, and Data sources is the last panel. Page height is at most 1084/1975 (caps 1900/2350); cards 108/293; Data sources 299/505 (caps 700/800); condition notice 43/80.
  - Against the v69 `cold-health` mock: same cards in the same order, then `Condition and evidence` with the same columns. Differences:
    - The mock's Backup card has an amber top border with a body-colour value and `View detail →`. The app colours the value amber and links the card label (the coldSiteViews precedent).
    - The mock's Unknown/Limited values are large; the app uses the `word` size.
  - **Over cap:** `Condition and evidence` at 390 is **556** (failed-start, pending, historical) and **591** (unknown), against the 430 cap. 1440 is 251/285 (cap 330).
- **Cleanup.** The DB was dropped (0 `w501` DBs remain), the seed file was deleted, and the API, Vite and Chrome were stopped (no listeners on 9791/6191/98xx).

### Q-C3-5 (cap breach, not chosen)

At 390 the `Asset` cell (C3 Asset cell rule: name + full asset UUID) is the narrow first column of a three-column `DataTable`. Each UUID wraps at its hyphens into 4 lines, so each row is about 130 px (see `cold-health-unknown-390-app.png`). The spec's 390 table rule ("scrolls within its panel with sticky first column; UUIDs break at character boundaries") needs CSS. `primitives.css` is not on C3's list, and no existing class gives a sticky first column or no-wrap cells. Rule:
- (a) add `frontend/src/ui/primitives.css` to C3's list for a scoped rule on a `cold-health-condition` panel class: at most 480 px, no-wrap Asset cell and sticky first column, so the table scrolls horizontally (expected about 300 px); or
- (b) raise the 390 condition cap to the measured 591 (+ margin); or
- (c) something else, such as the record ID on its own line in a smaller monospace style.
- **check-all** (on `56231727`): **All 11 guards passed.**

## Run — C3 rulings Q-C3-5 and mock differences, 2026-10-22 — BUILT

Commit `a9769dd9` (code) plus the evidence commit after it. Files: `ColdHealthDepth.tsx`, `ui/V69Layout.tsx`, `ui/primitives.css` and `coldHealthDepth.test.tsx`, all as the ruling names.
- **Q-C3-5.** The `Condition and evidence` Panel has `className="cold-health-condition"`. The ruling's scoped CSS was added verbatim to `primitives.css`: at ≤480 px, `min-width: 840px`, a sticky Asset column of at least 240 px, and the full ID kept on one line at 10px.
- **Cards.** All three cards use `assessment`, with amber tone only for `NEEDS_INVESTIGATION`, and there is no `word` prop. Labels are plain. `MetricCard` has a new optional `link` prop, rendered as `.v69-metric__link` (10px, top margin 10px); the card passes `View detail →` from `coldUiHref`, and a null destination gives no link.
- **Registry.** The `cooling:1` and `cooling:2` reasons already equal the Architect literals, so they are unchanged.
- **Tests.**
  - `coldHealthDepth.test.tsx` now also asserts: the panel class; the full ID in `[data-health-asset-id]`; the label is not a link; the detail link and its mapped href; no link for a null destination; `v69-metric--assessment` on all three cards with no size override.
  - Results: 16/16 focused. Adjacent (`coldHealthDepth`, `coldDepth`, `coldRoutes`, `coldSiteViews`, `coldFoundation`, `siteHealthBoundary`, `src/shell`): **62 files, 1419 passed**. `tsc -b` is clean.
  - `tools/check-all.ps1`: **all 11 guards passed** on `a9769dd9`.
- **Recaptures** of all five states at 1440/390, same method (private `assetops_w501c3cap_test`, throwaway seed, `lab_app` 9791, Vite 6191, own Chrome on CDP 9801+). `capture.mjs` now also measures every asset ID: its line count, whether it sits inside its cell, whether it is clipped, and the cell position.
  - Clocks: `failed-start` CURRENT, watermark 12:03:46.600618Z; `unknown` UNKNOWN, on the 2026-10-05 window; `pending` PENDING_RECOMPUTE, 12:08:34.644604Z; `historical` HISTORICAL with `known_at=W0` 12:08:07.635852Z. `refused` is 422 `COLD_WINDOW_INVALID`; it was re-shot after a cold Vite first load gave an unready frame.
  - Every capture has no document overflow and 0 ellipsized. Panel titles equal the mock's apart from the labelled Data sources deviation, which is the last panel.
  - **Condition and evidence:** 251/285 at 1440 (cap 330) and **311/345 at 390** (cap 430). Every ID is on 1 line, inside its cell and not clipped; at 390 the Asset cell is `sticky`.
  - Other blocks: cards 135 at 1440 and at most 347 at 390 (caps 200/430). Data sources 299/505 (caps 700/800). Page at most 1145/1784 (caps 1900/2350). Refusal 140.
  - Against the v69 `cold-health` mock: same cards in the same order, with an amber top border only on the Backup card, body-colour 17 px values, plain labels and `View detail →`, then `Condition and evidence` with the same three columns. The remaining differences are the labelled ones: the third probe row, the asset ID line, the condition notice, the currentness notice and the Data sources panel.
- **Cleanup.** The DB was dropped (0 `w501` DBs remain), the seed file was deleted, and the API, Vite and Chrome were stopped (no listeners).
