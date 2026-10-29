# PERF-01 measured time attribution

## Run 20261029-101114-000eaf

- pytest wall 3435 s; 4132 tests on 5 workers; first test start to last test end 3362.6 s
- measured test time (sum of set-up + call + teardown) 16202.6 s; attributed 16202.6 s; unattributed -0.0 s
- worker idle inside the span (workers x span - measured) 610.7 s
- memory: peak vm_used_mb=2738 vmmem_ws_mb=3553 runner_mem_mb=2216 pg_mem_mb=776 runner_procs=21 runner_rss_sum_mb=1776 runner_rss_max_mb=363 min win_free_mb=2747 vm_total_mb=3918 samples=561
- instrumentation: {'wrapped_calls': 132964, 'statements': 3270667, 'overhead_s_estimate': None}

| part | seconds | share of measured | wall-equivalent min (/ workers) |
| --- | ---: | ---: | ---: |
| DB create/clone/drop + migrations | 729.4 | 4.5% | 2.4 |
| Site/Foundation install + credentials | 288.0 | 1.8% | 1.0 |
| gateway subprocess start/stop | 744.7 | 4.6% | 2.5 |
| replay / ingest / seed (site build) | 11193.0 | 69.1% | 37.3 |
| app / router / TestClient start-up | 249.4 | 1.5% | 0.8 |
| other child processes | 57.7 | 0.4% | 0.2 |
| other fixture set-up | 207.8 | 1.3% | 0.7 |
| the test's own work (remainder of call) | 2583.8 | 15.9% | 8.6 |
| teardown | 148.8 | 0.9% | 0.5 |
| **total** | 16202.6 | | |

### Workers and the idle tail

| worker | tests | first start s | last end s | tail idle s | busy s |
| --- | ---: | ---: | ---: | ---: | ---: |
| gw0 | 662 | 0.0 | 3213.1 | 149.5 | 3205.8 |
| gw1 | 915 | 0.0 | 3194.6 | 168.1 | 3173.1 |
| gw2 | 729 | 0.0 | 3362.6 | 0.0 | 3354.6 |
| gw3 | 904 | 0.0 | 3306.7 | 55.9 | 3296.8 |
| gw4 | 922 | 0.2 | 3192.9 | 169.8 | 3172.2 |

### Top 30 files by measured time

| file | tests | total | db | install | gateway | build | app | subproc | setup other | checks | teardown |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| test_w403_opportunity_read_postgres.py | 10 | 790.6 | 3.1 | 6.5 | 0.0 | 531.3 | 2.0 | 0.0 | 0.1 | 247.6 | 0.0 |
| test_w303_portfolio_scope_snapshot_postgres.py | 10 | 711.5 | 4.3 | 12.0 | 55.4 | 575.1 | 0.7 | 0.0 | 0.0 | 55.9 | 8.0 |
| test_w206_ev_reads_postgres.py | 23 | 703.2 | 7.5 | 14.2 | 52.7 | 580.0 | 1.0 | 0.0 | 0.1 | 41.2 | 6.4 |
| test_w205b_ev_replay_postgres.py | 13 | 544.0 | 5.3 | 11.0 | 40.6 | 435.9 | 1.2 | 0.0 | 0.1 | 46.3 | 3.5 |
| test_w207_ev_site_reads_postgres.py | 19 | 516.6 | 5.0 | 10.3 | 36.1 | 409.5 | 1.3 | 0.0 | 0.1 | 49.9 | 4.5 |
| test_w403_scenarios_postgres.py | 10 | 442.2 | 2.1 | 4.0 | 0.0 | 371.2 | 2.2 | 0.0 | 0.1 | 62.6 | 0.0 |
| test_w503_ev_scenarios_postgres.py | 15 | 405.9 | 9.7 | 8.2 | 28.5 | 315.1 | 1.4 | 0.0 | 0.2 | 42.9 | 0.0 |
| test_w206_ev_store_postgres.py | 13 | 392.0 | 4.2 | 8.4 | 28.8 | 334.2 | 0.9 | 0.0 | 0.1 | 12.7 | 2.8 |
| test_w301_estate_index_postgres.py | 20 | 370.5 | 6.0 | 12.2 | 36.7 | 269.7 | 0.6 | 0.0 | 5.0 | 35.6 | 4.8 |
| test_w207_ev_money_postgres.py | 14 | 363.0 | 38.8 | 5.6 | 19.3 | 262.7 | 0.2 | 0.0 | 0.5 | 29.5 | 6.4 |
| test_w403_opportunity_worker_postgres.py | 5 | 362.3 | 1.6 | 3.8 | 0.0 | 324.0 | 0.0 | 0.0 | 0.1 | 32.8 | 0.0 |
| test_w402_reads_postgres.py | 6 | 336.3 | 1.6 | 3.5 | 0.0 | 314.6 | 0.0 | 0.0 | 0.1 | 16.4 | 0.0 |
| test_w504_ev_intent_postgres.py | 15 | 335.9 | 12.1 | 7.1 | 26.3 | 264.2 | 0.2 | 0.0 | 9.8 | 12.8 | 3.4 |
| test_w303_portfolio_comparison_postgres.py | 4 | 298.9 | 1.8 | 4.8 | 21.4 | 239.3 | 0.3 | 0.0 | 0.1 | 28.8 | 2.4 |
| test_w403_opportunity_scan_postgres.py | 5 | 279.4 | 1.3 | 2.5 | 0.0 | 274.6 | 0.0 | 0.0 | 0.1 | 0.9 | 0.0 |
| test_w403_replay_postgres.py | 2 | 268.7 | 1.0 | 0.9 | 0.0 | 156.8 | 5.0 | 0.0 | 0.1 | 104.9 | 0.0 |
| test_w203_cold_replay_postgres.py | 14 | 261.7 | 4.5 | 11.0 | 29.4 | 197.1 | 0.3 | 0.0 | 0.1 | 14.3 | 5.0 |
| test_w301_provenance_dto_postgres.py | 7 | 251.0 | 3.7 | 6.0 | 18.2 | 192.0 | 0.4 | 0.0 | 1.4 | 26.3 | 2.9 |
| test_w403_work_links_postgres.py | 3 | 250.0 | 1.2 | 2.0 | 0.0 | 211.5 | 0.2 | 0.0 | 0.1 | 35.0 | 0.0 |
| test_w503_ev_depth_postgres.py | 15 | 248.2 | 2.4 | 4.8 | 18.2 | 199.8 | 0.9 | 0.0 | 0.0 | 21.4 | 0.7 |
| test_w403_opportunity_job_isolation_postgres.py | 5 | 234.4 | 1.8 | 2.7 | 0.0 | 206.9 | 0.0 | 0.0 | 0.1 | 20.4 | 2.6 |
| test_w502_domain_intent_postgres.py | 11 | 210.1 | 9.1 | 8.7 | 25.8 | 146.5 | 0.7 | 0.0 | 9.4 | 6.8 | 3.1 |
| test_w501_cold_depth_postgres.py | 12 | 209.4 | 4.3 | 9.9 | 27.1 | 150.9 | 0.4 | 0.0 | 0.1 | 14.5 | 2.2 |
| test_w202_cold_replay_postgres.py | 12 | 202.2 | 3.7 | 9.0 | 25.1 | 151.2 | 1.5 | 0.0 | 0.1 | 9.1 | 2.6 |
| test_w301_estate_golden_postgres.py | 6 | 200.2 | 2.7 | 4.4 | 13.1 | 146.8 | 0.2 | 0.0 | 0.0 | 31.5 | 1.5 |
| test_w504_ev_intent_api.py | 6 | 186.3 | 1.9 | 4.2 | 12.9 | 148.9 | 0.3 | 0.0 | 6.1 | 10.4 | 1.5 |
| test_w302_pinned_facades_postgres.py | 8 | 171.7 | 2.6 | 4.4 | 13.6 | 138.6 | 0.1 | 0.0 | 0.2 | 10.8 | 1.4 |
| test_s4_schedule_health_postgres.py | 9 | 168.7 | 1.5 | 0.0 | 0.0 | 31.2 | 0.0 | 0.0 | 0.1 | 133.1 | 2.9 |
| test_w501_cold_scenarios_postgres.py | 7 | 165.7 | 8.5 | 4.5 | 13.6 | 85.7 | 0.3 | 0.0 | 0.1 | 51.1 | 2.0 |
| test_w302_money_comparability_postgres.py | 6 | 152.5 | 0.9 | 2.5 | 12.0 | 126.0 | 0.2 | 0.0 | 0.0 | 9.7 | 1.2 |

### Site set-ups

- root builds 736 across 624 tests; distinct set-ups 107; world time (db+install+gateway+build) in those tests 12452.7 s

| builds | world s | fingerprint | files |
| ---: | ---: | --- | --- |
| 64 | 1761.9 | `["test_w205b_ev_replay_postgres.Chain.open", "complete", {}, "start_release_upload"]` | test_w205b_ev_replay_postgres.py, test_w206_ev_publication_enqueue_postgres.py, test_w206_ev_reads_postgres.py, test_w206_ev_store_postgres.py ... |
| 139 | 990.4 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}, "d1e45727", "5ea3ed85", "84593783"]` | test_s405_resolver_postgres.py, test_s4_consequence_history_postgres.py, test_s4_consequence_recompute_postgres.py, test_s4_consequence_store_postgres.py ... |
| 38 | 982.1 | `["test_w205b_ev_replay_postgres.Chain.open", "interrupted", {}, "start_release_upload"]` | test_cc_placement_postgres.py, test_r373_request_access.py, test_w205b_ev_replay_postgres.py, test_w206_ev_reads_postgres.py ... |
| 41 | 828.4 | `["test_w402_reads_postgres._setup", ["<PostgresFoundationStore>", "<Engine>"], {}]` | test_w402_reads_postgres.py, test_w403_opportunity_job_isolation_postgres.py, test_w403_opportunity_links_postgres.py, test_w403_opportunity_read_postgres.py ... |
| 34 | 772.1 | `["test_w402_reads_postgres._reconcile", ["<Engine>", ["2026-10-06", "2026-10-07", "2026-10-08", "2026-10-09", "2026-10-10"]], {}]` | test_w402_reads_postgres.py, test_w403_opportunity_job_isolation_postgres.py, test_w403_opportunity_links_postgres.py, test_w403_opportunity_read_postgres.py ... |
| 23 | 685.2 | `["test_w205b_ev_replay_postgres.Chain.open", "late-record", {}, "start_release_upload", "advance_late"]` | test_w205b_ev_replay_postgres.py, test_w206_ev_reads_postgres.py, test_w206_ev_store_postgres.py, test_w207_ev_money_postgres.py ... |
| 8 | 663.9 | `["test_w303_portfolio_fixture_postgres.build_portfolio_fixture", ["<SubRequest>", "<MonkeyPatch>", "<CaptureFixture>"], {}]` | test_w303_portfolio_comparison_postgres.py, test_w303_portfolio_fixture_postgres.py, test_w303_portfolio_scope_snapshot_postgres.py |
| 38 | 654.0 | `["test_w202_cold_replay_postgres.Chain.open", "backup-failed", {}, "start_release_upload"]` | test_r373_request_access.py, test_w202_cold_replay_postgres.py, test_w203_cold_reads_postgres.py, test_w203_cold_replay_postgres.py ... |
| 30 | 616.0 | `["test_w402_reads_postgres._ingest", ["<Engine>", "<MgW402Install>"], {}]` | test_w402_reads_postgres.py, test_w403_opportunity_job_isolation_postgres.py, test_w403_opportunity_links_postgres.py, test_w403_opportunity_read_postgres.py ... |
| 23 | 356.1 | `["test_w202_cold_replay_postgres.Chain.open", "late-reading", {}, "start_release_upload"]` | test_w203_cold_replay_postgres.py, test_w204_cold_consequence.py, test_w301_cold_selection_on_postgres.py, test_w301_estate_index_postgres.py ... |
| 12 | 351.7 | `["test_w205b_ev_replay_postgres.Chain.open", "missing-meter", {}, "start_release_upload"]` | test_w205b_ev_replay_postgres.py, test_w206_ev_reads_postgres.py, test_w206_ev_store_postgres.py, test_w207_ev_money_postgres.py ... |
| 20 | 341.2 | `["test_w202_cold_replay_postgres.Chain.open", "excursion", {}, "start_release_upload"]` | test_w202_cold_replay_postgres.py, test_w203_cold_reads_postgres.py, test_w203_cold_replay_postgres.py, test_w204_cold_consequence.py ... |
| 10 | 288.1 | `["test_w205b_ev_replay_postgres.Chain.open", "fault", {}, "start_release_upload"]` | test_w205b_ev_replay_postgres.py, test_w206_ev_reads_postgres.py, test_w206_ev_store_postgres.py, test_w207_ev_money_postgres.py ... |
| 14 | 241.4 | `["test_w202_cold_replay_postgres.Chain.open", "late-reading", {}, "start_release_upload", "advance_late"]` | test_w202_cold_replay_postgres.py, test_w203_cold_reads_postgres.py, test_w203_cold_replay_postgres.py, test_w204_cold_consequence.py ... |
| 8 | 237.6 | `["test_w205b_ev_replay_postgres.Chain.open", "contradictory", {}, "start_release_upload"]` | test_w205b_ev_replay_postgres.py, test_w206_ev_reads_postgres.py, test_w206_ev_store_postgres.py, test_w207_ev_money_postgres.py ... |
| 11 | 198.2 | `["test_w202_cold_replay_postgres.Chain.open", "normal", {}, "start_release_upload"]` | test_w202_cold_replay_postgres.py, test_w203_cold_replay_postgres.py, test_w204_cold_consequence.py, test_w204_cold_reads.py ... |
| 4 | 161.1 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}, "df3b67c6", "5ea3ed85", "c9135f1a", "eee679ae", "5ea3ed85", "c9135f1a", "f4a8` | test_s4_finding_evidence_history_postgres.py, test_s4_finding_index_postgres.py, test_s4_finding_read_postgres.py, test_s4_finding_store_postgres.py |
| 30 | 142.0 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}, "df3b67c6", "5ea3ed85", "c9135f1a"]` | test_s4_finding_evidence_history_postgres.py, test_s4_finding_store_postgres.py, test_s6_action_apply_postgres.py, test_s6_action_store_postgres.py ... |
| 9 | 135.4 | `["test_w402_reads_postgres._reconcile", ["<Engine>", ["2026-10-07"]], {}]` | test_w402_reads_postgres.py, test_w403_opportunity_read_postgres.py, test_w403_scenarios_postgres.py |
| 7 | 121.8 | `["test_w202_cold_replay_postgres.Chain.open", "missing-probe", {}, "start_release_upload"]` | test_w202_cold_replay_postgres.py, test_w203_cold_reads_postgres.py, test_w203_cold_replay_postgres.py, test_w204_cold_consequence.py ... |
| 2 | 101.1 | `["test_w301_estate_golden_postgres.mixed_replay", ["<TopRequest>", "<MonkeyPatch>", "<timedelta>"], {}]` | test_w301_estate_golden_postgres.py |
| 1 | 95.4 | `["test_w303_portfolio_fixture_postgres.build_portfolio_fixture", ["<TopRequest>", "<MonkeyPatch>", "<CaptureFixture>"], {}]` | test_cc_placement_postgres.py |
| 6 | 87.4 | `["test_w202_cold_replay_postgres.Chain.start_release_upload"]` | test_w502_cold_scenario_producer.py, test_w502_domain_work_links_postgres.py |
| 3 | 85.0 | `["test_w205b_ev_replay_postgres.Chain.open", "interrupted", {"fresh": true}, "start_release_upload"]` | test_w504_ev_work_producer_postgres.py |
| 1 | 79.4 | `["test_w303_portfolio_fixture_postgres.build_portfolio_fixture", ["<TopRequest>", "<MonkeyPatch>", "<CaptureFixture>"], {"w1_source": "UNBOU` | test_w303_portfolio_scope_snapshot_postgres.py |
| 1 | 79.1 | `["test_w303_portfolio_fixture_postgres.build_portfolio_fixture", ["<TopRequest>", "<MonkeyPatch>", "<CaptureFixture>"], {"cold_drain": true}` | test_w303_portfolio_scope_snapshot_postgres.py |
| 1 | 78.9 | `["test_w303_portfolio_fixture_postgres.build_portfolio_fixture", ["<TopRequest>", "<MonkeyPatch>", "<CaptureFixture>"], {"cold_drain": false` | test_w303_portfolio_scope_snapshot_postgres.py |
| 1 | 77.7 | `["test_w303_portfolio_fixture_postgres.build_portfolio_fixture", ["<TopRequest>", "<MonkeyPatch>", "<CaptureFixture>"], {"w1_source": "MIXED` | test_w303_portfolio_scope_snapshot_postgres.py |
| 4 | 74.6 | `["test_w202_cold_replay_postgres.Chain.open", "contradictory", {}, "start_release_upload"]` | test_w202_cold_replay_postgres.py, test_w203_cold_replay_postgres.py, test_w204_cold_consequence.py, test_w501_cold_depth_postgres.py |
| 18 | 70.1 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}, "8728a720"]` | test_s4_evidence_decided_at_postgres.py, test_s4_schedule_health_postgres.py, test_s4_schedule_tick_postgres.py |
| 5 | 65.8 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}, "df3b67c6", "5ea3ed85", "c9135f1a", "eee679ae", "5ea3ed85", "c9135f1a", "f4a8` | test_s6_site_action_index_postgres.py, test_s6_verification_evaluator_postgres.py, test_s6_verification_holds_postgres.py, test_w303_portfolio_comparison_postgres.py |
| 2 | 56.6 | `["test_w205b_ev_replay_postgres.Chain.open", "complete", {"fresh": false, "install": "<install_second_ev_site>", "scenario_id": "ev-complete` | test_w302_money_comparability_postgres.py |
| 15 | 54.0 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}]` | test_s3_capability_read_postgres.py, test_s3_claim_limit_postgres.py, test_s4_evidence_consequence_work_postgres.py, test_s4_evidence_decided_at_postgres.py ... |
| 4 | 49.0 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}, "df3b67c6", "5ea3ed85", "c9135f1a", "eee679ae", "5ea3ed85", "c9135f1a", "f4a8` | test_s6_verification_evaluator_postgres.py, test_s6_verification_holds_postgres.py, test_w301_estate_index_postgres.py |
| 4 | 48.7 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}, "eee679ae", "5ea3ed85", "c9135f1a"]` | test_w403_alternative_postgres.py, test_w403_replay_postgres.py |
| 5 | 41.6 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}, "df3b67c6", "5ea3ed85", "c9135f1a", "eee679ae", "5ea3ed85", "c9135f1a", "f4a8` | test_s6_action_apply_postgres.py, test_s6_verification_plan_postgres.py, test_w401_work_service_postgres.py |
| 2 | 34.3 | `["test_w402_reads_postgres._reconcile", ["<Engine>", ["2026-10-07", "2026-10-08", "2026-10-09", "2026-10-10"]], {}]` | test_w403_opportunity_scan_postgres.py, test_w403_opportunity_worker_postgres.py |
| 2 | 34.2 | `["test_w402_reads_postgres._reconcile", ["<Engine>", ["2026-10-08"]], {}]` | test_w402_reads_postgres.py, test_w403_replay_postgres.py |
| 3 | 31.8 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}, "49f61049", "5ea3ed85", "df74c549", "52464e7b", "5ea3ed85", "c9135f1a", "4ff2` | test_w301_estate_golden_postgres.py, test_w301_estate_index_postgres.py |
| 4 | 30.7 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}, "df3b67c6", "5ea3ed85", "c9135f1a", "169ced82"]` | test_s4_finding_store_postgres.py, test_w301_estate_index_postgres.py, test_w303_portfolio_scope_snapshot_postgres.py |
| 1 | 30.1 | `["test_w205b_ev_replay_postgres.Chain.open", "late-record", {}, "start_release_upload", "advance_late", "advance_late"]` | test_w205b_ev_replay_postgres.py |
| 1 | 28.8 | `["test_w205b_ev_replay_postgres.Chain.open", "complete", {}, "start_release_upload", "release_and_upload"]` | test_w205b_ev_replay_postgres.py |
| 1 | 28.6 | `["test_w205b_ev_replay_postgres.Chain.open", "late-record", {}, "start_release_upload"]` | test_w301_provenance_dto_postgres.py |
| 5 | 25.5 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}, "5ea3ed85", "c9135f1a"]` | test_s4_power_demo_case_postgres.py |
| 2 | 25.1 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}, "df3b67c6", "5ea3ed85", "c9135f1a", "eee679ae", "5ea3ed85", "c9135f1a", "f4a8` | test_s6_verification_holds_postgres.py |
| 4 | 24.2 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}, "57523b03", "5ea3ed85", "1766a32b", "5ea3ed85"]` | test_w301_w1_snapshot_helpers_postgres.py, test_w302_w1_claim_limit_on_postgres.py |
| 4 | 20.2 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}, "5ea3ed85", "5ea3ed85"]` | test_lr01_money_eligibility_postgres.py, test_s4_power_demo_case_postgres.py, test_w301_w1_money_snapshot_helpers_postgres.py |
| 1 | 18.6 | `["test_w402_reads_postgres._reconcile", ["<Engine>", ["2026-10-08", "2026-10-09", "2026-10-10", "2026-10-11", "2026-10-12"]], {}]` | test_w403_replay_postgres.py |
| 1 | 16.7 | `["test_w202_cold_replay_postgres.Chain.open", "normal", {}, "start_release_upload", "release_and_upload"]` | test_w202_cold_replay_postgres.py |
| 2 | 15.4 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}, "df3b67c6", "5ea3ed85", "c9135f1a", "5ea3ed85", "84593783", "67d09500", "5ea3` | test_s6_verification_evaluator_postgres.py, test_w303_selectors_postgres.py |
| 3 | 15.1 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}, "df3b67c6", "5ea3ed85", "c9135f1a", "5ea3ed85", "84593783"]` | test_s6_verification_evaluator_postgres.py, test_s6_verification_plan_postgres.py |
| 1 | 14.3 | `["test_w402_reads_postgres._reconcile", ["<Engine>", ["2026-10-05"]], {}]` | test_w403_opportunity_read_postgres.py |
| 3 | 14.2 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}, "71f11bc5", "5ea3ed85", "c9135f1a"]` | test_r373_request_access.py, test_w601b_global_maintenance.py, test_w601c_request_detail.py |
| 1 | 13.9 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}, "df3b67c6", "5ea3ed85", "c9135f1a", "eee679ae", "5ea3ed85", "c9135f1a", "f4a8` | test_s6_verification_holds_postgres.py |
| 1 | 13.8 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}, "df3b67c6", "5ea3ed85", "c9135f1a", "eee679ae", "5ea3ed85", "c9135f1a", "f4a8` | test_s6_verification_evaluator_postgres.py |
| 1 | 13.7 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}, "df3b67c6", "5ea3ed85", "c9135f1a", "eee679ae", "5ea3ed85", "c9135f1a", "f4a8` | test_s6_verification_holds_postgres.py |
| 1 | 12.6 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}, "df3b67c6", "5ea3ed85", "c9135f1a", "eee679ae", "5ea3ed85", "c9135f1a", "f4a8` | test_s6_verification_evaluator_postgres.py |
| 2 | 12.6 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}, "eee679ae", "5ea3ed85", "c9135f1a", "f4a8e3ba", "5ea3ed85", "c9135f1a"]` | test_w403_alternative_postgres.py |
| 2 | 11.8 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}, "8319ad7d", "5ea3ed85", "718bbd33", "5ea3ed85", "dcee202f", "5ea3ed85"]` | test_s4_deferred_match_postgres.py |
| 1 | 10.8 | `["test_w402_reads_postgres._reconcile", ["<Engine>", ["2026-10-09"]], {}]` | test_w402_reads_postgres.py |

Distinct per-test set-ups (ordered root builds of one test): 121

| tests | world s | set-up | files |
| ---: | ---: | --- | --- |
| 59 | 1625.2 | `["test_w205b_ev_replay_postgres.Chain.open", "complete", {}, "start_release_upload"]` | test_w205b_ev_replay_postgres.py, test_w206_ev_publication_enqueue_postgres.py, test_w206_ev_reads_postgres.py, test_w206_ev_store_postgres.py ... |
| 22 | 1489.4 | `["test_w402_reads_postgres._setup", ["<PostgresFoundationStore>", "<Engine>"], {}] + ["test_w402_reads_postgres._ingest", ["<Engine>", "<MgW402Install>"], {}] +` | test_w402_reads_postgres.py, test_w403_opportunity_job_isolation_postgres.py, test_w403_opportunity_links_postgres.py, test_w403_opportunity_read_postgres.py ... |
| 137 | 983.6 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}, "d1e45727", "5ea3ed85", "84593783"]` | test_s405_resolver_postgres.py, test_s4_consequence_history_postgres.py, test_s4_consequence_recompute_postgres.py, test_s4_consequence_store_postgres.py ... |
| 35 | 903.2 | `["test_w205b_ev_replay_postgres.Chain.open", "interrupted", {}, "start_release_upload"]` | test_cc_placement_postgres.py, test_r373_request_access.py, test_w205b_ev_replay_postgres.py, test_w206_ev_reads_postgres.py ... |
| 8 | 663.9 | `["test_w303_portfolio_fixture_postgres.build_portfolio_fixture", ["<SubRequest>", "<MonkeyPatch>", "<CaptureFixture>"], {}]` | test_w303_portfolio_comparison_postgres.py, test_w303_portfolio_fixture_postgres.py, test_w303_portfolio_scope_snapshot_postgres.py |
| 38 | 654.0 | `["test_w202_cold_replay_postgres.Chain.open", "backup-failed", {}, "start_release_upload"]` | test_r373_request_access.py, test_w202_cold_replay_postgres.py, test_w203_cold_reads_postgres.py, test_w203_cold_replay_postgres.py ... |
| 21 | 629.4 | `["test_w205b_ev_replay_postgres.Chain.open", "late-record", {}, "start_release_upload", "advance_late"]` | test_w205b_ev_replay_postgres.py, test_w206_ev_reads_postgres.py, test_w206_ev_store_postgres.py, test_w207_ev_money_postgres.py ... |
| 18 | 303.7 | `["test_w202_cold_replay_postgres.Chain.open", "late-reading", {}, "start_release_upload"]` | test_w203_cold_replay_postgres.py, test_w204_cold_consequence.py, test_w301_cold_selection_on_postgres.py, test_w301_estate_index_postgres.py ... |
| 18 | 301.1 | `["test_w202_cold_replay_postgres.Chain.open", "excursion", {}, "start_release_upload"]` | test_w202_cold_replay_postgres.py, test_w203_cold_reads_postgres.py, test_w203_cold_replay_postgres.py, test_w204_cold_consequence.py ... |
| 4 | 251.2 | `["test_w402_reads_postgres._setup", ["<PostgresFoundationStore>", "<Engine>"], {}] + ["test_w402_reads_postgres._reconcile", ["<Engine>", ["2026-10-06", "2026-1` | test_w402_reads_postgres.py, test_w403_opportunity_read_postgres.py, test_w403_opportunity_worker_postgres.py, test_w403_scenarios_postgres.py |
| 14 | 241.4 | `["test_w202_cold_replay_postgres.Chain.open", "late-reading", {}, "start_release_upload", "advance_late"]` | test_w202_cold_replay_postgres.py, test_w203_cold_reads_postgres.py, test_w203_cold_replay_postgres.py, test_w204_cold_consequence.py ... |
| 8 | 240.1 | `["test_w205b_ev_replay_postgres.Chain.open", "missing-meter", {}, "start_release_upload"]` | test_w205b_ev_replay_postgres.py, test_w206_ev_reads_postgres.py, test_w206_ev_store_postgres.py, test_w207_ev_money_postgres.py ... |
| 6 | 181.7 | `["test_w205b_ev_replay_postgres.Chain.open", "contradictory", {}, "start_release_upload"]` | test_w205b_ev_replay_postgres.py, test_w206_ev_reads_postgres.py, test_w206_ev_store_postgres.py, test_w207_ev_money_postgres.py ... |
| 10 | 181.1 | `["test_w202_cold_replay_postgres.Chain.open", "normal", {}, "start_release_upload"]` | test_w202_cold_replay_postgres.py, test_w203_cold_replay_postgres.py, test_w204_cold_consequence.py, test_w204_cold_reads.py ... |
| 6 | 180.7 | `["test_w205b_ev_replay_postgres.Chain.open", "fault", {}, "start_release_upload"]` | test_w205b_ev_replay_postgres.py, test_w206_ev_reads_postgres.py, test_w206_ev_store_postgres.py, test_w207_ev_money_postgres.py ... |
| 1 | 171.5 | `["test_w205b_ev_replay_postgres.Chain.open", "complete", {}, "start_release_upload"] + ["test_w205b_ev_replay_postgres.Chain.open", "interrupted", {}, "start_re` | test_w301_provenance_dto_postgres.py |
| 1 | 163.8 | `["test_w205b_ev_replay_postgres.Chain.open", "complete", {}, "start_release_upload"] + ["test_w205b_ev_replay_postgres.Chain.open", "interrupted", {}, "start_re` | test_w205b_ev_replay_postgres.py |
| 4 | 161.1 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}, "df3b67c6", "5ea3ed85", "c9135f1a", "eee679ae", "5ea3ed85", "c9135f1a", "f4a8e3ba", "5ea3ed85", "` | test_s4_finding_evidence_history_postgres.py, test_s4_finding_index_postgres.py, test_s4_finding_read_postgres.py, test_s4_finding_store_postgres.py |
| 2 | 137.4 | `["test_w402_reads_postgres._setup", ["<PostgresFoundationStore>", "<Engine>"], {}] + ["test_w402_reads_postgres._reconcile", ["<Engine>", ["2026-10-07", "2026-1` | test_w403_opportunity_scan_postgres.py, test_w403_opportunity_worker_postgres.py |
| 2 | 131.2 | `["test_w402_reads_postgres._setup", ["<PostgresFoundationStore>", "<Engine>"], {}] + ["test_w402_reads_postgres._reconcile", ["<Engine>", ["2026-10-06", "2026-1` | test_w403_opportunity_read_postgres.py, test_w403_scenarios_postgres.py |
| 7 | 121.8 | `["test_w202_cold_replay_postgres.Chain.open", "missing-probe", {}, "start_release_upload"]` | test_w202_cold_replay_postgres.py, test_w203_cold_reads_postgres.py, test_w203_cold_replay_postgres.py, test_w204_cold_consequence.py ... |
| 2 | 113.2 | `["test_w205b_ev_replay_postgres.Chain.open", "complete", {}, "start_release_upload"] + ["test_w205b_ev_replay_postgres.Chain.open", "complete", {"fresh": false,` | test_w302_money_comparability_postgres.py |
| 27 | 110.3 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}, "df3b67c6", "5ea3ed85", "c9135f1a"]` | test_s4_finding_evidence_history_postgres.py, test_s4_finding_store_postgres.py, test_s6_action_apply_postgres.py, test_s6_action_store_postgres.py ... |
| 2 | 101.1 | `["test_w301_estate_golden_postgres.mixed_replay", ["<TopRequest>", "<MonkeyPatch>", "<timedelta>"], {}]` | test_w301_estate_golden_postgres.py |
| 1 | 95.4 | `["test_w303_portfolio_fixture_postgres.build_portfolio_fixture", ["<TopRequest>", "<MonkeyPatch>", "<CaptureFixture>"], {}]` | test_cc_placement_postgres.py |
| 1 | 92.8 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}, "eee679ae", "5ea3ed85", "c9135f1a"] + ["test_w402_reads_postgres._setup", ["<PostgresFoundationSt` | test_w403_replay_postgres.py |
| 3 | 85.0 | `["test_w205b_ev_replay_postgres.Chain.open", "interrupted", {"fresh": true}, "start_release_upload"]` | test_w504_ev_work_producer_postgres.py |
| 1 | 79.4 | `["test_w303_portfolio_fixture_postgres.build_portfolio_fixture", ["<TopRequest>", "<MonkeyPatch>", "<CaptureFixture>"], {"w1_source": "UNBOUND"}]` | test_w303_portfolio_scope_snapshot_postgres.py |
| 1 | 79.1 | `["test_w303_portfolio_fixture_postgres.build_portfolio_fixture", ["<TopRequest>", "<MonkeyPatch>", "<CaptureFixture>"], {"cold_drain": true}]` | test_w303_portfolio_scope_snapshot_postgres.py |
| 1 | 78.9 | `["test_w303_portfolio_fixture_postgres.build_portfolio_fixture", ["<TopRequest>", "<MonkeyPatch>", "<CaptureFixture>"], {"cold_drain": false}]` | test_w303_portfolio_scope_snapshot_postgres.py |
| 5 | 78.8 | `["test_w202_cold_replay_postgres.Chain.start_release_upload"]` | test_w502_cold_scenario_producer.py, test_w502_domain_work_links_postgres.py |
| 1 | 77.7 | `["test_w303_portfolio_fixture_postgres.build_portfolio_fixture", ["<TopRequest>", "<MonkeyPatch>", "<CaptureFixture>"], {"w1_source": "MIXED"}]` | test_w303_portfolio_scope_snapshot_postgres.py |
| 4 | 74.6 | `["test_w202_cold_replay_postgres.Chain.open", "contradictory", {}, "start_release_upload"]` | test_w202_cold_replay_postgres.py, test_w203_cold_replay_postgres.py, test_w204_cold_consequence.py, test_w501_cold_depth_postgres.py |
| 1 | 71.3 | `["test_w402_reads_postgres._setup", ["<PostgresFoundationStore>", "<Engine>"], {}] + ["test_w402_reads_postgres._ingest", ["<Engine>", "<MgW402Install>"], {}] +` | test_w403_opportunity_read_postgres.py |
| 1 | 68.9 | `["test_w402_reads_postgres._setup", ["<PostgresFoundationStore>", "<Engine>"], {}] + ["test_w402_reads_postgres._ingest", ["<Engine>", "<MgW402Install>"], {}] +` | test_w403_opportunity_read_postgres.py |
| 17 | 67.0 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}, "8728a720"]` | test_s4_evidence_decided_at_postgres.py, test_s4_schedule_health_postgres.py, test_s4_schedule_tick_postgres.py |
| 1 | 65.9 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}, "eee679ae", "5ea3ed85", "c9135f1a"] + ["test_w402_reads_postgres._setup", ["<PostgresFoundationSt` | test_w403_replay_postgres.py |
| 5 | 65.8 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}, "df3b67c6", "5ea3ed85", "c9135f1a", "eee679ae", "5ea3ed85", "c9135f1a", "f4a8e3ba", "5ea3ed85", "` | test_s6_site_action_index_postgres.py, test_s6_verification_evaluator_postgres.py, test_s6_verification_holds_postgres.py, test_w303_portfolio_comparison_postgres.py |
| 3 | 63.2 | `["test_w202_cold_replay_postgres.Chain.open", "late-reading", {}, "start_release_upload"] + ["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}, "df3b` | test_w301_estate_index_postgres.py |
| 1 | 57.0 | `["test_w205b_ev_replay_postgres.Chain.open", "missing-meter", {}, "start_release_upload"] + ["test_w205b_ev_replay_postgres.Chain.open", "late-record", {}, "sta` | test_w503_ev_depth_postgres.py |
| 1 | 54.5 | `["test_w205b_ev_replay_postgres.Chain.open", "fault", {}, "start_release_upload"] + ["test_w205b_ev_replay_postgres.Chain.open", "missing-meter", {}, "start_rel` | test_w503_ev_scenarios_postgres.py |
| 1 | 53.8 | `["test_w402_reads_postgres._setup", ["<PostgresFoundationStore>", "<Engine>"], {}] + ["test_w402_reads_postgres._ingest", ["<Engine>", "<MgW402Install>"], {}] +` | test_w402_reads_postgres.py |
| 4 | 49.0 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}, "df3b67c6", "5ea3ed85", "c9135f1a", "eee679ae", "5ea3ed85", "c9135f1a", "f4a8e3ba", "5ea3ed85", "` | test_s6_verification_evaluator_postgres.py, test_s6_verification_holds_postgres.py, test_w301_estate_index_postgres.py |
| 1 | 48.5 | `["test_w205b_ev_replay_postgres.Chain.open", "complete", {}, "start_release_upload"] + ["test_w205b_ev_replay_postgres.Chain.open", "fault", {}, "start_release_` | test_w503_ev_scenarios_postgres.py |
| 1 | 47.8 | `["test_w402_reads_postgres._setup", ["<PostgresFoundationStore>", "<Engine>"], {}] + ["test_w402_reads_postgres._ingest", ["<Engine>", "<MgW402Install>"], {}] +` | test_w402_reads_postgres.py |
| 1 | 47.0 | `["test_w402_reads_postgres._setup", ["<PostgresFoundationStore>", "<Engine>"], {}] + ["test_w402_reads_postgres._ingest", ["<Engine>", "<MgW402Install>"], {}] +` | test_w402_reads_postgres.py |
| 1 | 46.1 | `["test_w202_cold_replay_postgres.Chain.open", "excursion", {}, "start_release_upload"] + ["test_w205b_ev_replay_postgres.Chain.open", "interrupted", {}, "start_` | test_w401_site_indexes_postgres.py |
| 1 | 45.6 | `["test_w402_reads_postgres._setup", ["<PostgresFoundationStore>", "<Engine>"], {}] + ["test_w402_reads_postgres._reconcile", ["<Engine>", ["2026-10-07"]], {}] +` | test_w402_reads_postgres.py |
| 2 | 41.7 | `["test_w202_cold_replay_postgres.Chain.open", "late-reading", {}, "start_release_upload"] + ["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}, "df3b` | test_w301_estate_index_postgres.py |
| 5 | 41.6 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}, "df3b67c6", "5ea3ed85", "c9135f1a", "eee679ae", "5ea3ed85", "c9135f1a", "f4a8e3ba", "5ea3ed85", "` | test_s6_action_apply_postgres.py, test_s6_verification_plan_postgres.py, test_w401_work_service_postgres.py |
| 1 | 34.2 | `["test_w202_cold_replay_postgres.Chain.open", "normal", {}, "start_release_upload"] + ["test_w202_cold_replay_postgres.Chain.open", "excursion", {}, "start_rele` | test_w301_provenance_dto_postgres.py |
| 3 | 31.8 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}, "49f61049", "5ea3ed85", "df74c549", "52464e7b", "5ea3ed85", "c9135f1a", "4ff271a6", "5ea3ed85", "` | test_w301_estate_golden_postgres.py, test_w301_estate_index_postgres.py |
| 1 | 30.1 | `["test_w205b_ev_replay_postgres.Chain.open", "late-record", {}, "start_release_upload", "advance_late", "advance_late"]` | test_w205b_ev_replay_postgres.py |
| 1 | 28.8 | `["test_w205b_ev_replay_postgres.Chain.open", "complete", {}, "start_release_upload", "release_and_upload"]` | test_w205b_ev_replay_postgres.py |
| 5 | 25.5 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}, "5ea3ed85", "c9135f1a"]` | test_s4_power_demo_case_postgres.py |
| 2 | 25.1 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}, "df3b67c6", "5ea3ed85", "c9135f1a", "eee679ae", "5ea3ed85", "c9135f1a", "f4a8e3ba", "5ea3ed85", "` | test_s6_verification_holds_postgres.py |
| 4 | 24.2 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}, "57523b03", "5ea3ed85", "1766a32b", "5ea3ed85"]` | test_w301_w1_snapshot_helpers_postgres.py, test_w302_w1_claim_limit_on_postgres.py |
| 4 | 20.2 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}, "5ea3ed85", "5ea3ed85"]` | test_lr01_money_eligibility_postgres.py, test_s4_power_demo_case_postgres.py, test_w301_w1_money_snapshot_helpers_postgres.py |
| 1 | 17.8 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}] + ["s6_action_records.build", ["<CaseRunner>", {"F01": {"case_id": "F01", "day": "2026-10-06", "l` | test_s6_action_records_postgres.py |
| 1 | 17.4 | `["test_s4_finding_store_postgres.CaseRunner.__init__", [], {}] + ["s6_action_records.build", ["<CaseRunner>", {"F01": {"case_id": "F01", "day": "2026-10-06", "l` | test_s6_site_action_index_postgres.py |

Most frequent write statements in the check phase of tests of 5 s or more:

- 81359 x `INSERT INTO mini_opportunity_evidence (tenant_id,`
- 24631 x `INSERT INTO mini_depth_revision_evidence (tenant_id,`
- 7440 x `INSERT INTO finding_revision_evidence (finding_revision_id,`
- 4756 x `INSERT INTO ingestion_disposition (batch_id,`
- 4755 x `INSERT INTO accepted_evidence (id,`
- 3090 x `UPDATE recompute_job SET status`
- 1392 x `INSERT INTO action_basis_evidence (action_id,`
- 1090 x `INSERT INTO signal_binding_revision (id,`
- 803 x `INSERT INTO financial_consequence_work_attempt (id,`
- 764 x `INSERT INTO source_clock_attestation (id,`
- 696 x `INSERT INTO action_basis_assessment (action_id,`
- 674 x `INSERT INTO financial_consequence_power_interval (consequence_revision_id,`
- 466 x `UPDATE schedule_site_head SET stage`
- 465 x `INSERT INTO analytic_run_assessment (run_id,`
- 463 x `INSERT INTO assessment_revision (id,`
- 421 x `INSERT INTO analytic_run (id,`
- 405 x `INSERT INTO analytic_run_selection (tenant_id,`
- 404 x `INSERT INTO analytic_run_evidence (run_id,`
- 393 x `INSERT INTO asset (id,`
- 320 x `INSERT INTO source (id,`
- 283 x `INSERT INTO evidence_publication (id,`
- 276 x `INSERT INTO verification_metric (outcome_id,`
- 214 x `INSERT INTO financial_assumption_assignment (id,`
- 176 x `INSERT INTO mini_depth_selection (tenant_id,`
- 168 x `INSERT INTO mini_depth_revision (id,`

### Read-only versus writes after the build (tests of 5 s or more)

```json
{
  "heavy_tests": 629,
  "heavy_seconds": 15146.3,
  "read_only_after_build": 87,
  "read_only_after_build_seconds": 2562.4,
  "writes_after_build": 542,
  "writes_after_build_seconds": 12583.9,
  "heavy_with_root_build": 597,
  "heavy_with_root_build_read_only": 73,
  "heavy_setup_fixture_writes": 83,
  "check_write_histogram": {
    "1-10": 110,
    "0": 87,
    "11-100": 349,
    ">100": 83
  }
}
```

