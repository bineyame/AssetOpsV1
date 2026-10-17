# Architect request - W2-02 cold readiness gate (2026-10-18). Brief; edit `.agent/W2-02-build-spec.md` in place; amend `D-2026-10-17-w2-02-buildspec`. No code.

Implementer finished commit (4) (branch task/W2-02-cold-producer, packet `.agent/W2-02-review-packet.md` deviations 1-3). Blocker (High): `binding_service.acquisition_snapshot` applies the mini-grid configuration-gap check to COLD-LAB-001 (SITE_TYPE_UNSUPPORTED + electrical component gaps), so `RegisteredLabBasis` refuses every production cold Draft. The six Postgres proofs lift only that gap check test-only for COLDCHAIN (`open_cold_snapshot_gate`).
1. Specify exactly how cold-chain readiness gates the acquisition snapshot (which cold gaps, from which existing W2-01 readiness rules, what refuses), so production cold Drafts work without the test-only lift; name the code seam.
2. Rule on deviation 2: the session-id conflict proof posts directly to the S2 ingestion route with the session channel bound test-only (COLD-LAB-001 has no session channel; gateway refuses unbound channels), as W2-00 tests do. Acceptable?
3. Rule on deviation 3: `evidence/publication.py:simulation_records` now reads schema-4 envelopes by header (same rule as `seal_batch_v2`). Acceptable?
Print a 3-line summary.
