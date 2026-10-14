# T-test-speed planning notes (2026-10-14)

- Scope: owner item 1 only. Scheduled after S4-02d, outside W1 scoring. Packet name `T-test-speed-backend-suite.md` uses a tooling prefix to avoid implying an S1-S7 product slice.
- Code reality: `backend/tests/conftest.py:73-91` handles temp directories only. `backend/tests/test_s1_foundation_postgres.py:66-90` and `test_s1_bindings_postgres.py:64-82` own destructive module DB fixtures; imported by S4 files. `backend/pyproject.toml:23-39` has pytest but no xdist or markers. `tools/check-all.ps1:70-80` runs guards but not pytest.
- Baseline 11-16 minutes alone and 23-35 minutes with concurrent Postgres load is owner-observed in `.agent/planner-test-speed-brief.md:5`, not a measurement made during this planning pass. Implementation must record new same-machine timings and exact counts.
- Registry decision: no node. PRE-S3-03 has a packet and queue mention but no registry node; PRE-S3-04 has `I-PRE-S3-04` because it changes product Readiness. No registry JSON edit needed for tooling. Checker result recorded below.
- Key risk: xdist alone would run the current schema-dropping module fixture concurrently against one DB. Template clone alone still pays repeated module migration unless fixture ownership changes. Session isolation is per worker, while child processes and in-test lock/concurrency cases require special care.

## Planning verification

`node frontend/docs/architecture/check_v69_dependency_registry.cjs` passed: registry valid (224 nodes, 11 linked pilot panels). `git diff --check` passed. Planning pass did not run the backend suite because it changes no code or tests; implementation phase 1 records the real baseline.
