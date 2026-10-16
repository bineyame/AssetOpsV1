# S6-02a phase 2 - implementer brief

Work ONLY in worktree `C:\Users\assef\Bineyame\AssetOpsV1-review4`, branch `task/S6-02a-verification-core` (main merged in at `e39a3c20`). Touch no other worktree.

Environment: main venv python (`C:\Users\assef\Bineyame\AssetOpsV1\.venv\Scripts\python.exe` or the `.venv` here) with `PYTHONPATH` = this worktree's `backend;contracts;gateway;simulator` (confirm `assetops_backend.__file__` resolves here); `ASSETOPS_GUARD_PYTHON` = the same python; private `*_test` DB on the Docker Postgres (127.0.0.1:55432). Copy `var/sites/*.yaml` from the main checkout only if a test needs them. The keep-awake helper is NOT running (host policy), so the laptop may enter Modern Standby and slow runs; check System events 506/507 before calling a slowdown a regression. Memory is limited (~5 GB free): run focused tests serially or `-n 2`, never several Postgres-heavy runs at once.

Read: packet `tasks/S6-02a-verification-core.md` (phase 2 row, coordinator note R1/R2), `.agent/S6-02a-phase-1-handoff.md`, `.agent/S6-02a-phase-1-review.md`, and the Architect rulings `D-2026-10-16-s6-verification`, `D-2026-10-16-s602-questions`, `D-2026-10-16-s602a-cutoff` (`.agent/architect-S6-02a-cutoff-answers.md`).

## First: phase-1 review fixes
- F1 (Medium): freeze refuses with `VERIFICATION_FOUNDATION_NOT_COMPARABLE` unless the baseline's covering FoundationRevision is the change's split/superseded revision. Postgres test with an intervening revision (refused) beside the pass case.
- F2 (per `D-2026-10-16-s602a-cutoff`): freeze requires every baseline UTC day (incl. a cross-midnight previous day) CURRENT by `derive_status`; binding refuses before `later_end` and unless every later day is CURRENT; evaluator returns REASSESSMENT_PENDING unless both pinned windows stay CURRENT. Test pending/stale/failed, before/after `later_end`, and a pinned day turning non-current.
- F3 (ruling): keep "first accepted later-window report" as the cutoff; tests for another role/asset, the exact `later_start` boundary, and an unaccepted report not tripping it. The ruling also asks that the cutoff check and replacement insert be serialized against acceptance; use the smallest sound mechanism (for example a shared advisory lock or a transaction-level check). If it would need more than a minimal touch of the S2 acceptance writer, document the residual gap in the handoff instead of widening scope.
- F4: persist and compare the binding idempotency key (as freeze does) or drop the field; refuse binding to a non-head plan.
- F5: make the race test print `out` on failure and shorten the in-lock sleep.
- F6: filter window evidence to the plan's battery and bound assets.
- F7 (ruling): `+00:00` for every verification API timestamp; fixture asserts it.
- F8: label the second same-battery Action in `s6_action_api_contract.json` as a pre-S6-02a state.

## Then: phase 2 as the packet defines it
Evaluator job (outcome + metrics + RESOLVED/RESOLUTION_WITHDRAWN in one transaction under the battery `trial_lock`; idempotent retries return the same outcome ID; changed basis appends a superseding outcome), per-window S4-05 source resolution, S3/S4 pending-work gates and REASSESSMENT_PENDING, `lifecycle.reduce`/`is_unresolved` from the latest resolution, `PRIOR_TRIAL_GUARDRAIL_FAILED` and `PRIOR_TRIAL_REASSESSMENT_OVERLAP` (R1: only late evidence that invalidated the closure counts; test both sides), evaluation-request route, outcome/history reads, Action/Recommendation/Change verification state, versioned API fixture for S6-02b, the `D-verification-window` replay manifest (two registered Lab runs on a roles-3 Site; it must prove a complete positive path: pick seeds and windows with no dropped slot), demo `VERIFY` grant. Rerun `tools/writer_guard_probes.py` (phase-1 probes are unproven). Mutation checks only for fail-closed verdict rules, holds and the lock.

Final revision: `tools/check-all.ps1`, the registry checker, and ONE full suite from PowerShell `pytest backend/tests -n 2 --dist loadfile --no-loadscope-reorder -q --junitxml=<absolute path>` (cap 40 min given standby; report wall time and JUnit counts; zero failed/skipped).

Process: owner direction is demo speed over perfection; only correctness and fail-closed matter, no wording polish. Commit on the branch in logical steps; do not merge; do not touch `.agent/coordinator-handoff.md` or `.agent/owner-autonomy-2026-10-15.md`. If an Architect ruling is unimplementable, stop and report. Write `.agent/S6-02a-review-packet.md` and `.agent/S6-02a-phase-2-handoff.md` (git add -f; `.agent` is gitignored). Report concisely: commits, tests and counts, deviations, residual risks.
