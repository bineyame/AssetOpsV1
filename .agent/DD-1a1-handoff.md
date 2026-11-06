# DD-1a1 handoff (builder 12: R9 landed and accepted on L2; R6/R3/mill/Q8/Cold not run)

## Landed (R8, builder 11)
- R8 stream epochs in `tools/demo_story_days.py` `resolve`; `_trial_chain(..., epoch)`; L0 33 passed; probe `tools/dd1a1_fullday_probe.py stream` and `tools/dd1a1_r8_check.py <db> stream|full`. Helpers in `C:\Users\assef\dd1a1w\` (env.sh, d12.sh, mkdb.py).

## Landed (R9, builder 12; main merged first)
- Product (`backend/assetops_backend/actions/verification.py`): `_baseline_facts` + `_day_states(..., facts_window=)`. A baseline pin whose current run differs is `moved` only when the INTERVAL assessments meeting [baseline_start, baseline_end) differ (key, claim level, full result); equal facts -> `reselected` (listed only when present, so the S6-02b contract is unchanged). Applied in `_assess`, `current_state` (baseline_days) and F2 attribution (baseline). New port `VerificationPorts.run_assessments` wired in `actions/composition.py` (`reads.store.run_detail`); missing port or unreadable run fails closed as moved. Pre-flight: no schema change.
- Unit: `backend/tests/test_dd1a1_r9_baseline_facts.py` 6 passed; mutation (facts always equal) fails 3. Existing verification files (s6 evaluator/holds, md0_fixture, out_b3, walk1) 122+1 passed after the conditional-key fix.
- Build order (`tools/demo_combined_kobo.py`): `_trial_chain(..., admit)` admits later complements by received_at before the freeze, before the later run and before the evaluation. ACT-K1 steps/instants unchanged.
- `tools/dd1a1_r9_check.py <db>`: post-freeze baseline re-selections have equal facts; outcome VERIFIED; `reselected` iff run changed.

## L2 done (builder 12)
- R8 probe + full with/without: VERIFIED, r8/r9/r7 checks PASS, 0 AMBIGUOUS, compare EQUAL on Findings (final state), action, metrics (Q6), outcome. Details in `.agent/review-packet-DD-1a1.md`. Guards V, A, W, N, M pass (M needs NODE_PATH=plan2 frontend/node_modules). All DBs dropped, no processes.

## Next (resume here)
- R6 degraded check (`tools/dd1a1_degraded_check.py with|without|compare`, own DB each, one at a time), the five R3 L2 checks (need with/without nights builds), the mill day (0 generator starts, CH-9b mill outcome), Q8 cost per full Kobo/Cold day, the Cold failure day. No tooling yet beyond the builds. Then complete the packet's Open section.
