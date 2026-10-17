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
| `mini` | What happened in the selected hour Â· Operating context Â· Needs attention Â· Bounded money consequence Â· Next step | Same 5. Layout: statusbar (assessment state, scope, as-of, Dispatch link), objective line, 5 objective cards, then panel 1, pair 2+3, pair 4+5. | **Statusbar:** objective answer card. **Panel 1:** "This day" freshness, day selector, assessed periods (causal strip), limitations, exact refs, plus an in-panel "Hour not selected" gap. **Panel 2:** day timeline figure and readings coverage. **Panel 3:** Findings and the Finding list. **Panel 4:** money card. **Panel 5:** Finding and Dispatch links, or "No supported next action". **Cards:** Service, Battery, Fuel and Renewable each read "Not available" with their own note (five-objective gap); Dispatch shows the day reading. **Closed disclosure:** site record. |
| `dispatch` | Sources and 15-minute blocks Â· Selected block Â· {interval} Â· Accepted sample coverage | Same 3. Layout: statusbar, 4 day-total cards, pair, demo-data notice, full panel 3. | **Panel 1:** `dispatch-story` card, block strip, periods. **Panel 2 (title = actual selected block, or "No block selected"):** selected period and day Findings. **Panel 3:** "What limits this day's result", coverage table, comparison line, and the records table (closed disclosure). |
| `analysis` | Constraint comparison Â· Bounded fuel calculation Â· Coverage, confidence and alternatives | Same 3, as pair then full. | **Panel 1:** "How the readings lead to the outcome" (h3 steps became plain list items). **Panel 2:** fuel/money gap (baselined text unchanged). **Panel 3:** versions, stored record, limitations and comparison detail. |
| `evidence` | What we can conclude now Â· Data sources Â· data quality, not equipment condition Â· Most useful next evidence | Same 3. Layout: statusbar, panel 1, pair. | **Panel 1:** `evidence-conclusion` card. **Panel 2:** "Which sources reported, and when" (now a key-value list). **Legacy panel 3:** gap "Next evidence not identified". |
| `evidence-analysis` | Accepted records behind the conclusions Â· How a claim limit is set | Same 2; panel 2 titled "How each limit is set" (approved map entry `evidence-analysis:2`, coordinator ruling 2026-10-17). | **Panel 1:** records list, "Readings not accepted", record detail, and the advanced record disclosures. **Panel 2:** "How each limit is set", the `EvidenceClaimLimit` read, and analysis-status, comparison and gateway disclosures. |

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
- **Pass 1** (unchanged; detail in git history of this packet at `6a6528b2`): `siteOverviewScreen` and `overviewDispatchAssessment` card helpers read the objective cards (each card with its Operating-context block); `s5SiteWindowOverview` reads the statusbar as `objectiveCard()`, scans the panel 1 day-reading block and asserts no headline card + 5 panels; `siteFoundationRevision` checks Awaiting migration via the page refusal and 5 panels; `performanceDispatch` scopes to the dispatch body and panel 1 and asserts `expectV69Panels`; `siteDetail` sets aside only the `site-record` details (its buttons still required disabled); `s2LedgerEvidence`/`v01bEvidenceVisual` re-point the conclusion selector, Analysis link, records header, panel title and statusbar text.
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
- A `section.panel` (with an h3) planted before the Overview grid failed `s5SiteWindowOverview` "leads with the day answerâ€¦": the statusbar-first assertion failed before the `expectV69Panels` call.
- A titled `<Panel>` planted in ledger Evidence failed all 3 evidence structure tests (`expected [ 'What we can conclude now', â€¦(3) ] to deeply equal [â€¦(2)]`).

**Vocabulary filter proof:** "How a claim limit is set" planted inside body text failed "uses no implementation vocabulary". The filter drops only a text node whose whole text is the title.

## Checks run
- Pass 2 (`1554f013`): `tsc` clean; `check-all` 10/10; full `npm.cmd test` 75 files, 1965 passed.
- Compaction, final code revision `8270c9a6`: `npx.cmd tsc --noEmit -p .` clean; full `npm.cmd test` 76 files, **1984 passed, 0 failed**, wall 271 s; `tools/check-all.ps1` all 10 guards passed.
- Captures (`node tools/w1-fidelity-evidence.mjs`, same targets as pass 2; Part 2 data with `tick` before capture, Part 6 and Part 7 data; Part 6 revision ids are new per prepare): `mini/` 48/48 at `8270c9a6`, `dispatch/` 60/60 at `ff1bc248`, `evidence/` 60/60 at `8270c9a6` (168/168). Ports 9250/5660, 9150/5650, 9350/5670, CDP 9483-9485. One dispatch run and one mini run first failed panel-count/"rendered" claims while a fixture prepare loaded the machine; both reruns passed in full and are the recorded runs.
- Fixtures dropped afterwards: `assetops_s501_owner_w1f2` + `var\s501_owner_w1f2`, `assetops_s302_w1f2` + `var\s302_w1f2`, `assetops_s3walk` + `%LOCALAPPDATA%\AssetOps\s3-dispatch-walkthrough`.

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
| Screen Â· case | Panels (app h / mock h = ratio) |
| --- | --- |
| mini Â· p01 priced | happened 481/238=2.02 Â· context+attention 992/373=2.66 Â· money+next 679/193=3.52 |
| mini Â· p02 held | 528/238=2.22 Â· 992/373=2.66 Â· 582/193=3.02 |
| mini Â· unassessed | 395/238=1.66 Â· 469/373=1.26 Â· 294/193=1.52 |
| mini Â· failed | 395/238=1.66 Â· 520/373=1.39 Â· 294/193=1.52 |
| dispatch Â· supported | pair 605/489=1.24 Â· coverage 744/243=3.06 |
| dispatch Â· limited | pair 380/489=0.78 Â· coverage 728/243=3.00 |
| dispatch Â· failed | pair 289/489=0.59 Â· coverage 749/243=3.08 |
| analysis Â· supported | pair 349/432=0.81 Â· coverage 394/287=1.37 |
| analysis Â· limited | pair 1675/432=3.88 Â· coverage 416/287=1.45 |
| evidence Â· stocked | conclude 564/387=1.46 Â· sources+next 1172/387=3.03 |
| evidence Â· no readings | 525/387=1.36 Â· 1299/387=3.36 |
| evidence-analysis Â· supported | records 1047/266=3.94 Â· limits 1595/148=10.78 |
| evidence-analysis Â· limited | 1047/266=3.94 Â· 1749/148=11.82 |
| evidence-analysis Â· no selection | 1047/266=3.94 Â· 630/148=4.26 |

## Compaction (phases A and B; coordinator 1.3x rule)
Every statement kept; honest-state lines visible; closed disclosures hold IDs, digests and explanatory detail; rows past 3 are `hidden`, not removed, behind a "Show all N" button with `aria-expanded`.
- **Phase A** (`016ed942`): evidence records/sources 3 rows + Show all; evidence-analysis limit detail and technical rows closed; dispatch coverage 3 inputs + Show all. Detail: `W1-F2-compaction-phase-A-handoff.md`.
- **mini panel 1:** day chooser (bounds on the same line) is the leading `.v69-chips` row before panel 1, as on Dispatch/Evidence; limitations on one note line (each in its words); assessment and freshness references use the small `tech` disclosure.
- **mini context:** count and gap-rule lines visible (`ChartNote`); per-input table and record links in one closed `window-coverage` disclosure (was the open table plus `window-readings`).
- **mini attention:** list state `ProductStatus inline`; shown count + full-list link on one line; parity "same" note-size; references `tech`. Preview limit stays 2 (already below 3).
- **mini money:** amount, inline state, source line (`SourceProvenanceNotice compact`), qualifier visible; bars, gate/upstream, links and references in closed `window-money-detail`; "Open fuel cost" in the panel header. **Next step:** button + Dispatch link on one line.
- **analysis:** constraint table 3 blocks + "Show all N blocks"; the three technical disclosures nest in closed `analysis-technical`.
- **dispatch coverage:** record count + Show all on one line; detail disclosure `tech`; comparison line note-size (`ComparisonLine note`).
- **evidence-analysis:** the two panel notes are one (words kept); claim-limit state line inline (`.claim-limit__when` kept); `claim-limit-detail` and all Evidence `Advanced` disclosures `tech`. **evidence:** the visible gateway-contact fact now states a switched-off gateway (fixes the phase A regression; tone unchanged).
- Shared, additive: `Disclosure variant="tech"`, `SourceProvenanceNotice compact` (other callers unchanged).
- **Changed assertions: none** (phases A and B). Existing queries still find content in closed/hidden nodes.
- **New tests, each failed under a mutation and was reverted with `git checkout --`:** `s5SiteWindowOverview` "W1-F2 compaction: amount, stateâ€¦" (money detail `defaultOpen`); `s502OverviewFindingList` "â€¦state line is inlineâ€¦" (non-inline status); `performanceDispatch` "Analysis shows three constraint blocksâ€¦" (preview 30); `v01bEvidenceVisual` "a switched-off gatewayâ€¦" (fact ignores DISABLED) plus a negative case; `evidenceClaimLimit` "(phase B) the state line is inlineâ€¦".

## Panel heights at 1440, after compaction (`8270c9a6`; dispatch `ff1bc248`)
| Screen Â· case | Panels (app h / mock h = ratio) |
| --- | --- |
| mini Â· p01 priced | happened 366/238=1.54 Â· context+attention 493/373=1.32 Â· money+next 272/193=1.41 |
| mini Â· p02 held | 366/238=1.54 Â· 493/373=1.32 Â· 271/193=1.40 |
| mini Â· unassessed | 286/238=1.20 Â· 447/373=1.20 Â· 178/193=0.92 |
| mini Â· failed | 286/238=1.20 Â· 497/373=1.33 Â· 178/193=0.92 |
| dispatch Â· supported | pair 605/489=1.24 Â· coverage 345/243=1.42 |
| dispatch Â· limited | pair 380/489=0.78 Â· coverage 318/243=1.31 |
| dispatch Â· failed | pair 289/489=0.59 Â· coverage 318/243=1.31 |
| analysis Â· supported | pair 349/432=0.81 Â· coverage 349/287=1.22 |
| analysis Â· limited | pair 498/432=1.15 Â· coverage 291/287=1.01 |
| evidence Â· stocked | conclude 564/387=1.46 Â· sources 497/387=1.28 |
| evidence Â· no readings | 525/387=1.36 Â· 480/387=1.24 |
| evidence-analysis Â· supported | records 483/266=1.82 Â· limits 475/148=3.21 |
| evidence-analysis Â· limited | 483/266=1.82 Â· 495/148=3.34 |
| evidence-analysis Â· no selection | 483/266=1.82 Â· 401/148=2.71 |

**Above ~1.3x (deviations, content shape differs):** mini happened 1.54 (the mock's hour story vs the app's whole-day gap line, causal strip, day reading, limitations, freshness line and two reference links, all honest-state); mini money pair 1.41 (inline state line plus the source-data line the mock lacks); dispatch supported coverage 1.42 (limitations recorded); evidence conclude 1.36-1.46 (phase A: no cheap safe cut); evidence-analysis records 1.82 (3 rows + Show all, plus the visible not-accepted lines) and limits 2.7-3.3 (mock panel is one static paragraph; the app panel holds the day/period chooser, headline, state line and the not-available rule line).

Finishing pass: heights re-measured from the committed evidence.json files and match the table above. Dispatch captures are at `ff1bc248`; no dispatch or analysis source changed after it (`git diff ff1bc248 HEAD -- frontend/src` touches only Evidence claim-limit, Evidence ledger, Overview and the Overview CSS), so they are valid for `8270c9a6`. Gateway wording confirmed visible in the contact line (LedgerSiteEvidence.tsx line 817; test v01bEvidenceVisual asserts it).


## Review fix round (`.agent/W1-F2-review.md`, RETURN at `f3a2f518`)
Code commits: `471df7bc` (H1, M6), `4faf2807` (H2), `43d9f53f` (M3, M4), `260c6c5e` (M5), `73cb5a54` (Lows 7a-7c). Final code revision `73cb5a54`.

| Finding | Fix | Where |
| --- | --- | --- |
| H1 Dispatch chooser | Period chips and the block row moved into panel 1 under `DayBlockStrip`. Tiles are the mock's size: grid `minmax(58px,1fr)`, outcome word over start time, outcome colour as a top bar. Panel 2 now leads with the selected block's `ClaimBadge` and one plain sentence (`BLOCK_SENTENCE`), then its facts. The period facts follow under "The period this block is in: hh:mm to hh:mm UTC", with the term "Period outcome". With no block selected, the period facts lead as before. The duplicate "Select a block..." note in the chooser was removed; panel 1 keeps one. | `PerformanceDispatch.tsx` panel slots, `PeriodsAndBlocks`, `SelectedPeriod`; `primitives.css` `.dispatch-blocks` |
| H2 Evidence Analysis limits | The day and period chooser renders through a portal into the page's `.v69-chips` row (`chooserTarget`; `v69-chip-control` date input, `.button`, 11 px period links). Removed: the `headline-card__question` label, the "What the readings can support" line and the "This page states what arrived..." note. Visible: the mock's two paragraphs (`.claim-limit__prose`), one result line (sentence plus inline state), the "Not available yet" rule line and the Dispatch link (note size). The physical-capacity caveat moved to the top of the closed `claim-limit-detail`. The technical disclosures stay closed, after the list of limits. | `EvidenceClaimLimit.tsx`, `LedgerSiteEvidence.tsx` (`WindowChooser extra`, `ClaimLimit technical`), CSS |
| M3 repeated state line | Overview panel 1 omits the freshness `ProductStatus` when its words equal the statusbar's (same `db_now`). It keeps the source sentence and marks `data-freshness-in-statusbar`; when the words differ it stays one note line. Panel 1's two "How this was worked out" disclosures are merged into one (`window-assessment`, which now holds the assessment and freshness references). The money state is a note-size line (it differs from the statusbar). The Needs attention list state strip is removed, and its "as of" is now the reference "List known as of". Evidence panel 1's receipt state is one note-size inline line, and its notes bullet is at note size. | `SiteWindowOverview.tsx`, `OverviewFindingList.tsx`, `LedgerSiteEvidence.tsx` |
| M4 Needs attention | The mock's numbered list (`v69-attention`): rank, h3 title, one-line reason, "Open the Finding →". Removed: the "Findings for {date}" h3 (the section is now `aria-label`), the state strip, the large count sentence (the count now shares the note line with the shown count and the full-list link) and the "same Finding" note. When parity is "same" and the chosen Finding is neither audit-only nor one of several, the separate chosen line is omitted. Item 1 then carries `data-known-finding`, the link and "· the Finding chosen for this day", and the choice references join the list's one disclosure. | `OverviewFindingList.tsx` (`chosen` prop), `SiteWindowOverview.tsx` `KnownFinding` |
| M5 vocabulary | (a) `gaps_reason` is never rendered verbatim. It reads "No rule yet says which gaps in the readings matter here; the reading counts are shown instead." (b) Each record row is named by its role in words (unknown roles and channel IDs are humanised by `idWords`) over its source in words; the exact `source · device / signal` is the row title. Coded values read as words ("STOPPED state" becomes "Stopped"). Quality is shown in words. Source names in the sources table, the silent-source list and the per-source strip are humanised, with the exact ID as `title`. (c) "A delivery that was rejected as a whole is kept for audit and not listed as a reading." | `SiteWindowOverview.tsx`, `LedgerSiteEvidence.tsx`, `dispatchWords.ts` `idWords` |
| M6 Other explanations | The not-available `alternatives` row is suppressed when the result records alternatives, so exactly one "Other explanations" line remains. Every unavailable key now gets a named term: known words, or the key in plain words. The "Another result" fallback is gone. | `PerformanceDispatch.tsx` `unavailableTerm`, `AnalysisView` |
| 7a records panel | The not-accepted facts are one note line ("Readings not accepted: ..."), followed by the one closed disclosure. "Show all" and "Next page" are at note size. The two "Advanced details" rows were not merged: each holds a different table set, and both stay closed. | `LedgerSiteEvidence.tsx` `Rejected` |
| 7b chooser position | The Overview day chooser is now above the statusbar, as on Dispatch and Evidence. | `SiteWindowOverview.tsx` |
| 7c Feeder demand x3 | A timeline row whose reading kind repeats is labelled "{kind} · {device in words}". | `SiteWindowOverview.tsx` `Timeline` |
| 7d, 7e, 7f | 7d not changed (Analysis panel 1 cards). 7e: see captures. 7f accepted by the reviewer. | - |

### Changed assertions (re-pointed, none weakened)
- `performanceDispatch` "Analysis shows ... types the rest unavailable":
  - Was: unavailable `[alternatives, fuel_and_money, finding]`. Now: `[fuel_and_money, finding]`.
  - Also asserts exactly one "Other explanations" term, stating "1 recorded". The fixture records one alternative, and M6 requires suppressing the contradicting row.
  - The kept-when-none case is a new test.
- `s5SiteWindowOverview`, freshness state line in 5 cases where the freshness and statusbar words are equal (current, stale, pending, failed x2):
  - Was: `expectStateLineVisible(freshnessCard())`. Now: `expectFreshnessInStatusbar()`, which checks that panel 1 has no `.product-status`, carries the marker, and keeps the source sentence. Each case also asserts the same words on the statusbar; that assertion was added for the current case.
  - The failed-day `[data-freshness-state=FAILED]` text check became an attribute check. The words are asserted on the statusbar in the next lines.
  - The differing (unassessed) case keeps its panel-1 assertion and adds the `no` marker.
- `s5SiteWindowOverview` W1-UX-02:
  - Was: the first child is the statusbar. Now: the first child is the `.window-day` chooser, and its next sibling is the statusbar (Low 7b).
- `s502OverviewFindingList`:
  - Compaction test: was the inline state line with as-of. Now: no `.product-status` in the list, and the "List known as of" reference equals `knowledge_at`. The count, shown count and full-list link share a line.
  - W1-UX-02 current rows: the state words are asserted on the statusbar, and the list as-of as a reference. The row `/version \d+$/` check now runs on the row's reason line. Added assertions: ranks 1-2, h3 titles, item 1 is the chosen Finding (exactly one `data-known-finding`), no "same Finding" note, no list h3, and the choice references are in the list disclosure.
  - Date change: `findByText(/Findings for 2026-10-16/)` now waits on `[data-overview-finding-list-for="2026-10-16"]`, because the h3 was removed.
- `s2LedgerEvidence` clocks:
  - Was: `/operational audit record/`. Now: the exact plain sentence, plus a negative check for "server refused" and "operational audit record".
  - Added: each record row header has no ` / `, ` · ` or `_`, and its title holds the exact IDs.
- `v01bEvidenceVisual` silent source:
  - Was: "fuel-level-sensor" in the text. Now: "Fuel level sensor" in the text, with `li[title='fuel-level-sensor']`.

### New assertions and mutation proofs (committed first; each mutation reverted with `git checkout -- frontend/src`)
- H1 (`performanceDispatch` W1-UX-03 test): tiles and chips are in panel 1; panel 2 has no chooser; its first badge is inside `[data-selected-block]` and reads "Possibly avoidable"; the lead sentence and period label are present. Mutation: block badge removed. Result: failed.
- H2 (`v01bEvidenceVisual` limits test): the mock paragraphs are present; there is no "This page states" text, no `.headline-card__question` and no visible h3; the day form is absent from the panel and present in `.v69-chips`. Mutation: `chooserTarget={undefined}` (inline). Result: failed.
- M4 (`s502` current rows). Mutation: `merged = false`. Result: failed.
- M6 (two `performanceDispatch` tests). Mutation: the filter always passes. Result: failed.
- M3: one "How this was worked out" in panel 1, plus the `expectFreshnessInStatusbar` checks.
- M5(a): a new `s5` test checks that the raw `gaps_reason` never appears and the plain sentence does.

### Checks (final code revision `73cb5a54`)
- `npx.cmd tsc --noEmit -p .`: clean.
- Full `npm.cmd test`: 76 files, **1986 passed, 0 failed**, wall 181 s. No flake reruns were needed.
- `tools/check-all.ps1`: all 10 guards passed.
- Captures with `tools/w1-fidelity-evidence.mjs` at 1440 and 390, commit `581a70bf`, all at `73cb5a54`:
  - Claims: mini 48/48, dispatch 60/60, evidence 60/60.
  - Ports (API/web/CDP): mini 9260/5680/9494, dispatch 9160/5690/9493, evidence 9360/5700/9495.
  - Evidence passed on its rerun. On the first attempt the Vite server on 5700 exited by itself mid-run; that log is kept as `evidence/run-attempt1-devserver-exited.log`.
  - Fixtures dropped afterwards (the same three as before) and all servers stopped.

### Panel heights at 1440 after the fix round (app h / mock h)
| Screen · case | Panels |
| --- | --- |
| mini · p01 priced | happened 333/238=1.40 · context+attention 518/373=1.39 · money+next 272/193=1.41 |
| mini · p02 held | 333/238=1.40 · 518/373=1.39 · 271/193=1.40 |
| mini · unassessed | 260/238=1.09 · 404/373=1.08 · 178/193=0.92 |
| mini · failed | 236/238=0.99 · 454/373=1.22 · 178/193=0.92 |
| dispatch · supported | pair 507/489=1.04 · coverage 345/243=1.42 |
| dispatch · limited | 443/489=0.91 · 318/243=1.31 |
| dispatch · failed | 289/489=0.59 · 318/243=1.31 |
| analysis · supported | pair 349/432=0.81 · coverage 291/287=1.01 |
| analysis · limited | 498/432=1.15 · 262/287=0.91 |
| evidence · stocked | conclude 483/387=1.25 · sources 497/387=1.28 |
| evidence · no readings | 457/387=1.18 · 480/387=1.24 |
| evidence-analysis · supported | records 452/266=1.70 · limits 320/148=2.16 |
| evidence-analysis · limited | 452/266=1.70 · 320/148=2.16 |
| evidence-analysis · no selection | 452/266=1.70 · 363/148=2.45 |

Low 7e: the 390 dispatch coverage table scrolls inside `DataTable`'s `.data-table__scroll` (`overflow-x: auto`, focusable). Page overflow is 0.

### Known deviations (fix round)
1. **The Evidence Analysis limits panel is 2.16-2.45x, not the targeted ~1.3x** (was 2.7-3.3x).
   - Everything the review listed as removable is gone.
   - What remains visible is the content the review said to keep: the mock's two paragraphs, the result line with its state, the "Not available yet" line and the Dispatch link.
   - Three closed disclosure rows remain: limit detail, list of limits, technical. Each is about one line high.
   - Merging those three rows into one would cut about one more line height, but it would move content between the assertions that pin each disclosure. I left that to the reviewer's call rather than doing it inside this round.
   - The mock's paragraph height is the floor. The mock has no result or state line at all.
2. **The mini "happened" (1.40) and money (1.41) panels are just above 1.3x.**
   - happened: the duplicate state line and the second disclosure are gone. The rest is the honest whole-day gap line, the causal strip, the day reading and the limitations.
   - money: the note-size state line and the source line remain.
3. **Evidence Analysis records is 1.70x** (Low 7a: the not-accepted facts are now one note line). The two closed "Advanced details" rows were not merged.
4. **The list as-of moved into a reference (M3).** The Needs attention list's own "as of" (`knowledge_at`) is now the exact reference "List known as of" inside the list's closed disclosure. The visible state is the statusbar's.

## Fix round 2 (`.agent/W1-F2-rereview.md`, RETURN at `f2163bef`)
Code commits: `d30c585a` (findings 1, 2 and Low 3), then one follow-up for the no-day state. The follow-up was found by the full run: the no-day line still said "No assessment exists" through the inline `ProductStatus` sentence.

| Finding | Fix | Where |
| --- | --- | --- |
| M1 limits panel | One closed top-level `evidence-limit-details` row is the panel's last child. It holds a slot that receives the loaded assessment's detail (portalled through `detailTarget`), the list of limits and the technical rows. Standalone use (`detailTarget` undefined) keeps the `claim-limit-detail` disclosure. The physical-capacity sentence is appended to `[data-evidence-limit-note]` and is visible. The Dispatch link ends the result line. No-day, unavailable and refused states are one inline line. No-day now reads "No assessment selected: nothing is concluded. Choose a day, then one of its assessed periods." and has no block card, no "As of" line and no "No assessment exists". | `EvidenceClaimLimit.tsx`, `LedgerSiteEvidence.tsx` `ClaimLimit` |
| M2 inline status | `.product-status--inline` resets padding, border, radius and background and inherits font size, children included. | `primitives.css` |
| Low 3 records | `evidence-not-accepted` nests inside `evidence-records-technical`. | `LedgerSiteEvidence.tsx` |

### Moved assertions (none weakened)
- `v01bEvidenceVisual` nested-disclosure pairs: `evidence-records-technical` now also holds `evidence-not-accepted`. The analysis pair's outer is now `evidence-limit-details`, with inner `evidence-limit-list`, `evidence-analysis-technical`, `evidence-analysis-status`, `evidence-comparison` and `evidence-gateway`. The named-disclosure loop is unchanged.
- `evidenceClaimLimit` standalone tests are unchanged.

### New assertions
- `v01bEvidenceVisual` limits: exactly one top-level `details` in the panel, closed, named `evidence-limit-details`, containing the list of limits. The not-available line and the capacity note are outside any `details`; the note contains "not the equipment's physical capacity".
- No-day state: "nothing is concluded" occurs once, "No assessment selected" and "Choose a day, then one of its assessed periods." are present, "No assessment exists" is absent, and there is no `.product-status:not(.product-status--inline)`. This assertion failed on the first full run and drove the follow-up commit.
- `evidenceClaimLimit` (loaded, with the slot): one closed top-level row holding the RoleStrip and the limit list; no `claim-limit-detail`; headline, not-available line and note are outside any `details`; the Dispatch link is inside `.claim-limit__result`.

### Checks (final code revision: see git log; captures at that revision)
- `npx.cmd tsc --noEmit`: clean.
- Full `npm.cmd test` before the follow-up: 76 files, 1986 passed, 1 failed (the no-day assertion above). After the fix, `v01bEvidenceVisual` and `evidenceClaimLimit`: 69 passed. No other file changed after the full run.
- `tools/check-all.ps1`: all 10 guards passed.
- Captures with `tools/w1-fidelity-evidence.mjs` at 1440 and 390: mini 48/48 (API 9400, web 5800, CDP 9410), evidence 60/60 (API 9420, web 5820, CDP 9411). Fixtures dropped (`assetops_s501_owner_w1f2b`, `assetops_s302_w1f2b` and their `var` folders) and servers stopped. The s501 and s302 tools were run with the venv interpreter and `PYTHONPATH`; the s501 `prepare` used a scratchpad wrapper that renames the F01-gateway pipe to `assetops-s4-cases-gateway-w1f2b`, because another session's gateway holds the default pipe name (the repo is unchanged).

### Panel heights at 1440 (app h / mock h)
| Screen / case | Panels |
| --- | --- |
| mini p01 priced | happened 333/238=1.40, context+attention 518/373=1.39, money+next 270/193=1.40 |
| mini p02 held | 333/238=1.40, 518/373=1.39, 252/193=1.31 |
| mini unassessed | 244/238=1.03, 404/373=1.08, 176/193=0.91 |
| mini failed | 236/238=0.99, 454/373=1.22, 176/193=0.91 |
| evidence stocked | conclude 483/387=1.25, sources 497/387=1.28 |
| evidence no readings | 457/387=1.18, 480/387=1.24 |
| evidence-analysis supported | records 436/266=1.64, limits 266/148=1.80 |
| evidence-analysis limited | 436/266=1.64, 266/148=1.80 |
| evidence-analysis no selection | 436/266=1.64, 241/148=1.63 |

The limits panel went from 2.16-2.45x to 1.63-1.80x (the re-review expected 1.5-1.7x); what remains is the honest result line, the not-available line and the one closed row, none of which the mock has. Dispatch and analysis captures are unchanged (no source change since their last capture).
