# C1 review packet: Portfolio lifecycle cutoff (D-E4.2)

Branch `task/E4-C1-portfolio-lifecycle-cutoff`, from main 1f40cca0d. Spec: build sheet "E4 stop rulings", D-E4.2 Fix.

## Outcome
`estate/portfolio.attach_threads` reads every row's thread state and Action segments at
`chain.read.lifecycle_cutoff(default)` (the request cutoff `k`), in one port call, not one call per Site cutoff.
`day_at` and `visible_at` are unchanged. `_thread_cutoff` is set to the same value, so `action_segment_for` stays
consistent. The `cutoffs` parameter is kept; it no longer bounds the lifecycle. The comment cites CH6b2-R2 and D-E4.2.
`default` is now computed before the `port` guard, which also removes a latent NameError when there is no port and
there are Action rows.

## Files
- `backend/assetops_backend/estate/portfolio.py`: attach_threads, plus the `lifecycle_cutoff` import.
- `backend/tests/test_e4_portfolio_lifecycle_cutoff.py` (new, no DB). The fake `threads` port records kwargs and
  returns ACTION_IN_HAND only when `known_at >= 09:40Z`. Cases: (a)/(c) Cold and EV rows read at `known_at == k`, not
  at the 09:00Z last reading; (b)/(c) both rows read "Pending"; an OPEN thread keeps "No action agreed yet"; (d) the
  mini row's call kwargs are unchanged; rows of all three domains are read in one group.

## Updated assertions (all pinned a Cold/EV read at the evidence cutoff; permitted by the card)
- `test_ch2_threads.py` (cutoff test, tail): two calls `[(f1, row_k), (f2, k)]` become one call `(f1+f2, k)`.
- `test_ch3_rows.py::test_attach_threads_reads_actions_in_every_cutoff_group`: two calls become one; `_segment_at` is
  `{k: 2}` (was `{k: 2, cold_k: 1}`).
- `test_ch5a1_r1_visibility.py`: `known_at == STORY_CUTOFF` becomes `== envelope_k`. The visibility assertions
  (`visible_at == envelope_k`, shown or hidden by envelope) are unchanged: CH5a1-R2 R-1 does not move.

## Checks
- Targeted run: e4 (new), ch2, ch3, ch5a1_r1, w303_portfolio_workflow_labels, r4: **90 passed, 0 skipped**.
- Non-vacuity: the new file on main's portfolio.py gives 5 failed and 2 passed (the passing ones are the mini row and
  the OPEN row, which are expected to pass on both). Restored with `git checkout HEAD`.
- Not run: full suite (per the brief). The proof on a fresh build is D-E4.5/E4 work.

## Deviations
None.

## Residual risk
`lifecycle_cutoff` is the identity, so `_segment_no` and `_segment_at` share one key. If it ever diverges from `k`,
`visible_at` still uses `default`, as R-1 requires.
