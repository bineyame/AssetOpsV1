# Moving AssetOps work to the Ubuntu VPS (24 GB RAM, 8 vCPU)

Owner decision: `.agent/owner-vps-move-2026-11-11.md`. Cutover Thursday 12 Nov after the technical demo (~12:30). Tonight's rebuild and the demo stay on the laptop.

## What has to move

| Item | Laptop location | How it moves |
|---|---|---|
| Code, `main` | `C:\Users\assef\Bineyame\AssetOpsV1-plan2` (main) | `git push origin main` (owner-authorized for the move), VPS `git clone` |
| Unmerged branches in flight | 40+ worktrees, e.g. `task/ANY-2-AR3-AR6`, `task/ANY-2-AR4`, `task/PR-1-price-action`, `task/HON-1-complete-readings`, `task/OPEN-NOW-work-read`, `task/UQ-0-v72-sheet` (parked) | merge what is ACCEPTed before the cutover; the rest goes in `assetops-inflight.bundle` (`git bundle create ... <branches>`), copied over SSH, then `git fetch` from the bundle on the VPS |
| Uncommitted owner files on main | `.agent/owner-walkthrough-notes-2026-11-01.md`, `Docs/demo-sprint/implementation-logic-design-proposal.html` (never committed by agents) | copied as files (scp), not committed |
| Agent memory (rules, owner preferences) | `C:\Users\assef\.claude\projects\C--Users-assef-Bineyame-AssetOpsV1\memory\` | copy the folder into the VPS project's memory folder (`~/.claude/projects/<vps-project-path-slug>/memory/`); the VPS session reads `MEMORY.md` |
| Coordinator state | `.agent/coordinator-handoff.md` (+ all `.agent/` rulings, packets, owner files) | in git (main) |
| Demo database | `assetops_polish_client7_test` (tonight's build) or `client6` (fallback) in Docker `assetopsv1-postgres-1` (postgres:16.4-alpine) | `pg_dump -Fc` â†’ scp â†’ `pg_restore` into the VPS container â€” only the DB(s) still needed (not all 75 test DBs, 6.8 GB) |
| Demo work folder | `C:\Users\assef\Bineyame\AssetOpsV1-e3e\var\polish_client7` (frozen `tree`, `story.json`, `days.json`, logs) | tar â†’ scp; or simpler: run a fresh prepare on the VPS (it has the RAM for it) |
| Test template DBs | built by the test tooling | rebuilt on the VPS (do not copy) |

## VPS setup (one-time)

1. Packages (Ubuntu: apt; Docker from the official docker.com apt repo; Python 3.12 via deadsnakes PPA if the release lacks it; Node 24 via NodeSource; PowerShell 7 via the Microsoft apt repo): git, Docker + compose plugin, Python 3.12 (+ venv), Node 24 + npm, PowerShell 7 (`pwsh`, for `tools/check-all.ps1` / `check-architecture.ps1`), `postgresql-client` 16 (for pg_dump/pg_restore).
2. `git clone git@github.com:bineyame/AssetOpsV1.git ~/AssetOps` (deploy key or owner's key), `git fetch <bundle>` for in-flight branches.
3. `docker compose up -d` with the repo's `docker-compose.yml` (same image postgres:16.4-alpine, port 55432, credentials assetops/assetops-local-dev); set `max_connections=300` (D-E5.47).
4. Python venv: `python3.12 -m venv .venv && .venv/bin/pip install -r <the repo's requirements files>`; frontend: `npm ci` in `frontend/`.
5. Restore the demo DB if kept; otherwise run `tools/demo_combined.py --db <new> --work var/<new> prepare` (â‰ˆ2h45m on the laptop; likely faster on 8 vCPU).
6. Copy the memory folder; start Claude Code in `~/AssetOps`; first prompt: "read .agent/coordinator-handoff.md and .agent/vps-migration-plan.md and continue".

## Verification on the VPS before building resumes

- `pwsh tools/check-all.ps1 -Python .venv/bin/python` â†’ "All 18 guards passed." (the .ps1 tooling was written for Windows PowerShell 5.1 â€” expect a short portability fix round: paths, `\` separators, Windows-only cmdlets).
- A targeted backend test subset + one Postgres test file + vitest on one file.
- If a fresh prepare is run: self-check rows pass (same as the laptop build).

## Things that change for the coordinator and builders on Linux

- Shell: bash/pwsh instead of Windows PowerShell; scripts in scratchpad move to POSIX.
- Detached long jobs: `nohup`/`setsid` or `systemd-run --user` instead of `Start-Process` + the PowerShell watchdog; the memory watchdog thresholds can be relaxed (24 GB).
- Lane limits: with 24 GB and 8 vCPU, 4â€“5 lanes are realistic (re-check DB connections: max 300).
- Docker restarts: `docker restart assetopsv1-postgres-1` (no Docker Desktop).
- Paths in briefs: worktrees under `~/AssetOps-<name>`; `PYTHONPATH` built from the worktree root with `:` separators.
- Serving the demo app from the VPS needs either an SSH tunnel (`ssh -L 5490:localhost:5490 -L 8990:localhost:8990`) or a reverse proxy with auth â€” never expose the dev ports publicly.

## Cutover sequence (Thursday ~12:30, after the demo)

1. Pause all lanes; let running agents commit (or stop them; they re-start on the VPS from git).
2. Merge every ACCEPTed branch; run check-all on main; push `main`.
3. Bundle the remaining in-flight branches; copy bundle + memory folder + uncommitted owner files + (optional) demo DB dump to the VPS.
4. On the VPS: setup steps 1â€“6, verification, then resume the 17 Nov plan (revision 4 of `.agent/architect-sequence-client-scope-2026-11-11.md`) â€” first item: the EV-HB gate prepare (must be green by Fri 18:00).
