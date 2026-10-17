# W1-F1 independent review: shared layout guard + Sites, Foundation, Readiness, SLD

- Reviewer: fresh Claude Reviewer (not the author). Revision reviewed: `2a5d4869` (diff `c3b21c6e..2a5d4869`, excluding `.agent`). Worktree `AssetOpsV1-review5`.
- Judged against: `.agent/architect-W1-fidelity.md` (`D-2026-10-17-mockup-layout-spec`), the owner verdict (verbatim), the build brief, and the v69 mock (`index.html`, `mockups.css`) for `sites`, `foundation`, `readiness`, `sld`.

## Verdict: RETURN

The panel set, order and titles now match v69 on all four screens, in every variant tested, and the leading W1-UX answer cards are gone. Foundation's top fold matches the owner's request: Configured topology sits next to Identity and operating obligations, then the controls panel. Honest states are kept.

The slice still fails on two points the contract makes blocking:

1. **The guard can be bypassed.** I planted a leading answer card made of a `section` with an `h3`, and the guard passed. The handoff tells F2-F5 to write former panels as exactly that, h3 subsections.
2. **Readiness keeps the bulky readiness block the owner complained about.** It now sits inside panel 1. The mock's readiness strip has been replaced by the Foundation version strip.

Several Medium visual-style and prominence drifts also remain, and the owner would name them on sight.

## Findings

### 1. High: the structure guard misses a leading card that has no h2 and no `.panel` class
`frontend/src/test/panelStructure.ts:39` (the candidate selector `h2, section.panel, .panel, [data-headline-card]`)

- **What I did.** In `SiteModelView` (`frontend/src/sites/StoredFoundationViews.tsx:249`, directly after the strip), I planted:
  ```tsx
  <section className="callout" aria-label="What is configured for this period?"><h3>What is configured for this period?</h3><p>Planted leading answer card with a big verdict.</p></section><div className="card"><h4>Second planted card</h4></div>
  ```
- **Result.** `stocked: foundation` **passed** (1 passed). A planted `<Panel heading=...>` in the same place did fail (`+ "What is configured for this period?"`). Both plants were reverted with `git checkout`, and the tree is clean.
- **Why it matters.** The contract requires the guard to "reject any extra leading card/panel before panel 1". The handoff (§1) tells F2-F5 that "former panels become h3 subsections". So the very pattern the owner rejected can come back through the sanctioned route and still pass the guard. The Sites "Registered sites, not ranked" callout (finding 5) is already this pattern, although it is inside the panel.
- **Fix.** Make the guard an allowlist. Between the subtabs and panel 1, the only permitted siblings are `.status-strip`, `[data-page-refusal]`, `.v69-cards`, `.v69-chips` and the selected-part notice. Any other element there fails, and so does any `h2`-`h4`, `section`, `article` or `[role=region]` outside a v69 panel. Add a non-vacuity test that plants an h3 card and expects a failure, so this cannot regress.

### 2. High: Readiness has lost the mock's readiness strip, and panel 1 carries a bulky verdict, legend and explanation block
`frontend/src/sites/StoredFoundationViews.tsx:936-939` (strip) and `:951-952` (`ReadinessVerdict`, `ReadinessNextSteps` inside panel 1). Capture: `readiness-now-1440-app.png` vs `-mock.png`.

- **Strip.** In the mock, the readiness strip is the verdict: `Needs review · Configuration readiness is distinct from claim readiness`, on one line. The app repeats the Site model's Foundation version strip there, about 125 px tall.
- **Panel 1.** In the mock, panel 1 is just the evidence table. The app appends roughly 330 px below the table:
  - a "Configuration readiness" heading;
  - a full-width green "Set up to report" banner;
  - a three-chip colour legend;
  - two explanatory paragraphs;
  - "What to do next".
  Panel 1 ends up about twice the mock's height. This is the readiness content the owner called "takes a lot of space and is styled inferior". It moved screens but kept its bulk.
- **Why High.** The contract counts prominence mismatch as High.
- **Fix.**
  - Put the verdict badge and the one-line distinction in the Readiness strip, as the mock does. The Foundation version and period can be a compact part of the same strip.
  - Reduce the legend and paragraphs to a single `v69-chart-note` limit line under the table.
  - Keep the next-step line as the table's last row or a one-line note.
  - Keep the material limit visible ("configuration only; not connection or condition") per `-w1-ux-disclosure`.

### 3. Medium: the Readiness category cards do not use the mock's assessment metric style
`frontend/src/sites/ReadinessOverview.tsx:134-146`; `frontend/src/ui/V69Layout.tsx:30-44`

- **Mock.** The cards are `.metric.assessment.<tone>`: a 3 px coloured top border and a 17 px word value ("Complete", "Needs review", "Conditional").
- **App.** Each card renders a small badge as its value (`✓ Configured`), with no tone and no top border. The row reads as four near-empty boxes rather than the mock's scannable status row.
- **Fix.** Add the `assessment` variant (top-border tone plus word value) to `MetricCard`, and pass `tone` from `CARD_TONE`, with the state word as the value. The same variant fits the gateway metrics, whose mock cards also carry tone borders.

### 4. Medium: the Foundation strip is about 3.5 times the mock's height on all three Foundation views
`frontend/src/sites/FoundationRevisionPanel.tsx:118-200`. Captures: `foundation-now-1440`, `sld-now-1440`, `readiness-now-1440`.

- **Mock.** A one-line `.statusbar` of about 44 px: badge, effective text and one link.
- **App.** About 160 px over three rows:
  - the version, as-of, channel links and gaps;
  - a full-width row with the link on its own;
  - a state sentence plus a 400 px native `<select>`, then a full-width "How this was worked out" disclosure bar.
- **Effect.** Every Foundation view's panels sit about 115 px lower than the mock's. On SLD (`sld-battery`), the scheduled-period note adds a fourth row.
- **Judgement.** Known deviation 2 is real, but the contract allows "small reference disclosure", not a full-width bar.
- **Fix.**
  - Put the period selector inline as a compact control, sized like the mock's chips.
  - Make the exact references a small link-styled `details.tech` summary on the same row.
  - Keep the historical or scheduled note as one short line.

### 5. Medium: an in-panel answer callout and an extra toolbar push the Sites inventory table down
`frontend/src/sites/SitesIndex.tsx:321-332` (the `ProductStatus` and `ExactReferences` block) and `:392-420` (the search/mode/lifecycle toolbar). Capture: `sites-stocked-1440`.

- **Mock.** The Site inventory panel goes straight from its head to the table, and filtering is done with the chips above the cards.
- **App.**
  - It opens the panel with the former W1-UX answer card: a grey callout titled "Registered sites, not ranked" with four lines, plus a full-width "How this was worked out" bar.
  - Below that is a second filter toolbar (search box and two large selects) that the mock does not have.
  - The table starts about 250 px into the panel.
- **Why it matters.** The contract allows merging the card's state, scope and as-of into the panel. It does not allow keeping the card's visual form and bulk. This is the "answer card layered above the layout" pattern, one level down.
- **Fix.**
  - Reduce the state to the panel description or one `v69-chart-note` line ("Registered sites, not ranked · as of not recorded").
  - Move exact references to a small `details.tech`.
  - Fold search and filters into the chip row, or a compact single-line toolbar.
  - Mode and lifecycle can be chips if needed.

### 6. Medium: every Site screen uses "Foundation" as its page heading, not the mock's site-name heading
`frontend/src/sites/StoredFoundationViews.tsx:133-137` (also `frontend/src/shell/SiteFoundationFrame.tsx` refusal branches)

- **Mock.** The h1 is the site name ("Kobo Mini-grid") with a provenance badge, and the subtitle is the screen description ("Definition, topology and controls · ..."). The breadcrumb is Sites › site › Foundation.
- **App.** The h1 is "Foundation", with "Kobo mini-grid · KOBO-001" as the subtitle.
- **Why it matters.** The contract names "the mock's page heading" pattern explicitly. This header predates W1-F1, but F1 owns the shared patterns, and F2-F5 will inherit whatever F1 settles. The owner will see the difference at the top of every Site screen.
- **Fix.** Use the site display name as the h1, the read's evidence mode as the badge, and the mock's per-screen description as the subtitle. Settle this once in the shared page-heading pattern. If the Architect wants it deferred to F5, record that explicitly.

### 7. Medium: the reserve form and refusal buttons are browser-default controls inside v69 panels
`frontend/src/sites/FoundationRevisionPanel.tsx:526-560` (the `action-form` `<input>` and `<button type="submit">` without `.button`/`.field` styling). "Show the version in effect now" in the page refusal. Captures: `foundation-now-1440-app.png` (bottom of panel 3) and `foundation-no-version-1440-app.png`.

- **Problem.** Both are unstyled native inputs and grey buttons. The mock defines `.field` inputs and `.button` / `.button.primary`.
- **Placement.** Putting the reserve form inside panel 3 (known deviation 3) is acceptable per the contract ("put policy in panel 3"). The styling is not: it is the "styled inferior" complaint.
- **Fix.** Port `.field`, `.button` and `.form-footer` into `primitives.css`, and apply them to the form and the refusal action.

### 8. Low: the SLD panel adds three prose paragraphs and a summary/chip row
`frontend/src/sites/StoredFoundationViews.tsx:589-600` and `:682`; `SiteSingleLineDiagram.tsx:95`, `:1175`. Capture: `sld-now-1440`.

- **Mock.** Panel 1 is the head, then the drawing, then a one-line legend. The configured-not-live limit is a single blue notice below the panels.
- **App.** About 170 px of prose sits under the drawing, plus a summary line and chip above it.
- **Why only Low.** The limits must stay visible, so this is a density preference.
- **Fix.** Condense to one chart-note line under the legend.

### 9. Low: the SLD title uses the site type as the topology type
`frontend/src/sites/StoredFoundationViews.tsx:574` (`sldPanelTitle`)

- **Problem.** The approved rule is `{site name} · {configured topology type, if stated}`. The read has no topology type, so the rule implies the site name alone. "Mini-grid" is the site archetype, not a stated topology.
- **Why only Low.** It is plausible and not misleading.
- **Fix.** Drop the suffix, or get an Architect note that the archetype counts as the topology type.

### 10. Low: the same site appears in both Site inventory and In setup
`frontend/src/sites/SitesIndex.tsx:255`

- **Judgement.** Acceptable. The directory lists every registered site, and In setup filters on recorded lifecycle. The mock's semantics ("appear in the directory once activated") are not claimed.
- **Optional.** Add a short note in the In setup description that these sites are also listed above.

### 11. Low: the Site model no longer fails closed on a loaded read that carries `NO_EFFECTIVE_REVISION`
`frontend/src/shell/__tests__/siteFoundationRevision.test.tsx` (W1-UX-05 test "a scheduled period is never called in effect now; a gap makes it incomplete", third case)

- **Before.** The removed answer card said "No configuration for this period" and "No equipment or settings are recorded for the selected time".
- **Now.** The test asserts only "1 configuration gap" in the strip and the message in the controls panel. Nothing asserts that topology and controls are withheld.
- **Severity.** The backend returns `NO_EFFECTIVE_REVISION` only when `revision is None` (`backend/assetops_backend/sites/foundation_content.py:231`), which appears to reach the shell's no-version refusal path instead. So this branch is probably unreachable, hence Low.
- **Fix.** If the branch is kept, the Site model should render the panel skeletons with in-panel gaps, as Readiness does through `basisUnresolved`, and the test should assert that.

### 12. Low (residual): the Readiness no-version/refused variant drops the four category cards
Capture: `readiness-no-version-1440-app.png`

The mock row is not a panel, so the guard is satisfied. Optionally, render the four cards with "Unknown", to keep the grid.

## Deviations judged (as asked)
- **SLD title:** acceptable with a note (finding 9).
- **Taller version strip:** not acceptable at its current height (finding 4).
- **Reserve form in the controls panel:** placement acceptable, styling not (finding 7).
- **One site in both lists:** acceptable (finding 10).

## Changed assertions
I diffed the changed tests in `siteFoundationRevision.test.tsx`, `sitesIndex.test.tsx` and `foundationScreen.test.tsx`, and the adjacent route tests. The packet's account is accurate:
- Refusal h2 queries were re-pointed to `[data-page-refusal]`.
- The gateway heading became a regex, under the approved title rule.
- The "Connected" scan excludes only the mandated heading node.
- Unreadable Sites still asserts no digits and no "No sites registered".
- `data-product-status="positive"` is still absent.
- Commissioning is still "Not recorded".

Dropped without replacement: the Sites scope breakdown counts ("Mini-grid: 1", "Demonstration data: 2") and the "Not judged in this list" limit tag. The "does not judge how any site is operating" sentence is still asserted, so no honest-state claim is lost. The only weakened fail-closed path is finding 11.

## Checks I ran (from `frontend/`, PowerShell)
- `npx.cmd tsc --noEmit`: exit 0.
- `npx.cmd vitest run` on 12 files:
  - `siteFoundationRevision`, `foundationScreen`, `sitesIndex`, `sitesIndexRoute`, `siteConfiguration`, `siteDetailRoute`
  - `operatorSiteTabs`, `operatorRouteFrames`, `simulatorLabGate`, `siteTemplateCatalog`
  - `overflowContainment`, `sharedVisualVocabulary`

  Result: **12 files, 515 passed, 0 failed**, 33.7 s. Vitest ran under this sandbox.
- Guard plants: a titled `Panel` fails (good). An h3 `section` card plus an h4 `div.card` passes (finding 1). Both reverted.
- Not rerun:
  - full `npm.cmd test`: the packet cites 75 files, 1948 passed on `78ec219c`, and the reviewed head `2a5d4869` adds only `.agent` files;
  - `npm.cmd run build`, `tools/check-all.ps1` and the capture tool, which needs Chrome, the backend and a dev server.

  For these I relied on the packet's numbers, which I could not verify.

## Captures
- I opened the 1440 app/mock pairs for all four screens in both variants, and the Foundation pair at 390.
- At 390, the Foundation panels stack in mock order.
- The app's rail occupies the top of the 390 page, where the mock hides it. That is shell scope (W1-UX-07), outside this slice, and noted for F5.
- `evidence.json` and the `index.html` pairing are present.
