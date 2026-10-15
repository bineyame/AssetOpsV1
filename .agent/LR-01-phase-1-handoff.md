# LR-01 phase 1 handoff — source-time contract and reassessment

Branch `task/LR-01-late-reading-series-and-money-limit`, commits `2539e5cf`, `d1cbfe8a`, `07173066` (base `d4c80e77`). Phase 1 only; nothing merged.

## What landed

- **Clock attestation domain** `backend/assetops_backend/analytics/clock_attestation.py`: `ClockAttestation` (event row = one version), `effective_as_of(events, k)` (latest version recorded <= k per attestation; `REVOKED` drops it), `AttestationChange`, `validate_change` (only `SYSTEM_ATTESTER` + `SYSTEM_CLI|SYSTEM_FIXTURE`; proof class `SIMULATED` only, real-source refused; authority, simulated label, error <= 60 s, zoned non-empty validity; revoke needs reason), `next_event` (RECORDED v1 → REPLACED / EXPIRED (valid_to strictly inside) / REVOKED; expected-version conflict 409).
- **Migration 0014** `backend/migrations/versions/0014_source_clock_attestation.py`: `source_clock_attestation`, FK site/source, CHECKs (SIMULATED only, error 0..60000 ms, v1 ⇔ RECORDED, revoke reason), unique `(attestation_id, version)` and `(tenant, site, idempotency_key)`, trigger refuses UPDATE/DELETE. Head assertions moved to 0014 in `test_s1_bindings_postgres.py:118`, `test_s2_evidence_ledger_postgres.py:445`, `test_s4_evidence_consequence_work_postgres.py:516,539`.
- **Store** `postgres_assessment_store.py`: `_attestations()` loaded as of `knowledge_at` into `EvidenceQueryResult.attestations` in both `query_evidence` and `window_snapshot` (so the read's current input basis sees new proof → `STALE`). `record_clock_attestation(tenant, site, change, principal, now)` — validates, idempotent replay / `IDEMPOTENCY_CONFLICT`, refuses non-`SIMULATED` Site (`SIMULATED_PROOF_FOR_LIVE_SITE`) and foreign source, inserts the event, then in the same transaction requeues accepted readings of that source/epoch touching the **old and new** validity via `requeue_spans` (reading intervals, instant = +1 µs like the ledger, merged only when gap <= 2×BRACKET; job expansion `day_windows` supplies the bracket/neighbour days, not widened twice; uses `BRACKET`). `enqueue` refactored to shared `_enqueue`. `site_scope`, `clock_attestation_events` reads. Guard `tools/checks/configuration-persistence.ps1:633-636` adds the table to the assessment writer's INSERT-only set.
- **CLI** `backend/assetops_backend/record_clock_attestation.py` (`record|replace|expire|revoke`, fixed SYSTEM principal, no actor/credential flag, no HTTP route; store via `composition.build_postgres_assessment_store`).
- **cohort-4** `backend/assetops_backend/analytics/cohort.py` (`RULES = "cohort-4"`): per-reading clock (`ATTESTED` or NO_ATTESTATION / OUTSIDE_VALIDITY / SPANS_ATTESTATIONS / CONFLICTING_ATTESTATIONS / SIMULATED_PROOF_FOR_LIVE_SOURCE / ERROR_ABOVE_CEILING); same-attestation pairs ordered by `placed_at`, sequence disagreement = late arrival; placement overlap `|Δ| <= 2e` and genuine measurement overlap (touching ends excluded) → `REPORTS_OVERLAP` clock `ATTESTED`; pairs under two attestations → `CLOCK_STEP_UNPROVED`; epoch rules unchanged. `CohortLimit.clock/attestation_refs`, `CohortSelection.rules/clock_basis` (pinned attestation id/version/event id in the payload → input digest; only attestations touching a selected reading, to avoid churn). Pre-LR-01 payload shape unchanged when `rules is None`.
- **Model** `dispatch_v3.MODEL_VERSION = "dispatch-3.2"`; window limitation strings append `; clock <reason> [<refs>]`. `GENERATOR_SERIES_AMBIGUOUS` still raised at window level for any generator-role cohort limit.

## Outcome-table rows proven in phase 1 (S3 column)

| Row | Proof |
| --- | --- |
| Run 1, no attestation, late acceptance | pure `TestRunOneAndOnTimeVariant::test_admission_sequenced_...` (5-min power-mean shape); PG `TestClockAttestation::test_run_one_...` (status-row analogue via real ingestion): `INDETERMINATE`, `SEQUENCE_ORDER_INVERTED` clock `NO_ATTESTATION`, `GENERATOR_SERIES_AMBIGUOUS` |
| Attestation recorded, before settle | same PG test: requeued span, PENDING job, read `STALE` with `INPUT_BASIS_CHANGED` + `RECOMPUTE_OUTSTANDING`, head still run B |
| Reassessment settled | same PG test: new run/selection, not INDETERMINATE, no series/inversion limit, `clock_basis` pins id/v1/event id; all earlier revisions and selections byte-identical; replay at run B cutoff reproduces `sha_b` and reuses run B; idempotent re-record + settled pass create nothing |
| On-time-sequenced late upload | PG `test_on_time_sequenced_...` and pure variant |
| No attestation / expired / conflicting / revoked / clock step / overlap / live source / >60 s / other epoch | pure `TestFailClosedClockProof`, `TestOverlapUnderProof`, `TestAttestationEvents::test_revoked_...`; PG `test_simulated_data_without_attestation_stays_limited` |
| Epochs | pure `TestEpochs` (default stays AMBIGUOUS under proof; explicit cross-epoch selection, each epoch under its own proof) |
| Requeue creation/replacement/expiry/revocation | PG `test_creation_replacement_expiry_and_revocation_requeue_old_and_new_validity` (old+new validity spans, job window = reading span, worker windows = previous UTC day + day) |
| SYSTEM-only, append-only | pure parametrized refusals; PG `test_only_the_system_attester_writes_and_events_are_append_only` (gateway principal, lookalike, foreign source, no row/job written; trigger refuses UPDATE/DELETE); PG CLI test |

Finding/consequence/money columns are phase 2.

## Checks (revision `07173066`)

- Focused: `pytest test_s3_dispatch_assessment_postgres.py test_s3_dispatch_read_postgres.py test_s3_demo_configuration.py test_lr01_cohort_v4.py test_s3_dispatch_v3_analytic.py -n 2 --dist loadfile` → **78 passed**, 34 s. Head/downgrade subset of S1/S2/S4-evidence-work files (`-k "head or downgrade or migrat"`) → 6 passed.
- `tools/check-all.ps1` → All 9 guards passed (rerun at handoff).
- Mutations (each reverted with `git checkout`, tree clean): M1 late arrival always inverted → 3 failed; M2 no placement overlap → 2 failed; M3 touching means overlap → 7 failed; M4 simulated proof orders LIVE → 1 failed; M5 any principal writes → 3 pure + 1 PG failed; M6 requeue new validity only → PG requeue test failed. (A first M2 attempt was invalid — NameError — and was redone.)
- No full suite (phase 2 runs it once).

## Deviations / decisions taken (for the phase reviewer)

1. **Writer placement**: attestation writes live in the existing assessment store (extended guard), not a ninth writer, so the event and its requeue commit in one transaction.
2. **Expiry**: modelled as an explicit `EXPIRED` event that ends validity earlier; passive passing of `valid_to` needs no requeue (readings after it were never covered).
3. **Scope**: attestation scoped by tenant/Site/source/epoch (gateway implied by source). Coverage requires the reading's whole measurement interval inside one attestation's validity.
4. **Clock basis churn control**: `clock_basis` pins only attestations touching a selected reading, so an unrelated attestation does not create a new window revision.
5. PG run-1 proof uses instant generator status rows (the S2 test kit has no INTERVAL_MEAN envelope); the 5-minute mean shape is proven in the pure tests and will be proven end-to-end on the authored fixture in phase 2.

## For phase 2

- **Expected churn from dispatch-3.2** (not run here): literal `dispatch-3.1` in `backend/tests/test_s4_finding_*`, `test_s4_consequence_recompute_postgres.py`, `test_s3_performance_cutover.py`, `backend/conversions/s4-finding-cases-v1.json`, `fuel-cost-1-cases-v1.json`, `tools/s3_dispatch_walkthrough.py:70`, frontend `findingClient.ts` comment and `performanceDispatch/siteFinding*` tests. Reconcile requeues every head on bump.
- Finding: `finding_episode.py:302` refuses on `GENERATOR_SERIES_AMBIGUOUS`; carry span + `CohortLimit.evidence_ids/attestation_refs` (in run `cohort.limits`) into the revision, `SERIES_LIMIT` end reason, new `MATCHER_VERSION`.
- Eligibility pending signal: `derive_status` `STALE`/`PENDING` (`dispatch_read.py:72`) plus live jobs; attestation recording already makes the read STALE immediately (N3: missing selected window → `PENDING_REASSESSMENT`).
- Walkthrough: record attestation with `python -m assetops_backend.record_clock_attestation record --site KOBO-001 --source <gen ac-power source uuid> --epoch late-power-epoch-1 ...`; N1 (Performance comparison opens the source gate) and N2 (DB prefix/work dir) still open.
- Open question: none blocking. Reviewer may want to confirm deviation 2 (EXPIRED as an event) against Q3 "expiry".
