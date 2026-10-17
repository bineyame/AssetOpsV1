# W1-F2-overview handoff (partial: one refinement pass remains)

Branch `task/W1-F2-overview`, clean at `fde3e130`. Not merged. The packet is `.agent/W1-F2-overview-review-packet.md`; read it first for what landed, the per-screen panel map, the changed assertions and the deviations.

## State at the stop
- **Done:**
  - All five screens (`mini`, `dispatch`, `analysis`, `evidence`, `evidence-analysis`) render exactly the v69 panels, on imported and legacy Sites, in stocked, empty and refused states.
  - Structure tests added; planted-panel proof done.
  - Full suite 1965/1965 at `1554f013`; `tsc` clean; `check-all` 10/10.
  - Captures in `.agent/W1-F2-evidence/{mini,dispatch,evidence}`, all claims passed.
- **Not done:** the coordinator's later lessons (F1 review and re-review, `.agent/W1-F1-review.md`, `.agent/W1-F1-rereview.md` at `4e16f81c`). They arrived mid-build and are listed below. After this pass, rerun the full suite and recapture. The fixture commands are in the packet's "Checks run" and in walkthrough Parts 2, 6 and 7.

## Resume: the refinement pass, in order
1. **No blocks inside the status strip.**
   - Today `StatusBar` (`ui/V69Layout.tsx`) wraps a block `ProductStatus` in two places:
     - `SiteWindowOverview.tsx` `DayStatus`;
     - `PerformanceDispatch.tsx` `WindowView` → `StatusLine`.
   - CSS (end of `ui/primitives.css`) flattens it only visually.
   - Fix: add an additive `inline` variant to `ProductStatus` that renders spans (label badge, sentence, scope, as-of), or render those spans directly. Keep `data-product-status`, so `expectStateLineVisible` still works.
   - Move the stale-totals sentence (`PerformanceDispatch.tsx` `DayTotals`, `p.v69-objective[data-totals-stale]`) out of the pre-panel area: into the strip as a span, or into the card notes.
2. **No stray content between or after panels**, except where the mock has it:
   - The Dispatch demo-data notice between the pair and panel 3 matches the mock notice slot. Confirm against F1's tightened guard.
   - Evidence `Advanced name="evidence-earlier-store"` (after the closing notice) should move into the Data sources panel.
   - The `site-record` disclosure under the Overview grid (`SiteDetails.tsx`) should move into a panel or follow F1's rule.
   - The legacy `StatusBar` with `data-dispatch-selected-missing` (`SitePerformance.tsx`) is fine if the strip may hold text and a link.
   - The mini objective line `p.v69-objective` before the cards is the mock's `.objective`. Check that F1's guard allows it.
3. **Body-size explanatory text.** Convert it to `ChartNote` lines or one small notice, and move the full text into a closed disclosure, keeping every statement.
   - mini:
     - `HourNotSelected` (`overviewSlots.tsx`);
     - `DayReading` prose and the `FreshnessStrip` source-open sentence (`SiteWindowOverview.tsx`);
     - `NextStep` prose;
     - the money qualifier.
   - dispatch:
     - the panel 1 headline (`data-dispatch-headline`) — keep it at one line;
     - the coverage note;
     - the `SelectedPeriod` pinned notes.
   - evidence:
     - panel 1 paragraphs `data-evidence-rejection-count`, `data-evidence-limits` and the `NotAvailableYet` (baselined text must stay byte-identical);
     - the `ReportingFacts` note.
   - evidence-analysis: the `ClaimLimit` prose list. The `Rejected` paragraphs can become chart-notes.
   - Tests assert some of this text by data attribute, and that stays valid if the attributes are kept.
4. **Visual detail ported by F1.** Use F1's patterns once F1 lands; do not duplicate them:
   - card top border and large state word;
   - `.field` and `.button` for the Dispatch day picker, the Evidence window chooser and the Overview day selector;
   - page heading as site name, badge and per-screen description (Dispatch and Evidence headings still read "Performance" and "Evidence").
5. **Prominence items** from packet "Residual risk":
   - duplicate freshness line in mini panel 1;
   - per-source strip above the Evidence sources table;
   - two strips in Dispatch panel 1.
   Each is pinned by an existing W1-UX test. Move the content rather than delete the assertion.

## Open question for the Architect (blocking a clean vocabulary guard)
`evidence-analysis:2` "How a claim limit is set" uses listed vocabulary. It is handled by one named list, `frontend/src/test/v69PanelTitles.ts` `V69_TITLES_ON_VOCABULARY_LIST`, which needs a ruling.

## Anchors
- Overview: `sites/overviewSlots.tsx` (`OverviewGrid`, `OverviewRefused`); `SiteWindowOverview.tsx` (`DayStatus`, `ObjectiveCards`, `PeriodStrip`, `NextStep`, main); `SiteOverview.tsx` (legacy body, `DomainCard`, `DomainPeriods`, `DomainContext`).
- Dispatch: `PerformanceDispatch.tsx` (`DispatchSlots`, `DispatchRefused`, `WindowView`, `AnalysisView`); `SitePerformance.tsx` (`LegacySlots`, `LegacyRefused`).
- Evidence: `LedgerSiteEvidence.tsx` (`OverviewBody`, `Inspector` children, `ClaimLimit` children); `SiteEvidence.tsx` (`EvidenceRefused`); `panelPart.tsx`.

## Coordinator decision for the resume (2026-10-17)

- Evidence Analysis panel 2 title: render the plain variant **"How each limit is set"** (the existing panel title). Authority: `D-2026-10-16-w1-ux` bans "claim limit"/"claim" in default prose; add it to the approved title map in `frontend/src/test/v69PanelTitles.ts` and delete the vocabulary exception entry.
- Resume after W1-F1 merges to main: merge main, then apply F1 styles (cards, `.field`/`.button`, `SitePageHeader`) and the tightened guard; headings read the site name, badge and per-screen description.

## Resume state 2 (after main merge, `5a7320a7`)

- Main (final W1-F1) merged at `cc8f49fc`; conflicts resolved keeping both sides.
- Shared layer, `5a7320a7`:
  - `StatusBar` (`ui/V69Layout.tsx`) now renders F1's `div.status-strip.status-strip--line`. Every child must be inline; a block child fails `stripIntruders`.
  - `ProductStatus inline` (`ui/ProductStatus.tsx`) renders spans and keeps all data attributes. Use it inside any strip.
  - `V69Notice` carries `.notice`, so it is allowed between panels.
  - Guard: `.v69-objective` is allowed before panel 1. This is additive, and it is the mock's `.objective`.
  - Fixed an unclosed CSS rule at the end of the F2 statusbar block.
- Guard failures found after the merge (18 tests in 6 files):
  - `form.dispatch-day` sits before panel 1, on dispatch and analysis.
  - A block `ProductStatus` sits inside the strip: `StatusLine`, and `DayStatus` at `SiteWindowOverview:320`.
  - `section.dispatch-view` sits outside panels: legacy `SitePerformance`, t028.
  - Evidence: `form.evidence-window` and `div.evidence-statusbar` sit before panel 1. That StatusBar is local to `LedgerSiteEvidence.tsx`, so give it the strip classes.
  - Mini: `v69-statusbar` with a block child sits before panel 1, plus the objective line, which is now allowed.
  - Legacy overview (`siteOverviewScreen`): `v69-statusbar` with `Badge` and `span`. It should now pass; verify it.
- App-only controls such as the day picker and the window chooser go before panel 1 as a `.v69-chips` row. Use chip-sized controls (`.v69-chip-control`) and `.button`, as F1 did for the Sites search. Alternatively they can go inside the strip as chip-sized controls, as F1's period select is. Never put them in a free form before panel 1.
