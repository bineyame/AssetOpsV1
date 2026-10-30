# OUT-W Estate event windows for cold and EV Sites

Status: in_review

Outcome sprint, follow-up to OUT-C (P-C1, owner option A: "latest assessed event within the period"). Branch
`task/OUT-W-estate-event-windows`, worktree `C:\Users\assef\Bineyame\AssetOpsV1-outW`, cut from main `833e7c95`.
Implementation contract: `C:\Users\assef\Bineyame\AssetOpsV1-plan2\.agent\build-sheet-OUT-W.md` (§0 rules, §2 units W1-W3,
§3 wire, §5 acceptance, §6 register). Resolves R575; adds R576 and R577 (Architect ruling (a), 2026-10-31, EV 6 Oct).

## Gates (from the sheet)

- Acceptance §5 #1-#6; review points §8. Per-unit review for W1 and W2; W3 in the slice review.
- Focused tests per unit; check-all at every unit; full vitest and `run-backend-suite-in-container.ps1 -Tier fast` once at
  slice end (coordinator's go). The gate ignores only the 3 `w1f4VerificationStructure` tests.
- Captures at 1440/390 vs v70 on the w502 `positive` DB (`.agent/OUT-W-captures/`).

USER_REVIEW_REQUIRED: false for merge (fresh independent review gates merge; owner sees it in the post-sprint walkthrough).

Review packet: `.agent/OUT-W-packet.md`. History: `.agent/OUT-W-phase-handoff.md`.
