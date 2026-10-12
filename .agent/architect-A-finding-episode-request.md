# Architect request: A-finding-episode (2026-10-12)

Owner choice (verbatim, 2026-10-12): "lets go with option A" — selected `A-finding-episode` from a contested next-work ranking (`.agent/next-work-2026-10-12.json`; A-finding-episode 2.761 vs V-01a 2.655). Owner Codex rule (verbatim, 2026-10-11): "codex usage optimizaion is important, so keep the same arragment for S2 going forward" — batch questions.

State: main `79a0664` — S1, S2, S3-01 merged (dispatch-3.1 assessment, revisions, read API, Dispatch UI). Branch `plan/A-finding-episode` (from main) is for this decision.

One batched call:
1. **Record `A-finding-episode`** in `.ai/DECISIONS.md`: the Finding episode and revision contract for the first mini-grid Finding (from dispatch Candidate/Indeterminate assessments): episode identity (stable across late evidence, Site/domain/window keys compatible with the pre-S3 `A-claim-work-routes` route contract and the reviewed FindingIndex key constraints), when an assessment revision creates/updates/closes/splits an episode, immutable FindingRevision lineage to exact assessment revisions and accepted evidence IDs, how a FindingRevision references the selected dispatch-3.x revision (incl. older-rule results), what S4-01 persists and reads, honest states (no Finding vs not assessed vs stale), and the shared parts cold-chain/EV Findings will reuse. Then update the registry node `A-finding-episode` (status resolved with evidence) — or list the exact edit if that is the Planner's file — and say what S4-01 refinement must take from it.
2. **Rule on the pending S3-01 questions** in `.agent/S3-01-questions-4.md` (Q14-Q16; reviewer judged safe) and `.agent/S3-01-questions-5.md` (Q17-Q22), saying which (if any) need a follow-up task.
Write `.agent/architect-A-finding-episode-answers.md`. Say whether you want the owner to weigh in. No product code; leave edits uncommitted (the coordinator commits).
