# PERF-01 review: baseline and quick wins

Reviewer: a fresh Claude Reviewer, independent of the builder. Branch `task/PERF-01-baseline-quick-wins`, head d4fe44a5, diffed against main 504ae5f1 (the merge base).

## Verdict: REVISE

The test-pipeline work does what the plan's phase 1 asks for (R2, R3, R5, R7, R9 and R10). The proof evidence holds up when checked independently. Two findings block merge:

- H1: the branch makes the architecture guard fail.
- H2: the new host wrapper, which `.ai/ROLE_CONFIG.md` now makes the only host path, does not work as documented.

Both fixes are small.

## Findings

### H1 (High): the architecture guard fails on this branch

- **Where:** `var/test-results/PERF-01-attribution/*`, `PERF-01-profiles/*` and `PERF-01-workers5/*`. These 19 files were force-added in e87614aa and 614f0716.
- **What is wrong:** `var/` is in `.gitignore` (line 6), and `tools/checks/configuration-persistence.ps1` refuses any file tracked under `var/`. `tools/check-architecture.ps1` now fails with six "var/ holds tracked files" errors. Main tracks no files under `var/`, so this branch causes the failure.
- **Why it matters:** `check-all` goes red at merge, and every slice after this one inherits a failing guard.
- **Fix:** move the committed evidence out of `var/`, for example to `.agent/PERF-01-evidence/` or `Docs/demo-sprint/perf-01/`. Then update the paths in the packet and `untrack` the files under `var/`.

### H2 (High): `tools/run-host-tests.ps1` binds the first test file to `-Interpreter`

- **Where:** `tools/run-host-tests.ps1:20`, `param([string]$Interpreter = '', [switch]$AllowHostFull)`.
- **What is wrong:** `$Interpreter` is positional, so the first argument that is not a named parameter binds to it. `--` does not stop this.
  - I reproduced it: `& t.ps1 -- a.py b.py -q` gives `Interpreter=[a.py] args=[b.py|-q]`.
  - The result is that every documented form fails. This covers `backend/TESTING.md:116-129`, the usage line at `tools/run-host-tests.ps1:3`, and the Docker-outage fallback at `backend/TESTING.md:136`.
- **What I observed:**
  - `run-host-tests.ps1 -- backend/tests/test_s4_schedule_tick_postgres.py --collect-only -q` printed "REFUSED: no test file named". The file had become the interpreter, because `Test-Path -PathType Leaf` is true for it.
  - `run-host-tests.ps1 -AllowHostFull -- backend/tests ...` printed "no Python interpreter at 'backend/tests'".
  - With two or more files, the script would run `& <first-file.py> -c <probe>`. That is refused on this machine only because `.py` has no file association.
  - It works only when `-Interpreter <python>` is passed explicitly.
- **Why it matters:** `.ai/ROLE_CONFIG.md:456` makes this the only host path. Agents who follow `TESTING.md` will be refused every time and will likely go back to raw `python -m pytest`, which loses the R9 stale-origin protection.
- **Fix:** take the interpreter only from a named parameter, either `[Parameter(Position = ...)]` on a different design or by parsing `-Interpreter` out of `$args` by hand. Alternatively, keep the parameter and check that it ends in `python.exe` or `python`, otherwise treat it as a pytest argument. Then run each documented form once and record the result in the packet.

### M1 (Medium): the default cap is stale and does not scale with the chosen workers

- **Where:** `tools/run-backend-suite-in-container.ps1:27` (`$CapMinutes = 100`); the `backend/TESTING.md` Timing section, "Expected container full run: about 50 min; its default cap is 100 min"; and `.ai/ROLE_CONFIG.md:454-455`, which now defers to "expected wall and cap in TESTING.md Timing".
- **What is wrong:**
  - The measured `-Tier all` wall is 74.2 min (4135 tests), and the fast tier takes 62-72 min. Twice that is about 150 min.
  - The R10 guard can choose 2 workers. That roughly doubles the wall, so the default 100-min cap would record a healthy run as a HANG and kill it with exit 124.
  - The Timing table also has no rows for 4135 tests or for the dedicated server. The OPS-03 paragraph still says the runner uses `-n 2`.
- **Fix:** add the PERF-01 measured rows to Timing. Then either set the default cap from the measured wall, or scale it by the chosen worker count, for example `CapMinutes = 2 * expected * 4 / Workers` when it is not given.

### L1 (Low): the suite-sweep refusal can be bypassed by a flag value

- **Where:** `tools/run-host-tests.ps1:34`. Any argument that does not start with `-` counts as a target.
- **What is wrong:** the value of a flag counts as a "file", so `-Interpreter <py> -k foo` with no file runs the whole configured test paths. My `--collect-only` check collected 5766 tests across the host and backend. An absolute directory path is not refused either, because `Join-Path $worktree 'C:\...'` is not a directory.
- **Fix:** require at least one target that resolves to an existing file, or to a `file::node`.

### L2 (Low): the packet contradicts itself on proof status

- **Where:** `.agent/PERF-01-packet.md:41-45`.
- **What is wrong:** that section still says "Proof status: incomplete", with "The slow tier was not run separately" and "The frontend forks-versus-threads count was not run". The later section, at line 70 and after, says the proof passes and records the slow run and the frontend runs.
- **Fix:** mark the earlier section as superseded, or delete it.

### L3 (Low): the raw proof runs are not on the branch, and their revisions are not stated

- **What is wrong:** the packet's proof cites `var/test-results/OPS-03/<run-id>/` directories. They exist only locally, in this worktree's ignored `var/`. The packet also does not name the revision each run was taken on.
- **What I checked:** no test, conftest or plugin code changed after e7a8bcd5 (07:59), so runs 075935 and 090322 cover the head's test code. Commits 614f0716 and d4fe44a5 change only tooling, the sampler, profile files and the packet.
- **Fix:** record each run's revision in the packet. Keep a small manifest with the collected-ID hash and the pass-list hash next to the moved evidence (see H1).

### Notes (not findings)

- **Phase timing is not off by default.** `ASSETOPS_TEST_PHASE_TIMES` is always exported by `run-backend-suite-in-container.sh`, so phase timing is on for every Docker run. It only reads reports, and that is the phase-0 design, so this is acceptable. `-Attribution` is the only opt-in instrumentation, and it is genuinely off unless `ASSETOPS_TEST_ATTRIBUTION` is set (`phase_attribution.register`).
- **The profile script has no R9 import-origin check.** `tools/profile-tests-in-container.sh` relies on the cached venv and installs py-spy from PyPI at run time (pinned to 0.4.0). That is acceptable for a profiling-only tool.
- **The frontend suite is red on main.** Three tests fail in `w1f4VerificationStructure.test.tsx` under both pools, per `var/test-results/frontend/*.log`. That failure was found by this slice, not caused by it, and it needs its own owner.

## Checks the brief asked for

| Check | Result |
| --- | --- |
| No product code changed | Pass. The changed paths are `tools/`, `backend/tests/{conftest,phase_*}.py`, compose files, `frontend/vite.config.ts` (test pool only), `host/conftest.py`, docs, the packet and evidence. |
| No test body or assertion changed | Pass. The only lines changed in test files are 5 added `@pytest.mark.slow` decorators, and no lines were removed. |
| Slow tier explicitly excluded and run separately | Pass. `-m "not slow"` deselects them and `-m slow` selects them, and the slow run 090322 has 3 cases, all passed. The two TEL acceptance tests are marked but sit outside the backend suite. |
| Collected IDs total 4135 | Pass. My own `--collect-only` gave 4135, and `-m slow` gave 3 of 4135. The host TEL file gave 2 of 3 under `-m slow`. |
| Instrumentation off by default, cannot alter behaviour | Pass (see the note above). The wrappers call through and re-raise. The wrapped `BatchIngestionService` has no static or class methods that a plain-function wrapper would rebind. The proof run with attribution on matched the baseline exactly. |
| Test-only server never touches `assetopsv1-postgres-1` | Pass. In dedicated mode the runner, samplers and profiler all target `assetopsv1-postgres-test-1`. `up --no-recreate --wait postgres-test` names a service with no dependencies, and the run uses `--no-deps`. The server has its own volume, publishes no port and holds only `assetops_test` plus the harness's `*_test` databases. The host wrapper's default of the shared `assetops_test` was already authorized before this slice. |
| The worktree-safe runner refuses the stale-venv state | Pass. With PYTHONPATH pointing outside a fake worktree it printed REFUSED (exit 2). With no PYTHONPATH it showed the stale `AssetOPsV1` origins and a missing `assetops_field`, then REFUSED (exit 2). The container `.sh` checks `/workspace` in the same way. Usability is a separate problem (H2). |
| The memory guard is sound | Pass. It takes the smaller of the VM's available memory and the Windows free memory above the reserve, plus memory the VM holds unused, then subtracts the 400 MB fixed cost. In the 5-worker trial it predicted 2650 MB of growth (400 + 5x450) against 1698 MB observed (VM used went from 1040 to 2738 MB). The lowest Windows free memory was 2747 MB, above the 1536 MB reserve. It refuses with exit 3 below 2 workers. An explicit `-Workers` value bypasses it by design, and the choice is logged in `run-options.txt`. |
| No execution-policy override | Pass on the branch. No changed or new script passes one. `keep-awake-during-tests.ps1` and the sampler are started with `-NoProfile -File`. The only overrides in `tools/` are the pre-existing ones in `check-all.ps1`, which this slice neither changes nor calls. |
| Processes stopped by PID only | Pass. Every `Stop-Process` uses `-Id` from `Start-Process -PassThru`. Containers are stopped by `docker kill <run-unique name>`. |
| `.ai/ROLE_CONFIG.md` change | Appropriate, apart from the pointers covered by H2 and M1. It does not adopt the D4 policy: `-Tier all` stays the default, and TESTING says D4 waits for phases 1-3. |
| Proof evidence | Pass, checked independently with my own JUnit and collected-ID compare over `var/test-results/OPS-03/`. Baseline 183000, run 1 020406, fast run 075935 and slow run 090322 all have identical 4135 collected IDs. The fast and slow cases together equal the baseline cases exactly, with identical statuses, no overlap and 0 skips. The only failures in every run are the known w303 pair. Run 1 differs from the baseline by exactly the 3 slow IDs. |

## Commands run

- `docker ps` showed only `assetopsv1-postgres-test-1` and `assetopsv1-postgres-1`, with no `assetops-ops03-*` containers running.
- `tools/check-architecture.ps1`: **FAILED** (H1).
- `tools/check-agent-workflow.ps1`: passed.
- `npx.cmd tsc --noEmit` in `frontend`: exit 0.
- `pytest backend/tests --collect-only` gave 4135. With `-m slow` it gave 3 of 4135, and the host TEL file gave 2 of 3.
- `tools/run-host-tests.ps1`, dry runs only:
  - with no arguments: REFUSED;
  - in the documented forms: broken (H2);
  - with `-Interpreter` and one file: collected 1 of 7;
  - with `-k foo` and no file: bypassed the refusal (L1);
  - against a fake worktree: refused the stale origin.
- `tools/attribution-overhead.py`: 1.14 us per wrapped call and 1.40 us per statement, consistent with the packet's 0.88 and 1.3 us.
- I independently compared JUnit results and collected IDs across the four proof runs (the script is in the reviewer's scratchpad, not committed).

## Not verified

- **Frontend:** `npm.cmd test` and `npm.cmd run build` are not run, because esbuild hits the known sandbox denial. The thread-pool numbers (3451 passed and 3 failed, 203 s warm) come only from the committed logs.
- **No full suite and no Docker runner run:** neither was rerun, by instruction. The memory guard's live behaviour, the hang path and the `-Server shared` path were checked by reading the code only.
- **Report tools:** `tools/profile-summary.py` and `tools/attribution-report.py` were not checked line by line. Their outputs are measurement reports, not proof inputs.

## Residual risk

- **Cap under fewer workers:** the cap does not scale with the worker count (M1). On a memory-tight day the guard picks 2 workers, and the run is killed as a "hang".
- **Crash safety off:** `postgres-test` runs with fsync and full_page_writes off. If Docker crashes during a run, the volume may be corrupt, and the next run fails at start-up rather than failing over. TESTING should say how to recover, by removing only `assetopsv1_assetops-test-pg` and never the development volume.
- **Phase-1 target missed:** the result, 62-72 min against the plan's estimate of about 50, is already known to the owner, and phases 2 and 3 are approved to close the gap.
