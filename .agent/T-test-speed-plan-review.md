# T-test-speed planning packet: fresh Claude review

Reviewer: fresh Claude reviewer. The Codex Planner wrote the packet; I did not. Date 2026-10-14.
Worktree `AssetOpsV1-gap-planning`, branch `plan/test-suite-speed`, packet commit `2fc54c9b`.
Scope: `tasks/T-test-speed-backend-suite.md` (44 lines), its `tasks/README.md` tooling-lane row, `.agent/planner-test-speed-brief.md`, `.agent/planner-test-speed-notes.md`, judged against `.agent/owner-process-speed-2026-10-14.md` and the actual test harness. I checked the harness on this branch (main `0d137768`) and on `task/S4-02d-analytic-finding-worker-schedule` (main worktree, HEAD `62581ecd`), because the packet activates after S4-02d merges and S4-02d adds four test files.

## Verdict: RETURN for a short Planner amendment (targeted check is enough, no full re-review)

The direction is right. The packet does five things well:

- It makes per-worker databases plus a migrated template the mechanism and refuses `-n auto`.
- It keeps the `_test` guard and the "missing DB means skipped, never passed" rule.
- It refuses a shared live database posing as isolation.
- It treats focused sets as a workflow aid that never deselects from the full command.
- It keeps serial-with-template as the fallback when parallel runs cannot be made deterministic.

The no-registry-node decision is correct, and `backend/TESTING.md` is a sensible home for the guide. The code anchors are accurate (see the anchor checks below).

It is not ready to dispatch, for four reasons:

1. **The packet fails a repository guard** (H1).
2. **The fixture-ownership change would weaken today's isolation.** "Ordinary module setup truncates" gives each module less than the fresh migrated schema it gets today. The "dedicated clones" requirement for migration tests also does not fit how those tests are laid out (M1).
3. **The three-phase plan breaks the owner-adopted size rule** (M6).
4. **The process change does not reach the role briefs**, so the standing Reviewer brief would keep contradicting it (M7).

All four are text edits. The other Medium items (M2-M5, M8) can ship as implementer carries if the Planner prefers not to fold them into the text.

## Checks run (by me)

- `tools/check-agent-workflow.ps1`: **FAILED**, exit 1: `T-test-speed-backend-suite.md uses unrecognized Status: implementation`. This is the only failure (H1).
- `tools/check-architecture.ps1`: passed.
- `node frontend/docs/architecture/check_v69_dependency_registry.cjs`: exit 0.
- `git diff --check main`: exit 2. The failures are trailing whitespace in the committed raw log `.agent/planner-test-speed-log.txt` only. The packet and README are clean (L7).
- As instructed, I did not run the backend suite: another agent is using Postgres. Everything below is judged from code.

## Anchor checks (all verified)

- `test_s1_foundation_postgres.py:21-24`: module-level `URL` and the skip. `:66-90`: the module `engine` fixture (the `_test` assert, `DROP SCHEMA public CASCADE`, `DROP EXTENSION btree_gist`, `command.upgrade(head)`) and the per-test `store` truncate.
- `test_s1_bindings_postgres.py:64-82` is the same pattern.
- `test_s3_demo_configuration.py:138-149` resets and migrates inline.
- `test_s4_consequence_store_postgres.py:26-33`, `test_s4_consequence_recompute_postgres.py:23-30` and `test_s4_power_demo_case_postgres.py:27-34` are the autouse `gc.collect()` fixtures.
- `test_s4_evidence_drain_postgres.py:398-431` holds the Popen child (argv `URL`) and the advisory-lock asserts.
- `test_s4_evidence_consequence_work_postgres.py:464-544` holds the downgrade/upgrade cases.
- `backend/pyproject.toml:23-39`: no xdist, no markers, `testpaths = ["tests"]`.
- `conftest.py:73-91` handles basetemp only.
- `tools/check-all.ps1` runs 9 guards and no pytest.

Postgres is `postgres:16.4-alpine` (`docker-compose.yml`) and the role is `POSTGRES_USER` (superuser), so `CREATE DATABASE ... TEMPLATE` and `DROP DATABASE ... WITH (FORCE)` are both available. Migrations 0001-0013 seed no rows on an empty database (the 0011/0012 INSERTs are trigger and bootstrap-from-existing only), they create no roles, and there are no TRUNCATE triggers. Every advisory-lock assertion filters on `database = (SELECT oid FROM pg_database WHERE datname = current_database())` (drain `:398,:431`, work `:390`), so per-worker databases isolate them correctly.

## Findings

### H1 (High): the packet fails `tools/check-agent-workflow.ps1`, so `check-all` fails on the planning branch

`tools/check-agent-workflow.ps1:120-131` applies to every `tasks/T*.md`. It requires `^Status:\s*(\w+)` to be one of `planned|active|in_review|completed|blocked`. The packet's `Status: implementation-ready; ...` (packet `:3`) parses as `implementation`. The `T-` prefix chosen in the notes, to avoid looking like an S slice, puts the packet under the superseded T0xx naming that this guard and `AGENTS.md` both refer to.

**Fix:** pick one.

- (a) Rename to a non-`T` prefix, for example `tasks/OPS-test-speed-backend-suite.md`, and update the README link.
- (b) Keep the name and start the status line with a recognised word: `Status: planned (implementation-ready; activate immediately after ...)`.

I prefer (a), because it also stops the packet reading as part of the superseded T queue. Then rerun `check-agent-workflow.ps1`.

### M1 (Medium): "module setup truncates" weakens today's isolation, and "dedicated clones" for migration tests does not fit the tests as written

Today every module that uses `engine` starts on a freshly dropped and migrated schema. The packet (`:23`, phase 2) changes this to "ordinary module setup truncates". It also asks for destructive upgrade/downgrade tests to run "on dedicated clones that no ordinary test shares".

In practice:

- **Truncating does not undo schema changes.** `test_s4_evidence_consequence_work_postgres.py:144-165` creates a test trigger and function and drops them in `finally`. Five modules downgrade and re-upgrade in place: `test_s1_bindings_postgres.py:357-372`, `test_s2_evidence_ledger_postgres.py:433-443`, `test_s4_consequence_store_postgres.py:396-397` and `test_s4_evidence_consequence_work_postgres.py:464-544` (three cases). `test_s3_demo_configuration.py:142-149` drops the schema mid-session. If one of these fails part-way, the per-module rebuild currently contains the damage. Under truncate-only, every later module on that worker inherits the broken schema, and a head-revision assert would not catch a leftover trigger.
- **The migration tests sit inside ordinary modules.** They share the module `engine` and `site`/`store` fixtures and the import-time `URL`. Moving them to dedicated clones would mean rewriting test bodies and fixtures, which is exactly where coverage can quietly weaken.
- **The fixture is imported into many modules.** `engine`/`store` come in by name from `test_s1_bindings_postgres` in about 20 modules (S2, S3, S4 and S4-02d; see L1). A conftest fixture with the same name would be shadowed by those imports unless every import line is edited.

**Fix:** keep the database exclusive to one worker, as the packet already plans, and re-create it from the template at each module's setup.

- In `engine`, run `DROP DATABASE <worker_db> WITH (FORCE)` then `CREATE DATABASE <worker_db> TEMPLATE <run_template>` from an admin connection, and assert the head.
- Keep the fixture names and bodies in `test_s1_foundation_postgres.py`/`test_s1_bindings_postgres.py`, and have them call one shared harness function. All the `from test_s1_bindings_postgres import engine, store` lines then stay unchanged.

This keeps today's fresh-schema-per-module behaviour exactly, removes the repeated migrations, and lets in-place downgrade tests stay as they are. `WITH (FORCE)` also cuts off connections leaked by earlier modules, which bounds the slot leak per module. Drop the "dedicated clones" requirement, or reduce it to "only if a test cannot be isolated by the per-module re-clone".

If the Planner keeps truncation, specify instead:

- the truncate set is derived from the catalog (every table except `alembic_version`), not hand-listed;
- each module setup compares a schema fingerprint (triggers, functions, constraints) against the template, and re-clones on mismatch.

Phase 1 `--durations` must report setup time separately, so the saving from removing migrations is measured rather than assumed.

### M2 (Medium): routing must happen at configure time, and run identity must be per run rather than `gwN`

Every Postgres module, including S4-02d's `test_s4_schedule_tick_postgres.py:26` and `test_s4_schedule_health_postgres.py`, captures `URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")` at import. That value is then used in three ways:

- module skip marks;
- stores such as `PostgresFoundationStore(URL)`;
- child processes, through argv (drain `:413`) or `monkeypatch.setenv("DATABASE_URL", URL)` (S4-02d health `:230,:331,:413`, tick `:283`).

So per-worker routing only works if each process overwrites `os.environ["ASSETOPS_TEST_DATABASE_URL"]` in `conftest.pytest_configure`, before collection. A fixture-level route silently leaves modules on the base database. The packet's "use worker identity only for DB routing" (`:24`) also invites names like `assetops_gw0_test`, which collide between two concurrent invocations, and the packet offers that concurrency as a claim. `finally` cleanup does not run when an agent's process is killed, which happens with 11-35-minute suites under tool timeouts.

**Carry:**

- The controller generates a run ID (pid plus random). It reaches workers through xdist `workerinput`, and names are `<base>_<run>_<gw>_test`, at most 63 characters.
- Template creation is lazy: none for `--collect-only`, for non-Postgres focused commands, or when the URL is unset.
- The `_test` guard on the base URL runs before any DDL.
- DROP touches only names matching the run-owned pattern.
- A start-of-run sweep drops orphaned run-owned databases only when their run has no live sessions in `pg_stat_activity`.

### M3 (Medium): the packet does not say how to bound pools

All eight Postgres adapters build their own engine with `create_engine(url, pool_pre_ping=True)`: foundation `:124`, assessment `:103`, finding `:70`, ledger `:70`, gateway access `:49`, assumptions `:69`, consequence `:61` and schedule `:56`. Pool size is therefore not something a test can pass in. "Small pools ... do not alter production pool defaults" (`:25`) leaves the implementer to invent either a production constructor seam or a test-only monkeypatch.

A cap of `pool_size=1, max_overflow=1` can also starve a store that holds a dedicated claim connection while it works, for example `claim_site` in the drain and runner tests. That shows up as a 30-second pool timeout rather than a clear failure.

**Fix:** make explicit disposal the first lever. That means `store` and the analogous fixtures yield and then dispose, and the per-module `WITH (FORCE)` from M1. Allow a pool cap only through a test-scoped patch that is no smaller than the maximum simultaneous checkouts per store. Any pool timeout is a failure. Keep `gc.collect()` until session counts prove it is redundant.

### M4 (Medium): equal totals cannot show that no test was lost

"Equal collected/pass/skip totals ... (new harness tests count separately)" (phases 2 and 3) can hide a lost test that is offset by a new one, and a test that moves from passed to skipped while another moves the other way.

**Fix:** require a node-ID-level diff.

- Compare `--collect-only -q` sorted node IDs, and per-node outcomes from `--junitxml`, between baseline and final, and between serial and xdist.
- List added node IDs (harness tests) explicitly. Removed node IDs must be zero.
- Use the same junitxml to drive the guide's zero-skip check rather than parsing the summary line.

### M5 (Medium): timing comparisons are not controlled for machine load

The owner saw about 2x variance from concurrent Postgres load (11-16 minutes alone, 23-35 minutes shared). The phase-1 baseline and the phase-3 final runs would be taken hours or days apart under different load, so a "substantial improvement" could be noise, or could hide a real gain.

**Fix:**

- Time the final comparison back to back in one window: the baseline revision in a separate worktree, the new harness in this one, alternating, at least 2 runs each, reporting the median.
- Record a quiet-machine precondition at start and end: `pg_stat_activity` grouped by `datname`, plus other `pytest` processes.
- Run during a window with no other Postgres-heavy agent (owner item 7).

### M6 (Medium): three phases exceed the owner-adopted size rule

`.agent/owner-process-speed-2026-10-14.md` item 2, adopted at the coordinator's judgement, says an M task has at most two phases and the last phase's review doubles as the slice review. The packet (`:3`, `:30-34`, README row) is "M, split into three S phases".

Phase 1 (baseline, inventory and guide, with no test edits) is too small to justify its own build and review cycle.

**Fix:** use two phases.

1. Baseline, inventory, guide and the template/re-clone lifecycle with explicit disposal, all serial. Proof: node-ID diff and serial before/after timing.
2. xdist routing, grouping, connection budget, the guide's normal command and the brief edits from M7. Its review is the slice review.

Update the README row to match.

### M7 (Medium): the process change never reaches the role briefs

The guide contract (`:38-40`) only lands in `backend/TESTING.md`. Agents read their role briefs, not that file.

`.claude/agents/assetops-reviewer.md:40` instructs every Reviewer to run `.venv\Scripts\python.exe -m pytest backend/tests -q`. After this task that directly contradicts "reviewers rerun full only for a finding that needs it" and "at most one full suite at a time". `assetops-implementer.md:63-65` and `.ai/ROLE_CONFIG.md:371` already say "full once at the end" / "Full suites ... belong to the last phase", which is consistent but should point to the guide.

**Fix:** add these to the packet's edit list:

- the Reviewer brief's check block (focused files plus the implementer's same-revision full evidence; full rerun only for a finding; one full suite at a time);
- a one-line pointer in the implementer brief and in `ROLE_CONFIG.md`;
- any Codex-side reviewer prompt that hard-codes the full suite.

Then confirm `check-agent-workflow.ps1` still passes.

### M8 (Medium): the "serial group" is not defined

The packet asks for "module grouping or explicit serial group for migration/process/lock tests" (`:24`), but xdist has no "run alone" group. `xdist_group` only places tests on the same worker, which still runs at the same time as the other workers. With per-worker databases, the database state of migration, process and lock tests is already isolated (see the advisory-lock note above). What remains is CPU-contention timing.

S4-02d adds timing-sensitive cases: tick `statement_timeout_ms=3_000`, `lock_timeout_ms=1_000`, `backoff_base_seconds=1`, a `hang` child process (`test_s4_schedule_tick_postgres.py:400-407`), wall-clock skew asserts (health `:290`), and 30-second deadlines in drain and work.

**Fix:**

- Name `--dist loadfile`, which matches the module-scoped fixtures. With `--dist load`, every module's setup would run on several workers.
- Add timing-sensitive tests to the phase-1 inventory.
- If one flakes under contention, the remedy is a documented second serial invocation whose counts are reported and diffed together with the parallel run, never retries or reruns.

## Low (brief)

- **L1:** Evidence row `:16` names only S4 importers. `engine`/`store` are also imported by `test_s2_evidence_ledger_postgres.py:31` (plus `_alembic` at `:430`), `test_s2_gateway_access_postgres.py:27`, `test_s2_registered_basis_postgres.py:27`, `test_s2_site_evidence_postgres.py:27`, `test_s3_dispatch_assessment_postgres.py:25`, `test_s3_dispatch_read_postgres.py:14`, `test_s3_demo_configuration.py:135`, S4 assumption-read/finding-read/finding-store/evidence-history, and S4-02d's `test_s4_schedule_health_postgres.py:25` and `test_s4_schedule_tick_postgres.py:33-35` (`import test_s1_bindings_postgres as s1`). Cross-module helper imports also exist (`test_s4_consequence_store_postgres.py:38-40`). The inventory should list them all.
- **L2:** Pin the `pytest-xdist` version in `backend/pyproject.toml` dev extras and note that the shared `.venv` needs it installed.
- **L3:** Under xdist, confirm that workers receive a basetemp from the controller and that `conftest.pytest_configure` returns early on workers. Prove the sandboxed-reviewer fallback path (`.pytest-basetemp`) still works with `-n 2`.
- **L4:** This task necessarily runs several full suites (baseline, serial-after, two parallel, optional 3-worker, concurrent pair), against its own guide. State it as the one-off exception, and keep these runs in windows with no other Postgres-heavy agent.
- **L5:** The two concurrent-run claim should check `max_connections` (default 100) against the measured per-run peak times two before attempting it.
- **L6:** Keep `gc.collect()` removal out of scope unless M3's disposal makes it provably redundant. Removing it is not needed for the speed goal.
- **L7:** The tracked `.agent/planner-test-speed-log.txt` (4245 lines) fails `git diff --check` with trailing whitespace. The notes' "`git diff --check` passed" predates it. Consider not tracking raw Planner logs.

## Agreed as written

- No dependency-registry node. Like PRE-S3-03, this is tooling with no path to a W1 core panel. PRE-S3-04 has `I-PRE-S3-04` only because it changes product Readiness. No change to `queue_baseline_nodes`, and the registry check passes.
- `backend/TESTING.md` linked from `backend/README-db.md` is the right place for the guide. `tools/check-all.ps1` stays the separate guard command.
- `USER_REVIEW_REQUIRED: false` and an independent review are right for non-UI tooling.
- The serial-with-template fallback and the "no parallel speedup claim without determinism" rule.

## Implementer carries (if the Planner folds only H1, M1, M6 and M7 into the text)

M2 (configure-time routing, per-run IDs, lazy provisioning, orphan sweep), M3 (disposal first, pool cap only through a test patch at least as large as peak checkouts), M4 (node-ID and junitxml diff), M5 (back-to-back A/B timing with a quiet-machine record), M8 (`--dist loadfile`, timing-sensitive inventory, no reruns), and L1-L6.
