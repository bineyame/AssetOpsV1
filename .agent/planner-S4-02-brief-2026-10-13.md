# Planner brief: S4-02 refinement and split (2026-10-13)

Role: Planner (Codex, per `.ai/ROLE_CONFIG.md`). Working tree `C:\Users\assef\Bineyame\AssetOpsV1`, branch `plan/S4-02-refine` (from main `2c87037`). Codex cannot write .git: edit files only; the coordinator commits.

The owner selected S4-02 money (`I-financial-store`) next (verbatim in `.agent/owner-next-work-2026-10-13d.md`) after a ≤5% contest with A-S5-overview.

Already verified by the coordinator (do not repeat): check-all passes 9/9 on main, and next-work/verify-report exit 0. `A-S4-financial` is resolved by `D-2026-10-13-s4-bounded-financial-basis`. The fresh Claude review of that decision is ACCEPT.

## Read first (bounded)
- `.agent/coordinator-handoff.md` (top section only), `AGENTS.md`, `.ai/START_HERE.md`, `.ai/PLANNING_GUIDANCE.md`, `.ai/WORKFLOW.md` (Task Spec Size: S/M; ceiling 160-220 lines).
- `tasks/README.md`; `tasks/S4-02-bounded-financials.md` (outline); `tasks/S4-03-finding-evidence-history.md` as a recent implementation-ready example.
- **The decision and its review, which govern:** `.agent/architect-A-S4-financial-answers.md`, `D-2026-10-13-s4-bounded-financial-basis` in `.ai/DECISIONS.md`, and `.agent/A-S4-financial-review.md`. The review's Planner carries M1, M2 and L1-L7 (also in `.ai/MILESTONE_REVIEW_BACKLOG.md` "A-S4-financial carries") must each be resolved in the packets, or named as a question.
- The registry nodes on S4-02's path in `frontend/docs/architecture/v69-dependency-registry-pilot.json`: `I-S4-02`, `I-financial-store`, `D-financial-basis`, `I-financial-read`, `I-financial-ui`, `I-assumption-history-read`, `I-assumption-history-ui`; panels `financials:1-3`, `assumptions:1-3`, `mini:4`; gap `G-foundation-financial-assumptions`.
- Prior decisions `D-2026-10-09-pre-s3-claim-routes-and-actor` (A-actor-identity) and `D-2026-10-12-finding-episode-and-revisions`. The S4 parts of `frontend/docs/architecture/production-shaped-mvp-technical-design.md` and `site-first-execution-plan.md`.
- Mock: the `financials` and `assumptions` screens in `frontend/mockups/v69/`. The owner's missing-data rule applies: content without a source is shown as "Not available yet" through `<MissingClaim gapId>` (`D-2026-10-13-g01-placement-and-orphan-scan-boundary`, G-02 decision), or named for G-05.
- Built code only where needed for accurate anchors (bounded reads): the S4-01/S4-03 finding read/API, Foundation `specific-fuel-consumption`, `analytics/dispatch.py` (`SFC_UNCERTAINTY`), and the actor/principal handling (`finding_api.py`).

## Work
1. Split the outline into two implementation-ready packets, as the decision requires: `tasks/S4-02a-...md` (Site-scoped assumption publication, SYSTEM trigger, exact history read/UI, honest unpriced/quantity-unavailable Finding bridge) and `tasks/S4-02b-...md` (reviewed `fuel-cost-1` quantity bound, consequence store/recompute/read/UI, price-change revision, lineage walkthrough). Each packet needs:
   - concrete ACs, reviewer steps, file/API anchors, migration shape and out-of-scope;
   - honest missing states, including how new missing copy interacts with the orphan scan;
   - checks, including `tools/check-all.ps1` and 1440/390 layout evidence where layout-sensitive;
   - the owner walkthrough expectation, with `USER_REVIEW_REQUIRED` kept true on the slice that carries the S4-02 owner checkpoint;
   - phases under ~120k context each for a Claude implementer.
   Keep the original `tasks/S4-02-bounded-financials.md` as a short pointer, or the closeout record, as you judge consistent with the queue rules.
2. Map each S4-02 registry node to S4-02a or S4-02b (carry L2). Fix `I-S4-02` effort, and split nodes only if needed. List the exact registry and ledger edits; make them only if they are pure planning metadata that keep the guards green. Update the `tasks/README.md` S4 rows.
3. No product code. Do not merge.

## Open questions
Questions go to `.agent/planner-S4-02-questions-2026-10-13.md`. Each must be self-contained, with options, a recommendation, and whether implementation can proceed on a fail-closed default. Include only questions that genuinely block, or that would mislead an Implementer. Batch them; the coordinator sends them to the Architect in one call.

End with a short summary: files changed, and the questions file path (or "none").
