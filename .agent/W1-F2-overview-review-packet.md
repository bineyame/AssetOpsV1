# W1-F2-overview review packet

Task: W1 structural fidelity rework F2 (`mini`, `dispatch`, `analysis`, `evidence`, `evidence-analysis`). The contract is `D-2026-10-17-mockup-layout-spec` (`.agent/architect-W1-fidelity.md`) and the brief is `.agent/W1-F2-overview-build-brief.md`. Branch `task/W1-F2-overview`, stacked on W1-F1 `2a5d4869`. Frontend only. Not merged.

## Outcome
Each of the five screens now renders exactly its v69 panel set, in v69 order, with v69 titles (plus the approved `dispatch:2` dynamic title). Each uses the mock's layout:
- statusbar, then metric cards, then panels;
- panel 1 full width, then a two-column pair (or pair-then-full for dispatch and analysis).

The W1-UX answer cards (`overview-objective`, `dispatch-story`, `evidence-conclusion`) are gone. Their state line, answer, limits and destination now sit in the mock statusbar or in the owning panel.

When a read is refused, unavailable, closed or awaiting migration, the page states it once in a `div.page-refusal` and then renders the same panel slots, each with the gap stated inside it. This applies on both imported and legacy Sites.

## Files materially changed
- `frontend/src/sites/overviewSlots.tsx` (new): the five-slot `mini` grid, the in-panel "hour not selected" gap, and the refused Overview.
- `frontend/src/sites/SiteWindowOverview.tsx`: the imported-Site selected-day Overview.
- `frontend/src/sites/SiteOverview.tsx`: the legacy Overview and the refusals. Domains became the mock's objective cards; metrics moved to Operating context; periods moved to panel 1.
- `frontend/src/sites/SiteDetails.tsx`: Site information, Provenance and Quick actions moved into one closed `site-record` disclosure under the grid.
- `frontend/src/sites/PerformanceDispatch.tsx`: the imported-Site Dispatch and Analysis. `DispatchSlots` and `DispatchRefused` added; the Analysis view was rebuilt.
- `frontend/src/sites/SitePerformance.tsx`: legacy Dispatch and Analysis. `LegacySlots` and `LegacyRefused` added.
- `frontend/src/sites/LedgerSiteEvidence.tsx` and `EvidenceClaimLimit.tsx`: ledger Evidence and Evidence Analysis. `EvidenceClaimLimit` is no longer a panel.
- `frontend/src/sites/SiteEvidence.tsx`, `CapabilityReadiness.tsx` and the new `panelPart.tsx`: legacy Evidence and its Analysis. Each former panel became a `Part` (an h3-labelled part) of its owning panel.
- Additive changes to F1's shared layer:
  - `ui/V69Layout.tsx`: `StatusBar`, `V69Notice`, `CausalTimeline`.
  - `ui/primitives.css`: `.v69-statusbar`, `-objective`, `-notice`, `-prose`, `-money`, `-timeline`, `-code`, `.panel-part`, and the compact state line inside the statusbar.
  - `ui/index.ts` exports.
  - `.site-window-overview` is now `display: block`.
  - No F1 API was changed or removed.
- `frontend/src/test/v69PanelTitles.ts`: added `V69_TITLES_ON_VOCABULARY_LIST` and `withoutListedV69Titles`. See Known deviations, item 1.

## Per screen: v69 panels vs app
| Screen | v69 panels (order) | App now | Where former app content went |
| --- | --- | --- | --- |
| `mini` | What happened in the selected hour · Operating context · Needs attention · Bounded money consequence · Next step | Same 5. Layout: statusbar (assessment state, scope, as-of, Dispatch link), objective line, 5 objective cards, then panel 1, pair 2+3, pair 4+5. | **Statusbar:** objective answer card. **Panel 1:** "This day" freshness, day selector, assessed periods (causal strip), limitations, exact refs, plus an in-panel "Hour not selected" gap. **Panel 2:** day timeline figure and readings coverage. **Panel 3:** Findings and the Finding list. **Panel 4:** money card. **Panel 5:** Finding and Dispatch links, or "No supported next action". **Cards:** Service, Battery, Fuel and Renewable each read "Not available" with their own note (five-objective gap); Dispatch shows the day reading. **Closed disclosure:** site record. |
| `dispatch` | Sources and 15-minute blocks · Selected block · {interval} · Accepted sample coverage | Same 3. Layout: statusbar, 4 day-total cards, pair, demo-data notice, full panel 3. | **Panel 1:** `dispatch-story` card, block strip, periods. **Panel 2 (title = actual selected block, or "No block selected"):** selected period and day Findings. **Panel 3:** "What limits this day's result", coverage table, comparison line, and the records table (closed disclosure). |
| `analysis` | Constraint comparison · Bounded fuel calculation · Coverage, confidence and alternatives | Same 3, as pair then full. | **Panel 1:** "How the readings lead to the outcome" (h3 steps became plain list items). **Panel 2:** fuel/money gap (baselined text unchanged). **Panel 3:** versions, stored record, limitations and comparison detail. |
| `evidence` | What we can conclude now · Data sources · data quality, not equipment condition · Most useful next evidence | Same 3. Layout: statusbar, panel 1, pair. | **Panel 1:** `evidence-conclusion` card. **Panel 2:** "Which sources reported, and when" (now a key-value list). **Legacy panel 3:** gap "Next evidence not identified". |
| `evidence-analysis` | Accepted records behind the conclusions · How a claim limit is set | Same 2; panel 2 titled "How each limit is set" (approved map entry `evidence-analysis:2`, coordinator ruling 2026-10-17). | **Panel 1:** records list, "Readings not accepted", record detail, and the advanced record disclosures. **Panel 2:** "How each limit is set", the `EvidenceClaimLimit` read, and analysis-status, comparison and gateway disclosures. |

## Fidelity pass 2 (after the F1 merge; `5a7320a7`..`6a6528b2`)
Panel lists are unchanged from the table above; what moved inside and around them:
- **All five:** the statusbar is F1's one-line `.status-strip--line` with inline children only (`ProductStatus inline`; Evidence's local strip carries the strip classes). App-only choosers are `.v69-chips` rows with `.v69-chip-control` inputs and `.button`s (Dispatch day picker before panel 1, Evidence window chooser before panel 1, Overview day selector inside panel 1). Headings are F1's `SitePageHeader`: site name h1, provenance badge with the record's Site ID, per-screen description (`SITE_SCREEN_DESCRIPTIONS` mini/dispatch/analysis/evidence/evidence-analysis). Mock subtitles that state illustrative ratings (mini) or unsupported claims (evidence "capability readiness and claim ceilings", pinned absent by `siteEvidenceScreen`/`t028EvidenceCapability`) are replaced by plain descriptions of what is shown.
- **mini:** assessment state inline in the strip; panel 1 freshness is one note-size line (state + source-open) instead of a second state block; "Hour not selected", day reading, window bounds, money qualifier and Next-step prose are `ChartNote` lines.
- **dispatch/analysis:** stale-totals sentence is a strip span; panel 1 keeps one strip; headline, coverage, pinned notes and empty/none lines are chart-note lines; the block line is a bold line, not an h3; legacy `section.dispatch-view` is a plain `div`.
- **evidence:** rejection count, limits sentence, reporting note and every `NotAvailableYet` are note-size (text byte-identical); closing notice is `V69Notice` (`.notice`); the per-source strip sits below the sources table; the earlier-store disclosure closes the Data sources panel.
- **evidence-analysis:** panel 2 shows two note lines; the four-limit list moved, every statement kept, into a closed `evidence-limit-list` disclosure; the not-accepted and untimed lines are note-size.
- **Retained by F1's rule:** the closed `site-record` disclosure under the Overview grid (closed `<details>` is not on-screen content for the guard).

## Changed assertions (none weakened)
Each change below re-points an assertion at the content's new v69 home and asserts at least as much. Every changed file also adds `expectV69Panels`.
- **`siteOverviewScreen.test.tsx`**
  - Card helpers read the objective cards. `cardFor` returns each card together with its Operating-context block, so every fact the old card held is still asserted for the same domain.
  - The objective strip is the statusbar plus the objective key-values.
  - Unreadable Overview: asserts the page refusal, the 5 panels, the gap inside the panels, and that no cards are drawn. This replaces "heading Overview unavailable" plus "no h3".
- **`overviewDispatchAssessment.test.tsx`:** `cardFor` reads the objective card.
- **`s5SiteWindowOverview.test.tsx`**
  - `objectiveCard()` is now the statusbar (the state line).
  - The disclosure scan runs on the day-reading block in panel 1.
  - "leads with the answer card" became: no headline card, the statusbar is the first child, and the 5 v69 panels are present.
  - The stale headline assertion became: the Dispatch objective card shows "This result may miss newer readings".
- **`siteFoundationRevision.test.tsx`:** Awaiting migration is checked through the page refusal, `data-evidence-state`, and the 5 panels.
- **`performanceDispatch.test.tsx`**
  - The card scope became the dispatch body.
  - The question-text assertion became `expectV69Panels("dispatch", {interval})` plus "no headline card".
  - The disclosure count is scoped to panel 1.
- **`t028Screens.test.tsx`:** unchanged assertions. The legacy question text was kept verbatim.
- **`siteDetail.test.tsx`:** the only control set aside is the `site-record` `<details>` itself. It is a reading control, not a capability. Its buttons are still required to be disabled.
- **`s2LedgerEvidence.test.tsx` and `v01bEvidenceVisual.test.tsx`**
  - The `evidence-conclusion` card selector became `[data-evidence-conclusion]`.
  - The Analysis link is found in the panel-head of "What we can conclude now".
  - The records table header check reads the panel's first table, because the panel now also holds the rejected part.
  - The "How each limit is set" panel is now the v69 "How a claim limit is set".
  - The question-line text became the statusbar text, because the mock has no question line.
  - The vocabulary scans use `withoutListedV69Titles` (item 1 below).
- **`t028Vocabulary.test.tsx`:** same vocabulary filter.
- **Pass 2:**
  - `s2LedgerEvidence`, `t028Vocabulary`, `v01bEvidenceVisual`: the `withoutListedV69Titles` filter and `V69_TITLES_ON_VOCABULARY_LIST` are deleted, so the vocabulary scans are strict again; `V69_EVIDENCE_ANALYSIS_TITLE` is "How each limit is set". Stronger than before.
  - `operatorSiteTabs` "Site Evidence route": h1 `"Evidence"` became h1 = site display name, plus the header contains the Evidence description; the current-tab assertion still pins "Evidence".
  - `siteDetail.test` heading: h1 `site_id` + name as `<p>` became h1 = display name + the provenance badge contains `site_id`. Identity in the header is still pinned.
  - `sitesIndexRoute` row-opens-site: same change (h1 name + badge `site_id`).
  - `siteDetailRoute`: 6 `findByRole(heading, MG-00x)` load anchors now use the display name; the case-variant test adds a badge `site_id` check and keeps the main-text `MG-002`/no `mg-002` checks.
  - `siteDetailScreen` inert-actions: the unchanged-heading check reads the display name.
  - `t028Screens` legacy Dispatch: additive assertions for the v69 heading (h1 not "Performance", badge holds the Site ID, description present) on Dispatch and Analysis.

## New structure tests
- `mini`, in `siteOverviewScreen.test.tsx`, `s5SiteWindowOverview.test.tsx` and `siteFoundationRevision.test.tsx`:
  - legacy: populated, empty, unavailable;
  - imported window day;
  - awaiting migration.
- `performanceDispatch.test.tsx`, "W1-F2: v69 dispatch and analysis panel structure":
  - stocked with a block, a period or nothing selected;
  - empty day, for both views;
  - three refusals (cutover unreadable, closed, window not found), for both views, each checking that exactly 3 panels state the gap.
- `t028Screens.test.tsx`: legacy Dispatch stocked, Analysis, empty, and Performance unavailable.
- `s2LedgerEvidence.test.tsx`: ledger stocked, NO_DATA and REJECTED_ONLY, plus unavailable and not-found refusals, for both views.
- `siteEvidenceScreen.test.tsx`: legacy stocked, empty and unavailable, for both views.

**Planted-panel proof** (at `3d47c582`, reverted with `git checkout`, `git status` clean afterwards):
- A `section.panel` (with an h3) planted before the Overview grid failed `s5SiteWindowOverview` "leads with the day answer…": the statusbar-first assertion failed before the `expectV69Panels` call.
- A titled `<Panel>` planted in ledger Evidence failed all 3 evidence structure tests (`expected [ 'What we can conclude now', …(3) ] to deeply equal […(2)]`).

**Vocabulary filter proof:** "How a claim limit is set" planted inside body text failed "uses no implementation vocabulary". The filter drops only a text node whose whole text is the title.

## Checks run
- `npx.cmd tsc --noEmit`: clean.
- `tools/check-all.ps1`: all 10 guards passed, including architecture, agent workflow, navigation truthfulness and the missing-claim scan (31 tagged, 11 baselined).
- Full `npm.cmd test`, first run: 1964 passed, 1 failed. The failure was `t028Vocabulary` on the v69 title, now handled by the shared filter.
- Final full `npm.cmd test` at `1554f013`: 75 files, **1965 passed, 0 failed**. `tsc` was clean on the same revision.
- Side-by-side captures with `node tools/w1-fidelity-evidence.mjs`. Every run printed all claims passed: app rendered, mock rendered, same panel count, no horizontal overflow. Each folder holds `index.html`, `evidence.json` and `run.log`.

| Folder | Cases | Claims | Data |
| --- | --- | --- | --- |
| `.agent/W1-F2-evidence/mini/` | p01 priced, p02 held, unassessed, failed | 48/48 | Part 2 walkthrough data, `tick` before capture |
| `.agent/W1-F2-evidence/dispatch/` | dispatch supported (2 Oct, block 1), dispatch limited (9 Oct), dispatch failed (7 Oct); analysis supported and limited | 60/60 | Part 7 data |
| `.agent/W1-F2-evidence/evidence/` | evidence stocked, evidence no-readings period; evidence-analysis supported (6 Oct), limited (11 Oct), no selection | 60/60 | Part 6 data, which also has ledger Evidence; Part 4 was not rerun |

- All fixtures were dropped afterwards: `assetops_s3walk`, `assetops_s302_w1f2`, `assetops_s501_owner_w1f2`, and their work folders.
- Ports used: 9150/5650, 9250/5660, 9350/5670 (CDP 9483-9485).

## Known deviations
1. **Resolved:** `evidence-analysis:2` renders "How each limit is set" (coordinator ruling 2026-10-17 under `D-2026-10-16-w1-ux`), added to `APPROVED_TITLE_CHANGES`; the vocabulary exception list is deleted.
2. **Five-objective strip position.** It is rendered where the mock puts it: the metric-card row above panel 1, with each unknown cell individually honest. The Architect's map names panel 2 as the strip's home; the mock layout was followed.
3. **`EvidenceClaimLimit` is not split.** Its role/record spans stay with the limit they explain in panel 2. The map suggested panel 1 for the record spans.
4. **Legacy Evidence and legacy Analysis keep h3-labelled parts inside the owning panel.**
   - Covered: `panelPart.tsx`, plus `AssessmentAnalysis` sections, which are shared with Finding (F3).
   - They add no panel slot. They are still bulky, which is the concern in the coordinator's guard-hardening note. If F1's tightened guard rejects in-panel h3 parts, these need a flatter form.
   - Imported-Site screens (the walkthrough path) use no such parts, except `RecordFacts` h3 in the record detail and the Finding list h3.
5. **Not converted.** The frame-level "No such site" and "Site unavailable" states, and a Performance capability other than Dispatch, stay single panels. These are not valid screen identities for these routes.
6. **Ported from F1 (pass 2):** card top border and state word (Dispatch totals use `word`/`tone`), `.button`/chip controls, `SitePageHeader`. Other Performance subtabs keep the shared "Performance" heading until their own fidelity pass.
7. **Retained `site-record` disclosure.** Under the Overview grid (closed) there is a reference disclosure the mock lacks; F1's guard ignores closed disclosures.
8. **Site page h1 changed from `site_id` to the display name** on the Overview (T012/canonical-screen-2 had chosen `site_id`). This follows the v69 heading and F1's Foundation/Readiness/SLD; the record's `site_id` stays in the header badge and is asserted there.

## Residual risk / reviewer focus
- **Prominence (pass 2):** mini freshness is now one note line; the Evidence per-source strip is below the table; Dispatch panel 1 has one strip. Panel heights vs the mock are in the capture table; compare the 1440 pairs.
- The legacy Site paths have no captures; they are covered by the structure tests only.
- `siteFoundationChange` flake: not hit in these runs.

USER_REVIEW: hold for the combined owner walkthrough after F5, per the contract. Independent review is needed first.

## Panel heights at 1440, app vs mock: pass 2 baseline (`6a6528b2`, before the 1.3x compaction)
Pairs share one row height. Ratio = app / mock; the target is about 1.3 or less (coordinator rule, 2026-10-17).
| Screen · case | Panels (app h / mock h = ratio) |
| --- | --- |
| mini · p01 priced | happened 481/238=2.02 · context+attention 992/373=2.66 · money+next 679/193=3.52 |
| mini · p02 held | 528/238=2.22 · 992/373=2.66 · 582/193=3.02 |
| mini · unassessed | 395/238=1.66 · 469/373=1.26 · 294/193=1.52 |
| mini · failed | 395/238=1.66 · 520/373=1.39 · 294/193=1.52 |
| dispatch · supported | pair 605/489=1.24 · coverage 744/243=3.06 |
| dispatch · limited | pair 380/489=0.78 · coverage 728/243=3.00 |
| dispatch · failed | pair 289/489=0.59 · coverage 749/243=3.08 |
| analysis · supported | pair 349/432=0.81 · coverage 394/287=1.37 |
| analysis · limited | pair 1675/432=3.88 · coverage 416/287=1.45 |
| evidence · stocked | conclude 564/387=1.46 · sources+next 1172/387=3.03 |
| evidence · no readings | 525/387=1.36 · 1299/387=3.36 |
| evidence-analysis · supported | records 1047/266=3.94 · limits 1595/148=10.78 |
| evidence-analysis · limited | 1047/266=3.94 · 1749/148=11.82 |
| evidence-analysis · no selection | 1047/266=3.94 · 630/148=4.26 |
