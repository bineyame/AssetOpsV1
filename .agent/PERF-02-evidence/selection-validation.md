# Test-impact selection against merged slices

| merge | slice | files | mode | selected / total | changed tests missed | recorded failures | missed |
| --- | --- | ---: | --- | ---: | --- | --- | --- |
| 05f80711 | Merge task/PERF-01-baseline-quick-wins (memory/CPU samplers, phase attribution, test-only  | 44 | full | 250 / 250 | - | test_r373_request_access.py, test_w202_cold_replay_postgres.py, test_w203_cold_reads_postgres.py, test_w203_cold_replay_postgres.py | - |
| 2599d34b | Merge task/TEL-06-csv-collector (illustrative generic interval CSV collector; review ACCEP | 13 | full | 250 / 250 | - | - | - |
| 9cec4fcb | Merge task/CC-R2-placement (portfolio placement D5, estate case, MG-C stand-in, Portfolio  | 44 | selected | 168 / 250 | - | test_cc_placement_postgres.py | - |
| caf22405 | Merge task/TEL-05b-finding-money-withheld (money-affecting Finding from emulated generator | 15 | full | 248 / 248 | - | test_lr01_money_eligibility_postgres.py | - |
| 048b5828 | Merge task/TEL-05-postgres-acceptance (Modbus TCP proof Postgres acceptance, run alone twi | 4 | none | 0 / 248 | - | - | - |
| c41a20b1 | Merge task/TEL-04-poller (Modbus poller CLI, focused end-to-end proof through a real gatew | 7 | none | 0 / 248 | - | - | - |
| af7f1f90 | Merge task/CC-R1-claim-links-beneficiary (claim labels, beneficiary key, no-double-count i | 30 | selected | 159 / 248 | - | test_w301_w1_money_snapshot_helpers_postgres.py, test_w303_portfolio_comparison_postgres.py, test_w303_portfolio_fixture_postgres.py, test_w303_portfolio_scope_snapshot_postgres.py, test_w303_selectors_postgres.py | - |
| 267de09d | Merge task/TEL-01-field-core (TEL-00..03: field core, read-only Modbus TCP client, GX-shap | 33 | full | 247 / 247 | - | - | - |
| 0d688893 | Merge branch 'task/post-W6-final-fix' | 209 | selected | 165 / 247 | - | - | - |
| 77bd20c3 | Merge branch 'task/post-W6-W5-EV-work' | 761 | selected | 165 / 247 | - | - | - |

- 05f80711 full because: .gitattributes; backend/tests/conftest.py; backend/tests/phase_attribution.py

- 2599d34b full because: contract-fixtures/telemetry/generic-interval-csv-v1/kobo-window.csv; contract-fixtures/telemetry/generic-interval-csv-v1/manifest.json; field/profiles/generic-interval-csv-illustrative-1.json (run-time data the import graph cannot trace)

- caf22405 full because: contract-fixtures/telemetry/kobo-prolonged-public-observations-v1/manifest.json; contract-fixtures/telemetry/kobo-prolonged-public-observations-v1/observations.jsonl; field/profiles/gx-system-illustrative-2.json (run-time data the import graph cannot trace)

- 267de09d full because: .gitattributes; contract-fixtures/telemetry/kobo-public-observations-v1/manifest.json; contract-fixtures/telemetry/kobo-public-observations-v1/observations.jsonl
