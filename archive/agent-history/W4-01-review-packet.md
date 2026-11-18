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

## Fix round r1 (`task/W4-01-fix-r1`, from `afa35e79` + main; rulings: build-spec "Run 8 rulings (q8)" and "Review r1 rulings")
Captures re-taken at the fix revision (all 12 app captures, 1440 and 390, `.agent/W4-01-evidence/`); `capture.mjs`
`test_w401_stocked_five_rows_1440_and_390` passed 174 checks, now including counts, three-span strip, empty icon.
Heights vs caps unchanged-or-lower: incidents empty 1440 337 (cap 410), 390 421 (460); maintenance empty 317 (384), 383 (410);
stocked 420/460/316/360 as before; subrow one row (36 px), no page overflow.

| Finding | Fix | Test / capture |
| --- | --- | --- |
| q8-1 | `siteWorkCases.tsx` `WORK_MANAGE_UNAVAILABLE_STATUS`; two `REVIEWED_EXEMPTIONS` in `missing-claim-scan.mjs`; baseline untouched | check-all 10/10 incl. orphan scan and its fixture self-check |
| q8-2 | `registry.panels` `sitework-incidents:1`/`sitework-maintenance:1` (`status:gap`, reason awaiting review, requires per ruling, titles added); both ledger rows: `registry_dependencies` P-work-cases + node order, `task:W4-01`, bounded copy. Checker forced `coverage:bounded`, `follow_on:null`, `to_candidate:null` (S-task screen rule); the tier/global-control pendings moved to `to_real.remaining_work`; tier stays Deferred/pending owner | registry checker exit 0; Screen ledger PASS |
| q8-3 (5, 13) | icon (H2); fixture (M2) | below |
| H1 | `WorkSubrow` + `useWorkCounts` in `SiteAnalyticsFrames.tsx`: `Label (n)` from each list's `total_count` (W4 lists `limit=1` via new optional `WorkScope.limit`; Actions `limit=1`), same Site/window, independent, dash on pending/error/non-finite, no read without a window, cleared on key change | `siteWorkCases.test.tsx::work_subtab_counts`, narrow test; captures `subrow.labels` |
| H2 | `<RailIcon name="evidence"/>` in a 28 px `aria-hidden` wrapper | `incident_stocked_empty_and_refused`, narrow test (icon present on zero, absent on refusal); empty captures |
| H3 | CURRENT yields no word; qualifiers sit inside the detail span (no 4th slot) | `strip_words_and_coverage_copy`, stocked test (3 spans, no `.status-strip__state`) |
| M1 | behavior kept; exact same `known_at` sent on Next/Previous and shown | `incident_stocked_empty_and_refused`; `test_cursor_fence_and_full_count` (explicit K gives HISTORICAL, same page/token; changed basis 409) |
| M2 | `backend/tests/fixtures/w4/w401-work.json` (schema/keys per B7/B11, input + semantic expectations only) | `test_incident_attestation_reload_and_exact_links` replays schema, keys, sorted/LF form |
| M3 | CoverageLine sentences replaced; STALE copy, `As of: time not recorded`, `Reading work records`, `Showing n of total` asserted; Action label | `strip_words_and_coverage_copy`; `test_pinned_link_survives_...` (label, pinned event href); Finding null href already in `test_pending_link_and_missing_source_keep_gap` |
| M4 | #2 fence/HISTORICAL equality, #5 six-key zero DTO, #8 cursor K after read time 409 added; #1/#3/#4/#11 already asserted | `test_cursor_fence_and_full_count`, `test_site_window_cutoff_and_empty_count`; `test_list_refusal_has_null_rows_and_total` rerun |
| M5 | `git revert` of `9a5756f9` (0b) then `aff24bbd` (0a); the money-prereq test module `test_w301_w1_money_snapshot_helpers_postgres.py` (not on main) deleted by the 0b revert (it only tested those two functions) | see accounting below |

M5 accounting (vs main, `backend/assetops_backend`): money files now differ only by `financials/composition.py`
(`build_source_provenance` -> `build_public_provenance`, the preserved shared provenance port) and +1 selected column
`r.finding_revision_id` in `_EV_REVISION_SQL` (read by `public_provenance.py:304`, the shared port). No
`select_consequence_on`/`for_finding_on` remains. Main does not contain either money commit. Backend production code
changed in this round only by the two reverts (removal of unused money code); no new production logic.

Checks (private DB `w401i_test`, dropped afterward): `test_w401_site_indexes_postgres.py` + `test_w401_work_service_postgres.py`
13 passed; `test_w401_work_read_postgres.py` + `test_w401_work_api.py` 15 passed. Full backend suite not run (instructed).
Frontend full suite 92 files, 2364 passed + 1 failed (`w1f4ChangesWorkStructure` bare-label assertion, updated for H1 counts and rerun: 13 passed) = 2365; tsc exit 0; build exit 0; registry checker exit 0; check-all 10/10 (`ASSETOPS_GUARD_PYTHON` set).
Not changed: `operatorSiteTabs`/`operatorRouteFrames` tests (no Work-subrow content assertions there; coverage is in
`siteWorkCases.test.tsx`, which mounts the real `App`). Residual: the Action-link null-href-on-missing-lineage vector is not
reproduced (only the Finding null href is).
