# TEL-05b review packet: Finding proof, profile `-2`

PowerShell:
```
$env:PYTHONPATH = "C:\Users\assef\Bineyame\AssetOpsV1-tel5b\backend;C:\Users\assef\Bineyame\AssetOpsV1-tel5b\contracts;C:\Users\assef\Bineyame\AssetOpsV1-tel5b\simulator;C:\Users\assef\Bineyame\AssetOpsV1-tel5b\gateway;C:\Users\assef\Bineyame\AssetOpsV1-tel5b\host;C:\Users\assef\Bineyame\AssetOpsV1-tel5b\field;C:\Users\assef\Bineyame\AssetOpsV1-tel5b"
$env:ASSETOPS_GUARD_PYTHON = "C:\Users\assef\Bineyame\AssetOpsV1-plan2\.venv\Scripts\python.exe"
```

- Task: TEL-05b, `.agent/build-spec-telemetry-2026-10-27.md` § TEL-05b, sections J (TEL-T1-Q5, Q7) and K (Dev2); rulings amendment 2 (N1 replaced) and amendment 3 items 8-9.
- Branch `task/TEL-05b-finding-money-withheld`, from TEL-05 head `5c2f134f`. Build commit `a8aaaf5d`.
- Status: built and accepted locally. The Postgres gate is green twice, each run on a freshly created `assetops_tel5b_test` (revision `e02462a2`, which includes main `048b5828` merged in as `3e37dca3`).
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
| Unit-101 values exact, `NOT_A_MULTIPLE` a stop (J Q7) | Met: emulator tests, plus an end-to-end exact comparison of all 802 GOOD reports in both runs |
| Dispatch Finding cites only this test's accepted IDs | Met: one Finding per run, anchored 2026-10-13T05:05Z, window status CURRENT, citations a subset of the 802 accepted IDs |
| Provenance UNKNOWN / `NO_POSITIVE_BINDING` | Met (Finding revision, and each consequence revision UNKNOWN) |
| Every consequence read `current_amount_shown false` + `MIXED_OR_UNKNOWN_SOURCE`; no current amount in Finding read or index | Met: head and pinned reads both false; withheld `["AUDIT_ONLY","SOURCE_CLOSED","MIXED_OR_UNKNOWN_SOURCE"]`; index 409 `PERFORMANCE_CUTOVER_CLOSED` with rows null (L-Q1 (b)); the scan of the Finding read is empty |
| L-Q2: a PRICED revision with amounts exists, is withheld, provenance UNKNOWN | Met: one revision PRICED, USD 0 to 40.05760 (v4 price), `presented_as_current false` |
| Green twice, each on a fresh database | Met (below) |

## Checks run (revision `a8aaaf5d`)

- `field/tests` full: 150 passed. `test_field_gx_emulator.py`: 26 passed. `host/tests/test_field_observation_fixtures.py`: 2 passed. `gateway/tests/test_wire_contracts.py`: 32 passed.
- `host/tests/test_field_modbus_tcp_acceptance_postgres.py` without the database URL: 2 skipped (collection clean). The `-2` oracle was dry-run offline: 802 expected reports, all GOOD; counters VALUE 3170, all others 0.
- `tools/check-architecture.ps1`: passed. `tools/check-agent-workflow.ps1`: passed.
- Non-vacuity, each reverted with `git checkout --`:
  - `presented_value` made to quantize every row: the Q5 test and the `NOT_A_MULTIPLE` test both fail.
  - Enum label `RUNNING` changed to `RUN` in the profile: the freshness test and the table test fail.
  - One JSONL value byte changed: the freshness test fails.
- Postgres gate, alone on an idle laptop, with `tools/keep-awake-during-tests.ps1` running and a 1200 s cap per run (expected about 9 min). Command, from the worktree: `python -m pytest host/tests/test_field_modbus_tcp_acceptance_postgres.py -k profile_2 -q -s -p no:cacheprovider --basetemp %TEMP%ssetops-tel5b\<run> --junitxml <run>.xml`, with `ASSETOPS_TEST_DATABASE_URL=.../assetops_tel5b_test` on 127.0.0.1:55432. The database was dropped and recreated before each run and dropped at the end; no other database was touched.
  - Attempt 0 (`3e37dca3`), failed on a test defect, wall 543 s. Every gate passed up to step 5; the test then read `body["consequence"]` from the Finding read, which has no money section (only `/financials` does). Fix `e02462a2`: the Finding read is gated by the current-amount scan.
  - Gate run A (`e02462a2`): `1 passed in 542.57s`, wall 544 s; JUnit tests=1 failures=0 errors=0 skipped=0. Finding `c5e8c777-6870-4708-ae57-6c291a17fd34`, revision `163570fa-001e-4110-bcc7-6f561e0504cc`, consequence `047d301e-199c-41a0-bc87-62fc7e610a93`.
  - Gate run B (`e02462a2`): `1 passed in 542.07s`, wall 543 s; JUnit tests=1 failures=0 errors=0 skipped=0. Finding `6d1209f7-9a6d-4574-9a26-489a94ea408b`, revision `1d14f590-fc3e-4fdb-86cc-192d4d72891b`, consequence `d82666f0-4f4c-416e-9144-9913409fb92c`.
  - Each run: 802 accepted readings (battery_soc 97, feeder_demand 288, generator_power 96, generator_state 97, pcs_discharge_capability 96, pv_available_power 96, pv_power 32) in 578 batches, all receipts COMPLETED with no refusals. `process-jobs`: one job, DONE. Profile `-2` sha256 `638a6edfedfa4918503f5aeebf353f7e3f8ccfc3bd1dd22e4159023d0bdcc136`.
- Not run: the TEL-04 end-to-end file (heavy; unchanged).

## Known deviations

- The `-2` oracle and arrival helpers (`_expected_run_2`, `_arrived_2`) are local to the TEL-05 file. They reuse `tel4.oracle_outcome` and `expected_polls`. `tel4.expected_run`/`arrived` are bound to `-1` and parse values as `Fraction`, which fails on ENUM text. They were not changed, so the TEL-05/TEL-04 code under review stays as reviewed.
- Finding-index parameters added (Q1, confirmed in section L).
- L-Q2 (1) is applied to every gated Finding (Q3), not only one; a second Finding with no consequence would stop the test for the Architect.

## Residual risk

- **For the Architect:** the money is withheld by more than one gate. `withheld_reasons` also carries `AUDIT_ONLY` and `SOURCE_CLOSED`, because the S3 performance cutover is closed for the test Site ("No Performance comparison report exists"). `MIXED_OR_UNKNOWN_SOURCE` is present, `source_gate.permits_current_money` is false and the gate's state is UNKNOWN, so the source gate does withhold. But this proof does not show it as the only gate. The test was not tuned.

- Wall time is about 9 min per run.

## User-review focus

`USER_REVIEW_REQUIRED` is not stated for TEL-05b; the review is by the Lane T reviewer. Owner-facing claim wording is TEL-07.

## Step 6 (TEL-05b-Q3 addendum, section L)

Added a read-only step 6 after step 5: `build_consequence_read_service(URL).read(T, S, fid, frid, finding_revision_is_latest=True, source_open=True)` on the same head. It asserts ruling items 1-6 exactly and prints `currentness` past capsys. Assertions 1-3 carry a `STOP n` label, which means the TEL-07 fallback wording applies; 4-6 carry `SOURCE-GATE DEFECT n`. Focused tests: 28 passed, 2 skipped (no database URL). Both guards pass. **Pending:** one fresh-database Postgres run of the amended test, waiting on the coordinator's go.
