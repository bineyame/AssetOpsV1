# S4-05b phase 2 - implementer brief

Work ONLY in worktree `C:\Users\assef\Bineyame\AssetOpsV1-review2`, branch `task/S4-05b-producers-reads-walkthrough` (main merged in). Same environment as `.agent/S4-05b-phase-1-brief.md` (venv junction, PYTHONPATH, private `assetops_s405*` DBs, keep-awake running, memory tight: focused tests `-n 2` at most until the final full suite; ports API 8935 / web 5435).

Read: packet phase 2, `.agent/S4-05b-phase-1-handoff.md`, and the new ruling `D-2026-10-16-s405b-label` (`.agent/architect-S4-05b-answers.md`). A fresh phase-1 review is running in parallel; the coordinator will forward any High/Medium findings to you, fold them in when they arrive.

Build phase 2 as the packet defines it, plus the ruling:
- Interim labels and statements exactly as the ruling's table (Prepared example data / Generated test data / Sources do not agree / Source unverified), visible without opening a disclosure (also at narrow width and to assistive technology); per-record IDs, publications, reasons in the existing deeper source disclosure, in plain language; no vocabulary exemption; test populated positive, mixed and unknown states with the product vocabulary scan.
- MIXED/UNKNOWN blocks a current amount (`MIXED_OR_UNKNOWN_SOURCE`) in Finding Financials, consequence and the S5 Overview, regardless of CURRENT PRICED or LR eligibility; historical amounts stay audit-only with their own source state. Move the S5 Overview read off `demonstration_label.py` and update `tools/s5_overview_walkthrough.py`, S5 tests and `tools/s402b-fuel-cost-evidence.mjs`.
- Actions: remove `demonstration_label.py` runtime use from `actions/service.py`; recommendation and Action detail get source state from the stored resolver for the exact pinned origin FindingRevision; unresolved shows Source unverified. Note S6-02a (unmerged) also edits `actions/`; keep the change narrow.
- Partly sealed Lab stage: keep the fail-closed refusal, visible in Lab, with a regression test.
- The schedule-install gate update, `tools/s405_provenance_walkthrough.py` (prepare|serve|links|drop) and owner steps `.agent/S4-05b-owner-walkthrough.md` written for a non-developer (exact commands, ports, URLs, what to look for), layout evidence at 1440/390.

Final revision: `tools/check-all.ps1`, registry checker, `npx.cmd tsc --noEmit`, `npm.cmd test`, and ONE full backend suite from PowerShell (`pytest backend/tests -n 2 --dist loadfile --no-loadscope-reorder -q --junitxml=<absolute path>`, cap 25 min, zero failed/skipped; copy `var/sites/*.yaml` from the main checkout first, remove afterwards).

Owner direction: demo speed over perfection; final wording is the owner's W1 copy checkpoint. Commit in logical steps; do not merge; do not touch `.agent/coordinator-handoff.md`. Write `.agent/S4-05b-review-packet.md` and `.agent/S4-05b-phase-2-handoff.md` (git add -f). Report concisely.
