# post-W6 shell recapture: standing brief for each capture group

Worktree `C:\Users\assef\Bineyame\AssetOpsV1-review3`, branch `task/post-W6-shell`. Capture the CURRENT branch HEAD
(record `git rev-parse --short HEAD`). Rulings: `.agent/post-W6-shell-rulings.md` Q13, Q23, Q24, Q25.

## What to capture
`.agent/post-W6-shell-recapture/selection.json` lists 370 pairs (`batch, screen, case, width, route, producer,
frozen_app, tags`). Capture ONLY your group's batches, and only the selected `(screen, case)` pairs at both widths.
`frozen_app` (`batch-NN/<part>/...png`) names the frozen part folder, and so the producer mode and capture targets.

## How
- Read only what you need of the frozen batch: `.agent/post-W6-audit/batch-NN/batch-NN.md` (the "Frozen run" and
  producer sections), its `tools/` (or top-level) `capture-bNN.mjs`, the `targets-*.json` files, and the launch helpers.
  Run the SAME producers, unmodified, with the same modes. Build a filtered targets file holding only the selected cases.
- Reuse the batch's capture script, unchanged except that a filtered targets file is allowed. Do not add seeding,
  clicks or data. Default shell states need no click (Q25).
- Start Vite from THIS worktree's `frontend/` (current code), not from the frozen tree.
- Output to `.agent/post-W6-shell-recapture/batch-NN/<part>/`: screenshots plus the script's `evidence.json`
  (set `AUDIT_REVISION=<HEAD sha>`). Mock screenshots are optional; the frozen index already has them.
- Write `.agent/post-W6-shell-recapture/batch-NN/run.md` (at most 25 lines). Record the producer commands, DB names,
  ports, the SHA, the pair count captured against the count selected, and any case that could not be produced, with
  the reason (a capture gap; never fabricate).

## Hard rules (from `.agent/post-W6-audit/agent-brief.md`)
- Do not edit product code. Captures are capture-only. Data comes only from reviewed producer modes.
- DBs live only in container `assetopsv1-postgres-1`. You may create and drop `assetops_shellrc_bNN*_test`, and a
  producer's own prefix plus an `_audit` suffix, created and dropped only by that producer's own modes.
- Check `pg_database` first. If the producer's `_audit` DB exists, another agent owns it: wait, or use a
  `--db`-style `_test` name where the producer accepts one. Never touch any other DB. Drop your DBs when done.
- Ports:
  - API 18101-18107, Vite 5181, CDP 9521. Pass `ASSETOPS_CDP_PORT=9521`.
  - 18108-18109 are reserved for the DTO proof agent.
  - Where a producer hard-codes its own ports, first check them free with `netstat -ano | grep LISTEN`.
  - Another agent uses 189xx, 5189 and 8971-8977: never use those. If the w502 producer's 8971-8977 are busy, wait,
    or use its documented port override.
- Stop only the PIDs you spawned, by PID, and never by name. Before finishing, confirm none of your ports still listen.
- Do not run full vitest, `vite build` or backend suites.
- Do not commit. The coordinator commits.
- Be token-efficient: bounded reads, and trimmed logs written to files.
