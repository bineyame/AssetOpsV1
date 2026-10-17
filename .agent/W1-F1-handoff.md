# W1-F1 handoff: the shared layout API F2-F5 must use

Contract: `.agent/architect-W1-fidelity.md` (`D-2026-10-17-mockup-layout-spec`). Branch `task/W1-F1-foundation`. Review packet: `.agent/W1-F1-review-packet.md`.

## 1. Structure guard (every screen, every variant)
- `frontend/src/test/panelStructure.ts`
  - `expectV69Panels(screenId, values?, scope?)`: asserts that `<main>` renders exactly the v69 titles in order. Counted: every visible `h2` in `<main>`, plus any `section.panel`, `.panel` or `[data-headline-card]` without its own h2, which is reported as `"(untitled)"`. Content inside closed `<details>` or hidden nodes is skipped.
  - `renderedPanelTitles(scope?)`: the measured list.
  - `panelTitled(title)`: the panel element, for in-panel gap assertions.
- `frontend/src/test/v69PanelTitles.ts`: `expectedPanelTitles(screenId, values)` reads `docs/architecture/v69-rendered-panels.json` and applies `APPROVED_TITLE_CHANGES`. That map holds exactly the 5 Architect rules. Dynamic keys: `interval` (dispatch:2), `gateway` (readiness:2), `finding` (finding-evidence:1), `site` and optional `topology` (sld:1). Do not add an entry to keep an extra panel.
- Proven non-vacuous on `/sites` in W1-F1. A planted titled `Panel` and an untitled `div.panel` both failed, and the plant was reverted.
- Rules that follow from the guard:
  - A page-level state (refusal, no version) is a `div.page-refusal[data-page-refusal=...]` with its title in `<p className="page-refusal__title"><strong>`, never an h2. The panel slots follow it with the gap stated inside each panel.
  - A nested sub-panel is legitimate only where the mock nests one (readiness 3 and 4 inside the gateway panel). Otherwise use `div.subsection` with an `h3.subsection__heading`.
  - Merge a former panel's content into its owning panel: its table, its key values, or a one-line `ChartNote`.
  - **Never rebuild a former panel as an h3 subsection**, inside or outside a panel. That is the answer-card pattern the owner rejected.
  - Fix round 1 hardened the guard in two places:
    - Outside panels, any `h3`-`h6`, `section`, `article`, `[role=region]`, `.card` or `.callout` fails.
    - Before panel 1, anything fails except chrome, `.status-strip`, `[data-page-refusal]`, `.v69-cards`, `.v69-chips`, and the selected-part notice or chip.
    - Unit tests: `src/test/__tests__/panelStructure.test.ts`.
  - A closed disclosure may hold `Panel`s. They are not counted until opened, so keep substantive limits outside it.
- Fix round 1 shared patterns (`ui/V69Layout.tsx`; the "W1-F1 fix round 1" section of `ui/primitives.css`):
  - `SitePageHeader({siteName, siteId, mode, description})` renders the mock's Site page heading: the site name as h1, a `.prov-tag` badge and the screen description.
    - Every Site screen uses it.
    - Add each screen's description to `SITE_SCREEN_DESCRIPTIONS`, taken from the mock subtitle but without its illustrative values.
  - `MetricCard assessment` with `tone` renders `.metric.assessment`. Use it for every state-word card.
  - `ExactReferences variant="tech"` renders the mock's small `details.tech`. Use it for references in a strip or under a table, never as a full-width bar.
  - `.status-strip--line` is the mock's one-line `.statusbar`. Put the screen verdict first on the line through the strip's `lead`.
  - The mock's form controls: `.field`, `.input-row`, `.button`, `.button.primary`, `.form-footer`. No browser-default input or button inside a v69 panel.
  - `.v69-chips` may hold chip-sized `.v69-chip-control` search and select controls. Never add a second toolbar inside a panel.
  - A state line inside a panel is one `v69-chart-note`, never a `ProductStatus` callout.

## 2. Shared v69 patterns (`frontend/src/ui`, exported from `ui/index.ts`)
- `V69Layout.tsx`:
  - `MetricCards({columns: 3|4|5, label, data})` and `MetricCard({label, value, note, tone: green|amber|red|muted, word, data})`: the mock's `.cards` and `.metric`. Use `word` for a state or gap value.
  - `KeyValues({rows, label})`: the mock's `kv`.
  - `AttentionList({items: {key,title,body,action?}[], label})`: the mock's attention rows.
  - `ChartNote`.
- `Panel` gained `actions` (the mock's panel-head right link) and `className`.
- CSS, in the "v69 layout patterns" section at the end of `ui/primitives.css`:
  - `.v69-cards`, `.v69-metric*`, `.v69-key-values`, `.v69-attention*`
  - `.v69-chips` / `.v69-chip`, with `[aria-pressed=true]` as the active chip
  - `.gw-*`, `.page-refusal`
- Tokens in `tokens.css`: `--v69-panel-padding`, `--v69-radius-panel`, `--v69-gap`.
- `.panel` follows the mock: 19px padding, 7px radius, no header rule. `.panel-pair` is the mock's `.two-col`:
  - above 1100px: `1.8fr / minmax(270px,1fr)`
  - 761-1100px: `1.4fr / 1fr`
  - 760px and below: stacked
  - `.panel-pair--equal` gives equal columns.

## 3. Gap placement rules (missing-claim scan)
- Every missing-capability phrase goes through `<MissingClaim gapId placement>`. The placement must be in both `ui/gapCatalogue.ts` and `frontend/docs/architecture/v69-dependency-registry-pilot.json` `ui_placements`, and each placement renders once.
- When one claim covers two mock cards, render it once and point the second card at it. W1-F1 does this for the Sites "Evidence limited" card.
- Metric values use `Not available`, not `Not available yet`. The tagged note carries the claim.

## 4. Side-by-side evidence
- `node tools/w1-fidelity-evidence.mjs <out-dir> <mock-id>[:<case>]=<app-url> ...`
  - Uses the existing `widthGuard`. Optional environment: `W1_REVISION`, `ASSETOPS_CDP_PORT` (default 9473).
  - Writes `<id>[-case]-<1440|390>-app.png` and `-mock.png`, `evidence.json` (titles, panel boxes, overflow, URLs, revision) and `index.html` showing the pairs side by side.
  - Claims: the app rendered; the mock rendered; app and mock show the same panel count; no horizontal overflow on the app.
- Walkthrough data: `.agent/W1-UX-combined-owner-walkthrough.md` Part 1. In W1-F1, ports 8960 and 5460 were held by another worktree, so we used API 8970/8971 and web 5470/5471. Drop the fixtures afterwards.

## 5. Next
F2 (`mini`, `dispatch`, `analysis`, `evidence`, `evidence-analysis`) builds on the shared layer above. Each slice adds a route structure test per screen, in its stocked, empty and refused variants, plus pairs from `w1-fidelity-evidence.mjs`.
