# C1 review: Portfolio lifecycle cutoff (D-E4.2)

Reviewer: fresh Claude (Opus), independent of the builder. Diff: `git diff main...task/E4-C1-portfolio-lifecycle-cutoff`
(merge base 1f40cca0d = main), commits fa0122bf3 and 484a8d344.

## Verdict: ACCEPT WITH NOTES

There are no High or Medium findings. The fix does what D-E4.2 asks, and only that.

## Questions settled

1. **Reading at the request cutoff k is correct.**
   - No future leak (R-1). Before the fix, `known_at` was the Site's evidence cutoff `site_cutoff(domain, None, rec.cutoff, k)`. That value is `max(decided_at) <= k` (`estate/index.py:151-156`, `postgres_estate_read.py:134`). The fix only widens the bound up to `k`, never past it.
   - `visible_at` is still `default`, the envelope's transaction-time `k` (`portfolio.py:162-163`). The port bounds state by `known_at` and occurrences by `visible_at` (`postgres_estate_read.py:353-368`). An event known after the viewed `k` stays hidden.
   - Same cutoff as the board and claims. `chain_api.py:185-187` and `chain/claims.py:84,97` read the lifecycle at `lifecycle_cutoff(k)`. The Portfolio now does too, through the same function (`portfolio.py:154`), with `day_at = req.to - 1us` as before.
   - `_thread_cutoff` and `_segment_no`/`_segment_at` all use that one key, so `action_segment_for` stays consistent.
2. **The edited assertions are legitimately re-pinned, not weakened.**
   - `test_ch2_threads.py:264-267` and `test_ch3_rows.py:306-310` each pinned a cold row's read at the evidence cutoff. Both now pin one call at `k`, with exact equality on fids, aids and `k`, which is stricter than before.
   - `test_ch3_rows.py:310` adds `_thread_cutoff == k`.
   - `test_ch5a1_r1_visibility.py:117-118`: `known_at` moves to `envelope_k`. The R-1 assertions (`visible_at == envelope_k`, shown or hidden by envelope) are unchanged.
   - All three are permitted by the card. No other assertion changed.
3. **`cutoffs` is now unused by `attach_threads`.** Its only caller is `_portfolio` (`portfolio.py:786`), and no test relies on it bounding the lifecycle. The card said to keep it, and the docstring documents it (`portfolio.py:140-141`). See L1.

## Findings

- **L1 (Low): `cutoffs` is dead API.**
  - Where: `backend/assetops_backend/estate/portfolio.py:136`, `:782-786`. The map is still filled at `estate/index.py:151-156`.
  - Cost: none. `rec.cutoff` is already recorded by the coverage read, so no extra query runs.
  - Fix: optional follow-up. Drop the parameter and the `cutoffs=` fill in `_portfolio`, or leave it as the card ruled. Not blocking.
- **L2 (Low): a test name no longer matches what it pins.**
  - Where: `backend/tests/test_ch3_rows.py:291`. `test_attach_threads_reads_actions_in_every_cutoff_group` now asserts a single group.
  - Fix: rename it, for example to `..._reads_actions_in_the_request_cutoff_group`. This is cosmetic.
- **L3 (Low): residual risk, which predates C1.**
  - The board passes the raw request `known_at` (`None` means live) to `lifecycle_cutoff`. The Portfolio passes the resolved `scope["k"]` (`read_at` when no cutoff is given).
  - These agree at read time but are not the same literal value. C1 does not change this.
  - D-E4.2's proof on a fresh build is still owed under D-E4.5: both Cold start-failure rows and the EV row should read "Pending", and Cold temperature should read "No action yet".

## Checks run (by me, on 484a8d344)

- No-DB tests: `test_e4_portfolio_lifecycle_cutoff`, `ch2_threads`, `ch3_rows`, `ch5a1_r1_visibility`, `w303_portfolio_workflow_labels`, `r4_domain_row_thread_state`, `w303_portfolio_api`, `cov_partial_portfolio`, `ch6b2_portfolio_cards`.
  - Result: **164 passed, 1 skipped**. The skip was the one Postgres case, with no DB URL set.
- Postgres consumers of `_portfolio`/`site_work_rows` (`attach_threads`): `w303_portfolio_api`, `qw2_many_postgres`, `cc_placement_postgres`, `w303_portfolio_fixture_postgres`, `w303_portfolio_scope_snapshot_postgres`, `cov_partial_postgres`, `out_b4_board_postgres`, `ch5a2_contract`.
  - Base DB: `assetops_test`, routed by the harness to run-owned `_pt*_test` clones.
  - Result: **54 passed, 1 xfailed, 0 failed** in 19m39s.
  - An earlier attempt used a non-existent base, `assetops_c1rev_test`. It errored on connection and is not counted.
- `tools/check-architecture.ps1`, run with no -ExecutionPolicy flag.
  - From a bash-spawned powershell, it was refused by the execution policy.
  - From the PowerShell tool, it ran but failed every Python-backed rule. The cause: the c1 worktree has no `.venv` ("no Python interpreter at '' or .venv").
  - With `ASSETOPS_GUARD_PYTHON` set to the plan2 venv python: **Architecture check passed**.
- Free RAM was at least 2.5 GB before each run. Monitor waited once, at 2.47 GB.

## Not verified

- I did not rerun the packet's non-vacuity claim (5 failed, 2 passed on main's `portfolio.py`), because the worktree is read-only for me. From the diff, main read cold/EV rows at `cutoffs[site]` (the last reading), so cases (a), (b) and (c) must fail there.
- No full suite, per the brief.
- No fresh-build Portfolio proof (D-E4.5).
