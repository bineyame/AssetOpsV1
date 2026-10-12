# Architect request: S4-01 phase-1 fix-round questions (2026-10-12)

Owner Codex rule (verbatim, 2026-10-11): "codex usage optimizaion is important, so keep the same arragment for S2 going forward" — batched.

The S4-01 phase 1 fix round is complete on `task/S4-01-finding-identity` (packet section "Fix round 1" in `.agent/S4-01-phase-1-review-packet.md`); a fresh Claude re-review runs in parallel. Phase 2 (Finding read API) is next.

Rule in one pass on `.agent/S4-01-questions-2.md` Q10-Q15 (fail-closed defaults built). Q14 (every same-day reassessment appends BASIS_REFRESHED to every Finding on that day — how phase 2's read and phase 3's History must group/present provenance updates) and Q15 (the gateway F01 case runs on 2026-10-02 because the 10-03 fixture control sets generator minimum runtime to 0, which the Lab refuses) matter most. State exactly what phase 2 must implement for each. Record material decisions in `.ai/DECISIONS.md`, amend `tasks/S4-01-finding-identity.md` if needed, write `.agent/architect-S4-01-answers-2.md`, and say whether you want the owner to weigh in. No product code; leave edits uncommitted.
