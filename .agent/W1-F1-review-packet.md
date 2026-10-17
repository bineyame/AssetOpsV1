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
