# Planner brief: refine S4-01 (2026-10-12)

Role: Planner (Codex). Branch `task/S4-01-finding-identity` (from main `58b3263`). One bounded pass (owner Codex rule, verbatim 2026-10-11: "codex usage optimizaion is important, so keep the same arragment for S2 going forward").

Selection: next-work selected `I-finding-store` (S4-01); owner chose it in a contest (verbatim: "I-finding-store, and story path first until S4 is done"; `.agent/owner-contest-rule-2026-10-12.md`).

Inputs: the new `A-finding-episode` decision in `.ai/DECISIONS.md` and `.agent/architect-A-finding-episode-answers.md` ("what S4-01 refinement must take"); `D-2026-10-09-pre-s3-claim-routes-and-actor`; S3 decisions; S3-01 as built (`.agent/S3-01-review-packet.md`); owner W1 core panels for S4-01 (`finding:1,2,4`, and per the registry the S4-01-owned portions) in `.agent/W1-owner-input-proposal.md` and the registry mapping; carries in `.ai/MILESTONE_REVIEW_BACKLOG.md` ("A-finding-episode review carries": S4-01 fixture must cover a model-upgrade revision; bridge/merge tested or explicitly deferred); v6.9 mock screen `finding`.

Do (tracked edits; no product code; the coordinator commits):
1. Refine `tasks/S4-01-finding-identity.md` to implementation-ready: ACs, phases under ~120k implementer context, reviewer path, owner checkpoint walkthrough expectations, V-01-style mock comparison increment for `finding` (as S3-01 did for dispatch), honest missing states, fixtures through the normal S2/S3 path.
2. Create `tasks/S3-01u-dispatch-usability.md` (assessed-day discovery; paged evidence) per the Architect, plus its registry node and queue row (follow-up lane; not an S4-01 prerequisite).
3. Update registry/queue only where these packets change them; keep checker passing.
Run the registry checker, workflow and architecture checks and the live `--next-work` report. Questions: `.agent/planner-S4-01-questions.md` with fail-closed defaults (batched). Do not commit. End with a short summary.
