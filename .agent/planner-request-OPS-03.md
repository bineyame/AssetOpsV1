# Planner + Architect request: OPS-03 (run the full suite inside the Docker network)

You are the AssetOps Planner and Architect. Read:
- `.agent/owner-test-suite-policy-2026-10-20.md`;
- the OPS-03 row in `tasks/README.md`;
- `tasks/OPS-01-backend-test-speed.md`;
- `.agent/OPS-01-post-w2-report.md`, which measures ingest round trips at 1.2 ms through the Docker Desktop port forward versus 0.17 ms inside the container;
- `backend/TESTING.md`;
- the compose files and Dockerfiles in the repo;
- `tools/check-all.ps1`.

Write `tasks/OPS-03-suite-in-container.md`, a small tooling packet with an exact build contract. Settle every point an implementer would otherwise decide:
- how the suite runs on the same Docker network as `assetopsv1-postgres-1`: a test-runner container or `docker compose run`, the image, the volume mount of the worktree, Python and dependency installation, caching, and the environment (DB host and port inside the network, PYTHONPATH);
- the exact command and wrapper script name;
- how keep-awake and the 2x cap still apply;
- worker DB isolation and cleanup, staying under the 100-connection limit, and the `-n 2 --dist loadfile --no-loadscope-reorder` invariant;
- line endings and paths for Windows bind mounts;
- JUnit output location.

Acceptance:
- identical node IDs to the host run;
- 0 skips and 0 failures;
- two clean runs with timings and peak `pg_stat_activity`;
- the documented target (about 30 min) is a goal, not a pass gate;
- the host command stays supported as a fallback;
- no production semantics change.

Update the README row to "planned; implementation-ready". Write nothing else. Do not commit.
