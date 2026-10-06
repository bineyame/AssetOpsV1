# v6.9 Site Mock-up Comparison and Enhancement (Architect)

Produced by **Claude as Architect under the scoped 2026-10-06 exception** in
`.ai/ROLE_CONFIG.md` ("Scoped Claude Architect Exception: v6.9 Site Mock-ups").
Owner request and follow-up are verbatim in
`.agent/owner-v69-site-mockup-comparison-2026-10-06.md`. Scope covers the static
mock-ups in `frontend/mockups/v69/` only. Backend, frontend app, gateway and
simulator realization are excluded and stay Codex-bound.

Sources: `Docs/Product/AssetOps_Integrated_Product_Experience_and_Canonical_Screens_v6_9.pdf`
(text extract `.agent/v6_9_product_text.tmp.txt`; 8.18 at line 2903, 8.19 2972, 8.20 3077,
8.21 3161, 8.22 3260, 8.23 3357, 8.24 3443, 8.25 3546, 8.26 3625, 8.28 3777, 8.29 3862,
8.30 3960, 8.31 4054, 8.35 4410, 8.36 4536). Figure numbers equal section numbers
(Figure 18 = 8.18 and so on). Presentation rules: `D-2026-10-04-plain-language-analysis-views`,
`D-2026-10-04-practitioner-first-finding-presentation`.

Line references `screens.js:N` point to the **pre-change** file. A copy of it is in the
session scratchpad at `v69-before/`. Screen ids are route ids (`#/id`).

## 1. Summary verdict

The mock-up site pages were already stronger than v6.9 on claim honesty. They show
Unknown instead of invented healthy percentages, keep bounded ranges, include
"what it establishes / limit" tables, and attach a next step to every gap. Four
problems held them back:

1. **The two verticals had different skeletons.** The mini-grid Overview had a
   consequence panel and a next step but no causal story. The cold-room Overview had
   the causal story but no consequence and no next step. The Findings, Work, Evidence
   and Financials tabs for cold and EV were thin one-table stubs with different columns.
2. **Canonical vocabulary was broken in places.** v6.9 8.18 forbids opportunity or
   strength terms as status values, but the mock-up used "Opportunity", "Not assessed"
   and "Unverified" as card statuses.
3. **Some canonical structures were missing.** Site Work had no Actions | Incidents |
   Maintenance subtabs (8.26). Site Findings lens chips navigated away instead of
   filtering (8.25). Financials had no Confidence column (8.36). Temperature had no
   duration or exposure figures (8.29). Cold Backup never stated the 8.31 purpose,
   which is to separate backup failure from refrigeration failure.
4. **Simulator and implementation language leaked onto product screens.** Examples:
   "commit a Lab run", Health and Changes linking into the Simulator Lab, "Private
   truth" in the claim drawer, and record ids and mapping versions in the default
   Evidence reading.

All of these are now fixed in the mock-up. The site pages are at parity with v6.9
on structure, and stronger on causal clarity, cross-vertical consistency and
honest degraded states. Build plus browser review: 77 screens, 396 checks, 0
runtime errors. The tallest book page is 1560 px, against a limit of 1728.

## 2. Per-section gap table (before the changes)

Key: **C** = covered well, **M** = missing, **W** = weaker than spec, **X** = contradicts spec.

### Mini-grid 8.18–8.26

| v6.9 | Item | Mock-up (before) | Status | Now |
|---|---|---|---|---|
| 8.18 (Fig 18) | Five assessment cards routing to Performance | `mini`, screens.js:114 | C | kept |
| 8.18 | "Cards use canonical assessments … do not mix opportunity/strength terms" | Renewable = "Opportunity", Fuel = "Not assessed" (screens.js:114) | X | both Unknown; opportunity named in the note with F-109 |
| 8.18 | Status line shows assessment, service and confidence | assessment + scope only (screens.js:112) | W | adds Confidence: Low |
| 8.18 | Operational timeline with Demand / PV / Generator / SOC | no SOC series (screens.js:115) | W | SOC carried in the new causal strip; chart unchanged |
| 8.18 | Needs-attention items name their destination ("Performance > Dispatch") | generic links (screens.js:115) | W | destination labels added |
| 8.18 | Chart is context, not a status source | stated | C | kept |
| (beyond) | Causal story of the selected hour | absent | M | new "What happened" strip |
| 8.19 (Fig 19) | Asset condition separated from source health | `health`, screens.js:217-218 | C | kept |
| 8.19 | Open findings / open work counts per asset | free-text Work column | M | count columns added |
| 8.19 | Source health uses Online/Stale/Offline + quality grade | free-text status (screens.js:218) | X | vocabulary adopted; adds "Not connected" |
| 8.19 | Header "N monitored asset groups · summary only" | absent | M | added |
| rules | Product page must not route to the Simulator Lab | Gateway → `lab` (screens.js:218) | X | routes to Site Evidence |
| 8.20 (Fig 20) | ServiceWindow figures, demand vs served, events list | honest Unknown (`service`, screens.js:311-316) | W (legitimate degraded state) | adds delivered-by-feeder graphic, "interruptions seen" card, hatched "what was needed" bar |
| 8.21 (Fig 21) | Necessary / Candidate / Indeterminate; Indeterminate neutral grey | `dispatch`, screens.js:138-139, CSS `.segment.gap` | C | kept |
| 8.21 | Selected-interval constraint list with provenance per row | static 14:20 panel, no per-row provenance (screens.js:139) | W | panel follows selection; each row tagged observed / declared / missing |
| 8.21 | Plain wording | "episode transition uncertainty", "power-mean support" | X (presentation rule) | rewritten |
| 8.22 (Fig 22) | Waterfall opening + deliveries − use − closing ± uncertainty | table only (`fuel`, screens.js:321) | W | waterfall with hatched unknown terms; expected use 4.9–5.9 L derived from existing data |
| 8.23 (Fig 23) | Canonical assessment + confidence; opportunity links back to Dispatch | status "Opportunity identified" (screens.js:145) | X | Watch · Confidence Medium · Lens: Opportunity; link to Dispatch |
| 8.23 | Renewable share, curtailment | absent (productive-use adaptation) | M | not added (see section 5, D7) |
| 8.24 (Fig 24) | Backup event chains table with PASS/FAIL, days since test | readiness steps only (`backup`, screens.js:326-330) | M | shared chain table (empty-window row) and four cards including "Last witnessed test: No record" |
| 8.25 (Fig 25) | Columns Finding / Domain / Severity / Confidence / State / Consequence / Lens | no Severity, no Lens (screens.js:84-87) | M | shared component, Priority + Lens columns |
| 8.25 | Lens chips filter the same index | chips navigated to `renewable` and `asset` (screens.js:333) | X | in-place filter (`data-site-lens`) |
| 8.25 | Scope line "Scoped · N open · Manage in Findings" | notice only | W | status line added |
| 8.26 (Fig 26) | Subtab row Actions (n) / Incidents (n) / Maintenance (n) | Actions table only (`sitework`, screens.js:338) | M | three routed subtabs with counts and explicit empty states |
| 8.26 | Due column | absent | M | "Due" shown as "Not set", matching Portfolio's withheld-due rule |

### Cold chain 8.28–8.31

| v6.9 | Item | Mock-up (before) | Status | Now |
|---|---|---|---|---|
| 8.28 (Fig 28) | Separate Temperature / Backup / Cooling / Maintenance / Evidence cards; product risk as a purple chip | `cold`, screens.js:239-240 | C | kept |
| 8.28 | Maintenance card uses the assessment enum | "Unverified" | X | Needs attention · "outcome not yet verified" |
| 8.28 | Cards route within the site | Evidence card → `globalevidence` (root change) | X | → `cold-evidence` |
| 8.28 | Timeline includes compressor off and return to policy | stopped at peak (screens.js:83) | M | eight-event chain, ending "Back within 2–4°C by 19:45" |
| 8.28 | Immediate actions carry object refs and state | none | W | ACT-051 / WR-019 / F-118 with destinations |
| (beyond) | Objective sentence, bounded consequence, next step (parity with mini) | absent | M | added |
| 8.29 (Fig 29) | In-policy %, excursion duration, max deviation, degree-minutes | "Bounded" placeholder (`temperature`, screens.js:247-249) | W | 25–35 min; ≈70 °C·min (estimate); in policy 42–58%; coverage 13/13 |
| 8.29 | Excursion window, door/loading/power context | partial kv (screens.js:248) | W | window bounds and backup link added |
| 8.29 | Excursion highlighted on chart | absent | M | shaded band "Above 4°C for 25–35 min" |
| 8.30 (Fig 30) | Context normalisation table; candidate, not diagnosis | `cooling`, screens.js:255-258 | C | kept |
| 8.30 | Plain wording | "pull-down" | X (presentation rule) | "time back to 4°C" |
| 8.30 | Cooling energy figure | absent | M | not added (P3, no data in fixture) |
| 8.31 (Fig 31) | Multi-event chain table, Grid → Command → Genset → Transfer → Compressor → Temperature → Result | single-event cards and evidence table (`coldbackup`, screens.js:261-267) | W | shared chain table; transfer shown as an explicit missing link |
| 8.31 | Purpose: tell backup failure apart from refrigeration failure | never stated | M | headline "The backup failed; the refrigeration did not." |
| 8.31 | Evidence by causal step (what it establishes / limit) | present | C (stronger than spec) | kept |

### Readiness 8.35 (Site Evidence)

| v6.9 | Item | Mock-up (before) | Status | Now |
|---|---|---|---|---|
| 8.35 (Fig 35) | Capability × Full/Limited/None/N-A × ceiling × missing × next evidence | mini `evidence`, screens.js:154 | C | kept, plain wording |
| 8.35 | Backup readiness capability | absent | M | added (None) |
| 8.35 | Source health Online/Stale/Offline + quality | free text (screens.js:155) | X | adopted |
| 8.35 | "Each priority creates an Action" | first priority had no link (screens.js:155) | W | every item has a link; "Raise action →" opens site Work |
| 8.35 | Overall evidence readiness % | absent (deliberate) | deliberate | capability counts instead (D3) |
| D-2026-10-04 | Site Evidence has local Overview \| Analysis; ids out of the default reading | record table with mapping ids on the default page (screens.js:156) | X | moved to Evidence › Analysis |
| 8.35 cross-vertical | Same layout for every site | cold/ev evidence was a 4-column stub (screens.js:384-387) | W | shared `siteEvidenceScreen` |

### Financials 8.36

| v6.9 | Item | Mock-up (before) | Status | Now |
|---|---|---|---|---|
| 8.36 (Fig 36) | Consequence-line count instead of a financial assessment | `financials`, screens.js:180 | C | kept; adds "Data confidence" chip |
| 8.36 | Bridge columns Technical / Mechanism / Consequence / Basis / **Conf.** / Source | no Confidence (screens.js:94) | M | Confidence column added |
| 8.36 | Value returns to its source finding | Source column | C | kept |
| 8.36 | Portfolio roll-up link | absent | M | added |
| 8.36 | Subtabs Overview / Drivers / Assumptions / Scenarios | Consequences / Assumptions | W | renamed Overview / Assumptions; Drivers folded into Overview; Scenarios deferred (D4) |
| 8.36 | Implementation note in the default reading | "outward rounding…" notice (screens.js:184) | X (presentation rule) | moved to review notes |
| 8.36 | Assumption-set id in the default reading | "BC-MG-01-v1" | X (presentation rule) | removed from status |
| 8.36 cross-vertical | Same bridge for every site | cold/ev: no Source, no Confidence, no Assumptions subtab (screens.js:388-391) | W | shared `siteFinancialsScreen` + `-assumptions` screens |

### Out-of-section leaks fixed because they appear on site pages

| Where | Problem | Now |
|---|---|---|
| `variant()` screens.js:469 | "commit a Lab run" in the No-evidence state | plain sentence |
| claim drawer screens.js:521-522 | "Simulated · gateway mapped", "Private truth", SourceEnvelope inline | plain provenance; technical record inside a closed `<details>` |
| `changes` screens.js:133 | link into the Simulator Lab | links to Site Evidence |

## 3. Strengthening recommendations (beyond parity)

| # | P | Recommendation | Justification (one line) | Applied |
|---|---|---|---|---|
| R1 | P1 | One site-Overview skeleton for every vertical: status + confidence → objective → canonical cards → causal strip → context + needs attention (with destinations) → bounded consequence + next step | A practitioner learns one reading order and uses it at any site | yes (mini, cold) |
| R2 | P1 | Cards use only Healthy / Watch / Needs attention / Degraded / Unknown; opportunity becomes a lens chip or a note | Status and lens are different questions, and v6.9 8.18 says so | yes |
| R3 | P1 | Plain causal strip ("What happened") on both overviews, from accepted readings | Answers "why" before "how much", which v6.9 leaves to the deep views | yes |
| R4 | P1 | Cold Backup states the discrimination in one sentence ("backup failed; refrigeration did not") | That is the purpose of 8.31; tables alone made the reader infer it | yes |
| R5 | P1 | Temperature figures as bounded ranges from the 5-minute readings, plus a shaded excursion band | Gives real numbers without false precision; placeholders were weaker than the spec | yes |
| R6 | P1 | Shared Findings index (lens filters in place, Priority + Lens columns) for all verticals | Scoped indexes must mirror one object class (8.25) | yes |
| R7 | P1 | Site Work Actions \| Incidents \| Maintenance subtabs with counts and explicit empty states, for all verticals | Mirrors the left-nav WORK group one-to-one (8.26) and shows empty states honestly | yes |
| R8 | P1 | Shared Evidence layout with Overview \| Analysis; source status vocabulary; every gap raises an action | Applies D-2026-10-04 and 8.35 consistently; ids leave the default reading | yes |
| R9 | P1 | Shared Financials bridge with Basis + Confidence + Source, Assumptions subtab, roll-up link, for all verticals | The same discipline everywhere, and unpriced lines stay visible as lines | yes |
| R10 | P1 | No simulator wording or Lab routes on any Sites-root screen, enforced by a browser check | Owner presentation rule, now guarded rather than remembered | yes |
| R11 | P2 | Dispatch selected-block panel follows the selection, with observed / declared / missing tags per input | Makes the missing endpoint visible where the decision is made | yes |
| R12 | P2 | Shared backup chain table across verticals; an empty window is a labelled row | Cross-vertical pattern; "no event" differs from "passed" | yes |
| R13 | P2 | Fuel waterfall with hatched unknown terms | Shows graphically why no residual is stated | yes |
| R14 | P2 | Service: delivered-by-feeder bars with a hatched "what was needed" bar | Shows the missing half of the service judgement as a graphic | yes |
| R15 | P2 | Health: open findings/work counts, source status vocabulary | 8.19 parity, and links condition to work | yes |
| R16 | P2 | Renewable: canonical assessment + Opportunity lens + Dispatch link | 8.23 parity without losing the productive-use adaptation | yes |
| R17 | P2 | Claim drawer: plain provenance, technical record behind disclosure | Drawer opens from every site page; default reading stays plain | yes |
| R18 | P2 | Add SOC as a series on the Overview operating chart | Spec timeline includes SOC; currently carried only in the strip | **skipped** (strip carries it; chart needs a dual axis, and the book page height is tight) |
| R19 | P2 | Cold and EV Health pages get the source-status table | Same Health pattern as the mini-grid | **skipped** (outside the requested sections; low value for the demo) |
| R20 | P3 | Cooling energy figure on Cooling | 8.30 parity | skipped (no fixture data; would be invented) |
| R21 | P3 | Readiness subtab for cold/EV Foundation | Parity with the mini-grid Foundation | skipped (8.10, outside requested sections) |
| R22 | P3 | Financials Scenarios subtab | 8.36 parity | deferred to owner (W2) |
| R23 | P3 | Add F-119 and F-108 to the global Findings list and Portfolio | Site index now shows them; global lists should match | skipped (Findings/Portfolio roots are outside scope; follow-up) |

## 4. Change spec as applied (by screen)

All changes are in `frontend/mockups/v69/`. The record below is written so an
implementer could repeat it; it is already done.

**Shared (screens.js, new helpers after `lineChart`):**
- `causalStrip(events)`: generic timeline with tones `ok | gap | danger`. `eventChain()` now uses it with 8 cold events.
- `miniStory()`: five-event mini-grid strip.
- `INTERVALS`, `tag()`, `selectedInterval()`: driven by `stage.selected`; segments get `.selected` and `aria-pressed`.
- `backupChainTable(rows, emptyText)`: columns When / Grid / Start requested / Generator / Power to load / Load response / Outcome for service / Result.
- `SITE_FINDINGS`, `siteFindingRows()`, `siteFindingsScreen(domain)`: lenses All / Cost / Risks / Opportunities, as on Portfolio.
- `SITE_WORK`, `WORK_COLS`, `WORK_EMPTY`, `workRoutes()`, `siteWorkScreen(domain, kind)`.
- `SITE_EVIDENCE`, `siteEvidenceScreen(domain)`, `EVIDENCE_RECORDS`, `siteEvidenceAnalysis(domain)`.
- `SITE_FIN`, `siteFinancialsScreen(domain)`, `siteAssumptionsScreen(domain)` for cold and EV.
- `tabs()`: Financials subrow `Overview | Assumptions`, Evidence subrow `Overview | Analysis` and Work subrow `Actions (n) | Incidents (n) | Maintenance (n)` for every vertical. Still at most one subtab row.
- Click handler: `data-interval` sets `stage.selected`, re-renders, then opens the drawer. New `data-site-lens` filters in place.
- `lineChart('temperature')`: shaded excursion band with label.
- Claim drawer: provenance rows rewritten; envelope inside `<details class="tech">`.
- `variant()`: plain no-evidence copy, with no Lab wording.

**New screens:** `sitework-incidents`, `sitework-maintenance`, `evidence-analysis`,
`cold-/ev-work-incidents`, `cold-/ev-work-maintenance`, `cold-/ev-evidence-analysis`,
`cold-/ev-assumptions`, `cold-finding-excursion` (F-119). All have `book:false`, so the
PDF book stays at 40 pages.

**Per screen:** mini (R1–R3), health (R15, R10), dispatch (R11, wording), renewable (R16),
service (R14), fuel (R13), backup (R12), sitefindings (R6), sitework (R7), evidence (R8),
financials (R9, implementation note moved to review notes), changes (R10), cold (R1–R3, card
fixes, routing), temperature (R5), cooling (wording), coldbackup (R4, R12), cold/ev findings,
work, evidence, financials (R6–R9).

**mockups.css:** one appended line covering `.timeline-event.ok/.gap`,
`.segment.selected`, `.fill.unknown`, `.src-tag`, `.story-claim`, `details.tech`,
`.scope-count` and `.waterfall`.

**review-browser.mjs:** new checks for:
- no Lab route or simulator wording on every Sites screen;
- canonical card values on the mini Overview;
- the causal strip;
- in-place lens filtering;
- Work subtabs on all three verticals;
- the explicit empty Work state;
- the shared Evidence layout;
- the Financials Basis / Confidence / Source columns;
- the backup-versus-refrigeration sentence;
- the selected block following the selection.

The preview list also gains temperature, coldbackup, service, fuel, health,
evidence, cold-evidence, financials, cold-financials, sitefindings, sitework and
cold-work-incidents.

**Regenerated by tooling:** index.html, screen-manifest.json, browser-review.json,
AssetOps-v69-Screen-Review.pdf, AssetOps-Portfolio-v2.pdf, previews/*.png.

## 5. Decisions

Decided by the Architect, each with its justification:

- **D1. Unknown, never "Not assessed" or "Opportunity", as a card status.** v6.9 8.18
  restricts card values to the assessment enum. The opportunity stays visible in the
  card note and as a lens.
- **D2. Evidence card on the cold Overview uses evidence vocabulary (Limited) in neutral
  grey, not v6.9's "Healthy".** 8.35 and global Evidence keep Full/Limited/None separate
  from condition. 8.28 is internally inconsistent here, and the stricter rule wins.
- **D3. No single "overall evidence readiness %".** It would be an unexplained composite
  score (the prior mock-up already deferred it). Counts of Full / Limited / None capabilities
  answer the same question transparently.
- **D4. Financials subtabs are Overview | Assumptions.** v6.9 Drivers *is* the bridge, so
  a separate tab would fail the grammar-ownership test (D-2026-10-02). Scenarios waits for a
  scenario with a declared basis (W2).
- **D5. Temperature figures are bounded ranges from the 5-minute readings.** Duration is
  bracketed by readings (25–35 min). Exposure size is a straight-line estimate labelled as
  such. This reverses the earlier "no numbers" choice: the samples exist, and a placeholder
  reads as weaker than the spec.
- **D6. Source status vocabulary is Online / Stale / Offline plus "Not connected", read at
  the end of the selected window.** "Not connected" (never configured) must not be
  confused with Offline (configured but silent).
- **D7. The productive-use adaptation on Renewable is kept; renewable share and
  curtailment are not added.** It is an owner-led prior adaptation, and adding those
  figures would mean inventing data for a separate five-day study.
- **D8. Site Findings lenses copy Portfolio's (Cost / Risks / Opportunities), and the
  column is "Priority" rather than v6.9 "Severity".** The same Finding must read the same
  everywhere; Portfolio already set this precedent.
- **D9. Due shows "Not set".** Portfolio already withholds due dates because the fixture
  does not establish them; inventing them here would contradict Portfolio.
- **D10. F-119 gets a minimal Finding page.** INC-203 already referenced it with no
  destination, which was a dead reference.
- **D11. Shared builders over per-vertical copies.** Consistency across verticals is the
  point of the pivot; three copies would drift.

For the owner to weigh in on (each with the Architect's decision and justification):

- **W1. The "Simulated" badge on every product page heading and the Sites "Mode"
  column.** Decision: left unchanged in this pass. It is shared shell chrome, outside the
  site-page scope, and it is honest provenance. Recommendation: rename it to "Demo data"
  for client sessions, which keeps the honesty without simulator wording.
- **W2. Financials "Scenarios" subtab (v6.9 8.36).** Decision: deferred. No scenario in
  the fixture has a declared basis, and an empty subtab would be a place that owns nothing.
  Add it when a priced what-if exists, for example a stop-setting trial or a declared stock
  value.
- **W3. Global Findings list and Portfolio should list F-108 and F-119.** Decision: not
  changed, because those roots are outside this scope. Site indexes now show them, so the
  global lists are one follow-up edit from matching.
- **W4. Temperature estimate method (straight-line between readings).** Decision: shown
  as "≈70 °C·min, estimate". Please confirm this is acceptable for client-facing review,
  or say whether you prefer the range only.

## Files

- Changed: `frontend/mockups/v69/screens.js`, `mockups.css`, `review-browser.mjs`.
- Regenerated: `index.html`, `screen-manifest.json`, `browser-review.json`, both PDFs, `previews/*.png`.
- New previews: `previews/{temperature,coldbackup,service,fuel,health,evidence,cold-evidence,financials,cold-financials,sitefindings,sitework,cold-work-incidents}.png`.
- Not touched: portfolio.js/css, build.mjs, render-reference.ps1, `.ai/`, backend, frontend/src, gateway, simulator. Nothing committed.

---

## 6. Round 2 (owner follow-up 2, 2026-10-06)

Produced by Claude as Architect under the same scoped exception, extended by the
owner for: EV recommendations, interactive site selection, a date-range selection bar
and the site single line diagram. Mock-up files only; nothing committed.

Result: 82 screens and 437 browser checks pass with 0 runtime errors. The PDF book is
41 pages. The tallest book page is `coldbackup` at 1682 px, giving a PDF page of 1712
against the 1728 limit.

### 6.1 What was added

| Item | Where | What it does |
|---|---|---|
| EV Overview | `ev` | Rebuilt on the shared skeleton: status with confidence → objective → canonical cards (Session service Needs attention, Availability Watch, Site power Healthy, Charger condition Unknown, Evidence Limited) → seven-event "What happened on the service day" strip → context + needs attention (with destinations) → bounded money ($36.00 gross tariff estimate, not collected) + next step |
| EV recommendation | `ev-recommendation` (Findings › F-130 › Recommendation) | Covers what to do next (check connector 2, then witness a full session); owner (Charging operations lead); linked action ACT-061; a declared success criterion with guardrails; "What it is worth" as separate Service, Availability and Money lines; and other site recommendations with owners |
| Cold recommendation | `cold-recommendation` (F-118) | The same grammar, so all three verticals have a Recommendation tab; marked Accepted as ACT-051 |
| EV Health | `ev-health` | Card values changed to canonical ones (Unknown / Needs attention / Not applicable) |
| Site selector | page heading on every Sites screen (`#site-switch`) | Switches site and keeps the equivalent tab or subtab, via a slot map (Overview, Foundation, Single line diagram, Health, Performance with Backup ↔ Backup, Findings, Work Actions / Incidents / Maintenance, Financials Overview / Assumptions, Evidence Overview / Analysis). A tab with no equivalent falls back to the section's first view |
| Analysis period bar | under the tabs on every Sites screen | Presets: Event window · Selected day · Last 7 days · Last 30 days · Custom range (two dates and Apply). Shows "Analysed window", six period figures per site, and the top-bar window label. The range persists across tabs and sites; a note marks the page detail as the event in focus. In the evidence-limited and no-evidence review states, figures are withheld |
| Single line diagrams | Foundation › Single line diagram (`sld`, `cold-sld`, `ev-sld`) | Inline SVG in the mock-up style. Shows sources, conversion, breakers, the AC bus, feeders with kWh meters, and the monitoring row. Reporting dots (reporting / gap / not connected) come from the same source data as Site Evidence. A "What each part does" table follows. Overview context panels link to the diagram |

### 6.2 Decisions (Architect)

- **E1. The diagram lives in Foundation as its own "Single line diagram" subtab, for every
  site.** Foundation owns the configured physical model (8.10). v6.9 8.12 is a dedicated
  site view. Putting it inline on the Overview would push the Overview past the PDF
  page-height limit and bury the operational story. Overviews link to it from their
  context panel.
- **E2. Product view, not simulator view.** I reused §8.12's structure (sources, breakers,
  bus, loads) but left out its live flows, true-versus-reported values, breaker toggles and
  inject controls. Status dots show evidence reporting in the selected window, the one
  thing the product legitimately knows (D-2026-10-04-plain-language-analysis-views).
- **E3. Diagrams are drawn as inline SVG from site data rather than copied PNGs.** This
  keeps them consistent with the mock-up style and the site configuration, and lets
  evidence status drive the dots. The reference files in `Docs/Site_Line_Diagrams/` were
  used for symbols and layout (AC-coupled mini-grid; solar cold chain). Nothing was copied.
- **E4. The cold-room diagram follows the mock-up's site, not the solar reference.**
  GreenHarvest is grid plus diesel backup through a transfer switch, with a 10 kWh battery
  for controls only (Foundation now says so). The transfer switch is drawn as "not
  connected", which matches the missing link in the backup chain.
- **E5. EV extrapolation (v6.9 has no EV section).**
  - Objective: charge vehicles when scheduled within the 80 kW import limit.
  - Overview cards: Session service, Availability, Site power, Charger condition and
    Evidence. They map to the cold room's Temperature / Backup / Cooling / Maintenance /
    Evidence slots.
  - Performance subtabs: Sessions | Availability | Energy and site power.
  - No Backup view, because the site has no backup source.
  - Money: gross tariff estimate only, never collections. An interrupted session is
    unpriced as a loss; the recommendation shows one average session (≈ $3.49) as a
    labelled scenario per avoided interruption, not as lost revenue.
  - The EV diagram is drawn new: grid → site meter and load manager → bus → two 60 kW DC
    chargers plus depot auxiliary.
- **E6. Period figures come from one 30-day daily series per site (7 Sep – 6 Oct 2026).**
  Every preset and any custom range sums the same days, so they stay consistent.
  - The final day matches the event figures (mini: 0.5 h avoidable; cold: the failed start;
    EV: 12 attempts, 120 kWh).
  - Mini-grid cost exposure uses the same formula as `money()` and follows the
    assumption-price edit.
  - The 30-day figures reproduce existing fixture facts: 5 battery reserve breaches (Asset
    Health) and 2 of 3 automatic starts working (v6.9 8.31 pattern).
- **E7. Preset wording follows v6.9 terms.** v6.9 uses "selected day" and a top-bar date
  range, so the presets are Event window · Selected day · Last 7 days · Last 30 days ·
  Custom range, with "Analysed window" as the label. The page detail stays on the event in
  focus and says so, rather than pretending each chart re-aggregates.

### 6.3 Skipped or limited

- Page charts, cards and tables do not re-aggregate per range. Only the period strip and
  the window labels change, and the note says so. Full re-aggregation would need a
  per-range fixture for every screen.
- No click-through from diagram components to asset pages: only BAT-001 has an asset page.
  The note states the intended interaction.
- No separate site-selector preview frame: the selector appears in every site preview, and
  `site-switch-ev-work.png` / `site-switch-ev-findings.png` show the result of switching.

### 6.4 Owner weigh-in (updated)

- **W1 (Simulated badge): still open, and now more visible.** It sits next to the new site
  selector on every site page. Recommendation unchanged: rename to "Demo data".
- **W2 (Financials Scenarios subtab): unchanged.** The EV per-interruption scenario lives
  in the Recommendation, not in a Scenarios tab.
- **W3 (global lists for F-108 / F-119): unchanged.**
- **W4 (°C·min estimate): unchanged.** The period bar shows the same 25–35 min bound.
- **W5 (new): EV money.** Is "≈ $3.49 per avoided interruption (one average session,
  scenario)" acceptable on the EV recommendation, or should EV service consequences stay
  unpriced?
- **W6 (new): cold-room topology.** I drew a grid-plus-diesel site with a controls-only
  battery to match the existing cold story, not the solar direct-drive reference. Confirm,
  or ask for a solar cold-chain variant.

### 6.5 Files (round 2)

- Changed: `frontend/mockups/v69/screens.js`, `mockups.css`, `review-browser.mjs` (new checks; tallest-page detail in the PDF height assertion; new previews).
- Regenerated: `index.html`, `screen-manifest.json`, `browser-review.json`, both PDFs, `previews/*.png`.
- New previews: `ev-recommendation`, `sessions`, `sld`, `cold-sld`, `ev-sld`, `ev-evidence`, `ev-financials`, `date-range-30-days`, `date-range-custom`, `site-switch-ev-work`, `site-switch-ev-findings` (plus refreshed `ev`).

---

## 7. Round 3 (owner follow-up 3, 2026-10-06: layout and answers to W1–W6)

Produced by Claude as Architect under the same scoped exception. Owner text is verbatim
under "Owner follow-up 3" in `.agent/owner-v69-site-mockup-comparison-2026-10-06.md`.
Mock-up files only; nothing committed.

Result: 85 screens and 595 browser checks pass with 0 runtime errors. The PDF book is
41 pages. The tallest book page is now 1597 px (PDF page 1627 against the 1728 limit),
about 100 px of headroom regained.

### 7.1 Changes

| Owner point | Change | Where |
|---|---|---|
| Date window at the top, with site selection, as in v6.9 | v6.9 puts the date range in the top bar beside search and the user ("Aug 5 – Sep 3 2026"). The site appears in the breadcrumb and heading. On every site page the top bar now holds the site selector and an analysis-window button (clock · window · ▾). The button opens a popover with Event window / Selected day / Last 7 days / Last 30 days / Custom range, the Analysed window, and the six period figures. It closes on an outside click, on Escape or on navigation. The in-page period bar is removed | `shell()`, `rangePicker()`, `siteSwitch()` |
| W1 Simulated badge | Removed from the page-heading chrome of every page. On site pages a provenance tag sits beside the site name: "Simulated site · MG-DEMO-01" (tooltip: readings come from a simulated source, not field equipment). It is kept in the Sites list Mode column and the Foundation identity | `provTag()`, page heading |
| W2 Financials Scenarios | Placeholder subtab Overview \| Assumptions \| **Scenarios** for all three sites, with the empty state "No scenario defined yet" and a note that scenarios never change measured results | `scenarios`, `cold-scenarios`, `ev-scenarios` |
| W3 F-108 / F-119 | Added to the global Findings list (All and Risks lens) and to Portfolio priorities, which now show 6 findings and 4 in the Risks lens | `findingsTable()`, finding filter, `portfolio.js` |
| W4 °C·min | The ≈70 point estimate is replaced with a bound of **50–90 °C·min**, taking the lower and upper reading in each 5-minute step. That is the same treatment as the 25–35 min duration | `temperature` |
| W5 EV ≈ $3.49 | Kept as is | `ev-recommendation` |
| W6 Cold-room diagram | Redrawn as a hybrid, based on the solar cold-chain reference plus the backup path: 15 kWp solar → charge controller and 30 kWh battery → BMS + DC protection → DC bus → 10 kW inverter-charger → AC bus; grid and diesel generator → transfer switch → AC bus; feeders for the compressor (metered), fans and defrost, and controls / probe / alarms | `SLD.cold`, `sld()` gains generic DC-bus and transfer-switch groups |

### 7.2 Cold-room story kept consistent with the hybrid diagram

- **Night-outage rule (new, Foundation):** the battery holds controls and alarms; the
  compressor waits for the generator. The event is at 19:11 after dark, with no solar.
  This rule explains why cooling stopped despite a battery, so the existing chronology,
  the 4-minute cooling gap and the 25–35 min excursion all stand unchanged.
- The event chain says "Compressor stopped; battery holds controls (by design at night)".
  The Overview prose and Backup's "What the chain shows" both name the battery behaving as
  designed. The backup chain table reads "Compressor shed 19:11 (battery holds controls)".
- The site subtitle, Foundation power sources, Site Evidence sources (inverter-charger +
  battery) and the "What each part does" table are updated to match.
- Financials need no change: product exposure stays unpriced, and solar or battery energy
  does not create a consequence line.

### 7.3 Decisions

- **F1. Site and window sit in the top bar; period figures live in the window popover.**
  This matches the v6.9 header pattern, frees page height, and keeps figures one click
  from the window they describe. Changing a preset updates the top-bar label and the
  popover figures together.
- **F2. The provenance wording is "Simulated site" (not "Demo data").** The owner framed
  it as provenance. "Simulated" states the source precisely, and as a tag beside the
  site identity it no longer reads as global simulator chrome.
- **F3. Temperature exposure is a bound (50–90 °C·min), not a point estimate.** This is
  consistent with every other figure derived from sparse readings. The owner will revisit
  it.
- **F4. The hybrid cold room uses a night-outage load-shed rule.** That is how many
  hybrid cold rooms are actually designed, with the battery reserved for monitoring and
  alarms. It keeps one coherent incident story rather than rewriting the incident,
  finding, work and portfolio fixtures.

### 7.4 Weigh-in status

W1 to W6 are all answered by the owner and applied as above. Nothing new needs the
owner's decision. Revisit items the owner has flagged: W2 (Scenarios content) and W4
(the °C·min method).

### 7.5 Files (round 3)

- Changed: `frontend/mockups/v69/screens.js`, `portfolio.js` (F-108 / F-119 rows; 6 findings), `mockups.css`, `review-browser.mjs` (top-bar placement, no global badge, provenance tag, Scenarios placeholder, F-108 / F-119 in Findings and Portfolio, hybrid cold diagram, popover-aware range checks).
- Regenerated: `index.html`, `screen-manifest.json`, `browser-review.json`, both PDFs, `previews/*.png`.
- New previews: `date-window-topbar.png` (top bar with the window popover open), `scenarios.png`, `findings.png`; refreshed `cold-sld.png`, `portfolio.png`, `date-range-30-days.png`, `date-range-custom.png`, plus all site previews (top bar and provenance tag).

### 7.6 Fix: window picker on every operator page (owner: "i am not seeing option to select date range")

The picker previously rendered only on site pages. v6.9 section 5 makes the top-bar time window the controlling context for every page, so it now appears on all operator pages: Portfolio, Sites, Assets, Findings, Actions, Incidents, Maintenance, Evidence, Financials, plus the Finding and Action detail pages. The Simulator Lab shell is unchanged.

- The button is labelled "Window: <preset>" with the date range beside it.
- There is one shared window, and it persists across all pages and sites.
- On estate pages the popover shows six per-site figures for the window (Kobo cost exposure and reserve breaches; GreenHarvest excursions and automatic starts that worked; Depot interrupted sessions and delivered energy). It notes that the estate tables remain the illustrative selected examples.

Browser checks were added for: the picker existing and working on Portfolio and each global index, the Lab having no picker, and a window chosen on Portfolio persisting into a site. Result: 615 checks, 0 errors, PDF page 1627 px. New preview: `previews/window-picker-portfolio.png`.

---

## 8. Round 4 (owner follow-up 4, 2026-10-06: reduced confidence links to a call to action)

Produced by Claude as Architect under the same scoped exception. Owner text is verbatim
under "Owner follow-up 4". Mock-up files only; nothing committed.

Result: 85 screens and 744 browser checks pass with 0 runtime errors. The PDF page is
still 1627 px of 1728; the chips replace badges in place, so no height was added.

### 8.1 Pattern

There is one component, `conf(key)`. It renders a dashed chip, "Confidence: Low ⓘ" (amber;
Medium in blue), that opens a small popover:

- the level and what it applies to;
- a "Why · what raises it" list, one item per cause, each with a **cause category**, a
  plain one-sentence reason and **one call to action**;
- a footnote: fixing a cause raises confidence from the next accepted window, and past
  results are not rewritten.

A call to action either links to an existing screen or opens a **pre-filled "New action"
drawer** (site, action, raised from, suggested owner, success criterion, due "Not set";
example only, nothing is created). High confidence stays a plain badge.

**Cause categories:** Configuration gap · Source availability · Mapping gap · Coverage gap ·
Stale evidence. Each one reuses an existing gap from Site Evidence (8.35), the Readiness
table or the diagram status dots. There is no parallel readiness model.

### 8.2 Registry (every reduced confidence in the mock-up)

| Key | Level | Causes → call to action | Shown on |
|---|---|---|---|
| `f104` F-104 avoidable generator time | Low | Source availability: battery controller missed the 14:50 report → Restore reporting · ACT-049 (site Work). Coverage gap: generator status every 15 min, ±25 min → pre-filled "Report generator status every minute" | mini Overview, Dispatch, F-104 Overview and Analysis, site and global Findings, Portfolio, evidence drawer |
| `minifin` Kobo money consequence | Low | Source availability (inherits F-104) → ACT-049. Configuration gap: fuel rate is the public 0.30 L/kWh, no fuel curve declared → Foundation › Readiness (new row "Generator fuel curve: Not declared", which itself raises a pre-filled action) | Financials status ("Data confidence"), both bridge rows, Assumptions impact preview |
| `f109` F-109 productive-use headroom | Medium | Coverage gap: 3 of 5 days observed, day 4 missing service evidence → Performance › Service. Coverage gap: mill demand unconfirmed → pre-filled "Validate grain-mill demand" | Renewable, F-109, site and global Findings, Portfolio |
| `cooling` cold-room recovery comparison | Low | Mapping gap: door sensor and loading log not connected → Foundation › Single line diagram. Coverage gap: no comparable recovery test → pre-filled "Witnessed cooling recovery test" | Cooling |
| `f130` F-130 connector 2 interruption | Medium | Stale evidence: connector 2 last reported at 15:00 → Evidence. Source availability: SES-012 has no end record → ACT-061. Coverage gap: diagnostics not collected → pre-filled "Export charger 2 diagnostics" | EV Overview, F-130, site and global Findings, Portfolio, EV evidence drawer |

Also: the cold Site Evidence row "Backup response" now names the gap as "Transfer-switch
position (not mapped)" with a pre-filled "Map transfer switch" action. That is the owner's
mapping-gap example. F-118's confidence stays High, because the failed start is fully
observed; the missing transfer record limits the chain, not that conclusion.

### 8.3 Decisions

- **G1. Chip plus popover, not a new page.** The cause sits next to the number it
  qualifies and costs no page height. Deeper detail stays on Site Evidence, which the
  calls to action link to.
- **G2. Only Low, and Medium capped by evidence, carry causes.** High stays a plain badge,
  so the chip itself signals "there is something to fix".
- **G3. One call to action per cause, preferring existing work.** A cause links to an
  existing action (ACT-049, ACT-061) or screen where one exists. A pre-filled new action
  is used only where no managed work exists yet. This avoids duplicate actions for the
  same gap.
- **G4. "Stale evidence" is used only where a source stopped reporting** (connector 2
  after 15:00). A missing single report is "Source availability"; a cadence that is too
  slow is "Coverage gap".

### 8.4 Checks added

- No plain "Low" or "Confidence: Low / Medium" is shown without a cause chip, on every
  screen.
- Every chip on every screen (20 across the mock-up) opens a popover where each cause has
  a category, a reason, and either a link to an existing screen or a pre-filled action;
  the popover closes.
- Clicking through: a call to action navigates to site Work; a pre-filled action opens
  from EV; the evidence-drawer chip explains itself.

New preview: `previews/confidence-popover.png`.

---

## 9. Round 5 (owner follow-up 5, 2026-10-06: gateway status under Readiness)

Produced by Claude as Architect under the same scoped exception. Owner text: "under
readiness, lets have a gateway status with some details?". Mock-up files only; nothing
committed.

Result: 768 browser checks pass with 0 runtime errors. The PDF page is 1658 of 1728 px;
the tallest page is mini-grid Readiness.

### 9.1 What was added

- **Readiness on all three sites.** The mini-grid already had it. Cold and EV gain a
  Foundation › Readiness subtab (`cold-readiness`, `ev-readiness`), each with a short
  configuration and commissioning table:
  - cold: transfer-switch point "Not mapped" with a pre-filled "Map transfer switch"
    action; door and loading log "Not connected";
  - EV: connector status points configured; billing "Not connected"; tariff as a
    scenario.
  The site selector maps Readiness to Readiness.
- **Gateway status panel** (`gatewayPanel(domain)`), a product view using v6.9 8.13 fields
  as reference only. It contains:
  - **Status** (Online / Stale / Offline / Not connected) with the last message, absolute
    and relative to the window end.
  - **Availability**: uptime %, number of outages and minutes offline, plus an
    availability strip. The strip shows 15-minute or hourly cells for the event window
    and one cell per day for longer ranges.
  - **Data completeness**: received against expected readings, late readings, and the
    largest gap.
  - **Clock and delivery**: clock offset and sync, and how readings are delivered.
  - **Connected sources** as status pills (reporting / stale / never reported), with
    links to Health › Data sources and the single line diagram.
  - **Identity**: connection type, signal, firmware, and point-list version with its
    applied date.
  - **Effect on readiness and confidence**, whose calls to action reuse the existing
    actions (ACT-049, ACT-061, the "Map transfer switch" action, and a new pre-filled
    "Improve the gateway connection" action).
- **Follows the window picker.** Event-window figures are hand-set to each site's story.
  For longer ranges the figures come from the same daily series that drives the period
  figures, so they stay consistent: the mini-grid's missing readings equal 100% minus its
  "Readings received" figure.
- **Confidence link.** The follow-up 4 popovers' source-availability and stale-evidence
  causes (F-104, Kobo money, F-130) now carry a secondary "Gateway status →" link to the
  site's Readiness.

### 9.2 Per-site story (kept consistent)

- **Kobo:**
  - Event hour: gateway online the whole hour; 19 of 20 readings. The missing 14:50 report
    is the battery controller's, not the gateway's.
  - Delivery: readings are held on the gateway and sent in one batch at 16:00, which
    matches the 16:00 "received" times in Evidence.
  - Over 30 days: short gateway outages on low-coverage days, giving "Gateway offline N
    times · X% of readings missing" with the pre-filled connection action.
- **GreenHarvest:** the gateway stayed online through the grid outage because it is on the
  battery-backed controls feeder (the hybrid diagram). The transfer switch has never
  reported (not mapped).
- **Depot:** the gateway is online. Connector 2 went silent at 15:00 on the charger side,
  giving 900 of 960 status readings and a 60-minute largest gap. SES-012's end record was
  never sent.

### 9.3 Decisions

- **H1. Gateway status sits inside Readiness, not on Health or a new tab.** The owner
  asked for it there, and Readiness (8.10 / 8.35) is where "is the data arriving well
  enough to conclude anything" belongs. Health keeps per-source status.
- **H2. Gateway versus device.** The panel separates gateway faults from device or charger
  faults. Kobo's and Depot's gaps are device-side, so their calls to action point at the
  device actions, not at the gateway.
- **H3. Compact sources list.** Status pills replaced a table to keep the Readiness book
  page under the limit; nothing is collapsed or hidden.

### 9.4 Checks added

- A gateway panel with all field groups on each Readiness page, a working strip, valid
  links, and no simulator, envelope or run wording.
- The Readiness subtab is active on those pages.
- Gateway figures follow the 30-day window (30 day cells, outages shown).
- The F-104 confidence popover links to gateway status.

New preview: `previews/gateway-status.png`; Readiness pages were added to the preview list.

---

## 10. Round 6 (owner follow-up 6, 2026-10-06: assets and warranty, intelligence, work, settings)

Produced by Claude as Architect under the scoped exception, extended to the global
Assets, Findings, Evidence, Work and limited Settings areas. Owner text and outline are
verbatim under "Owner follow-up 6". Mock-up files only; nothing committed.

Result: 105 screens and 907 browser checks pass with 0 runtime errors. The PDF book is
still 41 pages at 1658 of 1728 px; all new screens are routed subtabs kept out of the
book.

### 10.1 Comparison with v6.9 (before this round) and what was applied

| v6.9 | Covered before | Missing | Weaker | Contradicted | Applied now |
|---|---|---|---|---|---|
| 8.3 Assets index | Inventory table; condition and evidence as separate columns | Open-findings column; filter chips (All, Needs attention, Work due, Evidence limited); KPI strip | 5 rows, no warranty | — | 7 assets with Condition, Evidence, Open findings, Open work and Warranty columns; five in-place filters (adds "Warranty attention"); KPI strip; "+ Register asset" |
| 8.27 Battery asset tabs | Health tab (reserve, power, capacity unverified, no remaining-life claim) | Performance, Configuration, Work, Evidence, Warranty tabs | Breadcrumb used the site, not BAT-001 | — | Tab row Health \| Performance \| Configuration \| Work \| Evidence \| Warranty. Breadcrumb is Assets › BAT-001 › tab · site |
| Warranty (v6.9: P1, deferred, no content contract) | — | Everything | — | — | **Filled in as an enhancement (decision J1):** BAT-001 Warranty tab and an Assets › Warranty & vendors view |
| 8.34 Maintenance work detail | WR-019 Verification (activity versus outcome) | Managed-object header; maintenance record; lifecycle; tabs | — | — | Tabs Overview \| Maintenance record \| Verification \| History; five-field header; lifecycle strip; the record lists notes, parts, time on site, return-to-service reading and the missing witness test, with basis (Measured / Operator record) |
| Asset registration / edit (not in v6.9) | — | — | — | — | Assets › Register asset: ATS-CR-01 draft with 6 steps and validation (make and model, 2 unmapped points, warranty, witness record all amber). BAT-001 edit (v2 validated, temperature point and commissioning capacity test outstanding) |
| 8.4 Findings index | Global table with chips | Lenses as the subtab row; workflow state as a filter; KPI strip; Lens column | Columns not aligned with site lists | Lenses as chips mixed with navigation | Subtab row All findings \| Cost \| Risks \| Opportunities. State chips filter in place. KPI strip (open, high priority, low confidence, awaiting verification). Rows come from the same registry as the site Findings lists (6 findings) |
| 8.32 Finding detail Overview | Claim, consequence, limits, next step | Priority / state / claim / lens chip row; "Where to look next" | — | — | Chip row Priority · Confidence (cause chip) · State · Claim · Lens; "Where to look next" panel (Analysis, Evidence, Alternatives, ACT-048) |
| 8.37 Claim evidence drawer | Observations, provenance, limits, technical record | Evidence chain with basis vocabulary; configuration at the time; approvals and overrides | — | — | Evidence chain table (Measured / Operator record / Observed absence / Unknown) for all three sites; mini-grid "Settings at the time" and "Approvals or overrides: None recorded" |
| 8.8 Portfolio evidence | Capability matrix | Recurring evidence gaps | — | — | "Recurring evidence gaps" table (device reporting, unmapped points, manual records not taken, tests never done), each with a call to action. Still no single readiness % (D3) |
| 8.5 / 8.38 Actions | Index; ACT-048 verification | KPI strip; Source column; ACT-049; managed header on Verification | — | — | KPI strip (due shows "Not set"); four actions with Source and Success criterion; lifecycle line; five-field header on ACT-048 Verification |
| 8.6 / 8.33 Incidents | INC-203 timeline | Severity, owner, findings/work columns; state vocabulary; managed header with closure criterion | — | — | Index per 8.6 with KPI strip and state vocabulary; INC-203 header (owner, SLA, state, source, closure criterion) |
| 8.7 Maintenance | One corrective row | Preventive work; KPI strip; repeat findings | — | — | Maintenance › Corrective \| Preventive · scheduled. Corrective: WR-019, WR-021 with verification and warranty columns. Preventive: 5 plan items (calendar or running hours), 2 overdue, with "What it proves" |
| Operational records (owner outline) | Operator records mentioned only inside the chain | Whole area | — | — | New Work › Operational records: 8 records (logs, manual readings, shift notes, site visits), type filter, "Feeds" links into evidence, 2 requested-not-done gaps, a manual-reading form |
| Settings · 3.10 (owner outline) | — | Whole area | — | — | New Admin › Settings: Operational policies (7 versioned policies; verification-window default editable as v4) \| Tenant configuration (organisation, currency, time zone, units, 5 users and roles, feature switches including the simulation workspace gate per 3.10) |

### 10.2 Asset health and warranty economics (owner point A)

- **Captured at registration:** vendor, who sourced it, purchase date and cost, term (10
  years, 6,000 cycles or 600 MWh), coverage limits (charge floor 10%, cells ≤ 45°C, rate ≤
  0.5C, 70% capacity guarantee), claim contact and documents.
- **Health and usage against the terms:**
  - The five reserve breaches (lowest 22%) sit *inside* the 10% warranty floor, so cover
    holds.
  - Temperature is not measured, so compliance "Cannot show" and cover is **at risk**
    ($64,000).
  - Capacity was never measured, so no claim is possible today. PM-0447 (capacity test,
    1 Nov) creates the baseline.
  - The claim-evidence confidence chip (Low) reuses the follow-up 4 pattern: coverage gap →
    "Add a battery temperature sensor"; configuration gap → "Add commissioning capacity
    test to the registration".
- **Claimable finding:** CHG-002 / F-130. Claimable only if diagnostics (ACT-061) confirm a
  connector defect. A repair-or-claim table compares $0 parts plus up to 10 days out of
  service against $850 and 2 days. It flags that an unauthorised repair voids cover, and
  values one interrupted session at ≈ $3.49 (the scenario from F-130).
- **Expired cover:** GEN-CR-01 expired Mar 2026, so the WR-019 repair is at own cost.
- **Vendor performance** across assets: faults, cover and claims.
- **Missing record = configuration gap:** INV-001 and ATS-CR-01, each with a call to action.
- **Financials:** Kobo's "Asset exposure" card reads the warranty record. EV Financials
  gains a third line, "Connector 2 fault: $0 parts if claimed, $850 if repaired locally".

### 10.3 Decisions (Architect)

- **J1. Warranty is filled in, beyond v6.9's P1 placeholder.** The owner asked for it, and
  health and usage evidence are exactly what decide whether cover holds. Money stays
  purchase cost and stated terms, never a forecast.
- **J2. Asset Overview tab: superseded. The owner overruled this decision in follow-up 7
  ("asset overview tab is nedeed").** Originally Health stayed the asset landing page.
  Now `asset-overview` is the first tab and the landing page: Overview | Health |
  Performance | Configuration | Work | Evidence | Warranty, matching the v6.9 asset tab
  set. It uses the site Overview pattern scaled to one asset:
  - an identity block (type, rating, site, diagram position, vendor, commissioned) with
    the "Simulated site" provenance tag;
  - status Watch with a "Confidence: Low" cause chip (new `batcond`: temperature not
    measured → add a sensor; capacity never measured → PM-0447);
  - five cards (Health, Usage, Open findings, Open work, Warranty), each linking to its
    tab;
  - a "What happened" timeline that follows the window picker: the event hour shows
    74% → 88% charge and the missing 14:50 report; Last 30 days shows the 5 reserve-breach
    days, matching the Health weekly bars;
  - needs attention, money (warranty cover at risk $64,000; part of Kobo's window cost
    exposure), and the next step.
  Landing links now point to Overview: Assets index, Warranty & vendors, and Site Health's
  "Open asset". Health-specific links (Site Overview Battery card, Readiness, Evidence,
  Portfolio asset-life card) still go to Health. BAT-001 is the only asset with detail
  pages, so no other Overview was needed. Checks were added; new preview
  `previews/asset-overview.png`.
- **J3. Work request tabs are Overview \| Maintenance record \| Verification \| History.**
  v6.9's Plan and Evidence tabs are folded in: the plan is the header's success criterion,
  and evidence sits in the record and the verification. "Maintenance record" names v6.9's
  "Execution / work evidence" in plain words.
- **J4. Findings lenses keep Cost alongside Risks and Opportunities.** This matches
  Portfolio and the site lists (D8), although v6.9 lists only Opportunity and Risk.
- **J5. Preventive items carry due dates; actions keep "Not set".** A maintenance plan's
  due date is a plan fact. Action due dates are still not set in this example (the
  Portfolio rule).
- **J6. Operational records are their own Work area.** Records are labelled "Operator
  record" wherever they feed evidence, and a requested record that was never taken stays a
  visible gap.
- **J7. Settings is admin, and limited.** Only the verification-window default is editable;
  the rest is read-only. The 3.10 gate is shown as "Simulation workspace (demo and
  testing)", admin only, with the rule that simulated sites keep their history and
  provenance when it is switched off.
- **J8. One managed-object header** (Owner · Due / SLA · State · Source · Success or
  closure criterion) on ACT-048, INC-203 and WR-019, per v6.9 §4.

### 10.4 Owner weigh-in (each with the Architect's decision)

- **W7. Vendor names:** fictional (Northwind Storage, Kestrel Gensets, Ampere Charge Co,
  Polar Cooling Co). Decision: keep fictional. Real names would imply real terms.
- **W8. PM-0455 overdue before the 6 Oct start failure:** shown as "context for INC-203, not
  a proven cause". Decision: keep it. It is a useful causal lead, and the wording stays
  bounded.
- **W9. Warranty "value":** shown as purchase cost and pro-rata terms, not market or
  residual value. Decision: keep it. A residual-value model would need assumptions not
  in the fixture.
- **W10. The Settings feature-switch label:** "Simulation workspace (demo and testing)".
  Decision: keep it. It is admin-only, and it is the plainest honest name for the 3.10
  gate.

### 10.5 Previews (round 6)

`assets-index.png`, `asset-warranty.png`, `assets-warranty.png`, `asset-register.png`,
`finding-detail.png`, `maintenance-preventive.png`, `wr-record.png`,
`operational-records.png`, `settings-policies.png`, `settings-tenant.png`.

---

## 11. Round 8 (owner follow-up 8, 2026-10-06: site creation by form, template and batch upload)

Produced by Claude as Architect under the scoped exception (extended for follow-up 8).
Owner text: "Creation of site in batch via upload, or from template or through form need
to be added in site setup — let the architect decide whether it should go in the settings
or sites". Mock-up files only; nothing committed.

Result: 110 screens and 962 browser checks pass with 0 runtime errors. The PDF page is
1658 of 1728 px; all new screens are subtabs kept out of the book.

### 11.1 Decision: site creation lives under Sites, not Settings

- **K1. Sites.** The decision and its reasons:
  - v6.9 §8.2 puts "+ Add site" on the Sites index.
  - A site is an operational object, created where it is found, in the same way that
    Register asset sits under Assets.
  - Settings holds what a new site *inherits* (policies, tenant units and time zone),
    not the sites themselves.
  - Sites gains a subtab row: Directory | Add site · form | From template | Batch upload |
    Setup history.
  - The creation pages are estate-level, so they carry the window picker but no site
    selector or site provenance tag.

### 11.2 What was added

| Screen | Content |
|---|---|
| Directory (`sites`) | Unchanged directory, plus an **In setup** panel: Lakeside Mini-grid (draft, by form), Westfield Depot (pending activation, from template) and any batch-imported drafts, each with its next step. "+ Form / From template / Batch upload" buttons. v6.9's "Create simulated site / Clone site into scenario" are not shown to operators; provenance is chosen inside the form |
| Add site · form (`site-create-form`) | Six steps: Identity (name, id, type, location, time zone, data source: field equipment or simulated source as provenance), Configuration, Assets (reusing Register asset, with vendor and warranty), Gateway and points, Policies inherited from Settings (with versions), Review. Validation separates **blocking** checks (all clear) from **gaps expected at creation**: gateway not connected yet, 0 of 14 points mapped, 2 warranty records missing, commissioning not recorded. These are the same categories that Readiness and the confidence chips use. Save draft / Activate (activation gives assessment Unknown, with the gaps listed in Readiness) |
| From template (`site-create-template`) | Four templates: Mini-grid AC-coupled, Mini-grid DC-coupled (new diagram), Hybrid cold room, EV depot. The selected template shows its single line diagram with every source "not connected" and real asset ids removed, a parameters form and the assets it adds. "Create draft from template" or continue in the form |
| Batch upload (`site-batch-upload`) | Download CSV or XLSX template; upload (sites-october.xlsx, 6 rows); **validation preview** per row: 2 ready, 1 warning (battery size defaulted), 3 errors (time zone missing, duplicate id MG-DEMO-01, unknown template with a suggestion). Inline fixes for two rows; "Import N rows · skip M". The result summary shows drafts created and rows skipped (with a download of the skipped rows). Imported drafts then appear under Directory › In setup |
| Setup history (`site-setup-history`) | Audit of create, import and activation events, consistent with existing dates: Depot point list v1 on 15 Sep, GreenHarvest v2 on 28 Sep, Kobo Foundation v4 on 6 Oct. The import adds a row when it is run |

### 11.3 Other decisions

- **K2. Simulated is provenance, chosen in the form's identity step.** A template never
  decides it. There is no "Create simulated site" entry on operator screens; the admin
  feature switch in Settings governs the simulation workspace (3.10).
- **K3. Templates are AssetOps site templates** (type, diagram, assets, point list), not
  the simulation workspace's templates. Their previews show nothing reporting, because
  nothing does yet.
- **K4. Validation never blocks a draft.** Activation needs only the blocking checks. The
  expected creation gaps stay visible and feed Readiness, so a new site is honest
  ("Unknown") from day one.

### 11.4 Owner weigh-in

- **W11. Templates are fixed for now: owner-confirmed (follow-up 9).** The 4 built-in
  templates are shown as "standard templates, available to all organisations"; nothing
  suggests they are edited in Settings today. **Future direction (owner):** template
  settings become tenant-specific, while the shared standard templates are checked into
  source code and available to all tenants.
- **W12. Batch upload creates drafts only: owner-confirmed (follow-up 9).** Every imported
  site passes the same activation review as a form-created site.

### 11.5 Checks and previews

- **Checks added:** the Sites subtab row and the In setup panel; the creation pages carry
  no site selector or site provenance tag; the six form steps and the expected-gap
  validation; template switching redraws a not-connected diagram with no real asset ids;
  batch per-row errors; fixing a row clears its error; import results; imported drafts
  appear in the directory; setup history records the import; mobile containment for the
  three creation screens.
- **Previews:** `site-create-form.png`, `site-create-template.png` (hybrid cold room),
  `site-batch-upload.png` (validation preview state).
