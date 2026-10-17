# W1-F3 findings and money - review packet

Task: W1 structural fidelity rework, F3 (`.agent/W1-F3-findings-money-build-brief.md`, contract `D-2026-10-17-mockup-layout-spec`). Branch `task/W1-F3-findings-money`, worktree `AssetOpsV1-review`. Main (final W1-F1, `4002b1ad`) is merged in. Not merged to main.

## Outcome

Six Site screens render exactly their v69 panels, in the mock's order, form and prominence: sitefindings, finding, finding-evidence, finding-history, financials and assumptions. The W1-UX answer cards are gone. Their content now sits in the panel that owns it, or in the one-line status strip. Where the read cannot support a panel, the panel keeps its place and states the gap inside it. Every money gate is unchanged.

## Panels per screen (v69 = app; checked by `expectV69Panels`)

| Screen | Leading pattern | v69 panels = app panels |
| --- | --- | --- |
| sitefindings | chips row, status strip | Findings at this site; trailing blue notice |
| finding | status strip | What happened · What limits this conclusion · What to do next · Where to look next |
| finding-evidence | (section row) | Evidence bundle · {Finding} (approved dynamic title) · Inspect source lineage |
| finding-history | (section row) | Revision history |
| financials | status strip | What happened → what it means in money · Assumptions in use · Trade-offs and exclusions; trailing notice |
| assumptions | - | Financial assumptions · Impact preview (pair) · notice · Interpretation history |

Genuine gaps, stated inside the owning panel and registered: editable assumption and impact preview, and the revenue, asset and realised-savings measures (Financials, Assumptions).

## Merge with final W1-F1 (where the two overlap, F1's version wins)

- `V69Layout.tsx`: kept both sides (F3 StatusBar/BigClaim/Notice; F1 SitePageHeader/SITE_SCREEN_DESCRIPTIONS).
- `primitives.css`: main's file plus F3's appended block. F3 duplicates of F1 patterns were removed: `.v69-statusbar`, `.v69-input-row`, `.v69-field`, `.v69-form-footer` and `.v69-button`. F3 screens now use F1's `.status-strip--line`, `.input-row`, `.field`, `.form-footer` and `.button`/`.button.primary`.
- Adapting to the tightened guard (commit `9f2feb2a`):
  - `StatusBar` renders `status-strip status-strip--line`.
  - The shared state line inside it uses the new additive `ProductStatus inline`: one `status-strip__state` span with the same label, sentence, scope and as-of hooks, and no blocks inside the strip.
  - Notices carry `.notice`. The Assumptions notice now follows its panel pair, as in mock `siteAssumptionsScreen`.
  - Route wrappers are `div`, not stray `section`s.
  - The "What this finding means in money" link moved into the Finding section row (`FindingSections aside`). Before, it was a body paragraph above panel 1.
  - In-panel `h3`s on the F3 screens are now the mock's eyebrow or strong text. `BigClaim` can only be a paragraph (its `as="h3"` option is removed).
- Lessons applied: no h3 rebuilds, no blocks in the status strip, and in-panel text at the mock's caption or prose size (12 px prose, 11-12 px state lines).

## Changed assertions (vs main; nothing weakened)

A catalogue of every removed `expect` in the five test files. Removed/added: s404SiteFindingIndex 16/33, siteFinancials 33/75, siteFinding 32/62, siteFindingEvidence 18/49, siteFindingHistory 11/35. Classes: RELOCATED (same guarantee, new DOM home), STRENGTHENED, REPLACED-BY-STRUCTURE (the element was removed by design; `expectV69Panels` plus a named in-panel assertion hold the guarantee). None is DROPPED.

- **sitefindings.**
  - The `card()` helper now points at `panelTitled("Findings at this site")`, and every text check is kept.
  - Claim headings now check the exact `[data-site-findings-claim]` text in the strip (x5).
  - `expectStateLineVisible` and the not-positive checks now run on the strip (x10).
  - New: a 6-state `it.each`. Non-row states show an in-panel gap, no rows and no count.
- **finding.**
  - The state-line card is replaced by `panelTitled("What happened")` plus `[data-finding-claim]`.
  - MONEY "Not yet available" is now the metric value "Not available" plus "No fuel or money estimate…". The no-`$`/USD/savings check widens from the card to all of `<main>` (strengthened).
  - The version list moved to History: siteFindingHistory asserts grouping, selection and `aria-current`.
  - The refusal now asserts the page refusal plus four in-panel gaps (strengthened).
  - The step strip checks moved to the Analysis-view test, which keeps the card.
- **finding-evidence.**
  - Card state lines are now `[data-evidence-state]` inside the bundle panel.
  - The headline is now `[data-evidence-headline]`.
  - The default-reading identifier check widens to both panels (strengthened).
  - The refusal now asserts the page refusal, no evidence rows and both panels' gaps (strengthened).
- **finding-history.**
  - The card is now `panelTitled("Revision history")`.
  - The question is now `.panel__description`.
  - The step timeline is replaced by all 205 version numbers in order (strengthened).
  - "Versions not read" is replaced by `[data-history-incomplete]` plus exactly 100 rows (strengthened).
  - New: a refused `it.each`.
- **financials and assumptions.**
  - Card and region lookups are now `panelTitled(...)` with the same text.
  - Refusal headings are now `[data-page-refusal]` plus in-panel gaps.
  - The headline amount is now scoped to `[data-financials-metric=operating-cost]`.
  - Value bars are replaced by `[data-bridge-amount=current]` and the exposure gap words. The "never a zero bar" guarantee is now: the gap word has no digit, plus no `\d.\d\d USD`.
  - The withheld case asserts `[data-financials-exposure-gap]` with no amount (strengthened).
  - The per-finding version list moved to Assumptions > Interpretation history. The Overview asserts no `[data-consequence-current='true']` (x4).
- **Money gates still asserted:**
  - No current amount unless the current read proves it: the STALE/PENDING/HISTORICAL/no-rounding `it.each` and the withheld `it.each`.
  - S4-08 Interpretation history is never current: the panel has no "current amount/today's cost". New MIXED/UNKNOWN source `it.each`: the source label shows and no amount is shown.
  - NO_PRICE/CONFLICT never use a default: on Assumptions, and since `23671e6a` also on the Financials Overview "Assumptions in use" (new `it.each`; this closes a coverage gap that predates F3).
- **Soft spots (copy, not guarantees):**
  - "The fuel amount is the same in every version shown" is no longer asserted. The nearest checks are "The price changed; the measured result did not." and the pinned "same as in the latest version". The click-through to the pinned URL is now a direct URL mount, and the href is still asserted.
  - The Overview group-hint wording moved to History with different words.
  - The three answer-card question lines were dropped with the cards.

## Checks run

- `npx.cmd tsc --noEmit`: clean after the merge and at the final revision.
- Focused: the five F3 test files plus `panelStructure.test.ts`, 249 passed. New `src/test/__tests__/w1f3PanelGuard.test.ts`, 24 passed. For each of the six screens, the approved panels pass, while a planted extra panel, a leading notice and a block inside the status strip each fail (non-vacuity).
- Full `npm.cmd test` at `c3b198f7`: Test Files 77 passed (77), Tests 2003 passed (2003), 215 s.
- Final full `npm.cmd test` at `23671e6a` (final code revision): Test Files 76 passed, 1 failed; Tests 2004 passed, 1 failed (2005), 213 s. The one failure is the known flake `siteFoundationChange` ("Unable to find … heading Battery reserve change", 7.9 s under full-suite load). Rerun alone: 10/10 passed.
- `tools/check-all.ps1` at `c3b198f7`: all 10 guards passed (Architecture seams, Navigation truthfulness, Agent workflow, Dependency registry, Delivery checker fixtures, Mock-gap catalogue fixtures, Missing-claim orphan scan, Missing-claim scan fixtures, Evidence width, Screen ledger).

## Side-by-side captures (1440 / 390)

Captured at `c3b198f7`. The code changes since then (`23671e6a`) add one test and one gap-line wording, with no layout change.
- Folders under `.agent/W1-F3-evidence/` (added with `git add -f`): `part5` (finding-evidence and financials, s405), `part8` (finding and finding-history, s4_finding), `part9` (sitefindings, s404), `part10` and `part10-emptyprice` (financials, s402b), `part11` (assumptions, s402a). Each holds `<id>[-case]-{1440,390}-{app,mock}.png`, `evidence.json` and an `index.html` side-by-side page.
- All 276 tool claims passed. The panel count matches the mock in every case at both widths, and `overflowX` is 0 at 390 everywhere. Fixtures were dropped and the servers stopped.

### Panel height at 1440, app vs mock (coordinator rule: about 1.3x or less; OVER = above 1.3)

| Screen-case | Panel | App px | Mock px | Ratio |
| --- | --- | --- | --- | --- |
| financials-emptyprice | What happened → what it means in money | 525 | 288 | 1.82 OVER |
| financials-emptyprice | Assumptions in use | 313 | 306 | 1.02 |
| financials-emptyprice | Trade-offs and exclusions | 313 | 306 | 1.02 |
| financials-priced | What happened → what it means in money | 477 | 288 | 1.66 OVER |
| financials-priced | Assumptions in use | 485 | 306 | 1.58 OVER |
| financials-priced | Trade-offs and exclusions | 485 | 306 | 1.58 OVER |
| financials-notcalculated | What happened → what it means in money | 477 | 288 | 1.66 OVER |
| financials-notcalculated | Assumptions in use | 358 | 306 | 1.17 |
| financials-notcalculated | Trade-offs and exclusions | 358 | 306 | 1.17 |
| financials-notworkedout | What happened → what it means in money | 525 | 288 | 1.82 OVER |
| financials-notworkedout | Assumptions in use | 313 | 306 | 1.02 |
| financials-notworkedout | Trade-offs and exclusions | 313 | 306 | 1.02 |
| financials-notfound | What happened → what it means in money | 99 | 288 | 0.34 |
| financials-notfound | Assumptions in use | 358 | 306 | 1.17 |
| financials-notfound | Trade-offs and exclusions | 358 | 306 | 1.17 |
| assumptions | Financial assumptions | 913 | 368 | 2.48 OVER |
| assumptions | Impact preview | 913 | 368 | 2.48 OVER |
| assumptions | Interpretation history | 514 | 211 | 2.44 OVER |
| assumptions-emptyprice | Financial assumptions | 391 | 368 | 1.06 |
| assumptions-emptyprice | Impact preview | 391 | 368 | 1.06 |
| assumptions-emptyprice | Interpretation history | 424 | 211 | 2.01 OVER |
| assumptions-recordedv1 | Financial assumptions | 783 | 368 | 2.13 OVER |
| assumptions-recordedv1 | Impact preview | 783 | 368 | 2.13 OVER |
| assumptions-recordedv1 | Interpretation history | 391 | 211 | 1.85 OVER |
| assumptions-version1 | Financial assumptions | 1187 | 368 | 3.23 OVER |
| assumptions-version1 | Impact preview | 1187 | 368 | 3.23 OVER |
| assumptions-version1 | Interpretation history | 514 | 211 | 2.44 OVER |
| finding-evidence | Evidence bundle · Generator support merits review | 903 | 287 | 3.15 OVER |
| finding-evidence | Inspect source lineage | 332 | 100 | 3.32 OVER |
| finding-evidence-notfound | Evidence bundle · Selected Finding | 99 | 287 | 0.34 |
| finding-evidence-notfound | Inspect source lineage | 99 | 100 | 0.99 |
| financials-priced | What happened → what it means in money | 477 | 288 | 1.66 OVER |
| financials-priced | Assumptions in use | 485 | 306 | 1.58 OVER |
| financials-priced | Trade-offs and exclusions | 485 | 306 | 1.58 OVER |
| financials-withheld | What happened → what it means in money | 632 | 288 | 2.19 OVER |
| financials-withheld | Assumptions in use | 358 | 306 | 1.17 |
| financials-withheld | Trade-offs and exclusions | 358 | 306 | 1.17 |
| financials-nofinding | What happened → what it means in money | 103 | 288 | 0.36 |
| financials-nofinding | Assumptions in use | 358 | 306 | 1.17 |
| financials-nofinding | Trade-offs and exclusions | 358 | 306 | 1.17 |
| finding | What happened | 436 | 279 | 1.56 OVER |
| finding | What limits this conclusion | 389 | 233 | 1.67 OVER |
| finding | What to do next | 389 | 233 | 1.67 OVER |
| finding | Where to look next | 511 | 404 | 1.26 |
| finding-stale | What happened | 477 | 279 | 1.71 OVER |
| finding-stale | What limits this conclusion | 468 | 233 | 2.01 OVER |
| finding-stale | What to do next | 468 | 233 | 2.01 OVER |
| finding-stale | Where to look next | 511 | 404 | 1.26 |
| finding-notfound | What happened | 99 | 279 | 0.35 |
| finding-notfound | What limits this conclusion | 119 | 233 | 0.51 |
| finding-notfound | What to do next | 119 | 233 | 0.51 |
| finding-notfound | Where to look next | 99 | 404 | 0.25 |
| finding-history | Revision history | 600 | 243 | 2.47 OVER |
| finding-history-latest | Revision history | 713 | 243 | 2.93 OVER |
| sitefindings | Findings at this site | 560 | 288 | 1.94 OVER |
| sitefindings-empty | Findings at this site | 279 | 288 | 0.97 |
| sitefindings-stale | Findings at this site | 259 | 288 | 0.90 |
| sitefindings-failed | Findings at this site | 259 | 288 | 0.90 |
| sitefindings-unassessed | Findings at this site | 285 | 288 | 0.99 |

**Status: NOT MET.** Most stocked panels are 1.5-3.3x the mock's height. Refused and empty panels are at or under the mock. The height work is the next phase; its plan is in `.agent/W1-F3-findings-money-handoff.md`.

## Known deviations

- The Finding money-view link sits at the right end of the Finding section row. It is chrome, not a panel; the mock has no such link on finding-evidence or finding-history, and the S4-02a bridge test needs it.
- F1 shared API changes are additive only: `ProductStatus inline`, `FindingSections aside`, `.input-row + .input-row` spacing, `.finding-sections*`.

## Open: the 1.3x height rule (added by the coordinator during the build)

This rule is not met yet; see the table above. The slice is not ready for review until a height phase brings the stocked panels within 1.3x and the captures are re-run.

## Residual risk

- jsdom has no layout. Size and prominence claims rest on the captures above.

## User review

W1 UI slice: the build and review can proceed now, and the merge waits for the owner's walkthrough.
