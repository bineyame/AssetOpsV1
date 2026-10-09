# Architect request: batched S2-02 questions + delivery-strategy contract questions (2026-10-09)

Owner instructions (verbatim): 2026-10-09 "codex review happens for the whole S2-0* for usage efficency. also bundle questions to codex, be efficent with its use". The owner confirmed `D-2026-10-09-owner-delivery-strategy` (`.ai/DECISIONS.md`), which allows planning-only drafts during S2-02.

One batched call. S2-02 is built (all phases) on `task/S2-02-ingestion-site-evidence` (HEAD `3ea80a9`; packet `.agent/S2-02-review-packet.md`; owner walkthrough `.agent/S2-02-owner-walkthrough.md`; recorded demo run `.agent/S2-02-demo-run-output.txt`). A fresh Claude review runs in parallel; the owner Evidence checkpoint follows; then one Codex review of S2-01c+S2-02.

Part A — open S2-02 implementer questions, each built on a fail-closed default:
- `.agent/S2-02-questions-4.md` (Q21-Q24; Q21 was later built — confirm)
- `.agent/S2-02-questions-5.md` (Q25-Q31). Q28 matters before the owner walkthrough: if the DB connection drops at commit during credential rotation, the new file is discarded though the old credential may already be revoked — could strand the gateway.
- `.agent/S2-02-questions-6.md` (Q32-Q36). Also note the demo produced 246 batches / 293 readings against the earlier 245/292 proof (implementer did not check why).

Part B — delivery-strategy planning drafts (Codex Planner, `.agent/delivery-drafts/`): answer `.agent/delivery-drafts/questions-for-architect.md` (four contract questions, including which shared contracts are mandatory pre-S3 gates). You may comment briefly on `reconciliation-draft.md` and `w1-panel-mapping-draft.md` only where they would mislead; they are applied after S2-02 closeout.

Please rule on all in one pass. Record material decisions in `.ai/DECISIONS.md`; amend `tasks/S2-02-ingestion-site-evidence.md` only if something must change before the owner walkthrough; record carries in `.ai/MILESTONE_REVIEW_BACKLOG.md`. Write `.agent/architect-batch-answers-4.md` with (a) anything that must be fixed before the owner walkthrough, (b) carries, (c) Part B answers. Say whether you want the owner to weigh in. Do not review the slice. No product code; leave edits uncommitted.
