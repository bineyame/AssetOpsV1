# Final complete review: full 1,414-pair recapture (standing brief)

Owner request (2026-10-25): a complete review at the end to ensure everything checks out. This part recaptures **every pair** of the frozen post-W6 audit index (`.agent/post-W6-audit/audit-index.json`, 1,414 pairs in batches 01–19) at the final main SHA, after all 11 fix cards and the final-review fix round merged.

## Where
- Run from the main checkout `C:\Users\assef\Bineyame\AssetOpsV1-plan2` (branch `main`). Record the exact SHA (`git rev-parse HEAD`) at start; do not pull or merge mid-run.
- Evidence goes to `.agent/post-W6-final-recapture/batch-NN/` (never overwrite `.agent/post-W6-audit/`). Commit evidence on a branch `audit/final-recapture` created from that SHA in a separate worktree is NOT needed: write files in plan2's `.agent/` only; the coordinator commits.

## How
- Reuse each batch's own capture tools in `.agent/post-W6-audit/batch-NN/tools/` (and its `part-*` folders) and its producer/mode list from `batch-NN.json`. Wrappers stay capture-only (drive URLs, wait, screenshot, measure DOM). Copy tools into the new batch folder if they write to fixed paths; adjust only output paths, ports and DB names permitted below.
- For every indexed pair (screen ID, case, width): app screenshot + DOM measures (panel titles/order, per-panel closed heights, overflow, colours/fonts as the original ledger did); reuse the frozen mock screenshot (mocks did not change) unless the original tool re-renders it cheaply.
- Compare each pair to: (1) its frozen-audit differences and register rows (`.agent/mock-departure-register.md`, now reconciled: D3 rows closed with merge SHAs, standing D1/D2/D4 rows), and (2) the ruled caps (`.agent/post-W6-*-rulings.md`, `*caps*-rulings.md`). Classify each pair: **PASS** (matches mock or every difference is a standing registered D1/D2/D4/D5 row or a ruled cap), **FIXED** (a frozen D3 difference now gone), **REGRESSION/OPEN** (a D3-class difference present: closed row reappeared, new difference, cap exceeded, document overflow, clipped content, raw system vocabulary), or **GAP** (state no longer reachable by its unmodified producer; say why).
- Per batch write `batch-NN.json` (per pair: route, producer/mode, SHA, classification, measures, paths) and `batch-NN.md` (counts, every REGRESSION/OPEN with evidence paths and suspected cause, every GAP).

## Hard rules
- Edit NO product code. No seeding, fabricated data or bypassed refusals.
- DBs only in container `assetopsv1-postgres-1`: `*_test` DBs (e.g. `assetops_audit_bNN*_test`), producers' own `<prefix>_audit*` scratch DBs created/dropped by the producer's own modes, plus `w301cap_test`, `w302j_test`, `w402r_test`. Producers run UNMODIFIED, never with a guard- or name-rewriting wrapper. Never touch any other DB. If any action is refused by permissions: stop and report; never work around it.
- Memory is tight (16 GB): ONE heavy job at a time; ≥2 GB free before each producer/capture; never overlapping instances of a capture script (check before relaunch; start Vite via a PowerShell start script, not bare nohup). Use the batch's original port digit.
- Stop only PIDs you spawned, by PID. After each batch: stop servers/Vite/Chrome/`serve` processes, drop DBs, remove `var/` work folders.
- No vite build, full vitest or full backend suite.
- Near your context limit: finish the current batch, write its files, append progress to `.agent/post-W6-final-recapture/PROGRESS.md` (batches done, counts, open issues), and stop.
