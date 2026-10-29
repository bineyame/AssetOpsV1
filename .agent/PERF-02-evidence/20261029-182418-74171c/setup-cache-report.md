# Set-up cache, run 20261029-182418-74171c

- ops: 820; hits 485, misses 50, live 285, verify 0
- measured copy cost (seconds per hit, restore of database + files + objects): median 0.39, mean 0.73, p90 1.41, total 352

| op family | hits | hit s | misses | miss s | live | live s | verify |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| w202_cold_replay_postgres.Chain.advance_late | 0 | 0 | 2 | 4 | 12 | 5 | 0 |
| w202_cold_replay_postgres.Chain.open | 108 | 39 | 6 | 15 | 21 | 37 | 0 |
| w202_cold_replay_postgres.Chain.release_and_upload | 0 | 0 | 1 | 1 | 1 | 0 | 0 |
| w202_cold_replay_postgres.Chain.start_release_upload | 4 | 5 | 6 | 98 | 129 | 1728 | 0 |
| w205b_ev_replay_postgres.Chain.advance_late | 3 | 5 | 2 | 6 | 20 | 47 | 0 |
| w205b_ev_replay_postgres.Chain.open | 146 | 46 | 7 | 23 | 39 | 85 | 0 |
| w205b_ev_replay_postgres.Chain.release_and_upload | 0 | 0 | 1 | 2 | 0 | 0 | 0 |
| w205b_ev_replay_postgres.Chain.start_release_upload | 137 | 178 | 14 | 393 | 40 | 917 | 0 |
| w402_reads_postgres._ingest | 25 | 32 | 2 | 99 | 3 | 141 | 0 |
| w402_reads_postgres._reconcile | 24 | 35 | 8 | 53 | 18 | 255 | 0 |
| w402_reads_postgres._setup | 38 | 13 | 1 | 1 | 2 | 1 | 0 |

Live (not cached) reasons:

- 108 x w202_cold_replay_postgres.Chain.start_release_upload: NotCached: the test wrote to the database since its previous op
- 25 x w205b_ev_replay_postgres.Chain.open: NotCached: a monkeypatch other than the UUID counter is active: setenv:ASSETOPS_ESTATE_PORTFOLIO_CURSOR_KEY_HEX, setitem
- 25 x w205b_ev_replay_postgres.Chain.start_release_upload: NotCached: a monkeypatch other than the UUID counter is active: setenv:ASSETOPS_ESTATE_PORTFOLIO_CURSOR_KEY_HEX, setitem
- 17 x w205b_ev_replay_postgres.Chain.advance_late: NotCached: the test wrote to the database since its previous op
- 14 x w402_reads_postgres._reconcile: NotCached: the test wrote to the database since its previous op
- 12 x w202_cold_replay_postgres.Chain.advance_late: NotCached: the test wrote to the database since its previous op
- 12 x w202_cold_replay_postgres.Chain.open: NotCached: a monkeypatch other than the UUID counter is active: setenv:ASSETOPS_ESTATE_PORTFOLIO_CURSOR_KEY_HEX, setitem
- 12 x w202_cold_replay_postgres.Chain.start_release_upload: NotCached: a monkeypatch other than the UUID counter is active: setenv:ASSETOPS_ESTATE_PORTFOLIO_CURSOR_KEY_HEX, setitem
- 8 x w202_cold_replay_postgres.Chain.open: NotCached: a monkeypatch other than the UUID counter is active: setattr:pg_harness.fresh_database
- 8 x w202_cold_replay_postgres.Chain.start_release_upload: NotCached: a monkeypatch other than the UUID counter is active: setattr:pg_harness.fresh_database
- 4 x w205b_ev_replay_postgres.Chain.open: NotCached: a monkeypatch other than the UUID counter is active: setattr:pg_harness.fresh_database
- 4 x w205b_ev_replay_postgres.Chain.start_release_upload: NotCached: a monkeypatch other than the UUID counter is active: setattr:pg_harness.fresh_database
- 3 x w205b_ev_replay_postgres.Chain.open: NotCached: a monkeypatch other than the UUID counter is active: setattr:assetops_backend.estate.financials.site_coverage
- 3 x w205b_ev_replay_postgres.Chain.start_release_upload: NotCached: a monkeypatch other than the UUID counter is active: setattr:assetops_backend.estate.financials.site_coverage
- 3 x w402_reads_postgres._ingest: NotCached: the test wrote to the database since its previous op
- 3 x w402_reads_postgres._reconcile: NotCached: a monkeypatch other than the UUID counter is active: setenv:DATABASE_URL, setitem:_Environ.DATABASE_URL, sete
- 3 x w205b_ev_replay_postgres.Chain.open: NotCached: a monkeypatch other than the UUID counter is active: setenv:DATABASE_URL, setitem:_Environ.DATABASE_URL
- 3 x w205b_ev_replay_postgres.Chain.start_release_upload: NotCached: a monkeypatch other than the UUID counter is active: setenv:DATABASE_URL, setitem:_Environ.DATABASE_URL
- 2 x w205b_ev_replay_postgres.Chain.open: NotCached: an injected scenario repository
- 2 x w205b_ev_replay_postgres.Chain.start_release_upload: NotCached: the test wrote to the database since its previous op
- 2 x w205b_ev_replay_postgres.Chain.advance_late: NotCached: a monkeypatch other than the UUID counter is active: setattr:test_w205b_ev_replay_postgres.LATE_DECISION
- 2 x w402_reads_postgres._setup: NotCached: a monkeypatch other than the UUID counter is active: setenv:DATABASE_URL, setitem:_Environ.DATABASE_URL, seta
- 1 x w205b_ev_replay_postgres.Chain.open: NotCached: a monkeypatch other than the UUID counter is active: setattr:_Tx.finding_pairs_in_scope
- 1 x w205b_ev_replay_postgres.Chain.start_release_upload: NotCached: a monkeypatch other than the UUID counter is active: setattr:_Tx.finding_pairs_in_scope
- 1 x w202_cold_replay_postgres.Chain.release_and_upload: NotCached: the test wrote to the database since its previous op
- 1 x w402_reads_postgres._reconcile: NotCached: a monkeypatch other than the UUID counter is active: setenv:DATABASE_URL, setitem:_Environ.DATABASE_URL, seta
- 1 x w202_cold_replay_postgres.Chain.open: NotCached: a monkeypatch other than the UUID counter is active: setattr:assetops_backend.analytics.adapters.postgres_ass
- 1 x w202_cold_replay_postgres.Chain.start_release_upload: NotCached: a monkeypatch other than the UUID counter is active: setattr:assetops_backend.analytics.adapters.postgres_ass
- 1 x w205b_ev_replay_postgres.Chain.advance_late: NotCached: a monkeypatch other than the UUID counter is active: setattr:PostgresEvidenceLedger.decide_chunk
- 1 x w205b_ev_replay_postgres.Chain.start_release_upload: NotCached: lab_execution.ev_reports is rebound by direct assignment
