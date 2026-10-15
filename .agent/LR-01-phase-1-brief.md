# LR-01 phase 1 — implementer brief

Branch `task/LR-01-late-reading-series-and-money-limit` (checked out in `C:\Users\assef\Bineyame\AssetOpsV1`, HEAD `2386a1a3`). Packet `tasks/LR-01-late-reading-series-and-money-limit.md` — build **phase 1 only** (source-time contract S3 cohort v4, SYSTEM-only simulated attestation persistence and input basis, affected-window requeue, reassessment keeping history). Authority: `.agent/architect-LR-01-answers.md` (Q1-Q4, packet changes 1-3, Follow-up M1) and `D-2026-10-15-lr01-source-time-cohort` in `.ai/DECISIONS.md`. Plan reviews: `.agent/LR-01-plan-review.md`, `.agent/LR-01-plan-rereview.md`.

## Carries from the plan re-review (Low; handle where they fall)

- N1 (phase 2, but design for it): LR-01 `run` must perform the Performance comparison that opens the source gate, so served Financials shows the four states rather than "blocked".
- N2 (phase 2): the walkthrough tool's DB prefix `assetops_lr01*` vs the existing `assetops_s402c3walk` guard and `s402c3*` drop rule, and `--work` path (repo-relative vs LOCALAPPDATA default): settle both consistently.
- N3 (phase 2): a missing selected window for any required day reads as `PENDING_REASSESSMENT`.

## Process rules (owner-approved speed rules)

- Focused tests only in this phase: the pure cohort tests and `backend/tests/test_s3_dispatch_assessment_postgres.py` plus whatever S3/attestation files you add or touch, and the replay-digest test at `:139-143`. Use `backend/TESTING.md` focused commands (they route to private `_test` DBs automatically). No full suite in phase 1 — that runs once at the end of phase 2.
- If any run is long, start `tools/keep-awake-during-tests.ps1` in the background first and cap the run at 2x its expected time; report an overrun rather than wait on it.
- Mutation checks only for the core cohort/ordering logic and the SYSTEM-only write refusal.
- Commit on the branch as you go. Do not merge. Do not touch `.agent/coordinator-handoff.md`. Run `powershell -ExecutionPolicy Bypass -File tools/check-all.ps1` before handoff.
- If an Architect ruling turns out to be unimplementable as written, stop and report the specific conflict instead of improvising.

## Handoff

`.agent/LR-01-phase-1-handoff.md` (git add -f): what changed, outcome-table rows proven in phase 1, focused test results, mutation results, deviations, open questions for phase 2. Report back concisely.
