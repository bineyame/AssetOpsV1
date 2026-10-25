# W6 verification captures: shared rules for every capture agent

Worktree `C:\Users\assef\Bineyame\AssetOpsV1-review8`, branch `task/post-W6-W6-global`, product SHA f3da6e90 (do not edit
product code, tests, producers or tools/; do not commit; the coordinator commits).

- Python: main venv `C:\Users\assef\Bineyame\AssetOpsV1\.venv\Scripts\python.exe` with
  PYTHONPATH="<wt>;<wt>/backend;<wt>/contracts;<wt>/gateway;<wt>/simulator;<wt>/host" (wt = the worktree above).
- Every API serve (plain uvicorn, W502/W504 serve): a fresh random `ASSETOPS_WORK_CURSOR_KEY_HEX` (64 hex) exported in the
  launching shell env. W502/W504 `env()` inherit it. No producer edits.
- DBs: only `*_test` names (your own unique tag, below) or the producers' own `<prefix>_audit*` modes. Check `pg_database`
  before creating; never touch DBs you did not create; drop all of yours at the end (producer `drop` or `DROP DATABASE`).
  Container `assetopsv1-postgres-1`. A permission refusal is recorded and reported, never worked around.
- Ports: another agent captures in `AssetOpsV1-review7` concurrently, and two sibling agents share this machine. Use ONLY
  your assigned ports. Check a port is free (Get-NetTCPConnection -State Listen) before binding. Stop every process you
  start by PID (record PIDs in your logs/pids.txt). Never kill a process you did not start.
- W502 cold walkthrough serve hard-codes ports 8971-8977 (shared by everyone). Before `serve`: confirm all seven free; if
  not, do other phases first and wait (Monitor with an until-loop, not sleep polling) until free. Hold them as briefly as
  possible: capture the cold phase, then stop the W502 serve processes immediately. Write `.agent/post-W6-W6-evidence/W502-LOCK`
  containing your agent name while you hold them and delete it after; respect the lock if a sibling holds it.
- Vite: `node node_modules/vite/bin/vite.js --port <yours> --strictPort --host 127.0.0.1` in `<wt>/frontend` with
  `ASSETOPS_API_PORT` set; restart per phase as the batch tools do. Headless Chrome on your own CDP port.
- `var/sites/*.yaml` are present in this worktree (copied). Batch 18 noted `var/sites/kobo-001.yaml` can be stale against
  the W6 import (`/api/sites` 503) and moved it aside for mini link-landing captures only, then restored it; do the same if
  needed and record it.
- Reuse the frozen batch tools (copy into your evidence folder, then change only roots/ports/revision/output paths):
  `.agent/post-W6-audit/batch-18/tools/*` and `.agent/post-W6-audit/batch-19/tools/*`. Mock = `frontend/mockups/v69/index.html`
  served by the same Vite, 1440x1000 and 390x900. The capture wrappers only navigate, wait, screenshot and measure.
- For every pair record: panel titles and order vs the frozen record (`batch-18.json` / `batch-19.json`), document horizontal
  overflow (scrollWidth > clientWidth), closed panel heights, console errors/warnings. Compare to the frozen run and list
  every changed title/order/overflow/console item; expected changes come from the W6 D3 fixes (see
  `.agent/post-W6-W6-rulings.md` and `.agent/post-W6-W6-handoff.md` "Visible labels").
- Context budget: never dump logs or JSON into context; filter to failures and summary lines; bounded reads only. Retry
  transient render misses once and keep the first run in logs/.
- Keep screenshots + evidence JSON + a compact `summary.json` in your folder. Do not write long narrative files.
