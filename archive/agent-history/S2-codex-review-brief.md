# Review brief: one Codex review of S2-01c + S2-02 (2026-10-09)

Role: Reviewer (Codex). Owner rule (verbatim, 2026-10-09): "codex review happens for the whole S2-0* for usage efficency. also bundle questions to codex, be efficent with its use". S2-01a and S2-01b had their own Codex reviews earlier.

Targets:
- S2-01c: merged to main at `b4006d1` (branch `task/S2-01c-gateway-diagnostics-faults`, diff `08712e7..6e42818`). Fresh Claude reviews: `.agent/S2-01c-review.md`, `.agent/S2-01c-fix-rereview.md`, `.agent/S2-01c-fix2-rereview.md`. Packet `.agent/S2-01c-review-packet.md`. Spec `tasks/S2-01c-gateway-diagnostics-faults.md`.
- S2-02: branch `task/S2-02-ingestion-site-evidence`, current HEAD (diff `6e42818..HEAD`; includes coordinator decision/record commits and delivery-strategy records that are not product work). Fresh Claude reviews: `.agent/S2-02-review.md`, `.agent/S2-02-fix-rereview.md`. Packet `.agent/S2-02-review-packet.md`; owner walkthrough `.agent/S2-02-owner-walkthrough.md`; recorded demo `.agent/S2-02-demo-run-output.txt`. Spec `tasks/S2-02-ingestion-site-evidence.md`.
- Decisions: S2 entries in `.ai/DECISIONS.md`; Architect answers `.agent/architect-*S2*` and `.agent/architect-batch-answers-*.md`. Carries: `.ai/MILESTONE_REVIEW_BACKLOG.md`. Open implementer questions not yet ruled: `.agent/S2-02-questions-7.md`.
- Standing criteria: task files, `.ai/WORKFLOW.md`, `.ai/ROLE_CONFIG.md`, project records.

Already run (do not re-run green suites unless testing a specific doubt): S2-02 backend with Postgres 1760, gateway 164, host 662, simulator 265, frontend vitest 1270, tsc/build clean, architecture/workflow checks; S2-01c final suites recorded in its packet; isolated end-to-end TLS demo recorded. The owner Evidence walkthrough runs in parallel.

Constraints: do not fix, merge or commit (git is read-only for you). Do not start servers on the owner's ports (8000, 5173/5183/5199/5213/5291) or modify `var/`. Write `.agent/S2-codex-review.md` with a verdict per slice and findings, each classified block or carry with reason.
