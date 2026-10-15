# LR-01 phase 1 — independent review

Reviewer: fresh Claude reviewer (did not author the work). Worktree `AssetOpsV1-review`, branch `review/LR-01-phase-1` at `445f3d18`; diff `ad2a96d0..445f3d18`.
Authority: packet `tasks/LR-01-late-reading-series-and-money-limit.md` (phase 1 row, S3 column), `.agent/architect-LR-01-answers.md` (Q1-Q4, packet changes 1-3, Follow-up M1), `D-2026-10-15-lr01-source-time-cohort`, plan review/re-review, brief, handoff.

## Verdict

**Accept with findings fixed on the branch.** One Medium (F1) blocks; the rest are Low/Info carries. The M1 placement/overlap rule, the fail-closed cases, the append-only history, the replay at run 1's cutoff, the SYSTEM-only write refusal and the old+new validity requeue are implemented as ruled and the tests have teeth. F1 is a requeue-scope hole: an attestation change can make windows outside both validity intervals read stale, and no work is ever queued for them.

## Findings

### F1 — Medium (blocking): an attestation change makes windows outside the requeue scope STALE with no work queued

- **Where:** `backend/assetops_backend/analytics/cohort.py` `_clock` (returns `NO_ATTESTATION` when the stream has no attestation, else `OUTSIDE_VALIDITY` when none touches the reading) and `_pair` (the joined reason string goes into `CohortLimit.clock`). `CohortLimit.payload()` → `CohortSelection.payload()` → `AnalyticInputSet.canonical()["cohort"]` → `input_sha256`. Requeue: `postgres_assessment_store.py` `record_clock_attestation` queues only readings that touch the old or new validity.
- **What is wrong:** whether any attestation exists for the stream, anywhere in time, changes the clock reason of every limited reading in that stream, so it changes the input digest of every window that has a series limit on that stream. The requeue reaches only readings that touch the validity, and `reconcile` checks only the model and configuration. A window far from the validity therefore reads `STALE_PROJECTION / INPUT_BASIS_CHANGED` permanently, with no job and no `RECOMPUTE_OUTSTANDING`. Recording a stream's first attestation flips `NO_ATTESTATION` to `OUTSIDE_VALIDITY`, and revoking its last one flips it back.
- **Reproduced** (temporary probe test, since removed): after run 1 (`SEQUENCE_ORDER_INVERTED ... clock NO_ATTESTATION`), record an attestation for the same source and epoch valid on DAY+2 only. Result: `requeued == []`; the DAY read is `STALE_PROJECTION ['INPUT_BASIS_CHANGED: ...']`; `reconcile()` returns `[]`; after `run_pending()` the head is unchanged and the read is still `STALE_PROJECTION`.
- **Why it matters:** this contradicts Q3 / packet change 1, which says to requeue the readings whose clock basis could change, because the implementation's basis changes more widely than its requeue. Phase 2 derives `PENDING_REASSESSMENT` from a stale selection (packet precedence; N3), so these windows would hold money withheld as "pending" with nothing pending, and the walkthrough's "settled" state would never arrive for them. It fails closed, but it never converges.
- **Fix (either):**
  - (a) Preferred, because it keeps the Architect's requeue scope. Make an uncovered reading's clock reason independent of attestations that do not touch it. For example, collapse `NO_ATTESTATION` and `OUTSIDE_VALIDITY` into one reason for readings no attestation touches. Refs are already empty for these readings.
  - (b) Widen the requeue to every accepted reading of the source and epoch.
- **Test to add:** a PG test showing that an attestation whose validity does not touch a limited window leaves that window `CURRENT` (or queues it), for both the first record and the last revoke on a stream.

### L1 — Low: placement and measurement overlap is checked only among readings under the same attestation

`cohort.py` `series_limits` groups attested readings by attestation (`groups[...key]`) before the placement (`|Δ| <= 2e`) and measurement-overlap checks. Two readings in one channel under different adjacent attestations can have overlapping placement-uncertainty intervals. If they arrive in sequence order, no limit is raised. M1 says overlapping placement-uncertainty intervals within one channel stay `REPORTS_OVERLAP` "even if gateway sequence agrees". This only bites within 2e of a validity boundary and never for 5-minute means, so it is narrow. **Fix:** run both overlap checks over all attested readings in the channel, using each reading's own error, rather than per attestation key.

### L2 — Low (carry to phase 2): interval-mean requeue and coverage are not proven end to end in Postgres

Decision #5 is accepted. The Postgres run-1 proof, requeue spans and CLI proof all use instant status rows, so the `COALESCE(interval_start/interval_end, ...)` path in `_STREAM_READINGS` and whole-interval coverage over persisted means are proven only in the pure tests. Phase 2's authored-fixture proof should assert the requeued span for the 07:00-07:05 power mean and the attested reassessment of it.

### I1 — Info: attestation write vs run cutoff race

`recorded_at` is the caller's clock, not the commit time. The attestation write takes advisory lock `:clock-attestation`, which is not the assessment's `:dispatch-assessment` lock. A run whose `knowledge_at >= recorded_at` but whose snapshot predates the commit pins no attestation and will not replay to its own digest later. This is the same class as the ledger's `decided_at` cutoff, and the same-transaction requeue makes it converge. Recorded as residual risk, not a defect of this slice.

### I2 — Info: migration 0014 details

- `source_id REFERENCES source(id)` alone; tenant and Site membership is enforced by the store (`SOURCE_NOT_IN_SITE`, tested), not by a composite foreign key.
- Downgrade drops the append-only history unconditionally. Migration 0012 refuses to downgrade while work rows exist; 0014 has no such guard. This is acceptable for a demo-only table, but it is a choice.
- The constraints otherwise match the contract: SIMULATED only, 0-60000 ms, `v1 <=> RECORDED`, revoke reason, unique `(attestation_id, version)` and `(tenant, site, idempotency_key)`, and a trigger that refuses UPDATE and DELETE (tested).

### I3 — Info: guard placement (deviation #1)

Extending the assessment store's INSERT-only set fits the configuration-persistence guard's intent: one confined writer per table, no other module may write it, and no UPDATE pattern was added for the table. Keeping the event and its requeue in one transaction is the deciding reason. The block comment above (`S3-01 phase 2 adds a fourth ...`) still lists only the old tables; the inline comment covers the change.

## Self-declared decisions

1. Writer in the assessment store: accepted (I3).
2. `EXPIRED` as an explicit event, and a passive `valid_to` needing no requeue: accepted. Validity is over reading times, not knowledge time. Readings after `valid_to` were never covered, and readings before it stay covered as time passes, so passive expiry changes no basis. Q3's "expiry" is the explicit early end, which is requeued over the old and new validity (tested: `spans == [span_3]`).
3. Whole measurement interval inside one validity, half-open: accepted as conservative. Coverage is not widened by the error, so a reading within e of `valid_to` counts as covered. That is consistent with M1 replacing the widened-interval wording; Info only.
4. `clock_basis` pins only attestations that touch a selected reading: accepted. Note that F1 leaks through the limit's clock reason, not through `clock_basis`.
5. Postgres run 1 with instant rows: accepted with carry L2.

## Fidelity checks (M1 and fail-closed)

- Placement at `placed_at` (interval end, otherwise source time) ± e; overlap when `|Δ| <= 2e`; touching measurement intervals excluded (`start < widest end`); a disjoint late arrival under one attestation is not an inversion (`rivals` excludes the same key). Matches M1, apart from L1.
- No attestation, outside validity, conflicting, straddling, cross-attestation step (`CLOCK_STEP_UNPROVED`), simulated proof on a live reading, error above 60 s (defensive in the cohort, refused at write and in the DB CHECK), other epoch or other source, and revoked (dropped by `effective_as_of`): all keep the sequence rule. Each has a pure test.
- Epochs: per-(source, epoch) attestation; the default cohort stays AMBIGUOUS across epochs; explicit selection orders each epoch under its own proof.
- SYSTEM-only: the principal must equal `SYSTEM_ATTESTER`, and the channel must be SYSTEM_CLI or SYSTEM_FIXTURE. The gateway principal and a lookalike are refused with nothing written and no job queued (Postgres). There is no HTTP route; the CLI is the only caller (grep) and has no actor or credential flag. The Site must be SIMULATED.
- Append-only and replay: earlier revisions and selections are byte-identical after reassessment, and replay at run B's cutoff reproduces `sha_b` and reuses run B. **Mutation (reviewer):** reading attestations with no knowledge cutoff makes the run-1 test fail at the `sha_b` assertion. Reverted, tree clean.
- Requeue: the old and new validity are both queried; the job carries the readings' intervals (instant +1 µs), and the worker expands to the previous UTC day and the day itself. Merging intervals closer than 2×BRACKET adds no day window (checked: a 36 h bracketed day cannot fit in a gap of 12 h or less). Creation, replacement, expiry and revocation are each asserted.

## Checks run (worktree, `assetops_backend.__file__` confirmed in `AssetOpsV1-review`)

- Focused: `pytest test_s3_dispatch_assessment_postgres.py test_s3_dispatch_read_postgres.py test_s3_demo_configuration.py test_lr01_cohort_v4.py test_s3_dispatch_v3_analytic.py -n 2 --dist loadfile` → **78 passed**, 30 s. This matches the handoff.
- Head/downgrade subset (`test_s1_bindings_postgres.py test_s2_evidence_ledger_postgres.py test_s4_evidence_consequence_work_postgres.py -k "head or downgrade or migrat"`) → **6 passed**.
- F1 probe: reproduced as above. The probe file was removed and was not committed.
- `tools/check-architecture.ps1` → passed. `tools/check-agent-workflow.ps1` → passed.
- `tools/check-all.ps1` in the worktree → 6/9. Missing-claim orphan scan and its fixtures failed (`Cannot find module 'typescript'`; the worktree has no `node_modules`), and Screen ledger failed (no `.venv` in the worktree). These are environmental and unrelated to the diff, which touches no frontend. **Not independently verified**; the handoff reports 9/9 at `07173066`.
- Full suite not run, per the phase 1 rules (phase 2 runs it). Frontend `tsc` and `npm` not run: no frontend changes in this diff.
- Private database `assetops_lr01p1rev_test` was created and dropped; no clones remain.

## Residual risk not named in the packet

- F1, until fixed.
- I1 (cutoff race, same class as the ledger).
- The `dispatch-3.2` churn listed in the handoff (S4 tests, conversions, walkthrough, frontend) is unverified until phase 2's full suite runs.
