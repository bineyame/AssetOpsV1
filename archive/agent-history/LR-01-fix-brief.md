# LR-01 fix round (Sonnet) - Architect deviation rulings + slice review Lows

Work ONLY in worktree `C:\Users\assef\Bineyame\AssetOpsV1-review`, branch `task/LR-01-late-reading-series-and-money-limit` (head `87019e52`). S5-01 is being built in the main checkout on a branch stacked on LR-01; do not touch the main checkout.

Environment: Python `C:\Users\assef\Bineyame\AssetOpsV1\.venv\Scripts\python.exe` with `PYTHONPATH=C:/Users/assef/Bineyame/AssetOpsV1-review/backend;C:/Users/assef/Bineyame/AssetOpsV1-review/contracts;C:/Users/assef/Bineyame/AssetOpsV1-review/gateway;C:/Users/assef/Bineyame/AssetOpsV1-review/simulator` (confirm `assetops_backend.__file__` is in this worktree). `frontend/node_modules` here is a real install (`npx.cmd vitest run <file>`, `npx.cmd tsc --noEmit`, `npm.cmd test` work). Private Postgres base DB ending `_test` per `backend/TESTING.md`. Keep-awake is running.

Inputs: Architect `C:\Users\assef\Bineyame\AssetOpsV1-gap-planning\.agent\architect-LR-01-deviations-answers.md`; slice review `.agent/LR-01-review.md` (L1-L3).

Do:
1. Ruling 1: correct the stale store module docstring the Architect names; confirm 0015 downgrade refuses duplicate history; add the L2 downgrade tests (refusal when a returning basis exists; clean path).
2. Ruling 2: the S5 seam (`backend/assetops_backend/scheduling/upstream.py`) must not rewrite an ELIGIBLE `money_eligibility` to PENDING_REASSESSMENT for S3/S4/schedule blockers; expose the shared eligibility result (with lineage) and the seam's own currentness/schedule status as separate fields with typed reasons. Update tests; the seam must still never permit a current amount unless eligibility is ELIGIBLE and upstream is current.
3. Ruling 4: correct "Finding money panel" wording in `tasks/LR-01-late-reading-series-and-money-limit.md`, `.agent/LR-01-review-packet.md` and `.agent/LR-01-owner-walkthrough.md` (money on the Financials bridge; Finding page shows the SERIES_LIMIT statement and evidence link).
4. Ruling 5: an integration test proving production composition wires the persisted gate into `ConsequenceReadService` and that a failed gate read shows no current amount.
5. Review L1 (owner-visible copy): `frontend/src/sites/FindingConsequence.tsx:436-442` `MoneyLimit` - word each limit by its relation (tail cut, head cut, inside episode, neighbouring window within 6 h) and source; do not call 07:05-08:00 "arrived out of order" when the late record is 07:00-07:05; skip the list when nothing is withheld by span; add a test for a non-tail limit. Keep copy plain and honest.
6. Review L3: add the residual (a neighbouring-day generator refusal can withhold a Finding it does not touch, until resolved) to the packet's known deviations and the owner walkthrough notes.

Proof: focused backend tests for touched areas; `npx.cmd tsc --noEmit` and the touched frontend test files plus `npm.cmd test`; then ONE full backend suite `-n 2 --dist loadfile --no-loadscope-reorder` (20-min cap) since backend code changed; `tools/check-all.ps1` (if a guard needs main-checkout-only tooling, run the guards that work here and say which could not). Re-run browser evidence for the Financials withheld state at 390 only if feasible here; otherwise say not run. Drop every DB you create.

Commit on the branch (small commits). Write `.agent/LR-01-fix-handoff.md` (git add -f) listing each item, files touched (especially `upstream.py`, which S5-01 will need to absorb), tests and results. Report concisely.
