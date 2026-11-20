# T1 review, round 1 (discovery, W5)

Reviewer: fresh Claude reviewer, 2026-11-19. Head reviewed: `d7368d38a` (build `2572dc7e9`, `71757e817`,
`4b59be33d`, closing `7e73f5b47`, rulings `5d5cedfe3`, `.gitignore` `d7368d38a`). Base `8dec9efaf`.

## Summary

- **Verdict: ACCEPT WITH FIXES.** One Medium finding (M1) to fix on the branch, then a verification re-review
  of M1 only. The Lows do not block.
- The three design flaws are fixed and hold under probing: canonical D (worktree, symlink), `GIT_*` scrubbed in all
  four halves, nested `--db` refused at once (exit 69, 0.1 s bash, 1.7 s pwsh).
- The marker test agrees across `.cjs`, `.py`, `_heavy_slot.ps1` and `heavy-slot.sh`: same order, reasons and
  ancestry. I reproduced forged-marker, orphan-after-SIGKILL and private-dir refusals by hand.
- The tripwire inventory is complete for the tree. Check 7 fails on a planted unpooled line. V1, V3, V4, V5, V6 and
  V10 fail as stated, and so do all four R5 inventory plants.
- Nothing under `.claude/` changed. There is no `.claude/settings.json`.
- Mid-build rulings Q1 and Q2 are applied. A refused vitest leaves `git status` clean.
- **M1:** a bash-pooled command's child starts with SIGINT and SIGQUIT ignored, and the wrapper turns INT into TERM.
  So Ctrl-C on a pooled Python job skips its `finally` and teardown. I reproduced this.
- **A16 is pending.** It is post-merge and the coordinator's job. Lanes 3 and 4 wait on it.

## Findings

### M1 (Medium, blocking). Ctrl-C no longer reaches a bash-pooled child, and pytest/DB cleanup is skipped

- **Where:** `tools/heavy-slot.sh:277-283` (the child subshell) and `:253-268` (`hs_on_signal`).
- **What is wrong:** `( ... exec "$@" ) <&0 &` is an async list in a non-interactive bash. Bash starts it with
  SIGINT and SIGQUIT set to SIG_IGN. I measured the child's `/proc/<pid>/status` `SigIgn: 0000000000000006`; a
  plain child has 0. Python keeps an inherited SIG_IGN for SIGINT, so there is no KeyboardInterrupt. On INT the
  wrapper sends TERM to the tree, not INT. Python's default TERM ends the process without running `finally`.
- **Reproduced:** a script `try: time.sleep(20) finally: print("cleanup ran")` started in its own session.
  `kill -INT -<pgid>`:
  - unpooled: prints `cleanup ran`;
  - `tools/heavy-slot.sh -- python3 fin.py`: prints nothing.
- **Why it matters:**
  - D-T1.15 and R6 rest on "Ctrl-C reaches the whole foreground group". It reaches the group, but the child ignores
    it.
  - A human who Ctrl-Cs a pooled Postgres pytest run, or a `--db` prepare, loses fixture teardown and `finally`
    cleanup (database drops, temp state). This is a regression against today's unpooled behaviour.
  - P7, P7b and P8 use TERM only, so the suite does not see it.
- **Fix:**
  - Start the child subshell with `trap - INT QUIT;`. I checked that this clears SigIgn to 0.
  - In `hs_on_signal`, forward the signal received (INT for INT, HUP for HUP, TERM for TERM) to the tree. Escalate to
    KILL only after the 5 s wait.
  - Add a case, for example P7c: a group INT to a pooled `python3` with a `finally` prints its cleanup line, and the
    slot frees.

### L1 (Low). The pwsh wrapper stops its child with SIGKILL at once

- **Where:** `tools/heavy-slot.ps1:92`.
- **What is wrong:** `Process.Kill(true)` is SIGKILL on Unix, so a TERM to the pwsh wrapper gives the child no
  graceful stop. The bash half sends TERM, waits 5 s, then sends KILL. This does not break I12b, which says only
  "kill the child's tree".
- **Fix (optional):** send TERM to the tree first, wait up to 5 s, then call `Kill(true)`.

### L2 (Low). check-all's FAIL excerpt for the inventory guard shows the `7b` todo's stack, not the failure

- **Where:** `tools/checks/test_heavy_slot_inventory.mjs:169-171`.
- **What is wrong:** in my V10 run, the `[FAIL] Heavy-slot tripwire inventory (T1)` excerpt was the `7b` assertion
  (the four `.claude` lines). The real failure, `tools/layout-evidence.mjs: no assertHeavySlot( call`, was not in
  the excerpt. Anyone reading check-all's output is pointed at the wrong file.
- **Fix:** report `7b` through `t.diagnostic(...)` with no failing assertion until T1-F1. Alternatively, have
  check-all print the first failing test.

### L3 (Low). Check 7's line matcher is easy to satisfy by accident

- **Where:** `tools/checks/test_heavy_slot_inventory.mjs:90-108`.
- **What is wrong:**
  - `line.lastIndexOf("heavy-slot.", at)` treats any earlier `heavy-slot.` on the line as pooling. For example,
    "`tools/heavy-slot.sh --status`, then `npx tsc`" passes.
  - `HEAVY` misses a bare `pytest`, `npm run typecheck`, `npm run build` and `npm test`. It also misses a capture
    `-evidence.mjs` at the end of a line or before a backtick, because the pattern needs a trailing space.
- **Today:** I grepped the five §6 documents by eye and found no unpooled command, so this is future-proofing.
- **Fix:** require the wrapper on the same command span (between backticks), and add the missing forms.

### L4 (Low). Check 1 accepts `assertHeavySlot(` anywhere, a comment included

- **Where:** `tools/checks/test_heavy_slot_inventory.mjs:28-30`.
- **Fix:** match a non-comment call line.

### L5 (Low, documentation). A forged owner file is an undocumented deliberate bypass

- **What is wrong:** writing your own pid into `<D>/slot-N.owner` while another holder holds slot N, then setting
  the marker, passes every tripwire, because the lock is held and you are your own "ancestor". It takes deliberate
  effort, like the §5.2 gaps.
- **Fix:** list it with the documented gaps in `backend/TESTING.md`/spec §5.2.

### L6 (Low). A killed self-test leaves temp repositories behind

- **What is wrong:** `/tmp/t1-pool-97TfPe` and `/tmp/t1-pool-BLp4NI`, from 16:10 (before my runs), were left by
  an interrupted run. `cleanup()` runs only in `finally`.
- **Fix (optional):** sweep `t1-pool-*` older than an hour at start-up.

## Known deviations 1-4

1. **Accepted.** The `vite.config.ts` typing (`@ts-expect-error`, `globalThis`). `tsconfig` includes the file.
   Pooled `npx tsc --noEmit` exits 0, and unpooled vitest is refused. If `@types/node` is ever added, the
   now-unused `@ts-expect-error` fails `tsc` loudly, which is the safe direction.
2. **Accepted, per mid-build ruling Q1.** The `.claude/agents` edits are dropped, and `7b` stays a todo reporting 4
   lines until T1-F1 (verified).
3. **Accepted, as a spec wording defect, not an Implementer defect.** A12 is `full`, with reasons beyond
   ALWAYS_FULL. The outcome, the D-T1.17 smoke set, is unchanged, and widening `TOOLS_EXEMPT` past D-T1.9 would have
   been scope creep.
4. **Accepted.** `flock` and `rm` are externals run after the lock open:
   - each is short-lived;
   - `rm` runs with every lock fd closed;
   - a `flock` child inherits the held fds for milliseconds only.

## Checks I ran (head `d7368d38a`)

- `node --test tools/checks/test_heavy_slot_pool.mjs`, 3 runs: 31 pass, 0 fail, about 19-20 s each. No unexplained
  kill in those 3 runs or in the 4 plant runs.
- `node --test tools/checks/test_heavy_slot_inventory.mjs`: 7 pass, 0 fail, 1 todo (`7b`, 4 lines), 0.19 s.
- **Plants** (in a detached scratch worktree, each restored; worktree removed):
  - V3: P-T2 fails.
  - V4: P-T3 fails.
  - V5: 16 cases fail, P2, P3 and P2c among them.
  - V6: P6 fails.
  - V10: check-all exit 1 with `[FAIL] Heavy-slot tripwire inventory (T1)`. The "Missing-claim" FAIL in that run
    is environmental: the scratch tree has no `node_modules`.
- **R5 inventory plants:** each one is reported with its file and line:
  - `layout-evidence.mjs` with the assert removed;
  - a module-level `import heavy_slot_check` in `demo_combined_cold.py:2`;
  - `host/conftest.py:50` without the check;
  - an unpooled `npx tsc` in `backend/TESTING.md:439`.
- **Temp-repo probes:**
  - unpooled node and python: 69, with the exact message;
  - pooled: pass;
  - pooled without `--db` for a DB tripwire: 69;
  - `GIT_DIR`/`GIT_COMMON_DIR` on the wrapper and on the tripwire: D unchanged, pass;
  - private `ASSETOPS_HEAVY_SLOT_DIR`: 69;
  - nested bash to pwsh, pwsh to bash, main to worktree, symlinked path: 0.14-1.8 s;
  - P9b, bash and pwsh: 69;
  - with both slots held, a nested entry runs (0.1 s), and a third entry gets 75 after `--wait-seconds`;
  - `Enter-HeavySlot` inside a held slot with the other slot busy: `Nested=True`, 0.7 s;
  - forged marker naming another holder's slot (node, python, pwsh `Assert-HeavySlotHeld`): 69, "holder is not
    this process or an ancestor";
  - `ASSETOPS_HEAVY_SLOT_CONTAINER=db` outside a container: 69;
  - `kill -9` of the bash and pwsh wrappers: slot free at once, the child holds 0 lock fds, and the orphan's marker
    is refused (also after a new holder takes that slot);
  - capture-style orphan (`sh -c 'sleep 60 & exit 0'`): slot free when the wrapper exits;
  - TERM to the wrapper only, and TERM to the group: 143, tree gone, slot free;
  - stdin kept;
  - no-`flock` `PATH` hands over to pwsh: marker set, exit 4 passed through, `--status` works.
- **Real tree, all refused with 69:**
  - unpooled `npx vitest run <file>`, `npx vitest@<ver>` and `npm test`;
  - pytest with a bogus URL, both conftests;
  - `pytest.main([...])`;
  - `GIT_DIR=/tmp/x` pytest;
  - `layout-evidence.mjs` and `evidence-checks.mjs --self-test`;
  - `demo_combined.py prepare`, both unpooled and pooled without `--db`;
  - `demo_combined_kobo.py build`;
  - `mechanism_dataset.py ensure`.
- **Real tree, not refused:**
  - `mechanism_dataset.py status`;
  - `demo_combined.py links` and `serve --help`;
  - `chain_clone.py drop`;
  - pytest without a URL (24 passed, 3 skipped);
  - `test_evidence_checks.mjs` (12 pass);
  - Vite config load without `VITEST`.
- **Pooled on the real pool** (only while `--status` showed both slots free):
  - vitest file: 2 passed, 1.9 s;
  - `npx tsc --noEmit`: exit 0;
  - `assertHeavySlot` cost: 16 ms.
- **Q2:** after a refused vitest, `git status --short` is empty. The timestamp file is ignored, and I deleted my
  strays.
- **select-tests:**
  - `--json` is byte-identical to main's for the same `--files`, except where `TOOLS_EXEMPT` changed by design
    (D-T1.9);
  - `--base main` gives `full` (deviation 3).
- `.claude/`: 0 files in the diff.
- **Files outside spec §3-§7:**
  - the 30 capture scripts and 8 DB children, which the spec covers by class;
  - the decision and state indexes and `specs/INDEX.md`, from the closing and spec commits;
  - `.gitignore` and `mid-build-questions.md`, allowed by the rulings.

  None is a finding.

## Not verified by me

- The Postgres smoke set (D-T1.17), which needs the coordinator's DB turn. I cite the packet and its logs
  (`smoke-pg_harness-xdist2.log`: 17 passed under `-n 2`). I read the ancestry walk for xdist workers in the code.
- R6/A10 timing. I did not rerun the 6 check-all runs, and cite `a10/summary.txt`: main median 43.7 s, T1 median
  45.5 s, +1.8 s, SKIP line printed. Two runs show a 0.2 s slot wait against A11's 0.1 s, measured under load. I note
  it and do not count it as a finding.
- Windows (D-T1.10), verified by inspection only:
  - the .NET share-None open is the same call as before;
  - `PosixSignalRegistration` is guarded;
  - `Get-Command -CommandType Application` is used.

## Residual risk the packet does not name

- **Git Bash on Windows.** If it ships `flock`, `heavy-slot.sh` will not hand over to pwsh. MSYS flock does not
  interoperate with .NET's share lock, so bash and pwsh holders would not exclude each other. Bash-pooled tools
  would then be refused by the tripwires' share-lock probe. That fails closed, but it is broken. A `uname` check
  that always hands over on MINGW/MSYS would close it.
- **The unexplained `node --test` kill.** It was not seen in my 7 runs. One hypothesis: the `finally` blocks
  `killQuiet` PIDs read from owner files or `/proc` after those processes are gone (P6, P7, P8), and PID reuse under
  load could hit an unrelated process. Killing only PIDs still in the case's own tree would close it.
