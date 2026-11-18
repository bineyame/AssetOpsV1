# Planner fix round 1 - S6-02a / S6-02b

You are the AssetOps Planner (Codex). Amend `tasks/S6-02a-verification-core.md`, `tasks/S6-02b-verification-ui.md`, `tasks/S6-02-verification.md`, `tasks/README.md` and the registry on `plan/S6-02-refine` in this worktree. No code; the coordinator commits.

Inputs: plan review `.agent/S6-02-plan-review.md` (RETURN M1; L1-L9; residual risks) and Architect rulings `.agent/architect-S6-02-answers.md` / `D-2026-10-16-s602-questions`.

1. Fold every Architect ruling into the packets (bands v1 and their computation, five-minute slot convention, plan replacement cutoff, interim labels "Trial missed a safety or service limit" / "Target not met" / "Could not conclude", latest-current default and historical selector), replacing the question sections with short "Architect rulings" sections.
2. M1: registry - `I-S6-02a`'s `sequenced_after` and the `requires` of `I-sim-verification-cases` and `I-verification-read` must point at `I-S6-01a` (or `I-action-store`/`I-action-read`), not the `I-S6-01` umbrella; keep `I-S6-01` on the umbrella and UI side. Confirm with `--next-work --json` that S6-02a nodes no longer carry S6-01/S6-01b in their proof path.
3. Lows: L1 state that `actions/adapters/postgres_action_store.py` (the ninth writer) writes the verification tables (no tenth writer); L2 name the re-evaluation trigger after late evidence (SYSTEM demo request acceptable) and how overlap is detected; L3 the evaluator's values for `action_event.triggering_fixture`, `actor_id`, `authorization_basis`, `triggering_job`; L4 list the store/records Postgres tests and the S6-01a contract fixture affected by the battery-scoped lock, and widen the recommendation read's `PRIOR_ACTION_UNRESOLVED` check to battery scope; L5 make `I-S6-02` require `I-S6-02b`; L6 name `tools/layout-evidence.mjs` for S6-02b; L7 cite where the Lab gets requested/delivered critical load and state the profile publishes power as intervals; L8 fix the LR-01 citation.
4. Residuals: a missing load binding fails comparability (never shrinks totals); demo scripts never present RESOLVED as permanent; note the point-reading risk for the new roles.

Keep Status `implementation-ready`; registry valid. Add a "Plan fix round 1" note to each packet. Print a short summary.
