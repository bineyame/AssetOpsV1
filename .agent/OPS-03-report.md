# OPS-03 report: full backend suite inside the Compose network

Branch `task/OPS-03-suite-in-container` from main `e8c9cef6`. Tooling only; no production code changed.
USER_REVIEW_REQUIRED: false. Independent review required.

## What landed

- `docker-compose.test.yml`: `backend-test-runner` (`python:3.12.7-slim-bookworm`, `profiles: [test]`,
  `depends_on: postgres: service_healthy`, `working_dir: /workspace`, no ports), bind `${ASSETOPS_WORKTREE:?}` at
  `/workspace`, named volumes `assetops-test-venv`, `assetops-test-pip-cache`, env per contract 2. URL from
  `${ASSETOPS_CONTAINER_TEST_DATABASE_URL:?}` (`postgres:5432/assetops_test`, URL-encoded password); no `DATABASE_URL`.
- `tools/run-backend-suite-in-container.ps1` (only public command): resolves worktree from `$PSScriptRoot`,
  checks `docker compose`, refuses if `assetopsv1-postgres-1` has a different Compose project label, starts
  Postgres, run dir `var/test-results/OPS-03/<run-id>/`, hidden keep-awake watching its PID (stopped in `finally`),
  samples `pg_stat_activity` every 5 s, cap from `pytest-started`, timeout record + kill + exit 124, propagates
  the container exit code, never prints the URL/password, never stops/removes Postgres.
- `tools/run-backend-suite-in-container.sh` (LF, pinned in `.gitattributes`): venv create, marker = image + Python
  version + SHA-256 of the four pyproject files, editable install on miss (marker written only after success),
  the exact pytest command from contract 5, `console.log`, `wall-time.txt`, `exit-code`.
- `tools/keep-awake-during-tests.ps1`: optional `-WatchProcessId`; default behaviour unchanged.
- `backend/tests/test_s2_gateway_access_postgres.py`: the Windows-only skip replaced by a POSIX branch in the same
  node ID (0644 refused with "not owner-only", 0600 accepted); the Windows DACL branch is unchanged.
- `backend/TESTING.md`: wrapper, JUnit location, cap, Linux credential test, measured timing; host commands kept
  as the supported fallback.

## Known deviation (contract 1/3 command shape)

The contract's `up -d --wait postgres` and `run --rm backend-test-runner` would **recreate** the shared
`assetopsv1-postgres-1` from any worktree other than the one that created it: the `./backend/db/init` bind source
is part of the Compose config hash. Proven with `--dry-run` before any real run: `Container assetopsv1-postgres-1
Recreate` for both. The wrapper therefore uses `up -d --no-recreate --wait postgres` and
`run --rm -T --no-deps --name assetops-ops03-<run-id> backend-test-runner` (dry-run: `Running` / `Healthy`, no
recreate). `depends_on: service_healthy` stays in the file; health is ensured by the preceding `up --wait`. `-T`
is needed for a non-TTY launch; `--name` lets the wrapper sample the runner's sessions and kill it on timeout.
Postgres `StartedAt` stayed `2026-10-14T00:10:05Z` throughout.

## Runs (revision `b2a3e779` test tree; image `python:3.12.7-slim-bookworm`)

Command: `powershell -NoProfile -ExecutionPolicy Bypass -File tools\run-backend-suite-in-container.ps1`.
Host baseline: `python -m pytest backend/tests --collect-only -q` on the same revision, 3268 unique IDs.

| Run id | pytest wall | JUnit cases / skip / fail / error | dup IDs | node-ID diff vs host | peak runner / server-wide | orphans after |
| --- | --- | --- | --- | --- | --- | --- |
| 20261020-124618-2b1519 | 46.5 min (2790 s) | 3268 / 0 / 0 / 0 | 0 | empty | 58 / 73 | 0 |
| 20261020-134938-0cf9b7 | 49.7 min (2979 s) | 3268 / 0 / 0 / 0 | 0 | empty | 56 / 67 | 0 |
| 20261020-144232-5dda66 (after forced kill) | 41.8 min (2506 s) | 3268 / 0 / 0 / 0 | 0 | empty | 58 / 70 | 0 |

- Runs 1 and 2 are the two clean consecutive runs; run 3 is a third clean run that also proves the sweep.
- Server-wide counts include other lanes' sessions; all well under `max_connections=100`. No pool timeout,
  `QueuePool limit`, `too many clients` or `TimeoutError` in any console log. JUnit per attempt under
  `var/test-results/OPS-03/<run-id>/junit.xml`.
- Cache: run 1 `marker miss` (install about 15 min, slow PyPI downloads at about 35 KB/s through Docker Desktop);
  runs 2 and 3 `marker hit`.
- Cap and forced termination: `-CapMinutes 2` run `20261020-143951-7b7682` exited 124 with `timeout.txt`
  (non-idle `pg_stat_activity`, runner process list, console tail); the runner was killed and removed, the
  wrapper's keep-awake stopped, and `assetops_pt10964b_{tpl,gw0,gw1}_test` were left behind. Run 3's first
  provisioning swept all three (confirmed absent at 11:43 UTC, one minute after pytest start).
- No System 506/507 standby events during the runs.
- `tools/check-all.ps1`: all 10 guards passed.

## Timing and cause

About 47 min against the host's 56-58 min; the 30-min goal is not reached. Remaining time is product-path work:
the top 30 durations alone sum to about 24 min of worker time (W2 EV vector artifact 193 s, the deliberate
120 s schedule-health wait, the 123 s tick-cost measurement, the 82 s hung-stage test, and the EV replay/store
chains at 30-40 s each). Expected container wall is recorded as about 50 min with a 100-min default cap
(`-CapMinutes`) in `backend/TESTING.md`.

## Residual risk

- The active node is not named on timeout: `-q` prints no node IDs and `PYTEST_CURRENT_TEST` is not readable from
  outside the worker; `timeout.txt` gives the worker processes, DB activity and console tail instead.
- The shared venv volume is per machine, not per worktree; a pyproject change in one worktree reinstalls it for all.
- Runs 1-3 were measured with the 120-min cap (default changed to 100 afterwards, `638e1dd3`).
