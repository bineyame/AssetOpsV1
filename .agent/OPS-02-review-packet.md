# OPS-02 review packet - statement-level product writer guard

Task: `tasks/OPS-02-writer-guard-ast.md` (size S, non-UI, USER_REVIEW_REQUIRED false). Branch
`task/OPS-02-writer-guard-ast` from main `5bfff665`; review range `git diff 66f1e192..HEAD`.

## Outcome delivered

Rule 8 now applies its unchanged writer policy to SQL statements extracted from the Python AST rather than to
source lines. All 11 forms that `.agent/S4-02d-phase-2-review.md` F-B recorded as missed now fail
`tools/check-architecture.ps1` for the correct ownership reason. A two-line `UPDATE <table> ... SET` is checked
for every writer (S4-05a phase-1 review L1). OPS-01 L1 also landed: `ASSETOPS_TEST_TEMPLATE=0` under pytest-xdist
is now a usage error raised before any routing.

## Files materially changed

- `tools/checks/sql_statements.py` (new): the table-agnostic AST extractor. It renders whole string expressions
  (implicit concatenation, triple quotes, escapes; `+`/f-string/`%`/`.format`/`join` with dynamic parts as
  `{?}`), strips SQL comments, splits text into clauses at write heads, synthesises SQLAlchemy Core
  insert/update/delete into SQL, and skips docstrings. A parse or read error exits 2.
- `tools/checks/configuration-persistence.ps1` rule 8: the interpreter lookup (fails hard), the extractor call,
  and a per-clause loop. The per-writer and reverse-ownership blocks are textually unchanged (`$line` = clause).
  New global refusals cover MERGE/COPY, a non-literal DML target and a dangling write head. The schedule store
  also refuses `merge`/`copy`/`THEN UPDATE|DELETE`, accepts an optional UPDATE alias, and words its "one line"
  rule as "one statement". The driver-import check stays line-based.
- `tools/check-all.ps1`: passes `-Python` to the guard as `ASSETOPS_GUARD_PYTHON`.
- `tools/writer_guard_probes.py` (new): the named, automated mutation corpus (38 negatives and one controls run).
- `backend/tests/conftest.py` `refuse_template_opt_out_under_xdist`; `backend/tests/test_pg_harness.py`, with
  4 new cases.

## Acceptance criteria

1. Statement parsing, fail closed, path:line attribution. **Met.** An unresolved target (f-string, `%`, `.format`,
   dynamic Core table) fails with "names its target table literally". A `{?}` SET list fails the schedule rule.
   MERGE/COPY are refused everywhere. Upserts stay refused in the schedule store, and other writers keep their
   existing insert/update allowlists. Imports are not blanket-allowed (the driver rule is unchanged). Each
   failure names `path:line`, where the line is the start of the Python expression.
2. 11 forms as separate negative mutations through `check-architecture.ps1`. **Met: 11/11 CAUGHT** with the
   default runner (9 min 31 s), and the controls run was ALLOWED. The full corpus with `--seam`: **38/38 CAUGHT
   + controls ALLOWED**, tree restored. The corpus includes a split UPDATE for each of the 8 writers and reverse
   ownership for the finding, assessment, access, assumption, consequence, schedule and consequence-work tables.
   The ledger check is "Foundation must not write ledger table". Controls cover triple-quoted multiline,
   lowercase, mixed case, alias, `FOR UPDATE OF h SKIP LOCKED` read, a `'update'` literal, `ON CONFLICT DO
   NOTHING`, a comment and a docstring. On unmutated main code `check-architecture.ps1` passes.
   Non-vacuity: removing the driver imports still yields "found no SQL write or driver import". A missing
   interpreter yields "cannot run its SQL statement extractor ... never skips" (exit 1).
   Phase-1 probes (`.agent/S4-02d-phase-1-probes.py guard`): **19/20 CAUGHT**; see Known deviations for
   `split update`. `delete`, `upsert` and `F1 lowercase delete` were rerun after the message fix (7c95c667).
3. L1. **Met.** `ASSETOPS_TEST_TEMPLATE=0 pytest -n 2 tests/test_pg_harness.py` gives `ERROR: ... cannot be
   combined with pytest-xdist` with exit 4. The serial opt-out still runs (14 passed, 3 skipped without a DB
   URL). The focused test makes no Postgres contact. Non-vacuity: disabling the raise makes 2 tests fail; the
   tree was then restored.

## Checks run

- `tools/check-architecture.ps1`: passed (clean tree, .venv junction to the main venv).
- `tools/check-agent-workflow.ps1`: passed.
- `tools/check-all.ps1`: All 9 guards passed (`.venv` junction to the main venv, removed afterwards).
- Full backend suite (revision `7c95c667`, the final code revision; later commits are docs only), from
  PowerShell with keep-awake: `pytest backend/tests -n 2 --dist loadfile --no-loadscope-reorder -q
  --junitxml=<scratch>/ops02-junit.xml`, real Postgres `127.0.0.1:55432/assetops_test`, wall time 510 s. JUnit:
  cases=2141, skipped=0, failed=1. The failure was `test_runs_api.py::TestTheShippedFuelLossEventAgainstAPropertylessFoundation::test_the_shipped_scenario_blocks_only_on_the_values_this_site_lacks`:
  `FileNotFoundError` for the gitignored `var/sites/mg-001.yaml`, an environment precondition of this worktree
  that the brief anticipated. After the main checkout's `var/sites/*.yaml` were copied in, the file was rerun:
  `test_runs_api.py` JUnit cases=28, skipped=0, failed=0. The copy was then removed. No run-owned `_pt` databases
  remain.

## Known deviations

- The phase-1 probe `split update` (an implicit-concatenation UPDATE of **allowed** schedule columns) is now
  correctly allowed. The old line rule refused every multi-line UPDATE because it could not see the columns.
  The statement guard checks them, and `F-B 2` proves that a split UPDATE of an unlisted column still fails.
  The phase-1 script was not edited (it is history).
- The schedule store's refusal message keeps its phase-1 prefix and appends "(nor merges or copies)".

## Residual risk

- SQL read from `.sql` files, or assembled across several statements, is not resolved beyond the dangling-head
  rule (`sql = "UPDATE site"; sql += ...` is caught). A head split across variables mid-keyword is not caught.
- The Core detection covers verbs imported from sqlalchemy, `sa.` attributes, and zero-argument
  `<x>.insert/update/delete()` in modules importing sqlalchemy. ORM session writes (`session.add`) are not
  modelled; no backend module uses the ORM.
- Rule 8 now needs Python. `check-architecture.ps1` alone uses the repository `.venv` or
  `ASSETOPS_GUARD_PYTHON`, and fails without them.
- LR-01 `source_clock_attestation`, S6-01a Action tables and S4-05a provenance tables: whichever merges second
  adds them to the rule-8 policy arrays; no extractor change is needed.

## User-review focus

None (USER_REVIEW_REQUIRED false). Reviewer focus: the new global refusals, and whether the clause split misses
a write head (`_HEAD` in `sql_statements.py`).

## Merge with main (2026-10-16)

Status: done, pending merge (review ACCEPT after fix round). `git merge main` (`0d3114a3`) at `d8789adb`; guard and
probe follow-up `48327c21`.

- Rule 8 (`tools/checks/configuration-persistence.ps1`) keeps OPS-02's statement loop and carries main's policy: nine
  writers (`$actionWriter` in `$pgWriters`, write/driver non-vacuity), LR-01 `source_clock_attestation` in
  `$assessTables` (insert-only, reverse ownership), S6-01a Action tables (insert-only, reverse ownership), S4-05a
  provenance (ledger INSERT with VALUES and no ON CONFLICT, reverse ownership, ledger DO UPDATE / non-arbiter
  ON CONFLICT / DDL refusals, provenance-insert non-vacuity, HTTP designation scan).
- S4-05a's split/qualified/quoted provenance verb refusal and S6-01a's Action every-line refusal now run twice: on
  source lines in the driver loop (their pre-OPS-02 form, including the verb-ending-a-line case) and on each extracted
  clause. Kept on lines so no form regresses; the clause form adds concatenated, comment-split and Core forms.
- New (tightening): an INSERT into an insert-only table (attestation, Action, provenance) carrying `DO UPDATE` is
  refused. No backend module upserts today. Messages that said "one statement per line" now say "one literal
  statement".
- Docs conflicts (ACTIVE_CONTEXT, CODE_STATE, tasks/README) kept both sides.

Evidence (revision `48327c21`; later commits are docs only):

- `python tools/writer_guard_probes.py --seam` (main venv interpreter): 68 CAUGHT, 0 MISSED; 4 controls ALLOWED
  (`controls` plus one multiline insert each for attestation, Action, provenance with an allowed arbiter); tree
  restored. 24 new probes: attestation/Action/provenance UPDATE, DELETE, TRUNCATE, upsert, split, schema-qualified
  and quoted forms, Core forms, an unlisted provenance arbiter, and reverse-ownership writes from another module.
- `tools/check-architecture.ps1` on the clean tree: passed under a UTF-8 console (`cmd /c "chcp 65001 & powershell
  ..."`) and from Git Bash (`ASSETOPS_GUARD_PYTHON` = main venv).
- Full backend suite from PowerShell with keep-awake, `var/sites/*.yaml` copied in temporarily (removed after),
  `PYTHONPATH` = this worktree's `backend;contracts;gateway;simulator`: `pytest backend/tests -n 2 --dist loadfile
  --no-loadscope-reorder -q --junitxml=<scratch>/ops02-merge-junit.xml`, real Postgres
  `127.0.0.1:55432/assetops_test`, wall 685 s (cap 20 min). `2372 passed`; JUnit cases=2372, skipped=0, failed=0.
- `tools/check-all.ps1` (temporary `.venv` junction, removed after): All 9 guards passed.
