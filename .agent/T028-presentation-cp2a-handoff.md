# T028 presentation checkpoint 2a - handoff to checkpoint 2b

Spec `.agent/T028-architect-presentation.md` (sections 2, 4, 5). 2a landed the
four graphics and the card projection (packet section "Presentation
checkpoint 2a"). 2b: the vocabulary guard, remaining jargon, the
layout-evidence rewrite and run, the Lab-off journey, then combined review.

## Graphic anchors and layout-relevant selectors

All graphics: `frontend/src/sites/assessmentGraphics.tsx`, region class
`.assessment-graphic` (`overflow-x: auto`, `primitives.css` "T028 presentation
checkpoint 2a" block), `data-graphic="<name>"` and `data-graphic-anchor`.

- Timeline: `figure.period-timeline[data-graphic="assessed-period-timeline"]`,
  `data-graphic-assessment=<assessment id>`, `data-compact="true"` on compact.
  Bar `svg.period-timeline__bar` (viewBox 1000x24, `preserveAspectRatio=none`,
  width 100%; compact min-width 120px). Bands `rect[data-band][data-band-kind]
  [data-x][data-width][data-part]`; open markers `[data-open-end=start|end]`;
  axis `[data-axis-start]`/`[data-axis-end]`; legend `ul.graphic-legend
  [data-legend]`; notes `[data-open-note]`; parts table `[data-timeline-table]`
  (rows `[data-timeline-row]`, buttons `[data-select-part=N]`, links
  `[data-part-link=N]`).
  Placements: Finding Overview (`FindingDetail.tsx` "When, and for how long"),
  Dispatch rows (`SitePerformance.tsx` "Timeline" column, compact), Overview
  card (`SiteOverview.tsx` `[data-overview-card-timeline]`, compact), Analysis
  (`assessmentAnalysis.tsx`).
- Fuel: `[data-graphic="fuel-range"]` with `data-fuel-low/high` (fractions of
  scale) or `data-fuel-unavailable=<status>` (no svg). Wrappers
  `[data-finding-fuel]`, `[data-analysis-fuel]`.
- Reported values: `[data-graphic="reported-values"][data-values-side]
  [data-values-part-start]`, tables `[data-value-bars="kW"|"%"]`, rows
  `[data-value-row][data-missing]`, bars `svg[data-bar-width]`, switch
  `[data-values-switch]`. Selected part `[data-analysis-selected-part]`.
- Coverage: `[data-graphic="coverage-by-input"]`, `[data-coverage-table]`,
  rows `[data-coverage-input][data-coverage-assessed]`. Site Evidence block
  `[data-evidence-assessment-coverage]` at `?view=analysis&assessment=<id>`.

## For 2b

- `tools/layout-evidence.mjs` ~4196 measures `.segment-strip` (gone; CSS
  removed) and ~4229-4340 the old T028 disclosures: rewrite to the selectors
  above. Measure at 640px and narrower: the Dispatch table's timeline cell
  (compact bar min-width 120px), the Analysis parts table and value tables
  (DataTable scroll regions), the card timeline, legend wrapping. Prove each
  measured set non-empty.
- Guard (section 4) must also scan graphic text: captions, legend, `<title>`
  per band, `aria-label` of the bar, open-end notes. Authored copy there uses
  "operating", "assessed part", "Start or stop time uncertain", "Generator
  operation not recorded"; no run/binding words. Band `<title>` and
  `aria-label` are in the DOM, so a rendered-text + accessible-name scan sees them.
- `shell-overflow.ps1` now names five svg modules; a new drawing elsewhere fails.

## Choices made (revisit if the reviewer disagrees)

See packet "Choices": `?part=N` selection and default part; unrecorded parts
hatched regardless of classification; neutral grey for Cannot determine; card
fuel only when BOUNDED; Analysis per-part values table replaced by parts table
plus selected part values; coverage link from Finding/Dispatch Analysis to
Site Evidence.

## Risks

- No browser look yet: label collisions, bar heights and the open-end markers
  at narrow widths are unverified (2b layout run).
- Very short parts render sub-pixel at true width (by design); the table and
  `aria-label` carry them.
- `INPUT_WORDS` is still a frontend mapping (cp1 note).
- `CODE_STATE.md` / `ACTIVE_CONTEXT.md` not updated for 2a; do it at T028
  closeout in 2b.
