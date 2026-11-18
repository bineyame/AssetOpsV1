# Architect request: batched pre-loop questions (2026-10-11)

Owner instructions (verbatim): 2026-10-09 "codex review happens for the whole S2-0* for usage efficency. also bundle questions to codex, be efficent with its use". 2026-10-11 "Confirm revised W1's 27 screens, core panels, demo values, K=10" then "proceed".

State on branch `plan/pre-S3-startup`: PRE-S3-03 (delivery checker / next-work report) is built and independently reviewed (`.agent/PRE-S3-03-review.md`: accept after F1, being fixed now; C1-C5 carried in `.ai/MILESTONE_REVIEW_BACKLOG.md`). The live next-work report REFUSES: 37 of 51 owner-approved W1 core panels (every S3-S7 core panel plus `evidence-analysis:2#b`) have only proposed `R-*`/`UI-*`/`D-*` gate IDs, not real registry nodes (`.agent/PRE-S3-03-handoff.md`). S3-01 is refined and not activated (`tasks/S3-01-dispatch-assessment.md`).

One batched call; rule on all:
1. `.agent/PRE-S3-03-questions.md` (Q1-Q9; built on restrictive defaults). Notably: V-01 has no effort size (blocked until sized — size it, or tell the Planner how to split it); `evidence-analysis:2` positive claim-limit portion treated as core; any task in review/active stops all selection; Q8 the stale user-visible Readiness wording (review C4) has no owning slice — assign it (e.g. a small fix slice or fold into an existing W1 task) and say whether it may be fixed before the loop starts.
2. `.agent/planner-S3-01-questions.md`.
3. The 37 proposed-only panel paths: state the rule the Planner must follow to turn proposed `R-*`/`UI-*`/`D-*` gates into real registry nodes (which become implementation nodes owned by S3-S7 packets, which architecture nodes they require, naming), so ranking can run without inventing technical readiness. Say whether this can be one Planner pass.
4. Review C5 (`delivery_plan.enables` unread) — fail closed or implement?

Record material decisions in `.ai/DECISIONS.md`; write `.agent/architect-batch-answers-5.md` with exact instructions for the Planner and any implementer fix. Say whether you want the owner to weigh in. No product code; leave edits uncommitted (a Sonnet implementer is fixing F1 in `delivery_next_work.cjs` concurrently; do not touch that file or its tests).
