# OPS-02 fix round (Sonnet) - review M1, M2 (+ cheap Lows)

Work ONLY in worktree `C:\Users\assef\Bineyame\AssetOpsV1-review2`, branch `task/OPS-02-writer-guard-ast` (head `c7d6f9c0`). Review: `.agent/OPS-02-review.md`. Guards need Python: set `ASSETOPS_GUARD_PYTHON=C:\Users\assef\Bineyame\AssetOpsV1\.venv\Scripts\python.exe` (or a temporary `.venv` junction, removed afterwards). No full suite (guard-only change).

1. M1: rule 8 fails on clean code under a UTF-8 console (PowerShell 5.1 prefixes stdin with a BOM). Make the extractor robust: decode stdin as `utf-8-sig` and strip a BOM from each path, or pass paths via a temp file/arguments. Prove: `check-architecture.ps1` passes on the clean tree both from the PowerShell tool (code page 65001; `chcp 65001` in a cmd wrapper) and from Git Bash.
2. M2: treat any name imported from `sqlalchemy` (incl. `from sqlalchemy.dialects import postgresql`, `from sqlalchemy import sql`) as a namespace and resolve dotted calls (incl. fully dotted `sqlalchemy.dialects.postgresql.insert`) to their root verb. Add probes for `postgresql.insert`, `sql.delete` and the fully dotted form to `tools/writer_guard_probes.py`.
3. Cheap Lows if each is a few lines: L1 keyword alias in UPDATE (`UPDATE site AS copy SET`); L2 quote-aware comment stripping and `bytes` SQL strings; L3 case-insensitive half-built refusal and an accurate message for a complete statement. Add a probe per fix. Otherwise record them in the packet residuals.
4. Run the probe corpus with `--seam` (all pass) and `check-all.ps1` once from PowerShell.

Commit small; write `.agent/OPS-02-fix-handoff.md` (git add -f). Do not touch `.agent/coordinator-handoff.md` or `.agent/owner-autonomy-2026-10-15.md`. Report concisely.
