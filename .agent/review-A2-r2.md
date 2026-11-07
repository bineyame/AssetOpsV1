# Re-review A2 (FUEL-1), fix round: ACCEPT

Scope: fix commits a76926a14, 6f9ee6996 (main merge), 598fc0ab3, 48ae07eda against review-A2.md (H1, L1-L4) and ruling A2-R1.

- H1 closed. The golden diff (a76926a14) adds only `generator_idle_seconds: 0` (CH-9b2 x2, S6 x2) and `priced_total: null` (one cost_check each) to `ch9b2_reserve_trial_golden.json` and `s6_verification_api_contract.json`. Nothing else changed.
- L1 closed. `trial_fuel_comparison.py` stores `priced_total` only when `v2 and state == "MODELLED_IMPROVEMENT" and amount > 0`. The new test `test_improvement_with_more_fuel_in_the_later_hour_has_no_priced_total` builds a modelled improvement (per-kWh change positive) whose total fuel rose. Without the `amount > 0` condition the result would carry a negative-amount `priced_total`, so the `"priced_total" not in out` assertion fails. It is not vacuous (reasoned from code; the packet also records a 1-failed run when the condition was removed, which I did not re-run).
- L3 closed. The `cost_checks` docstring in `postgres_estate_read.py` is correct: a /2 row may store a priced total that the port does not read.
- L4 closed. `IDLE_SECONDS_UNKNOWN` reads "the generator's idle time is not known for one or both hours". The other reason words were not touched by the fix commits (diff shows only that line plus its comment).
- Main merge 6f9ee6996 brought in only the TEST-drift and DIESEL/FUEL planning material, which is not part of the A2 diff: status.py docstring, estate-week golden, ch5c2 clock guard, ch5a1 scope, probe tooling, .agent docs. No A2 file was altered by the merge. No unintended changes found.

Checks run (a2 worktree, `assetops_a2_test`, free RAM 4.2 GB):
`test_tfc2`, `test_ch3_rows`, `test_out_e4_readback`, `test_out_e3_trial_comparison_postgres`, `test_ch9b2_reserve_byte_equal_postgres`, `test_s6_action_records_postgres`: 81 passed, 212 s.

Not run: frontend suite, architecture/workflow guards, full backend suite (out of scope for this re-review).

Findings: none. Verdict: ACCEPT.
