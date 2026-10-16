# S4 deferred-match fix - handoff

Branch `fix/S4-deferred-match` (worktree `AssetOpsV1-review4`), not merged. Brief `.agent/S4-deferred-match-brief.md`.

## Root fix
- `analytics/finding_episode.py`: `plan_pass` returns `(writes, deferred_window_starts)`; `plan` is the unchanged
  writes-only wrapper. A group skipped for coverage or the 20-minute continuity margin defers every selected window
  (usable or not) touching `[lo - 20 min, hi + 20 min]` of its clusters and episodes (`_Site.margin_windows`). An
  episode whose closure `_unsupported_write` cannot decide is deferred the same way.
- `analytics/adapters/postgres_finding_store.py`: `apply(..., deferred=...)` records the starts on the pass
  (`finding_match_pass.deferred_window_starts`). `match_state` adds `match_deferred` and
  `matched = pass_seq >= window_seq and not deferred` against the latest pass.
- Migration `0018_finding_match_deferral` (down `0017_evidence_publication`) adds `timestamptz[] NOT NULL DEFAULT '{}'`.
  The table stays insert-only, and the column is written only by the existing Finding store writer (rule 8 unchanged).
  Downgrade is refused while any pass records a deferral. Head pins are updated in 5 tests.
- `finding_service.MatchOutcome.deferred_windows` and the s4 stage output `deferred_windows` are for observability only.
- No S5-01, S4-04 or upstream read code changed. The upstream seam's existing bracket-day
  `not matched -> ("S4","MATCH_PENDING")` now fires.
- Retry: a deferral clears only on a later pass. That pass runs because the neighbour's reassessment moves the
  fence (selection seq or recompute-job marker), so the tick's `SKIPPED_UNCHANGED_FENCE` does not apply. The tests
  prove this with the tick alone. Health `s4_backlog` is unchanged: a deferral is not matcher backlog.

## Proof
- `backend/tests/test_s4_deferred_match_postgres.py` (real PG): scenario A (S4-04 H1 sequence plus form 2), scenario
  B, and a test that persistent deferral is recorded on every pass and then cleared. Scenarios A and B read the
  production S5 Overview and `match_state`. They require pending (no CURRENT, no ABSENT, reason MATCH_PENDING)
  and then CURRENT with the correct Finding after `tick.tick()`.
- Pure test `test_s4_finding_episode.py::test_the_pass_names_the_windows_it_deferred`.
- Mutations (committed first, reverted with `git checkout`):
  - Dropping `and not deferred` in `match_state` made scenarios A and B fail with freshness CURRENT, reasons [].
  - Returning an empty deferred set from `plan_pass` made 4 tests fail.
- Focused (`-n 2`): deferred, lr01 money PG, finding episode/read/store/evidence-history/api, power demo,
  schedule health/tick/upstream, s5 overview PG/read: **135 passed in 404.5 s**.
- `tools/check-all.ps1`: 9/9 passed (temporary `.venv` junction, since removed).
- Full suite at `948efa74`, run from PowerShell with `-n 2 --dist loadfile --no-loadscope-reorder --junitxml`, private base `assetops_s4dm_test`: **2376 passed in 17:23 (wall 17:25, inside the 20-minute cap)**. JUnit: tests=2376, failures=0, errors=0, skipped=0. The `var/sites` yaml files were copied in for the run and removed afterwards.

## Open / risk
- Fail-closed effect: a day whose Candidate run is near an edge stays MATCH_PENDING while the neighbour is not
  CURRENT. This includes a cluster ending exactly at midnight before D+1 has ever been assessed, because
  `covered` fails there. It was already deferred before this fix, only hidden.
- S4-04 phase 2 (index) is in `AssetOpsV1-review`. Once this lands, its index `matched` check reads the deferral
  as well. Its own guard for form 2 (a newer neighbour selection) is still needed there.
