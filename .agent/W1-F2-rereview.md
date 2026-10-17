# W1-F2 re-review (fix round)

Reviewer: fresh, independent Claude reviewer. Revision: `f2163bef` (code at `73cb5a54`). Fix diff: `5934b841..f2163bef -- frontend`.

## Verdict: RETURN

H1, M4, M5 and M6 are fixed, and so are Lows 7b, 7c and 7e. The structure tests are sound and no assertion was weakened. Two Medium findings block:

- **Finding 1:** the remaining causes of the Evidence Analysis limits panel's excess height (2.16-2.45x). This includes my decision on the three disclosure rows: merge them.
- **Finding 2:** the in-panel inline state line still renders as a grey, wrapping, mixed-size box on three panels. M3's money part is therefore not fixed on screen, although the code adds the note class.

Both fixes are small and CSS/markup-local.

## Findings

1. **Medium: the Evidence Analysis limits panel still carries non-mock bulk.** Locations: `frontend/src/sites/LedgerSiteEvidence.tsx:1488-1510`, `frontend/src/sites/EvidenceClaimLimit.tsx:446-454` and `:559`.
   - **The panel has three closed disclosures in a row.** They are `claim-limit-detail` (rendered inside the result), `evidence-limit-list` and `evidence-analysis-technical`. That breaks the one-disclosure-per-panel rule, and the not-available line sits between them.
   - **A material limit is behind a closed disclosure.** The fix moved the physical-capacity caveat ("not the equipment's physical capacity; configured ratings are not treated as observed") into the closed `claim-limit-detail`. `architect-W1-fidelity.md:13` says a closed disclosure cannot hide a material limit.
   - **The no-selection state (2.45x) is still the old block card.** It shows a 16 px `ProductStatus` card, "We have not checked this period / No assessment exists for this period...". It then shows "No assessment selected · As of: time not recorded", then a 16 px "Choose a day... Nothing is concluded until an assessment is chosen."
     - It says "nothing is concluded" twice.
     - "No assessment exists" contradicts the chip row's offer of assessed periods.
   - **Decision: merge the three rows into one.** Exact fix:
     - (a) In `ClaimLimit`, render one closed outer disclosure as the panel's last child, after `NotAvailableYet`: `<Advanced name="evidence-limit-details" summary="Advanced details — what limits it, how what can be said is narrowed, analysis status and earlier store">`. Inside it, in this order:
       - an empty slot `<div ref={setDetailSlot} data-claim-limit-detail-slot />`;
       - the existing limit-list content, keeping the inner `evidence-limit-list` `Advanced`, or as a plain list;
       - the existing `technical` node, which keeps its inner `evidence-analysis-status`, `evidence-comparison` and `evidence-gateway` disclosures.
     - (b) Give `EvidenceClaimLimit` a `detailTarget?: HTMLElement | null` prop, the same pattern as `chooserTarget`.
       - When the target is set, `Loaded` portals the detail *content* (RoleStrip, reasons, earlier versions, references) into it, without its own `Disclosure` wrapper.
       - When the target is `undefined` (standalone use and `evidenceClaimLimit.test.tsx`), it keeps the `claim-limit-detail` disclosure as now.
     - (c) Move the physical-capacity sentence out of the disclosure and keep it visible. Append it to the mock's second paragraph (`[data-evidence-limit-note]`) as one more sentence.
     - (d) Render the no-day, unavailable and refused states as one note-size line. Use the inline `ProductStatus` styled per finding 2, followed by one short sentence. For no-day:
       - Use "No assessment selected. Choose a day, then one of its assessed periods."
       - Drop the block card, the "As of: time not recorded" line and the second "nothing is concluded".
       - Drop the "No assessment exists" sentence for this state.
     - (e) Put the "Open this assessment in Performance › Dispatch" link at the end of the result line, not on its own line.
     - Expected height: about 1.5-1.7x. Two disclosure rows and the extra no-selection block go away. The remainder is honest result and not-available text that the mock has no data for.
   - **How the pinned assertions move** (none weakened):
     - `v01bEvidenceVisual.test.tsx:262-268` (the named-disclosure loop) is unchanged. The inner names still exist, closed, with `^Advanced details — ` summaries.
     - `v01bEvidenceVisual.test.tsx:289-296`: change the outer of the analysis pair from `evidence-analysis-technical` to `evidence-limit-details`, with the same three inner names. You may keep `evidence-analysis-technical` as a nested inner row, or drop it and re-point.
     - `evidenceClaimLimit.test.tsx:203` and `:225` are unchanged, because they cover standalone use with no target.
     - Add these to the H2 test:
       - The limits panel has exactly one top-level disclosure: `limit.querySelectorAll("details:not(details details)")` has length 1, and it is closed.
       - It contains the RoleStrip marker and the limit-list text.
       - `[data-claim-limit-headline]`, `[data-not-available='claim-limit-rule']`, `[data-claim-limit-pinned]` and the capacity sentence all have `closest("details") === null`.
     - Add to the no-day case: exactly one "Nothing is concluded" / "nothing is concluded" match in the panel, no `.product-status:not(.product-status--inline)`, and no "No assessment exists".

2. **Medium: the in-panel inline state line is still a grey, wrapping box with mixed type sizes.** Locations: `frontend/src/ui/primitives.css:4600` (`.product-status--inline` does not reset `.product-status` at `:3920`), `SiteWindowOverview.tsx:710`, `LedgerSiteEvidence.tsx:504` and `EvidenceClaimLimit.tsx:539`.
   - **What the captures show.** `.product-status`'s sunken background, padding and left border still apply inside `p.v69-chart-note`. `.product-status__bound` keeps `--text-sm`, while the sentence around it is at 10-11 px. Seen in the captures:
     - Overview money (`mini-p01-priced-1440-app.png`): two grey lines.
     - Evidence "What we can conclude now" (`evidence-stocked-1440-app.png`).
     - Evidence Analysis result line (`evidence-analysis-supported-1440-app.png`, and at 390).
   - **Why it matters.** This is exactly what M3 asked to remove. It also keeps money at 1.41x and adds a line to the limits panel.
   - **Fix.**
     - Add a reset next to `.product-status--inline`: `.v69-chart-note .product-status--inline, .claim-limit__result .product-status--inline { padding: 0; border: 0; border-radius: 0; background: transparent; }`.
     - Add `.v69-chart-note .product-status--inline *, .claim-limit__result .product-status--inline * { font-size: inherit; }`, keeping only the chip label at 10 px.
     - Recapture these three panels at 1440 and 390, and report the money and limits heights.

3. **Low: the Evidence Analysis records panel still has two disclosures** (`LedgerSiteEvidence.tsx:201`, `:1149`), and is at 1.70x.
   - "Different table sets" is not a reason to keep them apart: the same nested-outer pattern as finding 1 holds both.
   - Fix: nest `evidence-not-accepted` and `evidence-records-technical` under one outer `Advanced`. Re-point `v01bEvidenceVisual.test.tsx:289-296` in the same way.

4. **Low: the Dispatch panel 1 has two default-variant (large, bold, boxed) disclosures**, "What the outcomes mean" and "How this was worked out" (`PerformanceDispatch.tsx:471` and `DispatchReferences`). They were there before this round. Fix: make both `variant="tech"`, or fold the outcome meanings into the references disclosure.

5. **Low: mixed sizes remain elsewhere.**
   - On Overview, the operating-context timeline labels wrap to two lines ("Feeder demand · Clinic meter").
   - On Evidence, the "Most useful next evidence" source list is at 16 px among 11 px notes.
   - Fix: widen or ellipsize the timeline label column, and set the silent-source list to note size.

## Verification of the prior findings
| Prior | Status |
| --- | --- |
| H1 Dispatch chooser | **Fixed.** Chips and mock-sized tiles are in panel 1 under the strip. Panel 2 leads with the block's badge and sentence. The period facts follow under "The period this block is in", termed "Period outcome" (`dispatch-supported-1440-app.png`). |
| H2 limits | **Partly fixed.** The chooser is in the chip row, and the label, h3 and duplicate note are gone. The residue is in findings 1 and 2. |
| M3 repeated state | Freshness is said once, there is one panel-1 disclosure, the list state strip is gone, and the Evidence bullet is at note size. **The money and receipt lines still render as boxes (finding 2).** |
| M4 Needs attention | **Fixed.** Numbered `v69-attention` items (rank, title, reason, link). The chosen Finding is merged into item 1, and there is no "same" note or h3. This matches the mock. |
| M5 vocabulary | **Fixed.** The plain gaps sentence, record rows by role/source in words with the IDs as `title`, "Stopped", quality in words, and the plain audit sentence. |
| M6 alternatives | **Fixed.** One "Other explanations" line, and every key gets a named term. |
| 7a / 7b / 7c / 7e | 7a: the note line is done, but the two disclosures remain (finding 3). 7b fixed. 7c fixed. 7e: the scroll container is confirmed. |

## Remaining ~1.4x panels
- Overview "happened" at 1.40x: accepted. It is honest whole-day content, with one disclosure.
- Overview money at 1.41x: should fall to about 1.3x after finding 2.
- Dispatch coverage at 1.31-1.42x: accepted (honest limitations).

## Regression checklist
- **State said once:** yes, except the inline-box duplication of size and style (finding 2) and the no-day state (finding 1).
- **One disclosure per panel:** no for the limits panel (finding 1). Records and Dispatch panel 1 (findings 3 and 4) were like this before the round.
- **No leftover labels or h3s:** yes. The `headline-card__question` label is gone and the list h3 is gone.
- **No raw IDs, backend text or enums:** yes on the captured screens.
- **No contradictory lines:** the M6 contradiction is gone. The "No assessment exists" line is new to this panel (finding 1).
- **Mock rows, columns and chips present; tables and lists as in the mock:** yes. Needs attention is now the mock list.
- **Panel title:** "How each limit is set" versus the mock's "How a claim limit is set". This is the known vocabulary-list item awaiting a ruling (`V69_TITLES_ON_VOCABULARY_LIST`), so it is not a new finding.

## Assertions
I read every changed assertion. Each is re-pointed to the content's new home, with equal or stronger checks:
- The freshness state is asserted on the statusbar, plus the marker and the source sentence.
- The removed "This page states" line has a negative check. "draws no conclusion" is still asserted on the Overview panel.
- The audit sentence check is exact, with a negative check on the old wording.

None was weakened.

## Checks run (by me, at `f2163bef`)
- `npx.cmd tsc --noEmit -p .`: exit 0.
- `npx.cmd vitest run` on 9 focused files: **9 files, 251 tests passed**, 33 s. Vitest ran in this session, so the esbuild sandbox failure did not occur. The files:
  - `performanceDispatch`, `s2LedgerEvidence`, `v01bEvidenceVisual`, `s5SiteWindowOverview`, `s502OverviewFindingList`, `evidenceClaimLimit`, `panelStructure`, `siteEvidenceScreen`, `siteOverviewScreen`.
- I did not run the full suite. The implementer reports 1986 passed, 0 failed, at `73cb5a54`, which is the code revision under review.
- Captures viewed: 1440 app/mock for evidence-analysis supported, evidence-analysis no-selection (app), dispatch supported, mini p01 and evidence stocked (app); 390 app for evidence-analysis limited.
- Not viewed: the other pairs.
