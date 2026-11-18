# OPS-03 independent review

Branch `task/OPS-03-suite-in-container`, head `e1dd1957`, diff against `main` (9 files). Reviewer did not author the slice,
did not run the suite, and ran no real `compose up`/`run`.

## Verdict: ACCEPT

No High or Medium findings. Three Low items, none blocking.

## Deviation (contract 1/3 command shape): safety-necessary mechanical consequence; no Architect decision needed

- `docker-compose.test.yml` defines only `backend-test-runner` (profile `test`) and two named volumes. It does not override `postgres`.
- `compose ... --profile test config` (dummy env) shows `postgres` unchanged except its `./backend/db/init` bind source, which resolves
  to the invoking worktree (`...AssetOpsV1-review3\backend\db\init`). The live container's labels show it was created from
  `C:\Users\assef\Bineyame\AssetOpsV1\docker-compose.yml`, so the config hash differs from any other worktree.
- `--dry-run` from this worktree:
  - packet `up -d --wait postgres` gives `Container assetopsv1-postgres-1 Recreate`.
  - packet `run --rm backend-test-runner` gives `Recreate` as well, through `depends_on`.
  - wrapper `up -d --no-recreate --wait postgres` gives `Running`, then `Healthy`.
  - wrapper `run --rm -T --no-deps --name assetops-ops03-<id> backend-test-runner` creates only the runner container.
- The wrapper has no other compose verb, and no `down`, `stop`, `restart` or `rm` against Postgres. Its only Postgres
  touches are `docker exec ... psql` reads and the label check. `--rm` is kept. The packet's own rule is "do not stop or remove
  Postgres", so the packet's literal command would have broken a rule the packet itself sets. The deviation keeps the
  intent: Postgres is healthy before the run, and the runner is a one-shot. It is disclosed in the report.
- Postgres `StartedAt` is still `2026-10-14T00:10:05Z`, with project label `assetopsv1`.

## Checks run

- `tools/check-architecture.ps1`: passed. `tools/check-agent-workflow.ps1`: passed. I did not rerun the other eight
  `check-all` guards. The report says 10/10 passed.
- The credential test on the Windows host (`...::test_a_protected_dacl_that_grants_another_account_is_refused`): 1 passed.
- Host `pytest backend/tests --collect-only -q` on this head, with PYTHONPATH pinned to this worktree, gave 3268 IDs and 0
  byte-wise duplicates. Note: this worktree's `.venv` editable install points at the main checkout, and without the pin the
  collection fails with 29 import errors. That is a reviewer-environment artifact, not the slice.
- I parsed the implementer's JUnit files under `var/test-results/OPS-03/`:

  | Run | JUnit tests / skipped / failures / errors | Unique cases | Node-ID set vs host |
  | --- | --- | --- | --- |
  | 124618 | 3268 / 0 / 0 / 0 | 3268 | equal |
  | 134938 | 3268 / 0 / 0 / 0 | 3268 | equal |
  | 144232 (after kill) | 3268 / 0 / 0 / 0 | 3268 | equal |

  On the node-ID comparison, my first pass left 7 apparent mismatches. All 7 came from my own backslash conversion of
  escaped parameter IDs (`\n`, `\xb2`); none is a real difference. The DACL test is present in all three runs with no
  skip element.
- `wall-time.txt` gives 2795 / 2984 / 2510 s. `connections-peak.txt` gives server 73 / 67 / 70 and runner 58 / 56 / 58,
  under 100 in every run. There are no `QueuePool`, `too many clients` or `TimeoutError` lines in any console log. The
  report's 2790 / 2979 / 2506 s are the JUnit `time` values, which agrees.
- The runs used the `b2a3e779` test tree. `b2a3e779..e1dd1957` changes only docs, the report, the task status and the cap
  default (120 to 100), so the evidence applies to the head.
- Cleanup: the forced-cap run `143951` has `timeout.txt` and no junit. No `assetops_pt*_test` database is on the server now,
  so the `pt10964b` leftovers were swept. Other lanes' leftovers (`w206i_pt17e0dcc0_tpl_test` and others) are outside
  OPS-03's base and scope.

## Item checks

- **Test change:** the Windows DACL branch is byte-identical and passes on the host. The POSIX branch replaces a skip in
  the same node ID. It refuses mode 0644 through the `not owner-only` path of `verify_owner_only`, which is the same
  boundary as an "Everyone: read" ACE. It then restores 0600 and asserts acceptance. pytest's `tmp_path` is on container
  `/tmp`, not the NTFS bind mount, so chmod is real. Coverage is not weakened on either platform, and it is added on Linux.
- **`.gitattributes`:** `tools/run-backend-suite-in-container.sh text eol=lf`. `git ls-files --eol` shows `i/lf w/lf`.
- **keep-awake:** `-WatchProcessId` defaults to 0, so the default path is unchanged. It is consulted only when no host
  pytest is seen. The wrapper starts it before any Docker work and stops it in `finally`.
- **Host fallback:** the host commands in `backend/TESTING.md` are unchanged and documented as the supported fallback. No
  production code changed.
- **Secrets:** the URL is built in the environment only. The wrapper never prints it or runs `compose config`, and
  `DATABASE_URL` and the host test URL are removed before the run.
- **30-min goal:** the report says it was not reached, at about 47 min, and gives the cause (the top-30 durations). It is
  treated as a goal, not a gate, as the packet says. The expected wall (50 min) and the cap (100 min) were updated together.

## Findings

- **Low, `tools/run-backend-suite-in-container.ps1:58`:** when `assetopsv1-postgres-1` is absent, `up --no-recreate`
  creates it with the invoking worktree's `backend/db/init` bind. If that worktree is later deleted, the shared container
  keeps a dangling bind source. That source is only read at first init, so the impact is cosmetic or confusing.
  - Fix: one sentence in TESTING.md saying to create Postgres from the main checkout. Optional.
- **Low, `tools/run-backend-suite-in-container.ps1:91-103`:** the hang record cannot name the active node, which the packet
  asks for ("record the active node"). This is disclosed as residual risk in the report. The forced run's `timeout.txt`
  shows an empty console tail, because `-q` output was buffered, so the evidence is the process list and DB activity only.
  - Fix, later: write `PYTEST_CURRENT_TEST` from a conftest hook to a file in the run dir, or dump py-spy. This is not
  blocking for a tooling slice.
- **Low, residual:** an interrupted wrapper (Ctrl+C or a killed console) is not handled beyond keep-awake's idle exit. The
  named runner container may outlive it and keep holding sessions until it finishes. Untested.
  - Fix: a `finally` that runs `docker kill $runner` when `$compose` has not exited.

## Not verified

- I did not run the suite (as instructed), so the three runs are verified from their artifacts only.
- `--dry-run` cannot simulate the interactive part of `run`, so the claim that the runner's start does not touch Postgres
  rests on the dry-run create step and on `--no-deps`.
