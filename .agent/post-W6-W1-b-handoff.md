# post-W6 W1-mini-Action-b: build handoff (built, captured, closed out; in_review)

**Update 2026-10-25:** main (W1-a 3b4979d0) merged (d960eeee); 142/142 pairs captured; Q23 cap fallback e6af4ff0; full vitest, build, check-all run; packet `.agent/post-W6-W1-b-packet.md`. Open: Evidence requirements and Action history Q37 caps exceeded in synthetic probes with no ruled fallback (Architect). The "Remaining" list below is historical.

Branch `task/post-W6-W1-b`, worktree `AssetOpsV1-review7`, base W1-a head `ec9bfbe9` (W1-a not merged yet). Rulings: `.agent/post-W6-W1-rulings.md` (cross-card 1-5, W1-b 30-47, 48-63) amended by `.agent/post-W6-W1-b-preflight-rulings.md` (copied from main, commit `48210ee6`).

## Commits

- `3ad08bb5` unit A: frames, rail, Site Findings links, Financials links and history paging (Q19-Q28, Q33, Q35; R383).
- `e886124c` unit B: Action history resolution rows and counts (Q29/Q30).
- `6e55c0b6` unit C: verification chips/sources/plan headings/conflict copy, sitework manage link (Q31/Q32/Q34/Q36).
- `2dbd3351`, `9bf2ecdc`: test pin for the blue chip rule; typed stylesheet read.
- `62ed43d2`: R384/R385 register rows and labels (W1 ruling 57 / Q46).
- `14fa2c2b`: `test/panelStructure.ts` LEADING_SELECTOR admits `[data-mock-deviation="R383"]`.

## What landed, by ruling (file anchors)

- Q19/Q20: `SiteFindingIndex.tsx` `dispatchTarget`, `DomainCell`, `OpportunityHelper(renewable)`, panel description = mock text; `findingIndexClient.ts` optional `interval_assessment_revision_ids`; frame `SiteFindingsFrame` links `dispatch`/`renewable` (MINIGRID only).
- Q21/Q22: `FindingConsequence.tsx` `FinancialsStatusBar(rollUp)`, `TradeoffsPanel(technicalBasis)`, `technicalBasisHref` (day-only; revision only with explicit interval proof); `BridgeLinks.portfolio/dispatchAnalysis`; frame `SiteFinancialsFrame` links (`FINANCIALS_PATH`, `?day=&view=analysis`, `overview`).
- Q23: `SiteFinancials.tsx` `DEFAULT_HISTORY_LIMIT = 3`, `history_back` parsed by `ConsequenceHistory.tsx` `parseHistoryBack` (max 100, `0` only at bottom, base64url tokens); `HistoryPager` (Previous versions / Next versions / Back to newest); compact row with `Show this version` disclosure; columns Version, Fuel price, Recorded amount, Status; `PriceHistory` inside closed `Price versions recorded ({total})`; `operatorSiteRoutes.ts` `siteFinancialAssumptionsHref` appends repeated `history_back`.
- Q24: assumptions form footer `Return to financial overview` (`links.overview`).
- Q25: `OperatorShellLayout.tsx` ruled helper line; `navigation-truthfulness.ps1:654` pin; two new fixtures in `navigation-rail-fixtures.ps1` (Findings widened to index / prefix lookalike).
- Q26/Q27/Q33/Q35 (`SiteAnalyticsFrames.tsx` `CanonicalMiniFinding`, `SiteActionFrame`): no Site tabs on Recommendation and all Action views; R383 line under retained Finding tabs (overview, Analysis, evidence, history, and the unknown-section state); Action `Open site`; `/overview` alias (all Site types); unknown section body + `Open Action overview`; subtitle `{site}` until `w1ActionCode(title)` is non-null. CSS `.mock-deviation-line` in `sites/w4-mini-decisions.css`.
- Q28: `ANALYSIS_HELPER_SECTION` removed.
- Q29/Q30: `actionClient.ts` widened kind; `actionPresentation.tsx` words (unknown → `Recorded event`); `SiteAction.tsx` `historyRows`/`shownHistoryRows` (dedupe by resolution ID, keys `event:`/`outcome:`/`resolution:`), ruled meanings, chip `Latest at read time`, truncation sentence + `Show all {total} entries` only past 3, raw counts in references.
- Q31/Q32/Q34: `SiteActionVerification.tsx` plan Panel `className="w1f4-verification-plan"`, `requirementTone(true) = "info"`, `sourcePair`, `distinctGap`; `verificationWords.ts` Tone `info`; `verificationCards.tsx` `conflict` prop + `CONFLICT_CARD_NOTE`; `w1f4-verification.css` row-heading and `.verify-chip--info` rules.
- Q36: `SiteWorkActions.tsx` `WorkStrip(manage)`, docblock updated; frame passes `ACTIONS_PATH` (mini only).
- Register: R383 (pre-flight ruling 3, exact text), R384 (B4-21), R385 (B4-22), labels below the Success criteria and Evidence requirements tables.

## Tests and proofs

Focused files green at `9bf2ecdc`: siteAction 77, siteFinancials 94, s404SiteFindingIndex 39, operatorRailInventory 31, siteActionVerification 32, miniDecisions, w1f4ActionStructure, w1f4ChangesWorkStructure, w1f4VerificationStructure, domainActionVerification, cold/ev/siteWorkActions, siteFinding/Evidence/History, t028*, operatorRouteFrames, evDepth, estate. `tsc --noEmit` clean. Single-file revert proofs (each new test fails): OperatorShellLayout 7, SiteFindingIndex 9, FindingConsequence 3, ConsequenceHistory (module import fails, 40), SiteFinancials 12, SiteAnalyticsFrames 19, SiteAction 6, actionPresentation 1, SiteActionVerification 3 (+2 for R384/R385), verificationCards 1, w1f4-verification.css 2, SiteWorkActions 1. `verificationWords.ts` is type-only (no runtime proof). The Q22 invalid-window test is a negative test and also passes without the fix.

Known red outside W1-b: `shell/__tests__/siteDetailRoute.test.tsx` "offers the Site tab destinations" counts the linked Site crumb W1-a added in Q1 (`b09a5c07`); W1-b does not touch SiteDetails/SiteDetailFrame. W1-a owns that flip.

## Remaining (held for clearance)

1. Merge W1-a's final head (capture-round fallbacks) into this branch; rerun the focused files above plus `siteDetailRoute`.
2. Captures: all 118 indexed pairs (sitefindings, financials, assumptions, recommendation, five action-*, verification, sitework) at 1440/390, current SHA, plus Q40 reach (cold/EV Finding rail pairs, Finding representatives for R383, `requirementTone` pages). Caps: Interpretation history 800/1400 closed (Q23), Trade-offs 390 450, Evidence requirements 450/800, action-history 390 800. Viewer actions to log: Previous/Next versions, Show all entries. Producer gaps to record: five long rows, RESOLUTION_WITHDRAWN (check s602b `withdrawn` first).
3. Full vitest, production build; backend suite only if the coordinator requires it (frontend-only slice).
4. Closeout: review packet, CODE_STATE entry, ACTIVE_CONTEXT, register disposition of R197-R230 D3 rows after review.

## Choices where the rulings were silent

- R383 label also shows on the unknown Finding section state (it keeps the Site tab row).
- Paging links carry the effective limit (3 by default) explicitly.
- `eventWords` unknown kind reads `Recorded event` (no raw code).
- B4-22 also notes bold row headings on Evidence requirements; Q31 scoped the CSS to action-plan only, so Evidence row headings are unchanged.
