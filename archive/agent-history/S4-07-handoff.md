# S4-07 handoff (build complete; both phases in one go)

- State: built and `in_review` on `task/S4-07-evidence-decided-at`; packet `.agent/S4-07-review-packet.md`. Not merged.
- Anchors: `evidence/adapters/postgres_evidence_ledger.py` `_decision_instant`, `decide_chunk(completed_at=)`, `_coalesce_job` widen lift; `evidence/ledger.py` `decide_chunk` docstring; proofs `backend/tests/test_s4_evidence_decided_at_postgres.py`; F-A override-path test `test_s4_schedule_health_postgres.py::TestStaleWithoutJob`.
- Same-revision full suite: `f1e67a52`, 2147 passed / 0 skipped, 708 s.
- Next: fresh independent slice review (no UI checkpoint). Decide Known Deviation 1 (lift) - accept or route to Architect.
- Open: manual app-clock `process-jobs` residual; `recorded_at` comparand; no batch-lock contention mutation.
