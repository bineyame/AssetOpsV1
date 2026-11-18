# G-02 review packet - V-01a mock-gap pilot

Task: `tasks/G-02-v01a-gap-pilot.md` (Status `in_review`, USER_REVIEW_REQUIRED: true). Branch `task/G-02-v01a-gap-pilot`, diff base `42bd74d` (activation, from main `5625447`). Binding inputs: `.agent/architect-G-01-answers.md` (C5, C7) and `D-2026-10-13-g01-placement-and-orphan-scan-boundary`; G-01 carries C1, C6, C9 (`.ai/MILESTONE_REVIEW_BACKLOG.md`); V-01a round-3 Addendum and the conditional-acceptance rows. Handoff `.agent/G-02-handoff.md`. Questions `.agent/G-02-questions-1.md` (Q1-Q6, fail-closed defaults shipped).

Commits: `402e047` (catalogue, enrollment, UI tags, tests), `2f2be4d` (scan C7/C1 and fixtures), `0efee8c` (handoff and questions), `4db70f0` (evidence tool), and the records commit.

## Outcome delivered

- Each visible missing state on Sites, Site model (`foundation`), Readiness and SLD now has its own `<MissingClaim>` element. Each element carries one gap ID, which is never shown on screen. Visible copy is unchanged except for one deliberate change: the combined gateway line is now three sentences, one per claim (C5).
- `sites`, `foundation`, `readiness` and `sld` are enrolled in `gap_enrolled_screens`. Every non-core open portion on these screens lists its gaps, and the ledger rows list their gaps too.
- The orphan scan now also flags "not tracked yet" and "commissioning confirmation not recorded" (C7). Its result line states which merge-base baseline it compared against, or says the comparison was SKIPPED and why (C1).

## Files materially changed

- `frontend/docs/architecture/v69-dependency-registry-pilot.json`: 20 gaps, portion `gap_ids`, enrollment. `v69-screen-ledger.json`: `gap_ids` on the four rows.
- `frontend/src/ui/gapCatalogue.ts`: the mirror.
- `frontend/src/sites/SitesIndex.tsx`, `StoredFoundationViews.tsx`, `FoundationRevisionPanel.tsx`, `ReadinessOverview.tsx`, `SiteSingleLineDiagram.tsx`: tags. `GATEWAY_NOT_AVAILABLE_YET`, `DIRECTORY_AGGREGATE_ABSENT` and `SLD_NOT_DECLARED_NOTE` are replaced by one constant per claim.
- `tools/checks/missing-claim-scan.mjs`, `test_missing_claim_scan.mjs`, `missing-claim-baseline.json` (15 -> 12).
- Tests: `frontend/src/shell/__tests__/siteFoundationRevision.test.tsx`, `frontend/src/sites/__tests__/sitesIndex.test.tsx`, `frontend/docs/architecture/test_mock_gaps.cjs`.
- `tools/g02-gap-evidence.mjs` (new; CDP evidence at 1440/390).

## Pilot map (one ID per distinct claim)

All gaps are `open`, `target_wave: unplanned`, `allocation: pending owner review`, and `evidence.visual: null`. Each registry entry records its typed boundary (window, subject, source, cannot_mean), owner and review trigger.

| Gap | Portion / element | Kind / source | Placement(s) or reason |
| --- | --- | --- | --- |
| G-sites-operating-view | sites:1.operating-view | contract / absent | `sites.inventory.operating-view` (per-row cell), `.analysis-note` |
| G-sites-attention-counts | sites:1.attention-counts | contract / absent | `sites.inventory.attention-counts` |
| G-sites-setup-progress | sites:2#a | data_source / absent | `sites.inventory.setup-progress` |
| G-foundation-productive-use | foundation:2#b, :2.productive-use | contract / absent | `foundation.identity.productive-use` |
| G-foundation-obligation-policy | foundation:2#b | data_source / absent | unplaced: the Addendum forbids a fictional policy link |
| G-foundation-financial-assumptions | foundation:2.financial-assumptions | contract / undecided | `foundation.identity.financial-assumptions` |
| G-foundation-change-record | foundation:3.change-record | contract / absent | `foundation.controls.change-record` |
| G-foundation-constraint-evidence | foundation:3.constraint-evidence | contract / absent | `foundation.controls.constraint-evidence` |
| G-readiness-commissioning | readiness:1.commissioning | data_source / absent | `readiness.commissioning.{definition,confirmed,needed,declared,next-step}` |
| G-readiness-gateway-registration | readiness:2#a | decision / existing (I-S1-01) | unplaced: renders from a real read; the portion review is owed |
| G-readiness-gateway-contact | readiness:2#b | decision / existing (I-S2-02) | unplaced: unknown/unavailable are runtime states |
| G-readiness-gateway-uptime / -completeness / -signal-strength | readiness:2.* | data_source / absent | `readiness.gateway.uptime`, `.completeness`, `.signal-strength` |
| G-readiness-gateway-firmware (G-01) | readiness:2.firmware | data_source / absent | `readiness.gateway.firmware` |
| G-readiness-source-registration | readiness:3#a | decision / existing (I-S1-01) | unplaced: renders "Registered" |
| G-readiness-source-contact | readiness:3#b | contract / undecided; requires A-S7-health, I-source-health-read/-ui | `readiness.gateway.source-connection`, `.source-connection-registration`, `readiness.sources.arrival` |
| G-readiness-confidence-effect | readiness:4#a | contract / absent | unplaced: role gaps are under readiness:1; no rule |
| G-readiness-evidence-capability | readiness:4#b | contract / absent | unplaced: links to Site Evidence (G-03 copy) |
| G-sld-protection-metering | sld:1.protection-metering | contract / absent | `sld.diagram.protection-metering` |
| G-sld-reporting-status | sld:1.reporting-status | contract / undecided; same S7 nodes | `sld.diagram.reporting-status`, `.readings-status` |

Classified as normal states, not gaps (Q6): "Critical-load priority not configured", "Gateway contact unavailable" / "Contact unknown", "Dispatch not available here", "Not declared" cadence, and the typed unavailable-drawing note.

V-01a carries classified, not fixed:
- C1 (390 Readiness table scroll): measured as an inner scroll container, 324/529. The page does not scroll.
- C2 (readiness sentence versus gateway panel): unchanged.
- C3 (screenshot name clash): G-02 names are checked unique.
- C4 (SLD `aria-controls`): untouched.
- Gateway Site Evidence pointer: kept outside the tagged elements.
- Non-STALE gateway states are still proven only by response substitution. This is recorded in G-readiness-gateway-contact's unplaced reason and trigger.

## Acceptance criteria

1. **Inventory seeded from the merged UI and V-01a records, SLD inspected: met.** See the map above. Every Addendum row is accounted for.
2. **One ID per claim; mock_gaps fields; portion and ledger gap_ids; core preserved: met.** The checker enforces coverage of the enrolled screens. Core paths, `core`, `state`, `technical_requires` and `panel_status: partial` are unchanged.
3. **Signal and firmware separate; typed boundaries; absent producer stays data_source/absent; S1/S2 nodes only where they prove the claim: met.** No Lab value and no mock value is shown.
4. **Typed annotation of every visible placement; omitted content has an unplaced_reason; branches, selection, date, reload; real placement and exact membership; mutation checks: met, with the Q1 deviation.**
   - Vitest checks the exact pair set per gateway branch: CURRENT, UNKNOWN, 503, 404, none and loading.
   - It also checks that date, selection and reload leave the pair set unchanged, and that each element's text is exact.
   - Mutations: unknown and unused IDs (G-01 fixtures, still passing) and untagged new copy, including both new cues.
5. **App/mock comparison per manifest ID at 1440/390; deliberate differences and lineage; panel status unchanged: met.** See Layout evidence.
6. **Carries are inputs, not fixes: met.**

Architect and review carries:
- C5: three elements, three IDs, unique placements.
- C6: firmware in the loading branch is asserted.
- C7: two cues added, the current occurrences audited (both are tagged), mutation fixtures added, generic copy proven out.
- C1: the skip is visible.
- C9: per-element exact-text tests. Proof: an extra sentence inside the uptime element passes the scan but fails 2 G-02 Vitest tests.

## Checks run (actual results)

- `npx vitest run`: 61 files, 1445 passed. This ran after phase b; phase c changed only tools.
- `npx tsc --noEmit`: exit 0. `npm run build`: exit 0 (chunk-size warning only).
- `node frontend/docs/architecture/check_v69_dependency_registry.cjs`: `Registry valid: 212 nodes, 11 linked pilot panels`.
- `python frontend/docs/architecture/check_v69_ledger.py`: `v6.9 ledger valid: 110 screens, 88 distinct models, 258 panels`.
- `node --test`: `test_mock_gaps.cjs` 13 pass; `test_delivery_next_work.cjs` 35 pass; `tools/checks/test_missing_claim_scan.mjs` 17 pass.
- `node tools/checks/missing-claim-scan.mjs`: `passed: 25 tagged placement use(s), 12 baselined legacy occurrence(s); baseline compared with merge-base 56254477fd on main and the seed ceiling 16.`
- `powershell -ExecutionPolicy Bypass -File tools/check-all.ps1 -Python .venv/Scripts/python.exe`: all 9 guards passed (re-run after the records commit; see the final report).
- Real-tree mutations, each reverted with `git checkout`:
  - `readiness:2#a` gap_ids emptied gave `[gap_join]` and `[gap_enrollment] readiness: non-core unmapped portion readiness:2#a has no gap_ids`.
  - The setup-progress const rendered outside MissingClaim gave `[untagged_copy] frontend/src/sites/SitesIndex.tsx:333`, exit 1.
  - With git off PATH, the result line said `merge-base baseline comparison SKIPPED (git merge-base HEAD main failed ...: spawnSync git ENOENT); only the seed ceiling 16 limits growth`.
- The backend pytest suite was not run, as instructed. G-02 changes no backend code.

## Layout evidence

Run by a delegated subagent on private stores `assetops_g02evwalk` / `assetops_g02evempty`, copied read-only from `assetops_s4cases`. Ports were 8898/8899/5398/5399. The command was `node tools/g02-gap-evidence.mjs http://localhost:5398 http://localhost:5399 <dir>`.

**Result: 322/322 claims passed, exit 0.**
- Non-vacuity: `G02_ALTER=readiness.gateway.firmware` gave 304/322 (18 exact-text FAILs, exit 1). A clean rerun gave 322/322.
- The first run gave 318/322 because of a tool bug (it expected a loading-state attribute that does not exist). The tool was fixed, not the app.

What was measured at 1440x1000 and 390x900:
- The exact pair set and exact text on every route. The empty store has 0 tags.
- Gateway branches: stale (stored), plus current, unknown, 503, 404 and loading (response substitutions; these prove only what the UI renders).
- Part `pv-array`, past period `at=2026-09-29T11:57:49Z`, and reload.
- Visibility, including `readiness.sources.arrival` after opening its disclosure.
- No SLD tag inside an `svg`. No visible gap ID. No page horizontal scroll.

Measured facts:
- Inner scroll containers at 390: Readiness table 324/529 (seven tagged cells are reached by that scroll, then pass visibility), Sites table 356/517, controls table 324/395, SLD 322/952.
- All four Foundation control links render.
- 1 Site row, 6 Readiness rows.

Screenshots: 36 unique PNGs in `C:\Users\assef\AppData\Local\AssetOps\evidence\g02` (outside the repo). These are mock `g02-mock-{sites,foundation,readiness,sld}-{1440,390}` and app `g02-app-...` per route, state and viewport.

Cleanup: the servers were stopped by exact PID, both databases were dropped (the `pg_database` listing is empty), and the work folder was removed.

App vs mock (the differences are deliberate; lineage in brackets):
- **sites** [GET /api/sites]:
  - The four analytic columns become one "Not available yet" cell plus a note (operating-view).
  - The KPI tiles become a sentence (attention-counts).
  - The In setup table becomes "Setup progress not tracked yet." (setup-progress).
  - Left out: illustrative sites, the create tabs and the filter chips.
- **foundation** [stored Foundation read]:
  - "Grain mill" productive use becomes "Not declared".
  - The Financials link becomes "not available here".
  - "Review proposed change" and "Constraint evidence" become the change-record and constraint-evidence missing states.
- **readiness** [Foundation read; GET /api/sites/KOBO-001/gateway-health]:
  - The Confirmed column becomes "Not recorded" (commissioning).
  - The 100% / 95% / -87 dBm / firmware 2.4.1 values become four separate missing lines.
  - The per-source Reporting chips become source-contact lines.
  - Left out: the clock/delivery tile, the outage strip and the "Effect on readiness and confidence" panel (confidence-effect and evidence-capability are unplaced).
- **sld** [Foundation topology]:
  - Breakers and kWh meters are covered by protection-metering.
  - The reporting dots, the monitoring row and the legend are covered by reporting-status.
  - The "What it reports" column is not in the parts table; it is recorded as element `sld:2.what-it-reports` on `G-sld-reporting-status` (Fix round 1, F2).

## Known deviations

- Q1 (superseded by Fix round 1): the SLD Site-only slots are now tagged; see "Fix round 1". The earlier justification "`MissingClaim` renders HTML only" held for the SVG slots alone; the table cells, introduction and caption were always taggable.
- Six gaps are unplaced (Q3). Three of them are decision gaps on portions that render real reads.
- `tools/v01a-foundation-evidence.mjs` and `tools/g01-firmware-evidence.mjs` still assert the pre-split gateway copy. They would fail if re-run; `tools/g02-gap-evidence.mjs` supersedes them for these screens.

## Residual risk

- The scan cannot see an extra claim inside a tagged element (C9). Only the exact-text tests catch it, so later G packets need the same per-element text assertions.
- Copy on these screens beyond the two new cues ("not available here", "not assessed") is tagged here but not scanned. New copy of that kind elsewhere would pass untagged (Q2).
- The conditional V-01a visual acceptance is unchanged. No portion, panel or screen moves toward Real.

## User-review focus

- Reviewer:
  - Sample registry gap -> portion `gap_ids` -> ledger -> mirror -> `data-gap-*` joins.
  - Check the C7/C1 scan change and its fixtures (it changes detection behaviour).
  - Check the source-to-claim boundaries of the decision gaps (Q4).
  - Check the 1440/390 pairs.
- Owner: the four visible missing-state treatments, especially the three new gateway lines. See `.agent/G-02-owner-walkthrough.md`. Acceptance stays conditional and makes nothing Real.
- Outside G-02 scope, noted by the evidence run: the top bar's "Open Simulator Lab" and the Sites "Create a site in the Simulator Lab" button may conflict with the client-facing no-simulator-language rule. Both predate G-02.

## Fix round 1 (Architect Q1/Q2 overrulings, review F1/F2, evidence-tool carry)

Commits: `c25b351` (Q1/Q2/F2 code), the evidence-tool commit after it, and the records commit.

- **Q1.** `G-sld-reporting-status` now has seven placements, one per JSX source/slot kind: `sld.diagram.reporting-status`, `sld.diagram.readings-status` (existing), `sld.diagram.bus-slot` (SVG `<text>`, bus), `sld.diagram.node-slot` (SVG `<text>`, every other node), `sld.contents.readings-slot` (parts-table cell, a `MissingClaim` span inside the `<td>` that keeps `data-sld-row-slot`), `sld.contents.caption` ("both are empty in this build, for every component, and neither holds a reading."), `sld.intro.readings-status` (the introduction's "Whether any reading has arrived is not assessed..." sentence; `SITE_SLD_INTRODUCTION` split into scope and readings parts, rendered by one `SiteSldIntroduction`). Pure "configured diagram, never behaviour" sentences, and the panel description "not live power flow, and not reporting status", stay untagged as scope captions. Only the Site branch (`slots === null`) is tagged; the Lab branch renders its own `<text>` and cell unchanged.
- **SVG wrapper.** `MissingClaimSvg` (`frontend/src/ui/MissingClaim.tsx`): `as` is `"text"` or `"tspan"`, same runtime pair check, same `data-gap-*`; the words remain the element's own text, no ARIA is added or removed (text still read). Registry placements, mirror `gapCatalogue.ts` and ledger/registry joins updated; rendered words unchanged.
- **Scan.** Recognises `MissingClaimSvg`; validates `as` is a literal `text`/`tspan` and that `MissingClaim` is not used with SVG tags; uniqueness and known-ID checks apply to both. Real-tree proofs (committed first, reverted by `git checkout`): duplicate placement -> `ui_duplicate_placement` + `unused_placement`; unknown placement -> `ui_unknown_placement`; `as="p"` -> `ui_usage` ("never an HTML element inside SVG"); intro readings sentence rendered untagged -> `untagged_copy` at `SiteSingleLineDiagram.tsx:102`.
- **Q2.** New exact cues: `not available here` (negative lookbehind so "Dispatch not available here" stays, Q6), `reading(s)... not assessed` within one sentence fragment, `not assessed on this diagram`, `no proposed-change record here`, `no linked constraint evidence`. Not matched: bare "not assessed", "not declared", "No ... record here". One untagged-mutation fixture per cue plus an ordinary-states fixture. Fail-before: the new test file against the pre-fix scan fails the cue test and the SVG test (`node --test`: 16 pass, 4 fail); after: 20 pass. No baseline growth (12 legacy occurrences, ceiling 16 unchanged).
- **F1/F2.** Walkthrough line 5 now limited to asserted-absent claims; this packet's SLD justification replaced. `sld:2.what-it-reports` added to the gap's `element_ids`.
- **Tests.** The SLD Vitest test now asserts the eight pairs, SVG elements are `text`/`tspan` in the SVG namespace inside `[data-sld-node]`, HTML elements are in the XHTML namespace, one bus slot and nodes-1 node slots, every parts-table cell reads exactly "Readings not assessed here" with its tag, scope sentence untagged; `MissingClaimSvg` unit test.
- **Evidence (private copy, ports 8898/8899/5398/5399, 1440 and 390).** `tools/g02-gap-evidence.mjs` extended (counts by drawn nodes; claim (f) now requires SVG-tagged elements to be SVG `text`/`tspan` with count = node count, HTML ones not SVG). Result line: **321/322 claims passed**. SLD at 1440: all claims pass, (f) 10 SVG elements for 10 nodes. The one failure: `390 /sld: (c)` for `sld.contents.caption`: the tagged caption sentence is a single line 383px wide whose right edge is at 433px of a 390px viewport after scrolling it into view inside the parts table's inner scroll container. The caption lives in the table, which is wider than the phone viewport, so its tail is reachable only by that inner scroll. It is the pre-existing caption geometry now measured because the sentence is tagged; page scroll is clean. Left unfixed (layout change out of scope); **owner/reviewer decision**: accept, or move the sentence out of the `<caption>`. Servers stopped by exact PID, both databases dropped, work folder removed.
- **Old evidence tools.** Header on `tools/v01a-foundation-evidence.mjs` and `tools/g01-firmware-evidence.mjs` marks them superseded and expected to fail on the current tree.
