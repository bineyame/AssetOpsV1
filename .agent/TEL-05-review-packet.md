# TEL-05 review packet: Postgres acceptance, profile `-1`

PowerShell environment (0.1, with the `-tel5` worktree):
```
$env:PYTHONPATH = "C:\Users\assef\Bineyame\AssetOpsV1-tel5\backend;C:\Users\assef\Bineyame\AssetOpsV1-tel5\contracts;C:\Users\assef\Bineyame\AssetOpsV1-tel5\simulator;C:\Users\assef\Bineyame\AssetOpsV1-tel5\gateway;C:\Users\assef\Bineyame\AssetOpsV1-tel5\host;C:\Users\assef\Bineyame\AssetOpsV1-tel5\field;C:\Users\assef\Bineyame\AssetOpsV1-tel5"
$env:ASSETOPS_GUARD_PYTHON = "C:\Users\assef\Bineyame\AssetOpsV1-plan2\.venv\Scripts\python.exe"
$env:ASSETOPS_TEST_DATABASE_URL = "postgresql+psycopg://assetops:assetops-local-dev@127.0.0.1:55432/assetops_tel5_test"
```
`assetops_gateway` and `assetops_field` resolved to the `-tel5` worktree (checked).

## Task
TEL-05 of `.agent/build-spec-telemetry-2026-10-27.md`, with sections J and K and
`.agent/telemetry-rulings-2026-10-27.md` (D1(c), D2 / owner Q4, D5). Branch
`task/TEL-05-postgres-acceptance` from TEL-04 head 164be83c.

## Outcome
Readings travelled emulator -> Modbus TCP poller (subprocess) -> real gateway process
-> central `BatchIngestionService` over `PostgresEvidenceLedger` (real UTC clock, no
decision-clock override) and were accepted as evidence in a `*_test` database. Source:
not established (UNKNOWN / `NO_POSITIVE_BINDING`). No Finding is claimed and no money is
shown. No simulation publication is attached anywhere in the test.

## Files
- `host/tests/test_field_modbus_tcp_acceptance_postgres.py` (new): one test,
  `test_gx_profile_1_lands_as_accepted_evidence`, skipped without
  `ASSETOPS_TEST_DATABASE_URL`. Reuses the TEL-04 harness pieces (`run_poller`,
  `with_diagnostics`, `expected_run`, `arrived`, `assert_values_at_register_resolution`)
  by module import; delivery follows TEL-04-Dev2 (`_deliver_all`, 120 s cap).
- `host/tests/test_field_modbus_tcp_proof.py`: `expected_run` gains a keyword
  `replay_start: datetime = START` (default unchanged), so the TEL-04 oracle covers the
  03:00Z start. Three lines.

## Acceptance gates
| Gate | Status | Evidence (gate run 2) |
|---|---|---|
| Site in the `*_test` database only (D2) | met | KOBO-001 converted by `test_s1_bindings_postgres.converted` in `assetops_tel5_test`; gateway/sources enabled by the two `UPDATE ... disabled_at = NULL` statements; daytime registered draft gives the snapshot |
| Activation unchanged | met | `activate` returns the snapshot SHA-256 |
| Outcomes and values exact at register resolution (TEL-T1-Q7) | met | `arrived(envelopes) == expected_run(...)`; independent q/2 bound on every GOOD report; status counters equal the oracle; emulator writes 0; no holds |
| Receipts COMPLETED, no central refusal | met | 96 receipts, all `COMPLETED`; no disposition other than ACCEPTED/DUPLICATE (a timing refusal would fail and print its row); first/last batch IDs `00db00fa...d88f`, `ffbf7b18...3e6e` |
| Accepted evidence for both bound roles, IDs printed | met | 96 rows: `battery_soc` 48, `pv_power` 48; row IDs equal the receipts' ACCEPTED evidence IDs and the envelope count. E.g. `807566d3-12f2-4daf-b871-b0be31fc62c6` (SoC 03:00Z), `af259767-6944-4ddb-9f1c-6282e66c725a` (SoC 15:00Z), `3a0de645-6c3a-49cf-894f-3ad3eec26114` (PV 03:15Z), `9cd82e55-d5a4-4bd9-8e45-b52d746f65a3` (PV 15:00Z); all GOOD |
| Provenance UNKNOWN, reasons exactly `["NO_POSITIVE_BINDING"]` (D1(c), Q-T49) | met | `build_source_provenance(URL).resolve(T, S, ids)` -> `state: UNKNOWN`, one reason `NO_POSITIVE_BINDING` |
| Assess completes; cited evidence subset of this test's IDs; `NO_GENERATOR_STATE` present (Q-T50) | met | `assess_dispatch.main(["assess", ... "--cohort", *cohort_members(expect)])` -> run `03ad94a6-fb54-4a60-9148-4126cab6b06a`, created, one revision; `run(...).evidence` non-empty and within the IDs; `NO_GENERATOR_STATE` in the serialized detail |
| No consequence row for the Site (D5) | met | every public table named `%consequence%` with a `site_id` column (15 tables, cold/ev/financial) has 0 rows for the Site; the set is asserted non-empty |
| Green on two consecutive invocations, each on a fresh database (Q-T56) | met | see Checks |

SoC is published at 48 of the 49 boundaries 03:00Z-15:00Z; the oracle predicts the same
set from the timeline (equality holds), so the missing boundary is the fixture's, not a loss.

## Checks run
- Heavy-job rule: before each run, process list checked for pytest/vitest command lines;
  the TEL-04 reviewer's runs were waited out (90 s idle) and nothing was killed.
  `tools/keep-awake-during-tests.ps1` ran throughout. Expected ~13 min, cap 30 min each.
- Command (cwd the worktree): `python -m pytest host/tests/test_field_modbus_tcp_acceptance_postgres.py -q -s -p no:cacheprovider --basetemp $env:TEMP\assetops-tel5\<label> --junitxml $env:TEMP\assetops-tel5\<label>.xml`
- Revision 3a6a6e2f (final):
  - gate run 1: `1 passed in 747.05s`, wall 748 s; JUnit tests=1 failures=0 errors=0 skipped=0.
  - gate run 2: `1 passed in 746.69s`, wall 749 s; JUnit tests=1 failures=0 errors=0 skipped=0.
- Revision 34116c9c (one earlier run, same assertions): `1 passed in 745.00s`. Its
  printed records were swallowed by `capsys.readouterr()`; 3a6a6e2f prints them past
  capsys. Assertions unchanged between the two revisions.
- Skip path without the URL: `1 skipped`.
- `tools/check-architecture.ps1`: passed. `tools/check-agent-workflow.ps1`: passed.
- Database: `assetops_tel5_test` created in `assetopsv1-postgres-1` for this task and
  dropped afterwards. No other database touched.
- Not run: the TEL-04 E2E tests after the `expected_run` keyword (default-preserving;
  the TEL-04 reviewer is running them on 164be83c). No full backend suite (no backend,
  gateway or migration change).

## Known deviations
- Database name `assetops_tel5_test` instead of 0.1's `assetops_tel_test`, as the dispatch
  directed (keeps this worktree apart from the `-tel` worktree).
- "No `consequence` row": the schema has no single `consequence` table; the test checks
  all 15 `%consequence%` tables with `site_id`. Strictest reading, no design added.
- `.ai/**` and `tasks/**` not updated (0.2: the coordinator updates them at merge).

## Residual risk
- The real-clock ingestion passed here because `submit`/`decide` have no age rule
  (Q-T47); a future age rule would turn this into a timing refusal, which the test
  reports by row.
- The test imports the TEL-04 test module; a TEL-04 fix round that renames those helpers
  would need the same rename here.

## User-review focus
None required for TEL-05 (terminal-only, no UI). Claim record wording is TEL-07.
R-level: R2 (adapter lab-tested, emulator on one laptop). Profile
`gx-system-illustrative-1` v1, SHA-256 `96bb0dc6...1ad1c`; JSONL SHA-256
`3d62a831...5be6b`; source values are exact rationals from simulator-lab-publication v3.
