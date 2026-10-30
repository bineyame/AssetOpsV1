# OUT-C Early warnings, first set

Status: in_review

Outcome sprint, slice C. Branch `task/OUT-C-early-warnings`, worktree `C:\Users\assef\Bineyame\AssetOpsV1-outC`, cut from main `e8cf8a36`.
Implementation contract (wins over the sprint spec's Slice C): `C:\Users\assef\Bineyame\AssetOpsV1-plan2\.agent\build-sheet-OUT-C.md`
(§0 rules, §2 units U1-U6, §3 copy, §4 wire, §7 acceptance, §8 register). History: `.agent/OUT-C-phase-handoff.md`.

## Gates (from the sheet)

- Acceptance §7 #1-#8; review points §9.
- Per-unit review for U1 and U2; U3-U6 in the slice review.
- Validation §5: focused tests per unit; one full backend run `-Tier all` and one full vitest (idle machine, coordinator's go); check-all.
  The gate ignores only the 3 `w1f4VerificationStructure` tests and the ruled `coldWorkCases` K3b load flake.
- Heavy jobs (full vitest, full backend, captures at 1440/390) only after the coordinator's go.
- Register rows R560-R571, R541 resolved, notes on R08/R10/R358 in `.agent/mock-departure-register.md`.

USER_REVIEW_REQUIRED: false for merge (fresh independent review gates merge; owner sees it in the post-sprint walkthrough).

Review packet: `.agent/OUT-C-packet.md`.
