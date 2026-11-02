# Review packet: WALK1-1 (Portfolio checked days, Assure verified count, Grow card, labels)

Branch `task/WALK1-1-portfolio-fixes` from main `2058a6567`. Spec: `.agent/build-sheet-WALK1.md` §2 (WN-2, WN-1, WN-3 display), §8 R670-R673, §9 D-W1-4.

## Outcome delivered
- Portfolio (`estate/portfolio.py` `_portfolio`): `summary.count_basis` = `COMPLETE` (F complete/empty), `CHECKED_DAYS` (status PARTIAL), else null. Finding, opportunity, placement and category counts publish under either basis. `summary.checked_days[]` lists every PARTIAL Site with a `days` block. Money unchanged.
- Pre-flight E1: `select_evidence_scope` returns rows for a PARTIAL mini-grid Site (`mini_grid_rows`: one row per dispatch day; an unchecked day is UNASSESSED and has no typed gap). So `evidence_gap_site_count` follows the same rule (`evidence_known = E complete/empty or CHECKED_DAYS`).
- Outcome summary (`site_outcomes/read.py`): the board carries the private `_verified_results` (VERIFIED `ActionFact`s, all domains). The route strips it with its generic `_` prefix filter (`outcome_api.py:76`). The summary adds `verified_result_count` (null when no board loaded) and `verified_sites_unread`. `_summary_row`/`_unknown_row` pass `headline_money` through.
- Frontend: types are optional, so an absent field reads as null/[]/0. In `PortfolioOutcomes.tsx`:
  - `checkedDaysClause` is appended to the Protect, Assure and Optimize details.
  - Protect with zero findings on checked days reads `None found <small>on the days checked</small>`.
  - Protect wording is now "recorded as findings".
  - `verifiedText` provides the Assure lead.
  - `evidenceGapText(0, …, true)` reads "no evidence gaps on the days checked".
  - The Grow card takes its value from `headline_money` (one Site / k Sites, never summed) and falls back to `short_value`, then to "Not available yet".
- Pulse strip (`EstatePortfolio.tsx` `PulseCount`): a zero count of opportunities or evidence gaps under CHECKED_DAYS reads "Opportunity: None found on the days checked".
- `OutcomeBoard.tsx`: when `finding_gaps` is set, the board reads "None found on the days checked" and "No open issues on the days checked".
- Capital-F Lows: "Review finding" and "Open finding →" at the 5 listed lines.
- Register: R670-R673 added, and the new strings appended to the R655 row.

## Files materially changed
`backend/assetops_backend/estate/portfolio.py`, `backend/assetops_backend/site_outcomes/read.py`, `frontend/src/estate/{estateClient.ts,PortfolioOutcomes.tsx,EstatePortfolio.tsx}`, `frontend/src/sites/{OutcomeBoard.tsx,coldSiteViews.tsx,EvAssessmentViews.tsx,EvSiteViews.tsx}`, tests (`test_cov_partial_portfolio.py`, `test_out_b4_read.py`, `test_w303_portfolio_api.py`, `estatePortfolio.test.tsx`, `portfolioFixtures.ts`, `outcomeBoard.test.tsx`, `coldSiteViews.test.tsx`, `evAssessmentRoutes.test.tsx`), `.agent/mock-departure-register.md`.

## Acceptance (§2.5)
- PARTIAL estate: `count_basis == "CHECKED_DAYS"`, Protect `sites_with_primary_finding` is an int, the evidence gap count is an int, and `checked_days` is pinned. An UNKNOWN estate stays null. A COMPLETE estate stays COMPLETE. Met (`test_walk1_*` in `test_cov_partial_portfolio.py`).
- Summary: `verified_result_count` is 1 for one VERIFIED Action out of three, and `headline_money` passes through. A failed Site gives `verified_sites_unread` 1, and a summary where every board failed gives null. Met (`test_walk1_summary_verified_count_and_headline_money`).
- Vitest: Protect zero/n on checked days; the clause for one and for two Sites; COMPLETE keeps today's words; Assure lead 0/1/2/unread/null/absent; Grow one Site, two Sites, the short_value fallback and "Not available yet"; the pulse strip; the board with `finding_gaps`; capital-F strings; a w1 vocabulary scan over cards, strip and board. Met.

## Checks run (revision 253e0df03, except where noted)
- Backend scoped (12 files: cov_partial*, w303 portfolio api/reduction, cc_placement, out_b4 read/route/window, out_w2 summary window, out_d4, out_b1, out_b2): **238 passed, 1 skipped**. The skip is the w303 Postgres module, which needs a DB URL. Commit 3c5377af3; backend unchanged since.
- Postgres modules (`test_cov_partial_postgres`, `test_w303_portfolio_api` pg, `test_out_b4_board_postgres`) against my own `assetops_walk1a_test`: **not completed** (the session watchdog stopped the run). They are unverified on real Postgres.
- Vitest (estatePortfolio, outcomeBoard, coldSiteViews, evAssessmentRoutes): **189 passed**, with estatePortfolio re-run at 50/50 after the wording fix. `tsc --noEmit`: clean.
- Guards, run one at a time in the foreground with the check-all argument lists. Passed:
  - architecture: passes with `ASSETOPS_GUARD_PYTHON` set. Without it, rule 8 reports "vacuous" because the worktree has no `.venv`. This is environmental: check-all sets the variable.
  - navigation truthfulness
  - agent workflow
  - dependency registry
  - delivery fixtures
  - mock-gap fixtures
  - missing-claim scan (passes after fix commit 253e0df03)
  - missing-claim fixtures, 26/26
  - evidence width
  - mock deviation labels and vocabulary
  - screen ledger
- Estate guard self-test (`tools/checks/test_estate_guard.py`) when launched from Git Bash: fails on PowerShell execution policy (UnauthorizedAccess). This is environmental. Its PowerShell-launched re-run had not finished when this packet was written; see the reply.
- Full `check-all.ps1` in one run: not completed (over 10 minutes; the watchdog stopped it). Its guards were run individually as above.

## Known deviations
1. Assure lead before the summary loads reads **"Verified results not known yet"**, not the sheet's "Verified results not available yet". The missing-claim guard rejects untagged "not available yet" copy. The wording matches the card's own "Not known yet" value. Recorded in R671.
2. In the pulse strip a zero count under CHECKED_DAYS renders label first: "Opportunity: None found on the days checked". This keeps the sheet's phrase intact and reads as a sentence. Labelled MOCK DEVIATION R670 in code.
3. The checked-days clause is appended to the Protect, Assure and Optimize details only. The Grow detail follows its own §2.3 text ("· latest day per site").
4. The backend tests sit in `test_cov_partial_portfolio.py` (its fake world), not `test_cov_partial.py`. Importing the world into `test_cov_partial.py` would be circular.
5. `checked_days` lists PARTIAL Sites even when `count_basis` is null (the §2.1 rule). The client uses it only under CHECKED_DAYS.
6. Not changed (outside the listed lines): `EvAssessmentViews.tsx:345` `UnavailableInline label="Open Finding"` and `SitePerformance.tsx:408` "Open Finding".

## Residual risk / review focus
- The real-Postgres PARTIAL path is not re-run here. G1 captures (`portfolio-week`, `kobo-board-S`, `findings-*`) are due at the gate rebuild.
- Grow card copy: "{amount} estimated", "latest day per site". A cold/EV Grow row is judged on its latest event, not a day.
- The R655/R670-R673 register rows will touch the same file as WALK1-2's R674-R676 (an append-only merge).

USER_REVIEW: owner walkthrough after G1. No separate user review is needed for merge beyond the Reviewer.
