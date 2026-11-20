> Finished; historical. Archived from .agent/review-PIPE-1.md on 2026-11-18 (declutter step 4).
# Review: PIPE-1 (D-1 fix and guard speed-up, A1-A6, A10)

Reviewer: fresh Claude reviewer, independent of the author. Discovery depth (W5): the whole diff
`main...task/PIPE-1-checks-speedup` (9 commits, head 8a3ab5cf7) was read and its claims were re-run in a throwaway
worktree, now removed. Judged against `Docs/engineering/build-pipeline-and-checks-speedup.md` (D-1, A1-A6, A10, §9)
and the owner approval `.agent/owner-build-pipeline-speedup-request-2026-11-18.md`.

## Verdict: REVISE (one small fix round, M1 only)

The runner rewrite is sound. Every blocking guard on `main` is accounted for, the fast mode skips only the estate
self-tests, the trigger fails safe, and the measured speed-up is real: 41-42 s fast. M1 blocks the merge. It is in the
D-1 failure class: commit 6b5c182cb makes main's `.venv` the silent default in worktrees, and through it the
chain-coherence money guard still imports **main's** `contracts`. The packet's W6 sweep says that class is closed,
and it is not. The fix is a few lines. The re-review only needs to check M1 and its probe. Everything else below is
Low or a merge-time action.

## Findings

### M1 (Medium, acceptance gap: D-1 class sweep incomplete). Worktree runs of the chain-coherence guard import main's `contracts`
- **Where.** `tools/check-all.ps1:184` runs `test_chain_coherence.py` with no `PYTHONPATH`. `tools/check-all.ps1:94-95`
  (commit 6b5c182cb) falls back to `/opt/assetecon/AssetOpsV1/.venv`, whose site-packages holds setuptools editable
  finders for `assetops_backend`, `assetops_contracts`, `fixtures`, `assetops_simulator` and others, all pointing at
  the main checkout. `tools/checks/test_chain_coherence.py:17-19` puts this tree's `backend` on `sys.path`, but not
  `contracts`.
- **Shown.** In a worktree I recorded every loaded module whose file is under the main checkout:
  - `test_chain_coherence.py` loaded 11 modules from main's `contracts/assetops_contracts/`.
  - `test_event_register.py`, `test_fuel_wording.py`, `perf_budget.py --fixture`, `period_read_parity.py --self-test`
    and `check_v69_ledger.py` loaded none.
- **Planted violation.** I put `raise RuntimeError` in the worktree's `contracts/assetops_contracts/__init__.py`:
  - run as check-all runs it, the chain-coherence guard printed `183 passed`, so it never saw the branch's contracts;
  - with `PYTHONPATH=<wt>/backend:<wt>/contracts` it failed (2 failed);
  - `test_event_register.py` failed at collection, because it adds `contracts` to `sys.path` itself.
- **Why it matters.** This is the same failure as D-1, in a blocking money guard (§9). Fast mode is now the default
  in worktrees, so a branch that changes `contracts` gets this guard checked against main's contracts, and it passes
  silently. Before PIPE-1 this happened too when builders passed `-Python` with main's venv. But this slice owns the
  class (W6), and its packet (line 20) says the class is closed.
- **Fix (class, not instance).**
  - In `check-all.ps1`, give **every** Python guard process the `PYTHONPATH` the chain-graph guard already gets:
    this tree's `backend` and `contracts`, joined with `[IO.Path]::PathSeparator`. Pass it through `Add-Guard`'s
    environment, or set it once for the pool.
  - Add one cheap blocking probe guard. It imports `assetops_backend` and `assetops_contracts` with the guards'
    interpreter and environment, and fails if either `__file__` lies outside `$repoRoot`. Then no later venv change
    can bring the class back silently.
  - Show the probe failing once with the `PYTHONPATH` removed.

### L1 (Low). A run killed by SIGTERM or SIGKILL leaves its guard processes running, and its slot opens anyway
- **Where.** `tools/check-all.ps1:290-295`. The `finally` block kills children only when the script itself unwinds.
- **Shown.** I sent SIGTERM to a running check-all root:
  - the root exited;
  - 3 `check-architecture.ps1 -Only …` children kept running (I killed them by PID);
  - the flock slot was released at once.
  An agent's command timeout kills processes this way, so the 2-slot cap can be exceeded briefly. The packet's
  claim, "Interrupted runs kill their children by PID", holds only for Ctrl-C and exceptions.
- **Fix.** Register SIGTERM with `[System.Runtime.InteropServices.PosixSignalRegistration]::Create` (pwsh 7.2+)
  and kill the running children there. Or start the guards in their own process group and kill that group. Also
  correct the packet's claim.

### L2 (Low). "Full on main" is decided by the branch name only
- **Where.** `tools/check-all.ps1:120-122`.
- **What.** On a detached HEAD at main's tip (for example, a worktree like `-base`), the branch name reads `HEAD`. The
  diff against the merge-base is then empty, so the estate self-tests are skipped silently. The post-merge
  containment rests on the coordinator's checkout being on the branch `main`.
- **Fix.** Also treat the run as on main when `git rev-parse HEAD` equals `git rev-parse $Base`.
- **Operational note.** The main checkout `/opt/assetecon/AssetOpsV1` is on `task/PIPE-1-checks-speedup` right now.
  The coordinator's `main-checkall.sh` runs there, so it would test this branch, not `main`.

### L3 (Low, the author's open question 1). The estate trigger set misses the self-tests' anchor files
- **Where.** `tools/check-all.ps1:44-49`.
- **What.** `test_estate_guard.py` asserts on 12 real adapter files and one migration, named by constants at lines
  28-29, 110, 131-134, 180-181, 212, 229, 246, 266 and 294-295.
- **Effect.** A branch that renames or moves one of these breaks the self-tests only on main's run after the merge.
  That is late detection, not a hole: the writer seam itself runs on every slice.
- **Recommendation.** Do not add only `postgres_estate_read.py`. Derive the trigger list from the test's own path
  constants, with a regex over `test_estate_guard.py` that the trigger self-test also pins. Then the set cannot
  drift when an anchor is added.

### L4 (Low). The summary line changed, and the coordinator tooling parses the old one
- **Where.** `tools/check-all.ps1:287`.
- **What.** The line is now `All 31 blocking guards passed.` Both
  `/tmp/claude-1001/-opt-assetecon-AssetOpsV1/c6d26aed-1fa9-4f4e-a150-d6f87dd20a07/scratchpad/checkall-queue.sh` and
  `/tmp/claude-1001/-opt-assetecon-AssetOpsV1/fffff20f-2bc4-4558-ba83-bc7cc594e723/scratchpad/main-checkall.sh` grep
  `All [0-9]+ guards passed|Check failed`. After the merge, a passing run would show "NO RESULT", or an empty result
  for main.
- **Fix.** Either keep a line that still matches (for example `All 31 guards passed (31 blocking, 3 advisory).`) or
  update the scripts at merge. See the fallout list below.

### Info (no action required)
- **Windows PowerShell 5.1.** `Process.Kill($true)` (line 293) does not exist on .NET Framework. The empty `catch`
  hides that, so on 5.1 an interrupted run never kills its children. The 5.1 path is otherwise untested; see the
  checks below.
- **Failure summary.** `Check failed: X of N guards` counts advisory guards in N (35 in my planted run). This is
  cosmetic.
- **No timeouts.** Nothing bounds a slot wait or a single guard. A hung guard holds its slot until someone kills it.
  This is acceptable at the current scale.

## Scope (check 1)
- **Built.** Only D-1, A1-A6 and A10, plus rule text. The diff touches `tools/check-all.ps1`,
  `tools/check-architecture.ps1`, the new `frontend/docs/architecture/check_mock_gaps.cjs`, `frontend/tsconfig.json`,
  `.gitignore` and docs.
- **Not built.** Nothing from PIPE-2 (A7, A8), OD-4, OD-6 or OD-7: no change to `demo_combined*` or the self-check
  rows, no snapshot or clone code, no full-suite change.
- **Commit 6b5c182cb (venv fallback).** It is safe for site-packages: no third-party package resolves to main's code.
  It is **not** safe for the editable first-party packages unless every guard puts this tree first on `sys.path`.
  The editable finder is appended to `sys.meta_path`, so a `sys.path` entry wins. Only the chain-graph guard has that
  entry from check-all; the rest depend on each test's own `sys.path` edits. That is M1.

## Guard accounting (check 2): main's 21, as they are on the branch

| main | Branch |
| --- | --- |
| Architecture seams (one job, 14 modules) | 14 blocking jobs (`-Only <module>`); the manifest check runs in every job; if the list cannot be read, one whole-runner job runs instead. Writer seam (rule 8) PASS in fast mode |
| Estate guard self-tests | Conditional (A2): `-Full`, on `main`, a trigger file changed, or the diff unknown; alone, `-n 4` |
| Navigation truthfulness, standalone | Removed (A5). `tools/check-navigation-truthfulness.ps1` dot-sources the same module the architecture job runs; confirmed identical |
| Agent workflow | Blocking |
| Dependency registry | Advisory (A6), plus a new blocking `check_mock_gaps.cjs` making the same `validateMockGaps` call with the same inputs |
| Delivery checker fixtures | Advisory (A6) |
| Mock-gap fixtures; missing-claim scan; missing-claim fixtures; evidence width; mock deviation and client vocabulary | Blocking |
| Screen ledger | Advisory (A6) |
| Chain coherence; event register; fuel wording (K9); chain graph; perf budget; period parity; hard-wiring; style ratchet; style fixtures | Blocking |
| (new) Trigger-rule self-test | Blocking |

- **Totals.** 31 blocking in fast mode, 32 with the estate self-tests, 3 advisory.
- **What fast mode drops.** Only the estate self-tests are ever skipped.
- **Advisory.** No blocking guard became advisory, apart from the three the spec names.
- **Fail-safe.** `git merge-base HEAD no-such-branch` returns 128 and an empty result, which leads to `diffError`
  and a run. A `git` that cannot be found throws under `Stop`, so the run fails loudly.

## Evidence re-run (check 3)
All of this ran in a throwaway worktree of 8a3ab5cf7 under the scratchpad. It has been removed, and the shared stash
list is back to how it was.

| Check | Result |
| --- | --- |
| D-1 with a planted `NOT_CHAIN_SOURCED` key outside `ENTRIES` | The old `;` join imported main's `backend/assetops_backend/__init__.py`: exit 0, "chain graph OK" (vacuous). The new `:` join imported the worktree's backend: exit 1, `not_chain_sourced: REVIEWER:PLANTED_NOT_IN_ENTRIES`. In the full check-all, `[FAIL] Chain graph check` |
| A2 fires | One comment line appended to `tools/checks/_common.ps1` gave `[PASS] Estate guard self-tests, pytest -n 4 (changed: tools/checks/_common.ps1) (150.9 s): 17 passed` |
| A2 skips | Clean tree: `[SKIP] Estate guard self-tests: writer guard and its tests unchanged against main` |
| Honesty, missing-claim | Planted "Fuel cost not available yet" in `frontend/src/ui/GapGroup.tsx`: `[FAIL] Missing-claim orphan scan` (untagged_copy at :56), and the scan fixtures failed too, because they also run the real scan |
| Honesty, client vocabulary | Weakened the UTC pattern in `tools/demo-combined-vocabulary.mjs`: `[FAIL] Mock deviation labels and client vocabulary` |
| A6, gap catalogue blocks | Duplicated gap `G-readiness-capability-assessable`: `[FAIL] Mock-gap catalogue (live registry)` and `[FAIL] Mock-gap catalogue fixtures`; the v69 registry `[WARN]`; run exit 1 ("Check failed: 6 of 35") |
| A6, advisory warns | Duplicated a screen in the v69 ledger only: two `[WARN]`, "Advisory warnings: 2", "All 31 blocking guards passed.", exit 0 |
| A10 | Cold `tsc --noEmit` 35.0 s and 1.23 GB; warm 4.0 s. Planted a type error: TS2322, nonzero exit with the cache warm, and again on a second warm run. Reverted: exit 0. `frontend/.tsbuildinfo/` is ignored |
| Fast check-all timing | 42.0 s and 40.5 s wall (author: 40.2 s). Peak tree RSS 2.38 GB (process tree without threads, sampled every 0.25 s; author: 2.71 GB). Critical path: dependency-direction, 36.7 s |
| With the estate self-tests | 190.6 s, peak tree 2.97 GB (author `-Full`: 171.5 s, 2.89 GB), under the spec's 3.1 GB |

- My 52 GB figure from the first sampler counted threads as processes, and I discarded it. The figures above come
  from the corrected sampler.
- I never ran more than one heavy job at a time.

## A3 slot locks (check 4)
- **Mechanism.** `[IO.File]::Open(..., FileShare.None)` on Linux takes a kernel `flock`, which closes with the
  process.
- **Test.** I held `slot-1.lock` in a separate pwsh process, and a second opener got `IOException` (busy). After
  `kill -9` on the holder, the lock file stayed on disk, and the next open succeeded at once.
- **Conclusion.** A stale lock file never blocks. When I started, `slot-1.lock` was left over from the author's runs,
  and my run acquired it with 0.0 s wait.
- **Remaining gap.** Killing a run releases its slot while its children keep running (L1).

## Fallout to update at merge (check 5)
- **Coordinator queue scripts.** Both scripts named in L4 (`checkall-queue.sh` and `main-checkall.sh`) grep the old
  summary line. `main-checkall.sh` also waits on `checkall-queue.sh`.
- **`.agent/coordinator-handoff.md`**
  - Line 24 describes the central queue and the helper scripts.
  - Line 74 has the Windows `-Python C:\...` command and "read `All 18 guards passed.`".
  - Lines 30, 32, 48 and others record "check-all 19/19" (history; it can stay).
- **`.ai/NOW.md:54-56`.** "Until it merges, the central check-all queue still applies": flip this at merge.
- **`backend/TESTING.md:36-39`.** It gives the Windows form `powershell ... tools\check-all.ps1` and says nothing of
  fast mode, `-Full` or the slots. It is not wrong, but it is stale for the VPS.
- **Already updated by the branch.** `.ai/RULES.md` §7 and `.agent/lane-rules-vps-2026-11-12.md`.
- **No CI.** There is no CI config (`.github` and the like are absent). Nothing else in `tools/`, `.ai/` or the docs
  parses the count. The "21 guards" in the speed-up spec and its renderer is a historical measurement.

## The author's open questions (check 6)
1. **Should `postgres_estate_read.py` join the trigger set?** Not on its own. Derive the trigger set from all the
   anchor paths in `test_estate_guard.py` (L3). That costs nothing in fast mode on most slices, and it catches anchor
   drift before the merge.
2. **Should the G8/G9 fixtures stay unconditional?** Yes, keep them:
   - together they take about 4.5 s, off the 37 s critical path;
   - the missing-claim fixtures also run the real scan against the tree (my product plant failed them too), so they
     are not only a self-test of the scanner;
   - making them conditional would save nothing measurable.

## Other checks (check 7)
- **PowerShell parse.** `check-all.ps1` and `check-architecture.ps1` parse with 0 errors under the pwsh 7.7
  language parser. There is no 7-only syntax (`??`, `?.`, ternary, `&&`/`||`, `-Parallel`), and the
  `ArgumentList` branch is gated on the PowerShell major version.
- **Not verified.** A true Windows PowerShell 5.1 run: no `powershell.exe` exists on this VPS. It also inherits the
  `Kill($true)` gap (Info).
- **`chainScreenRoutes.test.ts` is pre-existing.** With main's `frontend/tsconfig.json` restored, the worktree's
  `frontend` matches `main`, apart from the new `docs/` `.cjs`. `vitest run src/__tests__/chainScreenRoutes.test.ts`
  gives 1 failed, 1 passed (`expected [ '/actions', … (63) ] to deeply equal [ … (64) ]`). The failure is on `main`,
  not caused by this branch.

## Checks run
- These run on every check-all: `check-architecture.ps1` via its 14 `-Only` jobs, and `check-agent-workflow.ps1`.
  Both passed in my clean run (42.0 s).
- No full suite, no database, no Docker, no ports 5490 or 8990.
- Every process I started was stopped. The three orphans from the SIGTERM test were killed by PID.

## Residual risk the packet does not name
- The packet's W6 sweep claim covers `backend` but not `contracts` (M1). Its claim about cleaning up after an
  interrupted run is true only for in-process interrupts (L1).
- The containment "full on main after every merge" depends on the coordinator's checkout being on the branch `main`
  (L2). That checkout is on this task branch right now.
- With 2 slots and 4 jobs each, the peak is about 6 GB across two concurrent runs. That fits the 12 GB available
  today, but nothing caps memory if `-Jobs` is raised.
