# FX-COLD-LINKED review packet

Task: DS-1f ruling D-E5.8 (build sheet OWN-GAPS, "DS-1f anomaly rulings (2026-11-10)", commit 12b5b37f1).
Branch `task/FX-COLD-LINKED` from main `12b5b37f1`; fix commit `bcdf5389b`.

## Outcome
A later clean Cold assessment inside the window no longer drops the open start-failure Finding, so the repeat-visit
warning (REPEATED_MAINTENANCE_NO_RESULT) still fires and the Maintenance "Repeat visits" card cannot say "None found".

## Files
- `backend/assetops_backend/site_outcomes/cold.py`: `ColdPorts.finding` (default returns None, so existing fakes
  stay valid); after the Action read, the EV block (`ev.py:149-162`) mirrored: each Action-origin or visit-linked
  Finding id missing from `cold_findings` is read by id; a refused read sets `findings_ok = False` (unsettles CC-3
  and every finding-moved outcome) and lists `cold_findings` in `reads.failed`. The Actions line moved above the
  Finding build (no behaviour change).
- `backend/assetops_backend/site_outcomes/read.py` `cold_ports`: binds `finding` to `cold_reads.linked_finding`.
- `backend/assetops_backend/analytics/adapters/postgres_assessment_store.py` `ColdReadService.linked_finding`: the
  card's "id read that does not" filter by the snapshot. `cold_reads.finding` was unusable: it returns None when
  the anchor lies outside `[lo, hi)` (`_finding_ids`). The new read takes the Finding by tenant/Site/domain/id and its
  latest revision with `knowledge_cutoff <= known_at` (else the ingestion watermark), reusing `_revisions` and `_item`.
- Tests: `backend/tests/test_fx_cold_linked.py` (3 unit), `backend/tests/test_fx_cold_linked_postgres.py` (1).

## Acceptance (D-E5.8)
- Mirror EV block, new `ColdPorts.finding` bound in `cold_ports`: met.
- Refused read unsettles CC-3 and lists `cold_findings`: met (unit test 2).
- Read independent of the selected assessment, as of `known_at`: met (new store read).
- Unit test with a later clean assessment, warning still fires, cites the Finding: met (unit 1; the fixture visit is
  MR-005, not WR-006).
- Postgres summary test over a window containing a clean post-failure day: met. w502 `positive` build (failure D
  16:00), then one clean `cold-normal` replay at D 18:00 through `demo_combined_cold.run_day` (the add-day path).
  The summary over `[D, D+1)` reads Cold on the clean window (asserted via the selected-window spy: 2 windows, the
  latest is 18:00). Assertions: one REPEATED warning for COLD-LAB-001 with count 3, fault "automatic start failure",
  a FINDING evidence ref, Cost NEEDS_ATTENTION on CC-3; the Site board over the day and over the clean window alone
  also carry the warning.

## Fails on main (proved, then restored with `git checkout HEAD --`)
- Postgres test on main's three source files: `AssertionError ... assert (0 == 1)`, no REPEATED warning in the
  summary; the board record shows `cold_findings rows 0` on the clean window.
- Unit tests on main: `TypeError: ColdPorts.__init__() got an unexpected keyword argument 'finding'` (main has no
  port; an API failure, not a behavioural one; the Postgres test is the behavioural proof).

## Checks (host, worktree PYTHONPATH, `assetops_test` base, one file at a time)
- test_fx_cold_linked 3 passed; test_out_b3_cold_ev 28; test_out_c3_cold_cost 6; test_out_c_rules 17;
  test_out_c2_board 13; test_out_d4_board 17; test_out_b4_window 9; test_ch6b1_r5_dated_lead 2;
  test_out_w2_summary_window 9; test_out_b2_vocabulary 4 - all passed.
- Postgres: test_out_c3_repeat_visits_postgres 1 passed (79 s); test_fx_cold_linked_postgres 1 passed (111 s on
  the fix; 97 s on the rerun after restoring the fix).
- No full suite (demo-sprint policy).

## Known deviations / notes
- The resolved Finding's links use the window of the analytic run that wrote its revision (it lies outside the
  board's clean window, so the board window would give a dead Finding link).
- A resolved Finding outside the window keeps `in_window = False`, so Protect does not claim a start failure in a
  clean window (asserted in unit 1); only the repeat warning and Cost row use it.
- Mini check (report only, not widened): mini reads Findings from `chain_findings` over the 31-day work window, not
  a single selected assessment, so the D-E5.8 gap does not occur there as such; a linked Finding whose anchor is
  31-60 days before the end (visits count over 60 days) would still be absent.

## Residual risk
- The Postgres test's clean run uses wall-clock receipt and a wall-clock worker (`story_clock=False`), like add-day.
- Backend change: needs the 11-11 rebuild (D-E5.10). USER_REVIEW: fresh Claude review per D-E5.10.
