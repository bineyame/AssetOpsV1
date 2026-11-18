# E4-C4 review: Performance comparison only on change (D-E4.8)

Reviewer: fresh Claude reviewer (did not author the slice). Branch `task/E4-C4-performance-on-change`, head 3a8530f82,
diff `main...HEAD` (7 files, +182/-3). Spec: D-E4.8 to D-E4.11 in `AssetOpsV1-plan2/.agent/build-sheet-OWN-GAPS-2026-11-08.md`.

## Verdict

**ACCEPT WITH NOTES. M1 must be fixed on the branch before merge** (a Medium finding blocks under D-E4.11). The skip
itself is correct: no input of `performance_migration run` can change while the Site's mark stays equal.

## Is the skip correct? Inputs of `performance_migration run` (backend/assetops_backend/performance_migration.py)

| Input | Where | Moves the mark? |
|---|---|---|
| `site_scope` (site, tenant) | `evidence` ledger | yes: `site`, `tenant` are 0047 input tables |
| `accepted_evidence` | `postgres_assessment_store.py:1225` (accepted_evidence, ingestion_disposition) | yes, both input tables, Site-scoped |
| `selected_intervals` | `:1234` (analytic_run_selection, recompute_job, analytic_run_assessment, assessment_revision) | yes, all input tables |
| `lineage_breaks` | `:1183` (analytic_run*, ingestion_disposition, assessment_revision, foundation_revision) | yes, all input tables |
| legacy claims | `JsonAssessmentStore` `<tree>/var/assessments` | no, but not written for imported Sites (legacy gate refuses KOBO-001 and KISIWA-001; E4 logs: empty baseline for both). Not a live input. |
| clock | `read_scope.clock()` only for `compared_at` | no, and nothing in `compare` or `permits_performance_cutover` depends on age or now |
| environment | `DATABASE_URL` | fixed per build |
| evidence-migration (S2) reports | not read by the Performance run | n/a |
| story / plan files | only which Sites run (`story()["sites"]`) | fixed per build |

- **add-dates and drains** write DB rows for the Site, so the mark moves and the next `performance_and_prebuild` reruns.
- **The first tick after prepare** has no marks file: `prepare` wipes `<work>` (`demo_combined.py:826-829`), so the first
  run is due. The finish ticks, drain-1 and drain-2 then record marks. The first `serve` tick skips only when they are equal.
- The run writes no DB rows itself, so it cannot move its own mark. Reading the mark before the run is the safe direction.
- The report dir `<tree>/var/evidence/migration-performance/<site lower>` matches the E4 logs (`.../kobo-001/...json`).

## Findings

1. **Medium: a mark that cannot be read crashes `serve` and kills the API.** `tools/demo_combined.py:1041-1055`
   (`read_site_mark`). Only a missing Site row returns None. A `psycopg` error (connection refused, too many
   connections, timeout) is not caught, so it propagates out of `performance_and_prebuild` and `tick`, out of the
   `serve` loop (`:1497-1512`, which catches only `KeyboardInterrupt`), and `finally` kills the API. Before C4 the loop
   had no in-process DB read: every DB failure was inside a `check=False` child, and the loop survived. The dispatch
   asks that an unreadable mark be treated as due, and the code does not do that. **Fix:** wrap the body in
   `try/except psycopg.Error: return None` (None is already due and records nothing), and add one test where the reader
   raises.
2. **Low: `c.read_only = True` is a no-op under `autocommit=True`.** `tools/demo_combined.py:1047`. psycopg applies
   `read_only` only in the `BEGIN` it issues (`_connection_base.py:568`), and autocommit issues none. The connection
   only runs two SELECTs, so nothing can be written. The "read-only" claim in the docstring and packet is not enforced.
   **Fix:** drop autocommit (one short transaction under `with`), or drop the claim. The connection is closed by
   `with psycopg.connect(...)`, so nothing leaks.
3. **Low: a Site whose comparison is not PASSED reruns on every tick.** `performance_migration.py` exits 1 on any
   outcome other than PASSED, so the mark is never recorded (`demo_combined.py:1069`). That is as specified ("record
   after exit 0"), and both Sites PASS today (E4 logs 97/98). But if a Site ever FAILS, the per-tick `F` churn of D-E4.8
   returns for it. Note this for PF3 triage: `stored > 0` on a quiet tick together with a non-PASSED performance line
   means this case.
4. **Low (style): the new constant and three functions are inserted inside C2's prebuilt-routes constant group.**
   `tools/demo_combined.py:347-371` splits `PREBUILT_ROUTES_FILE` from `PREBUILT_ROUTES_ENV` and `PREBUILT_SCHEMA`.
   Moving them below the group would fix it.

## Other checks

- **Atomic marks write:** temp file in the same folder, then `os.replace` (`:359-363`). The test spies on the replace.
- **A failed run records no mark:** checked in the code (`:1069`) and the test (`test_failed_run_records_no_mark`).
- **The four stubbed tests are not weakened.** Each stub returns None, so every run is due, which is the pre-C4
  behaviour. No assertion changed. finish_rows also gains `work` and `tree` (`tmp_path`, so there is no report and every
  run is due).

## Checks run (venv python, C4 worktree PYTHONPATH, `assetops_test`, one file at a time)

| Test file | Result |
|---|---|
| `test_e4_performance_on_change.py` | 6 passed in 0.30 s |
| `test_demo_combined_finish_rows.py` | 63 passed in 4.70 s |
| `test_demo_combined_mill.py` | 15 passed |
| `test_ch5c_env_parity.py` | 3 passed |
| `test_e4_prebuilt_routes_generator.py` | 10 passed |

- **Not run:** the full suite (the demo-sprint policy) and a live prepare or serve. PF3 by D-E4.9 is the E4 rerun's job.
