# post-W6 W2-cold independent review

Reviewer: fresh Claude reviewer (not the author). Branch `task/post-W6-W2-cold`, head `ee329b03`, product `8bfd4730`.
Diff reviewed: `git diff main...HEAD -- ':!.agent'` (merge-base `09196de0`, 17 files). Governing: `post-W6-W2-cold-rulings.md`
(cross-card ownership 1-8, Q0-Q15, per-ID list), `post-W6-W1-rulings.md` cross-card contract, the W2-cold card in
`post-W6-audit/fix-slices.md`, `ui-ux-decision-guide.md`, v69 mock.

## Verdict

**ACCEPT-with-findings.** One Medium (fix on the branch, or get an Architect ruling that cold Site pages are exempt) and three
Lows. Every other ruling checked is implemented as written. The tests prove the behaviour: three single-file reverts each
made the expected tests fail.

## Findings (ranked)

### M1 (Medium, acceptance gap): refused cold Site pages have no technical disclosure (ruling 5)

- Where: `frontend/src/sites/coldSiteViews.tsx:300-313` (`RefusedGap`). It is used as the first-panel refusal at :671
  (cold), :919 (cold-evidence), :1235 (cold-evidence-analysis), :1428 (cold-financials) and :1630 (cold-assumptions).
- What is wrong: cross-card ruling 5 says each refused Site page shows "one in-panel sentence and a technical disclosure".
  `RefusedGap` shows only the sentence, plus Retry on a 503. `coldSiteViews.tsx` contains no `ExactReferences`, so none of
  the five cold Site screens in R261 gives the refusal code anywhere.
  - Temperature and Backup (`RefusalReferences`, `ColdAssessmentViews.tsx`) and the new cold Findings index do follow the rule.
  - So do W2-EV's pages (`EvAssessmentViews.tsx` `RefusedGap`).
- Failure scenario: open `/sites/COLD-…?from=<later>&to=<earlier>` on Overview, Evidence or Financials. The page shows
  "The selected window needs both a start and an end, with the start before the end." There is no disclosure with
  `COLD_WINDOW_INVALID` or the requested bounds. A 403 or 503 likewise gives no code. The packet marks ownership 5 "done".
- Why it matters: the ruling defines one refusal set across mini, cold, EV and estate, and cold Site pages are the only
  ones that differ.
- Fix: render the existing `RefusalReferences` (or an equivalent `ExactReferences variant="tech"`) after the
  non-`repeat` sentence in `RefusedGap`. Add one assertion to `expectSentenceOnce` or the r261 cases. Alternatively,
  get a ruling that these pages are exempt.

### L1 (Low): Financials can hide a different read's refusal sentence

- Where: `coldSiteViews.tsx:1538`, `repeat={refused !== null}` on "Assumptions in use".
- What is wrong: the panel belongs to a separate read (`sRefused`). When the financials read and the assumptions read are
  refused for different reasons, the panel says only "Not assessed". For example, financials returns 503 and assumptions
  returns 403. The assumptions-specific reason then appears nowhere on the page.
- Fix: repeat only when the two reads give the same sentence, e.g. `repeat={refused !== null && refused.sentence === sRefused.sentence}`.
- This does not happen for a window refusal, because both reads refuse with the same code. That makes it an edge case,
  not a blocker.

### L2 (Low): cold Findings strip count is per page when a cursor is present

- Where: `ColdAssessmentViews.tsx:1294`. The count is `open = r.items.filter(SUPPORTED)`.
- What is wrong: with `next_cursor !== null` the strip says "Scoped to … · n open", counted from the first page only. The
  note "Showing the first {n} Findings; paging is not available on this page." sits under the table, away from the count.
- Fix (optional): qualify the count when a cursor exists, e.g. "n open in the first {k}".
- Q3 rules "`SUPPORTED` counts open" without addressing paging, so this is residual risk rather than a ruling breach. It
  cannot be produced (cursor is a named producer gap).

### L3 (Low, evidence): the stricter cap probe is 4 px over at 1440

- Where: packet Caps table. With the episode line also at 160 characters the cold Findings panel is 554 / 606 px, against
  the 550 / 850 cap.
- Why it is Low: the episode line is built from a timestamp (`episodePeriod`, :1251-1256), so it is a fixed-format typed
  value. Guide §1 says "keep fixed typed values", so the ruled case is the one the builder measured: titles at 160
  characters plus the longest gap, 539 / 786.
- Fallback order: the fallback followed guide §1. It only changed wrapping and column width (8 px padding, a 34rem desktop
  title column at `w2-cold-assessment.css:187`, a block episode line). No row or value is hidden, clamped or ellipsized,
  and the 390 table keeps its focusable scroller.
- The packet records this as informational, which is correct. No Architect cap request is needed.

## Already with the Architect (evidence only)

The cold Finding refused-window page shows the sentence 3 times: in the `PageRefusal` block, in Bounded conclusion and in
Operational context (`ColdAssessmentViews.tsx:1210-1213`). r3 `summary-r3.json` records `sentenceTotal: 3` at both widths
for `start-refused-window`. Q4 ("the Finding keeps its established section form") and ruling 5 ("no duplicate page
banner") conflict here. Not scored.

## Ruling-by-ruling check

- **Ruling 5 / Q5 copy:** exact strings match the rulings.
  - `WINDOW_REFUSAL_BODY` (`ColdAssessmentViews.tsx:57-61`) covers `COLD_TIME_INVALID`, `COLD_WINDOW_INVALID` and `COLD_WINDOW_TOO_LONG`.
  - Any other 422 gives "The selected window is invalid."; the title is "Window cannot be read"; the key stays `invalid-window`.
  - The strip chip uses `refusalText().title`, so a 403 or 503 is never called a window error.
- **Q4:** Temperature and Backup show `RequestedWindowBar` (none for an invalid window), the strip and four `Not assessed`
  tiles. Panel 1 has the sentence and the `cold-refusal-references` disclosure. `PageRefusal` is removed. The duration
  callout is hidden unless the read loaded.
- **Cold Findings branch (ownership 1-2, Q1-Q3):**
  - It is a `COLDCHAIN` branch layered before the EV and mini branches (`SiteAnalyticsFrames.tsx:500-511`), plus a one-line
    `coldAssessment` prop in `App.tsx`. There are no EV client imports.
  - `ColdFindingIndex` has the 7 columns, `LensChips`, strip copy, empty, no-assessment, cursor and refusal states and windowed links.
- **Site time:** cold Analysis uses the canonical `sites/siteTime.ts` (`siteTime`, `siteZoneAvailable`, `siteZoneLabel`)
  through `ColdTimeCell`. `eatTime` is main's W2-EV wrapper over `siteTime`, unchanged by this branch, so nothing is
  duplicated. The missing-zone header is `(UTC; Site time zone unavailable)`, as guide §4 asks.
- **Q6-Q11 and R245-R258:** implemented as ruled: units in `<small>`, the claim link, the Maintenance card, the chain join
  by `evidence_id` with ok/danger tones, the "steps above" copy, the normal-gap copy, the SLD link, deduplicated
  limitations, Portfolio evidence and "Review cooling →".
- **Tabs (ownership 3):** `coldTabSearch` returns undefined for non-cold Sites, and the mini test asserts no `known_at` on
  its tabs. `operatorSiteTabs.tsx`, `SiteFoundationFrame.tsx`, `SiteFindingIndex.tsx` and `siteTime.ts` are not edited.
- **Merge `38fdff6d`:** the three-dot diff of the shared files has only cold hunks, so shell, W1-a, W1-b, W2-EV and W6
  changes are intact.
  - Since then, main has moved to `0cfe43b3`.
  - A trial merge (`git merge-tree`) conflicts only in `.ai/CODE_STATE.md`. `App.tsx` and the register auto-merge.
- **Register:** R435-R437 sit in the W2-cold block (R435-R449), each with a visible `MOCK DEVIATION D1 (Rnnn)` label next
  to the change, asserted in tests.
- **Guards:** no guard file changed. One `productVocabulary.json` allow-entry was added, for the exact mock text "Inspect
  temperature claim" (ruled Q7, scoped to that string). That is a sanctioned exception, not a loosening.
- **Updated W2-04 tests:** the 403/503 cases moved from "sentence in every panel" to `expectSentenceOnce`. The helper
  asserts the sentence is in panel 1, that later panels say `Not assessed` without the sentence, and that the whole-page
  count is 1. This is exactly ruling 5, not weaker. The `[data-page-refusal]` assertion is narrowed to cold-finding and
  replaced by checks on the strip, title, 4 tiles and disclosure.
- **Recapture:**
  - r2 (`47d7929c`): 116 rows, which is 92 indexed cold pairs plus 16 URL-only, 2 excursion-rep, 2 tabs-known_at, 2 EV
    and 2 mini. It shows 0 overflow, 0 clipping and 0 console errors (my tally of `summary.json`).
  - Product changes after `47d7929c` (`7beb5f72`, `8bfd4730`) touch only refused paths and the missing-zone header, and r3
    (`8bfd4730`, 34 refused captures, 32 pass) covers the refused paths. So the r2 loaded captures still represent the product head.
  - The packet names what cannot be produced: cursor, pending/stale, 403/503, an unmatched step and the "Not determined" wrap at 390.
- **Stray files:** none. The non-`.agent` diff is 17 source/test/doc files; there is no `.venv`, `node_modules`,
  `__pycache__`, `var/` or `dist/` anywhere in the diff.

## Checks I ran (worktree `AssetOpsV1-ops04`, head `ee329b03`)

| Check | Result |
| --- | --- |
| `npx.cmd vitest run` coldFindingIndex, coldRoutes, coldSiteViews | 3 files, 137 passed |
| `npx.cmd vitest run` s404SiteFindingIndex, evFindingIndex (mini/EV regression) | 2 files, 46 passed |
| `npx.cmd tsc --noEmit` | exit 0 |
| `tools/check-all.ps1 -Python <main .venv>` | All 11 guards passed |
| Revert proof 1: cold branch condition set to `false` | 7 coldFindingIndex tests fail; mini test still passes |
| Revert proof 2: Excursion-context gap back to the sentence | 4 `r261_refusal_copy` cases fail |
| Revert proof 3: strip join outcome nulled | `r255_steps_join_outcomes_by_record_in_order` fails |
| Restore | `git checkout --` the three files; `git status` clean |

Not run (per dispatch): full vitest, build, captures, backend suite (no backend change). For those I rely on the packet: full
vitest 134 files / 3211 passed and build ok at `8bfd4730`. I could not verify those numbers.
