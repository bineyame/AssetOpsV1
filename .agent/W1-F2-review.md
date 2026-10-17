# W1-F2 review (Overview, Dispatch, Analysis, Evidence, Evidence Analysis)

Reviewer: fresh independent Claude reviewer. Revision reviewed: `f3a2f518` (code at `8270c9a6`), base `af1aa23e`.

## Verdict: RETURN

The panel set, order and titles match v69 on all five screens. No leading answer card remains, and the structure tests are sound. Two screens still differ from the mock in layout and prominence:
- On Dispatch, the block chooser sits in the wrong panel.
- On Evidence Analysis, the limits panel is 2.7 to 3.3 times the mock height and still uses the old answer-card styling.

The same inferior styling and repetition the owner objected to also recur across the screens. Findings 1 and 2 are High under the contract; findings 3 to 6 are Medium. All of them block.

## Findings

1. **High: the Dispatch block chooser is in panel 2, and panel 1 is a near-empty strip.** `frontend/src/sites/PerformanceDispatch.tsx:453-497` (`PeriodsAndBlocks` rendered at :476, block row at :873-887).
   - In the mock, panel 1 "Sources and 15-minute blocks" carries the main visual: a chart above a row of large selectable 15-minute tiles. The Selected block panel opens with the block's outcome badge, one sentence and a fact table.
   - In the app, panel 1 has only a thin day bar followed by about 250 px of blank space. The period chips and the clickable block row sit in panel 2, so the screen shows two block strips.
   - Panel 2 is titled with a block (04:00-04:15, Needed) but leads with the *period* outcome, "Possibly avoidable", over 03:45-09:15. A user reads the wrong outcome for the selected block.
   - Fix:
     - Move `PeriodsAndBlocks` (period chips and the block row) into panel 1 under `DayBlockStrip`, and size the tiles like the mock's.
     - Start panel 2 with the selected block's outcome badge and one sentence.
     - Show the period facts after that, under a label naming the period, or drop them to the Analysis view.

2. **High: the Evidence Analysis "How each limit is set" panel is 2.7-3.3x the mock and does not look like it.** `frontend/src/sites/EvidenceClaimLimit.tsx:301, 348-350, 392-399, 521`; `LedgerSiteEvidence.tsx` panel 2 wrapper.
   - The extra height is not honest-state that has to stay visible. It is:
     - a second date chooser, styled as a native unstyled `<input type=date>` plus a bare `<button>` (:348-350), on a page that already has a From/To chooser;
     - leftover W1-UX answer-card styling, `headline-card__question` (:521), showing as the uppercase "WHAT CAN THESE READINGS SUPPORT?";
     - an h3 "What the readings can support" (:301);
     - 16 px period links;
     - the "This page states what arrived..." note, which repeats the Evidence Overview.
   - Fix:
     - Move the day and period chooser into the page's `.v69-chips` row, using `.v69-chip-control` and `.button`.
     - Delete the `headline-card__question` label and the duplicate "This page states..." line.
     - Keep visible: the mock's two paragraphs, the one-line result sentence with its inline state, the "Not available yet" rule line, and the Dispatch link.
     - Keep the two technical disclosures closed.
     - Target about 1.3x.

3. **Medium: the same state line is repeated, with mixed type sizes (the owner's "styled inferior" complaint).**
   - Where:
     - `SiteWindowOverview.tsx:241-260`: the Overview panel 1 freshness `ProductStatus` repeats the statusbar word for word.
     - The Needs attention list state, rendered by `OverviewFindingList`, repeats it a third time.
     - On the money panel the inline `ProductStatus` wraps to two grey lines at body size.
     - Evidence panel 1 has a grey "Readings received and accepted ... As of" block that restates the statusbar, plus a 15 px bullet among 11 px notes.
   - Panel 1 also shows two identical "How this was worked out" disclosures.
   - These lines are why Overview "happened" is at 1.54x, money at 1.41x and Evidence "conclude" at 1.46x.
   - Fix:
     - Drop the in-panel state line wherever its state and as-of equal the statusbar's. Where they differ, render it as one `ChartNote`-size line.
     - Keep only the "source is open" sentence.
     - Merge the two disclosures into one.
     - Set the Evidence bullet to note size.

4. **Medium: the Needs attention panel is not structured like the mock's list.** `frontend/src/sites/OverviewFindingList.tsx:390` and the chosen-Finding block above it.
   - The mock shows a numbered list, each item with a title, a one-line reason and a link.
   - The app shows a 16 px chosen-Finding link and a disclosure, then an h3 "Findings for {date}", a state strip, a large count sentence, a one-item list of the *same* Finding, and a note explaining that they are the same.
   - Fix:
     - Render the mock's numbered item list.
     - Omit the separate chosen-Finding line when it is list item 1, and with it the "same Finding" note.
     - Keep one closed reference disclosure.

5. **Medium: internal vocabulary appears on screen.**
   - (a) `SiteWindowOverview.tsx:568` renders the backend `gaps_reason` verbatim, which shows "No reviewed gap rule exists for the Site context; coverage counts and the selected S3 coverage are shown instead." Fix: map the reason to plain words, for example "No rule yet says which gaps matter here; the reading counts are shown instead". Never render the raw string.
   - (b) The Evidence and Evidence Analysis tables show raw source and channel IDs, for example "generator-controller · generator-controller / status", "battery-pcs-controller" and "fuel-level-sensor", plus the raw enum "STOPPED state". Fix: use the configured source label, or a humanised ID shown once, with the role words already in `dispatchWords.ts`, and a plain state word.
   - (c) `LedgerSiteEvidence.tsx:1107` reads "the server refused ... operational audit record". Fix: "A delivery that was rejected as a whole is kept for audit and not listed as a reading."

6. **Medium: the Analysis panel 3 contradicts itself.** `PerformanceDispatch.tsx:1540-1549`.
   - When `read.unavailable.alternatives` and `result.alternatives` are both present, the panel shows "Other explanations: Not yet available." and then "Other explanations: 3 recorded". This was inherited from main, but it sits in the rebuilt panel.
   - The fallback term "Another result" also tells the user nothing.
   - Fix: suppress the unavailable row for `alternatives` when recorded alternatives exist, and give every unavailable key a named term (no "Another result" fallback).

7. **Low (does not block).**
   - (a) The Evidence Analysis records panel is 1.82x the mock. Three rows plus "Show all" is fine. Fold "Readings not accepted" into one note line plus one closed disclosure (merge its two "Advanced details" disclosures), and set "Show all / Next page" to note size.
   - (b) The day chooser sits above the statusbar on Dispatch and Evidence, but below the cards on the Overview. Pick one position.
   - (c) The Overview operating-context timeline lists "Feeder demand" three times. Disambiguate by source.
   - (d) The Analysis panel 1 nests three cards in 15 px text inside the panel, unlike the mock's single table rhythm.
   - (e) The 390 px Dispatch coverage table clips its fourth column. Confirm it scrolls.
   - (f) Dispatch coverage at 1.42x is acceptable, because its recorded limitations are honest-state.

## Panel-height judgement (packet's six deviations)
| Deviation | Verdict |
| --- | --- |
| Overview "happened" 1.54 | Cut the duplicate state line and the second disclosure (F3). The rest is honest-state. |
| Overview money pair 1.41 | Make the state one note line (F3). Keep the source-data line. |
| Dispatch coverage 1.42 | Accept. |
| Evidence "conclude" 1.36-1.46 | Cut the duplicate state block (F3). |
| Evidence Analysis records 1.82 | Low (F7a). |
| Evidence Analysis limits 2.7-3.3 | Not justified. Move the chooser and remove the remnants (F2). |

## Checks run (by me)
- `npx.cmd tsc --noEmit -p .` returned exit 0.
- I ran 8 focused vitest files, 277 tests, all passed (88 s):
  - `performanceDispatch`, `s2LedgerEvidence`, `siteEvidenceScreen`, `s5SiteWindowOverview`, `siteOverviewScreen`, `siteFoundationRevision`, `t028Screens`, `panelStructure`.
  - Vitest did run in this PowerShell session, so the known esbuild sandbox failure did not occur.
- I did not run the full suite. I cite the implementer's run: 1984 passed, 0 failed, at `8270c9a6`, which is the code revision under review.

## Other checks
- **Assertions:** I spot-checked removed lines in the diff. Each one is re-pointed to the content's new home, with at least as much asserted. For example, the "Overview unavailable" heading became the page-refusal check, plus `expectV69Panels` and in-panel gap text. `expectV69Panels` covers:
  - Overview: legacy populated, empty and unavailable; the imported day; awaiting migration.
  - Dispatch and Analysis: stocked, empty, and three refusals.
  - Evidence and Evidence Analysis: ledger stocked, NO_DATA, REJECTED_ONLY, unavailable and not-found; legacy stocked, empty and unavailable.
- **Commit `a09a8a12`:** it touches only `.agent/` (captures, `evidence.json`, `index.html`, packet tables). The dispatch index revision `ff1bc248` matches the packet. No source change, so it is harmless.
- **Captures viewed:** the 1440 pairs for Overview p01, Dispatch supported, Analysis limited, Evidence stocked and Evidence Analysis limited; the 390 pairs for Overview p01 and the Dispatch supported app capture.
- **Not verified:** the other 1440 and 390 pairs, and the legacy-Site paths, which have no captures.
