# W6-01a (unit A1) phase handoff - BLOCKED before code

Branch `task/W6-01a-global-incidents` from main 3a14f5aa. No code written; no DB created; no process started.
Stopped per dispatch rule (unspecified/contradicting code => report, do not choose).

## Blocking (A1 file list vs guards)
- Q1. `tools/checks/configuration-persistence.ps1:833` rule 8 `$pgReaders` admits a sqlalchemy import only in
  listed reader files (`:900-904`). New `work/adapters/postgres_global_read.py` needs that import, but the guard
  file is not in A1's list. Amend A1 to own a one-line `$pgReaders` addition?
- Q2. Only `work/composition.py` may import work adapters (`configuration-persistence.ps1:8`, domain at `:168-176`;
  pattern `work/composition.py:51-64`). `main.py` cannot build the global read itself. Amend A1 to own
  `backend/assetops_backend/work/composition.py` (e.g. `build_global_work_index_service`)?

## Non-blocking readings needing a ruling (batched)
- Q3. Apply `missing_lineage` to a case row whose link lacks lineage, as the Site list does (`work/site_index.py:220-221`)?
  Spec says only "`provenance_dto`" + `case_basis`.
- Q4. HISTORICAL on a cursor page that omits `known_at`: W4 labels explicit only (`site_index.py:300`), estate labels
  `k < read_at` (`estate/index.py:160`). And a page-two explicit `known_at`: W4 exact-equal rule (`site_index.py:291`)
  or estate wire-second rule (`estate/index.py:155-157`)?
- Q5. Authorized-Site candidates: reuse estate `imported_at < to` (`estate/adapters/postgres_estate_read.py:116`)?
- Q6. Read time: W4 `clock_timestamp()` + `test_read_clock_override` (`postgres_work_read.py:283-288`) needed for the
  pinned `12:00:02Z` reads, vs estate `now()` (`postgres_estate_read.py:90`). Confirm W4 form.
- Q7. Link labels for `finding_links`/`action_links` (`Link={label,href}`): reuse W4 `Finding {id[:8]}` /
  `Action {id[:8]}` (`site_index.py:177-191`)? Order of `linked_request_codes`?
- Q8. `links.site_incidents` `known_at` when the page omitted it: always the response `known_at` (example shows it)?
- Q9. Example `actor_id` `service:w601-fixture` vs §4 "inject `W401_FIXTURE_SERVICE_PRINCIPAL_ID`" = `service:w401-fixture`
  (`work_api.py:39`). Which principal does the seeder use?

## Tests
None run (no code).

Next: Architect amendment of A1 card (Q1-Q2 required; Q3-Q9 rulings), then rebuild A1; then A1 per-unit review.

## Run (A1 build after the A1Q amendment, 2026-10-22)
Commits: `ad1cefc1` (A1 Lane B + Lane A), `801e5ad8` (seed key fix). Files exactly the amended A1 list.
- Lane B: `work/global_index.py` (`GlobalWorkIndexService`, `parse_global_request`, HMAC cursor with `page_one_mode`),
  `work/adapters/postgres_global_read.py` (`PostgresGlobalWorkRead`/`GlobalReadTx`, W4 `_ReadTx` reused),
  `global_work_api.py`, `tools/w601_seed.py`, `backend/tests/test_w601a_global_incidents.py`.
- Lane A: G1 `$pgReaders` line, G2 composition builders + `main.py` mount, G3 README key block.
Tests: `test_w601a_global_incidents.py` 15 passed; with adjacent `test_w401_work_api.py` + `test_w301_estate_api.py`
34 passed (304 s, private `assetops_w601a_test`, dropped). Full backend suite not run (per dispatch).
`tools/check-all.ps1`: all 11 guards passed. G1 non-vacuous: deleting the reader line fails check-architecture
(sqlalchemy import in `postgres_global_read.py`), reverted with `git checkout`.
Seed CLI smoke: `--fixture historical` and `cursor_change --append` on `assetops_w601_a1_test` (dropped). No process left.

Readings to confirm (non-blocking, recorded rather than chosen silently):
- R1. §4 requires the ordered write clock, which `build_work_service` cannot take; the seed tool builds
  `WorkService(PostgresWorkStore(..., test_db_clock_override=...))` directly (outside every guard scan root; G6(c)
  names only `build_work_service`). Confirm.
- R2. `linked` fixture is not provided by A1 (needs Finding/Action producers); §4 allows a labelled pure snapshot. A2 decides.
- R3. The global selection token binds per-row case/revision/event/record/link-pair/lineage/cited IDs and request
  codes, not W4's cold/EV fence states (global status never derives from them, Q4).
- R4. `empty_scope` seeds the `incidents` rows; the empty scope comes from the read's deny-all access callback.
Next: independent A1 per-unit review, then A2.

## Run (A2 build, 2026-10-22) - BLOCKED before code
Read: this handoff, spec A2 card, §1, §2, §3.1 (F1-F6, G6, A1Q2), §4, both mock-measure files, mock `screens.js:514-517`,
and the code the card touches. No code written, no DB created, no process started. Stopped per dispatch (unclear => ask).

Blocking:
- A2Q1. `Open incidents` = OPEN+IN_PROGRESS (§2 incidents cards), but the §1 envelope has no per-state count and the UI
  reads `limit=5` pages, so the full-set count is not derivable once `total_count > 5` (the `incidents` fixture has
  6 in-tenant rows = 2 pages). (a) A1 adds an envelope count bound into the token (A1 files), (b) exact only when the
  whole set is on one page, else a stated gap (literal?), or (c) other? Also unspecified: the card's note (mock `INC-203`)
  and whether cards render on `EMPTY_SCOPE` / complete zero.
- A2Q2. Capture stress `5 rows, title200/actor128/UUID/reason`: `tools/w601_seed.py` (A1-owned, not in A2's list) writes
  only short titles and assignee `Field team A`; the incident row (§1) has no actor or reason field and shows no UUID.
  Which producer writes the stress rows (seed extension by whom, or capture-time DOM injection as mock-measure-2), and
  which cells carry actor128 (Owner = assignee?), UUID and reason?
- A2Q3. Pinned clock vs real read time: `--clock 2026-10-22T12:00:00Z` stores `recorded_at` 11:59:00Z+ on 2026-10-22, the
  server reads at `clock_timestamp()` (A1Q Q6; override is pytest-only) and §4 says captures use real DB time. Now is
  08:25Z, so a current read selects no row until after ~12:00:03Z. Wait, or use another `--clock` (e.g.
  2026-10-21T12:00:00Z, window 2026-10-14..2026-10-21, which §4 permits)?

Readings needing a ruling (proposed precedent in brackets):
- A2Q4. Source label: ledger claim says rows carry "a source label" and §2 gives the four work provenance literals, but
  the seven columns have no Source slot. Where does `source_provenance` render (secondary line, row disclosure)?
- A2Q5. Cutoff control: §2 controls are From/To/Show records/Reload/Previous/Next (no cutoff input); ledger `interaction`
  says "choose a UTC window or cutoff". URL `known_at` only, or an input (label?)?
- A2Q6. Refusal UI copy for 401 and 422 INVALID_WINDOW/INVALID_KNOWN_AT (incl. invalid page query, no fetch)/INVALID_LIMIT/
  INVALID_CURSOR is not in §2 [estate `REFUSAL_COPY`, `estateClient.ts:366-377`; INVALID_CURSOR -> cursor-change copy].
- A2Q7. "Footer slot replaces mock states footer": the mock's `States: ...` is the panel sub-line under the heading
  (`screens.js:36` `panel(title,body,sub)`), not below the table. Render in Panel `description` (mock slot) or below the table?
- A2Q8. Cell literals not in §2 [State `Open/In progress/Closed`, tones `siteWorkCases.tsx:146-160`; Start = §2 date
  format of root `occurred_at`; Incident = `{code} · {title}` -> `links.site_incidents`, clamp + `Full title text`;
  Site -> `links.site`; Findings / work = finding · action links / request codes as plain text (mock `F · F / WR · ACT`);
  empty cell text?].
- A2Q9. Registry JSON is in A2's list but §4 keeps rows `gap` and gives no A2 literal. Any edit (e.g. `incidents:1,2`
  reason "awaits build and independent review" -> built/awaits review, W4-01 precedent registry line 426), or none?
- A2Q10. Previous needs earlier cursors [Site W4 history-state trail, `SiteAnalyticsFrames.tsx:1601-1622`]; and is a
  `Showing x-y of N` line wanted (not in §2)?

Next: Architect amendment of the A2 card (A2Q1-Q3 required; Q4-Q10 rulings), then rebuild A2.

## Run (A1 reopen, A2Q1 state_counts)
`work/global_index.py` adds `state_counts` (`sum(1 for r in rows if r["wire"]["state"] == S)` over the full selection before paging; incidents only; EMPTY_SCOPE all 0). Added `test_state_counts_cover_full_selection` (closes "Pump stopped" via the seed Writer: 4/1/1 on both pages, zeros on EMPTY_SCOPE); `ENVELOPE` test set gained `state_counts`. `test_w601a_global_incidents.py` 16 passed; `tools/check-all.ps1` 11/11 guards passed. Test DB dropped; no processes left. A2 not built.

## Run (A2 rebuild after A2Q/CL3, 2026-10-22) - built and captured; BLOCKED on off-card test files
Commits: `db8b3847` (Lane B: `frontend/src/work/*`, seed `stress`), `63d62caa` (Lane A: route, rail, guards, Site Work
link/notice, ledger, registry), `ccbb0b43` (inline collapsed disclosures for the 600 px cap; captures + manifest).
Edits are confined to the amended A2 card files plus `.agent/W6-01-evidence/A2/`.

Checks:
- Focused: `globalIncidents.test.tsx` 21 passed. The card's Lane A tests (siteWorkCases, operatorRailInventory,
  operatorRouteFrames, w301EstateShellRoutes, estatePortfolioRoutes) pass with the work tests: 68 passed. `tsc --noEmit` is clean.
- `tools/check-all.ps1`: all 11 guards passed, both after Lane A and after the CSS change. The ledger checker and the
  registry checker (262 nodes, 51 linked panels) pass. The new F2 rail fixtures run inside check-architecture.
- Captures (`.agent/W6-01-evidence/A2/manifest.json`, 1440/390). States: positive (stress: 5 rows plus Next), zero,
  historical (`Historical as of 21 Oct 2026, 12:00 UTC`), refused_503 (absent DB), refused_window (no fetch) and
  cursor_changed (409 after `--append`). Every element is within its section 2 cap: panel 524/664 (positive),
  682/690 (historical at 390), cards 115/264. The document never overflows (1440/1440 and 390/390). The table
  scrolls in its panel at 390 (720/318) with `Scroll table horizontally` visible.
- Processes: Vite, uvicorn and Chrome are all stopped. DBs `assetops_w601_a2*_test` are dropped. The full backend suite was not run.

Blocking:
- A2Q11. Six frontend test files that are NOT on the A2 card pin the operator rail's live-link set without
  Incidents. They now fail (13 tests; `src/shell src/estate src/sites src/work src/ui`: 2451 passed, 13 failed):
  `shell/__tests__/{operatorSiteTabs:387, simulatorLabWorkspaceEntryPoint:93, siteDetailRoute:395/446,
  siteFoundationRoute:427/455/469, sitesIndexRoute:299/381}.test.tsx` and `ui/__tests__/sharedVisualVocabulary.test.tsx`.
  Each expects the list without `Incidents` or `/incidents`. `siteFoundationRoute:455` "has not gained a navigation item
  at any point since T004" checks a historical allow-list, so it needs a ruling on its literal. Amend the A2 card (and
  B2/E2, which repeat this) to own these files with the one-entry edits? CL3-7 named only `operatorRouteFrames`.

Readings (not chosen silently; confirm):
- R5. `Show records` keeps a URL `known_at` (section 1 "sends them unchanged") and clears the cursor and trail.
  `Reload` re-reads page one of the same query.
- R6. The control bar and status line sit in a `.site-date-bar` slot. The refusal and empty-scope blocks carry
  `data-page-refusal`, which keeps `expectV69Panels("incidents")` passing without editing `test/panelStructure.ts`.
- R7. `test/settled.ts` LOADING does not match `Loading the incidents across the estate.` (the file is off-card), so
  the test also waits for `[data-global-work-loading]` to disappear.
- R8. In the Vite dev server (StrictMode) each page read is fetched twice (`api=[200,200]`); a built app fetches once.
Next: rule A2Q11; then one small fix round edits the six test files; then the A2 per-unit review.

### Run update (A2Q11 applied, 2026-10-22)
Commit `428d4117`: only the six A2Q11 test files, with the ruled literals (labels and links with Incidents, icon
`["Incidents","incident"]`, `"Incidents"` added to `ADMITTED_SINCE_T004`). R5-R8 are confirmed; no code change.
`npx vitest run src/shell src/estate src/sites src/work src/ui`: 103 files, 2464 passed, 0 failed.
`tools/check-all.ps1`: all 11 guards passed. No process was started; no DB was created.
Next: A2 per-unit independent review.
