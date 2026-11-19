# T1 review packet: the heavy-tool slot pool, enforced (option C)

Branch `task/T1-heavy-tool-slot-pool`, worktree `/opt/assetecon/AssetOpsV1-t1`. Spec rev 2, rulings D-T1.11-18.
`USER_REVIEW_REQUIRED: false`. **Mid-build questions: 2** (`mid-build-questions.md`), both ruled
(`rulings.md` "Mid-build rulings", commit `5d5cedfe3`): **Q1** the `.claude/agents` edits are dropped from T1;
check 7b stays a todo until follow-up T1-F1. **Q2** `.gitignore` gains `frontend/vite.config.ts.timestamp-*`:
a refused `npx vitest run` (exit 69) still leaves the temp file on disk, harmless, and `git status` stays clean
(checked); no `git clean` needed. Vitest tripwire form:
**primary** (`createRequire(import.meta.url)` in `vite.config.ts`), typed without `@types/node` (deviation 1).
Evidence: `/opt/assetecon/evidence/T1-heavy-tool-slot-pool/build-2026-11-19/`.

## Commits (build: 3, staged by explicit path)

- `2572dc7e9` commit 1: pool (`tools/checks/_heavy_slot.ps1`, `tools/heavy-slot.{sh,ps1}`), check-all slot
  block, trigger rule, `check-architecture.ps1` `_*.ps1`, P1-P15 + A11.
- `71757e817` commit 2: check modules, shim installer, vite/conftests/runners/compose, 30 capture scripts,
  11 DB entry points, P-T1..P-T7 cases, inventory checks 1-6, check-all guards. (Two fixes folded in by
  autosquash before review: `chain_clone.py` name refusal before the tripwire; `wrapHold` waits on the owner
  file, concurrency 4.)
- `4b59be33d` commit 3: documents, `select-tests.py`, inventory check 7.
- closing commit: this packet, `mid-build-questions.md`, spec status, `specs/INDEX.md`, `.ai/state`.

## Acceptance

- **A1** yes. P2 (bash vs two pwsh holders: 75), P3 (pwsh vs two bash holders: 75, `Test-HeavyLockHeld` True
  True), P2c (bash and pwsh race for one slot, 20 iterations in 5 temp repos: exactly one wins every time; the
  winner holds until the loser has exited, so two winners cannot both finish).
- **A2** yes. P4, P4b (pwsh outer; `Enter-HeavySlot` outer), P4c (M to W, W to M, symlinked M), all nested,
  under 5 s; P9b nested `--db` exits 69 in under 3 s (bash) / 5 s (pwsh start-up).
- **A3** yes. P4c, P5b (`GIT_DIR`/`GIT_COMMON_DIR` set: still `M/.git/check-all-slots`), P-T2 (private dir
  refused by both tripwires).
- **A4** yes. P6, P6b, P6c (slot free within 3 s; P6c child holds no `check-all-slots` fd), P7, P8 (143,
  tree gone), P7b (group TERM).
- **A5** yes. P9: second `--db` exits 75 with the db-job line while a slot is free; plain entry exits 0.
- **A6** yes. P-T1..P-T5, P-T7 in the self-test; P-T6 live (below). Exact message asserted byte for byte.
- **A7** yes. Inventory checks 1-7 pass on the tree and report each planted fixture.
- **A8** yes. V1-V10 below.
- **A9** yes for the five non-`.claude` §6 documents (check 7 blocking); the two `.claude/agents` briefs are
  reported as a todo (Q1).
- **A10** yes. Inventory 0.3-0.5 s. Detached scratch worktrees, 3 fast runs each, alternating (`a10/`):
  `main` (`-Base main~1`) 45.2 / 43.7 / 43.1 s, median 43.7; T1 head (`-Base HEAD~1`) 49.5 / 45.5 / 42.6 s,
  median 45.5: **+1.8 s**. All six exit 0; slot wait 0.0-0.2 s; each T1 run printed the pool SKIP line.
- **A11** yes. Measured alone: first `Enter-HeavySlot` ≈ 60 ms idle (A11 case asserts ≤ 100 ms); check-all
  "0.1 s waiting for a slot".
- **A12** `full`, but **not for ALWAYS_FULL reasons only** (deviation 3).
- **A13** yes. Smoke set below, all pooled and green; unpooled Postgres runs refused.
- **A14** yes. `--json` byte-identical to HEAD's `select-tests.py` for three `--files` sets (26 591, 239, 144
  bytes); only printed lines changed.
- **A15** yes: 2.
- **A16** pending, coordinator, post-merge.

## Checks run (real output)

- `node --test tools/checks/test_heavy_slot_pool.mjs`: 31 pass, 0 fail; 17-29 s (load average 2-14), run 5x
  after the last change.
- `node --test tools/checks/test_heavy_slot_inventory.mjs`: 7 pass, 0 fail, 1 todo (7b, Q1); 0.28 s.
- check-all fast at `4b59be33d` + uncommitted nothing: `All 38 guards passed`, 61.2 s wall, 0.1 s slot wait,
  pool self-test 20.0 s (`check-all-fast-T1.log`).
- `pwsh tools/check-all.ps1 -SelfTestSelection`: 33/33 cases. `check-architecture` and `check-agent-workflow`
  pass inside check-all; `check-decision-index.py` OK.
- P-T6 live: `cd frontend && npx vitest run src/shell/__tests__/scenarioEmptyContractSeam.test.ts` exit 69 with
  the exact refusal; `../tools/heavy-slot.sh -- npx vitest run <same>` exit 0, 1 file / 2 tests passed, 2.1 s.
- Pooled `npx tsc --noEmit`: exit 0, 40 s. Regression, no DB: `test_dd1b2b_drain`, `test_md0b_ensure`,
  `test_ar2_prepare_period_rows`, `test_demo_combined_links`: 45 passed, 4 skipped; `test_chain_coherence.py`
  183 passed; `test_evidence_checks.mjs` 12 pass.
- Refusals by hand: `demo_combined.py prepare`, `demo_combined_kobo.py build`, `mechanism_dataset.py ensure`,
  `chain_clone.py settle ch0`: 69; `mechanism_dataset.py status`, `demo_combined.py links`, `chain_clone.py
  settle ../x` (CloneRefused first): not refused by T1. Container runner unpooled: 69 before any docker call.
  Vite config loads without `VITEST` (`loadConfigFromFile`, no temp file left).
- Tripwire cost, pooled: `assertHeavySlot` 19 ms, Python `require` 17 ms.
- No-`flock` hand-over: `PATH` with only pwsh/git/env/bash: marker set, exit code 4 passed through, `--status`.

## Smoke set (D-T1.17)

DB pre-check: `db-job` free, no DB job in `ps` (only the walkthrough `serve`). Own `assetops_t1_test` created,
dropped afterwards (no `assetops_t1%` left).
- `npx tsc --noEmit` pooled: exit 0. Vitest file pooled: 2 passed (P-T6).
- `backend/tests/test_pg_harness.py`: unpooled exit 69 (refusal); pooled 17 passed (5 s); pooled `-n 2`
  17 passed (xdist workers pass by ancestry).
- `host/tests/test_up1_reading_upload_flow_postgres.py`: unpooled exit 69; pooled 1 passed (9 s).
- Not run: full suites (milestone run, `--db`), per D-T1.17 and the dispatch.

## Planted violations (`plants-summary.txt`, `V*.log`; each restored with `git checkout`)

V1 inventory 1 fails · V2 inventory 4 fails · V3 P-T2 fails · V4 P-T3, P-T7, P5 (bash, pwsh) fail · V5 P2 and
P3 both fail · V6 P6 fails (orphan keeps the lock) · V7 P5 both fail · V8 P9 fails · V9 P7 fails (30 s) ·
V10 check-all with V1 uncommitted: `[FAIL] Heavy-slot tripwire inventory (T1)`, exit 1 (`V10-check-all.log`;
that run also exposed the `chain_clone` ordering defect, fixed in commit 2).

## Known deviations

1. `vite.config.ts`: the spec's two lines fail `tsc` (no `@types/node`: TS2307 `node:module`, TS2591
   `process`). Same statements, with `// @ts-expect-error` on the import and `process` read off `globalThis`,
   as the file's `apiPort` already does. Inventory check 3 accepts it.
2. `.claude/agents` edits of §6 not made: dropped from T1 by the Q1 ruling (follow-up T1-F1).
3. A12: `select-tests --base main` is `full`; besides the ALWAYS_FULL files it also names the §5.5 tools
   (`demo_combined*.py`, `chain_clone.py`, `mechanism_dataset.py`), `heavy_slot_check.cjs`,
   `profile-tests-in-container.ps1` ("a tool a test may run or read") and the two frontend `.mjs` capture
   scripts. D-T1.9's exemption list is fixed by the spec, so I did not widen it. The outcome (`full`, so the
   D-T1.17 smoke set) is unchanged.
4. `heavy-slot.sh` runs `rm` at exit (owner file) after the lock open, with every lock fd closed on that
   command; `flock` itself also runs after the DB lock open. Both are short-lived externals that hold no lock.
5. The inventory's browser-file set is scripts only (`.mjs .cjs .js .ts .tsx .py .ps1 .sh`): specs and other
   documents name Playwright without launching anything. 30 files today.
6. `Enter-HeavySlot` has one extra optional parameter, `-AnnounceTo Host|Error`, so check-all's wait line
   stays a host line and the wrappers' goes to stderr.
7. pytest refusal prints the message twice (once by `require`, once as pytest's `Exit:` reason).

## Residual risk

- One unexplained kill of a `node --test` run during the build, right after a run SIGKILLed by a
  `process.kill(0)` bug (fixed: `killQuiet` ignores pid ≤ 0). Not seen in the 7 runs since.
- The pool self-test spawns about 40 pwsh processes; under heavy load its 5 s nesting bounds include pwsh
  start-up (seen failing at concurrency 8 under load 14; concurrency is now 4).
- Q2 (ruled): a refused vitest leaves one ignored Vite temp file per run on disk.

## Review focus

1. `tools/heavy-slot.sh` after the first lock open (builtins only; child start; trap and tree kill).
2. `Test-HeavyMarker` / `checkMarker` / `check_marker` agree (order, reasons, ancestry, `/proc/locks` probe in
   the Node and Python halves, flock probe in bash, .NET probe in pwsh).
3. The check-all diff: slot block, marker export, three guards, trigger generalisation, SKIP line, `finally`.
4. The `.gitignore` line (Q2 ruling) and 7b as a todo (Q1 ruling).

## Fix round 1 (review-1: M1, L1-L6)

Commit `3bca18cfe`. Pooled runs: pool self-test 32 pass, 0 fail (31 plus the new P7c), about 20.4 s, two runs; inventory test 7 pass, 0 fail, 1 todo (`7b`).

- **M1 fixed.** The bash child starts with `trap - INT QUIT;`, clearing the SIGINT/SIGQUIT ignore of an async list. `hs_on_signal` forwards the signal received (INT, HUP or TERM) to the child's tree, then waits up to 5 s and sends KILL. New **P7c**: a group SIGINT to a pooled python job with a `finally` runs the cleanup, exits 130, and the slot is free. Proven: with `trap - INT QUIT;` removed, P7c fails.
- **Decision to review (INT/HUP only).** A terminal Ctrl-C or a group kill already reaches the child, so an immediate forwarded copy gave Python a second KeyboardInterrupt inside its `finally` (seen in the first P7c run). For INT and HUP the wrapper therefore waits up to 2 s for the tree to finish on its own, forwards the signal to what is still alive, then waits up to 5 s and sends KILL. TERM is forwarded at once. A signal sent to the wrapper alone reaches the child after at most 2 s.
- **L1 fixed (inspection plus Linux pwsh).** `tools/heavy-slot.ps1` collects the child's tree from `/proc`, sends TERM, waits up to 5 s, sends KILL to survivors, then `Kill(true)`. P8 (pwsh TERM) passes on Linux. The Windows branch of the shell is not run.
- **L2 fixed.** `7b` is a todo that reports its count through `t.diagnostic`, with no failing assertion, so check-all's excerpt shows the real failure. The count reads 5 instead of 4 because L3 is stricter.
- **L3 fixed in part.** The wrapper must be in the same backtick span before the heavy pattern, and the `-evidence.mjs ` trailing space is gone. A planted `` `tools/heavy-slot.sh --status`, then `npx tsc` `` is now reported. **Known gap:** bare `pytest`, `npm run typecheck`, `npm run build` and `npm test` are still not matched. Adding them flagged about 20 prose mentions in `backend/TESTING.md`, `.ai/RULES.md` and the lane rules, so it is not small.
- **L4 fixed.** Check 1 counts only an `assertHeavySlot(` on a line that does not begin with a comment marker (`//`, `#`, `*`, `/*`). A planted comment-only file is reported.
- **L5 documented gap, no code.** A process that writes its own pid into a held slot's owner file, then sets the marker, passes the tripwires. It takes deliberate effort, like the §5.2 gaps.
- **L6 documented gap, no code.** An interrupted self-test leaves `/tmp/t1-pool-*` behind, because `cleanup()` runs only in `finally`. The two directories from 16:10 were not touched.

## Fix round 2 (review-2 M2, ruling D-T1.15a)

Commit: "T1 fix round 2" (see `git log`). Pooled runs: pool self-test 35 pass, 0 fail (two runs, about 29-32 s); inventory 7 pass, 0 fail, 1 todo (`7b`).

- **Bash wrapper.** The 2 s wait and the INT/HUP KILL are gone. A first INT or HUP is counted and not forwarded; the wrapper keeps waiting for the child with no time limit. A second INT/HUP is forwarded once to the child's tree, never KILL. TERM goes to the tree, waits up to 30 s (was 5 s), then KILL. The wrapper exits with the child's own status (143 when TERM stopped it, 137 if it needed KILL).
- **pwsh wrapper on Linux.** The INT and HUP handlers set `Cancel`, follow the same first/second rule and never KILL. TERM: TERM tree, 30 s, KILL, exit with the child's status. Windows Ctrl-C still kills the child's tree at once, by inspection only.
- **Tests.** Cleanup is a Python `finally` that sleeps 9 s. P7c: group INT, cleanup finishes, exit 130, slot free. P7d: INT to the wrapper alone, child still running at 5 s, the second INT lets the cleanup finish, no KILL. P7e: TERM, cleanup finishes within 30 s, exit 143. P8c: P7c on the pwsh wrapper. With the first INT forwarded (plant), P7c and P7d fail.
