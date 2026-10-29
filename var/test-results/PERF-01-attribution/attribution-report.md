# PERF-01 measured time attribution

## Run 20261029-075935-ad347d

- pytest wall 3759 s; 4132 tests on 4 workers; first test start to last test end 3690.0 s
- measured test time (sum of set-up + call + teardown) 14520.4 s; attributed 14520.4 s; unattributed -0.01 s
- worker idle inside the span (workers x span - measured) 239.6 s
- memory: peak vm_used_mb=2453 vmmem_ws_mb=3147 runner_mem_mb=2087 pg_mem_mb=677 runner_procs=21 runner_rss_sum_mb=1480 runner_rss_max_mb=336 min win_free_mb=3273 vm_total_mb=3918 samples=655
- instrumentation: {'wrapped_calls': 132964, 'statements': 3270685, 'overhead_s_estimate': 4.4}

| part | seconds | share of measured | wall-equivalent min (/ workers) |
| --- | ---: | ---: | ---: |
| DB create/clone/drop + migrations | 653.4 | 4.5% | 2.7 |
| Site/Foundation install + credentials | 255.1 | 1.8% | 1.1 |
| gateway subprocess start/stop | 667.3 | 4.6% | 2.8 |
| replay / ingest / seed (site build) | 10072.4 | 69.4% | 42.0 |
| app / router / TestClient start-up | 208.1 | 1.4% | 0.9 |
| other child processes | 51.1 | 0.4% | 0.2 |
| other fixture set-up | 180.8 | 1.2% | 0.8 |
| the test's own work (remainder of call) | 2286.9 | 15.7% | 9.5 |
| teardown | 145.3 | 1.0% | 0.6 |
| **total** | 14520.4 | | |

### Workers and the idle tail

| worker | tests | first start s | last end s | tail idle s | busy s |
| --- | ---: | ---: | ---: | ---: | ---: |
| gw0 | 796 | 0.0 | 3605.0 | 85.0 | 3586.6 |
| gw1 | 1410 | 0.0 | 3627.7 | 62.2 | 3613.5 |
| gw2 | 1287 | 0.0 | 3659.0 | 31.0 | 3636.7 |
| gw3 | 639 | 0.1 | 3690.0 | 0.0 | 3683.6 |

### Top 30 files by measured time

| file | tests | total | db | install | gateway | build | app | subproc | setup other | checks | teardown |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| test_w403_opportunity_read_postgres.py | 10 | 724.4 | 2.2 | 5.5 | 0.0 | 487.0 | 2.2 | 0.0 | 0.1 | 227.4 | 0.0 |
| test_w303_portfolio_scope_snapshot_postgres.py | 10 | 627.9 | 3.1 | 10.0 | 45.2 | 509.0 | 0.5 | 0.0 | 0.0 | 53.3 | 6.8 |
| test_w206_ev_reads_postgres.py | 23 | 616.0 | 7.2 | 12.8 | 46.2 | 507.6 | 0.8 | 0.0 | 0.1 | 34.5 | 6.8 |
| test_w205b_ev_replay_postgres.py | 13 | 494.5 | 5.6 | 10.7 | 37.1 | 395.4 | 1.6 | 0.0 | 0.0 | 40.4 | 3.7 |
| test_w207_ev_site_reads_postgres.py | 19 | 442.1 | 4.2 | 8.6 | 31.6 | 349.7 | 1.0 | 0.0 | 0.1 | 42.0 | 5.0 |
| test_w403_scenarios_postgres.py | 10 | 423.6 | 1.8 | 3.3 | 0.0 | 355.8 | 2.4 | 0.0 | 0.1 | 60.2 | 0.0 |
| test_w503_ev_scenarios_postgres.py | 15 | 397.1 | 9.5 | 7.6 | 26.9 | 312.2 | 0.9 | 0.0 | 0.2 | 39.9 | 0.0 |
| test_w206_ev_store_postgres.py | 13 | 357.8 | 3.8 | 7.1 | 26.7 | 305.0 | 0.3 | 0.0 | 0.1 | 10.7 | 4.2 |
| test_w504_ev_intent_postgres.py | 15 | 353.8 | 10.5 | 7.4 | 26.4 | 280.9 | 0.3 | 0.0 | 10.1 | 14.3 | 3.9 |
| test_w403_opportunity_worker_postgres.py | 5 | 337.5 | 1.5 | 2.9 | 0.0 | 301.3 | 0.0 | 0.0 | 0.1 | 31.8 | 0.0 |
| test_w402_reads_postgres.py | 6 | 330.1 | 1.3 | 3.5 | 0.0 | 308.8 | 0.0 | 0.0 | 0.1 | 16.5 | 0.0 |
| test_w301_estate_index_postgres.py | 20 | 327.0 | 5.3 | 10.6 | 32.0 | 240.3 | 0.5 | 0.0 | 4.3 | 29.0 | 4.9 |
| test_w207_ev_money_postgres.py | 14 | 316.2 | 34.8 | 5.2 | 18.0 | 224.9 | 0.2 | 0.0 | 0.5 | 25.1 | 7.4 |
| test_w303_portfolio_comparison_postgres.py | 4 | 269.7 | 1.4 | 4.0 | 17.9 | 216.2 | 0.3 | 0.0 | 0.1 | 27.3 | 2.6 |
| test_w403_replay_postgres.py | 2 | 241.1 | 0.9 | 0.8 | 0.0 | 143.5 | 2.6 | 0.0 | 0.1 | 93.2 | 0.0 |
| test_w203_cold_replay_postgres.py | 14 | 232.6 | 4.0 | 9.3 | 26.9 | 176.5 | 0.2 | 0.0 | 0.1 | 12.2 | 3.4 |
| test_w503_ev_depth_postgres.py | 15 | 227.4 | 2.5 | 5.6 | 16.2 | 181.3 | 0.8 | 0.0 | 0.0 | 20.3 | 0.6 |
| test_w403_work_links_postgres.py | 3 | 221.3 | 1.1 | 1.9 | 0.0 | 189.7 | 0.2 | 0.0 | 0.1 | 28.3 | 0.0 |
| test_w403_opportunity_scan_postgres.py | 5 | 221.0 | 1.1 | 1.9 | 0.0 | 216.9 | 0.0 | 0.0 | 0.1 | 1.0 | 0.0 |
| test_w301_provenance_dto_postgres.py | 7 | 218.0 | 3.1 | 4.4 | 16.3 | 167.3 | 0.3 | 0.0 | 1.2 | 22.6 | 2.8 |
| test_w501_cold_depth_postgres.py | 12 | 200.9 | 3.6 | 8.7 | 25.1 | 146.6 | 0.4 | 0.0 | 0.1 | 13.1 | 3.3 |
| test_w403_opportunity_job_isolation_postgres.py | 5 | 194.8 | 1.4 | 2.1 | 0.0 | 172.1 | 0.0 | 0.0 | 0.1 | 16.5 | 2.7 |
| test_w502_domain_intent_postgres.py | 11 | 193.1 | 8.2 | 8.0 | 22.6 | 137.8 | 0.6 | 0.0 | 7.6 | 5.9 | 2.4 |
| test_w202_cold_replay_postgres.py | 12 | 177.8 | 3.5 | 7.4 | 22.5 | 132.6 | 1.2 | 0.0 | 0.0 | 7.7 | 2.9 |
| test_w301_estate_golden_postgres.py | 6 | 171.8 | 2.1 | 3.6 | 11.2 | 126.9 | 0.1 | 0.0 | 0.0 | 26.6 | 1.2 |
| test_w504_ev_intent_api.py | 6 | 168.7 | 1.6 | 3.1 | 11.8 | 136.8 | 0.2 | 0.0 | 4.9 | 8.7 | 1.6 |
| test_w302_pinned_facades_postgres.py | 8 | 156.6 | 2.9 | 4.2 | 12.6 | 125.2 | 0.1 | 0.0 | 0.1 | 9.8 | 1.6 |
| test_s4_schedule_health_postgres.py | 9 | 150.2 | 1.5 | 0.0 | 0.0 | 29.5 | 0.0 | 0.0 | 0.1 | 116.7 | 2.3 |
| test_w501_cold_scenarios_postgres.py | 7 | 149.3 | 8.1 | 4.2 | 13.3 | 76.7 | 0.4 | 0.0 | 0.1 | 44.9 | 1.5 |
| test_w302_money_comparability_postgres.py | 6 | 136.8 | 0.8 | 1.9 | 11.3 | 114.1 | 0.2 | 0.0 | 0.0 | 7.7 | 0.9 |

### Site set-ups

- root builds 736 across 624 tests; distinct set-ups 107; world time (db+install+gateway+build) in those tests 11211.7 s

| builds | world s | fingerprint | files |
| ---: | ---: | --- | --- |
| 64 | 1600.8 | `["test_w205b_ev_replay_postgres.Chain.open", "complete", {}, "start_release_upload"]` | test_w205b_ev_replay_postgres.py, test_w206_ev_publication_enqueue_postgres.py, test_w206_ev_reads_postgres.py, test_w206_ev_store_postgres.py ... |
| 38 | 924.7 | `["test_w205b_ev_replay_postgres.Chain.open", "interrupted", {}, "start_release_upload"]` | test_cc_placement_postgres.py, test_r373_request_access.py, test_w205b_ev_replay_postgres.py, test_w206_ev_reads_postgres.py ... |
| 139 | 893.2 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}, "d1e45727", "5ea3ed85", "84593783"]` | test_s405_resolver_postgres.py, test_s4_consequence_history_postgres.py, test_s4_consequence_recompute_postgres.py, test_s4_consequence_store_postgres.py ... |
| 41 | 748.9 | `["test_w402_reads_postgres._setup", ["<PostgresFoundationStore>", "<Engine>"], {}]` | test_w402_reads_postgres.py, test_w403_opportunity_job_isolation_postgres.py, test_w403_opportunity_links_postgres.py, test_w403_opportunity_read_postgres.py ... |
| 34 | 696.9 | `["test_w402_reads_postgres._reconcile", ["<Engine>", ["2026-10-06", "2026-10-07", "2026-10-08", "2026-10-09", "2026-10-10"]], {}]` | test_w402_reads_postgres.py, test_w403_opportunity_job_isolation_postgres.py, test_w403_opportunity_links_postgres.py, test_w403_opportunity_read_postgres.py ... |
| 23 | 603.3 | `["test_w205b_ev_replay_postgres.Chain.open", "late-record", {}, "start_release_upload", "advance_late"]` | test_w205b_ev_replay_postgres.py, test_w206_ev_reads_postgres.py, test_w206_ev_store_postgres.py, test_w207_ev_money_postgres.py ... |
| 8 | 596.1 | `["test_w303_portfolio_fixture_postgres.build_portfolio_fixture", ["<SubRequest>", "<MonkeyPatch>", "<CaptureFixture>"], {}]` | test_w303_portfolio_comparison_postgres.py, test_w303_portfolio_fixture_postgres.py, test_w303_portfolio_scope_snapshot_postgres.py |
| 38 | 591.7 | `["test_w202_cold_replay_postgres.Chain.open", "backup-failed", {}, "start_release_upload"]` | test_r373_request_access.py, test_w202_cold_replay_postgres.py, test_w203_cold_reads_postgres.py, test_w203_cold_replay_postgres.py ... |
| 30 | 549.3 | `["test_w402_reads_postgres._ingest", ["<Engine>", "<MgW402Install>"], {}]` | test_w402_reads_postgres.py, test_w403_opportunity_job_isolation_postgres.py, test_w403_opportunity_links_postgres.py, test_w403_opportunity_read_postgres.py ... |
| 23 | 315.4 | `["test_w202_cold_replay_postgres.Chain.open", "late-reading", {}, "start_release_upload"]` | test_w203_cold_replay_postgres.py, test_w204_cold_consequence.py, test_w301_cold_selection_on_postgres.py, test_w301_estate_index_postgres.py ... |
| 20 | 311.8 | `["test_w202_cold_replay_postgres.Chain.open", "excursion", {}, "start_release_upload"]` | test_w202_cold_replay_postgres.py, test_w203_cold_reads_postgres.py, test_w203_cold_replay_postgres.py, test_w204_cold_consequence.py ... |
| 12 | 308.3 | `["test_w205b_ev_replay_postgres.Chain.open", "missing-meter", {}, "start_release_upload"]` | test_w205b_ev_replay_postgres.py, test_w206_ev_reads_postgres.py, test_w206_ev_store_postgres.py, test_w207_ev_money_postgres.py ... |
| 10 | 266.3 | `["test_w205b_ev_replay_postgres.Chain.open", "fault", {}, "start_release_upload"]` | test_w205b_ev_replay_postgres.py, test_w206_ev_reads_postgres.py, test_w206_ev_store_postgres.py, test_w207_ev_money_postgres.py ... |
| 14 | 210.1 | `["test_w202_cold_replay_postgres.Chain.open", "late-reading", {}, "start_release_upload", "advance_late"]` | test_w202_cold_replay_postgres.py, test_w203_cold_reads_postgres.py, test_w203_cold_replay_postgres.py, test_w204_cold_consequence.py ... |
| 8 | 208.4 | `["test_w205b_ev_replay_postgres.Chain.open", "contradictory", {}, "start_release_upload"]` | test_w205b_ev_replay_postgres.py, test_w206_ev_reads_postgres.py, test_w206_ev_store_postgres.py, test_w207_ev_money_postgres.py ... |
| 11 | 177.3 | `["test_w202_cold_replay_postgres.Chain.open", "normal", {}, "start_release_upload"]` | test_w202_cold_replay_postgres.py, test_w203_cold_replay_postgres.py, test_w204_cold_consequence.py, test_w204_cold_reads.py ... |
| 4 | 144.5 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}, "df3b67c6", "5ea3ed85", "c9135f1a", "eee679ae", "5ea3ed85", "c9135f1a", "f4a8` | test_s4_finding_evidence_history_postgres.py, test_s4_finding_index_postgres.py, test_s4_finding_read_postgres.py, test_s4_finding_store_postgres.py |
| 30 | 127.7 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}, "df3b67c6", "5ea3ed85", "c9135f1a"]` | test_s4_finding_evidence_history_postgres.py, test_s4_finding_store_postgres.py, test_s6_action_apply_postgres.py, test_s6_action_store_postgres.py ... |
| 9 | 126.8 | `["test_w402_reads_postgres._reconcile", ["<Engine>", ["2026-10-07"]], {}]` | test_w402_reads_postgres.py, test_w403_opportunity_read_postgres.py, test_w403_scenarios_postgres.py |
| 7 | 112.1 | `["test_w202_cold_replay_postgres.Chain.open", "missing-probe", {}, "start_release_upload"]` | test_w202_cold_replay_postgres.py, test_w203_cold_reads_postgres.py, test_w203_cold_replay_postgres.py, test_w204_cold_consequence.py ... |
| 2 | 87.4 | `["test_w301_estate_golden_postgres.mixed_replay", ["<TopRequest>", "<MonkeyPatch>", "<timedelta>"], {}]` | test_w301_estate_golden_postgres.py |
| 1 | 83.4 | `["test_w303_portfolio_fixture_postgres.build_portfolio_fixture", ["<TopRequest>", "<MonkeyPatch>", "<CaptureFixture>"], {}]` | test_cc_placement_postgres.py |
| 6 | 77.3 | `["test_w202_cold_replay_postgres.Chain.start_release_upload"]` | test_w502_cold_scenario_producer.py, test_w502_domain_work_links_postgres.py |
| 3 | 75.6 | `["test_w205b_ev_replay_postgres.Chain.open", "interrupted", {"fresh": true}, "start_release_upload"]` | test_w504_ev_work_producer_postgres.py |
| 1 | 69.1 | `["test_w303_portfolio_fixture_postgres.build_portfolio_fixture", ["<TopRequest>", "<MonkeyPatch>", "<CaptureFixture>"], {"cold_drain": true}` | test_w303_portfolio_scope_snapshot_postgres.py |
| 1 | 68.3 | `["test_w303_portfolio_fixture_postgres.build_portfolio_fixture", ["<TopRequest>", "<MonkeyPatch>", "<CaptureFixture>"], {"w1_source": "MIXED` | test_w303_portfolio_scope_snapshot_postgres.py |
| 1 | 67.7 | `["test_w303_portfolio_fixture_postgres.build_portfolio_fixture", ["<TopRequest>", "<MonkeyPatch>", "<CaptureFixture>"], {"cold_drain": false` | test_w303_portfolio_scope_snapshot_postgres.py |
| 1 | 66.6 | `["test_w303_portfolio_fixture_postgres.build_portfolio_fixture", ["<TopRequest>", "<MonkeyPatch>", "<CaptureFixture>"], {"w1_source": "UNBOU` | test_w303_portfolio_scope_snapshot_postgres.py |
| 4 | 64.1 | `["test_w202_cold_replay_postgres.Chain.open", "contradictory", {}, "start_release_upload"]` | test_w202_cold_replay_postgres.py, test_w203_cold_replay_postgres.py, test_w204_cold_consequence.py, test_w501_cold_depth_postgres.py |
| 18 | 62.9 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}, "8728a720"]` | test_s4_evidence_decided_at_postgres.py, test_s4_schedule_health_postgres.py, test_s4_schedule_tick_postgres.py |
| 5 | 56.3 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}, "df3b67c6", "5ea3ed85", "c9135f1a", "eee679ae", "5ea3ed85", "c9135f1a", "f4a8` | test_s6_site_action_index_postgres.py, test_s6_verification_evaluator_postgres.py, test_s6_verification_holds_postgres.py, test_w303_portfolio_comparison_postgres.py |
| 2 | 50.6 | `["test_w205b_ev_replay_postgres.Chain.open", "complete", {"fresh": false, "install": "<install_second_ev_site>", "scenario_id": "ev-complete` | test_w302_money_comparability_postgres.py |
| 15 | 50.0 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}]` | test_s3_capability_read_postgres.py, test_s3_claim_limit_postgres.py, test_s4_evidence_consequence_work_postgres.py, test_s4_evidence_decided_at_postgres.py ... |
| 4 | 45.7 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}, "df3b67c6", "5ea3ed85", "c9135f1a", "eee679ae", "5ea3ed85", "c9135f1a", "f4a8` | test_s6_verification_evaluator_postgres.py, test_s6_verification_holds_postgres.py, test_w301_estate_index_postgres.py |
| 4 | 44.5 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}, "eee679ae", "5ea3ed85", "c9135f1a"]` | test_w403_alternative_postgres.py, test_w403_replay_postgres.py |
| 5 | 36.1 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}, "df3b67c6", "5ea3ed85", "c9135f1a", "eee679ae", "5ea3ed85", "c9135f1a", "f4a8` | test_s6_action_apply_postgres.py, test_s6_verification_plan_postgres.py, test_w401_work_service_postgres.py |
| 2 | 32.6 | `["test_w402_reads_postgres._reconcile", ["<Engine>", ["2026-10-08"]], {}]` | test_w402_reads_postgres.py, test_w403_replay_postgres.py |
| 2 | 29.1 | `["test_w402_reads_postgres._reconcile", ["<Engine>", ["2026-10-07", "2026-10-08", "2026-10-09", "2026-10-10"]], {}]` | test_w403_opportunity_scan_postgres.py, test_w403_opportunity_worker_postgres.py |
| 1 | 27.4 | `["test_w205b_ev_replay_postgres.Chain.open", "late-record", {}, "start_release_upload", "advance_late", "advance_late"]` | test_w205b_ev_replay_postgres.py |
| 3 | 27.0 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}, "49f61049", "5ea3ed85", "df74c549", "52464e7b", "5ea3ed85", "c9135f1a", "4ff2` | test_w301_estate_golden_postgres.py, test_w301_estate_index_postgres.py |
| 4 | 26.4 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}, "df3b67c6", "5ea3ed85", "c9135f1a", "169ced82"]` | test_s4_finding_store_postgres.py, test_w301_estate_index_postgres.py, test_w303_portfolio_scope_snapshot_postgres.py |
| 1 | 24.9 | `["test_w205b_ev_replay_postgres.Chain.open", "complete", {}, "start_release_upload", "release_and_upload"]` | test_w205b_ev_replay_postgres.py |
| 1 | 24.8 | `["test_w205b_ev_replay_postgres.Chain.open", "late-record", {}, "start_release_upload"]` | test_w301_provenance_dto_postgres.py |
| 2 | 22.3 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}, "df3b67c6", "5ea3ed85", "c9135f1a", "eee679ae", "5ea3ed85", "c9135f1a", "f4a8` | test_s6_verification_holds_postgres.py |
| 5 | 22.1 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}, "5ea3ed85", "c9135f1a"]` | test_s4_power_demo_case_postgres.py |
| 4 | 22.1 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}, "57523b03", "5ea3ed85", "1766a32b", "5ea3ed85"]` | test_w301_w1_snapshot_helpers_postgres.py, test_w302_w1_claim_limit_on_postgres.py |
| 4 | 17.9 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}, "5ea3ed85", "5ea3ed85"]` | test_lr01_money_eligibility_postgres.py, test_s4_power_demo_case_postgres.py, test_w301_w1_money_snapshot_helpers_postgres.py |
| 1 | 17.8 | `["test_w402_reads_postgres._reconcile", ["<Engine>", ["2026-10-08", "2026-10-09", "2026-10-10", "2026-10-11", "2026-10-12"]], {}]` | test_w403_replay_postgres.py |
| 2 | 14.7 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}, "df3b67c6", "5ea3ed85", "c9135f1a", "5ea3ed85", "84593783", "67d09500", "5ea3` | test_s6_verification_evaluator_postgres.py, test_w303_selectors_postgres.py |
| 1 | 14.4 | `["test_w202_cold_replay_postgres.Chain.open", "normal", {}, "start_release_upload", "release_and_upload"]` | test_w202_cold_replay_postgres.py |
| 3 | 14.1 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}, "df3b67c6", "5ea3ed85", "c9135f1a", "5ea3ed85", "84593783"]` | test_s6_verification_evaluator_postgres.py, test_s6_verification_plan_postgres.py |
| 1 | 13.5 | `["test_w402_reads_postgres._reconcile", ["<Engine>", ["2026-10-05"]], {}]` | test_w403_opportunity_read_postgres.py |
| 1 | 12.4 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}, "df3b67c6", "5ea3ed85", "c9135f1a", "eee679ae", "5ea3ed85", "c9135f1a", "f4a8` | test_s6_verification_holds_postgres.py |
| 1 | 12.0 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}, "df3b67c6", "5ea3ed85", "c9135f1a", "eee679ae", "5ea3ed85", "c9135f1a", "f4a8` | test_s6_verification_holds_postgres.py |
| 1 | 11.9 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}, "df3b67c6", "5ea3ed85", "c9135f1a", "eee679ae", "5ea3ed85", "c9135f1a", "f4a8` | test_s6_verification_evaluator_postgres.py |
| 3 | 11.6 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}, "71f11bc5", "5ea3ed85", "c9135f1a"]` | test_r373_request_access.py, test_w601b_global_maintenance.py, test_w601c_request_detail.py |
| 2 | 10.8 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}, "eee679ae", "5ea3ed85", "c9135f1a", "f4a8e3ba", "5ea3ed85", "c9135f1a"]` | test_w403_alternative_postgres.py |
| 1 | 10.1 | `["test_w402_reads_postgres._reconcile", ["<Engine>", ["2026-10-09"]], {}]` | test_w402_reads_postgres.py |
| 2 | 10.0 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}, "8319ad7d", "5ea3ed85", "718bbd33", "5ea3ed85", "dcee202f", "5ea3ed85"]` | test_s4_deferred_match_postgres.py |
| 1 | 10.0 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}, "df3b67c6", "5ea3ed85", "c9135f1a", "eee679ae", "5ea3ed85", "c9135f1a", "f4a8` | test_s6_verification_evaluator_postgres.py |

Distinct per-test set-ups (ordered root builds of one test): 121

| tests | world s | set-up | files |
| ---: | ---: | --- | --- |
| 59 | 1474.6 | `["test_w205b_ev_replay_postgres.Chain.open", "complete", {}, "start_release_upload"]` | test_w205b_ev_replay_postgres.py, test_w206_ev_publication_enqueue_postgres.py, test_w206_ev_reads_postgres.py, test_w206_ev_store_postgres.py ... |
| 22 | 1320.7 | `["test_w402_reads_postgres._setup", ["<PostgresFoundationStore>", "<Engine>"], {}] + ["test_w402_reads_postgres._ingest", ["<Engine>", "<MgW402Install>"], {}] +` | test_w402_reads_postgres.py, test_w403_opportunity_job_isolation_postgres.py, test_w403_opportunity_links_postgres.py, test_w403_opportunity_read_postgres.py ... |
| 137 | 886.6 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}, "d1e45727", "5ea3ed85", "84593783"]` | test_s405_resolver_postgres.py, test_s4_consequence_history_postgres.py, test_s4_consequence_recompute_postgres.py, test_s4_consequence_store_postgres.py ... |
| 35 | 855.1 | `["test_w205b_ev_replay_postgres.Chain.open", "interrupted", {}, "start_release_upload"]` | test_cc_placement_postgres.py, test_r373_request_access.py, test_w205b_ev_replay_postgres.py, test_w206_ev_reads_postgres.py ... |
| 8 | 596.1 | `["test_w303_portfolio_fixture_postgres.build_portfolio_fixture", ["<SubRequest>", "<MonkeyPatch>", "<CaptureFixture>"], {}]` | test_w303_portfolio_comparison_postgres.py, test_w303_portfolio_fixture_postgres.py, test_w303_portfolio_scope_snapshot_postgres.py |
| 38 | 591.7 | `["test_w202_cold_replay_postgres.Chain.open", "backup-failed", {}, "start_release_upload"]` | test_r373_request_access.py, test_w202_cold_replay_postgres.py, test_w203_cold_reads_postgres.py, test_w203_cold_replay_postgres.py ... |
| 21 | 552.2 | `["test_w205b_ev_replay_postgres.Chain.open", "late-record", {}, "start_release_upload", "advance_late"]` | test_w205b_ev_replay_postgres.py, test_w206_ev_reads_postgres.py, test_w206_ev_store_postgres.py, test_w207_ev_money_postgres.py ... |
| 18 | 276.7 | `["test_w202_cold_replay_postgres.Chain.open", "excursion", {}, "start_release_upload"]` | test_w202_cold_replay_postgres.py, test_w203_cold_reads_postgres.py, test_w203_cold_replay_postgres.py, test_w204_cold_consequence.py ... |
| 18 | 268.7 | `["test_w202_cold_replay_postgres.Chain.open", "late-reading", {}, "start_release_upload"]` | test_w203_cold_replay_postgres.py, test_w204_cold_consequence.py, test_w301_cold_selection_on_postgres.py, test_w301_estate_index_postgres.py ... |
| 4 | 240.4 | `["test_w402_reads_postgres._setup", ["<PostgresFoundationStore>", "<Engine>"], {}] + ["test_w402_reads_postgres._reconcile", ["<Engine>", ["2026-10-06", "2026-1` | test_w402_reads_postgres.py, test_w403_opportunity_read_postgres.py, test_w403_opportunity_worker_postgres.py, test_w403_scenarios_postgres.py |
| 14 | 210.1 | `["test_w202_cold_replay_postgres.Chain.open", "late-reading", {}, "start_release_upload", "advance_late"]` | test_w202_cold_replay_postgres.py, test_w203_cold_reads_postgres.py, test_w203_cold_replay_postgres.py, test_w204_cold_consequence.py ... |
| 8 | 205.8 | `["test_w205b_ev_replay_postgres.Chain.open", "missing-meter", {}, "start_release_upload"]` | test_w205b_ev_replay_postgres.py, test_w206_ev_reads_postgres.py, test_w206_ev_store_postgres.py, test_w207_ev_money_postgres.py ... |
| 6 | 164.2 | `["test_w205b_ev_replay_postgres.Chain.open", "fault", {}, "start_release_upload"]` | test_w205b_ev_replay_postgres.py, test_w206_ev_reads_postgres.py, test_w206_ev_store_postgres.py, test_w207_ev_money_postgres.py ... |
| 10 | 162.2 | `["test_w202_cold_replay_postgres.Chain.open", "normal", {}, "start_release_upload"]` | test_w202_cold_replay_postgres.py, test_w203_cold_replay_postgres.py, test_w204_cold_consequence.py, test_w204_cold_reads.py ... |
| 6 | 158.7 | `["test_w205b_ev_replay_postgres.Chain.open", "contradictory", {}, "start_release_upload"]` | test_w205b_ev_replay_postgres.py, test_w206_ev_reads_postgres.py, test_w206_ev_store_postgres.py, test_w207_ev_money_postgres.py ... |
| 1 | 149.0 | `["test_w205b_ev_replay_postgres.Chain.open", "complete", {}, "start_release_upload"] + ["test_w205b_ev_replay_postgres.Chain.open", "interrupted", {}, "start_re` | test_w301_provenance_dto_postgres.py |
| 1 | 149.0 | `["test_w205b_ev_replay_postgres.Chain.open", "complete", {}, "start_release_upload"] + ["test_w205b_ev_replay_postgres.Chain.open", "interrupted", {}, "start_re` | test_w205b_ev_replay_postgres.py |
| 4 | 144.5 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}, "df3b67c6", "5ea3ed85", "c9135f1a", "eee679ae", "5ea3ed85", "c9135f1a", "f4a8e3ba", "5ea3ed85", "` | test_s4_finding_evidence_history_postgres.py, test_s4_finding_index_postgres.py, test_s4_finding_read_postgres.py, test_s4_finding_store_postgres.py |
| 2 | 122.1 | `["test_w402_reads_postgres._setup", ["<PostgresFoundationStore>", "<Engine>"], {}] + ["test_w402_reads_postgres._reconcile", ["<Engine>", ["2026-10-06", "2026-1` | test_w403_opportunity_read_postgres.py, test_w403_scenarios_postgres.py |
| 2 | 116.5 | `["test_w402_reads_postgres._setup", ["<PostgresFoundationStore>", "<Engine>"], {}] + ["test_w402_reads_postgres._reconcile", ["<Engine>", ["2026-10-07", "2026-1` | test_w403_opportunity_scan_postgres.py, test_w403_opportunity_worker_postgres.py |
| 7 | 112.1 | `["test_w202_cold_replay_postgres.Chain.open", "missing-probe", {}, "start_release_upload"]` | test_w202_cold_replay_postgres.py, test_w203_cold_reads_postgres.py, test_w203_cold_replay_postgres.py, test_w204_cold_consequence.py ... |
| 2 | 101.3 | `["test_w205b_ev_replay_postgres.Chain.open", "complete", {}, "start_release_upload"] + ["test_w205b_ev_replay_postgres.Chain.open", "complete", {"fresh": false,` | test_w302_money_comparability_postgres.py |
| 27 | 99.7 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}, "df3b67c6", "5ea3ed85", "c9135f1a"]` | test_s4_finding_evidence_history_postgres.py, test_s4_finding_store_postgres.py, test_s6_action_apply_postgres.py, test_s6_action_store_postgres.py ... |
| 1 | 89.0 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}, "eee679ae", "5ea3ed85", "c9135f1a"] + ["test_w402_reads_postgres._setup", ["<PostgresFoundationSt` | test_w403_replay_postgres.py |
| 2 | 87.4 | `["test_w301_estate_golden_postgres.mixed_replay", ["<TopRequest>", "<MonkeyPatch>", "<timedelta>"], {}]` | test_w301_estate_golden_postgres.py |
| 1 | 83.4 | `["test_w303_portfolio_fixture_postgres.build_portfolio_fixture", ["<TopRequest>", "<MonkeyPatch>", "<CaptureFixture>"], {}]` | test_cc_placement_postgres.py |
| 3 | 75.6 | `["test_w205b_ev_replay_postgres.Chain.open", "interrupted", {"fresh": true}, "start_release_upload"]` | test_w504_ev_work_producer_postgres.py |
| 5 | 70.1 | `["test_w202_cold_replay_postgres.Chain.start_release_upload"]` | test_w502_cold_scenario_producer.py, test_w502_domain_work_links_postgres.py |
| 1 | 69.1 | `["test_w303_portfolio_fixture_postgres.build_portfolio_fixture", ["<TopRequest>", "<MonkeyPatch>", "<CaptureFixture>"], {"cold_drain": true}]` | test_w303_portfolio_scope_snapshot_postgres.py |
| 1 | 68.3 | `["test_w303_portfolio_fixture_postgres.build_portfolio_fixture", ["<TopRequest>", "<MonkeyPatch>", "<CaptureFixture>"], {"w1_source": "MIXED"}]` | test_w303_portfolio_scope_snapshot_postgres.py |
| 1 | 67.7 | `["test_w303_portfolio_fixture_postgres.build_portfolio_fixture", ["<TopRequest>", "<MonkeyPatch>", "<CaptureFixture>"], {"cold_drain": false}]` | test_w303_portfolio_scope_snapshot_postgres.py |
| 1 | 67.5 | `["test_w402_reads_postgres._setup", ["<PostgresFoundationStore>", "<Engine>"], {}] + ["test_w402_reads_postgres._ingest", ["<Engine>", "<MgW402Install>"], {}] +` | test_w403_opportunity_read_postgres.py |
| 1 | 66.6 | `["test_w303_portfolio_fixture_postgres.build_portfolio_fixture", ["<TopRequest>", "<MonkeyPatch>", "<CaptureFixture>"], {"w1_source": "UNBOUND"}]` | test_w303_portfolio_scope_snapshot_postgres.py |
| 1 | 66.2 | `["test_w402_reads_postgres._setup", ["<PostgresFoundationStore>", "<Engine>"], {}] + ["test_w402_reads_postgres._ingest", ["<Engine>", "<MgW402Install>"], {}] +` | test_w403_opportunity_read_postgres.py |
| 4 | 64.1 | `["test_w202_cold_replay_postgres.Chain.open", "contradictory", {}, "start_release_upload"]` | test_w202_cold_replay_postgres.py, test_w203_cold_replay_postgres.py, test_w204_cold_consequence.py, test_w501_cold_depth_postgres.py |
| 17 | 60.3 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}, "8728a720"]` | test_s4_evidence_decided_at_postgres.py, test_s4_schedule_health_postgres.py, test_s4_schedule_tick_postgres.py |
| 5 | 56.3 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}, "df3b67c6", "5ea3ed85", "c9135f1a", "eee679ae", "5ea3ed85", "c9135f1a", "f4a8e3ba", "5ea3ed85", "` | test_s6_site_action_index_postgres.py, test_s6_verification_evaluator_postgres.py, test_s6_verification_holds_postgres.py, test_w303_portfolio_comparison_postgres.py |
| 1 | 56.2 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}, "eee679ae", "5ea3ed85", "c9135f1a"] + ["test_w402_reads_postgres._setup", ["<PostgresFoundationSt` | test_w403_replay_postgres.py |
| 3 | 56.0 | `["test_w202_cold_replay_postgres.Chain.open", "late-reading", {}, "start_release_upload"] + ["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}, "df3b` | test_w301_estate_index_postgres.py |
| 1 | 53.1 | `["test_w205b_ev_replay_postgres.Chain.open", "fault", {}, "start_release_upload"] + ["test_w205b_ev_replay_postgres.Chain.open", "missing-meter", {}, "start_rel` | test_w503_ev_scenarios_postgres.py |
| 1 | 52.5 | `["test_w205b_ev_replay_postgres.Chain.open", "missing-meter", {}, "start_release_upload"] + ["test_w205b_ev_replay_postgres.Chain.open", "late-record", {}, "sta` | test_w503_ev_depth_postgres.py |
| 1 | 51.8 | `["test_w205b_ev_replay_postgres.Chain.open", "complete", {}, "start_release_upload"] + ["test_w205b_ev_replay_postgres.Chain.open", "fault", {}, "start_release_` | test_w503_ev_scenarios_postgres.py |
| 1 | 50.4 | `["test_w402_reads_postgres._setup", ["<PostgresFoundationStore>", "<Engine>"], {}] + ["test_w402_reads_postgres._ingest", ["<Engine>", "<MgW402Install>"], {}] +` | test_w402_reads_postgres.py |
| 4 | 45.7 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}, "df3b67c6", "5ea3ed85", "c9135f1a", "eee679ae", "5ea3ed85", "c9135f1a", "f4a8e3ba", "5ea3ed85", "` | test_s6_verification_evaluator_postgres.py, test_s6_verification_holds_postgres.py, test_w301_estate_index_postgres.py |
| 1 | 44.4 | `["test_w402_reads_postgres._setup", ["<PostgresFoundationStore>", "<Engine>"], {}] + ["test_w402_reads_postgres._ingest", ["<Engine>", "<MgW402Install>"], {}] +` | test_w402_reads_postgres.py |
| 1 | 43.7 | `["test_w402_reads_postgres._setup", ["<PostgresFoundationStore>", "<Engine>"], {}] + ["test_w402_reads_postgres._reconcile", ["<Engine>", ["2026-10-07"]], {}] +` | test_w402_reads_postgres.py |
| 1 | 42.2 | `["test_w402_reads_postgres._setup", ["<PostgresFoundationStore>", "<Engine>"], {}] + ["test_w402_reads_postgres._ingest", ["<Engine>", "<MgW402Install>"], {}] +` | test_w402_reads_postgres.py |
| 1 | 39.9 | `["test_w202_cold_replay_postgres.Chain.open", "excursion", {}, "start_release_upload"] + ["test_w205b_ev_replay_postgres.Chain.open", "interrupted", {}, "start_` | test_w401_site_indexes_postgres.py |
| 2 | 37.5 | `["test_w202_cold_replay_postgres.Chain.open", "late-reading", {}, "start_release_upload"] + ["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}, "df3b` | test_w301_estate_index_postgres.py |
| 5 | 36.1 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}, "df3b67c6", "5ea3ed85", "c9135f1a", "eee679ae", "5ea3ed85", "c9135f1a", "f4a8e3ba", "5ea3ed85", "` | test_s6_action_apply_postgres.py, test_s6_verification_plan_postgres.py, test_w401_work_service_postgres.py |
| 1 | 30.3 | `["test_w202_cold_replay_postgres.Chain.open", "normal", {}, "start_release_upload"] + ["test_w202_cold_replay_postgres.Chain.open", "excursion", {}, "start_rele` | test_w301_provenance_dto_postgres.py |
| 1 | 27.4 | `["test_w205b_ev_replay_postgres.Chain.open", "late-record", {}, "start_release_upload", "advance_late", "advance_late"]` | test_w205b_ev_replay_postgres.py |
| 3 | 27.0 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}, "49f61049", "5ea3ed85", "df74c549", "52464e7b", "5ea3ed85", "c9135f1a", "4ff271a6", "5ea3ed85", "` | test_w301_estate_golden_postgres.py, test_w301_estate_index_postgres.py |
| 1 | 24.9 | `["test_w205b_ev_replay_postgres.Chain.open", "complete", {}, "start_release_upload", "release_and_upload"]` | test_w205b_ev_replay_postgres.py |
| 2 | 22.3 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}, "df3b67c6", "5ea3ed85", "c9135f1a", "eee679ae", "5ea3ed85", "c9135f1a", "f4a8e3ba", "5ea3ed85", "` | test_s6_verification_holds_postgres.py |
| 5 | 22.1 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}, "5ea3ed85", "c9135f1a"]` | test_s4_power_demo_case_postgres.py |
| 4 | 22.1 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}, "57523b03", "5ea3ed85", "1766a32b", "5ea3ed85"]` | test_w301_w1_snapshot_helpers_postgres.py, test_w302_w1_claim_limit_on_postgres.py |
| 4 | 17.9 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}, "5ea3ed85", "5ea3ed85"]` | test_lr01_money_eligibility_postgres.py, test_s4_power_demo_case_postgres.py, test_w301_w1_money_snapshot_helpers_postgres.py |
| 1 | 16.7 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}] + ["s6_action_records.build", ["<CaseRunner>", {"F01": {"case_id": "F01", "day": "2026-10-06", "l` | test_s6_action_records_postgres.py |
| 8 | 15.8 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}]` | test_s4_evidence_decided_at_postgres.py, test_s4_finding_index_postgres.py, test_w401_site_indexes_postgres.py, test_w401_work_service_postgres.py |

Most frequent write statements in the check phase of tests of 5 s or more:

- 81359 x `INSERT INTO mini_opportunity_evidence (tenant_id,`
- 24631 x `INSERT INTO mini_depth_revision_evidence (tenant_id,`
- 7374 x `INSERT INTO finding_revision_evidence (finding_revision_id,`
- 4743 x `INSERT INTO ingestion_disposition (batch_id,`
- 4740 x `INSERT INTO accepted_evidence (id,`
- 3074 x `UPDATE recompute_job SET status`
- 1338 x `INSERT INTO action_basis_evidence (action_id,`
- 1055 x `INSERT INTO signal_binding_revision (id,`
- 766 x `INSERT INTO financial_consequence_work_attempt (id,`
- 764 x `INSERT INTO source_clock_attestation (id,`
- 669 x `INSERT INTO action_basis_assessment (action_id,`
- 584 x `INSERT INTO financial_consequence_power_interval (consequence_revision_id,`
- 466 x `UPDATE schedule_site_head SET stage`
- 463 x `INSERT INTO analytic_run_assessment (run_id,`
- 460 x `INSERT INTO assessment_revision (id,`
- 420 x `INSERT INTO analytic_run (id,`
- 404 x `INSERT INTO analytic_run_evidence (run_id,`
- 399 x `INSERT INTO analytic_run_selection (tenant_id,`
- 315 x `INSERT INTO asset (id,`
- 278 x `INSERT INTO evidence_publication (id,`
- 276 x `INSERT INTO verification_metric (outcome_id,`
- 255 x `INSERT INTO source (id,`
- 176 x `INSERT INTO mini_depth_selection (tenant_id,`
- 174 x `INSERT INTO financial_assumption_assignment (id,`
- 168 x `INSERT INTO mini_depth_revision (id,`

### Read-only versus writes after the build (tests of 5 s or more)

```json
{
  "heavy_tests": 572,
  "heavy_seconds": 13337.1,
  "read_only_after_build": 79,
  "read_only_after_build_seconds": 2256.7,
  "writes_after_build": 493,
  "writes_after_build_seconds": 11080.4,
  "heavy_with_root_build": 546,
  "heavy_with_root_build_read_only": 68,
  "heavy_setup_fixture_writes": 73,
  "check_write_histogram": {
    "1-10": 86,
    "0": 79,
    "11-100": 324,
    ">100": 83
  }
}
```

## Run 20261029-090322-b2ebc7

- pytest wall 287 s; 3 tests on 2 workers; first test start to last test end 221.8 s
- measured test time (sum of set-up + call + teardown) 313.6 s; attributed 313.6 s; unattributed 0.0 s
- worker idle inside the span (workers x span - measured) 130.0 s
- memory: peak vm_used_mb=1819 vmmem_ws_mb=3162 runner_mem_mb=660 pg_mem_mb=342 runner_procs=12 runner_rss_sum_mb=753 runner_rss_max_mb=168 min win_free_mb=3486 vm_total_mb=3918 samples=59
- instrumentation: {'wrapped_calls': 399, 'statements': 5386, 'overhead_s_estimate': 0.0}

| part | seconds | share of measured | wall-equivalent min (/ workers) |
| --- | ---: | ---: | ---: |
| DB create/clone/drop + migrations | 6.3 | 2.0% | 0.1 |
| Site/Foundation install + credentials | 0.0 | 0.0% | 0.0 |
| gateway subprocess start/stop | 0.0 | 0.0% | 0.0 |
| replay / ingest / seed (site build) | 7.2 | 2.3% | 0.1 |
| app / router / TestClient start-up | 0.0 | 0.0% | 0.0 |
| other child processes | 173.6 | 55.4% | 1.4 |
| other fixture set-up | 0.7 | 0.2% | 0.0 |
| the test's own work (remainder of call) | 125.5 | 40.0% | 1.0 |
| teardown | 0.4 | 0.1% | 0.0 |
| **total** | 313.7 | | |

### Workers and the idle tail

| worker | tests | first start s | last end s | tail idle s | busy s |
| --- | ---: | ---: | ---: | ---: | ---: |
| gw0 | 2 | 0.0 | 221.8 | 0.0 | 221.8 |
| gw1 | 1 | 0.0 | 91.8 | 130.0 | 91.8 |

### Top 30 files by measured time

| file | tests | total | db | install | gateway | build | app | subproc | setup other | checks | teardown |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| test_s4_schedule_health_postgres.py | 2 | 221.8 | 3.2 | 0.0 | 0.0 | 5.0 | 0.0 | 90.8 | 0.3 | 122.3 | 0.3 |
| test_s4_schedule_tick_postgres.py | 1 | 91.8 | 3.1 | 0.0 | 0.0 | 2.2 | 0.0 | 82.8 | 0.3 | 3.2 | 0.1 |

### Site set-ups

- root builds 3 across 3 tests; distinct set-ups 3; world time (db+install+gateway+build) in those tests 13.5 s

| builds | world s | fingerprint | files |
| ---: | ---: | --- | --- |
| 1 | 7.0 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}, "8728a720", "4d06723f"]` | test_s4_schedule_health_postgres.py |
| 1 | 5.3 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}, "8728a720", "91c5f51e"]` | test_s4_schedule_tick_postgres.py |
| 1 | 1.2 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}, "8728a720"]` | test_s4_schedule_health_postgres.py |

Distinct per-test set-ups (ordered root builds of one test): 3

| tests | world s | set-up | files |
| ---: | ---: | --- | --- |
| 1 | 7.0 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}, "8728a720", "4d06723f"]` | test_s4_schedule_health_postgres.py |
| 1 | 5.3 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}, "8728a720", "91c5f51e"]` | test_s4_schedule_tick_postgres.py |
| 1 | 1.2 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}, "8728a720"]` | test_s4_schedule_health_postgres.py |

Most frequent write statements in the check phase of tests of 5 s or more:

- 126 x `INSERT INTO finding_revision_evidence (finding_revision_id,`
- 65 x `UPDATE schedule_site_head SET stage`
- 30 x `INSERT INTO asset (id,`
- 26 x `UPDATE schedule_site_head SET claim_token`
- 24 x `UPDATE recompute_job SET status`
- 24 x `UPDATE schedule_tick_head SET claim_token`
- 24 x `INSERT INTO source (id,`
- 10 x `INSERT INTO schedule_site_head (tenant_id,`
- 10 x `UPDATE schedule_site_head SET mini_processed`
- 6 x `UPDATE schedule_site_head SET s3_processed`
- 6 x `INSERT INTO schedule_tick_head (environment,`
- 4 x `INSERT INTO assessment_revision (id,`
- 4 x `INSERT INTO analytic_run_assessment (run_id,`
- 4 x `INSERT INTO finding_revision_assessment (finding_revision_id,`
- 4 x `UPDATE schedule_site_head SET opportunity_processed`
- 4 x `UPDATE schedule_site_head SET s4_outcome`

### Read-only versus writes after the build (tests of 5 s or more)

```json
{
  "heavy_tests": 3,
  "heavy_seconds": 313.6,
  "read_only_after_build": 0,
  "read_only_after_build_seconds": 0,
  "writes_after_build": 3,
  "writes_after_build_seconds": 313.6,
  "heavy_with_root_build": 3,
  "heavy_with_root_build_read_only": 0,
  "heavy_setup_fixture_writes": 0,
  "check_write_histogram": {
    ">100": 2,
    "11-100": 1
  }
}
```

## Frontend

```
Test Files  2 failed | 139 passed (141)
      Tests  4 failed | 3450 passed (3454)
 Test Files  1 failed | 140 passed (141)
      Tests  3 failed | 3451 passed (3454)
﻿forks exit=1 wall_s=265
﻿threads exit=1 wall_s=326
﻿threads2 exit=1 wall_s=203
```

