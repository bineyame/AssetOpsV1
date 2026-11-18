# OPS-04 review (fresh reviewer, read only; no suite, no Docker)

Verdict: ACCEPT (two Low doc findings, non-blocking).

Checks
1. Workers plumbing: ps1 `-Workers` (default 4) -> `$env:ASSETOPS_TEST_WORKERS` -> compose `${ASSETOPS_TEST_WORKERS:-4}` in the test service environment -> `sh` script `-n "${ASSETOPS_TEST_WORKERS:-4}"`. Reaches pytest end to end; default 4 at every hop. The sh script is the compose `command`, so it inherits the container env.
2. synchronous_commit: `_create` is called only for the run template and per-worker clones (pg_harness lines 263, 312). Names derive from the `_guard`ed `*_test` base via `database_name`, which always ends in `_test`. The non-routed in-place path does not use `_create`, so no ALTER there. Safe in practice. Low: `_create` has no assert of its own that `name.endswith("_test")`; one line would make the claim local rather than inferred.
3. Old `ASSETOPS_TEST_SYNCHRONOUS_COMMIT`: no remaining code use. Only stale mentions: backend/TESTING.md line 81 (Low: still documents the knob) and historical .agent logs/reports (ignore).
4. Compose `command: ["postgres","-c","max_connections=200"]`: correct for postgres:16.4-alpine (the entrypoint runs postgres with the args). The image sets no other server flags and the compose file had no prior command, so nothing is dropped. It takes effect only after the container is recreated. Estimated peak at 4 workers (about 62-67 at 2 workers, 10-20 sessions per worker) is roughly 85-130, under 200.
5. Template clones: per-database settings live in pg_db_role_setting, not in the template copy. `_create(worker, template)` re-runs the ALTER for every clone, so each clone gets it explicitly. The template also gets it, which is harmless.

Low findings
- TESTING.md ~218-223 still says "Use -n 2 ... max_connections = 100"; update with the re-measure.
- TESTING.md line 81 lists the removed knob.
