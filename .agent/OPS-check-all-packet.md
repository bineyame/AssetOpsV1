# OPS-check-all-no-bypass packet

Owner approval: .agent/owner-checkall-no-bypass-2026-10-30.md ("go with your suggestion").

## Changes
- New `tools/check-navigation-truthfulness.ps1` (same logic, messages, exit codes as the former inline script; resolves repo root itself).
- `tools/check-all.ps1`: inline script and base64 launch removed; all PowerShell guards run as child `powershell -NoProfile -File ...` with no policy override. PASS/FAIL report, count and exit code unchanged.
- Docs: `backend/TESTING.md`, `.ai/ROLE_CONFIG.md` (new short section). No tools/README exists.

## Overrides removed
- tools/check-all.ps1 header comment (line 10) and Invoke-Guard calls for Architecture seams, Navigation truthfulness (EncodedCommand), Agent workflow.
- tools/checks/test_estate_guard.py:49
- tools/writer_guard_probes.py:1022 and :1024

## Proof
See final report (nav guard direct run, check-all 11/11, planted failure, grep).

## Deviation
The runner is `tools/check-navigation-truthfulness.ps1`, not `tools/checks/...`: check-architecture requires every .ps1 in tools/checks/ to be a registered module, so a runner there fails the Architecture guard (seen on first run).

## Proof (env: ASSETOPS_GUARD_PYTHON=plan2 .venv python, PYTHONPATH=<worktree>/backend)
- Direct nav guard: "Navigation truthfulness check passed."
- check-all: 11/11 PASS, same guard list, "All 11 guards passed.", exit 0. (Worktree needed a temporary junction frontend/node_modules -> plan2's, removed afterwards.)
- Planted `"/site-details"` in frontend/src/zzPlanted.ts: Architecture seams and Navigation truthfulness FAIL, "Check failed: 2 of 11 guards.", exit 1. File removed.
- `grep -rn ExecutionPolicy tools/`: only the rule comment in check-all.ps1.
