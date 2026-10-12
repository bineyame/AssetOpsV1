# V-01a round 2 handoff: phase 2a and 2b landed (round complete, in review)

Branch `task/V-01a-foundation-visual`. Round-2 base: `13620b6`. Authority: `.agent/architect-V-01a-answers.md` items 1-5, `D-2026-10-12-v01a-owner-visual-rulings`, owner text `.agent/owner-V-01a-feedback-2026-10-12.md` (including "Follow-up" and "Follow-up 2" at lines 15 and 19, added mid-round by the coordinator: match the mock's tab-header styling, colours and type sizes; restyle the left navigation like the mock, with icons).

## Phase 2a landed (3 commits)

- `83b81f3` **Site inventory (item 1).** `frontend/src/sites/SitesIndex.tsx`:
  - The columns are now Site (name link, then `id · location` as a `.cell-secondary`), Type, Mode (provenance badge), "Setup details" and Actions (View).
  - "Setup details" is a `<details class="site-setup">` holding a `<dl>` of Lifecycle, Configuration origin and Created from template.
  - The `Last analysed` column is removed, along with `lastAnalysed` and `NO_ANALYSIS_IN_WINDOW` from `siteViewModel.ts`.
  - `DIRECTORY_ANALYSIS_ABSENT` is the Architect's exact sentence, rendered under the table as `p.panel__note[data-testid=sites-analysis-absent]`.
  - CSS is in `ui/primitives.css` after `.cell-secondary`. Tests are in `sites/__tests__/sitesIndex.test.tsx`.
- `75c4824` **Readiness (item 2).**
  - `ui/Badge.tsx` has new tones `configured` (green) and `config-gap` (amber). Their tokens are in `ui/tokens.css` (`--badge-configured-*`, `--badge-config-gap-*`, the mock's `.badge.green` and `.badge.amber`). A CSS `::before` tick or "!" is the shape cue, so the badge's text content stays the word.
  - In `sites/FoundationBindingsPanel.tsx`:
    - `READINESS_TONE` colours the verdict: READY is green, INCOMPLETE is amber, UNKNOWN is neutral.
    - `roleTone()`: a configured role is green, a required unbound role is amber, and an optional unbound role is neutral.
    - `ReadinessLegend` renders a legend and a colour-scope line (`[data-readiness-legend]`, `[data-readiness-colour-scope]`).
    - The `.verdict[data-readiness-state]` colours are green, amber or neutral.
  - The PRE-S3-04 sentence and the "Binding vN" neutral badge are unchanged. The stale "awaiting credentials / no accepted evidence" copy was already absent (an existing test asserts that).
- `cf8ccd0` **Component selection (item 3).**
  - `shell/operatorSiteRoutes.ts`: `siteFoundationViewHref(siteId, segment, at, component?)` and `FOUNDATION_COMPONENT_PARAM = "component"`.
  - `shell/SiteFoundationFrame.tsx`:
    - `selectComponent` and the `partDeclared` check.
    - An effect clears an undeclared `component` with `replace`. It also records `missingPart {id, at}` so the notice shows only for that period.
    - The view hrefs carry `component`.
  - `sites/StoredFoundationViews.tsx`:
    - New props `selectedComponent`, `missingComponent` and `onSelectComponent`.
    - The notice `[data-selected-part-missing]` reads "Selected part is not in this Foundation period".
    - `SelectedPartPanel` (`[data-selected-part]`) appears on all three views, with channels from `partChannels()` for the selected period and a "Clear selected part" button.
    - `PartChoice` buttons (`aria-pressed`, `data-part-choice`) are on the topology cards and the parts-table rows. Selected cards and rows get `[data-selected]`.
  - CSS (`.part-choice`, `.part-clear`, `.notice`, `.notice--attention`) is at the end of `primitives.css`.
  - Tests: `shell/__tests__/siteFoundationRevision.test.tsx`, describe blocks "V-01a round 2: configuration-only…" and "…a chosen part stays chosen by component ID".

## Proofs and checks so far

- Non-vacuous runs, each restored with `git checkout`:
  - The old SitesIndex and view model fail 6 of 26 tests.
  - The old FoundationBindingsPanel fails 4 of 47. The Unknown-neutral test passes on the old code, because the old code was already neutral.
  - The old frame fails 4 of 51.
  - With the frame's clearing effect disabled, 2 of 51 fail.
- `vitest run src/sites src/shell`: 52 files, 1279 tests passed.
- `tsc --noEmit`: clean.
- Not yet run: the full vitest suite, build, `tools/check-all.ps1`, layout evidence.

## Phase 2b to do

1. **Item 4: bus-bar SLD and icons.**
   - `sites/sldViewModel.ts` holds the archetype lattice. `ARCHETYPE_LANES` is around line 379, `assignRows` around 498, and the placement around 692.
   - `sites/SiteSingleLineDiagram.tsx`: `boxFor` around line 185, node `<g class="sld-node">` around 370, the scroll region around 549. `SldUnavailable` (the typed unavailable state) must stay.
   - Recompose as source → horizontal bus → loads, using only the declared nodes and connections.
   - Add semantic icons per `SldSymbol`/`COMPONENT_TYPE_LABELS` (`siteViewModel.ts` around line 203), with accessible names. Use the same icons on the topology cards (`StoredFoundationViews.tsx`, `TopologyCards`).
   - Add the label "Configured, not live".
   - Make the nodes focusable and selectable through `onSelectComponent`, if feasible.
   - Do not draw breakers, meters or ratings that are not declared. Check 390 px readability.
   - Tests: `sites/__tests__/sldViewModel.test.ts` and `sldFixtures.ts`. Only the hybrid-mini-grid archetype exists in the fixtures.
2. **Owner follow-ups (shared).**
   - The tab-header styling: Site tabs and Foundation subtabs (`sites/FoundationSubtabs.tsx`, `shell/operatorSiteTabs.tsx`). The mock uses neutral text and only the active tab is emphasised.
   - Type and colour tokens (`ui/tokens.css`) aligned with the mock CSS at `frontend/mockups/v69/index.html` lines 2-80. The mock tokens are `--ink #17243b`, `--muted #617087`, `--line #e0e6ef`, `--page #f5f7fb`, `--navy #16233f`, `--green #168262`, `--amber #a46008`.
   - The left nav (`ui/NavRail.tsx`; `.nav-rail*` at `primitives.css` line 186 and around 2059) gets icons per root. Keep navigation truthful: `tools/check-all.ps1` includes the navigation guard.
   - Run the Dispatch, Finding, Evidence and Lab tests for regressions.
3. **Item 5: evidence and walkthrough.**
   - Refresh `tools/v01a-foundation-evidence.mjs` (309 lines). Its Sites claim at around line 176 still expects "Mode is provenance" and one row; add the new note and the column set.
   - Add selection and missing-part states, computed-style comparisons for tabs, type and nav at 1440 and 390, and nav icons.
   - Refresh `tools/v01a_foundation_walkthrough.py` and `.agent/V-01a-owner-walkthrough.md`.
4. **Closeout.**
   - Add a "Round 2" section to `.agent/V-01a-review-packet.md`, with per-panel records and accepted differences.
   - Add a short V-01a round 2 entry to `.ai/CODE_STATE.md` and update `.ai/ACTIVE_CONTEXT.md`. The task Status stays `in_review`.
   - Run the full vitest suite, `tsc`, the build, `tools/check-all.ps1` (`-ExecutionPolicy Bypass`) and the bounded layout evidence.

## Open risks

- The `missingPart` notice is component state. It disappears on reload, by design, once the address no longer names the part.
- The parts table at 390 px already scrolls horizontally (accepted difference C2). The new selection buttons sit in the first column, so they stay reachable.
- The `configured` green is close to the provenance badge green. The tick mark and the context (Readiness only) distinguish them; recheck this visually in 2b.

## Phase 2b landed (`4b9cd68..16d1095`)

- Item 4: bus-bar SLD, type icons (SLD and cards), "Configured, not live", keyboard-selectable parts. See
  the packet's "Round 2" section and the `.ai/CODE_STATE.md` entry "V-01a round 2".
- Follow-ups 1-2: mock tabs, type, colours and rail with icons, in shared tokens. Item 5: evidence tool
  105/105, walkthrough links and owner guide refreshed. Closeout: packet, CODE_STATE, ACTIVE_CONTEXT.
- Next: a fresh independent fix re-review over `git diff 13620b6..HEAD`, then the owner's visual checkpoint.
  No phase 2c.

