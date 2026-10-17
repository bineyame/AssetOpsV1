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

1. Phase 1 (from the handoff): extra response fields `bindings[].cadence_seconds` + `publication_mode`, `contact.limitations`; `contact.state=null` (limitation "Gateway contact is not available") when no health store is configured; topology node/edge and message object shapes chosen (design unspecified); invented copy `ROLE_UNBOUND` "Bind the <role label>" and `ROOM_MISSING` "Declare a cold room"; event outcome allowlists taken from the shared v4 kind-to-outcome table; no v4 metadata persisted on cold binding rows (W2-02 must derive/persist); COLDCHAIN edge media/endpoint pairs restricted to the design's pairs; `configuration_gaps` still `SITE_TYPE_UNSUPPORTED` for COLDCHAIN, so the gateway acquisition snapshot download refuses cold Sites (W2-02); contact uses current gateway facts, not as of `at`; added `FoundationService.publish_topology` (tests/fixtures only).
2. Gateway title identity: the store has no gateway display name, so `cold-readiness:2` uses `gateway_external_id` from `/gateway-health` (fallback "No gateway selected"); this is a current read, not as of `at`.
3. `cold-sld:1` is the Site name alone: the Foundation declares no topology type.
4. Site name comes from the current Site record, not the selected revision (no name field in the cold read).
5. Readiness table areas (Site definition, chamber probe, compressor, grid, backup generator and bus, transfer switch, door/loading log, ambient) group `cold-roles-1` roles; grouping and the "(optional)" marking are presentation choices, not specified. Mock has 4 illustrative rows; the app shows 8, so the table is taller than the mock.
6. Foundation panel 2 row "Door and loading observations" replaces the mock's "Loading observations": the capture tool's readiness check treats any "Loading" text as a page still loading.
7. The configured drawing is a layered box diagram of declared nodes/edges, not the mock's bus-bar SLD; it is shorter than the mock's drawing because only declared parts are drawn. Below 760 px it keeps a readable scale and scrolls inside its own keyboard-focusable region.
8. Gateway metric cards Availability/Data completeness/Clock show "Not available"/"Unknown" with a plain note; no MissingClaim placement was added for these cold cards (no catalogued gap ID exists for cold; the missing-claim scan passes).

## Residual risk

- Prominence: SLD drawing (about 320 px at 1440 vs the mock's ~600 px) and the denser readiness table are the panels to judge from the captures.
- The generic Foundation read still answers for cold Sites (with `SITE_TYPE_UNSUPPORTED` in its gaps); only its versions list is used by the cold views.
- Contact and gateway identity are current facts on historical periods; the panel says so.

## User-review focus

Walk the three routes for COLD-001 and COLD-002 side by side with `#/cold-foundation`, `#/cold-readiness`, `#/cold-sld` (`.agent/W2-01-evidence/index.html`): top fold, panel widths/heights, the missing-probe and never-contacted wording, and that nothing reads as a temperature, cooling or backup condition.
