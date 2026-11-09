# Review: OWN-G1 add-dates (re-review of the H1 fix round)

Reviewer: fresh Claude, not the author. Branch `task/OWN-G1-add-dates`, diff `ddbdaa044..fc6545de4`.

## Verdict: ACCEPT WITH NOTES (no High or Medium; two Low notes, neither blocks merge)

Checks run: `test_own_g1_add_dates.py` + `test_k7_kisiwa_story.py`: 143 passed (7 s), matching the packet. The plan2 venv needs
PYTHONPATH to include this worktree's backend, backend/tests, tools, contracts, simulator, gateway, host and field; with only
backend/tools, assetops_contracts and assetops_simulator resolve to another checkout and 14 K7 tests fail on import (environment, not code).
I did not run the wider no-DB set. No DB, no code edits. Diff touches only tools/, the G1 test file, packet and CODE_STATE:
nothing under backend/assetops_backend, host or frontend.

## 1. H1 closed: yes
- `tools/demo_combined.py:420-424`: Kisiwa default start is now max(last story night, last DONE night) + 1, so the earliest
  PUBLISHED night is the first planned date and goes through the existing resume branch. `--from` beyond a stuck night is
  measured from the same point, so it raises GAP_NOT_ALLOWED (asserted in `test_planner_resumes_a_published_night_first`).
  `--from` at/before the stuck night resumes it. A ranged `--to` cannot skip it (the range starts at the stuck night).
- `tools/demo_combined_kisiwa.py` `plan_night` (+4 lines): a new night with an earlier PUBLISHED entry raises
  NIGHT_NOT_FINISHED before any write (plan_night runs before `_publish_night`; `add_night` writes nothing earlier).
  Message names the night and `--from <date>`.
- Multi-site: Kisiwa is planned and refused in the same up-front plan as core sites, and the planner path is shared, so a
  stuck Kisiwa night is resumed first in date-major order; a mid-run child refusal now prints what was already added (L3).
- ADD_NIGHT_UNEXPECTED case: the night stays PUBLISHED, the next default run re-verifies it and raises again. Honest.
- Residual edge (Low, L-A): in `plan_night` the resume branch for a PUBLISHED `night` returns before the new stuck check,
  so a direct child call for a later PUBLISHED night while an earlier one is PUBLISHED would resume it. Not reachable through
  the planner (GAP_NOT_ALLOWED / earliest-first), only by hand-driving the child or a build already holding two PUBLISHED
  nights from the old code. Optional: apply the stuck check to the resume branch too (needs a one-line test).

## 2. Changed existing test: not a weakening
`test_plan_night_refusals_and_resume` now asserts chaining from a DONE night still yields the carried start state, and that
the same call with a PUBLISHED predecessor refuses NIGHT_NOT_FINISHED. This is the intended rule (never build on an unverified
night); the old assertion encoded the bug. Strictly stronger: positive and negative cases both present.

## 3. L5 dry-run preflight: acceptable
Running the preflight first is correct: a dry run must not show a plan the real run would refuse. The preflight is
read-only (one invalid POST rejected 422, no DB row; docstring "Writes nothing"). Its only residue is the child's log file under
`<work>/logs`, the same as any child run; no `.busy`, no add, drain, tick. Wording "nothing added" is accurate. Note (Low, L-B):
the dry-run tests mock `kisiwa_child`, so the log file claim and "dry run now needs a reachable DB/serve env" are untested; state
that in the packet or the CLI help so an owner running `--dry-run` offline is not surprised.

## 4. L2, L3, L4: correct and tested
- L2 `test_wk6_calls_study_ending` is a source-text assertion (exact call string, no `max(`). Brittle to reformatting, but it
  fails loudly and fixes the unguarded regression; acceptable for a no-DB guard.
- L3 `except BaseException` prints the partial added list then re-raises; `.busy` still released in `finally`; test asserts 7 Nov
  listed and 8 Nov not.
- L4 prefix tuple covers "mini-depth FAILED"; test checks wording and that finish_check is not called.
- L1 packet/CODE_STATE wording corrected.

## 5. Coverage: no-DB is enough to merge
The new rules are pure decisions (planner date selection, `plan_night` ordering) with must-fail tests, and the fix changes no
I/O, DB or product code. The earlier DB rehearsal (runs A/B) exercised the unchanged write/verify path. A targeted DB rehearsal
(leave a night PUBLISHED, re-run, see it resumed and verified) would be a nice owner-demo confidence step but is not required
before merge; I would do it only as part of the next fresh-build demo prep.

## Residual risk
Resume of a PUBLISHED night re-posts records at step 5 (existing behaviour, unchanged); correctness of that against a real
crash between steps 4 and 5 remains proven only by the original rehearsal and unit tests, not a forced-crash DB run.
