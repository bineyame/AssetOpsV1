> Moved verbatim from the former `.ai/CODE_STATE.md` on 2026-11-18 (declutter step 2), part 2 of 11; sections keep their original relative order; the original order of all sections is the numbering in `index-*.md`. Index: `INDEX.md` in this folder.

## PRE-S3-03 - Delivery checker and next-work report (in review)

Built on `plan/pre-S3-startup`; packet `.agent/PRE-S3-03-review-packet.md`, questions `.agent/PRE-S3-03-questions.md`.

- `frontend/docs/architecture/delivery_next_work.cjs` owns delivery-plan validation and the `next-work` report; `check_v69_dependency_registry.cjs --next-work [--out f]` / `--verify-report f` drive it (exit 3 on refusal or stale inputs). Fixtures: `test_delivery_next_work.cjs` (node:test).
- Registry claim portions now carry `id`, `core`, `variant` (bounded/positive/unknown) and `state` (delivered/open/unmapped/excluded). Only `open` portions with real-node `technical_requires` and no proposed IDs are reviewed paths; `delivered` needs resolved `delivered_by` plus evidence. `real` panels need every portion delivered and an accepted visual gate.
- 15 S1/S2 bounded portions recorded delivered (14 panels `reviewed_mapping:true`, all `partial`); V-01 is `delivery_plan.visual_gates.V-01` (effort unrecorded, so blocked); `outside_ranking` holds A-finding-index and A-money-comparability.
- `tools/check-all.ps1` is the normal check command (architecture, navigation, workflow, registry, delivery fixtures, ledger).
- Open: the live report refuses (37 approved core panels unmapped: evidence-analysis:2 and all S3-S7 cores still name proposed R-/UI-/D- IDs). Independent mapping review pending. Stale Readiness text after S2-02 (foundation_api.py:270,286,295-298; FoundationRevisionPanel.tsx:318-353) is unowned (Q8).

## OPS-01 - backend test turnaround (phases 1-2 built, review pending)

Branch `task/OPS-01-backend-test-speed` from main `52189ec7`. Handoffs `.agent/OPS-01-phase-1-handoff.md`, `.agent/OPS-01-phase-2-handoff.md`; packet `.agent/OPS-01-review-packet.md`. Guide: `backend/TESTING.md`.

- `backend/tests/pg_harness.py`: run-owned databases `<stem>_pt<run>_<tag>_test`, one migrated template per run (`ALLOW_CONNECTIONS false`), per-module `DROP ... WITH (FORCE)` + `CREATE ... TEMPLATE`, `assert_at_head`, lease-guarded orphan sweep, `empty_tables` (DELETE over the TRUNCATE CASCADE closure under `session_replication_role = replica`), `dispose`.
- xdist (`pytest-xdist==3.8.0`, dev extra): controller makes the run id (`conftest.pytest_configure_node` -> `workerinput`), routes nothing; workers `route(tag=gwN, run=...)` before collection and return early from basetemp handling; first worker builds the shared template under `pg_advisory_lock`; workers drop only their own DB; controller `cleanup_run` drops the rest (covers crashed workers). Workers move `conftest.START_FIRST` modules to the front.
- Normal full command: `pytest backend/tests -n 2 --dist loadfile --no-loadscope-reorder` (7.7 / 8.4 min, peak 35 / 32 sessions; serial 30.8 min; pre-OPS-01 41-80 min). `-n 3`: one run, 6.5 min, peak 41.
- Parametrize IDs must be deterministic (xdist refuses differing collections); `test_s3_performance_cutover.py` now uses fixed UUIDs.
- Role guidance: reviewers reuse implementer same-revision full evidence; full suite once per slice; keep-awake + 2x cap (`.claude/agents/assetops-{reviewer,implementer}.md`, `.ai/ROLE_CONFIG.md`).
- Escape hatches: `ASSETOPS_TEST_TEMPLATE=0`, `ASSETOPS_TEST_CLEANUP=truncate`; measurement knobs off by default.
- Open: inline stores still GC-disposed (no public `dispose()` on production stores); `gc.collect()` fixtures kept; concurrent full runs unproven (one-at-a-time policy); timing-sensitive S4 cases did not flake in 3 parallel runs but remain disk-stall sensitive; `-n 3` not adopted on one run.

## OPS-02 - statement-level rule 8 writer guard (done, pending merge)

Branch `task/OPS-02-writer-guard-ast` from main `5bfff665`; packet `.agent/OPS-02-review-packet.md`; closes S4-02d phase-2 review F-B and OPS-01 L1.

- `tools/checks/sql_statements.py`: table-agnostic AST extractor. Renders whole string expressions (implicit concatenation, triple quotes, escapes; `+`, f-string, `%`, `.format`, `"".join` with dynamic parts as `{?}`), strips SQL comments, collapses whitespace, splits on `;` and at each write head (INSERT INTO/UPDATE/DELETE/TRUNCATE/MERGE/COPY/CREATE/ALTER/DROP/GRANT; `DO|THEN|FOR|KEY UPDATE` stay in their clause), and synthesises SQLAlchemy Core `insert/update/delete` (aliased imports, `sa.` attributes, `table("x").delete()`) into SQL. Bare string statements (docstrings) are skipped.
- `configuration-persistence.ps1` rule 8 applies the unchanged per-writer policy tables to clauses (`$line` = clause, `$lineNumber` = expression start line); the driver-import check stays per line. New global refusals: MERGE/COPY, a DML clause whose target is not a literal identifier, a dangling write head (`sql +=` assembly). Schedule UPDATE allows a table alias; its "one line" rule became "one statement". Writer non-vacuity is reported only when the extractor ran (its own failure is reported instead).
- Interpreter: `ASSETOPS_GUARD_PYTHON` (set by `check-all.ps1` from `-Python`), else `.venv/Scripts/python.exe` or `.venv/bin/python`; a missing or failing extractor is a rule-8 failure, never a skip.
- Proof corpus `tools/writer_guard_probes.py` (`--seam` = rule-8 module only): 11 F-B forms, a two-line UPDATE per writer, reverse ownership per table family, dynamic/Core/fragment/CTE/upsert/COPY forms, plus one controls run.
- `backend/tests/conftest.py` `refuse_template_opt_out_under_xdist`: `ASSETOPS_TEST_TEMPLATE=0` under xdist (controller or worker) is a `pytest.UsageError` before routing; serial and `-n 0` unchanged.
- Adding a writer table (LR-01 `source_clock_attestation`, S6-01a Action tables, S4-05a provenance tables): extend the rule-8 policy arrays only; the extractor needs no change.
- Merge with main `0d3114a3` (2026-10-16): rule 8 statements carry the ninth writer (Action store, insert-only), LR-01 `source_clock_attestation` (assessment store, insert-only) and S4-05a provenance (ledger, insert-only; three DO NOTHING arbiters). S4-05a's provenance verb refusal and S6-01a's Action every-line refusal run on source lines (driver loop) and on clauses; new: an insert-only table (attestation, Action, provenance) is never upserted (`DO UPDATE`).
- Open: SQL read from files, or assembled across statements other than a dangling head, is not resolved; `.agent/S4-02d-phase-1-probes.py` "split update" is now an allowed form (see packet).
## PIPE-1: guard speed-up and D-1 (2026-11-18, `task/PIPE-1-checks-speedup`, in review)

- `tools/check-all.ps1`: 4-process pool (`-Jobs`), one job per architecture module (`check-architecture.ps1 -List`,
  `-Only <file>`); estate self-tests only when `configuration-persistence.ps1`, `_common.ps1`, `sql_statements.py` or
  `test_estate_guard.py` differ from `main`, with `-Full`, or on branch `main` (then alone, `pytest -n 4`); the trigger
  rule is its own guard (`-SelfTestSelection`); 2 runs at once machine-wide (`-Slots`, `<git-common-dir>/check-all-slots`);
  advisory mode (WARN) for the v69 registry, S1-S7 delivery fixtures and v69 ledger; new blocking
  `frontend/docs/architecture/check_mock_gaps.cjs`; duplicate navigation run removed; D-1 `PYTHONPATH` uses the platform
  separator; the interpreter falls back to the main checkout's `.venv`. Fast 40 s / 2.7 GB tree peak; `-Full` 172 s.
- `frontend/tsconfig.json` incremental, cache `frontend/.tsbuildinfo/` (ignored).
- Open: estate trigger set (reader file?), D-2 agent-workflow rewrite (A9), deletion of advisory guards (declutter step 5).

