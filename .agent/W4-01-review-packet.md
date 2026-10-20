# W4-01 review packet (work-case core and thin Site lists)

Task `tasks/W4-01-work-case-core.md`; contract `.agent/W4-01-build-spec.md` (closures 1-3, rulings q1-q7, commit-4/5
dry-reads). Branch `task/W4-01-work-case-core`, head `0e77205d` (+ this packet). Lane A. USER_REVIEW: owner W4
result review follows independent review (spec "Frozen surface and closeout").

## Commits
| # | Commits | Content |
| --- | --- | --- |
| 1 | `4cb89c68` | `0027_w4_work_cases` literal schema, triggers, scoped FKs, upgraded-head literals |
| 2 | `9533d97d` (+ W3-01 provenance unit `f6fd3c4f` line) | work model/service, sole INSERT-only `postgres_work_store.py`, rule-8 writer |
| 3 | `5973ca09`, `3353e858`, `99e5fea3` (+ W3 prereqs `86d0a074`..`98482cbb`) | command routes, case detail, read adapter, Q9 coverage |
| q4 | `a4dfd318`, `f3557bc2` | private read clock (q4-1), command-time link cutoff (q4-2) |
| 4 | `998d3330` | `GET /work/incidents`, `/work/maintenance` (`site-work-index-1`), cursor/fence/provenance |
| 5 | `8e0f331b`, `888063db`, `0e77205d` | Site UI routes, views, guard multiset, registry task tags, captures |

## Files materially changed (commit 5)
- New: `frontend/src/sites/{workClient.ts,siteWorkCases.tsx,SiteWorkIncidents.tsx,SiteWorkMaintenance.tsx,w4-work-cases.css}`,
  `frontend/src/sites/__tests__/siteWorkCases.test.tsx`.
- `frontend/src/shell/{operatorSiteRoutes.ts,SiteAnalyticsFrames.tsx}`, `frontend/src/App.tsx`,
  `frontend/src/ui/V69Layout.tsx`, `frontend/src/sites/SiteFoundationChange.tsx` (header union), `frontend/src/test/settled.ts`.
- `tools/checks/navigation-truthfulness.ps1`, `tools/checks/navigation-rail-fixtures.ps1`,
  `frontend/docs/architecture/v69-dependency-registry-pilot.json` (nine nodes `"task":"W4-01"`, status unchanged).
- Tests updated: `operatorSiteTabs`, `operatorRouteFrames`, `w1f4ChangesWorkStructure`, `siteWorkActions`.

## Acceptance (commit 5 dry-read)
| Criterion | Status |
| --- | --- |
| Routes `/sites/:siteId/work/{incidents,maintenance}` + href helpers; one Work subrow, Actions first, both live | Met (`SiteWorkCasesFrame`, `WorkSubrow`); no new Site tab or rail root |
| Unavailable multiset minus `Incidents×1, Maintenance×1`, guard + fixtures atomic; rail unchanged | Met; non-vacuity proved (reintroduced `<UnavailableTab label="Incidents" />` fails "inventory is exactly", reverted) |
| Window: default 7 complete UTC days to today 00:00, date form, `limit=5`, `known_at`+cursor bound, new window resets | Met (`defaultWorkWindow`, `workPageQuery`; Previous cursors in history state) |
| `Showing {first}–{last} of {total_count}`; 409 offers first-page reload; 422/503 visible, never zero | Met (jsdom `incident_stocked_empty_and_refused`) |
| Literal copy: headings, five columns, empty blocks, subcopy, strip, Manage text, notice | Met; **but** missing-claim scan refuses two strings (q8-1) |
| Fields: Case `code · title` plain text (`url:null`), Window EAT + UTC disclosure, narrative, pinned Finding links, state | Met; `Finding {8}` → `siteFindingHref(site, id, revision)` (`finding_link_uses_pinned_revision`) |
| Maintenance: Asset `asset_label`/`No asset linked`, Activity state+activity, Outcome `Unverified`+note, Next evidence copy | Met (`maintenance_activity_without_outcome`) |
| Chips: Incident OPEN red, IN_PROGRESS blue, CLOSED/CANCELLED neutral, COMPLETED blue, UNVERIFIED amber | Met; request OPEN amber (reading) |
| `expectV69Panels` + planted-panel rejection, all variants | Met (stocked, empty, refused for both screens) |
| Caps 1440/390, page caps, no page overflow, table-only scroll with retained first column and affordance | Met (`test_w401_stocked_five_rows_1440_and_390`, 126 checks pass) |
| Registry seven paths "reviewed" + checker | Partial: task tags only, checker passes; panel paths open (q8-2) |
| Same-revision full backend suite | Not run here by instruction (runs beside independent review) |

## Captures (`.agent/W4-01-evidence/`: `seed.py`, `capture.mjs`, `evidence.json`, `mock-measure.json`)
Seed (q3-10): fresh `w401h_test`, KOBO-001 by the real importer, 7 incidents + 3 requests (one COMPLETED with an
activity record, one CANCELLED) through the W4 service with the private `service:w401-fixture` principal at real DB
time; read only via uvicorn 9746 + vite 6145. Window stocked `2026-10-13..21`, empty `2026-09-01..08`, refused =
reversed window (422 `INVALID_WINDOW`). Files `{screen}-{stocked|empty|refused}-{1440|390}-app.png`,
`{screen}-{1440|390}-mock.png`. Revision `0e77205d`. Viewed: incidents stocked 1440/390, maintenance stocked
1440/390, incidents refused 1440, maintenance mock 1440.

| Screen · state | 1440 status/panel/notice (cap) | 390 status/panel/notice (cap) |
| --- | --- | --- |
| mock incidents | 37/316/42 | 91/354/78 |
| incidents stocked | 39/420/44 (48/460/54) | 84/460/63 (118/460/101) |
| incidents empty | 39/295/44 (48/410/54) | 84/379/63 |
| incidents refused | 39/145/44 | 84/212/63 |
| mock maintenance | 37/296/42 | 91/316/78 |
| maintenance stocked | 39/316/44 (48/384/54) | 84/360/63 (118/410/101) |
| maintenance empty | 39/275/44 | 84/341/63 |
| maintenance refused | 39/145/44 | 84/212/63 |

Pages ≤1034 px (caps 1431/1579); document overflow none; at 390 tables 720/760 scroll inside 309 px with sticky first
column (`stickyFirst: true`) and visible hint; subrow one row (36 px). Incidents stocked 390 sits exactly at its cap
(460) and 1440 stocked is 1.33x mock (under the reviewed 460 stocked cap). Seed has no Finding link (F01 evidence
received 2026-10-30 > real DB time, q2-4); pinned-link rendering is jsdom-only.

## Checks (serial, private `w401h_test`, dropped after)
- Backend focused at `0e77205d` (no backend change in commit 5): `test_w401_work_api.py` + `test_w401_site_indexes_postgres.py`
  16 passed, 360 s. Commit 4 run (handoff run 9): 45 passed at `998d3330`.
- Frontend focused: `siteWorkCases.test.tsx` 4 passed; the four updated UI files 100 passed.
- Frontend full `npx vitest run` at `0e77205d`: 92 files, 2362 passed, 1 failed - `siteFinancials.test.tsx`
  "reloads page one at the same moment when the basis changed (typed 409)" (unchanged S4-08 file, same load flake as
  W2-07); isolated rerun of the file 83/83 passed. Frontend delta +6 tests (4 new + 2 route assertions).
- `npm run build` (tsc + vite): passed. Registry checker: passed.
- `tools/check-all.ps1` at `0e77205d`: **8/10** - FAIL `Missing-claim orphan scan` and its fixture self-check:
  `siteWorkCases.tsx:105 untagged missing-capability copy "Case history is stored with this site. A global work page and
  create flow are not available yet."` and `siteWorkCases.tsx:240 ... "· Not available yet"` (q8-1). All others pass.
- Full real-Postgres backend suite: not run by this builder (policy: runs in parallel with the review).

## Builder readings (all runs)
- Commit 1 (8), commit 2 (8), commit 3 (6): ruled in spec tables "Eight commit-1/commit-2", "Six commit-3 builder readings".
- Run 5 (8): pending-rulings "Run 5 resolution and readings" 1-8 (cold/EV pin seq; link state mapping; mini-grid
  detail window; Action link event check; `work-link-selection/1` token; `INVALID_KNOWN_AT` message; detail link
  item shape; `build_cold_ev_selection_pins`). Run 6 r1-r5 ruled in q5.
- Run 9 (commit 4, 11): handoff run 9 "Readings taken" 1-11 (Action label/href; fence state without HISTORICAL;
  UNKNOWN pin null token; `wce1-` raw state; zero-case `basis_sha256:null`; six-digit times; row `recorded_at`;
  cursor K > read_at 409; no-revision case ineligible; fences deduplicated off-wire; test-scoped monkeypatches).
- Commit 5 (new): (1) request OPEN chip amber (S21 names incident red only); (2) Activity cell = state chip +
  activity, no second Unverified badge (dry-read over S20); (3) `STALE_SOURCE` strip copy `Linked evidence source is
  out of date` (no literal); (4) subtab labels without mock counts `(n)`; (5) empty block without the mock icon (svg
  guard); (6) Previous cursors in history state, shared link with a cursor shows `Showing {n} of {total}`; (7)
  page two passes explicit `known_at`, so it reads `HISTORICAL` ("Read as of ..."); (8) window form one row at 390,
  labels above inputs; (9) row disclosure "UTC and IDs" sits in Window (incidents) / Asset (maintenance) cell;
  (10) shared body in `siteWorkCases.tsx` beside the two named page files; (11) no Site switcher exists, so
  "keep subtab on Site switch" has no surface; (12) refusal states use inline `ProductStatus` (shows "As of: time
  not recorded"); (13) `backend/tests/fixtures/w4/w401-work.json` does not exist on the branch (earlier commits).

## Known deviations / residual risk
- check-all 8/10 until q8-1 is ruled; registry panel paths open (q8-2).
- Incidents 390 stocked panel is at the cap with five two-line rows; longer titles stay clamped, so height is bounded.
- jsdom bodies are hand-built to the backend row keys (no committed W4 list contract fixture).

## User-review focus
Live Work subrow; count vs unknown; Unverified outcome wording; 390 table scroll.
