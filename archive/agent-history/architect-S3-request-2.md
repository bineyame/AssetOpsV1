# Architect request: S3-01 phase-2 questions (2026-10-11)

Owner routing (verbatim, 2026-10-11): "codex usage optimizaion is important, so keep the same arragment for S2 going forward" — batched Codex questions.

S3-01 phase 2 (typed seam, dispatch-3, durable assessment, recompute worker) is built on `task/S3-01-dispatch-assessment` (packet `.agent/S3-01-phase-2-review-packet.md`); a fresh Claude review runs in parallel. Phase 3 (read API, Dispatch/Analysis UI, file-backed comparison, Performance cutover, V-01 dispatch comparison, owner walkthrough) needs your rulings first.

Rule on `.agent/S3-01-questions-2.md` Q1-Q8 in one pass (each built on a fail-closed default). Q1 (controls from the configuration selected at the cutoff vs only the as-accepted revision) and Q4 (how the default read shows a manifest-labelled fixture stream; ties to your earlier F4 ruling in `.agent/architect-S3-answers-1.md`) block phase 3. Also say whether phase 3 needs the projection table the implementer deferred. Record material decisions in `.ai/DECISIONS.md`, amend `tasks/S3-01-dispatch-assessment.md` if needed, write `.agent/architect-S3-answers-2.md` with the exact phase-3 changes, and say whether you want the owner to weigh in. No product code; leave edits uncommitted (a reviewer is reading the branch concurrently).
