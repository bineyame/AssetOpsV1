# W5-03b UI handoff: E4 EV Health and E6 EV Scenarios

Branch `task/W5-03b-ev-health-ui`, from `f8293bbe` (main with W5-03a, K2, K3 and E5). Builder: Claude Implementer, 2026-10-24. The pre-flight was already ruled; the build used `.agent/W5-03-build-spec.md` (E4/E6 cards and W5-03b pre-flight) plus `.agent/W5-03b-ui-preflight-rulings.md` 1-16. Ruling-vs-code points are in `.agent/W5-03b-ui-questions.md` (7 points). Each was built with the stated choice and needs Architect confirmation.

## Commits

| Commit | Unit |
| --- | --- |
| `9c9b67a4` | Backlog "W5-03b E5 Lows" in `backend/tests/test_w503_ev_scenarios_postgres.py`: removed the duplicate `accepted` key and the duplicate A6 and A3 blocks, plus the duplicate `limit=0` assertion. Foundation cases (c)/(d) now spy `foundation_revision_on` and assert the fallback resolves a real Foundation (`(c)` not one of the cited strangers; `(d)` the selected Foundation). The refused currency correction asserts the full ruled message. |
| `152ff839` | E4: `EvHealthDepth.tsx`, EV branch in `SiteHealthFrames.tsx` (before the S7 fallback; no Data sources panel, so the R60 extra panel is not present), `App.tsx` injects `evDepth`. `evDepthClient.ts` validates against the `EV_HEALTH_TUPLES` E1b tuple table. Both Foundation slots are live `Evidence › Data sources →` links. Registry node `I-W5-ev-health-ui` and row `(ev-health,1)` added; ledger `registry_dependencies` set. The stale clause is removed from `missing-claim-scan.mjs`. `settled.ts` gains the two new loading sentences. |
| `f69deb36` | E6: `evScenariosClient.ts`, `EvScenarios.tsx`, a live `Scenarios` subtab and view in `EvSiteViews.tsx` (local `DESCRIPTION.scenarios`; only this entry carries `scenario_at`), and the route in `evSiteRoutes.tsx`, `operatorSiteRoutes.ts` and `App.tsx`. Registry nodes `I-W5-ev-scenario-read/-ui`, row `(ev-scenarios,1)` and ledger set. Navigation guard: one EV `Scenarios` removed from `$expectedTabs` and a live `data-ev-subtab="scenarios"` + `<EvScenarios` assertion added. Rail fixtures: dropped tuple, dropped page branch, and an unavailable entry coming back. `evSiteMoneyRoutes.test.tsx`: the four unavailable assertions replaced with live ones. |
| `25320373` | E4 phone layout: source references on their own monospace lines (`evHealthDepth.css`), sticky Asset column with phone minimum widths, battery as the mock's plain large metric. |
| `a697415e` | E6: basis disclosure pinned to the phone table viewport (`evScenarios.css`), so long IDs break inside the visible scroller. |
| `3eb68c69` | E4: the Site-substrate guard rejected `sites/` importing `shell/operatorSiteRoutes`. `SiteFoundationFrame.tsx` now passes `evEvidenceHref` instead (questions point 7). |
| (this commit) | `.agent` evidence, register status, questions and this handoff. |

## Tests

- New: `evHealthDepth.test.tsx` (4 tests: `health_copy_and_sessions_destination`, `health_states_loading`, row order, client tuples) and `evScenarios.test.tsx` (3 tests: `routes_states_loading`, `row_disclosure_and_client`, `basis_disclosure_and_pending_historical`, which includes the ruling-16 earlier-`known_at` vector and the R98 cursor line).
- Changed: `evFoundation.test.tsx` (the two live links, with exact pathname, query and fragment across 6 address variants), `siteHealthBoundary.test.tsx` (an EV Site reads `/ev/health` with no S7 request and no Data sources panel; the exact source destination), `evSiteMoneyRoutes.test.tsx`.
- `expectV69Panels` and `expectPlantedPanelRejected` run on CURRENT Health and on CURRENT Scenarios (empty, authored, 50-row). Non-CURRENT variants assert notice order and the sole panel title directly (ruling 4). `panelStructure.ts` and `v69-panel-contracts.json` are not edited.

## Checks (final code `3eb68c69` unless noted)

- Focused Postgres, `-n 4`, on private `assetops_w503b_test` (dropped afterwards): `test_w503_ev_scenarios_postgres.py`, `test_w503_ev_depth_postgres.py`, `test_w503_ev_availability_postgres.py`, `test_w207_ev_site_reads_postgres.py`, `test_w207_ev_money_postgres.py`. Result: **77 passed**; JUnit tests=77, failures 0, errors 0, skipped 0; 652 s; keep-awake held and stopped by PID. Backend code did not change after this run.
- vitest full `--minWorkers=1 --maxWorkers=2`: **122 files, 2845 passed** at `a697415e` (496 s) and again at the final `3eb68c69` (249 s).
- `tsc --noEmit` clean; `vite build` ok; `check_v69_dependency_registry.cjs` valid (271 nodes, 64 linked pilot panels); `test_missing_claim_scan.mjs` 24/24.
- `check-all.ps1` at `3eb68c69`: **all 11 guards passed**. Navigation truthfulness runs the new rail fixtures, so each mutation is proven to fail. The Site-substrate guard proved itself by rejecting the first E4 import (Q7).
- Environment note: the first full vitest run had 551 failures (`Invalid Chai property: toHaveTextContent`). The cause was a `node_modules` junction to the main checkout, which loads two instances of vitest. The same failures occur on base `f8293bbe` with that junction. Replaced with a real `npm ci` install (untracked, gitignored); the next run was green. A `.venv` junction to the main checkout's venv remains (untracked) for the guard Python. Backend runs set `PYTHONPATH` to this worktree's packages, because the venv's editable install points at the main checkout.

## Captures: `.agent/W5-03b-ui-evidence/` (`capture.mjs`, `evidence.json`, 22 app PNGs + 4 mock PNGs)

States captured at 1440 and 390: `ev-health-fault`, `-unknown`, `-pending`, `-historical`, `-refused`; `ev-scenarios-empty`, `-authored`, `-historical`, `-pending`, `-refused`, `-pending-expanded` (the basis disclosure capture). Every pair: read_ok, no document horizontal overflow, panel titles equal to the mock (refusals excluded), 0 ellipsized, 0 overflowing cells, no cap exceeded.

Measured heights:

- Health, three-row fixture: panel 324 / 409 (cap 410/540), cards 135 / 307 (cap 200/380), page 1000 / 1150 at 1440/390.
- Health with R15: page 1195 at 390 (cap 1550).
- Scenarios one-row panel: 217 / 214 (cap 430/560). Empty panel: 305 / 345. Closing notice: 66 / 102 (cap 90/135).
- Expanded basis scroller: 360 / ≤360. Refusal: 140.

Producers:

- A throwaway seed test (deleted, never committed) drove the `ev_depth_cases.py` `Chain` and the E5 in-process POST (`scenarios_client`) on private `assetops_w503bcap_test` with `ASSETOPS_TEST_TEMPLATE=0`. Each state was reseeded fresh.
- Served by `lab_app` on port 9791, Vite on 6191, headless Chrome CDP on 9792.
- Clocks are the returned watermarks: 09:00, and 09:05 after the late record. Health historical uses the saved first watermark, `known_at` 09:00.
- Scenarios historical: root revision, saved `scenario_at` `2026-10-23T22:42:58.963238Z`, then correction. The read returns r1 `HISTORICAL`.
- Scenarios pending: authored on `complete`, then the E5 `late_import` at 09:05 (the `late-record` case has no complete session to author; P-E5-5).

Judgment calls:

- `ev-health-fault` uses the `interrupted` case (questions point 1).
- The authored-expanded capture was replaced by `pending-expanded`, which shows the same authored row, after the disclosure layout fix. Unexpanded captures predate `a697415e`/`3eb68c69`; those commits do not affect what they show.

Cleanup: capture DB dropped. My API was stopped by recorded PID; Vite by its listener PID 17468 and its cmd parent 14660. Chrome was killed by each capture run.

## Judgment calls (all also in the questions file or code comments)

1. Fault fixture `interrupted` instead of `fault` (Q1).
2. App prop `evScenarioList`, because `evScenarios` already exists (Q2).
3. `Sessions →` as ruled, against the mock's `View detail →` (Q3).
4. Literal `{n} … records` plurals (Q4).
5. Session reference placed in `Supported assessment` (Q5).
6. Shared Health subtitle kept (Q6).
7. Shell passes the EV Evidence path (Q7).
8. Battery card is a plain (non-assessment) gray metric, matching the mock's battery treatment, with value `Unknown`.
9. The Health empty sentence shows when there are zero `CONNECTOR` rows. The table is omitted only when no table row exists.
10. `ev-health` registry row reason, which the spec did not give: "Selected session and fault observations do not establish physical charger condition or a fault's cause."
11. E6 reuses the `coldScenarios.css` classes (same primitives; no shared component extracted and `ColdScenarios.tsx` untouched), plus an EV-only `evScenarios.css` for the phone pin.
12. `Kind`, assumption keys, window, cutoff and classification in the basis disclosure are printed verbatim in source-reference spans.
13. `mock-departure-register.md`: R16, R27, R56-R59 and R95-R98 status set to "built: W5-03b E4/E6, review pending". R15 is left as is because it is shared with E2/E3.

## Shared plumbing touched

- `main.py`, composition, seed tools, `conftest`, migrations: **not touched**.
- `tools/checks`: `missing-claim-scan.mjs`, `navigation-truthfulness.ps1`, `navigation-rail-fixtures.ps1`, all as ruled.
- Also shared: `frontend/src/test/settled.ts` (loading sentences) and `frontend/src/shell/SiteFoundationFrame.tsx` (Q7).

## Next

Independent E4 review, then E6 review (ruled order). User review: W5 UI follows the walkthrough-after-W6 rule; merge on review ACCEPT unless the Architect rules otherwise on the questions file.

## Fix round (E4 REVISE, E6 REVISE; rulings 17-29)

Branch `task/W5-03b-ui-fix`. Code commits: `8c204e27` (product, tests, registry), `4f661415` + `776140b0` (capture tool). Status: code done; DB, full-suite, build and capture batch pending the owner signal (see "Batch" below once filled).

| Finding / ruling | Where | Commit |
| --- | --- | --- |
| R17 `interrupted` fixture + non-vacuous E1b assertion | `backend/tests/test_w503_ev_depth_postgres.py`: `test_energy_health_selected_snapshot` keeps `fault` as its honest all-UNKNOWN vector (explicit UNKNOWN, no evidence); new `test_health_interrupted_selected_fault` asserts exactly one `NEEDS_INVESTIGATION` connector (c1) with one fault evidence ID equal to c1's session fault, and c2 `UNKNOWN`. Postgres run pending. Capture producer for the three-row state is `settled(chain,"interrupted")` (recapture pending). | 8c204e27 |
| R18 `evScenarioList` prop | Confirmed, no change | n/a |
| R19 `View detail →` | `EvHealthDepth.tsx`; `evHealthDepth.test.tsx` asserts label and destination | 8c204e27 |
| R20 singular literals | `faultNote(1)`, `1 record` in `EvScenarios.tsx`; tests for 0/1/2 and a one-record disclosure | 8c204e27 |
| R21 session placement | Confirmed; test asserts the session reference and `Open Sessions →` are in the second cell, not the first | 8c204e27 |
| R22/R103 subtitle label | MOCK DEVIATION (D4) R103 comment in `EvHealthDepth.tsx`; `siteHealthBoundary.test.tsx` asserts the literal and absence of the mock line; register row R103 status | 8c204e27 + register |
| R23 Foundation source link | Confirmed, no change | n/a |
| R24 / E4-M1 phone table | `evHealthDepth.css` per ruling (min-widths removed, fixed layout 27/36.5/36.5, padding, 9px header); capture records `tableScrolls` and `hidden_columns` | 8c204e27 |
| R25 / E4-M2 sticky header | `primitives.css` header grey `#f8fafd` incl. first cell; new `ui/__tests__/DataTable.test.tsx` (jsdom cascade over the real CSS; sticky 1440/390 and non-sticky). Mutation proof: removing the rule failed both sticky tests. Browser-computed values come from the capture (`headerBackgrounds`, `header_grey`). | 8c204e27 |
| R26 / E4-L1 registry | Pilot registry JSON: `I-W5-ev-health-ui.requires`, `(ev-health,1).reason`, "preserved gateway panel" removed from the E4 and E6 UI nodes. Spec E4/E6 nodes already carried the corrected text. | 8c204e27 |
| R27 / E4-L2 Unknown tone | `evHealthDepth.css` scoped selector | 8c204e27 |
| R28 / E6-L1 basis scroller | `evScenarios.css` `max-height: 360px` at <=640px | 8c204e27 |
| R29 / E6-H1 closing notice | `evScenarios.css` flex rule and `p` margin | 8c204e27 |
| E4-L3 tuple parity | `evHealthDepth.test.tsx`: independent literals checked against `ev_depth.py` source text and `EV_HEALTH_TUPLES`. Mutation proof: altering a backend literal failed it. | 8c204e27 |
| E6-L2 | `evScenarios.test.tsx`: previous sibling matches `.data-table__scroll` and holds `table.data-table`, no fallback | 8c204e27 |
| S-L1 | `capture.mjs`: `.data-table__scroll` metric with real widths, `table_scrolls_nonempty`, header backgrounds, basis max-height, per-pair revision, a non-SHA revision is refused | 4f661415, 776140b0 |
| S-L2 | `test_w503_ev_scenarios_postgres.py`: one duplicate `limit=0` assertion deleted | 8c204e27 |

Verified so far (DB-free): `tsc --noEmit` clean; focused vitest `DataTable`, `evHealthDepth`, `evScenarios`, `siteHealthBoundary` passing; registry JSON parses.
