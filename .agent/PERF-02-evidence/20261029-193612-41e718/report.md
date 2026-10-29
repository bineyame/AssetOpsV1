# Backend run 20261029-193612-41e718

- wall: 436 s (7.3 min)
- collected: 62; JUnit cases: 62; passed 62, failed 0, skipped 0
- summed test time (JUnit): 1754.3 s
- phases: set-up 33.4 s, call 1705.7 s, teardown 15.2 s; set-up share 0.019
- connections: peak server_total=29 client_backends=24 runner_sessions=23 assetops_test_dbs=23 samples=83
- memory: peak vm_used_mb=1780 vmmem_ws_mb=3718 runner_mem_mb=1058 pg_mem_mb=1612 runner_procs=15 runner_rss_sum_mb=879 runner_rss_max_mb=156 min win_free_mb=2965 vm_total_mb=3918 samples=73

## Slowest 40 files (summed per-test phases)

| file | tests | set-up s | call s | teardown s | set-up share |
| --- | ---: | ---: | ---: | ---: | ---: |
| tests/test_w402_reads_postgres.py | 6 | 5.2 | 374.3 | 0.0 | 0.01 |
| tests/test_w206_ev_store_postgres.py | 13 | 0.1 | 369.5 | 3.1 | 0.00 |
| tests/test_w207_ev_money_postgres.py | 14 | 23.9 | 300.4 | 4.5 | 0.07 |
| tests/test_w403_work_links_postgres.py | 3 | 3.9 | 255.2 | 0.0 | 0.02 |
| tests/test_w203_cold_replay_postgres.py | 14 | 0.1 | 251.0 | 4.7 | 0.00 |
| tests/test_w202_cold_replay_postgres.py | 12 | 0.1 | 155.4 | 3.0 | 0.00 |
