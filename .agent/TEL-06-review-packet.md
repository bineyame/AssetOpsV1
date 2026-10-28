# TEL-06 review packet (TEL-06a / TEL-06b)

Status: in_review. 06a green; 06b Postgres gate green twice on fresh databases.

PYTHONPATH (PowerShell):
```
$env:PYTHONPATH = "C:\Users\assef\Bineyame\AssetOpsV1-tel6\backend;C:\Users\assef\Bineyame\AssetOpsV1-tel6\contracts;C:\Users\assef\Bineyame\AssetOpsV1-tel6\simulator;C:\Users\assef\Bineyame\AssetOpsV1-tel6\gateway;C:\Users\assef\Bineyame\AssetOpsV1-tel6\host;C:\Users\assef\Bineyame\AssetOpsV1-tel6\field;C:\Users\assef\Bineyame\AssetOpsV1-tel6"
```
Interpreter: `C:\Users\assef\Bineyame\AssetOpsV1-plan2\.venv\Scripts\python.exe`. The import check names `AssetOpsV1-tel6\gateway` and `AssetOpsV1-tel6\field`.

Branch `task/TEL-06-csv-collector`, cut from main `caf22405`. Built over `b43283ca` (collector), `3a0a2c14` (rulings), `b7441d43` (profile, fixture, generator), `ded503fc` (06a) and `7c58841c` (06b).

## Task
TEL-06 in `.agent/build-spec-telemetry-2026-10-27.md`, as amended by section M (TEL-06 rulings Q1-Q9). The task is the illustrative generic interval CSV collector `assetops-generic-interval-csv/1`. Owner Q7 = (c): no vendor naming.

## Outcome delivered
- **Collector** (`field/assetops_field/export_csv.py`): `CSV_CODES` (8 codes), `CsvRefused(code, field, detail, profile_sha256)`, and `CsvCollector(profile, publisher)` with `.reports(path)` and `.collect(path)`.
  - `.reports(path)` validates the whole file first and makes no IPC call.
  - `.collect(path)` runs `admit`, then `seal_and_release`. It returns `{profile_sha256, file_sha256, session_ref, report_count, admissions, sealed}` (M Q7).
  - A row whose cell count differs from the header, or a blank line, gives `INVALID_VALUE` (M Q6).
  - The caller owns `release_previous` (M Q5).
  - The value is normalised through `exact_decimal_text` (M Q8).
  - The `report_key` is the spec's key (M Q9).
- **Profile** (`field/profiles/generic-interval-csv-illustrative-1.json`): four `ILLUSTRATIVE` kW rows at 0.001, laid out exactly as in the M Q1 table. The PV row is `pv_power`; the clinic, mill and residential meters are `feeder_demand`. Profile SHA-256 `1496bd9a18ef721a8d0cf35e2f5bbe4a057673dcbb4fdce595c1b385380bb036`.
- **Fixture** (`contract-fixtures/telemetry/generic-interval-csv-v1/kobo-window.csv` and `manifest.json`): 49 rows, 196 cells and 4 blank cells (03:00Z). CSV SHA-256 `8c886ba820d418e88fe1e41a10313e68b1f9c58275aa7b63c3a70745f579e9e9`. The source is the `-1` JSONL (`3d62a831…`, checked against its manifest). Each value is rounded half-even once at 0.001. The manifest keys are exactly those in M Q2 (e).
- **Generator**: `host/tests/field_observation_fixtures.py:generate_interval_csv_fixture`, also run as `python host/tests/field_observation_fixtures.py interval-csv`.
- **Freshness test**: `test_interval_csv_fixture_is_fresh_and_its_profile_matches_the_run` in `host/tests/test_field_observation_fixtures.py`. It checks:
  - byte equality of both files;
  - LF line ends and no BOM;
  - the counts;
  - the header;
  - that the collector accepts the fixture;
  - spans, cadences, classes and units against the publication profile;
  - roles against the snapshot bindings.
- **06a** (`host/tests/test_field_export_csv_proof.py`): uses `tel4.Bench` with its own expect file (M Q3, steps 1-4).
- **06b** (`test_generic_csv_lands_as_accepted_evidence`, a third test in `host/tests/test_field_modbus_tcp_acceptance_postgres.py`): uses a fresh `*_test` database with KOBO-001 (M Q4).

## Files materially changed
`field/assetops_field/export_csv.py`, `field/tests/test_field_export_csv.py`, `field/profiles/generic-interval-csv-illustrative-1.json`, `contract-fixtures/telemetry/generic-interval-csv-v1/{kobo-window.csv,manifest.json}`, `host/tests/field_observation_fixtures.py`, `host/tests/test_field_observation_fixtures.py`, `host/tests/test_field_export_csv_proof.py`, `host/tests/test_field_modbus_tcp_acceptance_postgres.py` (test appended, docstring paragraph), `.agent/TEL-06-questions.md` and the spec section M (Architect's rulings, committed as given).

## Acceptance criteria
| Gate | Status |
|---|---|
| Same file twice → identical message IDs, no new sequence | **Met (06a step 2).** All 196 are `ALREADY_ADMITTED`, with the same `(message_id, sequence)` per index, and `sealed.batch_ids == []`. The `sequence_state` rows and the `envelope_outbox` and `upload_batch` counts are unchanged. The second collect used a new `session_ref` after `release_previous`. |
| Renamed header refuses the whole file, 0 IPC admissions, names the profile SHA | **Met.** Focused: `link.calls == []` and the SHA is in both the attribute and the message. 06a step 3: `HEADER_MISMATCH`, with `envelope_outbox`, `report_admission` and `mapping_hold` unchanged. |
| A timestamp without `Z` → `INVALID_TIMING` | **Met** (focused, and 06a step 3). |
| A blank cell → `UNAVAILABLE` | **Met.** The 03:00Z cells arrive as `UNAVAILABLE`/`NO_MEASUREMENT` with `interval_start` 02:45Z (06a step 1). |
| A header unit `W` → `UNIT_INCOMPATIBLE` holds | **Met (06a step 4).** There are 49 PV holds, `HELD`/`UNIT_INCOMPATIBLE`/`unit`, and the other 147 are `ALREADY_ADMITTED`. The outbox and the sequences are unchanged. |
| 06b: accepted IDs listed, provenance `UNKNOWN`, no money row | **Met (green twice; see the 06b gate below).** It asserts 196 accepted rows equal to the receipts' IDs, `{"pv_power": 49, "feeder_demand": 147}`, the exact-value oracle, `UNKNOWN`/`["NO_POSITIVE_BINDING"]`, and zero consequence rows. It collects without a database (3 tests collected). |
| No vendor name in TEL-06 code, profile, fixture or UI text | **Met.** A case-insensitive grep of the TEL-06 files (collector, field test, profile, fixture, manifest, 06a) for victron, vrm, sma, huawei, solaredge, monta, monnit, cerbo, gx and aggsoft exits 1 (no match). No UI is touched. 06a and 06b import the TEL-04/05 modules, which name their `-1` source by design (Q-T66). |
| Every `CSV_CODES` entry has one focused test | **Met.** It is enforced by name in `test_every_csv_code_has_a_focused_test`. |

## Checks run (final code `7c58841c`)
- `pytest field/tests/test_field_export_csv.py`: 45 passed.
- `pytest field/tests`: 197 passed in 14.6 s.
- `pytest host/tests/test_field_observation_fixtures.py` (light, run as its own file): 3 passed in 8.4 s.
- `pytest host/tests/test_field_export_csv_proof.py` (06a, one file, medium weight; the coordinator allowed it): 1 passed in 6.7 s (8.7 s of wall time with `-s`).
- Non-vacuous proofs (each committed first, then reverted with `git checkout`, and `git status` was clean afterwards):
  - Disabling the BOM check and the duplicate check failed the 2 matching focused tests.
  - Forcing the report unit to `kW` failed 06a step 4: `('ALREADY_ADMITTED', None, None)` came back where `('HELD', 'UNIT_INCOMPATIBLE', 'unit')` was expected.
- Guards: `tools/check-architecture.ps1` → "Architecture check passed."; `tools/check-agent-workflow.ps1` → "Agent workflow check passed." Both were run directly with no policy override, and `ASSETOPS_GUARD_PYTHON` was set to the plan2 venv.

## Held heavy run (needs the coordinator's go)
Run 06b alone against `assetops_tel_test`, and only that test, twice in a row (M Q4):
`<python> -m pytest host/tests/test_field_modbus_tcp_acceptance_postgres.py -k test_generic_csv_lands_as_accepted_evidence -q -s -p no:cacheprovider --basetemp "$env:TEMP\assetops-tel\tel06b"`
The two existing tests in that file are not rerun.

## Known deviations
None from section M. The plan card's `SOURCE_TIME_IN_FUTURE` case is out of scope by M Q3.

## Residual risk
- `_oracle` in 06a takes the fixture semantics from the ruling (half-even at 0.001; blank for non-`REPORTED`), so it is independent of the CSV but not of the ruling.

## User-review focus
None is required beyond the normal review. Lane T items close with the coordinator's merge (Q-T3).
