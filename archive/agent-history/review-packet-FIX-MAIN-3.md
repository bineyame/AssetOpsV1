# FIX-MAIN-3 review packet
Task: regenerate backend/tests/fixtures/s6_verification_api_contract.json (stale since a8c748b7c CH-5a2b added verification.source_class).
Method: ASSETOPS_WRITE_S6_VERIFICATION_CONTRACT=1 via tools\run-host-tests.ps1 on test_s6_verification_evaluator_postgres.py (assetops_test DB).
Diff: 1 file, 1 insertion, 0 deletions. After excluding UUIDs, 40+ hex hashes and ISO timestamps, the only change is the added line `"source_class": "AUTHORED_DEMONSTRATION"`. Nothing else changed.
Re-run without env var: 11 passed (3:06), including test_verified_resolves_then_late_evidence_withdraws_and_overlap_blocks.
