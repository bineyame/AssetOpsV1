# OUT-E phase handoff (task/OUT-E-cost-proof)

Sheet: `C:\Users\assef\Bineyame\AssetOpsV1-plan2\.agent\build-sheet-OUT-E.md`. Status: E1-E5 built; review fixes in (2862e0b2); packet `.agent/OUT-E-packet.md`; only the `-Tier all` result line remains.

## Landed
- E1 `8e39626d`: CC-M merged; `0039_merge_objectives_cc` (down 0037+0038, empty); 20 head literals plus `mini_depth_probe` set to 0039;
  schema tests split HEAD from the migration under test (`TRIAL`, `OBJECTIVES`); only the 0036/0037 docstrings changed.
- E2 `0e849cba`: `verification_rules.window_evidence` gains `generator_kwh`; `financials/trial_fuel_comparison.py`;
  `tests/test_out_e2_trial_comparison.py`; `full_window(gen_kw="20")`.
- E3 `0ec2c147`: `financials/adapters/postgres_trial_comparison_store.py`; `financials/composition.build_trial_comparison_ports`;
  `VerificationPorts.trial_comparison`; `VerificationService._replay/_cost_check/_after_new_outcome` (hook in
  `evaluate` after a non-replayed new outcome in VERIFIED/INEFFECTIVE/INCONCLUSIVE); `PostgresActionStore.sfc_history`;
  guard `$trialComparisonWriter` + probes appended to `tools/checks/test_estate_guard.py`; s602b case `verified`
  (+ `publish_price_v1`, `VERIFIED_WINDOWS`); `complete_windows` gains 4 kW params and carries `trial_comparison`;
  test `test_out_e3_trial_comparison_postgres.py` + child `out_e_trial_child.py`.
- E4 `9517749e`: `summary()` adds `cost_check`, `trial_hours`; board `cost_line/trial_line/action_detail`, Earlier `detail`;
  mini Assure `VERIFIED_WITH_COST`; frontend `detail` small; tests `test_out_e4_readback.py`, `_postgres.py`, vitest.

## Next
- Run the DB tests: E1 set (`b8dv43ttg` log `scratchpad/outE/e1.log`), E3 postgres, E4 postgres, s602b users,
  `test_s6_verification_evaluator_postgres.py` (contract fixture may need `ASSETOPS_WRITE_S6_VERIFICATION_CONTRACT=1`
  for `generator_kwh`, `cost_check`, `trial_hours` keys only).
- check-all (PowerShell, ASSETOPS_GUARD_PYTHON set), then E5: captures, register R590-R594, full suites (ask coordinator).

## Risks
- Bash tool collapses `\\` to `\` in heredocs: write scripts with the Write tool when they hold backslashes.
- Guard self-tests take about 6 min (whole-tree copies) and need the PowerShell tool (execution policy).
