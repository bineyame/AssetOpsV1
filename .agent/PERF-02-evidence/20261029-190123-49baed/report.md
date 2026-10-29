# Backend run 20261029-190123-49baed

- wall: 2033 s (33.9 min)
- collected: 4132; JUnit cases: 4132; passed 4130, failed 2, skipped 0
- summed test time (JUnit): 9779.4 s
- phases: set-up 2382.4 s, call 7275.9 s, teardown 121.4 s; set-up share 0.244
- connections: peak server_total=132 client_backends=127 runner_sessions=126 assetops_test_dbs=126 samples=382
- memory: peak vm_used_mb=2473 vmmem_ws_mb=3750 runner_mem_mb=1867 pg_mem_mb=1250 runner_procs=24 runner_rss_sum_mb=1664 runner_rss_max_mb=313 min win_free_mb=2939 vm_total_mb=3918 samples=330

## Failed

- `tests.test_w303_portfolio_scope_snapshot_postgres::test_three_domains_same_window_cutoff_and_full_selection_ids`
- `tests.test_w303_selectors_postgres::test_portfolio_row_facts_and_verification_ids_match_stored_rows`

## Slowest 40 files (summed per-test phases)

| file | tests | set-up s | call s | teardown s | set-up share |
| --- | ---: | ---: | ---: | ---: | ---: |
| tests/test_w303_portfolio_scope_snapshot_postgres.py | 10 | 300.2 | 352.6 | 7.1 | 0.45 |
| tests/test_w403_opportunity_read_postgres.py | 10 | 5.3 | 561.6 | 0.0 | 0.01 |
| tests/test_w301_estate_index_postgres.py | 20 | 99.8 | 223.5 | 4.6 | 0.30 |
| tests/test_w403_replay_postgres.py | 2 | 10.5 | 270.5 | 0.0 | 0.04 |
| tests/test_w303_portfolio_comparison_postgres.py | 4 | 222.3 | 42.4 | 3.7 | 0.83 |
| tests/test_w403_scenarios_postgres.py | 10 | 3.1 | 226.7 | 0.0 | 0.01 |
| tests/test_w203_cold_replay_postgres.py | 14 | 0.1 | 219.9 | 4.6 | 0.00 |
| tests/test_w501_cold_depth_postgres.py | 12 | 0.1 | 185.9 | 2.5 | 0.00 |
| tests/test_w502_domain_intent_postgres.py | 11 | 164.2 | 8.1 | 2.9 | 0.94 |
| tests/test_s4_schedule_health_postgres.py | 9 | 17.0 | 152.5 | 2.8 | 0.10 |
| tests/test_w403_opportunity_worker_postgres.py | 5 | 2.7 | 169.3 | 0.0 | 0.02 |
| tests/test_w301_estate_golden_postgres.py | 6 | 0.0 | 159.5 | 0.8 | 0.00 |
| tests/test_s6_verification_evaluator_postgres.py | 11 | 24.3 | 125.7 | 0.3 | 0.16 |
| tests/test_w302_money_comparability_postgres.py | 6 | 0.0 | 136.6 | 1.4 | 0.00 |
| tests/test_w501_cold_scenarios_postgres.py | 7 | 5.9 | 130.5 | 1.1 | 0.04 |
| tests/test_s6_verification_holds_postgres.py | 7 | 15.3 | 112.2 | 0.3 | 0.12 |
| tests/test_w402_mini_stage_postgres.py | 3 | 6.1 | 121.5 | 0.0 | 0.05 |
| tests/test_cc_placement_postgres.py | 2 | 0.0 | 121.3 | 1.5 | 0.00 |
| tests/test_w204_cold_consequence.py | 35 | 0.1 | 119.4 | 1.7 | 0.00 |
| tests/test_w402_reads_postgres.py | 6 | 3.2 | 107.2 | 0.0 | 0.03 |
| tests/test_w206_ev_enqueue_postgres.py | 20 | 99.6 | 1.2 | 9.2 | 0.91 |
| tests/test_s4_evidence_decided_at_postgres.py | 10 | 19.0 | 85.9 | 2.5 | 0.18 |
| tests/test_s4_finding_evidence_history_postgres.py | 3 | 4.4 | 102.1 | 0.0 | 0.04 |
| tests/test_w402_replay_selection_postgres.py | 1 | 0.9 | 100.1 | 0.0 | 0.01 |
| tests/test_w204_cold_reads.py | 21 | 0.1 | 92.2 | 1.5 | 0.00 |
| tests/test_w206_ev_reads_postgres.py | 23 | 0.1 | 91.1 | 1.3 | 0.00 |
| tests/test_s6_action_apply_postgres.py | 12 | 20.3 | 71.7 | 0.1 | 0.22 |
| tests/test_w303_portfolio_fixture_postgres.py | 2 | 80.6 | 6.1 | 1.2 | 0.92 |
| tests/test_w205b_ev_replay_postgres.py | 13 | 0.1 | 86.5 | 1.2 | 0.00 |
| tests/test_s4_consequence_store_postgres.py | 13 | 66.5 | 16.2 | 3.6 | 0.77 |
| tests/test_s4_finding_index_postgres.py | 10 | 2.0 | 83.8 | 0.0 | 0.02 |
| tests/test_w203_cold_reads_postgres.py | 6 | 0.0 | 83.4 | 1.3 | 0.00 |
| tests/test_s4_evidence_consequence_work_postgres.py | 13 | 43.8 | 37.6 | 3.2 | 0.52 |
| tests/test_w207_ev_site_reads_postgres.py | 19 | 0.1 | 81.2 | 0.2 | 0.00 |
| tests/test_w502_domain_work_links_postgres.py | 5 | 28.8 | 51.8 | 0.5 | 0.36 |
| tests/test_s4_evidence_drain_postgres.py | 10 | 48.8 | 29.2 | 2.7 | 0.60 |
| tests/test_w207_ev_money_postgres.py | 14 | 21.9 | 53.5 | 5.2 | 0.27 |
| tests/test_w301_provenance_dto_postgres.py | 7 | 2.2 | 76.0 | 2.1 | 0.03 |
| tests/test_w403_opportunity_scan_postgres.py | 5 | 2.4 | 77.5 | 0.0 | 0.03 |
| tests/test_s6_action_store_postgres.py | 12 | 19.8 | 60.0 | 0.1 | 0.25 |

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
