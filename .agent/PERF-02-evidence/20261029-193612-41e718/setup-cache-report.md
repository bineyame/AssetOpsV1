# Set-up cache, run 20261029-193612-41e718

- ops: 131; hits 0, misses 67, live 23, verify 41
- measured copy cost (seconds per hit, restore of database + files + objects): no hits

| op family | hits | hit s | misses | miss s | live | live s | verify |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| w202_cold_replay_postgres.Chain.advance_late | 0 | 0 | 2 | 3 | 1 | 0 | 0 |
| w202_cold_replay_postgres.Chain.open | 0 | 0 | 6 | 27 | 1 | 3 | 19 |
| w202_cold_replay_postgres.Chain.release_and_upload | 0 | 0 | 1 | 1 | 0 | 0 | 0 |
| w202_cold_replay_postgres.Chain.start_release_upload | 0 | 0 | 10 | 111 | 14 | 179 | 0 |
| w205b_ev_replay_postgres.Chain.advance_late | 0 | 0 | 0 | 0 | 4 | 5 | 0 |
| w205b_ev_replay_postgres.Chain.open | 0 | 0 | 6 | 31 | 1 | 4 | 15 |
| w205b_ev_replay_postgres.Chain.start_release_upload | 0 | 0 | 21 | 505 | 1 | 21 | 0 |
| w402_reads_postgres._ingest | 0 | 0 | 8 | 376 | 0 | 0 | 0 |
| w402_reads_postgres._reconcile | 0 | 0 | 11 | 124 | 1 | 20 | 0 |
| w402_reads_postgres._setup | 0 | 0 | 2 | 4 | 0 | 0 | 7 |

Live (not cached) reasons:

- 13 x w202_cold_replay_postgres.Chain.start_release_upload: NotCached: the test wrote to the database since its previous op
- 3 x w205b_ev_replay_postgres.Chain.advance_late: NotCached: the test wrote to the database since its previous op
- 1 x w205b_ev_replay_postgres.Chain.open: NotCached: a monkeypatch other than the UUID counter is active: setattr:Chain.attest
- 1 x w205b_ev_replay_postgres.Chain.start_release_upload: NotCached: a monkeypatch other than the UUID counter is active: setattr:Chain.attest
- 1 x w202_cold_replay_postgres.Chain.advance_late: NotCached: the test wrote to the database since its previous op
- 1 x w202_cold_replay_postgres.Chain.open: NotCached: a monkeypatch other than the UUID counter is active: setattr:assetops_backend.analytics.adapters.postgres_ass
- 1 x w202_cold_replay_postgres.Chain.start_release_upload: NotCached: a monkeypatch other than the UUID counter is active: setattr:assetops_backend.analytics.adapters.postgres_ass
- 1 x w402_reads_postgres._reconcile: NotCached: the test wrote to the database since its previous op
- 1 x w205b_ev_replay_postgres.Chain.advance_late: NotCached: a monkeypatch other than the UUID counter is active: setattr:PostgresEvidenceLedger.decide_chunk

## Copy against fresh build (verify mode)

| op family | compared | rows equal | UUID counter equal | no saved fingerprint |
| --- | ---: | ---: | ---: | ---: |
| w202_cold_replay_postgres.Chain.open | 19 | 0 | 19 | 0 |
| w205b_ev_replay_postgres.Chain.open | 15 | 0 | 15 | 0 |
| w402_reads_postgres._setup | 7 | 0 | 7 | 0 |

Tables that differed (family: kind:table x times):

- w202_cold_replay_postgres.Chain.open: content:gateway x19, content:gateway_access_event x19, content:gateway_credential x19
- w205b_ev_replay_postgres.Chain.open: content:gateway x15, content:gateway_access_event x15, content:gateway_credential x15, content:recompute_job x15, content:source_clock_attestation x15
- w402_reads_postgres._setup: content:asset x7, content:foundation_revision x7, content:gateway x7, content:recompute_job x7, content:signal_binding_revision x7, content:signal_binding_set_revision x7, content:site x7, content:site_cutover_basis x7, content:site_import x7, content:source x7, content:tenant x7
