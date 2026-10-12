# Architect request: S4-01 phase-2 questions (2026-10-12)

Owner Codex rule (verbatim, 2026-10-11): "codex usage optimizaion is important, so keep the same arragment for S2 going forward" — batched.

S4-01 phase 2 (Finding read API) is built on `task/S4-01-finding-identity` (packet `.agent/S4-01-phase-2-review-packet.md`); a fresh Claude review runs in parallel. Phase 3 (Finding screen, R1 gateway-day labelling, owner walkthrough) follows and needs your rulings.

Rule in one pass on `.agent/S4-01-questions-3.md` Q16-Q20 (fail-closed defaults built). Q16 (401/403 only via an access check; default admits the development tenant — what phase 3 and the owner walkthrough may claim about access) and Q17 (the Q11 bridge rule only partly met: a contradictory report between the two OFFs is not detected because the dispatch-3.1 interval result does not carry it — S3 change, matcher read of window evidence, or accepted limitation?) matter most; also Q19 (Finding read not behind the Performance cutover gate). State exactly what phase 3 must do. Record material decisions in `.ai/DECISIONS.md`, amend `tasks/S4-01-finding-identity.md` if needed, write `.agent/architect-S4-01-answers-3.md`, say whether you want the owner to weigh in. No product code; leave edits uncommitted.
