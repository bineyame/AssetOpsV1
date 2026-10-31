# OUT-E Cost check after the trial

Status: in_review

Outcome sprint, slice E: after the generator stop trial is verified at Kobo, the Optimize cost Earlier entry and the
Assure Verified results line show the modelled cost change per kWh of feeder demand ("not realised savings") and the
Supply cost per kWh objective before and after the trial, on the trial's own frozen hours, fuel rate and diesel price.
Branch `task/OUT-E-cost-proof`, worktree `C:\Users\assef\Bineyame\AssetOpsV1-outE`, from main `b94aee17` (A, B, C,
OUT-W, FIX-01, D merged). Implementation contract: `C:\Users\assef\Bineyame\AssetOpsV1-plan2\.agent\build-sheet-OUT-E.md`
(§0 rules, §2 units E1-E5, §4 copy, §6 register, §8 acceptance, §9 review points). Architect ruling 2026-10-31 on E4
(option b; register R595 open). E2/E3 review: `AssetOpsV1-plan2/.agent/OUT-E2-3-review.md` (REVISE; fixed).

## Gates (from the sheet)

- Acceptance §8 #1-#5; review points §9. Per-unit review E1-E3; E4 and E5 slice review.
- Focused tests per unit (§5); check-all at every unit; one full `npx vitest run` and one
  `run-backend-suite-in-container.ps1 -Tier all` at slice end (migrations; coordinator's go). Known failures: the 3
  `w1f4VerificationStructure` vitest tests.
- Captures at 1440/390 vs v70: Kobo Overview on the `verified` and `inconclusive` DBs (`.agent/OUT-E-captures/`).

USER_REVIEW_REQUIRED: false
