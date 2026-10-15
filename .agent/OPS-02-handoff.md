# OPS-02 handoff (single phase, built; review next)

Landed on `task/OPS-02-writer-guard-ast` (from main `5bfff665`): `cacf9083` extractor + rule 8, `7fc6f35f` corpus,
`d2b89c14` L1, `a5eb86a6` closeout docs, `7c95c667` stable schedule message; packet `.agent/OPS-02-review-packet.md`.

Anchors:
- `tools/checks/sql_statements.py` `_HEAD` (clause heads), `Renderer.render`, `_core_clause`, `extract`.
- `tools/checks/configuration-persistence.ps1` rule 8: `$sqlWrite`/`$sqlTarget`/`$sqlDml`/`$sqlFragment`, the
  `$guardPython` lookup and `$sqlStatements` map, the per-clause `foreach ($statement in $moduleStatements)` loop,
  and the schedule-store block.
- `tools/writer_guard_probes.py` (`--seam` for the fast runner); `backend/tests/conftest.py`
  `refuse_template_opt_out_under_xdist`.

Next: one fresh independent review. Merge carries: whichever of LR-01 / S6-01a / S4-05a merges second adds its
tables to the rule-8 policy arrays; rerun `tools/writer_guard_probes.py` after any rule-8 edit.

Open risks: see packet "Residual risk" (file-loaded SQL, cross-statement assembly, Python now required by rule 8).
