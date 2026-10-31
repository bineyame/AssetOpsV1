# FIX-01 packet (final)

Task: estate day reads 409 when one Finding has two revisions across two selected windows (diagnosis: `.agent/FIX-01-diagnosis.md`).

## Delivered
- `estate/coverage.py::_windowed`: across a day's selected windows the highest `revision_no` of a Finding wins; the same
  revision id in two windows is no conflict (the later `(selected_at, seq, selection_id)` copy is held); equal
  `revision_no` with different ids (fork), a missing `revision_no`, and two revisions inside one window still raise.
  The episode-intersection filter runs before the dedupe. Site sets (`selected_assessment_revision_ids`, window evidence
  ids, `selection_id`) remain unions over all windows; each row cites only its winning revision's evidence.
- `estate/adapters/postgres_estate_read.py`: `revision_no` added to the EV and cold window rows.
- `estate/index.py::_finding_links`: counts only windows holding the winning `finding_revision_id`, so the link is no longer null.
- Register: R577 added as `resolved by FIX-01` (this branch did not carry it).

## Tests
- `backend/tests/test_fix01_windowed_dedupe.py` (11 unit tests, EV and cold synthetic): supersession both orders, higher
  revision from the earlier selection, same revision twice, fork raises, missing revision_no raises, two revisions in one
  window raise, episode filter before dedupe, link opens the winning window (and the superseded revision's window for the old id).
- `backend/tests/test_fix01_estate_two_revisions_postgres.py` (EV replay `interrupted` + `select_exact`): 200 on findings and
  evidence for the day, one row at revision_no 2, link href holds [08:00, 09:00) not 09:05, 2 selected windows, day before empty.
- `backend/tests/test_fix01_cold_estate_postgres.py`: cold late reselection reads 200, one row per Finding.
- Non-vacuity: planting the old logic (units: old raise and old link filter; guards: removed fork/one-window/missing-no checks)
  fails 6 + 3 unit tests; planting main's `coverage.py`+`index.py` fails the EV Postgres test (1 failed). Source restored by `git checkout`.

## Cold (ruling 3)
Neither alternative holds cleanly. Cold CAN in principle overlap: `cold_windows` (`postgres_assessment_store.py:1177`) merges a
job window with all selected cold windows within the bridge into one new window and never retires older selections. The
registered cold replay re-selects the same exact bounds, so it yields one selected window (probe: one window, 200). A real
cold overlap needs a fixture that does not exist; the shared guard is proven on synthetic cold windows. Recorded as a deviation.

## Checks run so far (real Postgres, one file at a time, plan2 venv)
- test_fix01_estate_two_revisions_postgres.py: 1 passed. test_fix01_cold_estate_postgres.py: 1 passed. Units: 11 passed.
- test_out_b4_board_postgres.py (w504 board, covering-day portfolio): 5 passed (296 s).
- test_out_c4_ev_warnings_postgres.py (w504 warnings): 1 passed (115 s).

## Final regression results (real Postgres, one file at a time, plan2 venv, after OUT-W's run finished)
All of test_w301_* (8 files), test_w302_* (10 files), test_w303_* (9 files) passed, each in its own run: e.g.
estate_index_postgres 20 passed, estate_index_ev 4, golden 6, evidence_ev 4, pinned_facades_postgres 8,
portfolio_comparison 4 (393 s), portfolio_scope_snapshot 10 (718 s). Zero failures, zero errors.
- `test_post_w6_w3_estate_links.py`: 1 failed on the first run. The test's `window()` double built Finding rows with only
  `finding_id`; the link now matches on `finding_revision_id` (real window rows always carry it). Fixed the double to
  carry `finding_revision_id`; 7 passed.
- `tools\check-all.ps1` (ASSETOPS_GUARD_PYTHON = plan2 venv, no -ExecutionPolicy): 9 of 11 guards PASS (estate guard
  self-tests, navigation, agent workflow, dependency registry incl. register, delivery, mock-gap, evidence width, screen
  ledger). 2 FAIL, both environmental: "Missing-claim orphan scan" and "Missing-claim scan fixtures" exit 1 with Node
  MODULE_NOT_FOUND (`frontend/package.json` require stack): this worktree has no installed frontend `node_modules`. They
  touch no FIX-01 file. Needs `npm ci` in `frontend` (not done here) and a re-run before merge.

## Post-merge (main 9ebb3d1c merged; head after this commit)
- Conflict: only `.agent/mock-departure-register.md` (R575/R576/R577). Kept main's R575 and R576; kept FIX-01's R577 row
  (resolved by FIX-01) in place of main's open R577. `site_selected_windows` and `summary()` merged without conflict.
- OUT-C4 EV test flipped: 6 Oct summary now 200, Depot `window_basis == "LATEST_EVENT"`, href starts `/sites/EV-LAB-001/ev?from=` and
  holds `&to=`. 8 Oct PERIOD assertion unchanged. Deviation: the Depot window is not exactly E [08:00, 09:00). OUT-W's
  `latest_window` takes max window_end, which is the reselected window [08:00, 09:05) holding the superseding revision.
  The test asserts from == E.from and to >= E.to. The Protect-equals-board check was not added (summary row shape differs).
- Results on the merged head, one file at a time, real Postgres, plan2 venv: out_c4_ev_warnings 1 passed (69 s); fix01_estate_two_revisions 1 passed (52 s);
  fix01_cold_estate 1 passed (30 s); out_c3_repeat_visits 1 passed (55 s); out_b4_board 5 passed (182 s);
  non-Postgres out_w1*, out_w2*, fix01_windowed_dedupe: 34 passed.
- `tools\check-all.ps1` (ASSETOPS_GUARD_PYTHON = plan2 venv): All 11 guards passed.
