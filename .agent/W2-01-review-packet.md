# W2-01 review packet - cold Foundation, readiness and configured topology

Task: `tasks/W2-01-cold-foundation.md` (two phases). Branch `task/W2-01-cold-foundation`, base main `8e0af014`. Design `.agent/W2-technical-design-cold.md` section 3 A-I (`D-2026-10-17-w2-01-answers`), panel map section 6; layout contract `D-2026-10-17-mockup-layout-spec`. Phase-1 handoff `.agent/W2-01-phase-1-handoff.md`. USER_REVIEW_REQUIRED: true (independent slice review, then the owner's later W2 walkthrough). Reviewer diff: `git diff 8e0af014..HEAD -- ':!.agent'`.

## Outcome delivered

- Phase 1 (backend): persisted `COLDCHAIN` configuration through the existing Foundation/binding revision path; `0021_w2_cold_config` no-op anchor; code-owned cold vocabulary, 13 typed properties, immutable `cold-roles-1`; cold Foundation validator on import and every revision; `GET /api/sites/{code}/cold/foundation?at=`; COLD-001 (complete) and COLD-002 (no chamber probe) fixtures; W2-00 review Low 2 folded (role check on the closed binding table).
- Phase 2 (frontend): the existing `/sites/:id/foundation`, `/foundation/readiness`, `/foundation/sld` routes render `cold-foundation`, `cold-readiness`, `cold-sld` for a COLDCHAIN Site (type from the Site record, so a refused Foundation read still lands on the cold views); MINIGRID unchanged. Exact v69 panel set/order/titles/grid: Foundation 2 (equal pair), Readiness 4 (gateway panel nests Connected sources and Effect), SLD 2. In-panel gaps per the panel map; `Configured`/`Needs a source` labels; exact IDs only in closed `details.tech`.

## Files materially changed (phase 2)

- `frontend/src/sites/ColdFoundationViews.tsx` (new): frame, cold strip, three views, refusal skeletons.
- `frontend/src/sites/coldFoundationClient.ts` (new): typed read with `loaded|refused|unavailable`.
- `frontend/src/sites/SiteSingleLineDiagram.tsx`: `ColdTopologyDiagram` (layered configured drawing; SVG must live in a diagram module per `shell-overflow.ps1`). `frontend/src/sites/w2-cold-foundation.css` (new).
- `frontend/src/shell/SiteFoundationFrame.tsx` (cold branch via `useSiteRecord`), `frontend/src/App.tsx` (`coldFoundation` client prop).
- `frontend/src/test/v69PanelTitles.ts` (`cold-readiness:2`, `cold-sld:1`), `frontend/src/test/settled.ts` (cold loading sentence), `frontend/src/ui/V69Layout.tsx` (three cold descriptions), `frontend/src/sites/siteViewModel.ts` (export `SOURCE_MODE_LABELS`).
- Tests: `frontend/src/sites/__tests__/coldFoundation.test.tsx` (19 tests).
- Phase-1 files: see the handoff "What landed".

## Acceptance criteria

| Criterion | Status |
| --- | --- |
| Phase 1: complete/missing-probe persist and reload; old/current selection; refusals (low>=high, wrong unit, duplicate probe-room link, cycles/duplicate edges, stale/overlapping binding, undeclared transfer, wrong tenant/Site); messages; 0020->0021->0020 | Met in phase 1 (`test_w201_cold_vocabulary.py` 28, `test_w201_cold_foundation_postgres.py` 16); full suite below |
| Read route 401/403/404/422/503 scoped to tenant/Site | Met (phase 1 tests) |
| Three routes render cold views for COLDCHAIN, MINIGRID unchanged | Met: structure tests + "MINIGRID-typed Site never reaches the cold views"; existing Foundation suite unchanged and green |
| Exact panel count/order/title/grid/prominence; approved dynamic titles | Met: `expectV69Panels` per route in stocked (COLD-001), missing-probe/no-contact (COLD-002), no-version (refused 404) and unreadable states, 12 cases; planted failure proven (leading panel + renamed SLD panel 2: 6 tests failed; reverted with `git checkout --` after commit `ebbeb269`) |
| In-panel gaps: undeclared equipment, per-source contact, confidence, part function, live state | Met: "Not declared", "Source contact unavailable", "Confidence is not assessed", "Function description not recorded", "Live state is unknown", "Undeclared in this version: ..." asserted inside their panels |
| Configured / Needs a source, never Mapped / Not mapped | Met (test asserts no `mapped` word on all three routes) |
| Exact IDs in contextual detail, plain default copy | Met: revision, asset, source, node/edge IDs only in closed `details.tech`; W1 vocabulary scan clean on the three routes |
| Reload / old-current selection | Met: `?at=` drives the read; "Show the version in effect now" re-reads with `at=null`; strip period selector from the versions read |
| Side-by-side 1440/390 captures, all routes | Met: `.agent/W2-01-evidence/` |
| Full backend suite, zero failed/skipped | NOT MET: run 2 stopped at the cap (54%); see Checks |

## Checks run

- Focused: `npx vitest run src/sites/__tests__/coldFoundation.test.tsx` 19 passed; adjacent `src/sites/__tests__` 742 passed; `siteFoundationRevision` + `src/test` + `src/ui` 190 passed.
- Typecheck `tsc --noEmit`: clean. Full `npm.cmd test` at `e5162465`: 77 files, 1976 passed. Production build `npm.cmd run build`: built (chunk-size warning only).
- `tools/check-all.ps1` at `e5162465`: 10/10 guards pass (first run failed shell-overflow on an SVG outside diagram modules; fixed by moving the drawing into `SiteSingleLineDiagram.tsx`, guard unchanged).
- Full backend suite: NOT COMPLETE. Command (TESTING.md normal): `.venv\Scripts\python.exe -m pytest backend/tests -n 2 --dist loadfile --no-loadscope-reorder -q --durations=30 --junitxml=.pytest-junit.xml`, `ASSETOPS_TEST_DATABASE_URL=.../assetops_w201full_test`, keep-awake running, `var/sites` copied from the main checkout, code revision `d93e3721` (= `e5162465` code). Run 1: base database not created first, so the 418 DB-module cases errored on connect (JUnit cases=2651, skipped=0, failed=418, all `database "assetops_w201full_test" does not exist`); the other 2233 passed, 11.4 min. Run 2 (base created): stopped at the 20-min cap (2x the documented 8-10 min) at 54% progress, still making progress (an `ingestion_disposition` insert active on gw0), no standby events 506/507 in the window. No JUnit for run 2. Run databases dropped and `var/sites` removed. The full backend suite is still owed on the final revision (a serial run, expected 30-45 min with a 90-min cap, or `-n 2` on a quieter machine). Phase-1 focused/adjacent backend runs are in the handoff (781 + 13 passed after the W2-00 fix; phase 2 changed no backend file).

## Layout evidence

`node tools/w1-fidelity-evidence.mjs .agent/W2-01-evidence ...` at `e5162465` (`W1_REVISION`), dev API on a private DB seeded with the phase-1 CLI (`import_kobo` + `convert_kobo_bindings` for COLD-001/COLD-002; confirmed working), web on 5475. Nine pairs x 1440/390: `cold-foundation|cold-readiness|cold-sld` x `stocked` (COLD-001), `missing-probe` (COLD-002, contact NEVER), `no-version` (COLD-001 `?at=2026-09-01T00:00:00Z`). 108/108 claims (app rendered, mock rendered, same panel count, no horizontal page overflow). Capture-log fields (app URL, mock hash, case, viewport, revision, image paths) are in `evidence.json`; pairs in `index.html`. The mock is the illustrative GreenHarvest site; structure and gap treatment are compared, not values.

## Known deviations

1. Phase 1 (from the handoff): extra response fields `bindings[].cadence_seconds` + `publication_mode`, `contact.limitations`; `contact.state=null` when no health store is configured (superseded in round 2: now `NEVER`, see below); topology node/edge and message object shapes chosen (design unspecified); invented copy `ROLE_UNBOUND` "Bind the <role label>" and `ROOM_MISSING` "Declare a cold room"; event outcome allowlists taken from the shared v4 kind-to-outcome table; no v4 metadata persisted on cold binding rows (W2-02 must derive/persist); COLDCHAIN edge media/endpoint pairs restricted to the design's pairs; `configuration_gaps` still `SITE_TYPE_UNSUPPORTED` for COLDCHAIN, so the gateway acquisition snapshot download refuses cold Sites (W2-02); contact uses current gateway facts, not as of `at`; added `FoundationService.publish_topology` (tests/fixtures only).
2. Gateway title identity: the store has no gateway display name, so `cold-readiness:2` uses `gateway_external_id` from `/gateway-health` (fallback "No gateway selected"); this is a current read, not as of `at`.
3. `cold-sld:1` is the Site name alone: the Foundation declares no topology type.
4. Site name comes from the current Site record, not the selected revision (no name field in the cold read).
5. Readiness table areas (Site definition, chamber probe, compressor, grid, backup generator and bus, transfer switch, door/loading log, manual temperature log (own row since the fix round), ambient) group `cold-roles-1` roles; grouping and the "(optional)" marking are presentation choices, not specified. Mock has 4 illustrative rows; the app shows 9, so the table is taller than the mock.
6. Foundation panel 2 row "Door and loading observations" replaces the mock's "Loading observations": the capture tool's readiness check treats any "Loading" text as a page still loading.
7. (Superseded by the fix round, H1.) The drawing is now the bus-bar SLD, scaled to fit at every width. Placement is by declared node role: supplies left, switch, vertical bar, cooling chain right. A part with no declared connection (the ambient probe) sits below the chain with no line. The mock's circuit breakers are not drawn: no protection is declared (G-sld-protection-metering).
8. Gateway metric cards Availability/Data completeness/Clock show "Not available"/"Unknown" with a plain note; no MissingClaim placement was added for these cold cards (no catalogued gap ID exists for cold; the missing-claim scan passes).

## Residual risk

- Prominence: the readiness table has 9 rows against the mock's 4. That makes panel 1 about 2.1x the mock at 1440 and 1.5x at 390, although the page as a whole is within budget.
- The generic Foundation read still answers for cold Sites (with `SITE_TYPE_UNSUPPORTED` in its gaps); only its versions list is used by the cold views.
- Contact and gateway identity are current facts on historical periods; the panel says so.

## User-review focus

Walk the three routes for COLD-001 and COLD-002 side by side with `#/cold-foundation`, `#/cold-readiness`, `#/cold-sld` (`.agent/W2-01-evidence/index.html`): top fold, panel widths/heights, the missing-probe and never-contacted wording, and that nothing reads as a temperature, cooling or backup condition.

## Fix round 1 (review `.agent/W2-01-review.md` RETURN)

Commits `79b07ec6`, `b3885275`, `e52d035e`. Frontend only. No backend, registry or guard file is changed: the net diff of `frontend/docs` and `frontend/src/ui/gapCatalogue.ts` against `a4e4cb10` is empty.

| Finding | Fix |
| --- | --- |
| H1 `cold-sld` drawing | `ColdTopologyDiagram` (`SiteSingleLineDiagram.tsx`) is redrawn in the mini-grid bus-bar idiom. It uses the existing `ComponentIconShape` icons, plus three new cold shapes (`TEMPERATURE_PROBE`, `COMPRESSOR`, `TRANSFER_SWITCH`) in `componentIcons.tsx`; the mini-grid archetype table is unchanged. It reuses `wrapName`/`NAME_LINE_BUDGET`/`NAME_LINES`, so names wrap and there is no ellipsis, and the `.sld-node__bar` vertical bus. Grid meter and generator feed the transfer switch, the switch feeds the bar, and the compressor leaves the bar on the right with a dashed cooling link to the room and a dotted link to the probe. A "Monitoring" strip has one box per configured source (`bindings`). Each box carries a hollow dashed marker, titled "Reporting not assessed here", and the legend says so; no reporting dot appears anywhere. The SVG scales to fit at every width (no inner scroller). Tests: bar, icons, wrapped names, no "…", strip count and markers, and a lane/row layout unit test. |
| M2 parts table and 390 density | The per-row "(configured) · Function description not recorded" is removed. `FUNCTION_UNKNOWN` is said once, in the footnote, and the test asserts exactly once. Readiness: the Declared detail sits under the chip as one short line, and a required gap already explained under "What is needed" is not repeated. At 640 px or narrower, cells are compact, the Area column gets a minimum width, the Confirmed and Next step cells do not wrap, and source chips are smaller. Repeated "not a live view" / "reporting unknown" sentences were dropped from the SLD panel; the page footnote keeps them. |
| Low 3 contradiction | "Manual temperature log" has its own row ("Needs a source" / "Optional"). A Configured row with an unconfigured optional reading says "X (optional) not configured", never "No source". The test asserts no Configured row contains "No source". |
| Low 5 availability timeline | An empty grey track sits under the gateway cards, labelled "No history to draw", with the mock's legend (Online / Short outage or missing readings / Offline 1 h or more) plus "No history". See deviation 9. |
| Low 4 contact `state:null` | Fixed in round 2 under `D-2026-10-17-f5-subtabs-and-contact` (see Round 2). |

Deviation 9: the brief asked for "not available yet" on the timeline. That phrase must render through a catalogued `MissingClaim` placement, and `test_mock_gaps.cjs` (Architect C5) fixes `G-readiness-gateway-uptime` at exactly one placement. Adding a cold placement is a registry change for the Architect, so the track states the plain fact "No history to draw". My first attempt added the placement; the mock-gap fixture failed it, and I withdrew it rather than edit the test.

Heights (`node tools/w1-fidelity-evidence.mjs .agent/W2-01-evidence ...`, revision `e52d035e`, API 5911 and web 5912 on the private DB `assetops_w201fixcap`, seeded with the phase-1 CLI and dropped afterwards; CDP 9512; **108/108 claims passed**):

| Route / case | Panel 1 at 1440 (app/mock) | Page at 390 (app/mock) |
| --- | --- | --- |
| cold-sld stocked | 709/702 (1.01x; was 479) | 2459/1905 (1.29x) |
| cold-sld missing-probe | 709/702 | 2424/1905 (1.27x) |
| cold-readiness stocked | 672/313 (9 rows vs 4) | 3144/2476 (1.27x; was 1.39x) |
| cold-readiness missing-probe | 690/313 | 3351/2476 (1.35x, about 1.24x net of the about 275 px shell rail; was 1.46x) |

At 390, the SLD drawing fits with no sideways scroll; the cold room and probes are inside the fitted drawing. Panel overflowX is 0 on all 18 captures.

Checks (fix round):

- `npx.cmd tsc --noEmit`: clean.
- `coldFoundation.test.tsx`: 21 passed, including `expectV69Panels` for all 12 cases.
- Planted failure, committed first: truncated drawing names, the per-row function text restored, and the manual log merged back into the door row. 3 tests failed; restored with `git checkout --`.
- Full `npm.cmd test`: at `79b07ec6`, 77 files, 1978 passed. At `e52d035e`, 1977 passed and 1 failed: the known flake `siteFoundationChange` ("Unable to find ... heading Battery reserve"). Rerun alone, it gave 10/10 passed.
- `tools/check-all.ps1 -Python <plan2 venv>`: 10/10 guards passed at `e52d035e`.

Pre-review self-check:
- The state line is said once.
- One disclosure per panel.
- No leftover labels or h3s.
- No raw IDs or enums in default copy.
- No Configured/No source contradiction.
- The mock's table columns, monitoring strip, legend and timeline are all present.
- The undeclared-parts and function limits stay visible.
- Readiness rows at 390 are about 2 lines.

## Full backend suite (coordinator)

At `a4e4cb10`: 2651 tests, 2649 passed, 2 failed, 0 skipped; 62 min wall under heavy machine load. Failures: `test_s6_action_apply_postgres::TestClockBehindIsStale` and `test_t027_ingestion::TestRebuildIsolated`; both passed rerun alone (2 passed, 41 s) and are logged as load flakes in `.ai/MILESTONE_REVIEW_BACKLOG.md`. Round 2 changes one backend read path (contact null closure) after that run; it is covered by the focused run below, not by a new full suite.

## Round 2 (merge of main, contact ruling)

Commits: `81f62703` (merge), `9e892d7a` (contact).

- Merge of `main` (W1-F2 shared UI, W1-UX-07 rail). Two conflicts, both resolved keeping both sides: `frontend/src/test/v69PanelTitles.ts` (F2's `evidence-analysis:2` title rule plus the two W2-01 cold rules; header now "the six W1 rules and the two W2-01 cold rules") and `frontend/src/ui/V69Layout.tsx` `SITE_SCREEN_DESCRIPTIONS` (F2's mini/dispatch/analysis/evidence/evidence-analysis entries first, then the three cold entries). `tsc --noEmit` clean.
- Contact null closure (`D-2026-10-17-f5-subtabs-and-contact`, `.agent/W2-technical-design-cold.md` W2-01 contact null closure; review Low 4). `contact.state` is never null in a successful read. `cold_foundation_api.py` maps: no health store -> `NEVER`, `as_of:null`, limitation "No gateway health read is configured"; selected gateway with no matching diagnostic -> `NEVER`, `as_of:null`, "No diagnostic is recorded for the selected gateway"; no selected gateway -> "No gateway is selected for this site" / none registered -> "No gateway is registered for this site". A health-read error stays the 503 `GATEWAY_ACCESS_UNAVAILABLE` refusal. UI (`ColdFoundationViews.tsx` `neverContact`): "No contact recorded" (no health read), "No contact received yet" (selected gateway, no diagnostic), "No gateway selected" / "No gateway registered" (never names a gateway as uncontacted). "Never contacted" is no longer shown; Correction (W2-02 step 0, re-review Low 2): the status follows only the cold read's `contact.limitations`; the seeded COLD-002 has a registered gateway with no diagnostic and reads "No contact received yet". "No gateway selected" appears only for the backend's no-selection limitation, and a failed frontend health read titles the panel "Gateway not read".
- Tests: backend `test_contact_states_and_unavailable_store` asserts both null cases (enum, null `as_of`, limitation; unmatched via a health store whose only diagnostic belongs to another gateway); `test_w201_cold_vocabulary` asserts `contact_document(None[, absent])`. Frontend `coldFoundation.test.tsx`: two new cases (missing store, unmatched) assert wording and absence of recent/stale/last-contact/never-contacted; the COLD-002 readiness case asserts "No gateway selected" and no "Never contacted".
- Deviation: the no-gateway-selected/registered limitations are exercised only through the existing COLD-002 UI case (empty health list), not by a backend API case; no cold fixture lacks a gateway registration.

Checks (round 2, at `9e892d7a`):
- Focused backend, serial, `.venv`, private DB `w201r2_test` on 127.0.0.1:55432 (created, then dropped): `pytest backend/tests/test_w201*.py` 44 passed, 29 s.
- `vitest run src/sites/__tests__/coldFoundation.test.tsx` 23 passed. Full `npm.cmd test`: 77 files, 2010 passed (no flakes needed rerun; includes `panelStructure.test.ts`).
- `tools/check-all.ps1 -Python <plan2 .venv>`: all 10 guards passed.
- No full backend suite in round 2.

