# FIX-01 packet (PARTIAL: regression runs paused at coordinator request)

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

## NOT YET RUN (paused on coordinator hold, OUT-W full run in container)
w301*/w302*/w303* files, test_post_w6_w3_estate_links, `tools\check-all.ps1`.
Script to resume: `$TEMP/runall.sh` pattern; run each file in its own invocation.
