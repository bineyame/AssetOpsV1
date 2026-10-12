# Architect request: S4-01 phase-1 rule calls (2026-10-12)

Owner Codex rule (verbatim, 2026-10-11): "codex usage optimizaion is important, so keep the same arragment for S2 going forward" — batched questions.

S4-01 phase 1 (Finding store, episode matcher, F01-F08 producer) is built on `task/S4-01-finding-identity` (packet `.agent/S4-01-phase-1-review-packet.md`); a fresh Claude review runs in parallel. Phase 2 (Finding read API) follows.

Rule in one pass on `.agent/S4-01-questions-1.md` Q1-Q9 (each built on a fail-closed default): revision uniqueness key vs the technical design; Indeterminate segments as an episode bridge; recurrence only across an observed OFF; window revision outside the basis hash; collateral SUPPORT_CHANGED revisions after a backdated control; fixture provenance; no `closed_at`; minimum runtime has no product route (fixture control used); `decided` times as ordering labels. Say for each what phase 2/3 must change, if anything. Record material decisions in `.ai/DECISIONS.md` (amend the `A-finding-episode` decision if apt), amend `tasks/S4-01-finding-identity.md` if needed, write `.agent/architect-S4-01-answers-1.md`, and say whether you want the owner to weigh in. No product code; leave edits uncommitted (a reviewer reads the branch concurrently).
