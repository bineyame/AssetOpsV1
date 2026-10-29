# Set-up cache, run 20261029-190123-49baed

- ops: 820; hits 535, misses 0, live 285, verify 0
- measured copy cost (seconds per hit, restore of database + files + objects): median 0.39, mean 0.77, p90 1.44, total 410

| op family | hits | hit s | misses | miss s | live | live s | verify |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| w202_cold_replay_postgres.Chain.advance_late | 2 | 4 | 0 | 0 | 12 | 5 | 0 |
| w202_cold_replay_postgres.Chain.open | 114 | 40 | 0 | 0 | 21 | 36 | 0 |
| w202_cold_replay_postgres.Chain.release_and_upload | 1 | 2 | 0 | 0 | 1 | 0 | 0 |
| w202_cold_replay_postgres.Chain.start_release_upload | 10 | 15 | 0 | 0 | 129 | 1754 | 0 |
| w205b_ev_replay_postgres.Chain.advance_late | 5 | 8 | 0 | 0 | 20 | 47 | 0 |
| w205b_ev_replay_postgres.Chain.open | 153 | 49 | 0 | 0 | 39 | 87 | 0 |
| w205b_ev_replay_postgres.Chain.release_and_upload | 1 | 2 | 0 | 0 | 0 | 0 | 0 |
| w205b_ev_replay_postgres.Chain.start_release_upload | 151 | 194 | 0 | 0 | 40 | 903 | 0 |
| w402_reads_postgres._ingest | 27 | 35 | 0 | 0 | 3 | 140 | 0 |
| w402_reads_postgres._reconcile | 32 | 50 | 0 | 0 | 18 | 257 | 0 |
| w402_reads_postgres._setup | 39 | 12 | 0 | 0 | 2 | 1 | 0 |

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
- 3 x w402_reads_postgres._ingest: NotCached: the test wrote to the database since its previous op
- 3 x w402_reads_postgres._reconcile: NotCached: a monkeypatch other than the UUID counter is active: setenv:DATABASE_URL, setitem:_Environ.DATABASE_URL, sete
- 3 x w205b_ev_replay_postgres.Chain.open: NotCached: a monkeypatch other than the UUID counter is active: setenv:DATABASE_URL, setitem:_Environ.DATABASE_URL
- 3 x w205b_ev_replay_postgres.Chain.start_release_upload: NotCached: a monkeypatch other than the UUID counter is active: setenv:DATABASE_URL, setitem:_Environ.DATABASE_URL
- 3 x w205b_ev_replay_postgres.Chain.open: NotCached: a monkeypatch other than the UUID counter is active: setattr:assetops_backend.estate.financials.site_coverage
- 3 x w205b_ev_replay_postgres.Chain.start_release_upload: NotCached: a monkeypatch other than the UUID counter is active: setattr:assetops_backend.estate.financials.site_coverage
- 2 x w205b_ev_replay_postgres.Chain.advance_late: NotCached: a monkeypatch other than the UUID counter is active: setattr:test_w205b_ev_replay_postgres.LATE_DECISION
- 2 x w402_reads_postgres._setup: NotCached: a monkeypatch other than the UUID counter is active: setenv:DATABASE_URL, setitem:_Environ.DATABASE_URL, seta
- 2 x w205b_ev_replay_postgres.Chain.open: NotCached: an injected scenario repository
- 2 x w205b_ev_replay_postgres.Chain.start_release_upload: NotCached: the test wrote to the database since its previous op
- 1 x w202_cold_replay_postgres.Chain.open: NotCached: a monkeypatch other than the UUID counter is active: setattr:assetops_backend.analytics.adapters.postgres_ass
- 1 x w202_cold_replay_postgres.Chain.start_release_upload: NotCached: a monkeypatch other than the UUID counter is active: setattr:assetops_backend.analytics.adapters.postgres_ass
- 1 x w205b_ev_replay_postgres.Chain.open: NotCached: a monkeypatch other than the UUID counter is active: setattr:Chain.attest
- 1 x w205b_ev_replay_postgres.Chain.start_release_upload: NotCached: a monkeypatch other than the UUID counter is active: setattr:Chain.attest
- 1 x w202_cold_replay_postgres.Chain.release_and_upload: NotCached: the test wrote to the database since its previous op
- 1 x w402_reads_postgres._reconcile: NotCached: a monkeypatch other than the UUID counter is active: setenv:DATABASE_URL, setitem:_Environ.DATABASE_URL, seta
- 1 x w205b_ev_replay_postgres.Chain.advance_late: NotCached: a monkeypatch other than the UUID counter is active: setattr:PostgresEvidenceLedger.decide_chunk
- 1 x w205b_ev_replay_postgres.Chain.open: NotCached: a monkeypatch other than the UUID counter is active: setattr:_Tx.finding_pairs_in_scope
