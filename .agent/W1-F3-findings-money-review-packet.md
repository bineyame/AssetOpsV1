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
  - Notices carry `.notice`. The Assumptions notice follows its panel pair. The mini `assumptions` mock (screens.js:338) puts its notice first; that notice is mock-only meta, so the app keeps its own notice after the pair (review L11: wording corrected).
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

The pre-height-phase table is superseded by "Height phase" below (its "Before" column).

## Known deviations

- The Finding money-view link sits at the right end of the Finding section row. It is chrome, not a panel; the mock has no such link on finding-evidence or finding-history, and the S4-02a bridge test needs it.
- F1 shared API changes are additive only: `ProductStatus inline`, `FindingSections aside`, `.input-row + .input-row` spacing, `.finding-sections*`.

## Height phase (coordinator's 1.3x rule)

Commits after `50ff8fa4`: `5e6e170a`, `f1c48973`, `f7a14429`, `92dfe93d`, `136f8e6e`, `6e364cac`, `08979345`, `cbf8819a` (captured), and `d79a9705` (fixes the singular "1 price" and stops the Finding version label wrapping; CSS and copy only).

### What changed, by screen
- **Shared, additive:**
  - `ShowAll` (`ui/Disclosure.tsx`): a plain "Show all N" expander. Its content stays mounted, so every row stays in the document.
  - `Disclosure variant="inline"`: the summary reads as one small link on a row's link line.
  - `.v69-state-line`: the state sentence, scope and "as of" on one compact line (`ProductStatus inline`).
  - `.v69-step-line`: a step strip shown as one line of marks. A step that is not done keeps its detail visible.
- **finding-history:**
  - The state shows as one line, and only the latest 3 versions show.
  - The earlier versions sit oldest first behind "Show all N versions (M earlier)", placed above the visible table, so the document order stays 1..N.
  - The expander opens by itself when the selected version is one of the hidden ones.
  - Each row has two lines. The per-row "Times and references" disclosure is now an inline link.
- **finding-evidence:**
  - The bundle shows the state line, the input table and one gap line, which holds both registered MissingClaims.
  - The counts, sources, cited-record pages and assessments are in one closed "How this was worked out". It opens by itself on a later page or when a record is selected.
  - The demonstration note stays visible.
  - The lineage trail is one step line, and broken steps stay visible. The links moved to the panel head.
- **assumptions:**
  - The pair is `align-items: start`, so Impact preview no longer stretches.
  - The state shows as one line.
  - The strip and the full schedule sit behind "When each price applies (N prices)".
  - "Where this version applied (N)" is now an expander.
  - The edit reason is shorter. The registered gap is unchanged and still says "signed-in operator".
  - Price history shows the latest 3 plus "Show all". The "How these times are read" disclosure is an inline link.
  - The contradiction is fixed: an empty fuel cost history beside listed price versions now adds, on the same line, "The price versions below are prices only; no fuel cost was worked out from them by this moment."
- **financials:**
  - The bridge state shows as one line. The withheld limits, the record link and the source/pending notes are 12px. The next step appears once.
  - Assumptions in use shows price, effective period and set-by. Version, currency and basis sit in the closed "How this was worked out".
  - Trade-offs and the method notes are 12px.
- **finding:**
  - The state shows as one line.
  - Three limits show and the rest sit behind "Show all N limits". The record-gap and series-limit lines are moved ahead of the others so they stay in the first three.
  - For a supported version, the lifecycle sentence moves inside the expander. A non-supported one, and "What could change it", stay visible.
  - "Open the recommendation" is a primary button. The pair is aligned to start.
- **sitefindings:**
  - 3 rows show, plus "Show all N Findings on this page".
  - The repeated amount sentence is now "Not in this list" in the cell, plus one gap note.
  - Related Findings sit inline. A same-day period names the day once. The day strip is one step line.

Every money gate is unchanged. No condition that decides whether an amount, price or default is shown was edited. Only the layout and the copy around them changed.

### Assertions: none of the existing ones changed or weakened
Every pre-existing test passed unchanged. The full list stays reachable, because hidden rows stay mounted inside `<details>`. The new tests below assert the default view and that every hidden item is still reachable:
- `siteFindingHistory`:
  - latest 3 shown, and versions 1..202 reachable in order behind a closed expander;
  - the state, completeness and no-replay lines visible;
  - a hidden selected version opens the expander;
  - no expander for 3 or fewer versions.
- `siteFindingEvidence`: the bundle's default reading is the state line, the input table and both MissingClaims, with the detail in one closed disclosure; a broken step and the named broken links stay visible.
- `siteFinancials`:
  - prices-only clarifier;
  - strip and schedule reachable behind the closed expander, with the state, price and disabled edit visible;
  - price history: latest 3 visible, the rest reachable in order;
  - Assumptions in use: 3 key values visible, 3 in the closed disclosure.
- `siteFinding`: (superseded by review fix round H1) every material limit visible; only the access note and the SUPPORTED lifecycle sentence in the closed expander; could-change visible; primary button.
- `s404SiteFindingIndex`: 3 rows visible, 5 reachable in the read's order, one visible amount note.

Copy edits that existing tests still match as substrings: the history no-replay line and the evidence lineage-complete line are shorter.

### Checks (height phase)
- `npx.cmd tsc --noEmit`: clean at `d79a9705`. The production build passed at `08979345`.
- Full `npm.cmd test`:
  - At `08979345`: 77 files, 2014/2014 passed.
  - At `cbf8819a`: 2013/2014. The one failure was `s404SiteFindingIndex` "changing the dates writes a new window" (a date-input value under load, in code this phase did not touch), and the file passes 36/36 on its own.
  - At `d79a9705` (copy and CSS only after that): `siteFinancials` and `s404` pass 118/118.
- `tools/check-all.ps1`: 10/10 guards passed at `08979345` and again at `d79a9705`.
- Captures:
  - Round 2 used `node tools/w1-fidelity-evidence.mjs` at `cbf8819a`, 1440 and 390. Evidence is in `.agent/W1-F3-evidence-height2/part{5,8,9,10,10-emptyprice,11}`, and round 1 is in `.agent/W1-F3-evidence-height/`.
  - 29 cases on unused ports (97xx/57xx, CDP 9773). Prepares ran one at a time, which avoided the Postgres "too many clients" cap.
  - 288/288 tool claims passed. The panel count matches the mock in every case at both widths, and overflowX is 0 at 390 everywhere.
  - Screenshots were checked for "could not be read" states, because the tool passes those when the titles still match.
  - All fixtures were dropped and every server stopped.

### Panel height at 1440, app vs mock at `cbf8819a` (OVER = above 1.3)
| Screen-case | Panel | Before | App px | Mock px | Ratio |
| --- | --- | --- | --- | --- | --- |
| finding-evidence | Evidence bundle | 903 | 414 | 287 | 1.44 OVER |
| finding-evidence | Inspect source lineage | 332 | 175 | 100 | 1.75 OVER |
| finding-evidence-notfound | both | 99 / 99 | 99 / 99 | 287 / 100 | 0.34 / 0.99 |
| financials-priced | What happened → money | 477 | 374 | 288 | 1.30 |
| financials-priced | Assumptions in use | 485 | 275 | 306 | 0.90 |
| financials-priced | Trade-offs and exclusions | 485 | 424 | 306 | 1.39 OVER |
| financials-withheld | What happened → money | 632 | 443 | 288 | 1.54 OVER |
| financials-withheld | Assumptions / Trade-offs | 358 / 358 | 275 / 295 | 306 / 306 | 0.90 / 0.96 |
| financials-notcalculated | Bridge / Assumptions / Trade-offs | 477 / 358 / 358 | 374 / 275 / 295 | 288 / 306 / 306 | 1.30 / 0.90 / 0.96 |
| financials-notworkedout, -emptyprice | Bridge / Assumptions / Trade-offs | 525 / 313 / 313 | 374 / 227 / 295 | 288 / 306 / 306 | 1.30 / 0.74 / 0.96 |
| financials-nofinding, -notfound | Bridge / Assumptions / Trade-offs | ≤103 / 358 / 358 | ≤103 / 275 / 295 | 288 / 306 / 306 | ≤0.36 / 0.90 / 0.96 |
| finding | What happened / Limits / Next / Where | 436 / 389 / 389 / 511 | 338 / 304 / 179 / 502 | 279 / 233 / 233 / 404 | 1.21 / 1.30 OVER (1.305) / 0.77 / 1.24 |
| finding-stale | What happened / Limits / Next / Where | 477 / 468 / 468 / 511 | 357 / 326 / 179 / 502 | 279 / 233 / 233 / 404 | 1.28 / 1.40 OVER / 0.77 / 1.24 |
| finding-notfound | four panels | 99-119 | 99-119 | 233-404 | 0.25-0.51 |
| finding-history | Revision history | 600 | 396 | 243 | 1.63 OVER |
| finding-history-latest | Revision history | 713 | 475 | 243 | 1.95 OVER |
| sitefindings | Findings at this site | 560 | 435 | 288 | 1.51 OVER |
| sitefindings-empty / stale / failed / unassessed | Findings at this site | 259-285 | 179-205 | 288 | 0.62-0.71 |
| assumptions | Financial assumptions / Impact preview / Interpretation history | 913 / 913 / 514 | 506 / 256 / 335 | 368 / 368 / 211 | 1.38 OVER / 0.70 / 1.59 OVER |
| assumptions-emptyprice | same | 391 / 391 / 424 | 295 / 256 / 326 | 368 / 368 / 211 | 0.80 / 0.70 / 1.55 OVER |
| assumptions-recordedv1 | same | 783 / 783 / 391 | 527 / 256 / 251 | 368 / 368 / 211 | 1.43 OVER / 0.70 / 1.19 |
| assumptions-version1 | same | 1187 / 1187 / 514 | 584 / 256 / 335 | 368 / 368 / 211 | 1.59 OVER / 0.70 / 1.59 OVER |

**Status: improved but not fully met.** Every stocked panel is shorter, with the worst at 1.95x (it was 3.3x), and refused and empty panels are at or under the mock.

Twelve rows are still OVER, from 1.305x to 1.95x. In each case the remaining height is content the brief says must stay visible: the compact state line, honest-state lines, registered gap lines, the exact-reference link, and the mock's own form rows. Going further would mean hiding one of those. That is a call for the coordinator or the Architect, not for me:
- **finding-history (1.63-1.95x):** the mock has a bare 3-row table. The app adds the state line (with "latest at read / keep this exact version"), the completeness line, the no-replay line and the references link.
- **finding-evidence lineage (1.75x, 175 px against 100):** the trail line, the trail claim, the "choose a record" gap line and the references link.
- **assumptions Interpretation history (1.55-1.59x):** the state line, the fuel-cost empty line with the prices-only clarifier, and 3 price versions instead of the mock's 2 rows.
- **assumptions Financial assumptions (1.38-1.59x):** the mock's two field rows, plus the in-use line, the selected-version line, the disabled edit with its registered reason, and the expanders.
- **The rest (1.39-1.54x):** sitefindings, the withheld bridge, priced trade-offs, and the finding limits in the stale case.

Not re-captured after `d79a9705`. That commit only changes one word and a `white-space: nowrap`, and can only shorten the sitefindings rows.


## Review fix round (`.agent/W1-F3-review.md`, RETURN at `a5e961fc`)

Commits `def88117`..`de19aeff` on the branch. Money gates untouched: `FindingConsequence.tsx` `shown`/`gated`, `BridgeTable current`, NO_PRICE/CONFLICT paths and `recorded_amount.disposition` are unchanged by every fix commit.

| # | Sev | Fix | Commit |
| --- | --- | --- | --- |
| 1 | High | `LimitList` renders every material limit visibly (bounded line, record gap, series limit, every `groups` item, stops, recurrence), each shortened to one sentence; only the development-access note and the SUPPORTED lifecycle sentence sit in `details[data-show-all='finding-limits-context']`. New test "with many limits, every material limit is visible" (4 limitation groups + gap + series + stops, 9 visible items). | `def88117` |
| 2 | High | Sitefindings: Domain ("Dispatch"), Priority and Confidence ("Not assessed", muted dashed badge) columns; Lens deferred to F5. Finding strip: Priority/Confidence "not assessed" chips. Financials: bridge Confidence column and "Data confidence: not assessed" chip. | `def88117`, `6a9557d0`, `80eb9f4f` |
| 3 | High | Interpretation history price versions are a `DataTable` (Version, Diesel price, Effective, Set by / why, Status + "Open version N"); "Prices as recorded then" moved into the row's exact reference. | `3960f44c` |
| 4 | Med | State said once: Finding panel keeps only source clause + as-of; Financials drops the "Modelled potential…" line and the duplicate "Why no current amount"; History one state line ("Latest recorded version when read · Version N of M · As of … · Keep this exact version"), completeness sentence dropped when complete (`data-history-complete` now marks the headline); Evidence one sentence, version said once in the scope; Sitefindings drops the in-panel amount note, "Showing N of N", and the one-day strip. | `def88117`, `6a9557d0`, `80eb9f4f`, `9aaa8c05` |
| 5 | Med | One disclosure per panel: Financial assumptions merged; Financials range method and counted readings folded into the bridge's disclosure (`ExactReferences extra`, additive); Finding Evidence exact references moved into the bundle's one disclosure, lineage panel has none. | `80eb9f4f`, `3960f44c`, `9aaa8c05` |
| 6 | Med | Evidence bundle Source column: "Source not named" / "N sources, not named" / "No source recorded" (the read carries no source label); IDs moved to the disclosure's reference list ("<Input>: source references"). | `9aaa8c05` |
| 7 | Med | Empty Interpretation history: one state line "No fuel cost version recorded by this moment; the price versions below are prices only." No "Every amount here…" when empty. | `3960f44c` |
| 8 | Med | Lineage: complete-trail sentence deleted (step line only, `data-evidence-lineage-complete` on the wrapper); no-record line reworded to "Open 'How this was worked out' above and choose a record to follow its trail."; one head link ("Back to this version of the Finding"). | `9aaa8c05` |
| 9 | Med | Sitefindings off-screen cells `white-space: nowrap`; Related moved under the Finding title. Re-captured at 390 (below). | `6a9557d0` |
| 10 | Low | Inline status: space before the provenance disclosure; bound starts with no separator. | `def88117` |
| 11 | Low | Packet wording on the Assumptions notice corrected (above). | this packet |
| - | coord. | Inline state line never a grey box: local reset of `.status-strip__state.product-status`, `--inline` and every tone (padding, border, background) and inherited sizes; F2 fixes the shared CSS separately. | `3960f44c`, `de19aeff` |
| H-table | - | Finding History: row "Open this version" and "Check their record trail" dropped (row keeps "Select version N" · "Its evidence" · "Times and references"); head keeps one link. | `9aaa8c05` |

### Re-pointed assertions (none weakened)
- `siteFinding`: the "at most 3 limits / Show all N" assertions are replaced by the stronger "every material limit visible" set (H1 asked for the opposite behaviour). State-line checks moved to `expectFindingStateVisible`, which still asserts label, sentence (non-positive) and as-of visible outside any closed disclosure; the scope's version/period moved to the strip (M4).
- `s404`: amount-note count 1 -> 0 with every row's "Not in this list" and the notice asserted instead; the one-day day strip is asserted absent while the Period cell is asserted to name the day; the two-day case still asserts 2 steps.
- `siteFinancials`: eyebrow price text -> the version's field value; "Showing 2 of 2" -> asserted absent; empty history line -> the state sentence; `financials-why` non-empty -> non-empty only when it adds a stored reason, else absent, with the state sentence asserted visible and >20 chars; disclosure counts 2 -> 1 per panel, and 4 for the history table (one per row).
- `siteFindingHistory`: "All 205 recorded versions are listed" -> `[data-history-complete]` on the headline "205 recorded versions…"; "version N" -> "Version N of M" in the scope; row Finding link and `data-history-check-evidence` -> asserted absent, with the head link and the row's `data-history-evidence-link` asserted on the same exact IDs; `data-history-open-evidence` -> absent, with the selected row's evidence link asserted.
- `siteFindingEvidence`: latest-at-read text -> scope "Version 2 of this Finding" plus label "Latest recorded version when read"; exact references -> last element of the bundle disclosure body, same six labels first, plus source-reference rows; lineage panel asserted to have no `details`; new M6 assertion that no input Source cell holds a `code` ID; disclosure vocabulary scan moved from lineage to bundle (count still 1).

### Fix-round deviations
- Finding History keeps one panel-head link ("Open version N of the Finding"). The review's height table asked to drop the head links as duplicates of row links, but with "Open this version" dropped from rows (same table) the head link is the only way to the Finding at a version; the head evidence link is dropped.
- Sitefindings Lens column waits for F5, as the review allows.

## Residual risk

- jsdom has no layout. Size and prominence claims rest on the captures above.
- `ShowAll` keeps hidden rows mounted; a very long list (205 versions) still renders every row in the DOM, as before.

## User review

W1 UI slice: the build and review can proceed now, and the merge waits for the owner's walkthrough.
