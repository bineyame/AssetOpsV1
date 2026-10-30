# OPS-check-all-no-bypass packet

Owner approval: .agent/owner-checkall-no-bypass-2026-10-30.md ("go with your suggestion").

## Changes
- New `tools/checks/check-navigation-truthfulness.ps1` (same logic, messages, exit codes as the former inline script; resolves repo root itself).
- `tools/check-all.ps1`: inline script and base64 launch removed; all PowerShell guards run as child `powershell -NoProfile -File ...` with no policy override. PASS/FAIL report, count and exit code unchanged.
- Docs: `backend/TESTING.md`, `.ai/ROLE_CONFIG.md` (new short section). No tools/README exists.

## Overrides removed
- tools/check-all.ps1 header comment (line 10) and Invoke-Guard calls for Architecture seams, Navigation truthfulness (EncodedCommand), Agent workflow.
- tools/checks/test_estate_guard.py:49
- tools/writer_guard_probes.py:1022 and :1024

## Proof
See final report (nav guard direct run, check-all 11/11, planted failure, grep).
