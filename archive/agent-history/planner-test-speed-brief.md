# Planner brief: backend test-suite speed-up packet (2026-10-14)

Role: Planner (Codex). Branch `plan/test-suite-speed` (worktree `C:\Users\assef\Bineyame\AssetOpsV1-gap-planning`, from main). Owner instruction (verbatim, `.agent/owner-process-speed-2026-10-14.md`): "do item 1 after S4-02d and add the rest based on observation and merit". This is a tooling task run right after S4-02d, ahead of normal next-work ranking (like PRE-S3-03: outside competitive W1 scoring; do not give it a W1 core score).

Problem observed today: the full backend suite (~2100 tests, Postgres-backed) takes 11-16 min alone and 23-35 min when another agent uses Postgres; implementers and reviewers each run it per phase; concurrent runs hit "too many clients".

Write ONE implementation-ready packet `tasks/T-test-speed-backend-suite.md` (rename if the repo convention suggests better; tell me):
- Goal: cut full-suite wall time substantially without dropping or weakening any test; measured before/after on this Windows dev machine.
- Investigate and specify from the ACTUAL code (code-reality check is mandatory: name only fixtures, conftest files, scripts and env vars that exist, with file:line): how tests get their Postgres database today (find the harness that requires `_test` DB names, per-test or per-module migration, engine/connection handling, `gc.collect()` workarounds), how `tools/check-all.ps1` and agent briefs run the suite.
- Options to evaluate and choose among, with justification: pytest-xdist parallel workers with one DB per worker; a migrated template DB cloned via `CREATE DATABASE ... TEMPLATE` instead of re-running migrations; connection-pool limits per worker; test selection markers (fast/unit vs Postgres) so phases run focused subsets; a documented "focused set" command per area. Keep determinism; handle tests that start subprocesses, advisory locks, or rely on a single shared DB.
- Process outputs: a short testing guide (where it belongs in the repo) stating: full suite once per slice at the end; per-phase focused/affected suites; reviewers rerun the full suite only when a finding needs it; at most one full suite at a time on this machine unless the new isolation makes concurrency safe.
- Phases (S/M sizing; each fits one Claude implementer context) with focused proof: identical pass count before/after, no skipped tests added, timing table, two concurrent full runs without "too many clients" if claimed.
- USER_REVIEW_REQUIRED false (no product UI); independent review required.
- Registry: decide whether it needs a registry node at all (tooling outside W1 scoring); if so mirror how PRE-S3-03 or other outside-ranking work is recorded and keep `check_v69_dependency_registry.cjs` passing. Add a `tasks/README.md` row in the appropriate lane.
Run `node frontend/docs/architecture/check_v69_dependency_registry.cjs`. Edit only the new packet, `tasks/README.md`, the registry JSON (only if needed) and `.agent/planner-test-speed-notes.md`. Do not commit.
