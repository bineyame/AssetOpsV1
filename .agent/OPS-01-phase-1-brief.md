# OPS-01 phase 1 — implementer brief

Branch: `task/OPS-01-backend-test-speed` (already created from main `1c7595de`, packet status active). Work in the main checkout `C:\Users\assef\Bineyame\AssetOpsV1`.

Packet: `tasks/OPS-01-backend-test-speed.md`. Build **phase 1 only** (baseline, `backend/TESTING.md`, serial template lifecycle, explicit store disposal), honouring carries M2 (lifecycle/guard parts that apply serially), M3, M4, L1, L6. Do not add xdist yet (phase 2).

## Observations from the S4-02d review (input, not requirements)

- The S4-02d reviewer polled `pg_stat_activity` during slow runs: no lock waits; long statements were per-module migration `ALTER TABLE` and per-test `TRUNCATE` waiting on `IO:DataFileImmediateSync` (Docker Desktop disk sync). Full suite varied 16 -> 37 min on the same code. So disk-sync variance is the dominant cost and noise source; measure it.
- Worth measuring (report, do not silently adopt): `CREATE DATABASE ... TEMPLATE ... STRATEGY FILE_COPY` vs the default `WAL_LOG`; and run-owned test databases only `ALTER DATABASE <run_db> SET synchronous_commit = off`. Never change server-wide settings (`fsync`, `postgresql.conf`, container config) — the server is shared.
- Because timing varies 2x run to run, record durations with `--durations=30` and keep the baseline honest about variance (two baseline runs if the window allows).

## Rules

- Scratch/test databases must end in `_test`; container `assetopsv1-postgres-1`, user `assetops`. Drop every DB you create.
- One full backend suite at a time on this machine; no other Postgres-heavy agent runs now.
- No test may be removed, skipped or weakened. Node-ID and JUnit outcome diffs per M4.
- Commit on the branch as you go. Do not merge. Do not touch `.agent/coordinator-handoff.md`.
- Run `powershell -ExecutionPolicy Bypass -File tools/check-all.ps1` before handoff.

## Handoff

Write `.agent/OPS-01-phase-1-handoff.md` (git add -f): what changed, baseline vs serial-template timings (with variance), node-ID diff result, zero-skip proof, peak sessions, inventory summary, open risks for phase 2. Report back concisely.
