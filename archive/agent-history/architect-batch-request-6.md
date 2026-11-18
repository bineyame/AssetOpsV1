# Architect request: loop instruction review + open mapping questions (2026-10-11)

Owner instructions (verbatim): 2026-10-09 "codex review happens for the whole S2-0* for usage efficency. also bundle questions to codex, be efficent with its use". 2026-10-11 "Confirm revised W1's 27 screens, core panels, demo values, K=10" then "proceed".

State (branch `plan/pre-S3-startup`): startup prerequisites 1/3/4/5 done and independently reviewed (PRE-S3-03 checker, PRE-S3-04 Readiness wording, W1 64-panel mapping all `reviewed_mapping:true` per `.agent/W1-mapping-review.md` and `.agent/W1-mapping-fix-rereview.md`). The live next-work report now ranks: select `I-sim-dispatch-cases` 3.018 over `A-finding-episode` 2.679 (gap 11.2%, no notice; S3-01 is USER_REVIEW_REQUIRED) — `.agent/W1-first-ranking.md`. The last carry round (C9: stop over every linked packet, plus a gate-refusal return bug and an `umbrella` status) is not yet independently re-reviewed.

One batched call:
1. Review the coordinator loop instruction `.ai/COORDINATOR_LOOP.md` (startup 6; "Coordinator, with Architect/Planner review") against `D-2026-10-09-owner-delivery-strategy`, `.ai/WORKFLOW.md` and `.ai/ROLE_CONFIG.md`. Amend it in place where it is wrong or unsafe; keep it short.
2. Rule on the mapping carries that are Architect questions in `.ai/MILESTONE_REVIEW_BACKLOG.md` "W1 mapping review carries": C1 (S4-03 bundling makes Finding Evidence/History wait on `A-finding-index`; accept or split), C5 (`A-action-index` gating all 14 Action panels vs Site list only), C6 (S6 panels' S4-01 Finding closeout dependency). Give exact registry/packet edits for the Planner/implementer.
3. Confirm whether anything else must close before loop activation (e.g. the C9 re-review, merging `plan/pre-S3-startup` to main), in order.

Record material decisions in `.ai/DECISIONS.md`; write `.agent/architect-batch-answers-6.md`. Say whether you want the owner to weigh in. No product code; leave edits uncommitted.
