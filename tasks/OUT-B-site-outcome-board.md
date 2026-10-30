# OUT-B Site outcome board from existing reads

Status: in_progress

Outcome sprint, slice B. Branch `task/OUT-B-site-outcome-board`, worktree `C:\Users\assef\Bineyame\AssetOpsV1-outB`, cut from slice A's head `7b826e97` (main is merged in once A merges).
Implementation contract: `C:\Users\assef\Bineyame\AssetOpsV1-plan2\.agent\build-spec-outcome-sprint-2026-10-29.md` rev 3: §0, §1, "Pre-flight rulings B (2026-10-30)" (wins over older Slice B text) and "Slice B". Pre-flight: `.agent/OUT-B-preflight.md`.

PYTHONPATH (PowerShell):
```
$env:PYTHONPATH = "C:\Users\assef\Bineyame\AssetOpsV1-outB\backend;C:\Users\assef\Bineyame\AssetOpsV1-outB\contracts;C:\Users\assef\Bineyame\AssetOpsV1-outB\simulator;C:\Users\assef\Bineyame\AssetOpsV1-outB\gateway;C:\Users\assef\Bineyame\AssetOpsV1-outB\host;C:\Users\assef\Bineyame\AssetOpsV1-outB"
```

## Gates (from the spec)

- Acceptance criteria B.7 #1-#9.
- Per-unit review for B1, B2 and B4 (ruling B "Units and size"); B3, B5 and B6 in the slice review.
- Validation: focused tests per unit; one full backend run `-Tier all` (idle machine, coordinator's go); full vitest; check-all. The gate ignores by name exactly the known main failures in `.agent/OUT-A-packet.md:99-108` (ruling B-Q32).
- Heavy jobs (measure-mock-panels, full vitest, full backend, captures) only after the coordinator's go.
- Register rows R535 and R540-R549 in `.agent/mock-departure-register.md`.

USER_REVIEW_REQUIRED: false for merge (fresh independent review gates merge; owner sees it in the post-sprint walkthrough).

Review packet: `.agent/OUT-B-review-packet.md`.
