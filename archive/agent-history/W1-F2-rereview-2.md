# W1-F2 re-review 2 (fix round 2)

Reviewer: fresh, independent Claude reviewer. Revision: `1a40f380`. Diff: `33025377..1a40f380 -- frontend`. Prior verdict: `.agent/W1-F2-rereview.md` (RETURN, M1 limits panel, M2 inline-status box).

## Verdict: ACCEPT

Both Medium findings are fixed as specified. No regression found. Three Low findings, none blocking.

## Prior Medium findings

**M1, the limits panel: fixed.**
- `LedgerSiteEvidence.tsx` `ClaimLimit` ends with one closed `evidence-limit-details` row. That row holds:
  - the detail slot;
  - the limit list;
  - `evidence-analysis-technical`, which keeps its inner rows.
- `EvidenceClaimLimit.tsx` portals the detail content into the slot through `detailTarget`. Standalone use (`detailTarget` undefined) keeps `claim-limit-detail`, so the existing standalone tests stand.
- The capacity sentence is appended to `[data-evidence-limit-note]` and is visible at 1440 and 390.
- The Dispatch link ends the result line.
- The no-day state is one line. It no longer has the block card, the "As of" line, a second "nothing is concluded" or "No assessment exists" (see `evidence-analysis-no-selection-1440-app.png`).
- The unavailable and refused states are one inline line.

**Height against the mock, at 1.63-1.80x.** The mock panel is two paragraphs. The app shows the same two paragraphs (the second is one sentence longer, because of the capacity caveat). It then adds three things:
- the selected assessment's result line, with its inline state, as of and the Dispatch link;
- the "Not available yet" rule line;
- the one closed row.

The mock has no data for any of these three, and each is honest state that must stay visible. Nothing duplicated or decorative remains, so I accept it.

**M2, the inline-status CSS: fixed.**
- `primitives.css:4600-4611`: `.product-status--inline` now resets padding, border, radius and background, and inherits font size, children included.
- The label stays at 10 px because `.product-status--inline .product-status__label` (0,2,0) beats `*`.
- The tone rule `.product-status--limited/--problem` sets a background. It has the same specificity but comes earlier, so the reset wins.
- No grey box remains in any of the captures:
  - Overview money, `mini-p01-priced-1440-app.png`: a chip plus a plain sentence.
  - Evidence "What we can conclude now", `evidence-stocked-1440-app.png`.
  - Evidence Analysis result line, at 1440 and at 390 (`evidence-analysis-limited-390-app.png`).

**Low 3, records: fixed.** `evidence-not-accepted` now nests inside `evidence-records-technical`, and the records panel has one closed row.

## Other users of `.product-status--inline`
I grepped for every usage:
- `SiteWindowOverview.tsx:253` (freshness note) and `:711` (money note);
- `SiteWindowOverview.tsx:339` (statusbar);
- `LedgerSiteEvidence.tsx:514` (receipt note);
- `EvidenceClaimLimit.tsx` (result, unavailable and refused);
- `PerformanceDispatch.tsx:625` (statusbar).

In the statusbars, `.v69-statusbar .product-status` (0,2,0) already reset the box and still sets the flex layout. The only change there is that the sentence and bound now inherit the statusbar's 11 px instead of `--text-sm`. That moves them closer to the mock, and the recaptured Overview statusbar renders correctly. Nothing is broken. The Dispatch statusbar was not recaptured (finding 1).

## Regression checklist
- **State said once: yes.** The no-day duplicate is gone, and the inline lines do not repeat the statusbar.
- **One disclosure per panel: yes** for both Analysis panels, which is the scope of this round. Dispatch panel 1 is the prior Low 4, not touched here. The Overview money panel's two rows (finding 3) predate this round.
- **No raw IDs or enums: yes.** The revision ID appears only in the `data-claim-limit-pinned` attribute.
- **No contradictions: yes.** "No assessment exists" is gone.
- **No assertion weakened: yes.**
  - `v01bEvidenceVisual` re-points both nested pairs to the new outers and adds inner names.
  - It adds new checks: one top-level `details`, closed; the capacity sentence and the not-available line outside `details`; one "nothing is concluded"; no "No assessment exists"; no block `product-status`.
  - `evidenceClaimLimit` adds a slot-case test. Its standalone tests are unchanged.

## Findings (Low, non-blocking)
1. **Low: the Dispatch captures are stale against the shared CSS change.**
   - The packet says "Dispatch and analysis captures are unchanged (no source change since their last capture)". But `primitives.css` changed `.product-status--inline`, which `PerformanceDispatch.tsx:625` uses in the statusbar.
   - The expected effect is benign: smaller, mock-sized bound text in the statusbar, as the Overview statusbar shows.
   - Fix: recapture Dispatch at the next capture pass, or correct the packet sentence.
2. **Low: the limited result says "the rest of the period is limited by the gaps below"** (`EvidenceClaimLimit.tsx:110`), but the gaps are now inside the closed row.
   - This predates the round: the gaps were already in the closed `claim-limit-detail`.
   - The headline states the limit itself, so no material limit is hidden.
   - Fix: change "below" to "listed under Advanced details", or drop it, at the W1 copy pass.
3. **Low: the Overview money panel stays at 1.40x, not the ~1.3x the prior review expected.**
   - The box is gone, but the panel still has two closed rows ("Source record for this cost" and "Cost range, money gate and links"), and they predate this round.
   - Fix: fold them into one row, at the W1 pass.

## Checks run (by me, at `1a40f380`)
- `npx.cmd tsc --noEmit -p .`: exit 0.
- `npx.cmd vitest run` on 9 focused files: **9 files, 252 tests passed.** Vitest ran in this session, so the esbuild sandbox failure did not occur. The files:
  - `v01bEvidenceVisual`, `evidenceClaimLimit`, `s5SiteWindowOverview`, `s2LedgerEvidence`, `siteEvidenceScreen`, `siteOverviewScreen` and `s502OverviewFindingList`: 7 files, 202 tests;
  - `performanceDispatch` and `panelStructure`: 2 files, 50 tests.
- I did not run the full suite. I cite the implementer's run: 1986 passed and 1 failed (the new no-day assertion). The follow-up commit fixed that failure, and the 2 affected files reran green.
- Captures viewed, 1440 app: evidence-analysis supported and no-selection, mini p01 and evidence stocked. Also the evidence-analysis supported mock, and evidence-analysis limited app at 390.
- Not viewed: the remaining mini and evidence pairs, and Dispatch (not recaptured).
