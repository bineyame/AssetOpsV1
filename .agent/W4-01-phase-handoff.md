# W4-01 phase handoff - run 9: commit 4 (lists) complete; commit 5 next (2026-10-20)

Merged main (q7 rulings + final dry-read). **Commit 4 `998d3330`**: Site Incident/Maintenance lists.

## What landed

- `work/site_index.py`: `parse_list_request` (q7-5 literals; window -> limit -> known_at -> cursor), `select(rx,...)`
  (all eligible cases at fixed K before paging; B1 rows + maintenance extras; Q8 fences; B8 `work-selection/1`
  token; full-set Q11 provenance with q7-4 guard), `WorkIndexService.read` (cursor `{v,tenant_id,site_id,kind,from,
  to,known_at,selection_token,after}`, r4 keyset, 409 `WORK_BASIS_CHANGED` on scope/cutoff/basis change).
- `work/adapters/postgres_work_read.py`: `_ReadTx.site_name`, `eligible_cases`, `action_window`; `link_selections`
  rows add `lineage`, `origin_finding_id`, `origin_finding_revision_id`; `LinkReadPorts.action_window`
  (`build_action_store(None).site_window_on`, wired in `work/composition.py`).
- `work/service.py`: `case_basis`, `provenance_dto`, `missing_lineage` (case_provenance unchanged in output).
- `work/link_coverage.py:coverage_of`; `work/model.py` INVALID_WINDOW/LIMIT/CURSOR, WORK_BASIS_CHANGED,
  `WorkRefused(code, message=None)`, `SCHEMA_INDEX`.
- `actions/site_index.py`: `window_scope`, `index_token` factored out of `read()` (behavior-preserving).
- `work_api.py`: `GET /work/incidents`, `GET /work/maintenance` before `/work/cases/{id}`; list refusals add
  `rows:null,total_count:null`; `lists=`/`access_basis=` router params. `main.py` passes `build_work_index_service`.
- Tests: new `test_w401_site_indexes_postgres.py` (5 nodes, runner tests before the `chain` test);
  `test_w401_work_api.py::test_list_refusal_has_null_rows_and_total`.

## Readings taken (none blocks; flag in review)

1. Action link label `Action {first 8 UUID chars}` (B1 names none); href = W1 `selected_action_links(..)["selected"]`
   (`/sites/{code}/actions/{id}?event_id={event}`); Finding href `/sites/{code}/findings/{id}?revision_id={rev}`.
   Both null when lineage is missing at K.
2. Fence `state` inside the token is the B9 link state without HISTORICAL; status HISTORICAL only when the query
   gives an explicit `known_at < read_at` (else an omitted page-two K from the cursor would change the token).
3. A lineage-valid pin whose reduced state is UNKNOWN (e.g. dispatch day unavailable) gets a null token.
4. `wce1-` basis `state` = the pinned snapshot's raw `state` (q6 "come from that pinned snapshot").
5. Zero-case list provenance has `basis_sha256: null` (shared DTO: no selected IDs); still UNKNOWN/EMPTY_CITATION_SET.
6. Wire times use six-digit `m.iso` (as detail, q4 r7), not the literal example's no-fraction form.
7. Row `recorded_at` = selected latest revision's `recorded_at` (dry-read).
8. A cursor K later than the new `read_at` is 409; explicit future `known_at` is 422 before cursor checks.
9. A case with no revision at K is not eligible (unreachable under the writer).
10. `linked_selection_fences` are deduplicated across cases and not on the wire (literal body has none); tests read
    them through `site_index.select`. Token `access_basis` = `finding_api.ACCESS_BASIS`.
11. Missing lineage is unreachable under q4-2; tests reach it by a TEST-SCOPED monkeypatch of
    `postgres_work_store._Tx.finding_pairs_in_scope` (only the cutoff), pending by a TEST-SCOPED dispatch reselection.

## Checks (private `w401g_test`, dropped after)

- On `998d3330`: `test_w401_{site_indexes_postgres,work_api,work_read_postgres,work_service_postgres}.py` +
  `test_s6_site_action_index{,_postgres}.py`: 45 passed (273 s).
- `tools/check-all.ps1` on `998d3330`: all 10 guards passed.

## Commit 5 resume point

Build per spec "Commit 5 implementer dry-read" and B10/S19-S31: `frontend/src/sites/{SiteWorkIncidents,
SiteWorkMaintenance,workClient}.tsx/ts`, `shell/operatorSiteRoutes.ts` (two routes + href helpers),
`shell/SiteAnalyticsFrames.tsx:1013-1014` subrow links, navigation guard/multiset updates, the four named UI test
updates and `tools/checks/navigation-rail-fixtures.ps1`. Client: `GET /api/sites/{code}/work/{incidents|maintenance}
?from&to&limit=5[&known_at][&cursor]`; bind response `known_at` + `next_cursor` across pages; 409 -> first-page
reload. Stocked capture via the private harness (`W401_FIXTURE_SERVICE_PRINCIPAL_ID`, q3-10). Then registry paths,
captures at 1440/390, one same-revision full backend suite, independent review.

# W4-01 phase handoff - run 8: stopped at q7 questions; commit 4 NOT started (2026-10-20)

Merged main (q5 + q6 rulings). Surveyed commit-4 seams against q5/q6 and stopped on five open questions,
`.agent/W4-01-pending-rulings.md` "q7" (asset label column absent; Action `sai1-` window; mini-grid Action token;
missing-lineage list provenance shape; list refusal literals). No code written; no tests or check-all run (no code
change since run 7's 10/10).

Resume plan (after q7 answers), files and anchors:
- `work/adapters/postgres_work_read.py`: add `_ReadTx.site_name`, `eligible_cases(kind,from,to,K)` (B10 membership,
  r4 order), `asset_label`; expose `lineage` (`pinned is not None`) in `link_selections` output (:146-153);
  add `LinkReadPorts.action_window` (site_window_on) and the q6 `wce1-` key inputs (already in `_cold_ev` :221-224).
- `work/link_coverage.py:_token` (:92) stays detail-only; list fences built in new `work/site_index.py`.
- `work/service.py:case_provenance` (:41) - split cited/selected from DTO so the list can union all cases.
- `work_api.py`: list routes beside `case_detail` (:143); list refusal body adds `rows:null,total_count:null`.
- `work/model.py:40-58`: add INVALID_WINDOW/INVALID_LIMIT/INVALID_CURSOR/WORK_BASIS_CHANGED messages+status.
- `main.py:464-466`: pass the list service. W1 helpers: `actions/site_index.py:_iso` (:75), `fence` (:146).
- Tests: new `tests/test_w401_site_indexes_postgres.py` (5 nodes: q5 three + Q7 pinned + q6 cold/EV), `runner`
  tests before `chain` tests; cold `chain` fixture pattern in `test_w401_work_read_postgres.py:179`.

# W4-01 phase handoff - run 7: q4 applied; commit 4 NOT started (context budget) (2026-10-20)

Merged main twice (`9373b800`, then the q5 merge; `.agent/*` conflicts took main's version). **Commit A (q4)**:
`a4dfd318` + `f3557bc2`. Commit 4 (lists) not started: stopped at the context budget before writing any list code.
Resume: build commit 4 per spec item 4, B1/B2/B8/B9/B10/S15, Q7/Q8/Q9/Q11 and **Run 5 rulings (q5) r1-r5**.

## Commit A (q4) - what landed

- q4-1: `work/adapters/postgres_work_read.py` `PostgresWorkRead(..., test_read_clock_override=None)`; `snapshot`
  calls it once in place of `SELECT clock_timestamp()` after `SET TRANSACTION READ ONLY`; asserts aware UTC.
  No request/env/`main.py` path sets it.
- q4-2: `work/adapters/postgres_work_store.py` `finding_pairs_in_scope` adds `created_at <= :command_now`,
  `action_pairs_in_scope` adds `e.recorded_at <= :command_now` (root join unchanged). Corrections already route
  copied links through `service.py:_check_links` (line ~300), so create and correction are both covered.
- Tests: `test_w401_work_service_postgres.py::test_link_pin_newer_than_command_refuses` (new; clock 1 us before the
  Finding revision, then the Action event -> `WORK_LINK_SCOPE_INVALID`, row counts unchanged; +1 s -> 201);
  `test_foreign_asset_and_evidence_refuse` now uses the `clocked` fixture (POSITIVE_NOW) so its refusals are the
  pair checks, not the new cutoff. `test_w401_work_read_postgres.py`: cases created via `Ctx(runner,
  VirtualDbClock(POSITIVE_NOW))`; mini-grid coverage + detail read at injected `POSITIVE_NOW+1s` (omitted cutoff);
  new `test_f01_detail_route_under_private_read_clock` (route via `build_work_router(None, ..., details=...)`;
  omitted -> 200 exact pins, coverage not UNKNOWN; `01:00:02Z` -> 422 `INVALID_KNOWN_AT`; `00:59:59Z` -> 404).
- Fragility found: a `runner` test placed after the cold `chain` test fails at setup with `AdminShutdown` (the
  chain fixture's DB reset kills the shared `engine` pool). The route test is ordered before the cold test.
  Commit 4's new test file should not mix `runner` tests after `chain` tests.

## Checks (run 7, private `w401f_test`, dropped after)

- On `a4dfd318`: `test_w401_work_{read_postgres,service_postgres,api}.py`: 20 passed, 1 failed, 1 error (mini-grid
  HISTORICAL at explicit earlier cutoff; route-test setup AdminShutdown after `chain`) -> fixed in `f3557bc2`.
- On `f3557bc2`: `test_w401_work_read_postgres.py` 4 passed (32 s).
  `f3557bc2` changed only the read test file; the service/api files' 20 passes stand.
- `tools/check-all.ps1` on `a4dfd318` (merge of main included): all 10 guards passed.

## Commit 4 resume anchors (surveyed, not built)

- W1 at-cutoff, connection-taking ports already exist (W3 q5): `PostgresFindingStore.index_snapshot_on(c,t,s,
  domain,analytic,known_at)` (`analytics/adapters/postgres_finding_store.py:495`), `fence_on` (:491, live only),
  `PostgresAssessmentStore.select_dispatch_days_on(c,t,s,from_,to,known_at)` (`postgres_assessment_store.py:683`),
  `PostgresActionStore.site_window_on(c,t,s,start,end,known_at)` (`actions/adapters/postgres_action_store.py:897`).
  Example consumer of the Finding pair: `financials/money_eligibility.py:197-206`.
- W1 Finding token: `analytics/finding_index.py:227 _token` = `"sfi1-"+sha256(json(basis,sort_keys,default=str))`,
  basis built at `FindingIndexService.read` (:259-:311) from snapshot + per-day `_day` (:236) over dispatch reads;
  only domain `mini-grid-dispatch` exists (:41). W1 Action token: `actions/site_index.py:146-172` `fence(actions,
  events)` + scope -> `"sai1-"+sha256`. q5 r1: reproduce these on the work snapshot connection at `known_at` via
  new `LinkReadPorts` entries (wired in `work/composition.py:_link_read_ports`), else null token / UNKNOWN. Whether
  `select_dispatch_days_on` rows reproduce `DispatchReadService.window` exactly (keys `status,status_reasons,
  selection,window_assessment,current_basis`) is unverified - check first. Cold/EV pins have no W1 index; per r1
  they get null/UNKNOWN unless an exact token exists (flag if that makes every cold/EV list UNKNOWN).
- Detail-only `work-link-selection/1` token stays in `work/link_coverage.py`; never reuse it as the list fence.
- Files to add: `work/site_index.py`, list reads in `postgres_work_read.py` (eligible cases by window/kind/cutoff,
  latest revision, events, latest record per r5, Asset label, `site.name`), list route in `work_api.py`
  (`GET /api/sites/{site_code}/work/{kind}`), `main.py` mount, `tests/test_w401_site_indexes_postgres.py` (4 nodes
  named in q5 + Q7) and `test_w401_work_api.py::test_list_refusal_has_null_rows_and_total`. List tests over F01
  pins use `test_read_clock_override` (q4-1) and the q2 command clock.
- Run 6 readings r1-r5 are now ruled in spec "Run 5 rulings (q5)"; r1 replaced the fallback; r2-r5 confirmed with
  additions (missing-lineage guard, fixed cursor cutoff, named assertions).

# W4-01 phase handoff - run 5: commit 3 complete (2026-10-20)

Branch `task/W4-01-work-case-core` (worktree `AssetOpsV1-review5`). Commit 1 `4cb89c68`, commit 2 `9533d97d`,
commit 3 partial `5973ca09`, merge of main `ec91ed70`, run-5 stop note `b85473aa`, **commit 3 `3353e858` + `99e5fea3`**.
Next: review of commit 3 (spec item 3: review this phase before UI), then commit 4 (lists).

## Prerequisites cherry-picked (q3 ruling 6; source -> result)

`a75b0291 -> 86d0a074`, `15dae742 -> 5c197d6e`, `2a1b59cf -> b11f20fb`, `c55dadd4 -> aff24bbd`,
`da15d71f -> 9a5756f9`, `4442d33c -> 3f10893f`, `8d73c035 -> 8a126dd3`, `9956b6b8 -> 0ca3a92e`,
`381cf1a2 -> 98482cbb`. Conflict resolutions (coordinator rule: independently ruled list appends -> union):
- `a75b0291`: `tools/checks/configuration-persistence.ps1` `$pgWriters` keeps `$workWriter` (W4 q2) and adds the
  `$pgReaders` line (W3 q5 ruling 3). Union, stable order.
- `15dae742`, `381cf1a2`: `.agent/W3-01-phase-handoff.md` only (not code); took HEAD/main's version.
No code conflict otherwise.

## What landed in commit 3

- `work_api.py`: `GET /api/sites/{site_code}/work/cases/{case_id}?known_at=` (`details=` param); access -> scope
  -> service 503 -> detail. `read_scope` catches `SiteStoreUnavailable`/`FoundationStoreError`/store errors in
  `scope()` -> 503 `WORK_STORE_UNAVAILABLE` on reads and POSTs (q3 reading 5). Detail needs no write grant.
- `work/detail.py`: `WorkDetailService.detail`, `parse_known_at` (single valid UTC instant; repeated/invalid ->
  422 `INVALID_KNOWN_AT`); `known_at > read_at` -> 422; case `created_at <= known_at` else 404; revision/event/
  record `recorded_at <= known_at` ordered `(recorded_at,id)`.
- `work/adapters/postgres_work_read.py`: `PostgresWorkRead.snapshot` (REPEATABLE READ, READ ONLY,
  `clock_timestamp()` read time), `_ReadTx` scoped SQL, `link_selections` (Q9 port), `_minigrid`
  (`select_dispatch_days_on` + `index_snapshot_on`), `_cold_ev` (q7-1 evidence cutoff, `selected_windows_on`,
  shared `_snapshot(..., selection_cutoff=K, selection_seqs=...)`, pinned assessment revision must match).
  `LinkReadPorts` injected by `work/composition.py:_link_read_ports` via `analytics/composition.py`
  (`build_cold_ev_selection_pins` added: rule-8 bans the adapter import outside analytics composition).
- `work/link_coverage.py`: pure `linked_coverage(snapshot,t,s,revision_id,from_,to,known_at)`.
- `work/service.py`: `case_provenance` (Q11) shared by command and read paths.
- `work/model.py`: `SCHEMA_DETAIL`, `INVALID_KNOWN_AT` (422).
- `main.py`: `details=build_work_detail_service(...)`.
- `tools/checks/configuration-persistence.ps1`: `postgres_work_read.py` in `$pgReaders`.

## Tests (q3 placement)

- `test_w401_work_api.py` +3: `test_detail_omitted_historical_and_future_known_at`,
  `test_detail_scoped_404_and_refusal_shape`, `test_scoped_site_outage_is_503`.
  `test_list_refusal_has_null_rows_and_total` moved to commit 4 (ruling 9).
- `test_w401_work_read_postgres.py` (new, 3): `test_minigrid_pinned_finding_and_action_coverage_on_one_connection`,
  `test_missing_pin_is_unknown_never_a_head`, `test_cold_pinned_link_keeps_its_seq_after_reselection` (q7 cross-ref).

## Checks (this run, private `w401e_test`, dropped after)

- On `3353e858`: W4 api/service/read/migration + W3 prerequisite tests (`test_w301_*` 5 files): 46 passed (13m33s).
- On `99e5fea3`: `test_w401_work_read_postgres.py` + `test_w401_work_api.py`: 13 passed (3m06s).
- `tools/check-all.ps1` on `99e5fea3`: all 10 guards passed.
- Guard non-vacuity: an `INSERT INTO work_event` in the reader fails rule 8 ("second product database writer");
  removing the `$pgReaders` entry fails ("Database driver imported outside"). Both reverted.

## Open risks / notes for review and commit 4

- F01 virtual clock: the F01 runner writes from 2026-10-29 (virtual), so at today's wall-clock read time its
  pinned revisions are not yet created (detail coverage UNKNOWN). The mini-grid test reads coverage at the
  runner's last recorded instant. A positive F01 detail through the route needs a ruling (pending rulings q4-1).
- Commit 2 accepts a Finding/Action link whose revision/event post-dates the command's DB instant (pending q4-2).
- Readings taken in this run: `.agent/W4-01-pending-rulings.md` "Run 5 readings".
