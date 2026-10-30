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
- The list's category text is the backend category label ("Optimize cost and efficiency"); the mock prints short names.
- Maintenance "window over 31 days": the page parser already refuses such a window, so that branch is defensive and proven only
  by the `coveringUtcDays` unit test.
- R358 row describes Incidents; a Maintenance note ("cards 2-3", R571) was appended instead of rewriting the row.
- The mini Site Findings list renders only for MINIGRID Sites in the mini index branch.
- From U4 (handoff): a connector label already starting with "Connector" is not prefixed again.

## Residual risk

- Estate surfaces have no real-data proof (P-C1 failed: the whole-day estate summary on w502 shows no REPEATED warning); carried to the combined dataset.
- Full suites not yet run on this head; the Kobo b4 Postgres tests after the U4 MG-4 change are covered only by the U4 run.

## User-review focus

Placement of the lists under the tables (estate, Site, Portfolio), the pulse wording, the Maintenance card and the request notice.
USER_REVIEW_REQUIRED: false for merge; the owner sees it in the post-sprint walkthrough.
