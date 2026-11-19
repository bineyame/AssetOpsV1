# T1 handshake (one combined round, RULES §4 items 6-7)

The Reviewer, after reading `spec.md` and `reviewer-guide.md`, and the Implementer, after a pre-flight of
`spec.md` against `main`, write their questions here in one batch. Number them R1, R2 and so on, and I1, I2 and
so on. Each question cites the spec section and says what is unclear and what answer the writer expects. The
Architect answers every question once, in `rulings.md` under "Handshake answers (round 1)", and folds the answers
into `spec.md`. The handshake ends when neither section has an open question; coding starts only then.

## Reviewer questions

Reviewer (fresh Claude, spec handshake round, head 51ed6f9c5). Read: `spec.md`, `reviewer-guide.md`, `rulings.md`,
`tools/check-all.ps1:135-230,316,405`, `tools/select-tests.py`, `tools/run-host-tests.ps1:1-30`, `backend/TESTING.md`,
`.claude/agents/*.md`, `.agent/lane-rules-vps-2026-11-12.md`. Measured: `select-tests.py --files <K7 pair>` takes 6.1 s
on an idle machine; `pwsh -File x.ps1 -- a -- -q` passes both `--` through on pwsh 7.7; a K6-scope grep finds
unpooled commands only in the §6 files today. **(done)** marks a question whose answer changes what counts as done.

**Lock interop**

- **R1 (§2, §7.2 P2-P4) Interop coverage.** P2/P3 test "all held, the other shell waits", and P4 nests only bash
  outer then pwsh inner. Not covered: (a) pwsh outer (`heavy-slot.ps1`, and check-all) with a bash nested entry, which
  is the check-all-guard case; (b) a bash and a pwsh entry racing for the same single free slot, where exactly one
  must win; (c) how many repetitions make P2/P3 "not flaky" (the guide says run twice by hand). Expected: add P4b
  (pwsh outer, bash nested; check-all outer, bash nested) and P2c (race, N iterations inside the test), and name N.
  **(done)**
- **R2 (§2 slot directory, marker test) Path canonicalization.** The marker is valid when "its directory equals
  `D`". In the main checkout `git rev-parse --git-common-dir` prints `.git` (relative); in a worktree it prints
  `/opt/assetecon/AssetOpsV1/.git`. pwsh `[IO.Path]::Combine`/`GetFullPath` does not resolve symlinks or `..` the
  way bash `realpath` does. A mismatch turns a nested entry into "stale", so it waits for a second slot while its
  parent holds one, which is the deadlock §2 rules out, ending in exit 75 after 1200 s. Expected: name the comparison
  (both sides canonical absolute path via the same rule, or device and inode), and a P case where the outer entry runs
  from the main checkout and the inner from a worktree (or the reverse). **(done)**
- **R3 (§2) Git environment redirects the pool.** `GIT_DIR`, `GIT_COMMON_DIR` or `GIT_WORK_TREE` in the environment
  changes what `git rev-parse --git-common-dir` returns, so `GIT_DIR=/tmp/x tools/heavy-slot.sh -- npx tsc` runs in a
  private empty pool (and check-all inherits the same hole today). H0 refuses `ASSETOPS_HEAVY_SLOT_DIR` but not these.
  Expected: either the wrappers and `Get-HeavySlotDir` resolve with those variables removed (and a P case proves it),
  or H0 refuses them on a pooled segment; say which, and whether check-all's resolution may change. **(done)**

**Deadlock and nesting**

- **R4 (§2 `--db` when nested) Lock-order inversion.** §2 says the order is always `db-job.lock` then a slot, but a
  nested `--db` takes `db-job.lock` while its parent holds a slot. With A on slot-1 and C on slot-2 both running a
  nested `--db`, and B holding `db-job.lock` and waiting for a slot, all three wait until 1200 s and two lanes fail with
  exit 75. The guide (R1) accepts "times out with exit 75", which is a bounded deadlock, not freedom from deadlock.
  Expected: a nested `--db` with no valid `ASSETOPS_HEAVY_DB` either refuses at once (exit 69, "put --db on the outer
  wrapper") or makes one non-blocking attempt only; the guide's R1 expectation is updated to match. **(done)**
- **R5 (§2 marker test) "Someone holds it" is not "my parent holds it".** Validity checks only that the named lock is
  held. A process that outlives its wrapper (SIGKILL orphan, or `setsid nohup ... &` inside a pooled command) keeps the
  marker; once another lane takes that slot, the orphan's pooled calls count as nested and take nothing. Expected:
  either the Architect records this as an accepted residual risk (in the spec and the packet), or validity also
  requires the owner file's `pid=` to be alive and an ancestor of the caller (Linux `/proc`; Windows skips). Say which
  so the R2 probes have a fixed bar.

**Leaked locks and the child**

- **R6 (§3.3 `set -m`) Process group, tty and stdin.** Under `set -m` the child runs in its own background process
  group. In a terminal, a read from the tty (an `npx` install prompt, `pytest --pdb`) stops it with SIGTTIN, and the
  `wait` loop must not treat a stopped child as exited or loop forever; Ctrl-C reaches only the wrapper's group. Does
  the Claude Bash tool give a controlling tty? Expected: the spec states the child's stdin (inherited), what happens
  on SIGTTIN/SIGTSTP (for example the wrapper uses `setsid` rather than `set -m`, or exits with the child's stop as a
  failure), and a P case for a child reading stdin (`heavy-slot.sh -- sh -c 'read x; echo $x' <<<y` prints `y`).
- **R7 (§2, §7.2 P6-P8, V5) Leak paths other than the child.** I will check: (a) helpers the bash wrapper starts after
  opening the fd (`git`, `date`, an owner-file writer) close it or run before the open; (b) a SIGKILL of the **pwsh**
  wrapper and of **check-all** releases the slot and its child or guards hold no fd (P6 and V5 cover bash only); (c)
  Windows `Process.Start` with `UseShellExecute=false` inherits only inheritable handles, and `FileStream` is not one
  (inspection). Expected: add P6b (pwsh wrapper SIGKILL) and P6c (check-all SIGKILL with a guard that sleeps), or say
  why not. **(done)**
- **R8 (§3.1 `Test-HeavyLockHeld`, §3.2 `-Status`, §3.4) Probes and the slot count.** (a) A probe on a free lock
  takes it for a moment; a real acquirer polling at that instant moves to the next slot or waits 2 s. Accepted?
  (b) `OpenOrCreate` on a marker naming `slot-5.lock` creates that file in `D`; should the probe use `Open` and treat
  a missing file as stale? (c) `check-all -Slots 3` takes `slot-3.lock`, which the wrappers (fixed at 2) never
  contend for, so it over-subscribes the machine. Should `Enter-HeavySlot` refuse `-Slots` other than 2 for the shared
  pool, or is `-Slots` left as is (§11)? **(done for c)**
- **R9 (§2 wait budget, §4 H5) Hold time and starvation.** The pool polls every 2 s with no queue. How long do
  `prepare`, `add-dates`, `add-day`, `tick` and `after-children` hold a slot (is `tick` one-shot)? While a DB job holds
  one of the two slots for, say, an hour, every tsc, vitest, pytest run and check-all of four lanes shares the other,
  and a check-all can lose every 2 s race to short runs until its 20-min limit fails it. Expected: the Architect
  states expected H5 hold times and whether exit 75 or check-all `exit 1` under that load is an accepted outcome, so
  I do not report it as a defect, or names a mitigation (in scope or follow-up).

**The hook: scope, parser and refusals**

- **R10 (§5.1, §5.2, A13) Where the hook does not run.** (a) It fails open when `node` is missing, the script file is
  missing (a session whose project directory is a worktree on a pre-T1 branch), the 10 s timeout is hit, or the hook
  exits anything but 2. Confirm this is intended. (b) Project settings are read from the session's project directory:
  a lane session started in a worktree that has not merged main after T1 has no hook. (c) Do PreToolUse hooks cover
  subagents' Bash calls? Expected: A13 also checks a subagent's Bash call and states the rule that each lane merges
  main before lanes 3 and 4 open (or the settings point at main's absolute path). **(done)**
- **R11 (§5.3 step 7) Exempt leading words that run commands.** These allow a heavy run under the current rules:
  `command npx tsc`; `git bisect run npx vitest run x`; `git -c alias.t='!npx tsc' t`; `git rebase --exec 'npx tsc'`;
  `awk 'BEGIN{system("npx tsc")}'`; `sed '1e npx tsc' f`; `codex exec`/`claude -p` asked to run one; `echo 'npx tsc' |
  sh` (no segment matches); `printf ... | xargs sh -c`. The guide makes "any other allowed heavy form" High. Expected:
  for each, refuse (then `command` moves to the prefix list of step 4, and git or awk with an exec form is scanned) or
  documented gap (added to D-T1.6's list and RULES §7). **(done)**
- **R12 (§5.3 steps 1-3) Tokenizer corner cases.** Rule for each, with a K1 row: (a) backslash-newline continues the
  line and is not a newline separator; (b) `#` comment text (`ls # npx tsc`) is not classified; (c) `$( )` and
  backticks inside single quotes are literal, inside double quotes they are classified (`git commit -m 'see
  \`npx tsc\`'` allows, `echo "$(npx tsc)"` refuses); (d) `$'...'` quoting; (e) the standard commit form
  `git commit -m "$(cat <<'EOF'` ... `EOF` `)"` with a heavy word in the body (heredoc removal must happen inside
  the substitution); (f) `<<<` here-strings are not heredocs; (g) an unterminated heredoc or quote: allow, refuse, or
  fail-closed under the prefilter? **(done)**
- **R13 (§5.3 step 8 B and E) Word-boundary bypasses.** Allowed today by `E` (end, whitespace, quote, `)`):
  `npx vitest@1.6.0 run x`, `npx tsc@5 --noEmit`, `node node_modules/typescript/lib/tsc.js`,
  `node node_modules/vitest/vitest.mjs run`, `python -c "import pytest; pytest.main(['backend/tests'])"`. Also, is
  `npx vite build` heavy (it is half of `npm run build`, which H1 refuses)? Expected: `E` gains `@`, `;`, `,`, `/`,
  and `.js|.mjs|.cjs` where they follow the tool name; `pytest.main` is H3; a ruling on `vite build`. Each becomes a
  K1 row. **(done)**
- **R14 (§5.3 steps 5-8) False refusals of normal commands.** Under the rules as written these refuse; say for each
  refuse or allow, with a K1 row: `bash tools/heavy-slot.sh -- npx tsc` and `sh tools/heavy-slot.sh ...` (step 6
  recognises only the wrapper as leading word); `pwsh -NoProfile tools/heavy-slot.ps1 -- ...` (positional script,
  no `-File`); `find . -name tsc`; `kill $(pgrep -f vitest)` and `pkill -f vitest`; `python3 -c "print('pytest')"`;
  `node -e "...vitest..."`; `echo ASSETOPS_HEAVY_SLOT=$ASSETOPS_HEAVY_SLOT` and `printenv ASSETOPS_HEAVY_SLOT`; pytest
  with an option value not in the step 8 list (`--timeout 60 tools/checks/test_a.py` makes `60` a positional that is
  not under `tools/`). Expected in particular: H0 is a token-level assignment test (assignment prefix, `export`/
  `declare`/`env` argument, `$env:NAME =`), not a substring match; and an unknown option is handled one stated way.
  **(done)**
- **R15 (§5.3 H3, D-T1.5) The `tools/` pytest exemption.** (a) `tools/../backend/tests/test_x.py` and
  `./tools/../backend` pass the prefix test; normalize first? (b) `tools/checks/test_estate_guard.py -n 4` is about
  2.5 min at four workers, and check-all runs it alone "to keep peak memory bounded" (`check-all.ps1:18,316`); by hand
  it is unpooled. Is it, or any `-n` run under `tools/`, pooled? **(done)**

**Fast path**

- **R16 (§3.4, §7.1 K5 and K7, A10) The hook guard's cost and flakiness inside check-all.** K7 runs
  `select-tests.py` on a backend file with 352 dependents: 6.1 s on an idle machine, against the guard's 10 s budget,
  and inside check-all it runs beside three other guards. K5 asserts a 150 ms median while check-all's pool loads the
  CPU, so it can fail check-all on a healthy branch. Expected: K7 uses a backend file with few dependents (or a stubbed
  graph) and the guard has a stated budget on this server; K5's hard bound runs only in the standalone run (A7), with a
  loose bound or report-only inside check-all. And R6's method: two runs each is thin against a 3 s threshold; name the
  run count (3 or more) and the statistic. **(done)**

**The document sweep and the proofs**

- **R17 (§5.4, §6, K6) The sweep's scope and its escape.** (a) How does a document show a refused form as an example
  (TESTING.md's new section, explaining what the hook refuses)? Prose without a code span, or an escape marker? (b) If
  the sweep later flags a file outside §6 (`.claude/skills/**`, `ROLE_CONFIG.md`), the Implementer must edit it, but
  the guide counts an unlisted file as a finding; which wins? (Today's grep finds none, so this is a rule question.)
- **R18 (§8) The planted proofs.** (a) V4 says "P2 or P3 fails"; with `>` and no `flock` both should fail; require
  both? (b) No planted proof covers the nesting probe (plant "nested whenever the marker is set": P5 must fail), the DB
  lock (plant "skip `db-job.lock`": P9 must fail), the TERM tree kill (plant "no trap": P7 must fail), H0 (plant H0
  off: K1 rows 31-33 fail) or the fail-closed prefilter (K3). Add V7-V10 or say why the mechanism is covered without
  them. **(done)**
- **R19 (reviewer guide R1, R6, H0) The guide's own probes.** (a) R1 says the check-all-in-pool run is "the one
  real-directory check-all run", but R6 runs check-all four times in scratch worktrees that share the real `D`; which
  holds, and may R6 runs take real slots? (b) After the merge the hook refuses `ASSETOPS_HEAVY_SLOT_DIR=...` (H0), so
  any later re-review or fix round cannot run the guide's hand probes. Is the private directory set only through the
  test files (`node --test`), through a script file (a documented gap), or does H0 allow it on a pooled segment whose
  value is under a `mktemp` directory? **(done)**
- **R20 (§3.2, §3.3 exit codes)** A child that exits 64, 69 or 75 cannot be told from the wrapper's own codes. Is that
  accepted, with the wrapper's stderr line the only way to tell (then say so in TESTING.md), or does the wrapper map
  them? Low.

**If the hook is not approved (the `.claude/settings.json` part is pending the owner)**

- **R21 (§5.1, D-T1.6, A5-A7, A13) What replaces the hook, and its proof.** With no hook, `classify` and `sweepDoc`
  still guard documents (K1, K6, K7, V1, V2, V6) but nothing refuses a run, so TW23's "merged and enforced" would rest
  on the rule alone. Which enforcement replaces it, and what proof do I check? My expectation for each option:
  (1) **Rule only**: K2-K4, V3 and A13 drop; the owner re-decides whether lanes 3 and 4 may open on a rule; I verify
  only the pool (A1-A4, A10-A12) and the sweep. (2) **In-tool tripwires** (vitest `globalSetup`, a pytest plugin, a
  tsc shim) that exit non-zero without a valid `ASSETOPS_HEAVY_SLOT`: proof is a planted unpooled `npx vitest run x`
  and pytest run refused with the message, the pooled form passing, and the select-tests cost of touching conftest or
  `package.json` stated and accepted. (3) **A process audit** (`heavy-slot.sh --audit`, scanning `/proc` for tsc,
  vitest, pytest, chrome and H5 processes with no slot-holding ancestor), run by check-all or on a timer: proof is a
  planted unpooled stand-in process named and a pooled one not, with A13 becoming "the audit finds no unpooled run
  over a working day". Expected: the Architect picks one (or a combination) and rewrites A5-A7, A13 and V3 to match.
  **(done)**

## Implementer pre-flight questions

(none yet)

## Status

Open: 21 (R1-R21). Answered: 0. Handshake: reviewer questions in; implementer pre-flight pending.
