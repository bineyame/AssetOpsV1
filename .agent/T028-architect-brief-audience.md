# Architect brief: T028 audience (Codex Architect, 2026-10-04)

You are the AssetOps Architect (Codex; `.ai/ROLE_CONFIG.md`, including
"Decision Requests Go To The Active Architect").

The owner's question, verbatim with the coordinator's reading:
`.agent/owner-T028-audience-question-2026-10-04.md`.

Target: branch `task/T028-dispatch-finding-and-evidence`, HEAD `30122ed`.
Task `tasks/T028-dispatch-finding-and-evidence.md`; packet
`.agent/T028-review-packet.md` (screens, owner walk); the screens under
`frontend/src/sites/` (FindingDetail, SitePerformance, FindingsIndexes,
CapabilityReadiness, SiteOverview) and the backend text they render
(`backend/assetops_backend/analytics/`). Sources of intent:
`.ai/ARCHITECT_DEMO_RECOMMENDATION.md`, `.ai/PRODUCT.md`, `.ai/FEATURE_MAP.md`
(C, D), `Docs/queue-review-feedback-verbatim.md`, decisions the task cites,
`D-2026-10-04-analytic-readiness-scope-and-gap-impact`, and the queue in
`tasks/README.md` (T029 next). Your earlier record on this slice:
`.agent/T028-architect-readiness-decisions.md`.

Already verified (do not re-run): backend 1485, host 616, frontend 1099,
checks pass; Codex review R1-R5 fixed; Claude re-review accepted.

Constraints: do not edit code, tests or task files; do not merge. Write
`.agent/T028-architect-audience.md`: your answer to the owner's question,
justification, what (if anything) should change and in which slice (T028
before merge, T029, or later), and whether you want the owner to weigh in.
If a durable decision is warranted, draft its `.ai/DECISIONS.md` entry text
there; the coordinator lands it. Write for the owner: plain language first.
