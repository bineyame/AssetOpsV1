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
- `tools/check-architecture.ps1` passed (with `ASSETOPS_GUARD_PYTHON` set to the plan2 venv; without it the worktree
  has no `.venv` and the guard refuses).
- No full suite (demo-sprint policy).

## Fix round 1 (review REJECT b95fe8587: H1, M3)
- H1 fix `1b0fdb61f`, in the `cold.py` compose and `_finding(..., selected=)`: a row that only the linked re-read
  returned gets `in_window = False`, whatever its episode bounds. The earlier note ("keeps `in_window = False`") held
  only for the unit fixture. Real START_RESPONSE revisions have NULL bounds, so they counted as in-window.
- Approach: forced off, not judged by anchor time. The selection's read (`_finding_ids`) already returns every
  Finding anchored in the window that has a revision by k. A Finding missing from that read is therefore not this
  window's Finding, as known at k. The store applies that one rule, and the composer does not re-derive it. Judging
  by anchor would let a day board claim the 16:00 failure while its overview and Protect come from the clean 18:00
  selection, which mixes two assessments. The linked rows still feed the REPEATED warning (`open_findings` uses
  `open`, not `in_window`), CC-3, and Action/case link resolution.
- M3 tests (`b08d0bcc6`, `9a47f04f3`):
  - Unit `test_linked_finding_with_null_bounds_never_counts_in_the_clean_window` (NULL bounds): no FINDING issue on
    any row; the Protect subline is `PROTECT_SUBLINE` and Protect is not NEEDS_ATTENTION; Cost is still
    NEEDS_ATTENTION; the warning is present.
  - Postgres: no FINDING issue on the clean board or the day board; Protect is not the start subline; the summary
    Protect state equals the clean board's.
  - Postgres, COH-4 run in process: `chain_coherence.coh4_findings_contain` over a one-day bundle (the day board
    plus `/api/estate/findings` for that day) returns [].
- Fail-before proof (branch with the tests committed and the fix absent):
  - Unit: `AssertionError`, because OPTIMIZE_COST carries the FINDING issue "Backup did not start - checked here as
    a safeguard".
  - Postgres: `AssertionError` with three board FINDING issues (Cost and Protect for the start failure, Protect for
    the excursion). At head the clean board's states were [NOT_MEASURED, NEEDS_ATTENTION, NEEDS_ATTENTION, WATCH].
- COH-4 note: the estate list takes midnight bounds only, and at head the day list held both Findings. So the
  day-pair COH-4 would not actually have fired. The false Protect claim was real; the COH-4 risk was inferred.
- Checks after the fix (all passed): test_fx_cold_linked 4, test_out_b3_cold_ev 28, test_out_c_rules 17,
  test_out_c2_board 13, test_out_c3_cold_cost 6, test_out_d4_board 17, test_out_b4_window 9,
  tools/checks/test_chain_coherence 181.
- Postgres via `tools/run-host-tests.ps1`: test_fx_cold_linked_postgres 1 passed (85.5 s); test_out_c3_repeat_visits_postgres
  1 passed (80.7 s). `tools/check-architecture.ps1` (with `ASSETOPS_GUARD_PYTHON`): "Architecture check passed."
  No full suite (demo-sprint policy). USER_REVIEW: fresh Claude re-review.

## Known deviations / notes
- The resolved Finding's links use the window of the analytic run that wrote its revision (it lies outside the
  board's clean window, so the board window would give a dead Finding link).
- After the fix, Action/case rows on clean windows resolve their linked Finding, so they lose the
  " · linked finding outside this view" suffix. That is the review's residual risk: EV-like and intended.
- Mini check (report only, not widened): mini reads Findings from `chain_findings` over the 31-day work window, not
  a single selected assessment, so the D-E5.8 gap does not occur there as such; a linked Finding whose anchor is
  31-60 days before the end (visits count over 60 days) would still be absent.

## Residual risk
- The Postgres test's clean run uses wall-clock receipt and a wall-clock worker (`story_clock=False`), like add-day.
- Backend change: needs the 11-11 rebuild (D-E5.10). USER_REVIEW: fresh Claude review per D-E5.10.
