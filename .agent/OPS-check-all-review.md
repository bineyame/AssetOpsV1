# OPS-check-all-no-bypass review (fresh Claude reviewer, 2026-10-30)

Branch `task/OPS-check-all-no-bypass`, head 4c45e2c9, diff `main...HEAD` (7 files).

## Verdict: REVISE (docs only)

The code change is correct and I would accept it as is. The docs are not yet accurate: one Medium and one Low finding, both documentation, both fixable on the branch.

## Code verification

- `tools/check-navigation-truthfulness.ps1` matches the removed inline script line for line: same dot-sources, same `Invoke-NavigationTruthfulnessCheck`, same `- <failure>` output, `exit 1` on failure, and the same pass message. The only additions are `Push-Location` to `Split-Path -Parent $PSScriptRoot` and a `finally` `Pop-Location`. Repo-root resolution works: I ran it with the current directory set to `$env:TEMP` and it passed.
- Placing the runner at `tools/` rather than `tools/checks/` is right. `check-architecture.ps1` fails on any unregistered `.ps1` in `tools/checks/` (lines 47-61).
- In `check-all.ps1`, three `Invoke-Guard` calls lose only `-ExecutionPolicy Bypass`, and the base64 `-EncodedCommand` is replaced by `-File`. The guard list, order, names, PASS/FAIL report, count and exit codes are unchanged.
- `tools/checks/test_estate_guard.py:49` and `tools/writer_guard_probes.py:1022,1024` only drop the two policy arguments. The scripts, assertions and env are unchanged, so no guard was weakened.
- `git grep -n ExecutionPolicy -- tools/` returns only `tools/check-all.ps1:13`, the rule comment.

## Checks run (ASSETOPS_GUARD_PYTHON = plan2 .venv python, PYTHONPATH = worktree backend, no policy flag)

- `powershell -NoProfile -File tools\check-navigation-truthfulness.ps1` run from `%TEMP%`: "Navigation truthfulness check passed.", exit 0.
- `tools\check-architecture.ps1`: "Architecture check passed.", exit 0.
- `tools\check-agent-workflow.ps1`: "Agent workflow check passed.", exit 0.
- `tools\check-all.ps1 -Python <plan2 python>`: 11/11 PASS, "All 11 guards passed.", exit 0. This used a temporary junction `frontend/node_modules` to plan2's copy, removed afterwards (plan2's copy is intact).
- Planted failure `frontend/src/zzReviewPlant.ts` containing `"/site-configuration"`. The direct nav guard exited 1 with the parameterless-destination message. check-all failed Architecture seams and Navigation truthfulness, printed "Check failed: 2 of 11 guards.", and exited 1. The plant was removed, and `git status` is clean apart from this file.
- No test suite, Docker or browser was run.

## Findings

**M1 (Medium, docs). The live docs still instruct the override, and the new docs omit the precondition.**
- `README.md:150-154, 277, 291-292` still give `-ExecutionPolicy Bypass` as the guard commands. They also explain that this is because plain `.ps1` runs fail under Restricted or RemoteSigned.
- `.claude/agents/assetops-reviewer.md:38-39`, the standing Reviewer brief agents follow, also still gives `-ExecutionPolicy Bypass`.
- Both contradict the new rule at `.ai/ROLE_CONFIG.md:647` ("No agent, script or doc may add `-ExecutionPolicy`"). The packet's "No tools/README exists" missed the root README.
- I also checked the precondition. This harness's shell inherits `PSExecutionPolicyPreference=Bypass` from the environment. With that variable removed, the effective policy is `Restricted` (every scope Undefined). Under it, `powershell -NoProfile -File tools\check-navigation-truthfulness.ps1` fails with "running scripts is disabled on this system", exit 1. The documented commands in `backend/TESTING.md:37-40` and `.ai/ROLE_CONFIG.md:647` therefore work only where something already sets an allowing policy. The failure is closed (non-zero exit), never a false pass.
- **Fix:**
  - Replace the Bypass forms in `README.md` and `assetops-reviewer.md`, and list `tools\check-navigation-truthfulness.ps1` among the individually runnable guards.
  - State the precondition in README, TESTING.md and ROLE_CONFIG. For example: guards need an execution policy that allows local scripts (the agent harness provides one; on a plain shell, the owner sets the CurrentUser policy once). Without it, the guards fail rather than pass.

**L1 (Low, docs).** `tasks/OPS-03-suite-in-container.md:9`, `tasks/G-01-...md:24` and `tasks/G-02-...md:24` still quote the Bypass form. These are completed task definitions and history, so a one-line note is enough, or leave them as they are. This does not block.

## Residual risk

- If a future harness or CI environment does not inherit an allowing policy, every PowerShell guard fails. This is intended fail-closed behaviour, but it will look like a broken guard unless M1's precondition text is in place.
- `check-all` children inherit the parent's process policy through the environment, so the parent and its children always run under the same policy.

## Coordinator verification of fix round 1 (177b8acd), 2026-10-30: ACCEPT
- M1 closed. README and the reviewer brief now give plain commands, the navigation guard is listed, and the policy-precondition note appears in README, TESTING.md and ROLE_CONFIG.
- L1 closed. The historical notes sit under the three quotes.
- The remaining `ExecutionPolicy` hits are the rule statement, history and archive only.
- The diff is docs only.
