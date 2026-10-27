# TEL-05 review: Postgres acceptance, profile `-1`

Reviewer: fresh Claude reviewer (did not author the slice). Branch `task/TEL-05-postgres-acceptance` at 5c2f134f, diffed against TEL-04 head 164be83c.
Authority: `.agent/build-spec-telemetry-2026-10-27.md` (TEL-05, Q-T46..Q-T56, sections J and K), `.agent/telemetry-rulings-2026-10-27.md` (D1(c), D2, D5), and the owner answers (test-DB Sites only, provenance UNKNOWN, no consequence, no simulation publication).

## Verdict: ACCEPT

No High or Medium findings. Every gate was rerun independently and held.

## Checks I ran (machine idle, one heavy job at a time, keep-awake running)

| Check | Result |
|---|---|
| `host/tests/test_field_modbus_tcp_proof.py` (TEL-04 proof, after the `expected_run` change) | `11 passed in 228.00s`, wall 229 s |
| `host/tests/test_field_modbus_tcp_acceptance_postgres.py`, run alone on a fresh `assetops_tel5r_test` (created with `CREATE DATABASE`, reset by `fresh_database()`, dropped with `DROP DATABASE ... WITH (FORCE)` afterwards) | `1 passed in 743.74s`, wall 745 s; JUnit tests=1 failures=0 errors=0 skipped=0 |
| `tools/check-architecture.ps1`, run directly | passed |
| `tools/check-agent-workflow.ps1`, run directly | passed |

My first attempt at the proof file errored at setup in 2.6 s. The cause was the `--basetemp` parent directory, which did not exist yet. That was my harness, not the slice. The clean rerun is the one recorded above. No non-test database was touched, and no process was killed by name.

## Gates, as observed in my run

- **Receipts:** 96 batch receipts, all `COMPLETED`. Every disposition was ACCEPTED or DUPLICATE, with no refusal and no timing refusal under the real UTC clock (Q-T47 holds).
- **Evidence per role:** 96 `accepted_evidence` rows, 48 `battery_soc` and 48 `pv_power`, all GOOD. The row IDs equal the receipts' ACCEPTED evidence IDs, and the count equals the outbox envelope count.
  - PV covers 03:15Z-15:00Z.
  - SoC covers 03:00Z-15:00Z except 12:45Z. The oracle (`expected_run`) predicts that gap from the timeline, and `arrived == expected` holds, so the gap comes from the fixture, not a loss.
- **Provenance:** `state` is `UNKNOWN` and the reason codes are exactly `["NO_POSITIVE_BINDING"]`. Every evidence entry is `UNBOUND`. After the run, `evidence_publication` and `batch_publication_link` each held 0 rows, so no simulation publication was attached.
- **Assessment:**
  - Exit code 0, with `created: true` and one revision.
  - The run detail's cited evidence is non-empty and a subset of this test's accepted IDs.
  - `NO_GENERATOR_STATE` is present.
- **Consequence:** all 15 `%consequence%` tables that have a `site_id` column hold 0 rows for the Site. The test asserts that this set of tables is non-empty. I also checked by hand: `finding` and `finding_revision` held 0 rows.

## Non-vacuity

The test cannot pass with nothing in it:
- `receipts` must be non-empty and `BOUND_ROLES <= roles`.
- `good > 0` (the GOOD count from the oracle must equal the independent q/2 bound count).
- `arrived(envelopes) == expected` is checked against an oracle built independently from the timeline.
- `cited` must be non-empty.
- `consequences` must be a non-empty dict.
- The provenance reason list is compared exactly, so an empty list fails.
- The status counters must equal the oracle's.

## Real path, no injection

- The emulator is the in-process `GxEmulator`. It is reached over real Modbus TCP on 127.0.0.1 by the `assetops_field.modbus_poller` subprocess.
- The poller writes to the real `GatewayProcess` over IPC, using the real activation.
- The harness `deliver` sends TLS posts to `FakeCentral`, whose batch route calls the real `BatchIngestionService(PostgresEvidenceLedger(URL))` (spec step 2).
- The test writes no canonical or evidence record directly. Its only direct SQL is the two spec-mandated `UPDATE ... disabled_at = NULL` statements, which stand in for credential provisioning (spec step 1).
- All reads go through the named services: `build_source_provenance`, `assess_dispatch.main` and `build_dispatch_read_service`.

## The TEL-04 change (`expected_run(..., replay_start=START)`)

- It is correct and preserves the default.
- `replay_start` only moves the origin of the boundary grid: `replay_start + cadence` for intervals, `replay_start` for states. `session_start` still filters as before.
- All three TEL-04 call sites rely on the default, which is TEL-04's 06:00Z `START`. Their behaviour is unchanged, which the 11/11 pass above confirms.
- TEL-05 needs the parameter because its replay starts at 03:00Z. Without it, the grid would begin at 06:00Z and drop three hours of boundaries.

## Findings

### High
None.

### Medium
None.

### Low
- **L1. `host/tests/test_field_modbus_tcp_acceptance_postgres.py:237`.**
  - What: `NO_GENERATOR_STATE` is a substring match over the whole serialized run detail.
  - Why it is Low: this matches the spec gate's wording ("appears in the serialized run detail"), but it would also pass if the code appeared somewhere other than as the run's recorded limitation.
  - Fix, if wanted: look for it in the specific reason or limitation field.
  - Classification: preference, not an acceptance gap.
- **L2. `host/tests/test_field_modbus_tcp_acceptance_postgres.py:240`.**
  - What: the TEL-07 statement says "No Finding is claimed", but the test does not assert that the Site has no `finding` row. The ruling text in D5 also mentions "no ... money row", which the test reads as the consequence tables.
  - Why it is Low: in my run there were 0 findings, and an explicit `assess` does not run `match-findings`, so nothing could raise one here.
  - Fix, if wanted: assert that the Site has no `finding` row, to back the claim record.
  - Classification: preference, not an acceptance gap. The spec gate lists only "no consequence row".

## Residual risk (beyond the packet)

- The test reaches the TEL-04 helpers by importing the module `test_field_modbus_tcp_proof`. pytest also collects that module on its own, and the import works only because `ROOT/host/tests` is on `sys.path`. The PYTHONPATH (`...\host`) and the `host/tests` rootdir conftest make this work today, so it is fragile only if the test layout changes. The packet names the rename risk but not this one.
- The packet's run times (747 s and 747 s) match mine (744 s). Its numbers are confirmed, not just cited.
