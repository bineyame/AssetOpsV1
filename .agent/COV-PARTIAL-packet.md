# COV-PARTIAL review packet

Task: `tasks/COV-PARTIAL-estate-coverage.md`. Contract: `AssetOpsV1-plan2/.agent/build-sheet-COV-PARTIAL.md` + Addendum 1.
Branch `task/COV-PARTIAL-estate-coverage`, base `0796218fc`. The commits are U1 `36ab2f54a`, U2 `eac8556df`,
U3 `b44f86572`, U4 `282cedb90`, docs `ea8fcef3e`/`4188e17c7`, and the replay fix `28fcf3965`. USER_REVIEW_REQUIRED: false.

## Outcome delivered
On `estate-coverage/2`, a live mini-grid Site has at least one day without an assessed selection, and every checked
day is current. Such a Site reads PARTIAL, with `days {policy, requested, checked, gaps[], withheld, text}`. It lists
Findings from the checked days only and carries no amount. It is never counted as covered. Estate roots read UNKNOWN
and Portfolio reads PARTIAL; neither is ever CURRENT. The UI shows:
- the "Some days not checked yet" badge;
- one note per partly checked Site, naming its unchecked days;
- the gap list in the scope drawer;
- "Partly checked · ..." on the affected rows;
- the estate Findings panel and notice.

## Files materially changed
- Backend: `estate/coverage.py`, `estate/index.py`, `estate/portfolio.py`.
- Frontend: `frontend/src/estate/{estateClient.ts, portfolioWords.ts, EstatePortfolio.tsx, estateShared.tsx,
  EstateEvidence.tsx, findingIndex.tsx, estatePortfolio.css}`.
- New tests: `test_cov_partial.py` (T1-T12), `test_cov_partial_portfolio.py` (S1-S6, X1, X2) and
  `test_cov_partial_postgres.py`. Vitest: `estatePortfolio.test.tsx`, `estateRoots.test.tsx`,
  `portfolioFixtures.ts`.
- Golden: `backend/tests/fixtures/w3/w301-estate-golden.json`.
- Docs: the register (R613 resolved, R620-R622), `.ai/DECISIONS.md` (`D-2026-10-31-estate-coverage-v2`),
  `.ai/CODE_STATE.md` and `.ai/ACTIVE_CONTEXT.md`.

## Every changed golden path (diff `282cedb90~1` to HEAD; replay without the write flag passes)
**Added `days` keys (39).** All are additive. Their value is `null` for cold, EV, one-day `not_applicable` and mixed
cold/EV Sites, and an object for mini-grid Sites.
- `$.branches.cold.cases[1..6].expected.coverage.sites[0].days`, plus `cases[6]...sites[1].days`: null.
- `$.branches.ev.cases[1..6].expected.coverage.sites[0].days`, plus `cases[6]...sites[1].days`: null.
- `$.branches.mini_grid.cases[0,1,2,5..12].expected.coverage.sites[0].days`, plus `cases[12]...sites[1].days`:
  object. `cases[4]...sites[0].days` is null.
- `$.branches.mixed.cases[1].expected.coverage.sites[0,1].days`: null. `sites[2,3].days`: object.
- `$.branches.mixed.cases[2].expected.coverage.sites[0..3].days`: null.
- `$.branches.mixed.cases[3].expected.coverage.sites[0,1].days`: null. `sites[2,3].days`: object.

**State flips that Addendum 1 Q1 allows** (KOBO-001, live 10-06..10-12, at least one gap, checked days current):
- `$.branches.mixed.cases[0].expected.sites[2].coverage_state` changes from UNKNOWN to PARTIAL (scope-mixed).
- In findings-mixed-week:
  - `$.branches.mixed.cases[1].expected.coverage.sites[2].state` changes from UNKNOWN to PARTIAL.
  - `....sites[2].source_freshness` changes from UNKNOWN to RECENT.
  - `$.branches.mixed.cases[1].expected.rows` goes from length 0 to 2: rows from the checked day, with no amount.
  - The root `status` stays UNKNOWN.

No other path changed.

## Literal edits to existing tests (beyond the U1 allowance, which was `test_w301_estate_coverage.py` only; that file needed none)
1. `test_w301_estate_index_postgres.py:561` (Addendum 1 Q2). The PowerSite gap read is now PARTIAL with
   `days` (3, 2) and gap `2026-10-07`. Its amounts are None. The root `status` stays UNKNOWN.
2. `test_w301_estate_index_postgres.py:187` (commit `28fcf3965`, found by the U4 replay). The exact cold
   coverage-Site dict gains `"days": None`. Equality stays exact; this is the additive key from §2.6.
3. `test_w301_estate_api.py:130`. The exact UNKNOWN coverage literal gains its additive `days` object.
   `:233` adds `days is None` on the C5 day-count mismatch (Addendum 1 Q3; the state stays UNKNOWN).
4. `test_w302_evidence_api.py:247`. The expected coverage-Site key set gains `"days"`.
5. `estatePortfolio.test.tsx:424-429`. The word map gains `PARTIAL`, and the list of statuses the fixtures cover
   gains `"PARTIAL"`.

## Acceptance criteria
- §0, nothing reads as zero or on track: MET. X1 covers the Findings, Evidence, Financials, Scope and Portfolio
  roots. T11 and the captures confirm it (root UNKNOWN, Portfolio PARTIAL).
- §2 rule, T1-T12: MET (`test_cov_partial.py`).
- §3 Portfolio status order, S1-S6: MET.
- §4 U3 words, placement, drawer, rows and Findings copy: MET in vitest and in the live captures below.
- §4 U4 Postgres proof, golden and the `:561` edit: MET. The golden replay without the write flag passes.
- §5 merge gate (`-Tier all` and full vitest): NOT RUN, deferred to the coordinator's go after LINK-LINEAGE.

## Checks run (final code revision `28fcf3965`; only the packet follows)
- **U4 §5 Postgres set plus the U1/U2 sets**, 17 files, on DB `assetops_covp_test`, at revision `4188e17c7`:
  - Result: `2 failed, 168 passed in 1558s` (wall 26:01). Another lane's `-Tier all` (ops03, started 19:14) shared
    the machine for part of the run.
  - The golden passed.
  - Failure 1: `test_cold_ev_day_intersection_selects_exact_windows` was genuine (the missing `days`). It is fixed
    in `28fcf3965` and rerun: 1 passed.
  - Failure 2: `test_historical_minigrid_outstanding_marker_page_two_keeps_basis`, `EstateRefusal: INVALID_CURSOR`.
    This is the known pre-existing failure listed in sheet §5.
  - An earlier attempt was stopped by PID past twice its expected time, because an ops03 `-Tier all` started
    alongside it.
- **Backend** `test_cov_partial.py test_cov_partial_portfolio.py`: 30 passed.
- **Vitest (scoped):** `src/estate/__tests__` (5 files), plus `idxGapsFindingIndex`, `t028Vocabulary`,
  `w301EstateShellRoutes` and `globalMaintenance`. Result: 9 files, 138 passed. `npx tsc --noEmit` is clean.
- **`tools\check-all.ps1`** at `28fcf3965`: all 11 guards passed, including the missing-claim scan.

## Non-vacuity proofs (each mutation was made on committed code, run, then undone with `git checkout --`; the tree was clean after each)
- `index.py:38`, PARTIAL-to-UNKNOWN check disabled: T11 and X1 fail (2 failed).
- `coverage.py:152`, gap-touching head drop disabled: T7 fails.
- `coverage.py:170`, `withhold=False`: T8 and X1 fail.
- `portfolio.py:572`, `status = 'CURRENT'` in place of PARTIAL: S1-S6 `[states0-PARTIAL]` and `[states3-PARTIAL]`
  fail.
- `EstatePortfolio.tsx` partial-note filter set to `false`: `partlyCheckedSiteNamesItsDaysAndWithholdsValue` and
  `...ManyGapsPointsToTheScopeList` fail.

## Layout evidence: captures (`.agent/COV-PARTIAL-captures/`, 12/12 claims in `covp-claims.json`)
Producer: `tools/s404_finding_index_walkthrough.py prepare|serve --db assetops_s404_owner_covp_test` on ports
8944/5444, with `ASSETOPS_ESTATE_PORTFOLIO_CURSOR_KEY_HEX` set.

Window `2026-10-15 to 2026-10-22`:
- Checked days: 15, 19 and 21. Gap days: 16, 17, 18 and 20.
- The dirty 10-27 and the failed 11-05 are outside the window.
- API: Portfolio `PARTIAL`, Findings root `UNKNOWN` with `total_count` null and 4 rows.

| Claim | 1440 | 390 |
|---|---|---|
| Badge "Some days not checked yet", sentence "Portfolio: Partly checked" | PASS | PASS |
| Note exactly "Kobo mini-grid: 3 of 7 days checked · 4 days not available yet · not checked: 16 Oct, 17 Oct, 18 Oct, 20 Oct" | PASS, 1 line | PASS, 2 lines |
| Drawer "Mini-grid · Partly checked" + "Days not checked yet: 16 Oct, 17 Oct, 18 Oct, 20 Oct" | PASS | PASS |
| Findings panel "Kobo mini-grid is partly checked; totals are unknown." + notice "Kobo mini-grid: 3 of 7 days checked · 4 days not available yet." | PASS | PASS |
| Rows read "Partly checked · No consequence recorded" | yes | yes |
| No state code (`PARTIAL`, `UNASSESSED`, `NO_ASSESSED_SELECTION`, `UNKNOWN`, `CURRENT`, ...) in main text, `title` or `aria-label` | PASS | PASS |
| Horizontal page overflow ≤ 0 | -15 (scrollbar) | 0 |

The files are `covp-portfolio-note-{1440,390}.png`, `covp-portfolio-drawer-{1440,390}.png` and
`covp-findings-partial-{1440,390}.png`. The capture script is `idxcap.mjs`-style, kept in the session scratchpad
as `covcap.mjs`.

**Capture deviation.** The producer stamps `site_import.imported_at` with the real clock, which left the estate
scope empty for October windows. On the private producer DB only, I backdated it with
`UPDATE site_import SET imported_at='2026-10-01Z'` for KOBO-001. This is the same move as
`test_w301_estate_index_postgres.py:93` `imported_before`. No tool or product code changed.

**Cleanup.** The servers were stopped by PID (27972 and 7240). `assetops_s404_owner_covp_test` was dropped with the
producer's `drop` command, and `assetops_covp_test` was dropped.

## Known deviations
- CO-6/CO-6b in `tools/demo_combined_finish.py` are left to DEMO-A (Q4).
- MOCK DEVIATIONS R620 and R622 apply: the note, the chip and the notice are not in v70.
- At 390 px, the Portfolio Findings table keeps its existing in-panel horizontal scroll (min-width 720px). That
  predates this slice. The page itself does not overflow.

## Residual risk
- `-Tier all` has not yet run on this branch. Other suites may compare whole coverage-Site dicts and miss the
  additive `days` key (as the cold one did). A grep of the backend tests found only field reads in the remaining
  files.
- Five orphaned `assetops_gateway serve` children of the first, stopped run remain: PIDs 2592, 2052, 22440, 31564
  and 7664. My attempt to stop them was refused by the permission classifier. They are idle.

## User-review focus
The partly checked Portfolio week (note and drawer) and the estate Findings notice, in the combined walkthrough.
