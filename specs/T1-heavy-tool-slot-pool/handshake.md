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
  backticks inside single quotes are literal, inside double quotes they are classified (``git commit -m 'see `npx tsc`'`` allows, `echo "$(npx tsc)"` refuses); (d) `$'...'` quoting; (e) the standard commit form
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

Implementer (Claude, pre-flight against `main` f074a4cc5; branch head 3d5b67e82 already contains `main`, so the §0
merge is a no-op). Tools: util-linux `flock` 2.41.3, pwsh 7.7.0, node v24.22.3, git 2.53.0, bash 5.3.9.

**Lock interop (§2, D-T1.2), scratch file only: passes.** (A) pwsh `[IO.File]::Open(p,'OpenOrCreate','ReadWrite',
'None')` held: bash `exec {fd}>>p; flock -n -x $fd` returns 1 (busy); free after pwsh exits. (B) bash `flock` held:
the pwsh open throws `System.IO.IOException` ("being used by another process"); free after bash exits. (C)
`/proc/locks` shows the .NET lock as `FLOCK ADVISORY WRITE`, so it is `flock(2)`. (D) a pwsh holder that exits
without `Dispose` while its `Start-Process` child lives: the lock is free (close-on-exec, no inheritance). (E) bash
child started with `{fd}>&-` after its parent exits: free. (F) the same without `{fd}>&-`: the child keeps the lock
(the V5 premise holds). (G) a second `FileShare.None` open of a file in the same pwsh process throws `IOException`.

**Already asked by the Reviewer** (no separate number; my implementation default in brackets): R2 [both sides
resolve `D` with `git -C <repo> rev-parse --path-format=absolute --git-common-dir` (git 2.53 here; both checkouts
print `/opt/assetecon/AssetOpsV1/.git`) and compare the strings exactly; no symlink resolution on either side],
R4 [refuse at once, exit 69], R5 [accepted residual risk], R8b [see I12], R10 (also: in a pre-T1 worktree the hook's
own suggestion `tools/heavy-slot.sh -- ...` fails with "No such file", so every lane must merge main before its next
heavy command, or the suggestion names `/opt/assetecon/AssetOpsV1/tools/heavy-slot.sh`, which resolves the same `D`),
R13 (`vite build`), R14 (`bash tools/heavy-slot.sh`), R16 (I measured K7 at 6.3, 6.7 and 6.4 s, load 1.7).

- **I1 (§3.1) `tools/checks/_heavy_slot.ps1` fails check-architecture as placed.** `tools/check-architecture.ps1:58-72`
  discovers every `tools/checks/*.ps1` except `_common.ps1` and fails "is not registered in
  tools/check-architecture.ps1, so it never runs". Expected: either (a) the exclusion becomes `_*.ps1` (adds
  `tools/check-architecture.ps1` to the files I touch, one line), or (b) the module moves to `tools/_heavy_slot.ps1`
  (then it joins `TOOLS_EXEMPT` and `$heavySlotFiles`). My default: (a).
- **I2 (§3.2) `heavy-slot.ps1` cannot start a `.ps1` command.** A bare name is resolved with `Get-Command
  -CommandType Application`, which does not return scripts, and `Process.Start` with `UseShellExecute=false` cannot run a
  `.ps1` on either OS. That breaks K1 row 19 (`... heavy-slot.ps1 -- tools\run-host-tests.ps1 -- ...`) and every pooled
  rewrite of the TESTING.md PowerShell lines (I8). Expected: when the first command word ends in `.ps1` and names a
  file, the child is `(Get-Process -Id $PID).Path -NoProfile -File <script> <args>`. Add a P case
  (`heavy-slot.ps1 -- <tmp>/x.ps1 a b` sees both arguments and its exit code passes through).
- **I3 (§3.2) Only the `pwsh -File` form keeps the `--`.** Tested on pwsh 7.7: `pwsh -NoProfile -File s.ps1 -Db --
  npx tsc -- -q` gives `$args` with both `--`, but in-session `& s.ps1 -Db -- npx tsc -- -q` drops the **first** `--`,
  so the "missing `--` is exit 64" rule refuses every in-session call. Also `-File` splits a `-name:value` token
  (`-c:1` arrives as `-c`, `1`); `--tb=short` survives. Expected: only the `pwsh -NoProfile -File tools/heavy-slot.ps1`
  form is supported and documented (TESTING.md's PowerShell lines use it), the usage line says so, and the colon split
  is a documented limitation. Or: accept a missing `--` when the first non-option word is not an option.
- **I4 (§3.3) The child start line as written fails on every non-`--db` run.** `"$@" {slotfd}>&- {dbfd}>&- &` with
  `dbfd` unset (or empty) is `bash: dbfd: ambiguous redirect`, exit 1, with or without `set -u` (tested bash 5.3).
  Expected (my default): `( exec {slotfd}>&-; <if db> exec {dbfd}>&-; exec "$@" ) &`, so `$!` is the command's own PID
  and only open fds are closed.
- **I5 (§5.2) The refusal's suggestion breaks on assignments and prefix commands.** `tools/heavy-slot.sh --
  <segment>` for K1 row 12 gives `tools/heavy-slot.sh -- PYTHONPATH=a:b .venv/bin/python ...` (the wrapper tries to
  run `PYTHONPATH=a:b`), and for row 25 puts `setsid nohup` inside the wrapper: `setsid` forks when its caller leads a
  process group (the child does, under `set -m`), so the wrapper returns at once, frees the slot and the job runs
  unpooled. Expected: (a) the suggestion hoists the step-4 prefix (assignments, `env`, `setsid`, `nohup`, `timeout`,
  `nice`, `time`, `stdbuf`, `exec`) before the wrapper, giving `PYTHONPATH=a:b tools/heavy-slot.sh -- .venv/bin/python
  -m pytest ...` and `setsid nohup tools/heavy-slot.sh --db -- .venv/bin/python tools/demo_combined.py ... > log 2>&1`
  (§4's form), with K2 rows for both; (b) a pooled segment whose command after `--` starts with `setsid` (or `nohup`)
  is refused, under the rule of the inner command, with the hoisted suggestion. Confirm both.
- **I6 (§5.3 step 8) `npm [opts]` is undefined.** K1 row 4 (`npm --prefix frontend test`) needs to know that
  `--prefix` takes a value. Expected (my default): skip `--x=y`, flags starting with `-`, and the value after `--prefix`,
  `-C`, `--workspace`, `-w`, `--userconfig`, `--cache`; the next word is the npm command.
- **I7 (§5.3 H5) One heavy database entry point is missing.** `tools/mechanism_dataset.py ensure` builds the
  templates when they do not match (`tools/mechanism_dataset.py:396-408`, "build it now, with no budget"); it is not in
  H5 (`status` and `drop` rightly are not). `tools/demo_combined_drain.py` and `demo_combined_rows.py` exist but are
  helpers that the parent runs; I leave them out. Expected: add `ensure` to H5 with a K1 row; confirm the two helpers
  stay out.
- **I8 (§5.4, §6) TESTING.md: the sweep refuses more lines than §6 lists.** By the §5.3 rules: 19; all **five**
  `tools\run-host-tests.ps1` lines 147, 150, 153, 156, 159 (§6 says four); 162; 163-164 and 167-168 (inline spans that
  run over a line break); the fenced block 210-213 (`tools\run-backend-suite-in-container.ps1`, H3 always); 347. Lines
  24-25 are single-word spans and are not swept. Expected: (a) all of these are rewritten (fenced 210-213 to
  `pwsh -NoProfile -File tools/heavy-slot.ps1 -- tools\run-backend-suite-in-container.ps1 ...`, which needs I2); (b)
  an inline span that crosses a line break is joined into one span (CommonMark) and reported at its first line.
- **I9 (§6) The lane rules' Guards line keeps the old wording.** `.agent/lane-rules-vps-2026-11-12.md:7` says
  check-all "allows 2 runs at once machine-wide (a third waits for a slot by itself)", the clause §6 rewords in RULES
  §7. Expected: reword it the same way (one clause); §6 lists only the vitest and Database lines.
- **I10 (§7.2) The pool self-test exceeds 30 s run serially, and inherits a real marker inside check-all.** P2, P3,
  P6, P7, P8 and P9 each wait 3-6 s, and about eight pwsh starts add 0.5-1 s each: roughly 30-35 s in sequence.
  Inside check-all every spawned case would also inherit check-all's real `ASSETOPS_HEAVY_SLOT` and print
  `ignoring stale` (its directory is not the temp `D`). Expected (my defaults): the cases run concurrently
  (`node:test` `concurrency`, each case its own `mkdtemp` directory), and every spawn removes `ASSETOPS_HEAVY_SLOT`,
  `ASSETOPS_HEAVY_DB` and `DOTNET_SYSTEM_IO_DISABLEFILELOCKING` from its environment unless the case sets them. The
  same scrub applies to K2-K5 spawns.
- **I11 (§10, §0.3, §8) The commit plan and the real-slot rule.** (a) Commit 1 ("pool and check-all") would add both
  `Add-Guard` lines while `test_heavy_slot_hook.mjs` arrives in commit 2, so check-all at commit 1 fails ("a guard
  that cannot run is a failure"); W2 also asks for tests first. My default: commit 1 = shared module, both wrappers,
  `test_heavy_slot_pool.mjs`, check-all with the slot change, the pool self-test guard and the SKIP line; commit 2 =
  hook, settings, `test_heavy_slot_hook.mjs` and the hook guard line in check-all; commit 3 = docs and select-tests.
  check-all then changes in two commits; `-Base <head>~1` (A10) still measures commit 3 alone. (b) Do this handshake
  commit and the closing commit (packet, spec `Status`, `.ai/state` entry) count against "three commits at most"? My
  default: no. (c) §0.3 says nothing I run may hold a real slot for more than a few seconds, but §10 runs check-all
  once and V6 a second time (about a minute each of a real slot). My default: check-all runs are exempt, run only when
  `--status` shows a free slot; V6 is run with the plant uncommitted (check-all's diff includes the working tree).
- **I12 (§3.1-§3.3) Texts and edge cases the spec leaves open.** My defaults, to confirm or replace: (a) the wrappers'
  first-wait line: `heavy-slot: both heavy slots are busy (tools/heavy-slot.sh --status); waiting up to <n> s.`, and
  for the DB lock `heavy-slot: another database job holds db-job.lock; waiting up to <n> s.`, each printed once, to
  stderr; (b) Ctrl-C: both wrappers exit 130 after stopping the child tree; (c) `--status` prints `slot-1`, `slot-2`
  and `db-job` always (a missing file is `free`), plus any other existing `slot-N.lock`; (d) extends R8b:
  `FileNotFoundException` and `DirectoryNotFoundException` are subclasses of `IOException`, so `Test-HeavyLockHeld`
  as specified ("true when the open throws `IOException`") reports a missing file as **held**. Default: open with
  mode `Open` (never create), catch the two not-found exceptions first and return `$false`; bash probes open with
  `<` and treat a missing file as free; (e) a label is reduced to one line (newlines and `=` to spaces) before it
  is written to the owner file.
- **I13 (§3.3 `set -m`, D-T1.2) A group kill now spares the child.** Extends R6. Without `set -m` the child shares the
  wrapper's process group, so a SIGKILL (or TERM) sent to the Bash tool's whole group stops both. With `set -m` the
  child has its own group: a group SIGKILL kills the wrapper only and the child runs on unpooled. That widens D-T1.2's
  accepted case from "a SIGKILLed wrapper, rare" to "any group kill". I could not find how the Claude Bash tool stops
  a timed-out command. Expected: either accept this (and record it in the spec), or drop `set -m`, keep the child in
  the wrapper's group, and on TERM/HUP/INT stop the tree by walking `/proc/<pid>/task/*/children` (`pkill -P`
  recursively). P7 holds either way; P6 kills the wrapper by PID, not by group, so it does not see the difference.
- **I14 (§5.1, owner approval pending) Commit `.claude/settings.json` on the branch?** Extends R21 (which asks what
  replaces the hook if it is refused). Until the owner answers: my default is to build everything, commit
  `.claude/settings.json` on the branch (no running session reads it, since every session's project directory is the
  main checkout, and it acts only after the merge and a restart), and mark the merge as gated on the owner's approval
  in the packet. Or should it stay uncommitted, with K4 and V3 recorded as pending?
- **I15 (§3.4) The pool self-test's trigger rule has no self-test.** check-all proves its estate trigger with fixed
  cases (`-SelfTestSelection`, `tools/check-all.ps1:83-133`); §3.4 adds a second trigger rule with none. Default:
  generalise `Get-SelfTestDecision` with a file-list parameter, use it for both, and add four cases (pool file
  changed, none changed, `-Full`, diff error) to `-SelfTestSelection`. Also: should `tools/heavy-slot-hook.mjs` and
  `tools/select-tests.py` join `$heavySlotFiles` if K7 moves into the pool self-test (R16)? Default: yes, if it moves.

## Status

Open: 0. Answered: 36 (R1-R21, I1-I15), in `rulings.md` "Handshake answers (round 1)", folded into `spec.md` rev 2.
Handshake: **closed** (2026-11-19). Coding may start.
