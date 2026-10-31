# OUT-D Declared objectives and status

Status: in_review

Outcome sprint, slice D (rev 6 §4.3: an outcome's status is judged against a declared objective, labelled on screen).
Branch `task/OUT-D-declared-objectives`, worktree `C:\Users\assef\Bineyame\AssetOpsV1-outD`, cut from main `833e7c95`
(OUT-W merged in). Implementation contract: `C:\Users\assef\Bineyame\AssetOpsV1-plan2\.agent\build-sheet-OUT-D.md`
(§0 rules, §3 units U1-U6, §4 copy, §6 register R580-R586, §8 acceptance, §9 review points). Architect rulings:
`.agent/decisions-while-owner-away-2026-10-30.md` (Q1) and the 2026-10-31 rulings on the U4 review
(`AssetOpsV1-plan2/.agent/OUT-D4-review.md` M1, M2, L1).

## Gates (from the sheet)

- Acceptance §8 #1-#6; review points §9. Per-unit review for U1-U3; U4 slice review (shared seam); U5-U6 slice review.
- Focused tests per unit (§5); check-all at every unit; one full `npx vitest run` and one
  `run-backend-suite-in-container.ps1 -Tier all` at slice end (schema change; coordinator's go). The gate ignores only
  the 3 `w1f4VerificationStructure` tests.
- Captures at 1440/390 vs v70: Kobo, GreenHarvest and Depot Overview, Portfolio (`.agent/OUT-D-captures/`).

USER_REVIEW_REQUIRED: false for merge (fresh independent review gates merge; owner sees it in the post-sprint walkthrough).

Review packet: `.agent/OUT-D-packet.md`. History: `.agent/OUT-D-phase-handoff.md`.
