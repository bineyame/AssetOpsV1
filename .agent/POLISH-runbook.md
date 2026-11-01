# POLISH runbook (client-demo polish build)

Build: worktree `C:\Users\assef\Bineyame\AssetOpsV1-polC` (branch `task/POLISH-PC-final-gate`), work `var/polish_full`,
DB `assetops_polish_full_test`, private tree code `e413fc8c8` (main `06543e540` + the PC copy pass + Addendum 14), rebuilt 2026-11-01 18:29-18:50. Story day
**S = 2026-10-30**. Fallback: the DEMO-B build (`AssetOpsV1-demo3`, `var/demo3_full`, `assetops_demo3_full_test`,
S = 2026-10-29), runbook in `.agent/DEMO-B-packet.md`; never rebuild or edit it.

After a merge the build can be served from any main checkout that holds `var/polish_full` (the work folder is
untracked; the tree inside it carries its own backend). If a later merge changes backend or producers, rebuild (step 1).

## Steps (PowerShell; timings measured 2026-11-01 on this machine)

0. Environment, in every PowerShell window that runs Python:
   ```powershell
   cd C:\Users\assef\Bineyame\AssetOpsV1-polC
   $w="C:\Users\assef\Bineyame\AssetOpsV1-polC"; $env:PYTHONPATH="$w\backend;$w\contracts;$w\tools;$w\simulator;$w\gateway;$w\host;$w\field"
   $py="C:\Users\assef\Bineyame\AssetOpsV1-plan2\.venv\Scripts\python.exe"
   ```
1. **Prepare** (only to rebuild; it moves every date): `& $py tools/demo_combined.py --db assetops_polish_full_test --work var/polish_full prepare`
   - 1007-1254 s (last run: Kobo 854 s, cold 49 s, EV 86 s; cap 3120 s); self-check **17 pass, 0 fail, 0 skipped**.
   - The DB is guarded by the work folder's marker: prepare refuses a DB made from another worktree's `var/polish_full`.
     Run `drop` from the owning worktree first (PC did this for `AssetOpsV1-polA3`).
2. **Serve**: `& $py tools/demo_combined.py --db assetops_polish_full_test --work var/polish_full serve`
   - API answers on 8990 at once; first tick and the first `performance:` line about 7-15 s later; then one tick every
     120 s. Wait for the first `performance:` line before showing anything (STALE_PROJECTION before it).
3. **Frontend** (second window, from `frontend/`): `$env:ASSETOPS_API_PORT="8990"; npm.cmd run dev -- --port 5490 --strictPort`
   - Vite ready in 0.75-2.3 s.
4. **Links** (S = 2026-10-30; re-quote after every rebuild from `& $py tools/demo_combined.py --db assetops_polish_full_test --work var/polish_full links`):
   - Portfolio, week: `http://localhost:5490/portfolio?from=2026-10-24T00:00:00Z&to=2026-10-31T00:00:00Z`
   - Findings, week: `http://localhost:5490/findings?from=2026-10-24T00:00:00Z&to=2026-10-31T00:00:00Z` (`/findings/cost|risks|opportunities`)
   - Kobo trial-before S / trial-after S+1: `http://localhost:5490/sites/KOBO-001?date=2026-10-30` / `?date=2026-10-31`
     (other story days: 2026-10-02 normal, 10-09 overcast, 10-16 overuse, 10-20 missing, 10-23 overuse, 10-27 late, 10-29 normal)
   - Kobo ACT-001 verification: `http://localhost:5490/sites/KOBO-001/actions/79ade806-21a8-41ac-ad9d-664b36f8afd1/verification`
   - Kobo Finding: `http://localhost:5490/sites/KOBO-001/findings/f5795203-6bcf-49cb-b36b-478cee91002a?revision_id=2047529a-bc34-45ff-bd4e-986167a12454`
   - GreenHarvest failure night S: `http://localhost:5490/sites/COLD-LAB-001?from=2026-10-30T16:00:00Z&to=2026-10-30T17:05:00Z`
     (degraded S-3d `2026-10-27T16:00:00Z`-`17:05`; normal S-7d `2026-10-23T16:00:00Z`-`17:05`)
   - Depot fault S-3d: `http://localhost:5490/sites/EV-LAB-001/ev?from=2026-10-27T08:00:00Z&to=2026-10-27T09:00:00Z`
     (normal S-10d: `2026-10-20T08:00:00Z`-`09:00`)
   - Maintenance (must reach the build day, R629): `http://localhost:5490/maintenance/preventive?from=2026-10-02T00:00:00Z&to=2026-11-02T00:00:00Z`;
     Corrective `http://localhost:5490/maintenance?from=2026-10-02T00:00:00Z&to=2026-11-02T00:00:00Z`; WR-006 (Starter/control
     inspection, GreenHarvest) opens from it and shows the third-visit notice.
   - `serve`/`links` now print these route forms (PA-3 `story_links`); the DEMO-B P-01 hand corrections are no longer needed.
5. **P-08 line (D-3, R645):** "Depot: the follow-up Action is on Work › Actions; the fault-window board shows the warning
   and the plan." The Action is dated at build time, never backdated into the story window.
6. **Review mode** (MOCK DEVIATION labels, for the owner only): open `http://localhost:5490/?review=labels` once in the
   browser session; labels then show (for example R453 on the Kobo board at 390 px, R396/R363/R365 on WR-006). Client mode
   is the default.
7. **Captures** (optional, with 2-3 running; from the worktree; exits 1 if any capture is unsettled or, with STRICT, has a counted hit):
   ```powershell
   $env:DEMOB_STRICT="1"; node tools/demo-combined-evidence.mjs capture $w\var\polish_full <out>
   New-Item -ItemType Directory -Force <out>\mock | Out-Null
   node tools/measure-mock-panels.mjs --mock frontend/mockups/v70 <out>\mock ((node tools/demo-combined-evidence.mjs mock-ids) -split ' ')
   node tools/demo-combined-evidence.mjs compare <out> <out>\mock\mock-measure.json
   ```
   28 captures 308-361 s (open the Portfolio once first: on a cold serve its first read can outlast the settle wait, as the first Addendum 14 run showed); review-mode set (`DEMOB_REVIEW_LABELS=1 DEMOB_ONLY=wr-overview,kobo-board-S`) 64 s; mock 55 s.
8. **Stop:** Ctrl+C in each window, or `taskkill /PID <pid> /T /F` on the serve and npm PIDs (the serve tree holds
   uvicorn). Check ports 8990 and 5490 are free.
