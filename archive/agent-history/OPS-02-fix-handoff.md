# OPS-02 fix round handoff (review M1, M2, L1-L3)

Code commit: see `git log` (one commit "OPS-02 fix round ..."). Files: `tools/checks/sql_statements.py`,
`tools/checks/configuration-persistence.ps1` (fragment pattern/message only), `tools/writer_guard_probes.py`.

- M1: extractor reads `sys.stdin.buffer`, decodes `utf-8-sig`, strips a BOM from each path. `check-architecture.ps1`
  passes on the clean tree from Git Bash and under `cmd /c "chcp 65001 & powershell -File ..."`.
- M2: every name imported from `sqlalchemy[.x]` that is not a verb or table constructor is a namespace; dotted
  chains resolve to their root (`_root`), so `postgresql.insert`, `sql.delete`, `sqlalchemy.dialects.postgresql.insert`
  are refused. 3 probes.
- L1: `AS` lookbehind on write heads (`UPDATE site AS copy SET` stays one clause). Probe. Unaliased `UPDATE site copy SET`
  remains a residual.
- L2: comment stripping skips `'..'`, `".."`, `$$..$$`; bytes constants render as latin-1. 2 probes.
- L3: `$sqlFragment` is case-insensitive (UPDATE needs a target token so a bare "update" string is not flagged); message
  now "ends before its SET, VALUES or WHERE clause". Probe; the old fragment probe expectation was updated.

Checks: `writer_guard_probes.py --seam`: 45 CAUGHT, controls ALLOWED, tree restored. `check-all.ps1` from the PowerShell
tool (UTF-8 console) with a temporary `.venv` junction: All 9 guards passed (junction removed). Note: check-all does not
forward ASSETOPS_GUARD_PYTHON to the screen ledger check (needs `.venv`); pre-existing, not changed.
Residuals: `UPDATE x copy SET` (alias without AS); `;` inside a quoted literal still splits statements.
