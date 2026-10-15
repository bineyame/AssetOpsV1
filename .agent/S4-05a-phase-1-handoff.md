# S4-05a phase 1 handoff - admission authority and immutable binding

Branch `task/S4-05a-provenance-binding-resolver` (worktree `AssetOpsV1-review3`), from main `fd7afd2c`.
Build commit `2dd7b92e`. Private test DB `assetops_s405a_test` left in place for phase 2. No `.venv` junction or `var/sites` copy was used. Phase 1 only; phase 2 (resolver) not started. No full suite (owned by S4-05b).

## What landed

- Migration `backend/migrations/versions/0014_evidence_publication.py` (down `0013_schedule_state`). Separate
  insert-only tables (the packet's preferred design; `ingestion_batch` is not altered except one added
  unique constraint):
  - `evidence_publication`: UUID, tenant/Site/gateway/source scoped FKs, `UNIQUE (site_id, external_batch_id)`
    (one publication per admission slot), `payload_sha256`, `source_class` with a null-safe class CHECK
    (authored needs fixture ID+version and no run; simulation needs run ID + 64-hex run digest and no fixture),
    `actor_kind='SYSTEM'`, actor, basis, channel (`SYSTEM_CLI|SYSTEM_FIXTURE|SYSTEM_LAB_RELEASE`),
    `publication_trigger`, `recorded_at` (DB clock).
  - `batch_publication_link`: PK `batch_id`, unique `publication_id`; two composite FKs over
    (tenant, site, gateway, source, external batch ID, payload digest, id) to `ingestion_batch` (new
    `ingestion_batch_commitment_unique`) and `evidence_publication`, so a link can only join an exact commitment.
  - Trigger `source_provenance_immutable` refuses UPDATE/DELETE on both. Downgrade refuses while publications exist.
- Ledger writer `evidence/adapters/postgres_evidence_ledger.py`: `admission_lock_key` / `_lock_slot`
  (`pg_advisory_xact_lock` on tenant|Site|external batch ID); `open_batch` takes the lock, reads the slot's
  publication, raises `PublicationMismatch` on a different gateway/source/digest, inserts the batch
  (`... DO NOTHING RETURNING id`) and inserts the link only when it inserted the batch.
  `register_publication(record)` takes the same lock, refuses `ALREADY_ADMITTED` for any existing batch
  (IN_PROGRESS included), re-reads gateway/source registration (`GATEWAY_NOT_REGISTERED`,
  `SOURCE_NOT_AFFILIATED`, `GATEWAY_NOT_SIMULATED` for simulation), returns the stored ID for an identical
  retry, refuses `PUBLICATION_CONFLICT` / `PUBLICATION_ID_REUSED`.
- `evidence/ledger_service.py`: `PublicationMismatch` -> recorded refusal 409 `PUBLICATION_MISMATCH`
  (nothing admitted; never downgrades to unknown).
- `evidence/publication.py` (domain): classes, `PublicationAuthority` constants `FIXTURE_PUBLISHER`,
  `LAB_RELEASE_PUBLISHER` (server constants; non-SYSTEM or unknown channel -> `SYSTEM_PRINCIPAL_REQUIRED`),
  `authored_record(specs, tenant, batch_text, fixture_id, fixture_version)` (digest recomputed by the canonical
  parser; fixture must be the server spec's declared ID+version), `simulation_records(RunAttestation)` (stage
  is this run's and `STAGED`; each batch re-parses to its stated digest, names the run's Site and pinned
  snapshot, holds exactly its listed messages, all staged by this run), `register_authored`, `register_run`.
- `evidence/adapters/authored_fixture_specs.py` + `composition.build_authored_fixture_specs()`: registry of
  P01 `assetops.s4-power-demo-cases` v1 and P02 `assetops.s4-power-late-demo-cases` v1.
- `runs/source_publication.py`: `run_identity_sha256(run)` (SHA-256 over run_id, created_at,
  deterministic_identity, registered_basis from `render_run_document`) and `run_attestation(run, stage)`
  (stage read by attribute; the gated `gateway_stage` contract is not imported). Only run ID + digest are stored.
- `publish_source.py`: server-side CLI for authored batches (`--site --fixture-id --fixture-version
  --batch-file [--publication-id]`); no HTTP route.
- Rule 8 (`tools/checks/configuration-persistence.ps1`, block after the schedule writer): ledger may INSERT
  provenance only, one line with VALUES and no ON CONFLICT; ledger-wide `DO UPDATE` refused and ON CONFLICT
  allowed only as the three existing DO NOTHING arbiters; ledger DDL/TRUNCATE refused; other writers and
  non-writers refused; non-vacuity per provenance table; HTTP modules (`main.py`, `*_api.py`) may not reference
  designation. Existing eight-writer allowlists, reverse ownership and driver non-vacuity unchanged (the Action
  writer is not on main at `fd7afd2c`).
- Head assertions moved to `0014_evidence_publication` in `test_s1_bindings_postgres.py:118`,
  `test_s2_evidence_ledger_postgres.py:445`, `test_s4_evidence_consequence_work_postgres.py:516,539`.

## Evidence

- `backend/tests/test_s405_publication_postgres.py`: 20 tests, real Postgres (private `assetops_s405a_test`).
- Focused + adjacent run on `2dd7b92e`: S1 bindings, S1 cutover, S2 ledger, S4 evidence-consequence work,
  S4-05a = 96 passed, 136 s. Earlier: S2 ledger/gateway access/site evidence/registered basis + pg harness
  + S4-05a = 105 passed (1 head-assertion failure, fixed in the commit).
- `tools/check-architecture.ps1` and `tools/check-agent-workflow.ps1` pass.
- open_batch lock cost (200 interleaved samples each, private DB, this laptop, one other focused pytest
  running elsewhere): pre-S4-05a statement alone median 12.10 ms / p95 15.49; new open_batch unpublished
  16.61 / 21.68; published (lock + read + link insert) 19.15 / 25.10; unpublished with two threads on
  distinct slots (n=20) 18.68 / 31.93. Added cost about 4.5 ms median unbound, 7 ms bound, per batch (not
  per envelope). Distinct slots do not wait on each other; the same slot serializes (proved by the
  held-lock test: neither registration nor upload ran within 0.6 s while another transaction held the key).
- Mutation proofs (each applied to the committed tree, checked, restored by `git checkout`; tree clean after):
  rule 8 fails with the intended message for ledger UPDATE, DELETE, TRUNCATE and DDL on provenance; an upsert on
  the publication INSERT; an ON CONFLICT arbiter other than the three allowed; a multi-line provenance INSERT;
  another writer (Foundation store) and a non-writer (`evidence/publication.py`) inserting provenance; the link
  INSERT removed (non-vacuity); `evidence_api.py` importing the designation command. Behaviour: the targeted
  test fails when open_batch skips the slot lock, registration ignores a partial admission, open_batch ignores a
  mismatched commitment, a LIVE gateway is accepted for simulation, an identical retry conflicts, or a batch
  with messages the run did not stage is accepted. Truth-table mutations belong to phase 2.

## Next (phase 2)

Resolver per packet phase 2. Provenance join: `accepted_evidence.batch_id -> batch_publication_link.batch_id
-> evidence_publication.id`, scoped by tenant/Site; unlinked = unbound. Several run IDs -> `MIXED` (N-L2;
no compatible-run-basis record exists). FindingRevision evidence at `analytics/finding_read.py:350,446`,
consequence power IDs at `financials/consequence_read.py:87,149`.

## Carries / risks

- Migration re-chain: 0014 here collides with LR-01 (0014/0015) and S6-01a (0014). Whichever merges later
  renumbers onto the then-single head and updates the four head assertions above. Not re-chained now.
- N-L1 (S4-05b): call `run_attestation(run, port.registered_stage(run))` + `register_run` in the registered
  commit path (`simulator_lab_api.py` ~3270, before `port.release_registered`), refusing release on any
  `PublicationRefused`. Phase 1 proves the verification with a duck-typed stage; the real port is untested here.
- The run identity digest is computed from the YAML run record at registration time; nothing in Postgres
  re-verifies it later (the run store is file-backed). A reviewer may want the digest domain/fields named in a
  decision.
- Authored verification checks the server's spec ID/version and canonical bytes; it does not re-derive the
  batch from the spec (the producer in S4-05b builds it from the spec).
- Lock key is the admission slot (tenant, Site, external batch ID), not including gateway/source: the slot is
  the uniqueness scope of `ingestion_batch_external_unique`, so this serializes every contender; gateway, source
  and digest are compared under the lock. Stricter than the packet's wording; flag if the Architect disagrees.
- No TRUNCATE trigger (packet asks for UPDATE/DELETE triggers; the test harness TRUNCATE fallback has none);
  TRUNCATE is refused by rule 8 only.
- Residual from plan review resolved by design: the binding is a separate table, and rule 8 distinguishes the
  existing batch `ON CONFLICT ... DO NOTHING` from any provenance upsert.
