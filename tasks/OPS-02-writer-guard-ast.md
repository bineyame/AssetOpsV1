# OPS-02 — statement-level product writer guard

Status: active (activated 2026-10-15 from main `5bfff665` under the owner-absence work order; plan review ACCEPT `.agent/small-followons-plan-review.md`); was implementation-ready
Size: S; one build and one fresh independent review
Branch when activated: `task/OPS-02-writer-guard-ast`, from merged main
USER_REVIEW_REQUIRED: false (non-UI; guard and test-harness only)
Owner: architecture checks; S4-02d F-B carry

## Outcome and authority

Rule 8 recognizes SQL writes as statements across Python string formatting and rejects writes outside the existing product writer boundaries. The proof closes `.agent/S4-02d-phase-2-review.md` F-B. This packet adds no registry node and does not authorize a new writer. Independent of unmerged LR-01/S5-01/S6-01/S4-05.

## Code reality and boundary

- `tools/checks/configuration-persistence.ps1:641-825` names eight PostgreSQL writers and applies `$sqlWrite`, target and per-writer tests line by line. The schedule store owns only four schedule tables and named mutable columns; assumption assignments permit only a set-once `recorded_to`; Finding/consequence inserts remain append-only. Preserve all writer/table/column boundaries and non-vacuity checks.
- `.agent/S4-02d-phase-2-review.md:59-84,220` records 11 missed probe forms: three split literal statements (including schedule head and cursor), triple-quoted multiline, literal newline escape, two SQL-comment-separated forms, MERGE, SQLAlchemy Core update, Core delete, and lowercase COPY. The listed forms are the acceptance corpus; record each as an automated mutation probe against `tools/check-architecture.ps1`.
- `backend/tests/conftest.py:103-116` configures xdist workers; `backend/tests/pg_harness.py:88-108` silently turns routing off for `ASSETOPS_TEST_TEMPLATE=0`. OPS-01 Low carry L1 requires an xdist usage error before worker DB mutation. This small check belongs here if it stays bounded.

## Build and acceptance

1. Parse Python source or executable SQL statements so implicit concatenation, multiline/triple-quoted text, escaped newlines and SQL comments are normalized before applying writer policy. Resolve only statically provable statements; refuse a write-shaped dynamic/unknown target or SQLAlchemy Core mutation that cannot be safely assigned to an allowed table/column. Attribute failure to source path and line. Do not blanket-allow imports, `MERGE`, `COPY`, DDL, upserts or a new statement form merely because it resides in an existing writer.
2. Run all 11 recorded forms as separate negative mutations and require `tools/check-architecture.ps1` failure for the correct ownership reason. Add allowed controls for existing real multiline SQL, case, aliases and harmless read statements; run the guard over current main without false positives. Confirm the existing phase-1 guard probes still fail as intended and all eight writers remain non-vacuous. Preserve cross-writer reverse checks for ledger, gateway access, assessment, Finding, assumption, consequence, schedule and Foundation.
3. If L1 fits: reject `ASSETOPS_TEST_TEMPLATE=0` whenever pytest-xdist is active, before a worker could reset a shared database. Focused test should invoke the configuration path without touching Postgres and assert a clear usage error, while serial opt-out remains valid. If this widens the slice, leave L1 explicitly in the OPS-01 backlog and report why.

Focused checks: the guard mutation corpus, `tools/check-architecture.ps1`, `tools/check-all.ps1`, and `backend/tests/test_pg_harness.py` if L1 lands. On the final revision run one real-Postgres full backend suite per `backend/TESTING.md` with JUnit zero skipped/failed, keep-awake and 20-minute cap; provide same-revision evidence to the reviewer. No UI or owner checkpoint.

## Architect questions

Recommendation: use a Python AST extractor called by the PowerShell guard for static strings and Core calls, preserving rule 8's policy tables; fail closed on unresolved writes. No policy change is requested. If a newly discovered dynamic form needs a legitimate exception, return the precise statement and table/column to the Architect before broadening ownership.

## Coordinator note after plan review (`.agent/small-followons-plan-review.md`: ACCEPT)

Implementer carries (Low): the Python extractor must locate the interpreter as `tools/check-all.ps1` does and fail hard (not skip) when it cannot run; name where the 11-form probe set lives and automate it; LR-01 (unmerged) adds `source_clock_attestation` to the assessment writer's rule-8 tables - whichever merges second carries it; a full suite is warranted only by the OPS-01 L1 `conftest` change.
