# W5-03b E4 (EV Health UI) and E6 (EV Scenarios UI): independent review

Reviewer: fresh Claude reviewer (did not author the slice), 2026-10-24.
Branch `task/W5-03b-ev-health-ui`, head `37aec48b` (builder head `a0ec1890` plus a main merge that touched only register rows). Diff reviewed: `git diff f8293bbe..a0ec1890 -- . ':!.agent'`, plus the `.agent` evidence.
Sources: `.agent/W5-03-build-spec.md` (E4/E6 cards, W5-03b pre-flight, executable registry JSON), `.agent/W5-03b-ui-preflight-rulings.md` 1-16, `.agent/W5-03b-e5-rulings.md`, `.agent/W5-03b-e5-rereview.md` (L1), `.agent/mock-departure-register.md`, `.agent/W5-03b-ui-handoff.md`, `.agent/W5-03b-ui-questions.md`, captures in `.agent/W5-03b-ui-evidence/`, v69 `index.html:181` (metric), `:689-691` (ev-health), `:859-862` (ev-scenarios) and its CSS.

## Verdicts

| Unit | Verdict | High | Medium | Low |
| --- | --- | ---: | ---: | ---: |
| E4 EV Health | **REVISE** | 0 | 2 | 3 |
| E6 EV Scenarios | **REVISE** | 1 | 0 | 2 |
| Shared (both units / evidence / E5 test fix) | n/a | 0 | 0 | 2 |

E4's product logic is correct and well tested. It is held by one unruled phone-layout decision that departs from the mock (E4-M1), plus an inherited header-colour departure (E4-M2) that the Architect should place. E6 is held by one unlabelled visual departure with a one-line CSS fix (E6-H1). Nothing found in either unit is a correctness defect in the data path.

## Checks I ran

| Check | Result |
| --- | --- |
| `npx.cmd tsc --noEmit` (frontend, ops04) | exit 0, clean |
| `npx.cmd vitest run --maxWorkers=1 --minWorkers=1` on `evHealthDepth`, `evScenarios`, `evFoundation`, `siteHealthBoundary`, `evSiteMoneyRoutes` | **5 files, 82 tests passed**, 49.5 s. Config loading worked in this session. React duplicate-key warnings (`Session events source` etc.) and act() warnings come from pre-existing EV Foundation source-reference code, not this diff. |
| Captures | Read all 22 app PNGs' key states and the 4 mock PNGs, and parsed `evidence.json` (blocks, order, caps). |

What I did not run, per the dispatch constraints: Postgres tests, the full vitest suite, `vite build`, captures, `tools/check-all.ps1` / `check-architecture.ps1` / `check-agent-workflow.ps1`, `check_v69_dependency_registry.cjs` and `test_missing_claim_scan.mjs`. For those I rely on the handoff's claims (check-all 11/11 at `3eb68c69`, registry checker valid, scan 24/24, focused Postgres 77 passed, full vitest 2845 passed at `3eb68c69`). Those claims are **unverified by me**. The handoff's final-code revision is `3eb68c69`. `a0ec1890` adds only `.agent` files, and `37aec48b` changes only register rows, so the cited runs apply to the reviewed product code.

## E4: EV Health

### Verified correct

- **Composition (R60 gone).** `SiteHealthFrames.tsx` branches `EV_CHARGING` to `EvHealthDepth` before the S7 fallback. The EV page has no Data sources panel and makes no `/source-health` or `/battery` request. `siteHealthBoundary.test.tsx` asserts both, and the captures show only `Condition and evidence`. `SiteHealth.tsx`, `panelStructure.ts` and `v69-panel-contracts.json` are untouched.
- **Four-tuple validation.** `EV_HEALTH_TUPLES` (`evDepthClient.ts:328-333`) matches the backend `CONNECTOR_FAULT`, `CONNECTOR_UNKNOWN`, `SITE_METER` and `METER_UNKNOWN` (`analytics/ev_depth.py:21-28`) character for character, including `limitation: null` for `SITE_METER`. Every row is checked as a 5-tuple, and any other tuple makes the read malformed (unavailable state). Five negative mutations are tested.
- **Cards and rows.** Cards are one per `CONNECTOR` in DTO order using `label`, then the battery. The `Needs attention` count is `evidence_ids.length`. Battery uses the DTO `limitation`. Table order is fault, then `SITE_METER`, then other connectors, and a `kind:UNKNOWN` meter is omitted (R97). The fault row carries `Session {id}` and `Open Sessions →`. A Sessions link appears only when the returned window has a pair. The bare route calls `getHealth` with a null window. All of these are tested.
- **Notices.** R15 sits immediately before `.v69-cards` and R16 immediately after the sole panel, in all four non-CURRENT states (test plus capture `order`). `expectV69Panels` and `expectPlantedPanelRejected` run on CURRENT only (ruling 4).
- **Foundation source links and guard.** `evSourcesHref` keeps `from,to` only when both are valid UTC instants in order, keeps `known_at` only when it is valid, drops `gateway`, and appends `#ev-site-sources-heading`. That fragment exists at `EvSiteViews.tsx:914`. Six address variants are tested in `evFoundation.test.tsx`. The `evEvidenceHref` prop route (Q7) leaves `tools/checks/site-substrate.ps1` unchanged, so the substrate still imports no shell code. The guard is not loosened.
- **Missing-claim scan.** Only the `Health > Data sources (...)` clause is removed. The Financials, Assumptions and attention-row reasons stay, and those two unavailable entries remain asserted in `evFoundation.test.tsx`.
- **settled.ts.** The two sentences added (`the site's charger condition read`, `the site's EV scenarios`) match `HEALTH_LOADING` and `EV_SCENARIOS_LOADING` exactly. Nothing else changed.
- **Caps.** Measured 324/409 panel (cap 410/540), 135/307 cards (cap 200/380) and 1000/1150 page, up to 1195 with R15 (cap 1200/1550). No document overflow.

### Findings

**E4-M1 (Medium; implementer decision not covered by a ruling; visible mock departure at 390).** `frontend/src/sites/evHealthDepth.css:19-26` sets `min-width: 150px` on the row header and `170px` on each `td` at ≤640 px. This forces the `Condition and evidence` table wider than the 360 px panel, so at 390 `Next evidence` is off-screen and can only be reached by scrolling the table sideways (see `ev-health-fault-390-app.png` and `-pending-390-app.png`). The v69 mock at 390 (`ev-health-390-mock.png`) shows all three columns. The spec's rendering-limits paragraph *permits* in-panel table scrolling with a sticky first column, but nothing requires this one. The min-widths are the builder's choice ("instead of squeezing each ID into a 70px column"), with no register row and no MOCK DEVIATION label. The capture evidence did not surface it either, because the `tableScrolls` metric is vacuous (S-L1). **Why it matters:** a third of the mock's content is hidden by default on phone, and nobody signed that off. **Fix:** either remove the min-widths so the table fits like the mock (IDs already break per character, and `.ev-health-ref` is block-level and small), then recapture at 390, or have the Architect register and label the scroll as a departure. Routed to the Architect below.

**E4-M2 (Medium; inherited primitive, visible on this screen).** `frontend/src/ui/primitives.css:5406-5415` (W5-03a E2 `stickyFirstColumn`) gives every first-column cell `background: var(--surface-raised)`, including `thead th:first-child`. As a result the `ASSET` header cell renders white, while `SUPPORTED ASSESSMENT` and `NEXT EVIDENCE` render the mock's header grey `#f8fafd`. This is visible in every E4 capture at both widths. The mock header row is uniformly grey. E4 did not author the rule, but E4 opted into it (`EvHealthDepth.tsx:150`), so it is a new unlabelled departure on `ev-health`. **Fix:** give the sticky header cell the table-head background, for example `.data-table__scroll--sticky .data-table thead th:first-child { background: <thead background>; }`. That rule is in an E2-owned shared file, so the Architect must assign the owner. Availability and Energy have the same artifact.

**E4-L1 (Low; registry JSON drifts from the executable spec, and the handoff misstates the reason).** `frontend/docs/architecture/v69-dependency-registry-pilot.json:293`: `I-W5-ev-health-ui.requires` is `["A-ev-site-projections","I-W5-ev-depth-read"]`, but the spec's executable E4 node (`W5-03-build-spec.md` "E4 — registry nodes") is `["A-ev-site-projections"]`. At `:481` the `(ev-health,1)` reason is the builder's own sentence, and handoff judgment call 10 says "the spec did not give" one. The spec does give one: `"Selected faults warrant investigation but do not diagnose charger condition."` (E4 panel rows). Both nodes' `acceptance_target` also keeps "preserved gateway panel where applicable", copied verbatim from the spec, which no longer applies to Health after R60. The builder's text is not worse, but "the executable registry JSON governs" (P-E4-11). **Fix:** use the spec's `requires` and reason, or ask the Architect to amend the spec. The gateway-panel wording is an Architect item.

**E4-L2 (Low; tone treatment).** The mock's gray connector card (`metric(...,'gray',...)`) has a gray top border and a *dark* `Unknown` value: the mock CSS has no `.assessment.gray` value colour. The app uses `tone="muted"` (`EvHealthDepth.tsx:129`), and the shared rule `.v69-metric--assessment.v69-metric--muted .v69-metric__value` (`primitives.css:5042`) turns the value text grey. Ruling 5 says "gray `Unknown`", and R57 says "same positions and tones", so the intent is arguably the mock's gray *tone*, not grey text. The battery's grey text is explicitly ruled (ruling 6). Minor. Architect item.

**E4-L3 (Low; test strength).** `evHealthDepth.test.tsx:239-249` builds its fixtures from the exported `EV_HEALTH_TUPLES`, so a future drift between that table and `ev_depth.py` would not fail any test. I confirmed by hand that they match today. A Python-to-JS parity assertion (or a fixture JSON shared with `test_w503_ev_depth_postgres.py`) would pin it. This is a preference rather than an acceptance gap.

## E6: EV Scenarios

### Verified correct

- **Client against E5 as built.** The top-level, window, selection, item, assumption and basis key sets equal `service.py:282-293` and `rules.BASIS_KEYS`. The window clocks and `assessment_revision_id` are nullable (ruling 11). Basis `from/to/cutoff` are required strings, matching `check_basis`. The code pattern matches `scenario_code`'s `ESCN-%06d`. Provenance requires a non-array object with a string `classification`, and extra fields are kept (ruling 13). `selection.source_provenance` is never null on the server (`dual_blocks` fallback). The client sends no `limit` or `cursor` (tested), and `next_cursor` adds the R98 line inside the panel with no pager (tested with 50 rows).
- **scenario_at carry.** `scenario_at` is parsed separately from the URL (`evSiteRoutes.tsx`) and sent only by the Scenarios read and the Scenarios subtab href. Overview and Assumptions use `sel(routes.x, window)` and drop it. The exact hrefs for all three subtabs are tested (`evScenarios.test.tsx:143-148`). The `EvSiteClient` read is skipped on the Scenarios view (`evSiteRead` not called).
- **Page literals.** h1 is the Site name. The local `DESCRIPTION.scenarios` is used without editing `V69Layout.tsx`. The panel title and meta, the exact empty title and paragraph, the blue notice copy, the pending literal and the refusal heading all match. Valid no-selection renders the empty block after the R15 UNKNOWN sentence and does not refuse. The historical earlier-`known_at` vector shows the `Historical` badge plus R15 (ruling 16).
- **Guards and fixtures.** `$expectedTabs` loses exactly one `Scenarios`. The live assertion requires `data-ev-subtab="scenarios"` and `<EvScenarios` in `EvSiteViews.tsx`. All three rail mutations (subtab dropped, page branch dropped, unavailable entry restored) match real lines (`Set-ModuleLines` throws on no match, and line 405 is `{financial ? (`), so none is vacuous. `evSiteMoneyRoutes.test.tsx` replaces all four unavailable assertions with live href and zero-slot checks.
- **Registry.** `I-W5-ev-scenario-read/-ui` and the `(ev-scenarios,1)` row match the spec's executable JSON. The ledger `registry_dependencies` is set and no other ledger field is promoted (ruling 9). No observed-outcome node exists.

### Findings

**E6-H1 (High; unlabelled mock departure).** The blue closing notice stacks its info icon on its own line above the text at both widths (`ev-scenarios-*-1440-app.png`, `-390-app.png`). In the mock (`.notice{display:flex;gap:10px;align-items:flex-start}`), the icon sits inline to the left of the sentence. The cause is that `EvScenarios.tsx:289` tags the notice `data-ev-scenarios-closing-notice`, but the only flex rule is keyed to cold's attribute: `coldScenarios.css:106-107` `.v69-notice[data-scenarios-closing-notice]`. The measured notice is 66/102 px against the mock's 42/78. It is inside the 90/135 cap, but caps do not excuse a layout mismatch. No register row covers this. **Fix:** in `evScenarios.css`, add `.v69-notice[data-ev-scenarios-closing-notice] { display: flex; gap: 10px; align-items: flex-start; }` and `.v69-notice[data-ev-scenarios-closing-notice] p { margin: 0; }`. Do not edit `coldScenarios.css`, per P-E6-6. Then recapture the five Scenarios states at 1440 and 390.

**E6-L1 (Low; inherited cold phone rules, and the evidence wording hides it).** Because the EV disclosure carries `cold-scenarios-basis` and the panel carries `cold-scenarios-panel`, `coldScenarios.css:110` (cold Q-C5c-2) applies at ≤640 px. It sets the basis scroller to **220 px** and the table to `min-width: 820px`. The E6 card specifies a 360 px internal scroller at 390. 220 is within that cap, so this is not a violation, but it is a cold-specific ruling applied to EV by accident. The handoff reports "Expanded basis scroller: 360 / ≤360", while `evidence.json` records `basis: 220` at 390. **Fix:** either accept 220 explicitly (Architect) or override it with `max-height: 360px` in `evScenarios.css`, and correct the handoff line.

**E6-L2 (Low; vacuous assertion).** `evScenarios.test.tsx:316`: `expect(line.previousElementSibling?.querySelector("table") ?? line.previousElementSibling).not.toBeNull()` passes whenever the R98 line has *any* previous sibling, so it does not prove that the line is "immediately below the DataTable". **Fix:** assert `line.previousElementSibling` matches `.data-table__scroll` (or contains `table.data-table`) without the `??` fallback.

## Shared

**S-L1 (Low; evidence non-vacuity).** `.agent/W5-03b-ui-evidence/capture.mjs:104` measures `tableScrolls` with `.data-table-scroll, .table-scroll, [data-table-scroll]`. `DataTable` renders `.data-table__scroll` (`DataTable.tsx:58`), so the selector never matches and every pair reports `tableScrolls: []`. This is how E4-M1 went unreported. The `evidence.json` header is also `"revision": "wip"`, and the unexpanded captures predate `a697415e`/`3eb68c69`, which the handoff discloses. **Fix:** use `.data-table__scroll`, report the overflowing tables, and stamp the commit SHA when the post-fix recapture runs.

**S-L2 (Low; E5 test-Low fix incomplete, and the handoff overstates it).** `backend/tests/test_w503_ev_scenarios_postgres.py:630-633` still has the identical `limit=0` `EV_LIMIT_INVALID` assertion twice. The re-review L1 named it (then at `:645-648`), and handoff commit `9c9b67a4` says it was removed. The diff contains no `limit` line. The other L1 items are genuinely fixed: the duplicate `"accepted"` key, the A6 block and the A3 loop plus 404 each now appear once, and every assertion was kept. The new Foundation spies are real. (c) asserts that the fallback resolved a non-null Foundation that is not one of the cited strangers, and (d) asserts that it resolved the selected Foundation, using string-to-string comparison because `_ev_plain` lowercases. The currency correction now asserts the full ruled message. **Nothing is weakened.** **Fix:** delete one of the two `limit=0` assertions.

## Implementer decisions not covered by a ruling or by the 7 open points

1. 390 min-widths that force table scroll on Health (E4-M1).
2. Opting Health into `stickyFirstColumn`, which brings the white header cell (E4-M2).
3. Registry `requires` and the reason text replacing the spec's executable JSON (E4-L1).
4. Reusing cold Scenarios CSS classes, which brought the 220 px phone scroller and the 820 px table but not the closing-notice flex rule (E6-H1, E6-L1). Judgment call 11 records the reuse, not these effects.
5. Basis `Window` shown as `{from} – {to}` in one source-reference span. This is consistent with the card and is not a finding.

## Items for the Architect

The builder's 7 open points (`.agent/W5-03b-ui-questions.md`: fault fixture, the `evScenarioList` prop, the `Sessions →` label, plurals, the session-cell column, the Health subtitle, the `evEvidenceHref` route) are with the Architect and are not repeated here. I found nothing that contradicts the builder's account of Q1, Q2 or Q7: the tuple data, the prop collision and the substrate guard each check out.

1. **E4-M1:** either keep the phone Health table scroll and register it (D2, with a MOCK DEVIATION label in `evHealthDepth.css`), or rule that the min-widths be removed so all three columns are visible as in the mock.
2. **E4-M2:** assign the owner of the sticky-header background fix in `primitives.css` (an E2 primitive, also visible on Availability and Energy).
3. **E4-L1:** confirm the spec's `(ev-health,1)` reason and the `I-W5-ev-health-ui.requires`, or amend the spec. Also retire "preserved gateway panel where applicable" from the E4 and E6 node `acceptance_target` text, since R60 withdrew that panel.
4. **E4-L2:** say whether `gray` for an `UNKNOWN` connector card means the mock's gray tone (dark value) or grey value text.
5. **E6-L1:** accept the inherited 220 px phone basis scroller or require 360 px.

## Residual risk the packet does not name

- The `EV_HEALTH_TUPLES` and backend wording are pinned only by hand-checking (E4-L3). Any server copy change turns EV Health into the unavailable state, and no frontend test fails.
- The capture metrics `overflowingCells`, `ellipsized` and `tableScrolls` cannot detect hidden table columns. Until S-L1 is fixed, a "0 overflow" capture line does not mean all content is visible at 390.
- The guard, registry-checker, scan, Postgres and full-suite results are the implementer's, at `3eb68c69`. I did not rerun them.
