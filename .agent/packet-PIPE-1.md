# PIPE-1 review packet: D-1 fix and guard speed-up (A1-A6, A10)

- Branch `task/PIPE-1-checks-speedup` (from `main` 3729ee44d). Spec: `Docs/engineering/build-pipeline-and-checks-speedup.md` §4.5 D-1, §7.1 A1-A6 and A10, §9 guardrails. Approval: `.agent/owner-build-pipeline-speedup-request-2026-11-18.md` (PIPE-2, OD-4, OD-6, OD-7 not built).
- Evidence (outside the repo): `/opt/assetecon/evidence/PIPE-1/run-2026-11-18/` (10 logs).
- `USER_REVIEW_REQUIRED: false` (tooling only; no product, UI or data change).

## What changed, per action

| Action | Commit | Change |
| --- | --- | --- |
| A1 / D-1 | 6a7af9475, 6b5c182cb | `tools/check-all.ps1` joins `PYTHONPATH` with `[IO.Path]::PathSeparator`, set on the chain-graph process only. Default interpreter tries both venv layouts, then the main checkout's `.venv` (worktrees have none; before, every Python guard failed as "missing tool" without `-Python`). |
| A6 | c4bc9fab4 | Advisory mode (WARN, never fails). Advisory: v69 dependency registry + S1-S7 queue, delivery-checker fixtures (S1-S7), v69 screen ledger. New blocking `frontend/docs/architecture/check_mock_gaps.cjs` = the live `mock_gaps` validation the registry guard used to carry. Gap fixtures and missing-claim scan stay blocking. |
| A5 | 460ca9529 | Standalone navigation-truthfulness call removed (the architecture runner runs the same module). |
| A2, A4 (+A3 slot) | 8bda8466c, 07e8a3907 | Process pool of 4 (`-Jobs`); each architecture module is its own job (`check-architecture.ps1 -List` / `-Only <file>`; no args = unchanged). Estate self-tests run only when `configuration-persistence.ps1`, `_common.ps1`, `sql_statements.py` or `test_estate_guard.py` differ from `main` (committed, staged, unstaged, untracked), with `-Full`, on branch `main`, or when the diff cannot be computed; then alone after the pool with `pytest -n 4`. The trigger rule has its own blocking guard (`-SelfTestSelection`, 10 cases, trigger files written out). Machine-wide slot cap (`-Slots 2`, lock files in `<git-common-dir>/check-all-slots`, released on exit). Interrupted runs kill their children by PID. |
| A3 | d3252550b | `.ai/RULES.md` §7 and `.agent/lane-rules-vps-2026-11-12.md`: builders run fast check-all themselves before review; coordinator runs it on `main` after each merge (full by itself). |
| A10 | b8cb9fc13 | `frontend/tsconfig.json` `incremental` + `tsBuildInfoFile: ./.tsbuildinfo/…`; `frontend/.tsbuildinfo/` git-ignored. |

"On main after merge" trigger (A2): no new mechanism. check-all detects branch `main` and runs full; the coordinator already runs check-all on `main` after each merge (handoff), now written into RULES §7. `-Full` exists for milestones.

D-1 sweep (W6, class "Windows path conventions in guard plumbing"): every other `PYTHONPATH` builder in `tools/` uses `os.pathsep`, `[IO.Path]::PathSeparator`, or `:` inside the Linux container (`run-backend-suite-in-container.sh`). `chain-structure.ps1`, `configuration-persistence.ps1`, `run-host-tests.ps1` already try both venv layouts. Python guards in check-all that import `assetops_backend` (`test_event_register.py`, `test_chain_coherence.py`) put this tree's `backend` on `sys.path` themselves; `perf_budget.py`/`period_read_parity.py` import it only in database mode, not in check-all.

## Timings and memory (this VPS, 8 vCPU; load avg 2-5 from other agents)

| Run | Wall | Peak single RSS | Peak tree RSS | Result |
| --- | ---: | ---: | ---: | --- |
| Spec baseline (3729ee44d) | 589.6 s | 1.24 GB | n/a | 21/21 |
| Before, re-measured today (3729ee44d, worktree) | **574.5 s** | 1.01 GB | n/a | 21/21 |
| After, fast mode (`tools/check-all.ps1`) | **40.2 s** | 1.04 GB | **2.71 GB** | 31/31 blocking, estate SKIP |
| After, `-Full` (estate self-tests forced, `-n 4`) | **171.5 s** (estate 133.1 s) | 1.14 GB | **2.89 GB** | 32/32 |
| Two runs, `-Slots 1` | 2nd waited 36.1 s, then ran | | | both pass |

Peak tree RSS (sum over the whole process tree, sampled every 0.25 s) stays under the spec's 3.1 GB. Critical path: dependency-direction module 33 s. `pytest-xdist` 3.8.0 is in `.venv` (nothing installed).

`tsc --noEmit`: cold 32.4 s / 1.23 GB; warm no change 3.7 s; one-file edit 10.2 s.

## Guard evidence (planted in a throwaway worktree of 3729ee44d, removed after)

- **D-1**: planted a `NOT_CHAIN_SOURCED` row outside `ENTRIES` in the worktree's `chain/graph.py`. Old line: imports `/opt/assetecon/AssetOpsV1/backend/...`, exit 0 "chain graph OK" (vacuous). New line: imports the worktree's backend, exit 1 `not_chain_sourced: SIGNAL:PIPE1_PLANTED_NOT_IN_ENTRIES` (`d1-proof.log`); the full new check-all also FAILs that guard (`planted-run1.log`).
- **A2 trigger**: unstaged edit to `configuration-persistence.ps1` → "Estate guard self-tests, pytest -n 4 (changed: tools/checks/configuration-persistence.ps1)" ran (`planted-run1.log`). Trigger-rule guard: dropping `sql_statements.py` from the list → exit 1; breaking the match → 4 FAIL lines, exit 1; clean → 10/10.
- **Writer seam per job (A4)**: planted `INSERT INTO action` in `estate/adapters/postgres_estate_read.py` → `Architecture seams: configuration-persistence.ps1` FAIL "A second product database writer…" (and 3 estate self-tests fail) (`planted-run1.log`).
- **Manifest under -Only**: unregistered `tools/checks/zz-planted.ps1` → `-List` refuses, fallback whole-runner job FAILs "is not registered" (`planted-run2.log`).
- **A6**: duplicate `mock_gaps` gap ID → `Mock-gap catalogue (live registry)` FAIL + fixtures FAIL, v69 registry WARN, run exit 1. Duplicate screen in the v69 ledger only → both v69 guards WARN, run **exit 0** "Advisory warnings: 2" (`planted-run3.log`). Clean worktree → 31/31, exit 0.
- **A10**: planted type error → tsc exit 2 with the incremental cache warm; clean → 0.

## Other checks

- `tools/check-agent-workflow.ps1`: passed. `tools/check-architecture.ps1` (no args): passed, 88.3 s.
- Guard tests: node `--test` (mock gaps, missing-claim, mock-deviation, style ratchet, evidence checks, hard-wiring) 81/81; pytest `tools/checks/` (chain coherence, chain structure, event register, fuel wording, perf budget, period parity) 253 passed; `test_estate_guard.py` 17 passed (`-n 4`, in the `-Full` run).
- Focused vitest sanity for the tsconfig change: `globalWorkClient.test.ts` 5/5. Seen, not mine: `src/__tests__/chainScreenRoutes.test.ts` 1 fails with `main`'s tsconfig too (route list drift on `main`).
- No full suite, no database, no Docker, no ports touched.

## Open questions (spec defaults applied)

1. Estate trigger set: spec's four files applied. The self-tests also copy `backend/assetops_backend` and assert on the real estate reader (`postgres_estate_read.py`); add it as a trigger? (The writer seam itself runs every slice, so a real violation is still caught.)
2. Missing-claim and evidence-width fixtures stay unconditional (spec G8/G9 suggested "only when the scanner changes"; not in A2's scope; together ~4 s in parallel).
3. Advisory guards: remove in declutter step 5 as the spec says; `check_v69_dependency_registry.cjs` also feeds `--next-work` (left as is).
4. Coordinator handoff (`.agent/coordinator-handoff.md`) still describes the central queue and `checkall-queue.sh`; left for the coordinator to rewrite.
5. Guard count changed (21 → 31 blocking in fast mode, 32 with estate; 3 advisory). Summary line is now "All N blocking guards passed."

## Known deviations

- A2 and A4 share one commit (one runner rewrite); the A3 slot mechanism is in it too. Rule text for A3 is its own commit.
- Not built: A9 (agent-workflow guard rewrite, D-2), PIPE-2 (A7, A8), OD-4/6/7.
- Windows PowerShell 5.1 path (no `ArgumentList`) uses a quoted argument string; not exercised here (VPS only).

## Review focus

`tools/check-all.ps1` trigger computation (merge-base, untracked files, failure → run), pool completion and child cleanup, advisory status handling; `tools/check-architecture.ps1` `-List`/`-Only`; `check_mock_gaps.cjs` equals the registry guard's call.
