# TEL-05b review packet: Finding proof, profile `-2` (phase 1 of 2)

PowerShell:
```
$env:PYTHONPATH = "C:\Users\assef\Bineyame\AssetOpsV1-tel5b\backend;C:\Users\assef\Bineyame\AssetOpsV1-tel5b\contracts;C:\Users\assef\Bineyame\AssetOpsV1-tel5b\simulator;C:\Users\assef\Bineyame\AssetOpsV1-tel5b\gateway;C:\Users\assef\Bineyame\AssetOpsV1-tel5b\host;C:\Users\assef\Bineyame\AssetOpsV1-tel5b\field;C:\Users\assef\Bineyame\AssetOpsV1-tel5b"
$env:ASSETOPS_GUARD_PYTHON = "C:\Users\assef\Bineyame\AssetOpsV1-plan2\.venv\Scripts\python.exe"
```

- Task: TEL-05b, `.agent/build-spec-telemetry-2026-10-27.md` § TEL-05b, sections J (TEL-T1-Q5, Q7) and K (Dev2); rulings amendment 2 (N1 replaced) and amendment 3 items 8-9.
- Branch `task/TEL-05b-finding-money-withheld`, from TEL-05 head `5c2f134f`. Build commit `a8aaaf5d`.
- Phase 1 status: everything built; focused non-DB tests and guards green. **The Postgres test has not been run** (heavy-job slot held by the TEL-05 reviewer). Phase 2 = two runs, each on a fresh database.
- Builder questions `.agent/TEL-05b-questions.md`, ruled in spec section L (2026-10-28) and applied in the second commit: Q1 index parameters confirmed (a CURRENT 200 must have rows; only 200/409-closed pass); Q2 zero consequence revisions is a STOP.

## Outcome delivered

- `field/profiles/gx-system-illustrative-2.json`: status `ILLUSTRATIVE`, version 1. Unit 100 `pv-ac-output` row as in `-1` (row status `UNPINNED`). Unit 101, addresses 1000-1014: the eight rows of the spec table, written from `field_fixtures.gx2_rows()` (the TEL-01 table), and a test asserts the file's rows equal it row for row. 843, 842 and 817-819 are absent.
- `contract-fixtures/telemetry/kobo-prolonged-public-observations-v1/{observations.jsonl,manifest.json}`: 1036 observations, `kobo-mini-grid-prolonged:2`, `registered-kobo-publication:4`, timestep 5, 2026-10-13T03:00Z-11:00Z, sha256 `c49aa7c846b264cec552fa9fa5837703980aec3edc97c5e397996d1bb25f85b1`. Outcomes: REPORTED 1026, NO_PRECEDING_INTERVAL 10. The generator status reads RUNNING 67 times and STOPPED 30 times.
- `host/tests/field_observation_fixtures.py`: `prolonged_draft()` (in-memory `registered.converted()`, then `test_s6_verification_publication.configure()` and `draft()` imported, so the build is exactly theirs); `prolonged_run()`; `generate_prolonged_fixture(out_dir)`; CLI `prolonged`. The execution is shared with the daytime fixture through `_execute(draft)`, with `gateway=None`.
- Freshness test `test_prolonged_fixture_is_fresh_and_profile_2_matches_the_run_and_its_snapshot`: byte equality, manifest SHA, LF only, public keys only. Every `-2` row's reading class, cadence, span and unit equal the V4 declaration. Every row's role equals the snapshot binding's role. The `enum_map` texts are a subset of the status binding's ENUM map labels (the labels the gateway checks, `service.py:864-869`).
- Emulator cases (`field/tests/test_field_gx_emulator.py`; `Bench` now takes `jsonl`/`profile`/`start`, defaults unchanged):
  - `test_profile_2_is_the_tel05b_table`;
  - `test_every_unit_101_observation_reads_back_exactly_through_profile_2`: 770 REPORTED and 6 SENTINEL reads, each `== Fraction(reported_value)` (ENUM: the same text);
  - `test_quantization_follows_row_status_not_profile_status` (TEL-T1-Q5);
  - `test_a_unit_101_value_finer_than_the_register_stops_with_not_a_multiple` (J Q7: the timeline refuses with `EncodeRefused`, never quantizes).
- Postgres test `test_gx_profile_2_raises_a_finding_with_no_money_shown`, in the TEL-05 file. The TEL-05 test body is unchanged.
  - Setup: Postgres KOBO-001 converted, the S3 then S6 configurations applied (`s6.configure`), gateway and sources enabled, `s6.draft(store)` as the snapshot.
  - Path: real gateway, in-process emulator over profile `-2` and the prolonged JSONL, poller subprocess at rate 60, `_deliver_all`.
  - Readings: an exact comparison against an oracle (the TEL-04 `oracle_outcome` and `expected_polls`, with a `-2` value rule). Unit-101 values compare to `Fraction(reported_value)` exactly, ENUM values as text, the PV row at register resolution. There is also an independent check against the source.
  - Central: receipts COMPLETED, no refusals, all six dispatch roles accepted.
  - Steps 1-5 in spec order, failing fast:
    1. `process-jobs` gives all `DONE`, then `match-findings`.
    2. Findings are non-empty; otherwise the test stops and prints `window_statuses`. Each Finding's latest revision is checked: its provenance `cited_accepted_evidence_ids` ⊆ this test's IDs, `UNKNOWN`, `["NO_POSITIVE_BINDING"]`.
    3. `publish_assumption fixture` with no `--step`.
    4. `recompute_consequences run --tenant demo --site KOBO-001`.
    5. `TestClient(main.create_app())` reads the index, each Finding (`revision_id`), the head consequence read and every `financial_consequence_revision` read pinned. Every consequence read must have `current_amount_shown false` with `MIXED_OR_UNKNOWN_SOURCE` in `withheld_reasons`. In every body, no `current_amount_shown`/`presented_as_current` may be true. In the Finding read, `consequence.amount` must be null and not PRICED.
  - Each ID, the provenance, the profile SHA and each read are printed past capsys for the claim record.

## Files materially changed

`field/profiles/gx-system-illustrative-2.json` (new), `contract-fixtures/telemetry/kobo-prolonged-public-observations-v1/*` (new), `host/tests/field_observation_fixtures.py`, `host/tests/test_field_observation_fixtures.py`, `field/tests/test_field_gx_emulator.py`, `host/tests/test_field_modbus_tcp_acceptance_postgres.py`, `.agent/TEL-05b-questions.md`. No file in lane 0.2's protected list; no `tools/checks` change; `.gitattributes` already covers `contract-fixtures/telemetry/**` (`text: unset` confirmed).

## Acceptance criteria

| Gate | Status |
|---|---|
| Profile `-2` per table, row statuses, sentinels, spans/cadences/period 60 | Met (table test, loader, freshness vs V4) |
| enum texts are labels of the snapshot status binding | Met (freshness test) |
| JSONL pinned with manifest, freshness test | Met |
| Unit-101 values exact, `NOT_A_MULTIPLE` a stop (J Q7) | Met offline (emulator tests). The end-to-end exact comparison is coded but **not yet run** |
| Quantization on row status (T1-Q5) | Met |
| Dispatch Finding cites only this test's accepted IDs | Coded, **not run** |
| Provenance UNKNOWN / `NO_POSITIVE_BINDING` | Coded, **not run** |
| Every consequence read `current_amount_shown false` + `MIXED_OR_UNKNOWN_SOURCE`; no current amount in Finding read or index | Coded per section L, **not run** |
| L-Q2: ≥1 consequence revision per gated (fid, frid), ≥1 PRICED with amounts (else STOP with recompute output and price rows); each read's selected revision `presented_as_current false`, own `source_provenance.state UNKNOWN` | Coded, **not run** |
| Green twice, each on a fresh database | **Not run** (phase 2) |

## Checks run (revision `a8aaaf5d`)

- `field/tests` full: 150 passed. `test_field_gx_emulator.py`: 26 passed. `host/tests/test_field_observation_fixtures.py`: 2 passed. `gateway/tests/test_wire_contracts.py`: 32 passed.
- `host/tests/test_field_modbus_tcp_acceptance_postgres.py` without the database URL: 2 skipped (collection clean). The `-2` oracle was dry-run offline: 802 expected reports, all GOOD; counters VALUE 3170, all others 0.
- `tools/check-architecture.ps1`: passed. `tools/check-agent-workflow.ps1`: passed.
- Non-vacuity, each reverted with `git checkout --`:
  - `presented_value` made to quantize every row: the Q5 test and the `NOT_A_MULTIPLE` test both fail.
  - Enum label `RUNNING` changed to `RUN` in the profile: the freshness test and the table test fail.
  - One JSONL value byte changed: the freshness test fails.
- Not run: the Postgres test (phase 2), and the TEL-04 end-to-end file (heavy; unchanged).

## Known deviations

- The `-2` oracle and arrival helpers (`_expected_run_2`, `_arrived_2`) are local to the TEL-05 file. They reuse `tel4.oracle_outcome` and `expected_polls`. `tel4.expected_run`/`arrived` are bound to `-1` and parse values as `Fraction`, which fails on ENUM text. They were not changed, so the TEL-05/TEL-04 code under review stays as reviewed.
- Finding-index parameters added (Q1, confirmed in section L).
- L-Q2 (1) is applied to every gated Finding (Q3), not only one; a second Finding with no consequence would stop the test for the Architect.

## Residual risk

- The S3 performance cutover gate, `process-jobs` job creation under the real UTC clock, and the matcher's window statuses are untested until phase 2. The spec's stop applies: no Finding means report, no tuning.
- Wall time per run is about 8 min of replay plus setup and delivery.

## User-review focus

`USER_REVIEW_REQUIRED` is not stated for TEL-05b; the review is by the Lane T reviewer. Owner-facing claim wording is TEL-07.
