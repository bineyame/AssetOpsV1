# CH-5c handoff 6: fix round CH5c-R6 built; branch review-ready

Builder 6. Branch `task/CH-5c-perf`, worktree `AssetOpsV1-ch5c`. Spec: sheet §8.5. Results: packet section
"Fix round CH5c-R6" in `.agent/review-packet-CH-5c.md`.

## Done
- Guard fix: chain_response SQL in `chain/adapters/postgres_response_store.py`, file reads in
  `chain/adapters/file_code_version.py` and `file_chain_config.load_prebuilt_routes`; wired in `chain/composition.py`;
  registered as `$responseWriter` in `tools/checks/configuration-persistence.ps1` (2 declared shapes, table owner,
  anti-vacuity; proofs in the packet).
- R6: `Demo.serve_env()` feeds tick and serve; `prebuild.run` reports `code_version` and skips without
  `SERVE_KEYS` (`SKIPPED_NO_SERVE_ENV`); per-version prune; factory kept (`create_app`, seam).
- Tests: env parity (L0/L1, proved non-vacuous), 2 new L2. Focused 72 passed / 1 skipped. Guards 14/14 (two parts).
- `fresh` on a recreated clone: 23/23, 23 `chain_response` rows; clone dropped.

## Open
- §8.5 real-serve acceptance moved to end-game E4 (exact check in the packet).
- Merge held for review.
