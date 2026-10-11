# S3-01 phase 3a + dispatch-3.1 review (fresh Claude reviewer)

Reviewer: a fresh Claude reviewer (independent; did not author phase 3a or dispatch-3.1).

**Verdict: accept with findings fixed on the branch.** One BLOCK (R1) must be fixed before phase 3b builds on the read; R2-R5 are carries.

Diff reviewed: `6fd70ee..5a5d39e` on `task/S3-01-dispatch-assessment`.

## Findings

### R1 (BLOCK) A FAILED recompute job makes the window read FAILED forever, even after a later successful reassessment

- Where: `backend/assetops_backend/analytics/adapters/postgres_assessment_store.py` `window_snapshot` job query (status IN ('PENDING','LEASED','FAILED') overlapping the read range, no age/selection filter) and `selected_intervals` (same query); `backend/assetops_backend/analytics/dispatch_read.py` `derive_status` (`if failed: return FAILED`). Nothing ever moves a FAILED job out of FAILED (`enqueue` coalesces only into PENDING).
- Reproduced (isolated DB `assetops_s3rev3a_test`, scratch test outside the tree): deliver -> CURRENT; late SoC reading -> broken model fails 3x -> FAILED (correct); then a new reading arrives, the real worker pass is `DONE` and selects a new run whose input and configuration hashes equal the current basis. The read still returns `FAILED` with only `RECOMPUTE_FAILED: job ...: RuntimeError: model crashed`. Jobs: `DONE, FAILED, DONE`.
- Why it matters: violates "Read states" (FAILED = the latest recompute failed with the prior selection kept) and Q12/Q4 (`FAILED` with inspectable prior revision on retry exhaustion, not a permanent mark). Every window within the 6 h bracket of the failed job is affected too. In the comparison (`selected_intervals`, Q16) every such interval is `STALE_PROJECTION` -> `UNPROVEN` permanently, so a nonempty comparison gate can never reopen after any transient exhausted failure. Phase 3b would display a false FAILED. The existing test stops at the failure and never covers recovery.
- Fix direction: a FAILED job only counts while no later DEFAULT selection of the window covers it (e.g. ignore FAILED jobs whose window is covered by a selection whose job/lease began after the job failed, or mark the failed job superseded when a later job for an overlapping range completes); same rule in `selected_intervals`. Add the recovery test (and its comparison counterpart).

### R2 (CARRY, before a nonempty comparison is relied on) The gate does not revalidate a PASSED report against the current selection

- Where: `backend/assetops_backend/analytics/performance_comparison.py` `permits_performance_cutover`; `backend/assetops_backend/main.py` `performance_gate`.
- What: the gate rechecks schema, Site, tenant, environment, model version, outcome, legacy digest and live lineage, but not whether the intervals the report classified are still the selected ones. After a PASSED report, new evidence can reassess a MATCH/INTENTIONAL_DELTA interval to another claim (same model, no lineage break) and the gate stays open on a stale classification.
- Why it matters: no live effect for KOBO-001 (empty legacy set, zero-inventory statement), but on the nonempty path the gate would stay open on a report that no longer describes the read. Fix: record the selection heads (run IDs or a digest) in the report and refuse when they changed, or reclassify at gate time.

### R3 (CARRY, low) Report/legacy file-store failures are 500, not 503

- Where: `main.py` `performance_gate` calls `performance_reports.latest(...)`, which raises `EvidenceStoreUnavailable` on an unreadable report (`evidence/adapters/legacy_comparison_file.py:49-50`), and `legacy_dispatch_claims(...)`; `performance_api.py` `cutover` and `open_scope` catch only `AssessmentStoreUnavailable`.
- Fix: map the file-store unavailable errors to the 503 typed state (and a closed cutover body), with a route test.

### R4 (CARRY, low, theoretical) Migration 0008 does not backfill selections for runs written under 0007

- `run_heads`, `assessed_sites`, `lineage_breaks` and the read take heads only from `analytic_run_selection`. A database holding 0007-era DEFAULT runs would read UNASSESSED, never reconcile those windows, and not count them in `selected_heads_other_model`, so the gate could open. Checked read-only: `assetops` and `assetops_s2demo` are at 0006, `assetops_s3cases` at 0008, `main` has no 0007; no live database is affected. Fix only if 0007 could reach a persistent database alone: backfill, or refuse the upgrade over existing runs (as 0003 does).

### R5 (CARRY, harness) Producer first-run failure: harness fragility under load, not shown to be a product defect

- `tools/s2_demo_walkthrough.py` `deliver_all` returns as soon as a pass reports `stopped` (an upload `TIMEOUT` with a batch retrying), so the remaining batches are not delivered; `VERIFY` then fails, which is the fail-safe outcome. Gateway retry on timeout is intended S2 behaviour. The packet's explanation (overlapping heavy runs) is plausible and the clean rerun passed, but the failed run's log was not retained, so the cause is not independently verifiable. Optional fix: have `deliver_all` wait (bounded) for retrying batches, and keep failed-run logs.

### Notes (no finding)

- R1 makes the Q16 default (bracket-widened job overlap in the comparison) unsafe in combination: every interval near a once-failed job is UNPROVEN forever. Once R1 is fixed, Q16's default is fine. Q14 (one documented delta, no catch-all) and Q15 (stricter MATCH) are safe fail-closed defaults.
- The fixture annotation reaches a window only through run evidence IDs; an AMBIGUOUS window whose alternatives include a fixture epoch carries none. It is never positive, so the rule holds; phase 3b may still want such an alternative named as manifest-labelled.

## Focus areas checked

- F3: `_multi_epoch` over window-present members only; default AMBIGUOUS; explicit selection still possible. Closed.
- F4: `run_pending` reconciles every assessed Site first, and the read independently compares configuration/input/model hashes. Closed.
- F5: 10-09 interval NECESSARY, window LIMITED naming `INTERVAL_LIMITED ... OPEN_BOUND`. Closed. F6: lease expired on last attempt -> FAILED with reason. Closed. Fixture template by minimum (source_time, sequence). Closed.
- Selection log: append-only trigger; written for created and reused DEFAULT runs inside the job commit; explicit runs never become heads. Correct.
- Status derivation: correct for UNASSESSED/PENDING/CURRENT/STALE_PROJECTION (incl. Q12 RECOMPUTE_OUTSTANDING and MODEL_VERSION_CHANGED), except FAILED persistence (R1).
- Drill-down pinned to stored run/revision evidence IDs, tenant- and Site-scoped; as-accepted vs selected configuration and backdated `selection_note` present.
- Fixture label: manifest annotation by exact evidence IDs, attributed to the manifest with its digest, never central provenance.
- Routes: 404 foreign/unknown Site, run, revision; 409 closed; 503 for the assessment store (file stores: R3).
- Version bump: old runs/revisions untouched and addressable with `OLDER_RULE_RESULT`; dispatch-3 heads read STALE_PROJECTION; explicit selections not remapped; migration evidence shows 9 heads moved and 12 runs / 18 revisions of dispatch-3 kept.
- Comparison/gate: MISSING_SOURCE -> EXCEPTIONS (closed); INTENTIONAL_DELTA only via the registry entry with the interval's own limitation and comparable basis; empty set stated as zero-inventory, not parity; other-model report and other-model heads refused.

## Checks run by this reviewer

- `tools/check-architecture.ps1`: passed. `tools/check-agent-workflow.ps1`: passed.
- Targeted backend with Postgres (isolated `assetops_s3rev3a_test`, created and dropped by me): `test_s3_dispatch_read_postgres.py`, `test_s3_dispatch_assessment_postgres.py`, `test_s3_performance_cutover.py`, `test_s3_dispatch_v3_analytic.py`, `test_scenario_fingerprints.py`: 61 passed (70 s).
- R1 reproduction: one scratch test kept outside the tree; failed as described.
- Not re-run (Implementer-reported, not independently verified): full backend suite (1826), host, gateway, simulator, check-all, non-vacuity mutations, producer, and the migration/gate run on `assetops_s3cases`.
- Frontend: no frontend file in the diff; `npm.cmd test`/`build` and `tsc` not run. Layout evidence: not applicable (no UI this phase).
- Owner servers, `var/`, ports 8610/8643 and `assetops_s3cases` data untouched (one read-only `alembic_version` query on `assetops`, `assetops_s2demo`, `assetops_s3cases` for R4). Working tree clean.
