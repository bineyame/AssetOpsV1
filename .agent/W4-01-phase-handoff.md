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
