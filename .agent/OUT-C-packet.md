# OUT-C review packet: early warnings, first set

Task: `tasks/OUT-C-early-warnings.md`. Contract: `AssetOpsV1-plan2/.agent/build-sheet-OUT-C.md` (wins over the sprint spec).
Branch `task/OUT-C-early-warnings`, worktree `AssetOpsV1-outC`, cut from main `e8cf8a36`. Unit history: `.agent/OUT-C-phase-handoff.md`.
U1 per-unit review: ACCEPT (`AssetOpsV1-plan2/.agent/OUT-C1-review.md`, L1-L3 done). U2 per-unit review: ACCEPT, with L1/L2 test gaps closed here.

## Outcome delivered

- Backend (U1-U4): pure producer `outcomes/warnings.py` (`early-warnings/1`, seven rules, never money); catalogue/2 measures MG-4 and
  CC-3; visits read by occurrence over 60 days (`site_outcomes/visits.py`, three recorded-time windows); board and estate summary
  carry `warnings[]` and `categories[].warning_count`; w502 `positive` authors repeat visits and plans (GreenHarvest Cost row).
- Frontend (U5): `sites/EarlyWarnings.tsx` `EarlyWarningList` (mock `outcomes.js:137-140` structure and classes, explainer dialog
  sharing the board's `ExplainerDialog`), `SiteEarlyWarnings` (board read) and `miniBoardDay`; estate Findings lenses (All/Cost/Risks/
  Opportunities filter) under the table in the panel; three Site Findings lists under the list in the panel (`showSite` false);
  Portfolio list under the ranked table (`max` 4), pulse "{n} warnings not yet priced" (Unknown until loaded, no icon), Protect card
  detail with the warning clause (`protectDetailText`). `estate/useOutcomeSummary.ts` shared hook.
- Frontend (U6): Maintenance card 4 "Repeat visits without a result" (`data-global-work-card="repeat_visits"`) replaces "Repeat
  findings", summary over the covering UTC days; request-page amber notice from the Site board (no window) when the REPEATED warning's
  `href` path ends with the case id.
- Register: R560-R571 added; R541 resolved; notes on R08, R10, R358.

## Files materially changed (U5/U6 and closeout)

`frontend/src/sites/{EarlyWarnings.tsx,OutcomeBoard.tsx,outcomeBoardClient.ts,outcomes.css,SiteFindingIndex.tsx,ColdAssessmentViews.tsx,EvFindingIndex.tsx}`,
`frontend/src/estate/{estateClient.ts,findingIndex.tsx,EstatePortfolio.tsx,PortfolioOutcomes.tsx,useOutcomeSummary.ts}`,
`frontend/src/shell/SiteAnalyticsFrames.tsx`, `frontend/src/App.tsx`, `frontend/src/work/{GlobalMaintenance.tsx,WorkRequestOverview.tsx}`,
`frontend/src/test/outcomeBoardFixture.ts`, tests listed below, `backend/tests/test_out_c4_mini_ev.py`, `.agent/mock-departure-register.md`.
U1-U4 files: see the handoff.

Existing tests changed: `globalMaintenance.test.tsx` card-4 label and note now the replacement card's (sheet U6: retired card);
`outcomeBoardFixture.ts` `policy_versions.warnings` "early-warnings/1". Extended (helpers gained an optional client argument, no
assertion removed): `estatePortfolio`, `estateRoots`, `s404SiteFindingIndex`, `coldFindingIndex`, `evFindingIndex`,
`workRequestOverview`. New: `sites/__tests__/earlyWarnings.test.tsx`.

## Acceptance (§7)

1. Never-money for every rule, injected double fails: met in U1 (`test_out_c1_never_money.py`); frontend money regex in every list test.
2. Positive and negative per rule; 4 OPEN + 3 COMPLETED gives one warning: met in U1 (`test_out_c_rules.py`).
3. w502 `positive` board: met by `test_out_c3_repeat_visits_postgres.py` (U3). Portfolio matrix cell: P-C1 failed, so vitest only,
   carried to the combined dataset.
4. w504 `positive` no PEAK; connector warning iff unavailable time: met by `test_out_c4_ev_warnings_postgres.py` (U4).
5. Estate Findings lenses: met in vitest (`estateRoots` "OUT-C U5": All 4, Cost 1, Risks 3, Opportunities none). Real data: not run (P-C1).
6. Pulse incl. 0, singular and Unknown; Protect clauses; w1 scan and money regex: met in vitest (`estatePortfolio` "OUT-C U5").
7. Maintenance card = 1: vitest only (P-C1). "Third visit" notice: met in vitest; the capture on the latest cold request is pending.
8. Full backend run, full vitest: NOT RUN (await the coordinator's go). check-all: 11/11 pass on `86fc3e59`.

## Checks run

- `npx tsc --noEmit`: clean. vitest on touched files (11 files): all pass (`earlyWarnings` 7, `estatePortfolio` 34, `estateRoots` 15,
  `s404` 42, `coldFindingIndex` 11, `evFindingIndex` 10, `globalMaintenance`, `workRequestOverview`, `outcomeBoard`, `miniDecisions`,
  `w301EstateShellRoutes`). `vitest related` could not run: it tries to parse a `.py` file in the import graph, so the test files were named directly.
- Backend `test_out_c4_mini_ev.py` 10 pass. Proofs (each mutation reverted with `git checkout`): `ev.py:98` `hi`->`lo` fails
  `test_ev_visit_windows_are_anchored_at_the_window_end`; `mini.py:257` `end`->`start` fails
  `test_mini_visit_windows_are_anchored_at_the_board_day_end`; dropping `dispatch is not None` from MG-4 (`mini.py:269`) fails the
  existing `test_failed_dispatch_leaves_mg4_unknown` (L2: already covered, no new test needed). Frontend: removing the estate list
  fails `estateRoots` "eachLensLists...".
- `tools\check-all.ps1` (ASSETOPS_GUARD_PYTHON = plan2 venv): All 11 guards passed. `check-architecture.ps1` and
  `check-agent-workflow.ps1` run directly: passed. No `-ExecutionPolicy` used.
- New strings scanned against `terms` + `w1.terms` + `w1.codes`: 0 hits; tests run `scanProductVocabulary(..., {set: "w1"})` on
  the list, the card and the notice. No new `<svg>`, no `variant`, no frontend "Not available yet" literal (diff grep).
- Not run (need the coordinator's go): full vitest, `run-backend-suite-in-container.ps1 -Tier all`, captures at 1440/390 vs v70
  (GreenHarvest Overview with the Cost row open, its Findings list, the latest request page, Depot Overview on w504). Layout
  evidence: not run; the 390 px reflow of `.oc-warn` (`minmax(min(260px,100%),1fr)`, `overflow-wrap: anywhere`) is unverified.

## Known deviations

- No OUT-C task file existed; `tasks/OUT-C-early-warnings.md` was created as a pointer to the sheet so it can carry `Status`.
- WR notice reads `body.selected.site_code` (the sheet says `body.site_code`; the wire nests it under `selected`).
- The list's category text is the backend category label ("Optimize cost and efficiency"). This matches the mock: its `CATN` uses the full category names (`outcomes.js:11-16`). (Corrected in the final-review fix round, L4; the earlier "short names" claim was wrong.)
- Maintenance "window over 31 days": the page parser already refuses such a window, so that branch is defensive and proven only
  by the `coveringUtcDays` unit test.
- R358 row describes Incidents; a Maintenance note ("cards 2-3", R571) was appended instead of rewriting the row.
- The mini Site Findings list renders only for MINIGRID Sites in the mini index branch.
- From U4 (handoff): a connector label already starting with "Connector" is not prefixed again.

## Residual risk

- Estate surfaces have no real-data proof (P-C1 failed: the whole-day estate summary on w502 shows no REPEATED warning). P-C1 is structural, not a data gap: the cold read selects only a run whose window covers the request, so a combined dataset alone will not fix it. It is R575 (open), owned by the follow-up slice (Rulings C final review, P-C1 option A).
- Full suites not yet run on this head; the Kobo b4 Postgres tests after the U4 MG-4 change are covered only by the U4 run.

## User-review focus

Placement of the lists under the tables (estate, Site, Portfolio), the pulse wording, the Maintenance card and the request notice.
USER_REVIEW_REQUIRED: false for merge; the owner sees it in the post-sprint walkthrough.

## Acceptance #8 (full runs and captures, head b6650116)

- Frontend full vitest (`frontend/`, `npx vitest run`): 3522 passed, 3 failed, 144 files (143 pass, 1 fail), 323 s. The 3 failures are the known
  `w1f4VerificationStructure` tests; no other failure (a duplicate run started by another agent was stopped by PID before this one finished;
  no unexpected failures appeared). Log `.agent/vitest-full.log` (ignored).
- Backend `tools
un-backend-suite-in-container.ps1 -Tier all`: started 21:58 local, 4 workers, postgres-test, wall 2300 s (38m18s),
  **4338 passed, 0 failed**, JUnit `errors=0 failures=0 skipped=0 tests=4338` (no `<skipped`). Run dir
  `var/test-results/OPS-03/20261030-215840-fd3ad2` (exit 0). No failure to rerun on main.
- Captures at 1440 and 390, each with its v70 mock pair, in `.agent/OUT-C-captures/shots/` (tool `capture-outc.mjs`, targets `targets.json`,
  evidence `shots/raw-evidence.json`, logs `logs/`). Producers: w502 positive (GreenHarvest, DB `w502b_positive_outc_test`, API 8971/Vite 5471),
  w504 (Depot, `w504a_positive_outc_test`, 8981/5481; other w504 modes prepared by the tool, all dropped). 40/40 then 10/10 claims passed.
  - `overview-cold-cost-open` (mock `cold`): Cost row open; shows "3 repair visits in 60 days without a result", the Repair and call-out
    Unknown line, Maintenance effectiveness 3 visits, and the Issues column "Risk Repeated maintenance without a result". No page overflow
    (1425/1425 at 1440 with scrollbar, 390/390).
  - `findings-cold` (mock `cold-findings`): `.oc-warn` list inside "Findings at this site" panel, 3 items (Risk + 2 Early warning); 0 items
    overflow. **Reflow evidence:** 1440: three items side by side (x 268-629, 647-1009, 1027-1388, list 1120 wide); 390: one column
    (every item x 36-354, list 318 wide), scrollWidth = clientWidth, page scrollWidth 390 = clientWidth 390, no page overflow.
  - `request-latest-cold` (mock `wr-overview`; URL `/maintenance/requests/722623c3-...?site_id=COLD-LAB-001&known_at=...`): amber notice
    "This is the third visit to generator-1 in 60 days, and the linked finding is still open. Repeated work ..." directly above the panel pair
    (`nextIsPair` true), at both widths, no overflow.
  - `overview-ev-depot` (mock `ev`, w504): Protect row open: "Connector c1 out of service" Risk issue, "2 issues"; no overflow.
- No estate captures (P-C1 failed). Layout evidence: the measurements above come from the capture tool (CDP), not `layout-evidence.mjs`.
- Observations (not C defects): the Depot Protect row also shows "Connector Connector c1" in B-owned text (availability line and
  "Connector Connector c1: 44 min out"); C's own warning title is single-prefixed. Cost row in the GreenHarvest Overview carries the
  warning in the row's Issues column, not an `.oc-warn` block (so `warnLists` is empty there by design). The Overview and Depot
  targets needed a custom ready selector because the default "Loading" heuristic stayed false on pages that were fully rendered.
- toolseck-all.ps1: All 11 guards passed.
- Cleanup: all `_outc_test` DBs dropped, API/Vite/Chrome stopped by PID, no listeners left on 8971-8987/5471/5481/9621.

## Final-review fix round (Rulings C, final review; review `OUT-C-review.md` at 0297540a)

Commits: `04fa0d8a` (M1), `4b42b2ca` (rulings), and this packet commit.

| Item | Done |
|---|---|
| F1 `fault_name` | `visits.py` `FAULT_NAMES` fills `WarningFacts.fault_names`; `warnings.py` `_repeated` sets `Warning.fault_name` when every open linked id maps to one name, else `LINKED_FINDING`; wire key `fault_name` (null off REPEATED); `OutcomeWarning.fault_name`. No new read; schema versions unchanged. |
| H1-1 | `SiteEarlyWarnings` passes `showSite` (`EarlyWarnings.tsx`); the three Site Findings lists render through it. |
| H1-2/3/5/6 | R572 copy: seen line, Cost contributor, `COST_SUBLINE_FAULT` (else `COST_SUBLINE`), `repeatVisitNotice(count, subject, faultName)`, card note. |
| H1-4a | `cold.py`: `options[COST]` = the start-test option with Protect's `start_href` only when the start failure is a FINDING ref of the repeat warning. |
| H1-4b / H1-6 | Risk badge kept (R573); card 4 `tone="amber"` when the count is >= 1. |
| M2 | `repeatCheckSites` + six states in `RepeatVisitsCard`; "None in the last 60 days" only with every Site checked (R574). |
| L2 | `mini.protect_clear`; strings in `COPY`. |
| L1 | `ev.connector_name` at both sites. |
| M1 | 648 paths untracked; 4 tracked remain, all also tracked on main e8cf8a36. |
| L4 | Known deviations corrected (full names match the mock's `CATN`; P-C1 is structural, R575). |
| Register | R572-R575 added; R575 open, owned by the P-C1 follow-up slice. |

Checks (on 4b42b2ca plus the s404 test-expectation edit in this commit):
- pytest, every non-Postgres `test_out_*` (plan2 venv, worktree PYTHONPATH): **196 passed**. Run once without
  `PYTHONDONTWRITEBYTECODE`: `git status --short` empty afterwards (M1 confirmed).
- `test_out_c3_repeat_visits_postgres.py` alone on `assetops_out_c_cold_test`: **1 passed** (28 s). It now asserts the
  authored-data copy: `fault_name`, seen tail, Risk badge, Cost subline and contributor, Cost option href = Protect's.
- vitest on 9 files (earlyWarnings, globalMaintenance, workRequestOverview, coldFindingIndex, evFindingIndex,
  s404SiteFindingIndex, outcomeBoard, estatePortfolio, estateRoots): **200 passed**. `tsc --noEmit`: exit 0.
- New vitest cases: one per M2 state (refused = existing case; no Site checked; partly checked; all checked = "0";
  found + all checked, amber; found + unchecked, amber + " · not checked for GreenHarvest") and the cold-Site UNKNOWN
  Cost never-"None" case. Pytest: fault_name agreement/fallback, Cost option present/absent, subline fallback,
  `protect_clear` m = 24/1/0/None, no double "Connector" prefix, `fault_name` in the never-money walk.
- Non-vacuity: weakening `repeatCheckSites` to `read_state === "AVAILABLE"` failed 4 card cases (including the
  never-"None" case); reverted with `git checkout`, tree clean.
- `tools\check-all.ps1` (ASSETOPS_GUARD_PYTHON = plan2 venv, no policy flag): **All 11 guards passed**.
- Vocabulary scan (terms + w1.terms + w1.codes + w1 patterns, 107 patterns) on all 19 new viewer strings: 0 hits.
- Not run, as instructed: full suites, browser and layout evidence. The card-4 amber tone and the Site-name prefix
  are proven in vitest only; no new capture.
