# Backend run 20261029-182418-74171c

- wall: 2158 s (36.0 min)
- collected: 4132; JUnit cases: 4132; passed 4130, failed 2, skipped 0
- summed test time (JUnit): 10457.6 s
- phases: set-up 2441.6 s, call 7879.4 s, teardown 137.1 s; set-up share 0.233
- connections: peak server_total=117 client_backends=112 runner_sessions=111 assetops_test_dbs=111 samples=408
- memory: peak vm_used_mb=2495 vmmem_ws_mb=3756 runner_mem_mb=1929 pg_mem_mb=1381 runner_procs=24 runner_rss_sum_mb=1675 runner_rss_max_mb=325 min win_free_mb=3026 vm_total_mb=3918 samples=351

## Failed

- `tests.test_w303_portfolio_scope_snapshot_postgres::test_three_domains_same_window_cutoff_and_full_selection_ids`
- `tests.test_w303_selectors_postgres::test_portfolio_row_facts_and_verification_ids_match_stored_rows`

## Slowest 40 files (summed per-test phases)

| file | tests | set-up s | call s | teardown s | set-up share |
| --- | ---: | ---: | ---: | ---: | ---: |
| tests/test_w303_portfolio_scope_snapshot_postgres.py | 10 | 295.0 | 346.1 | 7.9 | 0.45 |
| tests/test_w403_opportunity_read_postgres.py | 10 | 5.7 | 560.7 | 0.0 | 0.01 |
| tests/test_w301_estate_index_postgres.py | 20 | 100.0 | 221.1 | 4.1 | 0.31 |
| tests/test_w303_portfolio_comparison_postgres.py | 4 | 221.4 | 41.1 | 3.1 | 0.83 |
| tests/test_w403_replay_postgres.py | 2 | 10.6 | 249.0 | 0.0 | 0.04 |
| tests/test_w402_reads_postgres.py | 6 | 3.1 | 250.8 | 0.0 | 0.01 |
| tests/test_w205b_ev_replay_postgres.py | 13 | 0.1 | 231.9 | 2.5 | 0.00 |
| tests/test_w403_scenarios_postgres.py | 10 | 3.3 | 230.0 | 0.0 | 0.01 |
| tests/test_w203_cold_replay_postgres.py | 14 | 0.1 | 221.6 | 5.1 | 0.00 |
| tests/test_w206_ev_reads_postgres.py | 23 | 0.2 | 196.9 | 2.5 | 0.00 |
| tests/test_w501_cold_depth_postgres.py | 12 | 0.1 | 179.8 | 2.7 | 0.00 |
| tests/test_w403_opportunity_worker_postgres.py | 5 | 2.9 | 173.9 | 0.0 | 0.02 |
| tests/test_s4_schedule_health_postgres.py | 9 | 16.8 | 153.0 | 2.8 | 0.10 |
| tests/test_w502_domain_intent_postgres.py | 11 | 157.7 | 7.6 | 2.8 | 0.94 |
| tests/test_w301_estate_golden_postgres.py | 6 | 0.0 | 162.0 | 1.4 | 0.00 |
| tests/test_s6_verification_evaluator_postgres.py | 11 | 23.6 | 127.4 | 0.4 | 0.16 |
| tests/test_w206_ev_store_postgres.py | 13 | 0.1 | 148.0 | 1.5 | 0.00 |
| tests/test_w202_cold_replay_postgres.py | 12 | 0.1 | 136.8 | 3.6 | 0.00 |
| tests/test_w302_money_comparability_postgres.py | 6 | 0.0 | 135.9 | 1.7 | 0.00 |
| tests/test_w501_cold_scenarios_postgres.py | 7 | 5.3 | 129.7 | 1.7 | 0.04 |
| tests/test_cc_placement_postgres.py | 2 | 0.1 | 125.3 | 1.1 | 0.00 |
| tests/test_w402_mini_stage_postgres.py | 3 | 5.9 | 115.8 | 0.0 | 0.05 |
| tests/test_s6_verification_holds_postgres.py | 7 | 14.9 | 106.4 | 0.2 | 0.12 |
| tests/test_w204_cold_consequence.py | 35 | 0.1 | 119.5 | 1.8 | 0.00 |
| tests/test_w207_ev_money_postgres.py | 14 | 24.0 | 82.7 | 7.3 | 0.21 |
| tests/test_s4_evidence_decided_at_postgres.py | 10 | 18.8 | 90.5 | 3.2 | 0.17 |
| tests/test_w206_ev_enqueue_postgres.py | 20 | 97.4 | 1.0 | 8.4 | 0.91 |
| tests/test_r373_request_access.py | 10 | 55.8 | 46.5 | 0.8 | 0.54 |
| tests/test_s4_finding_evidence_history_postgres.py | 3 | 4.9 | 94.9 | 0.0 | 0.05 |
| tests/test_w402_replay_selection_postgres.py | 1 | 0.8 | 94.7 | 0.0 | 0.01 |
| tests/test_w504_ev_work_producer_postgres.py | 4 | 77.0 | 16.5 | 0.0 | 0.82 |
| tests/test_s6_action_apply_postgres.py | 12 | 21.4 | 71.9 | 0.1 | 0.23 |
| tests/test_w203_cold_reads_postgres.py | 6 | 0.0 | 89.2 | 1.1 | 0.00 |
| tests/test_w303_portfolio_fixture_postgres.py | 2 | 81.6 | 6.4 | 1.5 | 0.91 |
| tests/test_s4_finding_index_postgres.py | 10 | 1.9 | 85.7 | 0.0 | 0.02 |
| tests/test_s4_consequence_store_postgres.py | 13 | 67.9 | 16.2 | 3.4 | 0.78 |
| tests/test_s4_evidence_consequence_work_postgres.py | 13 | 43.5 | 39.4 | 4.4 | 0.50 |
| tests/test_w204_cold_reads.py | 21 | 0.1 | 84.5 | 1.5 | 0.00 |
| tests/test_s4_consequence_recompute_postgres.py | 13 | 66.6 | 15.3 | 2.9 | 0.79 |
| tests/test_s4_evidence_drain_postgres.py | 10 | 51.1 | 29.3 | 3.2 | 0.61 |

## Comparison with the baseline

```json
{
  "collected_identical": true,
  "collected_only_in_baseline": [],
  "collected_only_in_run": [],
  "cases_identical": true,
  "pass_only_in_baseline": [],
  "pass_only_in_run": [],
  "known_failures": {
    "tests.test_w303_portfolio_scope_snapshot_postgres::test_three_domains_same_window_cutoff_and_full_selection_ids": [
      "failed",
      "failed"
    ],
    "tests.test_w303_selectors_postgres::test_portfolio_row_facts_and_verification_ids_match_stored_rows": [
      "failed",
      "failed"
    ]
  },
  "skipped_in_run": [],
  "unexpected_failures": [],
  "proof_passes": true
}
```
