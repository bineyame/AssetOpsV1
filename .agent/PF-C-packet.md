# PF-C + PF-W review packet (card B2)

- Branch `task/PF-C-coverage-once` (worktree `AssetOpsV1-pfc`), from main `4b20b0462`.
- Specs: `.agent/architect-proposal-portfolio-layout-2026-11-10.md` §4 PF-C1/PF-C2, §10 (word inventory); owner items 2-3 (`owner-walkthrough-2026-11-10.md`); D-E5.46 (`build-sheet-OWN-GAPS-2026-11-08.md`, last section); layout `frontend/mockups/v71/portfolio-tabs.html` `.pf-coverage`.

## Outcome
- **PF-C1, coverage once.** `site_outcomes/read.py` `portfolio_coverage()` builds one `coverage_line` `{state, lead, rule, sites[{site_code, site_name, complete, text}], days_text}` from the same `counted.days` the cards count. The summary and `/api/estate/chain` both carry it. The frontend `estate/PortfolioCoverage.tsx` renders it once, between the context row and the tab row (`role="note"`), on every tab. It adds each Site's estate gap days in the D-E5.46 short words, the "What these words mean" glossary (8 terms) and the "Which days, and why →" link to the Scope tab. When every day is complete, it collapses to the green "Complete readings on every day".
- **Removed:** the R620 per-Site notes in the context row, and the C6 eyebrow copy of the findings count (the lens row keeps one copy, "· so far, some days incomplete").
- **PF-C2, exception-only card days.** Protect and Assure send `days_line: null`. Grow and Optimize send one only when their claim days differ from the shared line's days per Site (`_own_days`). The browser labels it "Different days:". The estate "Why?" days fall back to `coverage_line.days_text` (`chain_api.py`), and guard COH-17 W3 follows the same fallback.
- **C7:** a row of a Site with incomplete days reads "Value not shown while this site has incomplete days". The same wording applies in the estate Findings index (R622).
- **PF-W, the words.**
  - Every `chain/vocabulary.py` data template moves from "checked" to the readings family: counts, money, days lines, Why?, MG-1, income, Protect small, Assure "not judged yet", withheld note. A parametrised test refuses `checked|unchecked|checking` in every NODE/WHY/CARD/COUNT/MG1 template.
  - New shared vocabulary in `vocabulary.py`, held byte-for-byte in `portfolioWords.ts` and enforced by a parity test: `READINGS_TERMS` (complete / partial / too few / no readings received / not enough / conflicting / still processing / not analysed yet), `GAP_REASON_WORDS` (D-E5.46 table verbatim, full + short, including READINGS_CONFLICT and NOT_ENOUGH_READINGS for GAP-REASONS to wire), `STILL_PROCESSING`, and `incomplete_sites()`/`incompleteSites()` ("{n} site(s) with incomplete days").
  - Frontend F rows:
    - context badge "Some days incomplete" / "Portfolio: Some sites have incomplete days";
    - Site state "Incomplete days" (portfolioWords, estateShared, EstateEvidence);
    - estate Findings "So far" line "{n} sites with incomplete days" (D-E5.26 amended);
    - Scope tab "Incomplete days: {day}: {reason}";
    - OutcomeBoard zero forms;
    - Opportunity zero.
- `estate/coverage.py` is untouched.

## Files materially changed
- **Backend:** `backend/assetops_backend/chain/vocabulary.py`, `site_outcomes/read.py`, `chain_api.py`.
- **Guard:** `tools/checks/chain_coherence.py` (W3 fallback; N1 also refuses the new day-count form).
- **Frontend:** `frontend/src/estate/{PortfolioCoverage.tsx (new), EstatePortfolio.tsx, PortfolioOutcomes.tsx, portfolioWords.ts, estateClient.ts, estatePortfolio.css, estateShared.tsx, EstateEvidence.tsx, findingIndex.tsx}`, `sites/OutcomeBoard.tsx`, `test/panelStructure.ts` (v71 coverage line allowed between context and tabs).
- **Tests:**
  - new `backend/tests/test_pfc_coverage_line.py`;
  - pinned strings updated in about 18 backend test files and `tools/checks/test_chain_coherence.py`;
  - ch5a1/ch5a2 goldens regenerated from their in-memory fakes (`ASSETOPS_REGEN_CH5A*_GOLDENS=1`; no capture);
  - `tools/demo_combined_{finish,rows}.py` pinned strings;
  - frontend `estatePortfolio.test.tsx` (R620 tests replaced by 5 PF-C tests), `estateRoots.test.tsx`, `outcomeBoard.test.tsx`.

## Checks
- **Tests first:** `test_pfc_coverage_line.py` failed at collection before the code (ImportError `portfolio_coverage`). Frontend: with main's `EstatePortfolio.tsx` over 5d76e193f, `vitest -t "coverageLine|incompleteSite"` = 4 failed; reverted with `git checkout HEAD --`.
- **Backend pytest, one file at a time,** final: test_pfc_coverage_line 123 passed; ch6b2_portfolio_cards 55; ch6_claims 9; ch5b_why 48; ch5a2_contract 26; ch5a1_board_contract 13; demo_combined_finish_rows 75; out_b2_vocabulary 4; out_b3_cold_ev 28; idx_gaps_board 6; walk1_5_solar_window 11; mb1_thread_line 42; ch3_rows 42; walk1_3b 16; demo_story_days 92; out_b2_mini 32; out_d4_board 17; ch5d1_optimize_card 7; ch6_contract 12; out_b1_board 29; out_w2_summary_window 9; k10 10; cov_partial 20; out_c2_board 13; qw2_reuse 4; out_b4_read 11; ch6b_estate_chain 20; ch5a2b_claims 31; ch6_evaluator 46; ch6_r2a_rows 6; cov_partial_portfolio 13; walk1_productive_sales 22; tools/checks/test_chain_coherence 181. All 0 failed.
- **Vitest per file:** estatePortfolio 85/85, estateRoots 23/23, outcomeBoard 27/27, estateEvidence 17, estatePortfolioRoutes 4, estateFinancials 11, s5SiteWindowOverview 63, w302 2.
- **Other checks:** `tsc --noEmit` clean. `check-architecture.ps1` (ASSETOPS_GUARD_PYTHON=plan2 venv): "Architecture check passed." (code at 5d76e193f).
- Not run: Postgres test files that pin the old strings (sed-updated only; e.g. `test_ch6b_estate_postgres.py`, `test_ch9b3_mill_verdict_postgres.py`); no full suites (rule).

## MOCK DEVIATIONs
- **MD-PFC-1:** v71 names the partial day inside a Site clause ("Kobo: 6 Oct partial readings"). The chain grades are counts, so the clause reads "Kobo: complete readings on 6 of 7 days · 1 with partial readings". Named days come from the estate gaps ("4 Nov: no readings").
- **MD-PFC-2:** v71 `aria-label="Days checked"` becomes "Readings coverage".
- **MD-PFC-3:** the days-line parts read "· {p} with partial readings · {n} with too few readings, not counted" rather than §10.2's terse "· {p} partial · {n} too few", so each term is the glossary term.
- **MD-PFC-4:** the glossary is a `Disclosure` in the line. v71's per-term hover `abbr` is not built.
- **MD-PFC-5:** the lead combines the server lead with "· {n} site(s) with incomplete days" when the estate has PARTIAL Sites. "All days checked" becomes "Complete readings on every day".

## Known deviations / left for others
- **Section 10 B rows outside `chain/vocabulary.py`** are NOT changed, to keep the card at 1.25 units and to avoid many Site-surface pins: `site_outcomes/mini.py` gap lines, `board.py` thread lines ("fully checked days to close"), `ev.py`, `actions/verification_families.py` / `fuel_verification.py`, `outcomes/objectives.py`, `objective_facts.py`, `fuel_balance/night_text.py`. These need a follow-up (PF-W2).
- `ui/productWords.ts` currency words ("Some days are not checked yet"…) and `work/GlobalMaintenance.tsx` "Partly checked" are outside the section 10 inventory and unchanged.
- PB-4 files (`SiteFindingIndex.tsx`, `OverviewFindingList.tsx`) are untouched, per the brief.
- `estate/coverage.py` `DAYS_CHECKED` text ("{c} of {n} days assessed · {g} not available yet") is unchanged (it says "assessed", and the brief forbids touching it). It is no longer shown on the Portfolio.
- Guard W3's new `coverage_line` branch is exercised only by live bundles. The committed fixture bundles predate it, so they use the Protect fallback; no planted-break test was added for the new branch.

## User-review focus
- The wording choices (exact strings above), especially "Value not shown while this site has incomplete days" and the "Not analysed yet" definition ("AssetOps has not analysed the day yet; it will, without any action from you.").
- Lead behaviour when the server says complete but the estate has gap days.
