> Moved verbatim from the former `.ai/CODE_STATE.md` on 2026-11-18 (declutter step 2), part 3 of 11; sections keep their original relative order; the original order of all sections is the numbering in `index-*.md`. Index: `INDEX.md` in this folder.

## T009 - Shared visual vocabulary

What this slice settled in code.

`frontend/src/ui/` is the one visual vocabulary and a leaf. It holds
`tokens.css` (type scale, neutrals, rail, accent, four badge tones, spacing,
radius), `primitives.css` (the classes), and seven components: `AppHeader`,
`NavRail`, `Breadcrumbs`, `PageHeader`, `Badge`, `Panel`, and `DataTable` with
`FactList`/`Fact`. Before this slice the app had no stylesheet at all.

The values were read from `Docs/UI Design/Motivation/ScreenMockups.png`, not
invented: dark navy rail with a bright blue active item, white cards on a pale
blue-grey page, pill badges, one blue accent. Visual vocabulary only; no mockup
literal, control, column or rail item came with it.

Names in the primitives are deliberately generic - `DataTable`, `Panel`,
`Badge`, never `SiteTable`, `SitePanel`, `SiteBadge`. The T006 single-definition
guard flags a Site presentation component anywhere outside
`frontend/src/sites/`, so a Site-named primitive would fail it, correctly.

`tools/checks/ui-primitives.ps1` is a new seam with two clauses. Leaf
direction: the primitives import no shell code, no simulator code, no feature
flag and no Site substrate. Shared vocabulary: both the shell root and the
substrate must import the module, because a vocabulary nobody imports has been
forked. Five violations were proven to fail it.

`NavRail` owns no items. Both rails pass their own, so the operator rail and
the Lab rail cannot converge through the component they share. The Lab's items
are declared in `simulatorLabRoutes.tsx`, which is already the only module
allowed to spell a simulator path; `SimulatorLabShell` takes them as props and
names no path, so the gate chokepoint is unchanged.

The Simulator Lab has a rail for the first time, listing `Simulator Lab` and
`Site Templates` - the two destinations that already rendered truthful content.
The mockup's other eight rail items have no route behind them and are absent.

Badge tones are one per vocabulary and never shared: provenance, lifecycle,
origin, neutral. They differ in fill, border weight and corner radius as well
as hue, so the distinction survives greyscale, and every badge renders the word
it means so colour never carries meaning alone. A badge renders only where a
record supplies its value: template provenance stays plain text because a site
created from no template renders an absence there, and every stated absence on
Site Configuration stays plain text for the same reason.

`PageHeader` has no action or badge slot. `+ New Site` restyling is T011's, the
Site identity badge is T012's, and `Edit`/`Version History` are never rendered
at all, so the slots would have been machinery nothing fills.

The brand mark is drawn in CSS rather than as an inline `<svg>`, because
several screens assert no `svg`, `canvas`, `img` or `figure` exists in their
container and that guard is worth more than the glyph. Keep it that way.

What this slice leaves open.

1. Breadcrumbs are provided but adopted by no screen. Adopting them means
   changing settled back-link copy or adding a destination, both of which stage
   1 forbids. They belong to T011-T013 with the screens they describe.
2. Not rendered in a browser. Verified by the suites, the typecheck, the build,
   and by confirming the built stylesheet ships with the expected classes.
   Browser tooling was unavailable in the session.
3. Contrast is reasoned against WCAG AA and documented in `tokens.css`, but no
   contrast checker was run and no automated accessibility assertion exists.
4. Nothing proves a surface renders *with* the vocabulary rather than merely
   importing it. The guard proves the import; the rest is review-time.
5. `SiteConfiguration.tsx` carries a UTF-8 BOM, pre-existing from T008. It is
   invisible to the compiler and the tests and silently defeats line-anchored
   shell commands.

## T011B - Shell and dense content overflow containment

What this slice settled in code.

Every table renders through `DataTable`, which wraps it in
`.data-table__scroll`, a region that owns the table's horizontal overflow. The
wrapping happens in the primitive rather than at each call site so a screen
cannot render a bare table by forgetting to, and a guard clause holds the other
half: a `<table>` element anywhere outside `frontend/src/ui/DataTable.tsx`
fails the architecture check.

The region is a named focus stop - `tabIndex={0}` plus `role="region"` labelled
by the heading the table already answers to - because a region only a mouse can
scroll hides its far side from a keyboard. Both are conditional on the caller
supplying `labelledBy`: an unnamed `role="region"` is not exposed as a landmark
and an unnamed focus stop announces nothing.

Only `overflow-x` is declared. CSS resolves the other axis to `auto` once one
axis scrolls, but the box has no height constraint, so it grows to its rows and
never produces a vertical scrollbar. Giving that region a height is what would
put rows behind an inner scrollbar.

`.app-shell > .app-frame` sets `min-height: 0`. `.app-frame` keeps its own
`min-height: 100vh` because `SimulatorLabShell` renders that frame standalone,
outside the shell. Two uses of one frame, and the nested one is the exception:
deleting the base rule would take the Lab's full height with it, which is why
the guard asserts both halves separately.

New seam, `tools/checks/shell-overflow.ps1`, registered as the eighth. Five
clauses: the region contains the inline axis; the standalone frame is full
height; the nested frame is not; no shell selector hides page overflow; every
table goes through the primitive. The fourth is the one that matters most -
`overflow-x: hidden` on the document is the tempting wrong fix, because the
scrollbar disappears and the content beyond it becomes unreachable rather than
contained. Hiding is not containing.

Each clause was proved to fail on its own, worded so no sibling clause could
fire instead. That is the T011A lesson applied.

Nothing was dropped to make anything fit, and that is now asserted here rather
than only in the slices that introduced each inventory: nine Sites index
columns, eight Site tabs with no menu, toggle or hidden element, both rail
labels.

What this slice leaves open.

1. Nobody has seen the fix work. jsdom has no layout, so no test here can
   observe a scrollbar; everything asserted is structure and CSS text. This
   needs a browser before it is believed.
2. At exactly 1280px the Sites index table will probably still scroll inside
   its region. The table's floor is roughly 950-1100px and the rail and padding
   take about 250px more. That is the intended behaviour; closing it would mean
   changing density or dropping a column, which the policy forbids.
3. No affordance says more columns exist to the right of the region. That is a
   design addition, not a correction.
4. The tab row wraps rather than scrolling, so it has no overflow owner. A
   wrapping row cannot overflow, and a wrapped tab is visible where a scrolled
   one is not.
5. The unsupported-viewport state the policy permits is not built. It is new
   chrome that makes a claim and should have its own slice.
6. No breakpoint tokens were introduced, so the conditional breakpoint-token
   seam in the guard table remains unshipped.

## T011C - Site tab row treatment

What this slice settled in code.

A destination looks like a link because it is one. `.site-tabs__link` no longer
overrides the colour, so it inherits the accent every other link in the product
uses, and the current tab is told apart by weight and underline rather than by
being the only thing that is not grey.

That override was the defect. T011A styled a destination `--text-secondary` and
a label `--text-muted`, five percent apart, and the user read the whole row as
disabled. Nothing was disabled; the treatment said otherwise, which is a
reminder that the three-state rule is only as true as its rendering.

Two signals now, not one. A divider marks where the destinations end, and a
sentence under the row says how many aspects have no content in this build yet,
so the distinction holds in greyscale and for a reader who does not know that
grey means unbuilt here.

The sentence counts rather than names. The first version listed all six under a
row that had just shown all six, and the user's browser pass called it heavier
than the row it was explaining. It reads "Six aspects of a Site have no content
in this build yet." - `of a Site`, not `of this Site`, because no aspect is
missing content because of anything about the site on screen, and the shorter
phrasing must not become a claim about that particular site.

`labelledAspectsSentence` derives that sentence from the tab inventory and is
exported with the inventory as a parameter, so tests can hand it arrangements
this product does not have yet. An aspect promoted to a destination leaves the
sentence in the same change that moves it. A written-out list would have gone
stale the first time an aspect got content, and the screen would then have said
something has no content while the tab beside it opened that content. It
returns null when nothing is labelled, so the day every aspect has content the
sentence disappears rather than becoming an empty claim.

The sentence states what this build contains and never what a later one will.
`coming soon` and its family stay banned, and the guard enforces it inside this
module - it caught a code comment that explained the ban by quoting the banned
phrase, which is incidental evidence that the `ada4149` repair holds.

The baseline rule moved from `.site-tabs` to `.site-tabs__list`. The sentence
lives inside the same landmark, and a border on the nav would have drawn itself
under the sentence, leaving the active tab's negative-margin underline against
nothing.

What the user confirmed, and what is still unseen.

This row was seen. The user rendered it, reported the six read as disabled,
chose the treatment, rendered the result, and confirmed the row reads correctly
with only the sentence to shorten. That is the whole reason this slice exists,
and it is settled. What remains unseen belongs to T011B, not here: whether
chrome stays anchored while a table scrolls, and whether an empty operator page
with the gate open still runs past the viewport.

What this slice leaves open.

1. The correction may overshoot: two accent destinations could make the row
   read as all links. Not raised by the user, and not something a test sees.
2. The divider is a border rather than an element, so the grouping is visual
   only and the sentence is the whole non-visual channel.
3. The sentence sits inside the nav, so a reader skipping navigation skips the
   explanation with it.
4. Colour and divider have no guard clause. Consistent with the viewport
   policy, which leaves exact visual fit to review, but it means a future slice
   could regrey the row without anything failing except a human looking.

## V-01a - Site and Foundation visual fidelity (in_review)

Branch `task/V-01a-foundation-visual`; packet `archive/agent-history/V-01a-review-packet.md`. Visual gate only; no new data claim.

- `FoundationPeriodStrip` (`FoundationRevisionPanel.tsx`): an `?at=` instant that is not a period start now
  gets its own selected option ("At ... (from the address)"). Before this, the controlled select fell back to
  "In effect now" on reload or shared links while showing another period.
- `Panel` takes an optional `description` (the v6.9 `.panel-head p` sub-line, CSS `.panel__description`).
  It is used on Site inventory, Configured topology, the SLD panel and Configuration readiness. The Readiness
  sub-line carries the PRE-S3-04 separation at the top of the view.
- Sites list panel retitled "Site inventory" (v6.9 label). The topology bus label carries the bus's declared
  rating (`data-topology-bus`, e.g. "AC bus · 400 V").
- Devices caption (`SiteConfiguration.tsx` `SiteFoundationDevices`) no longer says "none has reported". It
  states only that reporting is not assessed here (backlog carry).
- Tools: `tools/v01a_foundation_walkthrough.py` (copy of `assetops_s4cases`, plus an empty migrated DB;
  API 8860/8861, web 5360/5361) and `tools/v01a-foundation-evidence.mjs` (25 claims at each of 1440 and
  390 = 50; CDP port 9361).
- Q1-Q5 were answered by the owner and ruled in `D-2026-10-12-v01a-owner-visual-rulings` (round 2 below).
- Open: `SiteOverview.tsx:241` stale "No window" text stays with S5-01 (backlog C2).
- Open: the shell-wide `layout-evidence.mjs` stops at the Lab run-setup precondition in the walkthrough tree.

### V-01a round 2 (owner rulings; packet section "Round 2")

- `SitesIndex.tsx`: columns Site / Type / Mode / Setup details / Actions; `Last analysed` and
  `NO_ANALYSIS_IN_WINDOW` removed; `DIRECTORY_ANALYSIS_ABSENT` note under the table.
- Readiness: Badge tones `configured` (green, tick) and `config-gap` (amber, "!"), configuration-only;
  `ReadinessLegend` in `FoundationBindingsPanel.tsx`.
- Part selection: `component=` beside `at` (`FOUNDATION_COMPONENT_PARAM`, `siteFoundationViewHref`);
  `SiteFoundationFrame` clears an undeclared part and shows `[data-selected-part-missing]`;
  `SelectedPartPanel` on all three views.
- SLD (`SiteSingleLineDiagram.tsx`): bus-bar layout (`latticeFor`, `runPoints`, `SldBus`, `SldNode`),
  `data-sld-layout="bus-bar"`, `SLD_CONFIGURED_NOT_LIVE`, optional `SldSelection` (svg becomes a named
  `group`, parts are `role="button"` toggles). The slot text is now "Readings not assessed here"; the constant
  name `AWAITING_RUNTIME_OR_EVIDENCE` is unchanged. The view model is unchanged except `sldSymbolFor`.
- Icons: `sites/componentIcons.tsx` (one icon family per type, used by the SLD and `ComponentTypeIcon` on the
  topology cards); `ui/RailIcon.tsx` (mock line icons; `NavRailItem.icon`).
- Shared type, colour, tab and rail tokens follow the mock (`ui/tokens.css`). This affects every screen.
- Guard: `shell-overflow.ps1` allows fixed-size icon svgs in exactly those two modules.
- Open: bus-bar routing has no detour for a supply that bypasses an occupied conversion row. No stored topology
  has one.
- Open: the V-01a evidence tool does not exercise Finding detail. The store holds 11 Findings, but its prepare skips the comparison step, so the index is empty and detail answers PERFORMANCE_CUTOVER_CLOSED. The reviewer verified detail at 1440/390 by hand on a private copy.
- Open: the Lab run interval drawing now uses the bus-bar geometry; its browser label-collision check (layout-evidence T025d) is unverified behind the Lab precondition.
- Open: `layout-evidence.mjs` still stops at the Lab run-setup precondition.


### V-01a round 3 (readiness and organization; packet section "Round 3")

- `sites/ReadinessOverview.tsx` (new): `readinessCards()`/`ReadinessCards` (four cards from typed `configuration_gaps`;
  Unknown only on `NO_EFFECTIVE_REVISION`), `ReadinessEvidenceTable` (six rows; Confirmed always "Not recorded"),
  `GatewayStatusPanel` over the S2 `/gateway-health` read (`App.tsx` → `SiteFoundationFrame` `gatewayHealth`).
  Gateway badges are neutral; contact is labelled as server-time, apart from the selected `at`.
- Plain-first layers: `Disclosure` "Advanced details — Foundation records | diagram records | roles, channels and
  records | selected part channels" (`foundation-advanced`, `sld-advanced`, `readiness-advanced`,
  `selected-part-channels-{model,sld}`). "Review or change bindings" (`[data-review-bindings]`) opens the Readiness one.
- Site model: `IdentityPanel` critical-load/loads/productive-use/financial facts; `FoundationControlsPanel`
  "Evidence / change" column (`[data-control-link]`). SLD: `[data-sld-missing]` note; parts table shows counts only.
- `SelectedPartStrip` replaces the global Selected part panel (topology panel and `SiteSldPrimary` `strip`);
  Readiness shows `[data-selected-part-chip]`. Sites: "Operating view" column and `sites-aggregate-absent` note.
- Tools: `v01a_foundation_walkthrough.py` gains `--db/--empty-db/--work-name` and `drop` (refuses owner defaults);
  `v01a-foundation-evidence.mjs` 185 claims, gateway variants via DevTools `Fetch` interception (documented in its
  header); `layout-evidence.mjs` expects six Sites columns and excludes `[data-review-bindings]` from actions.
- Open: only STALE gateway contact is reachable on the stored copy; other states are intercepted-response evidence.
- Open: registry `readiness:2#a/2#b/3#a` and the ledger/registry conditional caveats wait for independent review
  and the owner's decision; nothing was edited.
- Open: `.readiness-cards` 2-column band (480-900 px) unmeasured; `layout-evidence.mjs` still stops at the Lab precondition.

## V-01b - Lab and Evidence visual fidelity (in_review)

Task `tasks/V-01b-evidence-lab-visual-fidelity.md`, branch `task/V-01b-evidence-lab-visual`, diff base `b1ac0a8`.
Packet `archive/agent-history/V-01b-review-packet.md`, handoff `archive/agent-history/V-01b-handoff.md`, questions `archive/agent-history/V-01b-questions-1.md`
(Q1-Q8, fail-closed defaults shipped), owner guide `archive/agent-history/V-01b-owner-walkthrough.md`. No backend change.

- Site Evidence (`frontend/src/sites/LedgerSiteEvidence.tsx`, `ui/primitives.css` "V-01b Evidence" block): status bar
  of window facts with neutral "No capability conclusion yet" badge and "Analysis →"; `evidence:1` "What we can
  conclude now"; `evidence:2` "Data sources" table beside `evidence:3` "Most useful next evidence" (two-column
  ≥1100px); each unsupported portion is a "Not available yet: ..." statement. Analysis: `evidence-analysis:1`
  accepted records table (`listRecords`, "Open record" → "Exact message as received"), `evidence-analysis:2`
  "How each limit is set" (Q4). Technical panels under closed "Advanced details — ..." disclosures.
- Conflict original time: refused-readings table "Original reading" column renders `conflicts_with_source_time`
  with a link to `conflicts_with_evidence_id` (S2-02 batch-4 carry closed).
- Lab run (`shell/RunIngestionOverview.tsx`, `shell/runIngestion.css`, `RunFrame.tsx`, `RunCommitPanel.tsx` `onRead`):
  h1 "Draft run" (Q2) then h2 "Gateway & Ingestion": status strip, four `[data-flow-box]`es, `lab:1` envelope `<pre>`,
  `lab:2` truth vs observed, `lab:3` release and ingestion with the Commit panel, `lab:4` boundary; "Execution and
  recorded history" below; seven "Advanced details — ..." disclosures. `GatewayLedgerView.tsx` Q1 Stage label.
- Lab phone shell: `SimulatorLabShell.tsx` uses `app-frame app-frame--lab`; every <640px shell rule lists both
  `.app-frame--operator` and `.app-frame--lab` (S1-03 Q1 carry closed). Guard `tools/checks/shell-overflow.ps1` 2b
  requires each narrow selector part to start with one of the two and fails when either has no narrow rule
  (non-vacuity proven in the packet). `overflowContainment.test.tsx` asserts the class.
- Tests: `shell/__tests__/v01bEvidenceVisual.test.tsx` (10), `v01bLabIngestion.test.tsx` (9); order/name updates in
  `cockpitLayout`, `runExecution`, `simulatorLabGate`, `s2LedgerEvidence`, `runsInventory` (Commit first).
- Tools: `archive/tools/v01b_lab_evidence_walkthrough.py` (prepare/links/serve/drop, `--db/--empty-db/--work-name`, owner
  ports 8862/8863/5362/5363); `archive/tools/v01b-lab-evidence-evidence.mjs` (101 claims at 1440/390, SourceEnvelope trace,
  intercepted 503 gateway variant); `tools/layout-evidence.mjs` registered Lab Site/dates/profiles, Kobo registered run
  section (`ASSETOPS_LAYOUT_V01B_ONLY`, `ASSETOPS_LAYOUT_V01B_RELEASED_RUN`), `ASSETOPS_CDP_PORT`, run-setup overflow
  proof at 390px. Full run with KOBO-001: 398 PASS / 5 FAIL, all named preconditions.
- Open: Q8 drawing precondition (T025d label claims unmeasured); Q1 stale Stage upload constant; `.action` cascade
  over `.action--primary` elsewhere; layout tool creates a draft per run; ledger/registry caveats wait for owner
  acceptance (nothing edited).

## G-01 - Mock-gap catalogue and orphan guard (in_review)

Task `tasks/G-01-mock-gap-catalogue-and-guard.md`, branch `task/G-01-mock-gap-catalogue-and-guard`, diff base `db98e54`.
Packet `archive/agent-history/G-01-review-packet.md`, handoff `archive/agent-history/G-01-handoff.md` (design + phase log), questions
`archive/agent-history/G-01-questions-1.md` (Q1-Q4, fail-closed defaults shipped), owner guide `archive/agent-history/G-01-owner-walkthrough.md`.
No backend change.

- Registry schema `assetops.v69.dependency-registry.pilot.v3` with top-level `mock_gaps` (version 1,
  `gap_enrolled_screens: []`); one gap `G-readiness-gateway-firmware` (data_source/absent/open/unplanned, element
  `readiness:2.firmware`, placement `readiness.gateway.firmware`). Ledger row `readiness.gap_ids`. Portions may carry
  `gap_ids` (none yet). Readiness is not enrolled; G-02 enrolls `sites`, `foundation`, `readiness`, `sld`.
- `frontend/docs/architecture/mock_gaps.cjs` `validateMockGaps(registry, {contracts, screenIds, screenLedger,
  requirePresent})` returns typed errors (gap_shape/id/duplicate/reference/enum/combination/requires/cycle/placement/
  join/ledger/enrollment). Registry checker runs it with `requirePresent: true`; `nextWork` with `false`, refusing on
  errors (type `mock_gaps`) and adding an informational `gap_catalogue` summary; gaps never touch candidates/scores.
- UI: `frontend/src/ui/gapCatalogue.ts` (`UI_GAP_CATALOGUE` typed mirror) and `frontend/src/ui/MissingClaim.tsx`
  (`data-gap-id`/`data-gap-placement`/`data-gap-status`; unknown pair is a TS error and a runtime throw).
  `ReadinessOverview.tsx` splits `GATEWAY_FIRMWARE_NOT_AVAILABLE_YET` out of `GATEWAY_NOT_AVAILABLE_YET` and renders it
  through `MissingClaim` unconditionally in `GatewayStatusPanel`.
- Guard: `tools/checks/missing-claim-scan.mjs` (TS AST) checks mirror == registry, literal catalogued MissingClaim
  pairs, every placement used, and untagged copy (`not available yet`/`not yet available`/`no reviewed source`) equals
  `tools/checks/missing-claim-baseline.json` exactly (dated 2026-10-13, 16 entries, shrink-only vs merge-base main
  baseline, `SEED_CEILING = 16`). check-all guards: "Mock-gap catalogue fixtures", "Missing-claim orphan scan",
  "Missing-claim scan fixtures".
- Open: baseline holds 16 legacy untagged strings for G-02..G-05; non-core ranking and per-screen completion remain
  W1-exit owner decisions; Q1 phrase set excludes `not recorded` (commissioning copy is for G-02).

## G-02 - V-01a mock-gap pilot (in_review)

Task `tasks/G-02-v01a-gap-pilot.md`, branch `task/G-02-v01a-gap-pilot`, diff base `42bd74d` (main `5625447`).
Packet `archive/agent-history/G-02-review-packet.md`, handoff `archive/agent-history/G-02-handoff.md`, questions `archive/agent-history/G-02-questions-1.md`
(Q1-Q6, fail-closed defaults shipped), owner guide `archive/agent-history/G-02-owner-walkthrough.md`. No backend change.

- Registry `mock_gaps.gap_enrolled_screens = [sites, foundation, readiness, sld]`; 20 new gaps (23 total). Every
  non-core open portion of the four carries `gap_ids` (`sites:2#a`, `foundation:2#b`, `readiness:2#a/#b`, `3#a/#b`,
  `4#a/#b`); ledger rows list their gaps. Core paths, `core`, `state`, `technical_requires`, `panel_status` unchanged.
- Placed (17 gaps, 25 MissingClaim uses incl. firmware and S4-03's two): Sites operating view (cell + note), attention
  counts, setup progress; Foundation productive use, financial assumptions, control change record, constraint evidence;
  Readiness commissioning (5 placements), gateway uptime / completeness / signal strength (Architect C5 split, one
  element each) + firmware, per-source contact (3 placements); SLD protection/metering and reporting status (2).
  Unplaced with reasons: obligation policy, confidence effect, evidence capability, and three portion-review gaps.
- Visible copy unchanged except the gateway split; bundled Sites/SLD notes are now one element per claim.
- Scan: phrase set + `not tracked yet`, `commissioning confirmation not recorded` (C7); the result line names the
  merge-base comparison or `SKIPPED (<reason>)` (C1). Baseline 15 -> 12 entries (G-03/G-04 remain).
- Tests: `siteFoundationRevision.test.tsx` "G-02: V-01a pilot missing-state placements" (branch/date/selection/reload,
  exact per-element text) and the G-01 block (C6 loading); `sitesIndex.test.tsx`; `test_mock_gaps.cjs`;
  `test_missing_claim_scan.mjs` (17). Evidence tool `tools/g02-gap-evidence.mjs`.
- Open: SLD per-node SVG slots/captions restate the reporting-status fact untagged (Q1); other euphemisms are tagged
  but not scan cues (Q2); `tools/v01a-foundation-evidence.mjs` and `tools/g01-firmware-evidence.mjs` assert the
  pre-split gateway copy (historical).

## W1-UX-01 - shared product presentation (built, in_review)

Branch `task/W1-UX-01` (base main `3e6dbc88`, unmerged); packet `archive/agent-history/W1-UX-01-review-packet.md`; shared API `archive/agent-history/W1-UX-01-handoff.md`. Frontend only.

- Words: `frontend/src/ui/productWords.ts` - `currentnessWords`, `readResultWords`, `moneyWords`, `outcomeWords(outcome, reasons, sourceClass)`, `limitationWords`, `sourceQualification`, `asOfText`/`plainTime`; unknown codes -> `UNRECOGNISED_SENTENCE`, never positive.
- Components: `frontend/src/ui/ProductStatus.tsx` - `ProductStatus`, `ProductOutcome`, `ProductLimitation`, `HeadlineVisualCard`, `ExactReferences` (closed "How this was worked out"), `ValueBars` (null = hatched "not known"), `StepStrip`; CSS at the end of `primitives.css`.
- Scan: `productVocabulary.json` v3 with `w1` set v1; `scanProductVocabulary(root, page, { set: "w1" })`, `scanDisclosureVocabulary`, `rawCodes` (case-sensitive; SOC/UTC/kW/kWh/PV allow-listed); a scan root cannot exempt itself. Shared check `frontend/src/test/productPresentation.ts` `expectStateLineVisible`.
- Migrated and opted into W1: Overview objective (`SiteWindowOverview.tsx` `Objective`), Evidence conclusion (`LedgerSiteEvidence.tsx` `OverviewBody`), Action state (`SiteAction.tsx` `ActionStateCard`).
- Capture: `tools/w1-ux-01-evidence.mjs <out> <mock-id>[:<case>]=<url>`.
- Open: the other 23 W1 routes remain on the T028 scan until UX-02..05; domain word maps still duplicate cross-screen states; the Evidence read has no read instant (as of = latest delivery received); the Action summary has no source class; registry Low D (`I-W1-UX-01` requires) untouched.

## W1-UX-02 - Site, Finding and money presentation (built, in_review)

Branch `task/W1-UX-02` (base main `a8cbb3d1`, code `bc1cea1b`, unmerged); packet `archive/agent-history/W1-UX-02-review-packet.md`; handoff `archive/agent-history/W1-UX-02-handoff.md`. Frontend only.

- Migrated to the W1-UX-01 layer and opted into the W1 set: `sites` (`SitesIndex.tsx` `SitesAnswer`), `mini` freshness/money/timeline/Finding list (`SiteWindowOverview.tsx`, `OverviewFindingList.tsx`), `sitefindings` (`SiteFindingIndex.tsx`), `finding`/`finding-evidence`/`finding-history` (`SiteFinding.tsx`, `SiteFindingEvidence.tsx`, `SiteFindingHistory.tsx`), `financials` (`FindingConsequence.tsx`), `assumptions` (`SiteFinancials.tsx`, `ConsequenceHistory.tsx`).
- Word maps: `findingCurrentnessWords` (`findingWords.ts`), `consequenceWords` (`FindingConsequence.tsx`), `MONEY_STATE_WORDS` on `moneyWords`; `FRESHNESS_WORDS`, `CURRENTNESS_WORDS`, `STATE_HEADLINE` removed. `FindingRefusalCard` (`findingPresentation.tsx`).
- `LINK_WORDS` stays equal to backend `BROKEN_WORDS`; `LINK_DISPLAY_OVERRIDES` rewords two "fingerprint" codes on screen.
- Money: a `ValueBars` amount only for a PRICED+CURRENT bridge with both bounds; every other state draws a not-known mark and gives a "why no current amount" line. The S4-08 history is recorded-only.
- Evidence: `tools/w1-ux-02-evidence.mjs`; all eight screens captured at 1440/390 (packet).
- Open: untimed reads say "As of: time not recorded"; `LINK_DISPLAY_OVERRIDES` awaits a backend rewording; there is no Financials Analysis tab; `FindingDetail.tsx` (legacy route) is not migrated; `s502-overview-finding-list-evidence.mjs:148` is stale.
## W1-UX-03 - Evidence, Dispatch and Analysis presentation (built, in_review)

Branch `task/W1-UX-03` (base main `b4a89314`, unmerged); packet `archive/agent-history/W1-UX-03-review-packet.md`; handoff `archive/agent-history/W1-UX-03-handoff.md`. Frontend only.

- `frontend/src/sites/periodStrip.tsx` (+ `.css`): local `PeriodStrip` - rows of read-returned time segments on the period's own bounds, optional exact links per segment, required summary text, hatched "not known" row; used by Evidence and Dispatch.
- Evidence Overview: `ReportingFacts` (readings / gateway contact / analysis up to date as separate facts, as-of, per-source latest-taken strip). Evidence Analysis: lead question; S2 limit panel and the S3-02b section ("What the readings can support") precede the inspector.
- `EvidenceClaimLimit.tsx`: shared `ProductStatus` (currentnessWords; CURRENT without a positive conclusion -> limited tone; refusals via `readResultWords`, as of = answer time), `RoleStrip` covered/missing per needed reading; local `CURRENTNESS_WORDS` removed; Technical disclosure values are single labelled references.
- `PerformanceDispatch.tsx`: `statusWords` wraps `currentnessWords` with dispatch `STATUS_SENTENCES` (`dispatchWords.ts`, replaces `STATUS_WORDS`); Overview `HeadlineVisualCard` "dispatch-story" with `DayBlockStrip` (exact revision+block links), totals (unstated portion = not known), limitations, Analysis link, `DispatchReferences`; Analysis `ReadingsToOutcome` (readings -> rule -> bounded conclusion), versions list, stored record and comparison as closed technical disclosures; `constraintWords` unknown -> plain fallback.
- `assessmentAnalysis.tsx`: method version / assessment reference / record-set reference -> `ExactReferences`.
- W1 set opted in: `evidence-analysis`, `dispatch`, `analysis` (`evidence` since UX-01). Capture tool `tools/w1-ux-03-evidence.mjs`.
- Open: G-04 baselined fuel/money sentence keeps "claim" (W1 scan allows only it); no-day claim-limit state has no read instant; source strip shows latest-taken only (no per-source span in the read).
## W1-UX-04 - Action, work, change and verification presentation (built, in_review)

Branch `task/W1-UX-04` (base main `b4a89314`, unmerged); packet `archive/agent-history/W1-UX-04-review-packet.md`. Frontend only. All nine routes opted into the W1 vocabulary set (action-overview was opted in by W1-UX-01).

- Answer cards (shared `HeadlineVisualCard`, `data-headline-card`): `recommendation` (`SiteRecommendation.tsx` `RecommendationCard`), `change` (`SiteFoundationChange.tsx` `ChangeCard`), `action-work` / `action-history` (`SiteAction.tsx` `WorkCard`, `HistoryCard`), `site-work` (`SiteWorkActions.tsx` `SiteWorkCard`), `verification` / `action-plan` / `action-evidence` (`verificationCards.tsx`, mounted in `SiteActionVerification.tsx`).
- Domain-local words in `actionPresentation.tsx`: `applicationWords`, `recommendationWords` (holds are problem/waiting, never positive), `plainEventWords`, `trialStep` (moved from `SiteAction.tsx`).
- As-of sources (no read carries a read instant except Site Work `read_at` and Evidence `knowledge_cutoff`): recommendation = acceptance time, else latest stored input window end, else (held) the blocking Action's latest recorded step; change = `recorded_at`; verification = outcome `recorded_at`, else the Action read cutoff/last event; plan = plan `recorded_at`.
- Site Work: proved zero only after a loaded read (`read_at` beside it); a refused/unread list shows "As of: time not recorded" and no count.
- Verification card: failed limits in plain units (minutes, %, kWh); a selected earlier outcome reads Historical with "Current state:" beside it.
- Jargon labels made plain: Input/Plan content/Day group/Configuration reference; stored measure values and day-group status are exact references.
- Capture: `tools/w1-ux-01-evidence.mjs` knows all W1-UX-04 cards; `W1_NO_VISUAL_OK`, `W1_TAB_TRACE` env.
- Open: refusal states cannot meet `expectStateLineVisible` (no instant to show); Evidence completeness counts slots with no problems (caller-side `slotProblems`); duplicate word maps in `verificationWords.ts` remain (wrapped, not replaced).

## W1-UX-05 - Foundation, Readiness, SLD, Health and battery presentation (built, in_review)

Branch `task/W1-UX-05` (base main `815888f0`). Packet `archive/agent-history/W1-UX-05-review-packet.md`.

- Settled: the five routes `foundation`, `readiness`, `sld`, `health`, `asset` lead with the shared `HeadlineVisualCard` and are opted into the W1 vocabulary set. Cards live in `frontend/src/sites/foundationHeadlines.tsx` and `healthHeadlines.tsx`, with domain-local `ProductWords` (period, set-up readiness, contact summary, gateway contact, battery condition); none is `positive`.
- Foundation wording: signal binding -> "channel link", digest -> "content reference", type labels "Solar array"/"Supplied users"; single values marked via `frontend/src/sites/exactValues.tsx` (`UserName`, `ExactRef`).
- SLD reporting is drawn as a not-known mark; Health contact and reported-fact age are separate lanes; battery "cannot yet be judged" with missing inputs as a step strip.
- S7-01b Lows: L1 (observed-after-receipt -> Unknown age), L3 (selected-gateway IDs to the disclosure), L4 (`isBatteryDetail` requires UNKNOWN; 409 test) done.
- Refusals, the empty Foundation period and the unreadable store carry the state line.
- Open: S7-01b L2 (backend negative `receipt_lag_seconds`); shared `expectStateLineVisible` rejects `asOfText(null)`; three backend "binding" statements replaced in the UI only when no link set is in effect; green S1 "Ready to report" verdict remains under the neutral card; `tools/w1-ux-05-evidence.mjs` 390 px overflow measurement inherits a UX-01 timing issue.
- Proof at `af9b6406`: tsc 0; full frontend 1755 passed; check-all 9/9; served captures for all five screens (empty-period page not run by design).

## W1-UX-06 - W1 presentation closeout and combined owner walkthrough (built, in_review)

Branch `task/W1-UX-06` (base main `a9b3b297`, main merged at `22df6d7d`). Packet `archive/agent-history/W1-UX-06-review-packet.md`; phase-1 handoff `archive/agent-history/W1-UX-06-phase-1-handoff.md`; ruling `D-2026-10-17-w1-ux-06`.

- Settled: one shared evidence width check `tools/evidence-checks.mjs` (`widthGuard`, `AS_OF_PATTERN`) in all 24 browser evidence scripts, enforced by `tools/checks/test_evidence_checks.mjs` (inventory + proximity rule ignoring commented guards) in `check-all.ps1`; shared `expectStateLineVisible` accepts only a formatted UTC instant or "As of: time not recorded".
- Backend: negative `receipt_lag_seconds` -> null; no-set sentences say "channel-link set"; `READINESS_STATEMENT` says "Set up to report means ..." (configuration only); `BINDINGS_NOT_REGISTERED` refusal reworded (code unchanged).
- Labels per the ruling: "Set up to report" badge, "Set-up steps" strip, old/unknown-age selected-gateway lines, non-positive unrecognised/zero-enabled headlines and state line (Health `contactSummaryWords`), own-key Readiness codes (`Object.hasOwn`).
- Financials `useRead` is keyed on its request (no stale-answer commit); `w1-ux-02-evidence` amount check scoped to the card.
- Fixed: Action Evidence crashed on object `SourceSide.reasons` (`SiteActionVerification.tsx`, type in `verificationClient.ts`).
- Walkthrough: `.agent/W1-UX-combined-owner-walkthrough.md` (16 parts, 26 screens + S4-08); final captures and per-tool guides in `.agent/W1-UX-06-evidence/` (1898/1908; the 10 failures are "small visual" on held/empty cards).
- Open: owner notes 1-13 in the walkthrough (money words L4, untimed money L6, Readiness strip vs contact, card/panel duplication, no-picture held/empty cards, SLD 390 inner scroll); `widthGuard` window fallback unexercised in real Chrome; `LINK_DISPLAY_OVERRIDES` and G-04 allowance carried from UX-02/03.
- Proof: backend full 2590 passed/0 skipped at `b7d75daf`; frontend and guards in the packet.

## W1-UX-07 - full v6.9 left menu with unavailable entries (built, in_review)

Branch `task/W1-UX-07` (base main `3bb1b8b2`). Packet `archive/agent-history/W1-UX-07-review-packet.md`; ruling `D-2026-10-17-w1-rail`.

- Settled: `NavRailItem` is a discriminated union (`NavRailUnavailableItem`: `kind: "unavailable"; to?: never`); unavailable roots render as `li.nav-rail__unavailable` text with visible `NAV_RAIL_UNAVAILABLE_STATUS` ("Not available yet") and `aria-label="<label>, Not available yet"`, no link/handler/tabindex.
- `OperatorShellLayout.operatorRailItems`: six groups / eleven roots in v6.9 order; live only Sites `/sites` and Findings `/findings`. One item per line (the guard parses it).
- Workspace footer: `WorkspaceShellLayout` renders the gated `Workspace utilities` nav ("WORKSPACE" + "Open Simulator Lab") and passes it via outlet context (`WorkspaceChrome`); `OperatorShellLayout` places it under the rail and stays flag-free. The old `.workspace-bar` above the shell is gone.
- Guard: `Get-OperatorRailFailures` in `navigation-truthfulness.ps1` (fail-closed inventory, live targets registered inside the OperatorShellLayout block before the `*` catch-all, no destination on unavailable items, NavRail type check); 14 fixtures in `tools/checks/navigation-rail-fixtures.ps1` (architecture seam).
- Orphan scan: `REVIEWED_EXEMPTIONS` in `missing-claim-scan.mjs` exempts only the NavRail status const (file + const + exact text, refs confined to that file).
- Evidence: `tools/w1-ux-07-rail-evidence.mjs` (1440/390, gate on/off, mock rail equality).
- Open: promoting any other root needs its cross-site route, inventory, guard expectation and tests changed together; the 390 px rail is about 575 px tall above content (owner look).

## POLISH PB-0 - strict capture gate, review-mode labels, guard 12 (built, in_review)

- P-04 mechanism (sheet §2, Addendum 1 Q1): `frontend/src/ui/mock-deviation.css` ends with
  `:root:not([data-review-labels="on"]) [data-mock-deviation] { display: none !important; }`, loaded app-wide by
  `main.tsx`, which calls `applyReviewLabels()` (`ui/reviewLabels.ts`) before rendering. `?review=labels` stores
  `sessionStorage["assetops.reviewLabels"]="on"`, `?review=off` removes it; storage failures fall back to the parameter.
  Every label must sit in an element carrying `data-mock-deviation="Rnnn"` (or render through `MockDeviation`).
- Guard 12 (`tools/check-all.ps1`, "Mock deviation labels and client vocabulary"):
  `tools/checks/mock-deviation-labels.mjs` (a) untagged labels, (b) unregistered ids, (c) hide rule; fixtures in
  `tools/checks/fixtures/mock-deviation-labels/`. check-all now reports 12 guards.
- `tools/evidence-checks.mjs` exports `LOADING_LINE`, `SETTLE_PROBE`, `mainSettled` (whole-line loading sentence,
  `aria-busy`, `[data-repeat-check="loading"]`); `demo-combined-evidence.mjs` settles with them.
- `demo-combined-evidence.mjs`: `DEMOB_STRICT=1` exits 1 on counted hits; `DEMOB_REVIEW_LABELS=1`; exempt regions
  `[data-technical-details]`, `[data-time-zone-note]`, `[data-vocabulary-exempt]`; product terms from
  `productVocabulary.json` after its own glosses; captures.json carries `vocabulary_counted` and `exempt_hits[]`.
- Region rules (Addendum 5) live in pure `tools/demo-combined-vocabulary.mjs` (`classifyCapture`, `CAPTURE_TEXTS`):
  ids are checked on all visible main text and only `[data-technical-details]` hides them; `data-vocabulary-exempt`
  exempts product kinds only, `data-time-zone-note` only UTC; MOCK DEVIATION never exempt. Tests sit in guard 12.
- Open: `[data-repeat-check]` (PB-3), `[data-technical-details]`/`[data-time-zone-note]` (PB-1/PB-2) not yet rendered;
  the strict baseline in `archive/agent-history/POLISH-PB-0-packet.md` is the hit list later slices clear.

## POLISH PB-1 - shell, time consolidation, P-03 (built, in_review)

- Time (§3 Times, D-4 revised by Addendum 6 Q7, Addendum 7): `frontend/src/ui/time.ts` is the one client formatter:
  `formatDay`, `formatDayTime`, `formatTime`, `formatRange`, `formatDayRange`, options `{timeZone, seconds, year}`;
  computed in UTC unless a Site zone is passed (due dates only); unparseable input gives `Time not available yet`.
  `ui/TimeZoneNote.tsx` renders `[data-time-zone-note]` "Times in UTC" (the `dueDates` variant is for PB-3, Addendum 7 Q6).
- Delegating formatters (names kept): `productWords.plainTime`/`asOfText`, `actionPresentation.when`,
  `estateShared.utcInstant`, `globalWorkClient.globalWorkUtc[Seconds]`, `coldFormat.hm/dayHm/windowText`,
  `EvEnergy.utcSeconds`, `EvScenarios.utcMinute`, `SiteFindingIndex.utcText`, `SiteWorkActions.utcText`,
  `FoundationRevisionPanel.formatInstant`, `SiteHealth.formatInstant`, `portfolioWords.dayMinute`,
  `estateFinancialsWords.moneyWindowText`, `EstateEvidence` windowText, `WorkRequestHistory.historyUtc`.
  Seconds only where a ruling shows them (R372 historical lines, R369 history, SiteHealth, EvEnergy, cold `hm`).
- Notes sit in: `EstateDateBar`, the Kobo day control (`SiteWindowOverview` DaySelector), cold `SelectedWindowBar`/
  `RequestedWindowBar`, EV `SelectedWindowBar` and the EV assessment requested bar, global work `StatusLine`,
  the work request as-of line, and the verification status strip.
- §3.1 rows done in PB-1 (Addendum 7 Q1a; PB-2/PB-3 skip them): Kobo "Day" control with the bounds sentence deleted;
  Kobo CURRENT line "Latest checked readings · 29 Oct 2026 · updated …" (`DayStateLine`); cold "… · information up to
  17:05"; EV "… · as of 27 Oct, 09:00"; work "Updated … · Reload"; estate window/cutoff/disclosure (R652);
  "Supported, coherent source" → "Well supported" (Q4).
- Shell: rail "Simulator Lab"; `OperatorShellLayout` banner `[data-demonstration-banner]` (R651); `SitePageHeader`
  badge "Example data" for the SIMULATED mode word. P-03 CSS in `estatePortfolio.css`.
- Test helper `AS_OF_PATTERN` (and its mirror in `tools/evidence-checks.mjs`) no longer expects " UTC".
- Open (listed for PB-3 in `archive/agent-history/POLISH-PB-1-packet.md`): visible "UTC" left in non-capture screens
  (PerformanceDispatch, SiteFinding*, LedgerSiteEvidence, EvidenceClaimLimit, EvAvailability, assessmentGraphics,
  MiniPerformance, MiniScenarios, ColdScenarios, ColdCooling, coldDepthGraphics, evDepthGraphics, siteWorkCases,
  coldWorkPresentation, SiteAction, Foundation panels, Simulator Lab tooling) and their page notes.

