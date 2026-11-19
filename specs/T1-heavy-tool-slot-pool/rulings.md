# T1 rulings

Architect rulings for T1, the heavy-tool slot pool. The design rulings below are rev 1 of `spec.md`
(2026-11-19). The answers to the handshake round (`handshake.md`) and any mid-build ruling are appended in the
sections at the end and folded into `spec.md` in the same change. Each ID has a line in
`.ai/decisions/index-rulings-6.md`.

## Design rulings (rev 1)

- `D-T1.1` **One pool: check-all's two slots.** Heavy tools take the same `slot-1.lock` and `slot-2.lock` in
  `<git-common-dir>/check-all-slots` that check-all takes (PIPE-1 A3). Why: the memory case in the go-to-market
  plan (B03, §2.4) sizes the machine for two heavy holders in total, and a separate pool would allow four.
  Check-all's acquisition moves into `tools/checks/_heavy_slot.ps1`, so there is one pwsh implementation.

- `D-T1.2` **Lock protocol: exclusive `flock`, held by the wrapper only.** pwsh keeps the .NET
  `FileShare.None` open (which is `flock` on Linux, close-on-exec); bash uses `flock(1)` on an fd that the child
  does not inherit. The interop self-test is the proof, and if it fails the slice stops. Why the wrapper and not
  the child tree: if children inherited the lock, an orphan (a Chrome a capture failed to stop) would hold a slot
  and block every lane for 20 minutes. The cost is that a SIGKILLed wrapper's child runs on unpooled, which is
  rare: agents' timeouts send TERM, and the wrapper stops its tree on TERM, HUP and INT. Turning .NET file
  locking off is refused.

- `D-T1.3` **Nesting by a verified marker.** A holder exports `ASSETOPS_HEAVY_SLOT`. A pool entry that finds it
  checks that the named lock is really held before it takes nothing. A stale marker is ignored. This is what keeps
  a pooled command that starts another pooled command (or check-all) from waiting for a second slot. Forging the
  marker, or pointing the pool at a private directory with the test-only `ASSETOPS_HEAVY_SLOT_DIR`, is refused by
  the hook (rule H0).

- `D-T1.4` **Database jobs: the DB lock plus one slot.** A `--db` job takes `db-job.lock` first, then one slot.
  This makes the existing rule of one heavy database job at a time mechanical (B03: "a database job also keeps
  the existing one-at-a-time database rule"). B03's two-slot case ("if it measures above 3.1 GB") waits for the
  DM05 measurement and is out of scope, since a job that needs two slots raises the risk of starvation and
  deadlock and the measurement is not yet made.

- `D-T1.5` **(The pytest scope is revised by D-T1.16.)** **What is pooled.** tsc, vitest, every backend, host or gateway pytest run (not only Postgres
  files), the container and host suite runners, browser captures and heavy database jobs. Guard self-tests
  under `tools/` are not pooled. Why the pytest scope is broad: 199 test files have `postgres` in their name,
  but many Postgres modules do not (for example `test_w401_work_api.py`), and a hook that sees only a command line
  cannot tell them apart. A pooled non-database pytest run costs a few seconds of a slot (the queue model in B03
  gives a mean wait of about 3 s). This widens B03's "backend test files that use Postgres", so it is put to the
  owner below.

- `D-T1.6` **(Superseded by D-T1.11, 2026-11-19.)** **Enforcement: a Claude Code `PreToolUse` hook on Bash, plus the rule.** The hook is
  `.claude/settings.json` running `tools/heavy-slot-hook.mjs`, as B03 specifies. It fails closed when it cannot
  parse a command that looks heavy, and is otherwise open, so a hook defect cannot block unrelated work. Known
  gaps, which RULES §7 still binds: script files, a heredoc fed to a shell, `eval`, aliases, Codex sessions, the
  Monitor tool and a human terminal. In-tool tripwires (in conftest or the vitest config) are deferred, because
  touching the test harness makes select-tests choose the full suite.

- `D-T1.7` **Not pooled: check-all and long-running servers.** Check-all takes its own slot. A demo `serve`,
  the vite dev server and uvicorn would each hold a slot for hours. A capture's servers run outside the pool,
  and the capture itself runs inside it.

- `D-T1.8` **(Superseded by D-T1.11, 2026-11-19; the documents are now checked by inventory check 7.)** **Class fix for copyable commands.** The class is an unpooled heavy command in a document that agents
  copy from. The sweep is `sweepDoc` over the start-path documents, the agent briefs, `backend/TESTING.md` and
  the VPS lane rules. It runs as a guard, so the class stays closed after the first fix.

- `D-T1.9` **select-tests exemptions.** `tools/heavy-slot.sh`, `tools/heavy-slot.ps1` and
  `tools/select-tests.py` join `TOOLS_EXEMPT`, because no backend test runs or reads them (checked with
  `git grep`). Without the exemption, T1's own slice-end selection would be the full backend suite, which runs
  against the test-suite policy and tests nothing T1 changes.

- `D-T1.10` **Windows by parity, not hardware.** The pwsh wrapper uses the exact .NET call that check-all already
  uses on Windows. `heavy-slot.sh` without `flock` hands over to pwsh. `.gitattributes` is not changed, because
  that file is ALWAYS_FULL in select-tests. Windows hardware verification is out of scope, since the build machine
  is the Linux VPS.

## Rev 2 rulings (2026-11-19: owner option C and handshake round 1)

- `D-T1.11` **Enforcement is option C: in-tool tripwires (owner).** The owner's words: "C for T1"
  (`owner/owner-playwright-and-t1-c-2026-11-19.md`). Each heavy tool refuses to start, with exit 69, unless it
  runs inside a held slot:
  - tsc: a `node_modules/.bin` shim, reinstalled by `postinstall`;
  - vitest: `vite.config.ts`;
  - pytest with a database: both conftests;
  - the container runners;
  - the 30 browser-launching scripts;
  - the database entry points.

  An inventory guard keeps the class closed. This supersedes the hook (D-T1.6) and the document classifier
  (D-T1.8). There is no `.claude/settings.json`.

  Why C is stronger than the hook: it binds Codex, subagents and human terminals, which the hook could not see.
  It needs no session restart, and it has no shell parser to bypass. The bypasses that remain are deliberate
  ones (§5.2 gaps). Its costs: it touches ALWAYS_FULL files (D-T1.17), and the tsc shim lives in `node_modules`,
  outside git. The post-merge install and the `-Full` guard cover that second cost.

- `D-T1.12` **Canonical pool directory (fixes R2 and R3).**
  - Every caller gets `D` from `git rev-parse --path-format=absolute --git-common-dir`, run with every `GIT_*`
    variable removed, then canonicalised with `realpath` and joined with `check-all-slots`.
  - Markers compare as canonical paths.
  - `ASSETOPS_HEAVY_SLOT_DIR` is honoured by the wrappers only (for self-tests) and never by a tripwire.
  - check-all's resolution changes to the same function. The result is identical for every checkout here.

- `D-T1.13` **A nested `--db` refuses at once (fixes R4).** A `--db` entry inside a held slot without a valid DB
  marker exits 69 with "put --db on the outermost wrapper". So no entry that holds a slot ever waits for the DB
  lock, and the lock order is always DB, then slot. Bounded deadlock is not accepted.

- `D-T1.14` **Holder ancestry (R5).** On Linux, a marker passes only when the owner file's `pid=` is the caller
  or an ancestor of the caller. This closes the orphan case and the forged-marker case. Windows skips this check
  (documented).

- `D-T1.15` **The child stays in the wrapper's process group (R6, I13).** There is no `set -m`. A group kill stops
  both the wrapper and the child. A signal to the wrapper alone kills the child's tree, found through
  `/proc/<pid>/task/*/children`. stdin is kept with `<&0`. SIGTTIN cannot occur, because the child is in the
  foreground group.

- `D-T1.16` **Pytest is pooled when `ASSETOPS_TEST_DATABASE_URL` is set (revises D-T1.5).**
  - This is B03's own scope: "backend test files that use Postgres".
  - A tripwire sees the environment at run time, so it can tell a database run from a plain one, which the hook
    could not. Without the URL, the Postgres modules skip and the run is light.
  - Owner question 1 of rev 1 falls away.

- `D-T1.17` **T1's slice-end checks are a smoke set, not full suites.** T1 touches ALWAYS_FULL files: both
  conftests, the container runner, `docker-compose.test.yml`, `vite.config.ts` and `package.json`. So
  select-tests reports `full`.
  - The change in those files is a start-up guard. P-T1 to P-T7 and the pooled smoke set prove it.
  - Under the owner's test policy (2026-11-19: isolated, smoke and regression tests while building, full suites
    at key milestones), the full backend and frontend suites run at the next milestone run, pooled with `--db`.

- `D-T1.18` **Starvation under a long database job is accepted (R9).** Expected hold times:
  - `prepare` holds about 2.0-2.35 h (four Sites, `backend/TESTING.md` slow tier);
  - `add-dates` and `add-day` hold minutes to tens of minutes;
  - `tick` is one-shot, minutes;
  - `after-children` is a development probe.

  While a prepare holds one slot, every other heavy run shares the other slot. A wait timeout (exit 75), or
  check-all's `exit 1` after 20 minutes under that load, is an accepted outcome, not a defect. Mitigation: the
  coordinator schedules database jobs (one at a time, not on demo days; PIPE-2 shortens them). A FIFO queue is a
  follow-up if starvation is seen.

## For the owner (defaults applied, W3)

1. **Two slots for a large database job (D-T1.4).** Deferred until the DM05 measurement. Default: one slot plus
   the DB lock.
2. **Humans are refused too (D-T1.11).** An unpooled `npx vitest` or `npx tsc` in your own terminal is refused,
   and the message gives the pooled form. Default: yes, since that is what makes the pool hold.

Rev 1 questions 1 (pytest scope) and 2 (Codex) are closed by option C (D-T1.16, D-T1.11).

## Handshake answers (round 1)

Every answer below is folded into `spec.md` rev 2. "Superseded" means that the question concerned the hook or
the classifier, which option C removes; no work follows from it.

### Reviewer

- **R1.** Accepted.
  - Added P4b: pwsh outer with a bash nested entry, and the `Enter-HeavySlot` (check-all) path with a bash
    nested entry.
  - Added P2c: a race between a bash and a pwsh entry, N = 20 iterations in the test; exactly one wins each
    time.
  - Repeat count: P2 and P3 are single cases, and P2c carries the repetition.
- **R2.** Defect, fixed (D-T1.12). Both sides use the same git command with `GIT_*` removed, then `realpath`,
  and compare strings. P4c runs main checkout to worktree, the reverse, and through a symlink.
- **R3.** Defect, fixed (D-T1.12). Every `GIT_*` variable is removed for the git call, in the wrappers,
  check-all and the tripwires (P5b). check-all's resolution may change; the result is identical here. The
  override cannot bypass the pool either, because tripwires ignore it (P-T2).
- **R4.** Defect, fixed (D-T1.13). The nested `--db` exits 69 at once (P9b). The guide's R1 now expects an
  immediate 69, not a timeout.
- **R5.** Fixed rather than accepted (D-T1.14). The Linux ancestry check applies to wrappers, check-all and
  tripwires (P5c, P-T3). Windows skips it, as documented.
- **R6.** Fixed (D-T1.15).
  - stdin is inherited through `<&0` (P13).
  - There is no separate process group, so there is no SIGTTIN or SIGTSTP problem.
  - Ctrl-C reaches the whole foreground group.
  - The Claude Bash tool gives no controlling tty. Either way, the design does not depend on one.
- **R7.**
  - (a) Accepted: every external command runs before the first lock open; after it, the wrapper uses builtins
    only.
  - (b) Added P6b (pwsh wrapper SIGKILL) and P6c (the `Enter-HeavySlot` path SIGKILL with a child, checked with
    `/proc/<child>/fd`). A whole check-all run is not used in the self-test, because it would cost a minute per
    run. P6c tests the same module and the same .NET open.
  - (c) Windows handle inheritance is checked by inspection, as you planned.
- **R8.**
  - (a) Accepted. A probe can push an acquirer to the next slot or to one more 2 s poll. The ancestry check
    runs before the probe, which keeps probes rare.
  - (b) A probe opens with `Open`, never creates the file, and treats a missing file as free (I12d).
  - (c) `Enter-HeavySlot` refuses `-Slots` above 2 (P15). `-Slots 1` stays allowed.
- **R9.** D-T1.18: the hold times are stated there. Exit 75, or check-all `exit 1` under a long database job,
  is accepted. A FIFO queue is a follow-up.
- **R10.** Superseded: there is no hook. The equivalent question, where enforcement does not reach, is answered
  in A16:
  - the tsc shim works machine-wide once installed;
  - the vitest, pytest, capture and database tripwires reach a lane only after it merges main, so each lane
    merges main before its next heavy command, and lanes 3 and 4 open after that.

  Subagents, Codex and humans are all covered, because the check runs in the tool.
- **R11, R12, R13, R14.** Superseded: there is no shell classifier.
  - Two of the forms R13 lists remain reachable and are documented gaps: `node
    node_modules/typescript/lib/tsc.js` and running vitest through its `.mjs` directly. Each takes deliberate
    effort.
  - `vitest@1.6.0` through npx still loads `vite.config.ts`, so it is refused.
  - `pytest.main(...)` with a database URL still runs the conftest, so it is refused.
  - `npx vite build` alone stays out of scope (D-T1.7). It is not in B03, and `npm run build` is refused through
    tsc.
- **R15.** (a) Superseded: there are no path prefixes. (b) Accepted gap: a hand-run of guard tests under
  `tools/` is unpooled. check-all runs them inside its slot.
- **R16.** The hook guard, K5 and K7 are gone.
  - The new always-on guard is static and runs in under 2 s.
  - The pool self-test runs only when its trigger rule selects it.
  - R6 method: 3 runs each, comparing medians.
- **R17.**
  - (a) A document shows a refused example on a line that contains the word `unpooled` or `refused`; inventory
    check 7 skips such lines.
  - (b) The scope is the §6 file list, and an edit outside it is a finding. If check 7 is ever widened, the list
    widens in the same change.
- **R18.**
  - (a) V5 now requires both P2 and P3 to fail.
  - (b) Added:
    - V7: nesting whenever a marker is set, caught by P5;
    - V8: skipping the DB lock, caught by P9;
    - V9: no TERM trap, caught by P7;
    - V3 and V4: the tripwire's directory and ancestry checks.

    The H0 and prefilter proofs are superseded.
- **R19.**
  - (a) A check-all run takes a real slot like any check-all run, and is allowed when `--status` shows a slot
    free (I11c). That includes R6's scratch-tree runs. All other lock probes use the self-test's temp repository.
  - (b) Superseded: there is no H0. The override is harmless, because tripwires ignore it.
- **R20.** Accepted: the codes are not remapped. The wrapper's stderr line is the way to tell them apart, and
  TESTING.md says so.
- **R21.** Answered by the owner's choice: option C (D-T1.11). Its proof:
  - P-T1 to P-T7, including a planted unpooled run and the pooled form passing, live for vitest (P-T6) and on a
    fake install for tsc (P-T5);
  - the inventory guard and V1-V4;
  - A12/D-T1.17, which states the select-tests cost;
  - A16, which replaces the old A13.

### Implementer

- **I1.** Default (a): the `tools/check-architecture.ps1` exclusion becomes `_*.ps1`.
- **I2.** Accepted. A `.ps1` first word runs through `(Get-Process -Id $PID).Path -NoProfile -File` (P14).
- **I3.** Accepted. Only the `pwsh -NoProfile -File` form is supported, and a missing `--` exits 64. The
  `-name:value` split is a documented limitation.
- **I4.** Your default is adopted:
  `( exec {slotfd}>&-; [db] exec {dbfd}>&-; exec "$@" ) <&0 &`.
- **I5.** (a) Superseded: there is no hook suggestion. (b) Accepted: a wrapped first word of `setsid` exits 64
  with "put setsid/nohup before the wrapper" (P12).
- **I6.** Superseded: there is no npm parsing.
- **I7.** Accepted. `mechanism_dataset.py ensure` is added. `demo_combined_drain.py` and `demo_combined_rows.py`
  stay out.
- **I8.** (a) Accepted. Every line you list is rewritten (spec §6). (b) Superseded: there is no span sweep. Check
  7 is line-based.
- **I9.** Accepted. Line 7 of the lane rules is reworded the same way as RULES §7.
- **I10.** Accepted. The cases run concurrently, each in its own temp repository, and every spawn scrubs the
  four variables.
- **I11.**
  - (a) The commit plan is per spec §0, with the tripwires as commit 2.
  - (b) Your default: the handshake and closing commits do not count.
  - (c) Your default: check-all runs are allowed when `--status` shows a slot free, and V10 runs with the plant
    uncommitted.
- **I12.** Defaults (a) to (e) are adopted as written; they are in spec §2 and §3.2.
- **I13.** You are right that a group kill sparing the child widens D-T1.2. `set -m` is dropped (D-T1.15). P7b is
  added.
- **I14.** Superseded: there is no `.claude/settings.json`.
- **I15.** Accepted. `Get-SelfTestDecision` is generalised and gets four new cases, and `$heavySlotFiles`
  includes the check modules and the shim installer.

**Still blocking coding: none.**

The vitest tripwire's `import.meta.url` resolution has a fixed fallback (spec §5.3) and is not an open
question. If neither form works, that is a mid-build stop under RULES §4 item 7.

## Mid-build rulings

(None yet. Each one stops only the affected part (RULES §4 item 7). If the done criteria change, the reviewer
guide is updated too.)
