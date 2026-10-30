# OUT-A Category labels and links

Status: in_review

Outcome sprint, slice A. Branch `task/OUT-A-category-labels`, worktree `C:\Users\assef\Bineyame\AssetOpsV1-outA`, cut from main `287a63a7`.
Implementation contract: `C:\Users\assef\Bineyame\AssetOpsV1-plan2\.agent\build-spec-outcome-sprint-2026-10-29.md` rev 2, §0, §1.1-1.3, "Pre-flight rulings A (2026-10-29)" and "Slice A". Pre-flight: `.agent/OUT-A-preflight.md`.

PYTHONPATH (PowerShell):
```
$env:PYTHONPATH = "C:\Users\assef\Bineyame\AssetOpsV1-outA\backend;C:\Users\assef\Bineyame\AssetOpsV1-outA\contracts;C:\Users\assef\Bineyame\AssetOpsV1-outA\simulator;C:\Users\assef\Bineyame\AssetOpsV1-outA\gateway;C:\Users\assef\Bineyame\AssetOpsV1-outA\host;C:\Users\assef\Bineyame\AssetOpsV1-outA"
```

## Gates (from the spec)

- Acceptance criteria A.7 #1-#10.
- Per-unit review for A1 (shared seam); A2-A6 in the slice review.
- Validation: focused tests per unit, `tools/select-tests.py --base main` at slice end, one full backend run `-Tier fast` at merge (ruling A-Q15), full vitest, check-all.
- Golden/contract fixtures regenerated only through write flags, with the categories-stripped equality proof.
- Register rows R520-R528 in `.agent/mock-departure-register.md`.

USER_REVIEW_REQUIRED: false for merge (fresh independent review gates merge; owner sees it in the post-sprint walkthrough).

Review packet: `.agent/OUT-A-packet.md`.
