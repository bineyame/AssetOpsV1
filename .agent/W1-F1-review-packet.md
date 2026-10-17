# W1-F1 review packet: shared mockup layout guard, plus Sites, Foundation, Readiness and SLD rebuilt to v69

- **Branch:** `task/W1-F1-foundation`, worktree `AssetOpsV1-review4`. Not merged.
- **Contract:** `.agent/architect-W1-fidelity.md` (`D-2026-10-17-mockup-layout-spec`).
- **Brief:** `.agent/W1-F1-build-brief.md`.
- **Shared API for F2-F5:** `.agent/W1-F1-handoff.md`.
- **USER_REVIEW:** there is no task file for this slice. Per the contract, the owner does not review until F1-F5 all pass the independent review. This slice needs the independent Reviewer, not the owner yet.

## Outcome
1. The shared guard: `expectV69Panels` and the approved title map. It was proven non-vacuous: on `/sites`, a planted titled `Panel` and a planted untitled `div.panel` each failed the guard (`expected ['Planted extra panel', ...]` and `"(untitled)"`), and both plants were reverted with `git checkout`.
2. The shared v69 CSS and components (see the handoff).
3. Each of the four screens renders exactly its v69 panels, with no leading answer card, in every variant tested.
4. A side-by-side capture tool, `tools/w1-fidelity-evidence.mjs`.

## v69 panel list vs app panel list
In every variant, the panels counted inside `<main>` match the list below. Sources: the structure tests and `evidence.json`.

| Screen | v69 panels | App panels (stocked) | Empty / refused variants |
| --- | --- | --- | --- |
| sites | Site inventory · In setup | Site inventory · In setup | Empty and unreadable directory: the same two panels, with the state inside "Site inventory" and the gap inside "In setup" |
| foundation | Configured topology · Identity & operating obligations · Time-valid control configuration | Configured topology · **Identity and operating obligations** (approved change) · Time-valid control configuration | No-version: the same 3 panels with in-panel gaps. Legacy (not imported) site: the same 3 panels |
| readiness | Readiness and commissioning evidence · Gateway status · GW-MG-01 · Connected sources · Effect on readiness and confidence | The same, with **Gateway status · edge-kobo-001** (approved dynamic title from the selected read) | No-version, unreadable store, not imported: 4 slots with gaps, titled "Gateway status · No gateway selected". Contact unavailable, none or pending: titled from registration |
| sld | Kobo Mini-grid · AC-coupled mini-grid · What each part does | **{site name} · {site type}**, e.g. "Kobo mini-grid · Mini-grid" · What each part does | No-version, unreadable, not imported: 2 slots, the first titled with the route's site ID |

What the app shows outside the panels, and why each is allowed:
- **All four Foundation views:** the version strip (Foundation version, period, as-of, channel links, gaps, period selector and the "How this was worked out" exact references) sits above the panels. It is a `section.status-strip` with no h2, matching the mock's status strip.
- **Readiness:** the metric cards row sits above the panels, also matching the mock.
- **Sites:** the type chips and the 3 metric cards sit above the panels, matching the mock.
- **Page-level refusals:** these are `div.page-refusal[data-page-refusal]` and are never panels.

## Files materially changed
- **Shared:** `frontend/src/test/panelStructure.ts`, `frontend/src/test/v69PanelTitles.ts`, `frontend/src/ui/V69Layout.tsx`, `frontend/src/ui/primitives.css`, `frontend/src/ui/tokens.css`, `frontend/src/ui/Panel.tsx`.
- **Screens:**
  - `frontend/src/sites/SitesIndex.tsx`
  - `frontend/src/sites/StoredFoundationViews.tsx`
  - `frontend/src/sites/ReadinessOverview.tsx`
  - `frontend/src/sites/FoundationBindingsPanel.tsx`
  - `frontend/src/sites/FoundationRevisionPanel.tsx`, which now holds the strip's exact references
  - `frontend/src/sites/SiteConfiguration.tsx`, the legacy model view rebuilt into the 3 panels
  - `frontend/src/shell/SiteFoundationFrame.tsx`, where the refusals and legacy notices are now page-level statuses
  - `foundationHeadlines.tsx` was deleted
- **Catalogue and tooling:** `frontend/src/ui/gapCatalogue.ts` (placements unchanged; it mirrors the registry), `tools/g02-gap-evidence.mjs` (texts), `tools/w1-fidelity-evidence.mjs` (new).

## Code fixes made while repairing tests (not assertion changes)
- **Effect on readiness:** the panel repeated the readiness statement word for word, so a test found two copies. The panel now says the verdict is configuration only and does not restate it.
- **Readiness "What to do next":** with an unrecognised readiness code it said "nothing else is missing from the set-up". That claim was not fail-closed. It now says the state is not recognised. "Nothing else is missing" is said only for `READY_TO_REPORT`, and a known non-ready state with no listed step gets a neutral line.
- **Not-imported Readiness and SLD:** these views had gained a view row. It was removed again, keeping the settled rule that a legacy site has no view row.
- **Gateway metric values:** "Not available yet" became "Not available". The missing-claim scan flagged the untagged copy; the tagged note carries the claim.
- **Banned W1 word:** "Claim limits..." in the Effect panel was reworded to avoid a banned W1 word.
- **Sites counts:** the setup gap text avoids "history" and "created", which settled forbidden-action and no-Simulator assertions ban. The two count cards share one claim rendered once, because a placement renders once and the registry was left unchanged.

## Changed assertions (none weakens an honest-state or fail-closed check)
Abbreviations: `R` = `src/shell/__tests__/siteFoundationRevision.test.tsx`, `S` = `src/sites/__tests__/sitesIndex.test.tsx`.

**Renamed heading**
- `R` gateway tests (V-01a r3, G-01, G-02, about 15 sites): the heading `"Gateway status"` became the regex `/^Gateway status · /` (approved title readiness:2). The G-01/G-02 10 s timeouts were `findByRole` waiting on the old heading name, not a code bug. Each now passes in milliseconds.
- `R`: `"Identity & operating obligations"` became `"Identity and operating obligations"` (approved title foundation:2).
- `R` SLD parts: `"What each configured part is"` became `"What each part does"` (the v69 title). Its column assertions are now scoped to the panel's own `table`, because the Advanced disclosure moved inside the panel.

**Removed panel or card**
- Refusals (`R:504`, `:860`, `:883`, `:517`): an h2 role query became a check on the `[data-page-refusal=<kind>]` text, through the new helper `refusal()`. The not-imported checks still reject "Stored versions unavailable", and vice versa.
- `R` W1-UX-05 vocabulary test: it scanned the answer card's disclosure. It now scans the strip's exact-reference disclosure. The W1 scan, both open and closed, is unchanged, and the test also asserts that no `[data-headline-card]` exists.
- `R` W1-UX-05 answer-card tests (12): each fact was re-pointed to its new home.
  - "in effect now" and "Scheduled" are the strip state, with as-of and gap count.
  - The missing setting is the "Generator start / stop" row in the controls panel, which says it "declares no generator start or stop threshold".
  - `rev-2` and the exact time are the strip references.
  - The readiness verdict state and badge tone, `data-readiness-next-steps`, the commissioning row "Not recorded", and gateway "registered" (not contact) all live in panel 1.
  - For an unrecognised code: a neutral badge, the code in the references, and the new fail-closed next-step line.
  - Empty period and unreadable store: the state line, scope and as-of are now inside `data-page-refusal`.
  - SLD: `data-sld-summary` inside the SLD panel, with "1 of N devices have a linked reading channel" and "Whether linked parts are reporting is not assessed here."
  - Dropped: step-strip state counts (there is no step strip in v69), and the headline wording "N of 5 operating settings". Each setting's state is still asserted in its own table row.
- `R:305`: unchanged. The strip still never shows the content digest, so the strip references leave it out.
- `S` W1-UX-02 card tests (3): the state line, limit sentence and closed exact references are now inside "Site inventory" (`data-sites-state`). The registered count is the first metric card. The empty and unreadable states still show no digit ("None" and "Unavailable"), and unreadable still never says that no site is registered.
- `S` aggregate note: it became the metric cards (the count is supported; Needs attention and Evidence limited are "Not available" with one tagged claim) plus the setup gap in "In setup".
- `S` G-02: in the empty and unreadable states the old check was "no gap tagged". It is now "exactly the count and setup gaps, plus `expectV69Panels`". This is required by the contract ("panel skeletons with in-panel gaps"), and no per-row gap appears when there are no rows.
- Legacy model:
  - `src/sites/__tests__/siteConfiguration.test.tsx:486`: the h2 became an h3.
  - `src/sites/__tests__/foundationScreen.test.tsx` (about 397 and 674): the section-order checks became `expectLegacyFoundationPanels`. It asserts the exact 3 panels, with the Definition, Topology and Controls anchors as h3s inside their owning panels. At about 438, 468, 488 and 500, the scope changed to `section.panel h3` or `.subsection`. The Key-parameter no-dash, no-zero checks are unchanged.

**New panel order or second table**
- `R` panel-order tests (Site model, Readiness, SLD): `sectionOrder` became `expectV69Panels`. The tests also check: strip first, the reserve form and Foundation-records disclosure inside panel 3, Role coverage, links and Acquisition (in that order) inside panel 1's Advanced disclosure, and the parts disclosure inside "What each part does".
- `R` cards order: the cards precede the evidence heading, which precedes the gateway heading, checked by DOM position.
- `R` evidence-table columns and plain layer: scoped to the panel's own table, or to the panel minus its Advanced disclosure (which still must not hold `b-battery-soc`).
- `R` gateway unavailable: the `/Connected/` scan excludes only the mandated "Connected sources" heading. All other words are still scanned.
- `S`, `sitesIndexRoute`, `siteDetailRoute`, `operatorSiteTabs`, `overflowContainment`, `sharedVisualVocabulary`: `ByRole("table")` became the table named "Site inventory", because "In setup" is a second table.
- `operatorRouteFrames`, `simulatorLabGate`, `siteTemplateCatalog`: the empty and unavailable h2 queries became `findByText`, since the state is now inside the panel.
- `S` filters: the Type select became the v69 chips, `data-site-filter`, with options "All sites" plus the types present. The interactive-control list now starts with the chip buttons, and the combobox list is `sites-mode` and `sites-lifecycle`.

## Structure tests (new)
- **`/sites`:** `sitesIndexRoute.test.tsx`, "W1-F1: the Sites route keeps the v69 panel structure", stocked, empty and unreadable. Also covered in `S` for loaded, empty and unavailable.
- **Foundation, Readiness, SLD:** `R`, "W1-F1: Foundation, Readiness and SLD keep the v69 panel structure in every variant", 12 tests:
  - stocked, for each of the 3 views
  - no-version, for each view, with the count and text of each in-panel gap
  - unreadable store and not-imported, for readiness and sld
  - gateway contact unavailable, none or pending
  - no registered gateway, titled "No gateway selected"
- **Legacy model:** `foundationScreen.test.tsx`, plus `R:517` through the app route.

## Checks run (final revision 78ec219c, frontend-only slice)
- `npm.cmd test`: **75 files, 1948 passed, 0 failed**, wall 122 s. An earlier full run on c6063222 found 12 failures in adjacent Sites tests. They were fixed in 78ec219c, and only then was this run made.
- `npx.cmd tsc --noEmit`: exit 0. `npm.cmd run build`: built (exit 0; chunk-size warning only).
- `tools/check-all.ps1`: **All 10 guards passed**. This includes architecture, agent workflow, navigation, the missing-claim orphan scan (31 tagged uses) and the screen ledger.
- **Missing-claim scan on the new SLD sentence** "Whether linked parts are reporting is not assessed here.": no pattern matches. The `readings?…not assessed` pattern needs the word "reading", and the scan passed.
- No backend change, so no backend run.

## Captures
- **Location:** `.agent/W1-F1-evidence/` (force-added). `index.html` shows every pair side by side. `evidence.json` records URLs, mock hash, revision, viewport, titles, panel boxes and overflow. `run.log` has 96/96 claims passing.
- **Pairs,** each `<id>-<case>-<1440|390>-{app,mock}.png`:
  - sites stocked and empty
  - foundation now and no-version
  - readiness now and no-version
  - sld now and battery-selected
- **Data:** `v01a_foundation_walkthrough.py` on API 8970/8971 and web 5470/5471. Ports 8960 and 5460 were held by another process. The fixtures were dropped afterwards.

## Known deviations
1. **SLD title:** it uses the site type ("Mini-grid") as the configured type, because the Foundation read has no topology-type field (the approved rule says "if stated"). The skeleton states use the route site ID and say "Site type unknown".
2. **Strip height:** the Foundation strip is taller than the mock's one-line strip. It holds the period selector, the channel-link line and the exact references that the removed answer cards carried.
3. **Reserve form:** the reserve-change form sits inside panel 3, below the controls table. The mock has no edit form, but the contract puts policy and controls there.
4. **In setup columns:** the panel lists sites whose recorded lifecycle is not Active (Site, Type, Lifecycle). The mock's Created by, Next step and Created columns have no read and are covered by one gap. In this demo a site appears in both Site inventory and In setup, whereas the mock lists in-setup sites only in setup.
5. **Gateway skeleton:** the slot nests "Connected sources" and "Effect" inside the gateway panel, as the stored view does and as the mock nests them.

## Residual risk
- The guard ignores closed `<details>`. Opening "Advanced details" on Readiness reveals nested `Panel`s (Role coverage and others), which are not counted.
- Visual density at 390 for readiness and sld is for the Reviewer to judge from the captures. Overflow was measured at 0 on every app capture.

## User-review focus
For the Reviewer: compare every capture pair at both widths, especially the strip height on Foundation and the In setup duplication on Sites. Also check the changed-assertion list above.

## Fix round 1 (review `.agent/W1-F1-review.md`, RETURN)
Commits: `9767f963` and `601acc8d` (guard), `c50dc97d` (build), `ce42ef17` (Lows 9 and 10), `d7f544d3` (CSS sizes; captures). Frontend only.

| # | Finding | Fix | Anchor |
| --- | --- | --- | --- |
| 1 High | Guard bypass by an h3/section card | `expectV69Panels` now runs two more checks. **Leading allowlist:** before panel 1, only page chrome (`nav`, `header.page-header`) and `.status-strip`, `[data-page-refusal]`, `.v69-cards`, `.v69-chips`, `[data-selected-part-missing]`, `[data-selected-part-chip]` may render. **No stray sections:** an `h3`-`h6`, `section`, `article`, `[role=region]`, `.card` or `.callout` outside a panel or leading pattern fails. | `frontend/src/test/panelStructure.ts` (`leadingIntruders`, `strayOutsidePanels`) |
| 1 proof | Non-vacuity | New `src/test/__tests__/panelStructure.test.ts`, 5 tests. A planted h3 `section.callout`, a headingless `div.callout`, an h4 `div.card` and a stray h3 subsection all fail; mock chrome and leading patterns pass. With the leading check neutered, 2 of these tests failed (reverted). The reviewer's product plant (an h3 `section.callout` after the strip in `SiteModelView`) failed 2 route tests with `elements before panel 1 … <section class="callout"> "What is configured for this period?…"`, reverted with `git checkout`. The tree is clean. | |
| 2 High | Bulky Readiness verdict | The verdict now leads the strip: `[Set up to report] Configuration readiness is distinct from what the readings can support`, then the compact Foundation version. Removed from panel 1: the heading, the banner, the legend, the paragraphs and "What to do next". What remains is three `v69-chart-note` lines under the table: (a) the verdict reason with named Foundation gaps and the read's own statement; (b) the colour scope: configuration only; green does not mean a device is connected, records have arrived, Evidence is accepted or equipment is in good condition; (c) `Next step:`. | `FoundationBindingsPanel.tsx` (`ReadinessVerdictLead`, `ReadinessVerdictNotes`); `StoredFoundationViews.tsx` (`ReadinessNextSteps`, `ReadinessView`) |
| 3 | Category cards | New `MetricCard assessment`: a 3 px tone top border (green, amber or grey) and a 17 px state word. The Readiness cards use it. | `ui/V69Layout.tsx`, `ReadinessOverview.tsx` |
| 4 | Strip height | The strip is one flex line: badge, effective period, state, channel links and gaps, as-of. After them: a 200 px chip-sized selector (aria-label kept; the visible "Period shown" label is dropped), the next link, and a link-styled `details.tech`. The historical note is shortened. | `FoundationRevisionPanel.tsx` (`FoundationPeriodStrip`); `ExactReferences variant="tech"` |
| 5 | Sites callout and toolbar | Both are removed. Search, Mode and Lifecycle become chip-sized controls in the chip row, with visually hidden labels. The panel now runs: head → table → one note line (`Registered sites, not ranked · All registered sites · As of: time not recorded. …`) → `details.tech`. | `SitesIndex.tsx` (`SitesDirectory`) |
| 6 | Page heading | Shared `SitePageHeader`: the site name as h1, a `.prov-tag` badge (`Demonstration data · KOBO-001`), and the screen description from `SITE_SCREEN_DESCRIPTIONS` (foundation, readiness, sld). It is used by the stored views, by the refusal branches (Site ID as the name, no badge) and by the legacy Site model. | `ui/V69Layout.tsx`, `SiteFoundationFrame.tsx`, `SiteConfiguration.tsx` |
| 7 | Form controls | Ported `.input-row`, `.field`, `.button`, `.button.primary` and `.form-footer`. The reserve form now uses `.field` inputs and a primary submit button. The refusal action uses `.button.primary`. | `ui/primitives.css` (fix-round section); `FoundationRevisionPanel.tsx` |
| 9 Low | SLD title | The title is the site name alone. The panel description says "Topology type not stated in this version · …". | `sldPanelTitle` |
| 10 Low | Site in both lists | The In setup description now adds: "they are also listed in Site inventory". | `SitesIndex.tsx` |
| 11 Low | NO_EFFECTIVE_REVISION | The Site model now fails closed. It shows the strip, then three skeleton panels, each saying "No configuration for this period: … No equipment or settings are recorded for the selected time." The test asserts the structure, that text in every panel, no part tiles, no tables and no reserve form. | `SiteModelView`; test "a scheduled period is never called in effect now" |

**Not done:** Low 8 (condensing the SLD prose) and Low 12 (Unknown cards in the refused Readiness view). These are density or optional changes, left for the F5 sweep.

**Changed assertions.** None weakens an honest-state check.
- The h1 "Foundation" checks now expect the site name, plus subtitle and provenance (`siteFoundationRoute` ×5, `foundationScreen` ×2).
- `panel("Configuration readiness")` is split. `verdictLead()` covers the badge and its tone. `readinessPanel()` covers the reason, statement, missing roles and gaps.
- The legend-chip test is now a scope-line test that names all three colours and asserts the legend is absent.
- The separation sentence is asserted in the strip and in the page's gateway note.
- Card `.badge` checks now read the value text and the `v69-metric--{green,amber,muted}` class.
- The Sites interactive-control order follows the new DOM. The controls are the same and none was added.
- The unrecognised-state sentence is read from `.verdict__sentence`.
- The SLD title values drop `topology`.

**Checks** (this branch):
- `npx.cmd tsc --noEmit`: exit 0.
- Focused, on `ce42ef17`: 6 files, 238 tests, all passing (`siteFoundationRevision`, `sitesIndex`, `sitesIndexRoute`, `foundationScreen`, `siteFoundationRoute`, guard unit tests).
- Full `npm.cmd test` on `ce42ef17`: **76 files, 1953 passed, 0 failed**, wall 183 s. `d7f544d3` changes CSS only.
- `npm.cmd run build`: built, with the chunk-size warning only.
- `tools/check-all.ps1`: **all 10 guards passed**.

**Captures** (`.agent/W1-F1-evidence/`, revision `d7f544d3`):
- Same 8 cases as before. 96/96 claims passed; overflow is 0 on every app capture.
- Servers: API 8970/8971 and web 5470/5471, because 8960 and 5460 were held by another worktree. The fixture databases `assetops_v01a*_w1f1fix` were dropped afterwards.
- Panel 1 top position at 1440, with the mock's 108 px review/top bars subtracted:

| Screen | App (px) | Mock (px) | Note |
| --- | --- | --- | --- |
| Foundation | 339 | 308 | the review measured about 115 px low |
| Readiness | 499 | 434 | |
| SLD | 339 | 308 | |
| Sites | 291 | 374 | |

- Readiness panel 1 height: 592 px vs the mock's 364 px (it was about 2× the mock before).
- Foundation strip: about 73 px on 2 lines vs the mock's 44 px (it was about 160 px).

**Known deviations (fix round)**
1. At 1440 the strip takes 2 lines (about 73 px), not 1. It carries channel links, gaps and the as-of time, which the mock's strip does not, so the selector and links wrap to the second line.
2. Readiness panel 1 keeps the closed, full-width "Advanced details" disclosure, which holds the role, binding and acquisition Panels. Together with the six table rows and three note lines, this keeps the panel taller than the mock.
3. The SLD panels remain taller than the mock (Low 8 not done).

## Fix round 2 (re-review finding A, Lows B and C)

Commit `f95c9f41` plus captures. Frontend only.

| Item | Change | Where |
| --- | --- | --- |
| A, SLD | The two introduction paragraphs, the bindings statement and the "not declared / not assessed" paragraph now use `v69-chart-note` (10 px). Wording is unchanged. | `SiteSingleLineDiagram.tsx` (`SiteSldIntroduction`, `data-sld-bindings`), `StoredFoundationViews.tsx` (`data-sld-missing`) |
| A, Gateway panel | The period note (was a `notice`), the "Read at" line and the unavailable/none sentences are `v69-chart-note`. The key-value row is kept. | `ReadinessOverview.tsx` |
| A, Sites | The "Assessment, top issue..." sentence is `v69-chart-note` (kept as the one scope note). | `SitesIndex.tsx`, `primitives.css` (`.v69-chart-note.panel__note`, `.not-available-yet.v69-chart-note`) |
| B | `expectV69Panels` also runs `stripIntruders` (any heading, paragraph, div, list or table in `.status-strip` that is not a `status-strip__*` part) and `strayBetweenPanels` (a non-empty sibling of a panel that is not a panel, panel wrapper, chrome, leading pattern, `.notice`, `.note` or `[data-readiness-scope]`). | `test/panelStructure.ts` |
| C | The no-version refusal has breadcrumbs (Sites / KOBO-001 / Foundation), no repeated Site ID badge, and the ISO timestamps in the server message are shown as plain times. | `SiteFoundationFrame.tsx`, `V69Layout.tsx` (`hideBadge`) |

**Deviation:** the full text was not moved into the closed disclosure. It stays in place at note size, so every statement is still present exactly once and no assertion changed. The disclosure move would duplicate text and break unique-text assertions.

**Planted tests (non-vacuity):** `panelStructure.test.ts` gained 4 tests. Bulk planted in a strip (28 px div with bold and a paragraph) fails with "blocks inside the status strip". A bold-label div between panels fails with "content blocks between panels". A one-line strip and a `.notice` between panels pass. Both guards ran clean on the real screens (`siteFoundationRevision.test.tsx`, 107 tests). No existing assertion changed.

**Checks:** `tsc --noEmit` clean. Focused 22 files / 839 passed. Full `npm.cmd test`: 76 files, 1957 passed. `tools/check-all.ps1`: all 10 guards passed.

**Captures** (revision `f95c9f41`, `.agent/W1-F1-evidence/`, ports 5480/5481 and 8980/8981, fixtures dropped): 96/96 claims, overflow 0. Panel heights at 1440 (app vs mock; round 1 in brackets):
- Sites: inventory 289 vs 314 [300]; In setup 234 vs 253 [234].
- Readiness: panel 1 592 vs 364 [592]; Gateway status 845 vs 561 [902].
- SLD: drawing panel 974 vs 596 [1055]; parts panel 640 vs 287 [640].

SLD and Gateway panels are still taller than the mock; the remainder is data-driven (drawing, 10-row parts table, sources and effect lists). The SLD note text is about 80 px lighter, the Gateway panel 57 px.

## Coordinator after fix-2 re-review (2026-10-17)

- A2 fixed: the Gateway contact sentence, both source-count sentences and the signal-strength and firmware lines are now `v69-chart-note`; wording and assertions unchanged. tsc clean; full `npm.cmd test` 1957 passed. Readiness recapture deferred to the W1-F5 all-screens capture audit.
- Carried to F5: Low D (SLD row pitch ~143 vs ~106 px, repeated "Readings not assessed here", empty canvas), Low F (strip check skips any `status-strip__*` class), body-size closing scope note on Readiness, "Setup progress not available" on Sites, SLD description indent.
