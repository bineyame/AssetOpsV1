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
