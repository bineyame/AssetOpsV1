# OPS-02 independent review - statement-level writer guard + OPS-01 L1

Reviewer: fresh Claude reviewer (did not author the slice). Worktree `AssetOpsV1-review2`, branch
`task/OPS-02-writer-guard-ast` at `8eefb190`, diff `66f1e192..8eefb190`. Inputs: `tasks/OPS-02-writer-guard-ast.md`
(incl. coordinator note), `.agent/small-followons-plan-review.md`, `.agent/S4-02d-phase-2-review.md` F-B,
`.agent/OPS-02-review-packet.md`, `.agent/OPS-02-handoff.md`.

## Verdict

**Accept with findings fixed on the branch** (M1, M2). Both are small and local to `tools/checks/sql_statements.py`
(plus a probe each). The design is right: an AST extractor feeding the unchanged rule-8 policy tables, with every
existing writer/table/column boundary and the non-vacuity checks preserved, fails closed when Python is absent or
extraction fails, and closes all 11 F-B forms. L1 is correct and non-vacuous. The Lows can ride the same fix round
or go to the backlog.

## Findings

### M1 (Medium, acceptance gap: guard broken in a UTF-8 console) - extractor reads a BOM as part of the first path

`tools/checks/configuration-persistence.ps1:718` pipes the module list to Python
(`($extractorInput -join "`n") | & $guardPython ...`); `tools/checks/sql_statements.py:453-458` reads
`sys.stdin` and opens each line as a path. When the console code page is 65001 (UTF-8), Windows PowerShell 5.1
prefixes the native-stdin stream with a UTF-8 BOM even though `$OutputEncoding` reports US-ASCII. Reproduced:

- From this session's PowerShell tool: `check-architecture.ps1` fails with
  `sql_statements: cannot read ﻿backend/assetops_backend/analytics_api.py` and
  `Rule 8 SQL statement extractor failed (exit 2)`.
- Minimal repro: `cmd /c "chcp 65001 & powershell -File enc.ps1"` where `enc.ps1` pipes `"abc"` to Python
  gives `b'\xef\xbb\xbfabc\r\n'`; with `chcp 437` it gives `b'abc\r\n'`.
- The same `check-architecture.ps1` from Git Bash (code page 437) passes.

It fails closed, so it is not a soundness hole, but it means `check-architecture.ps1` and `check-all.ps1` fail on a
clean tree for anyone whose console is UTF-8 (Windows Terminal with the UTF-8 option, `chcp 65001`, and this
project's own PowerShell agent tool). A gate that fails on clean code in the coordinator's default shell will be
bypassed or "fixed" carelessly. Fix: read `sys.stdin.buffer` and decode as `utf-8-sig` (and/or `lstrip("﻿")`
each path), or pass the list via a temp file / arguments instead of stdin. Add a probe or note that runs the guard
under `chcp 65001`.

### M2 (Medium, acceptance gap: Core mutation not refused) - module-bound SQLAlchemy verbs are invisible

`_sqlalchemy_names` (`sql_statements.py:337-354`) records verbs only from `from sqlalchemy... import insert/update/
delete` and modules only from `import sqlalchemy[...] [as x]`. A module bound by `from sqlalchemy.dialects import
postgresql` (the documented idiom for `postgresql.insert(...).on_conflict_do_update`), `from sqlalchemy import sql`
(`sql.delete(...)`), or a dotted call `sqlalchemy.dialects.postgresql.insert(...)` is neither recognised nor refused.
Reproduced through the seam runner by appending to the Finding store (insert-only to its own tables):

```python
from sqlalchemy.dialects import postgresql
from sqlalchemy import table
_R = postgresql.insert(table("site")).values(id=1)
```

Rule 8 passes. The packet's acceptance item 1 requires refusing a "SQLAlchemy Core mutation that cannot be safely
assigned to an allowed table/column", and Core insert/update/delete is one of the F-B families (forms 9-10); this is
the same miss with a different import spelling, silently, inside a writer that may import sqlalchemy. No backend
module uses Core today (all writers use `text()`), so this is latent, not live. Fix: treat any name bound by a
`from sqlalchemy[.x] import y` that is not a verb or table constructor as a sqlalchemy namespace, and resolve an
Attribute call's root `Name` through dotted chains (`a.b.c.insert(...)` with `a` in modules); add one probe for
`postgresql.insert` and one for `sql.delete`.

### L1 (Low) - a keyword alias between UPDATE and SET splits the clause and hides the write

`_HEAD` (`sql_statements.py:262-264`) splits at any head word not preceded by `[\w.]`/DO/THEN/FOR/KEY.
`"UPDATE site AS copy SET lifecycle = :l WHERE id = :i"` (COPY, UPDATE, DELETE, ALTER, DROP, MERGE are unreserved
in PostgreSQL and valid as aliases after `AS`) becomes `UPDATE site AS` + `copy SET ...`; neither matches
`$sqlWrite` or `$sqlFragment`. Reproduced: passes rule 8 in the Finding store. The old line guard also missed every
aliased UPDATE outside the schedule store, so this is not a regression, and an accidental keyword alias is unlikely.
Fix: only split at heads in statement position (clause start, after `(`, `)` or `;`), or treat an `UPDATE` clause
without `SET` that has more than one token as a fragment.

### L2 (Low, regression vs the line guard) - the SQL normaliser is not quote-aware; bytes literals are not rendered

- `normalize` strips `--` and `/* */` inside SQL string literals. `"SELECT '--' AS x; DELETE FROM site WHERE id = 1"`
  loses the DELETE (the `--` comment eats the rest of the line). Reproduced: passes rule 8 in the Finding store.
  The old line guard caught it.
- `Renderer.render` only handles `str` constants. `b"DELETE FROM site WHERE id = 1"` (psycopg accepts `bytes`
  queries) is invisible. Reproduced: passes. The old line guard caught it.
Both are contrived. Fix: strip comments with a small tokenizer that skips `'...'`/`"..."`/`$$...$$`, and render
`bytes` constants decoded as latin-1.

### L3 (Low) - the dangling-head refusal is case-narrow and its message can mislead

`$sqlFragment` (`configuration-persistence.ps1:701`) is case-sensitive and omits lowercase `update` (deliberately,
to avoid prose). `"update site"` then `+= " set ..."` passes in a writer (reproduced). This is within the packet's
stated residual (multi-statement builds), but the residual should name it. Separately, a complete single statement
`DELETE FROM site` (no WHERE) also matches the fragment pattern and is reported as "assembled in one expression"
alongside the real reason; harmless but confusing.

No false positives on main from the `sql +=` refusal: the clean tree passes (`check-architecture.ps1` from Git Bash).

## Questions the dispatch asked

- **Extractor soundness.** Implicit concatenation, triple quotes, escaped newlines, SQL comments, f-strings,
  `%`, `.format`, list `join` and `+` with names (rendered `{?}` and refused as non-literal targets), CTE clause
  splitting, MERGE `THEN UPDATE` kept in-clause, row locks not treated as writes, docstrings skipped, Core verbs
  imported directly or aliased (`insert as pg_insert`) and `sa.` attributes: all verified by direct `extract()` calls
  and probes. Gaps: M2, L1, L2, L3.
- **Fail closed.** Missing interpreter -> explicit failure (code read, `:712-714`); non-zero extractor exit ->
  failure (`:719-720`, and observed live under M1); non-vacuity gated on `$extractorRan` so it is not double-reported.
  Parse/read errors exit 2. Good.
- **Boundaries preserved.** The per-writer and reverse-ownership blocks are textually unchanged apart from `$line`
  now being a clause; `$sqlTarget` gained `ONLY`/schema/quote handling; driver-import rule unchanged and still
  line-based. Sample corpus run below; all caught.
- **Known deviation (`split update` of allowed schedule columns now accepted).** Acceptable. The old refusal was a
  proxy for "the guard cannot see the columns"; the statement guard now checks each column, and `F-B 2` proves an
  unlisted column in a split UPDATE still fails.
- **Runtime.** The extractor over all backend modules takes ~2 s wall (91 clauses, 30 KB JSON). The line loop now runs
  only the driver regex per line. The added cost to `check-all.ps1` is a few seconds; acceptable.
- **Residuals.** `.sql` files: only `backend/db/init/01-test-database.sql` exists and is outside rule 8's scope
  (`backend/assetops_backend/`), as before. Multi-statement builds and ORM: stated; add L3's lowercase case.
- **OPS-01 L1.** Correct: `refuse_template_opt_out_under_xdist` is the first statement of `pytest_configure`, before
  any `route()`/run-id, and checks both controller and worker. Semantics match `pg_harness` (`== "0"`). Live CLI
  check reproduced (exit 4, clear message); serial opt-out still runs. The packet's non-vacuity claim (disabling the
  raise fails 2 tests) is plausible from the test code; not rerun.

## Checks run (this worktree, `8eefb190`)

| Check | Result |
| --- | --- |
| `tools/check-architecture.ps1` from the PowerShell tool (UTF-8 console) | **FAILED**: rule-8 extractor exit 2 on BOM (M1) |
| `tools/check-architecture.ps1` from Git Bash (`ASSETOPS_GUARD_PYTHON` = main venv) | passed |
| `tools/check-agent-workflow.ps1` | passed |
| `sql_statements.py` alone over `backend/assetops_backend` | ~2 s, 91 clauses |
| `writer_guard_probes.py --seam` sample: F-B 1, 3, 6, 8, 9, 10, split finding, split assumption, reverse schedule, dynamic set list, fragment, core aliased postgres insert, cte delete, controls | 13/13 CAUGHT, controls ALLOWED, tree restored (2 min 8 s) |
| `writer_guard_probes.py` (full `check-architecture.ps1` runner): F-B 4, 7, 11 | 3/3 CAUGHT, tree restored (2 min 13 s; launched from Git Bash) |
| Reviewer mutations (seam, Finding store): keyword alias, `postgresql.insert`, bytes, quoted `--`, lowercase fragment | all PASSED the guard (M2, L1-L3); control (bare multi-line delete in `tick.py`) REFUSED |
| `pytest tests/test_pg_harness.py -q` (no DB URL) | 14 passed, 3 skipped (DB-only cases) |
| `ASSETOPS_TEST_TEMPLATE=0 pytest -n 2 tests/test_pg_harness.py` | UsageError, exit 4 |
| `ASSETOPS_TEST_TEMPLATE=0 pytest tests/test_pg_harness.py` (serial) | 14 passed, 3 skipped |

Not rerun: the full backend suite. Cited from the packet: revision `7c95c667` (final code revision; later commits
are docs only - confirmed by `git diff 7c95c667..8eefb190 --stat` touching only `.agent/`), JUnit cases=2141,
skipped=0, failed=1 (`test_runs_api.py` gitignored `var/sites/mg-001.yaml`), that file rerun with the yaml present
28/0/0. M1/M2 fixes touch only the guard, so the fix round does not need a new full suite. `check-all.ps1` not run
(it would fail in this console per M1; the implementer reports 9/9 from a non-UTF-8 console). Frontend checks are not
applicable (non-UI slice).

## Carry (not this slice)

`backend/tests/test_runs_api.py:551` reads `var/sites/mg-001.yaml`, which `.gitignore:6` (`var/`) excludes, so every
full run outside the main checkout fails one test and every reviewer has to hand-copy files. Recommend a small OPS
follow-on owned by the test-harness lane (with the planned test-suite speedup task): commit the fixture under
`backend/tests/fixtures/` (or derive it from `config/`) and point the test at it. Zero-skip policy means a skip is
not an acceptable fix.

## Residual risk not named in the packet

- Rule 8 now depends on the console encoding of whoever runs it (M1) until fixed.
- Core recognition is name-based; any import spelling the extractor does not model is silently unchecked rather than
  refused (M2). A fail-closed alternative, if the fix grows: refuse any `.insert/.update/.delete(...)` call in a
  writer module whose root name resolves to any sqlalchemy import.
