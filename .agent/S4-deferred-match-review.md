# S4 deferred-match fix - independent review

Reviewer: fresh Claude reviewer, not the author. Worktree `AssetOpsV1-gap-planning`, branch `review/S4-deferred-match`
at fix head `75c2d65b`. Diff `28324074..75c2d65b`. That is the merge-base with main. Main has since moved to `7f877bc8`
with a log-only commit, which explains the 6-line `.agent/owner-autonomy` difference in a two-dot diff. Python is the
main venv with `PYTHONPATH` set to this worktree. `assetops_backend.__file__` resolves to
`AssetOpsV1-gap-planning\backend\assetops_backend\__init__.py`.

## Verdict

**Accept.** There are no High or Medium findings. The three Low findings below do not block.

## What I verified

- **Root, fail-closed.** `plan_pass` defers in the two places where a group is left unmatched:
  - The coverage/margin skip (`finding_episode.py:728-734`). It defers every *selected* window, usable or not, that
    touches `[lo-20m, hi+20m]` of each cluster and episode. That set includes the CURRENT deferring day and the
    non-CURRENT neighbour.
  - The episode-only branch when `_unsupported_write` returns None, i.e. a closure that cannot be decided (`:738-739`).

  The other branches all produce writes, so nothing else is left unmatched silently. `match_state` reads
  `:w = ANY(deferred_window_starts)` on the latest pass only, and `matched` now also requires that the window was
  not deferred. A neighbour with no selection already reads `matched=false` (`seq is None`), so fail-closed holds
  without recording it.
- **No stuck state.** A deferral is cleared only by a later pass. I checked the fence argument against
  `PostgresFindingStore._fence`, which is the Site max selection seq plus a recompute_job count, `max(created_at)`
  and an ordered status string, plus the revision count. It also matches `stages.s4`, which skips only when that
  fence and the matcher version are unchanged. When the neighbour is reassessed, the recompute job is created and
  changes status, and the new selection raises the seq. Each of these moves the fence, so the tick does not return
  `SKIPPED_UNCHANGED_FENCE`. Scenario A and scenario B clear the deferral with `tick.tick()` alone, and they pass.
- **Consumers, checked by reading the code.**
  - Upstream seam (`upstream.py:132`): the bracket-day `not matched -> S4 MATCH_PENDING` now fires.
  - S5-01 `site_overview/read.py`: unchanged. It goes through the seam.
  - `finding_read.window_state:631`: a deferred no-candidate day reads `FINDING_MATCH_PENDING`, which is correct.
  - `money_eligibility:121`: a deferred day adds `MATCH_PENDING`, which is fail-closed and more conservative.
  - `health.py:240`: uses only `matched_through_selection_seq` with `_EPOCH`, so it is unaffected.
  - S4-04 phase-1 index on `task/S4-04-site-finding-index`: does **not** use `match_state`. See L1.
- **Migration 0018.** Checked on a scratch DB, which I dropped afterwards:
  - Single head `0018_finding_match_deferral`, down revision `0017_evidence_publication`. No other in-flight branch
    has an 0018 or 0019 migration (main, S4-04, OPS-02, S6-01b).
  - Existing and new rows default to `{}`.
  - An empty downgrade succeeds to 0017.
  - With one deferral row, the downgrade is refused with the RAISE message and the version stays at 0018.
  - An UPDATE is still refused by the 0009 append-only trigger.
- **Rule 8.** The only writer is still `postgres_finding_store.py`. `finding_match_pass` is already in its
  statement-level table list (`tools/checks/configuration-persistence.ps1:651-653`), and `tools/` is untouched.
  `check-architecture` passes.
- **Tests reproduce the evidence.** Scenario A is the S4-04 H1 sequence plus form 2 (neighbour reassessed, no
  rematch). Scenario B is an earlier Finding with a later deferred edge cluster. Both read the production Overview
  and `match_state`, and require no CURRENT, no ABSENT, and MATCH_PENDING, then CURRENT with the correct Finding
  after the tick. The persistence test checks pass rows `[2, 2, 0]`.
- **My own mutation.** I removed `and not deferred` from `match_state` and reverted it with `git checkout`, and the
  tree is clean. Result: scenario A and scenario B fail with `{'state': 'CURRENT', ..., 'reasons': []}`, and the
  persistence test passes, which is expected because it asserts `match_deferred`. The fix is what makes the tests
  pass.

## Findings

### L1 (Low, handoff accuracy and integration note) - the S4-04 index does not read the deferral

`.agent/S4-deferred-match-handoff.md`, "Open / risk", second bullet, says: "Once this lands, its index `matched`
check reads the deferral as well." On `task/S4-04-site-finding-index` that is not true. `finding_index.py:240`
computes `matched` from its own `index_snapshot` pass row, and `postgres_finding_store.py:~463` on that branch
selects only `id, selection_seq, completed_at`. It never calls `match_state`.

This does not block, for two reasons. Phase 2's `candidate_reach` (S3 Candidate within 20 minutes of an edge)
inspects the neighbour, and that neighbour's STALE or MATCH_PENDING state blocks CURRENT independently. And the
fix on this branch is correct for every `match_state` consumer on main.

Fix: correct the handoff sentence. When S4-04 rebases, it should either select `deferred_window_starts` in
`index_snapshot` and AND it into `matched` per day, or call `match_state`, so that there is one definition of
"matched". Expect a textual conflict in `postgres_finding_store.py`.

### L2 (Low, missing test) - 0018 downgrade refusal is not tested in the suite

The existing migration tests only update head pins. I exercised the refusal manually (above). A small test,
modelled on `TestMigrationPaths`, would keep that behaviour from regressing.

### L3 (Low, nit) - lost line continuation in a test

`backend/tests/test_s4_finding_episode.py:206` has a ~160-character line with a run of spaces inside the
expression, apparently where a continuation was lost. It is valid Python. Rewrap it.

## Checks run

- Focused, `-n 2`, private DB `assetops_s4dmrev_test` (dropped afterwards). Files: test_s4_deferred_match_postgres,
  test_s4_finding_episode, test_s4_schedule_upstream_unit, test_s4_schedule_health_postgres,
  test_s4_schedule_tick_postgres, test_s5_overview_postgres, test_s5_overview_read,
  test_lr01_money_eligibility_postgres, test_s4_evidence_consequence_work_postgres::TestMigrationPaths, and
  test_s4_finding_store_postgres. Result: **114 passed in 341 s**.
  - My first attempt errored at setup (34 errors) because I had not created the base DB. That was my setup mistake,
    not a code defect.
- Mutation (above): 2 failed, 1 passed, as expected.
- Migration scratch script (above): all expectations held.
- `tools/check-architecture.ps1`: passed. `tools/check-agent-workflow.ps1`: passed.
  `ASSETOPS_GUARD_PYTHON` was set to the main venv python.
- Full suite: not rerun. Cited: the implementer ran it at `948efa74`, the fix commit, which carries all code under
  review (`75c2d65b` adds only the handoff). Result: JUnit tests=2376, failures=0, errors=0, skipped=0, 17:23
  (wall 17:25), with `-n 2 --dist loadfile`.
- Frontend: no frontend change in the diff, so I did not run `tsc`, the frontend suite or the build. No layout
  evidence is needed.
- Not verified: `tools/check-all.ps1`. I cite the implementer's 9/9.

## Residual risk not named in the packet

- **Health shows IDLE while a window is deferred and pending.** `s4_backlog` ignores deferral (by design). If the
  neighbour never becomes CURRENT, D stays MATCH_PENDING and no S4 alarm fires. Examples are a cluster ending at
  exactly midnight while D+1 never receives data, or a neighbour that stays on another model. When the neighbour is
  STALE with no job, the existing `S3_STALE_NO_JOB` alarm shows it. When it is UNASSESSED, nothing shows it. This is
  honest pending, and it falls within the accepted "longer pending" residual.
- **Deferral is coarse.** A whole window is deferred even when only one group in it is pending. As a result, money
  eligibility for an unrelated, fully matched episode on that day also reads MATCH_PENDING. This is fail-closed, not
  wrong.
- **A pass is not deterministic from the fence alone.** Window S3 status also depends on the input hash, which is
  not in the fence. If a neighbour flipped from STALE back to CURRENT without any job or selection change, no new
  pass would run and the deferral would remain. The fence design already has this property (S4-02d). The fix makes
  it visible as pending rather than hidden.
