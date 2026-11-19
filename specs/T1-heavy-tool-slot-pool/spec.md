# T1: the heavy-tool slot pool, enforced (implementer spec)

Status: live. Architect spec rev 1, 2026-11-19. Branch `task/T1-heavy-tool-slot-pool`
(worktree `/opt/assetecon/AssetOpsV1-t1`). Review depth: discovery (new mechanism, W5).
Reviewer guide: `reviewer-guide.md`. Questions: `handshake.md`. Answers and design rulings:
`rulings.md` (D-T1.1 to D-T1.10), folded into this file.

Sources: delivery plan row `T1` (`Docs/demo-sprint/product-direction-layer4/delivery-plan.md:59`, pack branch);
the retired go-to-market plan §2.4 "B03" (same slice, 2-3 units); PIPE-1 A3
(`Docs/engineering/build-pipeline-and-checks-speedup.md`); owner TW23 (item 7,
`owner/owner-sitting1-answers-2026-11-18.md`): four build lanes, with B03 merged and enforced before
lanes 3 and 4 open; owner "yes, start T1 now" (`.agent/owner-start-t1-2026-11-19.md`).

`USER_REVIEW_REQUIRED: false` (tooling only; no screen, copy or semantics). The three default rulings in
`rulings.md` "For the owner" are applied pending the owner's answer (W3).

## 0. Before you start

1. `git merge main` (main has RULES §4 items 6-7; the worktree copy `.agent/RULES-main-2026-11-19.md` is
   only a convenience). Never rebase.
2. Pre-flight this spec against `main` together with the Reviewer's questions (RULES §4 item 6): write your
   questions in `handshake.md` "Implementer pre-flight". Code starts only after `rulings.md` answers them.
3. No suites, no DBs, no Docker. Stay off ports 5490 and 8990. Every self-test in this slice uses a private
   temp slot directory; nothing you run may hold a real slot for more than a few seconds.

## 1. Outcome and why

With four build lanes, agents running `tsc`, vitest, Postgres test files, browser captures and the heavy
database job at the same time exhaust the server's memory (no swap) and stall it. Today only check-all takes
a slot (PIPE-1 A3: `tools/check-all.ps1:202-221`, a lock file per slot in `<git-common-dir>/check-all-slots`,
opened with `FileShare.None`, 2 slots, 2 s poll, 20 min limit). T1 puts every heavy tool through **the same
two slots**, and a project hook refuses an unpooled run, so the memory worst case in the go-to-market plan
(11.6 GB with the pool) holds. Lanes 3 and 4 open when T1 is merged and the post-merge live check (§9, A13)
passes.

## 2. Structure: the records and the rules

**Slot directory** `D` = `$ASSETOPS_HEAVY_SLOT_DIR` if set (test use only, D-T1.3), else
`<absolute git-common-dir of the script's own repository>/check-all-slots`, else (no git)
`<system temp>/assetops-check-all-slots`. All 61 checkouts on this server share
`/opt/assetecon/AssetOpsV1/.git`, so `D` is machine-wide. Resolve from the script's location
(`$PSScriptRoot/..`, `"$(dirname "$0")/.."`), never from the caller's cwd.

| File in `D` | Meaning | Authority |
| --- | --- | --- |
| `slot-1.lock`, `slot-2.lock` | a heavy slot; held = an exclusive advisory lock on an open file | the lock, nothing else |
| `db-job.lock` | the one-at-a-time heavy database job (D-T1.4) | the lock |
| `slot-N.owner`, `db-job.owner` | diagnostics only: `pid=`, `child=`, `label=`, `since=` (UTC ISO 8601), `cwd=`, `db=yes|no`, one per line | never authority; may be stale |

**Lock protocol (D-T1.2).** Exclusive, non-blocking `flock(2)` on the file, polled every 2 s.
- pwsh: `[IO.File]::Open($path, 'OpenOrCreate', 'ReadWrite', 'None')` exactly as check-all does today. .NET on
  Linux implements `FileShare.None` as `flock(LOCK_EX|LOCK_NB)` and opens with close-on-exec; on Windows it is a
  share-mode-0 handle, not inherited by children. A held lock throws `System.IO.IOException`.
- bash (Linux): `exec {fd}>>"$path"` then `flock -n -x "$fd"` (util-linux `/usr/bin/flock`). Never `>` (no
  truncation). Children never inherit the fd: the command is started with `{fd}>&-`.
- The interop self-test (§7, P2 and P3) is the proof that the two see each other. If it fails on this server,
  stop with `SPEC_AMBIGUITY`; do not substitute another mechanism.
- `DOTNET_SYSTEM_IO_DISABLEFILELOCKING` set to anything non-empty turns .NET locking off: both wrappers refuse to
  run (exit 69, `heavy-slot: refused: DOTNET_SYSTEM_IO_DISABLEFILELOCKING is set; the slot locks would not hold.`),
  and check-all fails with the same text before taking its slot.

**The holder is the wrapper process, not its children.** A slot is released when the wrapper (or check-all)
exits, however it exits, because the kernel drops the lock with the last fd. On SIGTERM, SIGHUP or SIGINT the
wrapper stops its child's whole process tree first (§3.3). On SIGKILL of the wrapper the slot is released at
once and the child may run on unpooled; this is accepted (D-T1.2: a leaked lock would block every lane for up to
20 min, an orphan over-subscribes once). Orphans such as a Chrome a capture script failed to stop therefore never
hold a slot.

**Nesting marker (D-T1.3).** A process that holds a slot exports `ASSETOPS_HEAVY_SLOT=<absolute path of its
slot-N.lock>`; a holder of the DB lock also exports `ASSETOPS_HEAVY_DB=<absolute path of db-job.lock>`. A pool
entry (either wrapper or check-all) that finds `ASSETOPS_HEAVY_SLOT` set checks it:
- valid when its directory equals `D`, its name matches `^slot-[1-8]\.lock$`, and a non-blocking lock attempt on it
  fails (someone holds it): the entry is **nested** and takes no slot. The wrapper `exec`s the command (bash) or
  runs it directly (pwsh); check-all prints `check-all: inside a held heavy slot (<path>); not taking another.`
- otherwise **stale**: release the probe lock if it was taken, print
  `heavy-slot: ignoring stale ASSETOPS_HEAVY_SLOT=<value>` to stderr, and acquire normally.
- `--db` when nested: if `ASSETOPS_HEAVY_DB` is valid by the same test (name `db-job.lock`), nothing more is
  taken; else acquire `db-job.lock` only (no second slot), within the same wait budget.
Forging the marker is refused by the hook (rule H0). The test-only `ASSETOPS_HEAVY_SLOT_DIR` is refused the same
way, so an agent cannot point the pool at a private empty directory.

**Acquisition order and deadlock freedom.** Order is always `db-job.lock`, then the lowest free slot. Every holder
takes at most one slot and at most the DB lock. Nested entries take nothing (or only the DB lock). So no process
ever waits for a second slot while holding one, and every wait is bounded by the wait budget (default 1200 s,
exit 75). Heavy database jobs take one slot (D-T1.4; two slots only after the DM05 measurement, out of scope).

## 3. The pool: files and interfaces

### 3.1 `tools/checks/_heavy_slot.ps1` (new; the one pwsh implementation)

Dot-sourced by `tools/check-all.ps1` and `tools/heavy-slot.ps1`. Functions (names fixed; internals yours):

| Function | Contract |
| --- | --- |
| `Get-HeavySlotDir([string]$RepoRoot)` | `D` as in §2; creates it (`New-Item -ItemType Directory -Force`) |
| `Test-HeavyLockHeld([string]$Path)` | `$true` when an open with `FileShare.None` throws `IOException`; otherwise disposes the probe and returns `$false` |
| `Enter-HeavySlot -SlotDir <s> [-Slots 2] -WaitSeconds <n> [-Db] [-Label <s>] [-Announce <s>]` | Applies the marker test, then acquires in the §2 order with a 2 s poll. Prints `-Announce` once (to the host) the first time it has to wait. Returns `[pscustomobject]@{ Nested; SlotPath; SlotStream; DbPath; DbStream; WaitedSeconds }`, or `$null` on timeout (having released anything it took). Writes the `.owner` file(s) after acquiring |
| `Exit-HeavySlot $Handle` | Disposes the streams; deletes an `.owner` file only if its `pid=` is this process. `$null`-safe |
| `Write-HeavySlotOwner $Path $Fields` | writes the owner file (UTF-8, LF) |
| `Assert-HeavySlotLocking` | throws the D-T1.2 refusal text when `DOTNET_SYSTEM_IO_DISABLEFILELOCKING` is non-empty |

### 3.2 `tools/heavy-slot.ps1` (new)

```
pwsh -NoProfile -File tools/heavy-slot.ps1 [-Db] [-SlotWaitSeconds <n>] [-Label <text>] -- <command> [args...]
pwsh -NoProfile -File tools/heavy-slot.ps1 -Status
```
- A plain script with no `param()` block, no `[CmdletBinding()]`: it parses `$args` itself, like
  `tools/run-host-tests.ps1`, so `--noEmit`, `-q`, `-k x` and a second `--` reach the command untouched. Options
  are read only before the first `--`; an unknown option, a missing `--` or an empty command is a usage error
  (exit 64, one line naming the form above).
- Default wait 1200 s. Default label: the first two words of the command.
- Runs the command as a child (`System.Diagnostics.Process`, `UseShellExecute = $false`, no redirection, each
  argument through `ArgumentList`; a bare name resolved with `Get-Command -CommandType Application`, first hit).
  Exports the marker variables in the child's environment only.
- SIGTERM and SIGHUP: a `PosixSignalRegistration` handler (pwsh 7.2+, as `tools/check-all.ps1:140-175`) kills the
  child tree (`Kill($true)`); the wrapper then exits 143 (TERM) or 129 (HUP). Ctrl-C unwinds through `finally`
  and kills the child tree. Windows PowerShell 5.1 is not supported (pwsh 7 only), as today.
- Exit code: the child's; 64 usage; 69 refused or unavailable; 75 no slot within the wait
  (`heavy-slot: no slot came free in <n> s (-SlotWaitSeconds).`).
- `-Status`: one line per lock file, `slot-1: free` or `slot-1: busy pid=<p> child=<c> label=<l> since=<t> cwd=<d>`;
  a busy lock whose owner file is missing or whose `pid=` is not alive prints
  `slot-1: busy, holder unknown (owner file stale); find it with: fuser -v <path>`. Exit 0.

### 3.3 `tools/heavy-slot.sh` (new, LF, mode 100755: `git update-index --chmod=+x`)

```
tools/heavy-slot.sh [--db] [--wait-seconds <n>] [--label <text>] -- <command> [args...]
tools/heavy-slot.sh --status
```
- `#!/usr/bin/env bash`, `set -u` (not `-e` around the wait loop). Same options, defaults, messages (with the bash
  option names), exit codes and status format as §3.2.
- No `flock` on `PATH` (Git Bash on Windows): `exec pwsh -NoProfile -File "<dir>/heavy-slot.ps1"` with the options
  translated (`--db` to `-Db`, `--wait-seconds` to `-SlotWaitSeconds`, `--label` to `-Label`, `--status` to
  `-Status`). No pwsh either: exit 69.
- Run: `set -m`; `"$@" {slotfd}>&- {dbfd}>&- &`; `child=$!`; rewrite the owner file with `child=`;
  `trap` TERM, HUP, INT: `kill -TERM -- -$child`, wait up to 5 s, then `kill -KILL -- -$child`, exit 128+signal.
  Loop on `wait "$child"` until it has really exited (a trapped signal interrupts `wait`). `trap EXIT` removes the
  owner file only if its `pid=` is `$$`.
- Nested (§2): `exec "$@"`.

### 3.4 `tools/check-all.ps1` (edit; behaviour unchanged for a run that takes a slot)

- Dot-source `tools/checks/_heavy_slot.ps1` after `$repoRoot` is set. Call `Assert-HeavySlotLocking` before the slot.
- Replace the loop at `:202-221` with `Get-HeavySlotDir` + `Enter-HeavySlot -Slots $Slots -WaitSeconds
  ($SlotWaitMinutes * 60) -Label "check-all" -Announce "check-all: all $Slots slots are in use by other runs;
  waiting for one."`. On `$null`: the existing line `Check failed: no check-all slot came free in $SlotWaitMinutes
  min (-SlotWaitMinutes).` and exit 1. `$slotWait` keeps its meaning. Not nested: set
  `$env:ASSETOPS_HEAVY_SLOT = $handle.SlotPath` before any guard starts, so a guard that ever calls the pool runs
  nested. Nested: print the §2 line and take nothing.
- `finally`: `Exit-HeavySlot $handle` replaces `$slotStream.Dispose()`; remove `$slotStream`.
- New guards (in the pool, not `-Alone`):
  - `Add-Guard "Heavy-slot hook (planted unpooled runs, T1)" $Node @("--test", "tools/checks/test_heavy_slot_hook.mjs")`, every run.
  - `Add-Guard "Heavy-slot pool self-test (T1)" $Node @("--test", "tools/checks/test_heavy_slot_pool.mjs")`, only
    when `-Full`, on main, when `$diffError` is set, or when `$changed` contains one of
    `$heavySlotFiles = @("tools/heavy-slot.sh", "tools/heavy-slot.ps1", "tools/checks/_heavy_slot.ps1",
    "tools/checks/test_heavy_slot_pool.mjs", "tools/check-all.ps1")`. Otherwise print, next to the estate SKIP line,
    `[SKIP] Heavy-slot pool self-test: no pool file changed. It runs with -Full and on main.`
- Header comment: one line under the PIPE-1 bullets: `- T1: the same slots pool tsc, vitest, backend pytest,
  browser captures and heavy database jobs (tools/heavy-slot.sh, tools/heavy-slot.ps1).`

## 4. What goes through the pool (D-T1.5), how it runs today, what runs instead

Pooled form from the worktree root; from `frontend/` use `../tools/heavy-slot.sh`. pwsh form:
`pwsh -NoProfile -File tools/heavy-slot.ps1 -- ...` (`-Db` for a database job).

| Class | Runs today as | Run instead |
| --- | --- | --- |
| H1 type check | `cd frontend && npx tsc --noEmit`, `npm run typecheck`, `npm run build` (`tsc --noEmit && vite build`) | `cd frontend && ../tools/heavy-slot.sh -- npx tsc --noEmit` |
| H2 vitest | `npx vitest run <files>`, `npx vitest related --run <files>` (select-tests), `npm test` | `cd frontend && ../tools/heavy-slot.sh -- npx vitest run <files>` |
| H3 backend pytest | VPS: `.venv/bin/python -m pytest <files>` with `PYTHONPATH` and `ASSETOPS_TEST_DATABASE_URL`; Windows: `tools\run-host-tests.ps1 -- <files>`; Docker: `tools/run-backend-suite-in-container.ps1` (its `.sh` half runs inside the container), `tools/profile-tests-in-container.*` | `tools/heavy-slot.sh -- .venv/bin/python -m pytest <files> -q`; `tools/heavy-slot.sh -- pwsh -NoProfile -File tools/run-backend-suite-in-container.ps1 ...` |
| H4 browser captures | `node tools/<name>-evidence.mjs`, `node tools/uqfi-captures.mjs`, `node tools/measure-mock-panels.mjs`, `node tools/evidence-checks.mjs --self-test`, `node frontend/mockups/v70/review-browser.mjs`, `node frontend/docs/architecture/extract_v69_panels.mjs`, a direct headless Chrome (`$ASSETOPS_CHROME`) | `tools/heavy-slot.sh -- node tools/layout-evidence.mjs <base-url>` |
| H5 heavy database job | `python tools/demo_combined.py ... prepare|add-day|add-dates|tick|after-children`; `tools/demo_combined_{kobo,cold,ev,kisiwa,mill,finish,ex1,after}.py` run directly; `tools/chain_clone.py create|settle`; `tools/mechanism_dataset.py build|derive`; pytest naming `test_demo_combined_postgres.py` | `setsid nohup tools/heavy-slot.sh --db -- .venv/bin/python tools/demo_combined.py --db <db> --work <w> prepare > <log> 2>&1 &` |

Not pooled (D-T1.7): check-all itself (it takes its own slot; `-Full` on main included); long-running servers
(`demo_combined.py serve|links|drop|live-field`, `npm run dev`, `vite`, uvicorn, `host/lab_app.py`) because they
would hold a slot for hours; guard self-tests under `tools/` run with pytest or `node --test`; `select-tests.py`.
A capture's servers start outside the pool; the capture run is pooled.

## 5. The refusal: `.claude/settings.json` and `tools/heavy-slot-hook.mjs` (D-T1.6)

### 5.1 `.claude/settings.json` (new, tracked; no other keys)

```json
{
  "hooks": {
    "PreToolUse": [
      { "matcher": "Bash",
        "hooks": [ { "type": "command", "command": "node \"$CLAUDE_PROJECT_DIR/tools/heavy-slot-hook.mjs\"", "timeout": 10 } ] }
    ]
  }
}
```
It takes effect from `main`'s checkout (the coordinator's project directory) after the merge, in sessions
started after it (the coordinator restarts; §9 A13). Do not touch `~/.claude/settings.json` or any
`settings.local.json`.

### 5.2 `tools/heavy-slot-hook.mjs` (new; ES module, Node standard library only)

- `export function classify(command)` returns `{ decision: "allow" | "refuse", rule, segment, suggestion }`
  (`rule` one of `H0`-`H5`, `null` on allow). `export function sweepDoc(text)` returns
  `[{ line, command, rule }]` for every refused command found in a document (§5.4). Run as a script (`import.meta`
  main check) it reads the hook JSON from stdin, takes `tool_input.command` (absent or not a string: exit 0),
  and on refuse writes the message below to stderr and exits **2**; on allow exits 0 with no output.
- Refusal message (exact form):
  ```
  heavy-slot: refused (<rule> <class name>): `<segment, first 120 chars>` runs a heavy tool outside the slot pool.
  Run it as: <suggestion>
  RULES §7: tsc, vitest, backend pytest, browser captures and heavy database jobs run only through tools/heavy-slot.sh (T1).
  ```
  `<suggestion>` is `tools/heavy-slot.sh -- <segment>` (H5: `tools/heavy-slot.sh --db -- <segment>`), plus
  ` (from frontend/: ../tools/heavy-slot.sh)` for H1 and H2. For H0: `do not set <name>; the pool sets it.`
  Class names: H0 marker, H1 type check, H2 vitest, H3 backend pytest, H4 browser capture, H5 database job.
- Fail closed, narrowly: any exception inside `classify` refuses (exit 2, `heavy-slot: hook could not parse the
  command; refused. Simplify it or report to the coordinator.`) **only** when the raw command matches the prefilter
  `/tsc|vitest|pytest|py\.test|-evidence|captures|chrom|playwright|demo_combined|chain_clone|mechanism_dataset|run-host-tests|run-backend-suite|profile-tests|backend-test-runner|npm|ASSETOPS_HEAVY|DISABLEFILELOCKING/`;
  otherwise it allows. Budget: under 150 ms per call (median of 20, §7 K5).

### 5.3 The classification algorithm (fixed; tests in §7 pin it)

1. **Heredocs.** Remove every heredoc body: after a `<<` or `<<-` with delimiter `WORD`, `'WORD'` or `"WORD"`,
   drop the following lines up to the line equal to `WORD` (leading tabs ignored for `<<-`).
2. **Substitutions.** Every `$( ... )`, `` ` ... ` `` and `<( ... )` body (nesting-aware) is classified as a command
   line of its own (recursively), in addition to its segment.
3. **Segments.** Split on `&&`, `||`, `;`, `|`, `&` and newline outside single and double quotes (backslash escapes
   honoured; `>&`, `&>`, `2>&1` and `|&`'s `&` are not separators). Strip leading `(`, `{` and `!`.
4. **Leading word.** Skip assignments `NAME=value` and the prefix commands `env` (with `-u NAME`, `-i`,
   assignments), `time`, `/usr/bin/time` (`-v`, `-f X`, `-o X`), `nohup`, `setsid` (`-f`, `-w`), `nice`
   (`-n N`), `timeout` (options, then the duration), `exec`, `stdbuf` (`-oL` style). The next word is the leading
   word; compare by basename, splitting on `/` and `\`.
5. **H0 marker**, on every segment whose leading word is not `grep`, `rg`, `git`, `cat`, `head`, `tail`, `sed`,
   `less`: refuse an assignment to `ASSETOPS_HEAVY_SLOT`, `ASSETOPS_HEAVY_DB`, `ASSETOPS_HEAVY_SLOT_DIR` or
   `DOTNET_SYSTEM_IO_DISABLEFILELOCKING`, in shell (`NAME=`, `export NAME=`, `env NAME=`) or PowerShell
   (`$env:NAME =`) form.
6. **Pooled segment.** The leading word is `heavy-slot.sh` or `heavy-slot.ps1`, or it is `pwsh`/`powershell`
   (`.exe` too) with a `-File` (or `&`) argument whose basename is `heavy-slot.ps1`: allow, except refuse H5 when the
   text after the wrapper's `--` matches H5 and the wrapper options before `--` lack `--db`/`-Db`.
7. **Exempt leading words** (allow without scanning): `grep egrep fgrep rg git gh echo printf cat head tail less
   sed awk ls wc diff sort uniq cut tr jq test [ true false : cd pushd popd which type command cp mv rm mkdir
   touch chmod stat file du realpath readlink basename dirname codex claude`. (`find` and `xargs` are not exempt.)
8. **Heavy patterns** on the segment's whole text, quoted parts included. `B` = start, whitespace, `/`, `\`, a
   quote, `(` or `=`; `E` = end, whitespace, a quote or `)`.
   - H1: `B tsc E`; `npm [opts] run|run-script typecheck|build`.
   - H2: `B vitest E`; `npm [opts] test`, `npm [opts] t`, `npm [opts] run|run-script test`.
   - H3: `B (pytest|py.test) E`, allowed when the pytest arguments have at least one positional target and every
     positional target starts with `tools/` or `./tools/` (positional = not starting with `-`, not the value of
     `-k -m -n -p -o -c -W -r --deselect --rootdir --basetemp --dist --maxfail --tb --durations --confcutdir
     --ignore --log-level`, not a redirection or its file); and, always, a word whose basename is
     `run-host-tests.ps1`, `run-backend-suite-in-container.ps1|.sh`, `profile-tests-in-container.ps1|.sh`, or the
     word `backend-test-runner`.
   - H4: a word whose basename matches `^[A-Za-z0-9_.-]+-(evidence|captures)\.mjs$`, `measure-mock-panels.mjs`,
     `review-browser.mjs` or `extract_v69_panels.mjs`; `evidence-checks.mjs` followed by `--self-test`; a word whose
     basename is `chrome`, `chrome.exe`, `google-chrome`, `google-chrome-stable`, `chromium`, `chromium-browser`,
     `headless_shell` or `playwright`; the text `$ASSETOPS_CHROME` or `${ASSETOPS_CHROME}` used as a command.
   - H5: a word with basename `demo_combined.py` and a later word in `prepare add-day add-dates tick
     after-children`; `chain_clone.py` with `create`/`settle`; `mechanism_dataset.py` with `build`/`derive`;
     basenames `demo_combined_kobo.py demo_combined_cold.py demo_combined_ev.py demo_combined_kisiwa.py
     demo_combined_mill.py demo_combined_finish.py demo_combined_ex1.py demo_combined_after.py
     test_demo_combined_postgres.py` (any arguments).
   First match, in the order H0, H5, H1, H2, H3, H4, names the rule. No match: allow.

Known gaps, accepted and documented in RULES (D-T1.6): a heavy tool started from inside a script file, a heredoc
fed to a shell, `eval` of a variable, an alias; Codex sessions (no Claude hook); a human terminal. The rule binds
them; the hook catches the copyable forms.

### 5.4 The document sweep (the class fix, D-T1.8)

`sweepDoc(text)` classifies (a) every non-blank line inside a fenced code block that does not start with `#`,
and (b) every inline code span that contains a space and whose first word is `node npx npm python python3 pytest
pwsh powershell cd docker bash sh` or starts with `tools/`, `tools\`, `.venv`, `./` or `../`. The hook test runs it
over the agent-read documents in §6 and fails on any refused command, naming `file:line`.

## 6. Commands agents copy: edits

| File | Change |
| --- | --- |
| `.claude/agents/assetops-reviewer.md:35-38` | the pytest and vitest/tsc lines become `tools/heavy-slot.sh -- .venv/bin/python -m pytest <focused backend files> -q` and `cd frontend && ../tools/heavy-slot.sh -- sh -c 'npx vitest run <focused files> && npx tsc --noEmit'`; the check-architecture and check-agent-workflow lines stay |
| `.claude/agents/assetops-implementer.md:54` | `tools/heavy-slot.sh -- node tools/layout-evidence.mjs <base-url>` |
| `.agent/lane-rules-vps-2026-11-12.md` (tracked, `AGENT_KEEP`) | **vitest** line: the pooled form; **Database** line: Postgres test files and heavy DB jobs through the pool (`--db` for a job), the coordinator's turn rule unchanged; one new bullet **Heavy tools** pointing to RULES §7 |
| `backend/TESTING.md` | a section `## The heavy-tool slot pool (T1)` after "When to run what" (≤ 25 lines: what is pooled, both forms, `--db`, `--status`, exit 75, nesting, the hook); every fenced and inline command the §5.4 sweep refuses rewritten to the pooled form (today lines 19, 162, the four `tools\run-host-tests.ps1` lines of the S1-S4 block, 347 as prose or pooled) |
| `.ai/RULES.md` §7, Guards bullet | replace "it allows 2 runs at once machine-wide and waits for a free slot" with "it takes one of 2 heavy slots machine-wide and waits for a free one"; add one bullet after it: "Heavy tools (tsc, vitest, backend pytest, browser captures) and heavy database jobs run only through the slot pool, `tools/heavy-slot.sh -- <command>` (`--db` for a database job; pwsh `tools/heavy-slot.ps1`); a project hook refuses an unpooled run, and the rule binds what the hook cannot see (T1, `backend/TESTING.md`)." |
| `.ai/START_HERE.md:72` | `- Tests: \`backend/TESTING.md\`; heavy tools through \`tools/heavy-slot.sh\`. Guards: \`tools/check-all.ps1\`.` |
| `tools/select-tests.py` | the printed lines only (`select()`'s return value and `--json` unchanged): `backend: tools/heavy-slot.sh -- pwsh -NoProfile -File tools/run-backend-suite-in-container.ps1 -Tier fast -Targets '<files>'` and `frontend (in frontend/): ../tools/heavy-slot.sh -- <command>`; add `"tools/heavy-slot.sh", "tools/heavy-slot.ps1", "tools/select-tests.py"` to `TOOLS_EXEMPT` (D-T1.9: no backend test runs or reads them; check with `git grep -n "heavy-slot\|select-tests\|select_tests" backend host gateway`) |

Not edited: `.gitattributes` (ALWAYS_FULL in select-tests; a change would select the full suite; the Linux
checkouts are LF and Windows uses the pwsh form, D-T1.10), `.ai/NOW.md` (coordinator), `AGENTS.md`.

## 7. Tests (written first, W2)

### 7.1 `tools/checks/test_heavy_slot_hook.mjs` (`node --test`; under 10 s, K5 and K7 spawn processes)

K1, the fixture table: `classify` returns exactly these. Add cases, never remove them.

| # | Command | Expect |
| --- | --- | --- |
| 1 | `cd frontend && npx tsc --noEmit` | refuse H1 (the planted violation) |
| 2 | `cd frontend && ../tools/heavy-slot.sh -- npx tsc --noEmit` | allow |
| 3 | `npx vitest run src/App.test.tsx` | refuse H2 |
| 4 | `npm --prefix frontend test` | refuse H2 |
| 5 | `npm run build` | refuse H1 |
| 6 | `frontend/node_modules/.bin/vitest related --run src/a.ts` | refuse H2 |
| 7 | `bash -c "cd frontend && npx tsc --noEmit"` | refuse H1 |
| 8 | `echo ok; npx tsc` | refuse H1 |
| 9 | `tools/heavy-slot.sh -- true && npx vitest run x` | refuse H2 |
| 10 | `echo $(npx tsc --noEmit)` | refuse H1 |
| 11 | `npx tsc --noEmit \| tail -5` | refuse H1 |
| 12 | `PYTHONPATH=a:b .venv/bin/python -m pytest backend/tests/test_s1_foundation_postgres.py -q` | refuse H3 |
| 13 | `.venv/bin/python -m pytest tools/checks/test_chain_coherence.py -q -p no:cacheprovider` | allow |
| 14 | `python -m pytest -q` | refuse H3 |
| 15 | `python -m pytest -k tools backend/tests/test_x.py` | refuse H3 |
| 16 | `pwsh -NoProfile -File tools/run-backend-suite-in-container.ps1 -Tier fast` | refuse H3 |
| 17 | `tools/heavy-slot.sh -- pwsh -NoProfile -File tools/run-backend-suite-in-container.ps1 -Tier fast` | allow |
| 18 | `tools\run-host-tests.ps1 -- backend/tests/test_x.py` | refuse H3 |
| 19 | `pwsh -NoProfile -File tools/heavy-slot.ps1 -- tools\run-host-tests.ps1 -- backend/tests/test_x.py` | allow |
| 20 | `node tools/layout-evidence.mjs http://127.0.0.1:5173` | refuse H4 |
| 21 | `tools/heavy-slot.sh -- node tools/uqfi-captures.mjs` | allow |
| 22 | `node tools/evidence-checks.mjs --self-test` | refuse H4 |
| 23 | `node --test tools/checks/test_evidence_checks.mjs` | allow |
| 24 | `"$ASSETOPS_CHROME" --headless=new --dump-dom about:blank` | refuse H4 |
| 25 | `setsid nohup .venv/bin/python tools/demo_combined.py --db x_test --work var/x prepare > log 2>&1 &` | refuse H5 |
| 26 | `setsid nohup tools/heavy-slot.sh --db -- .venv/bin/python tools/demo_combined.py --db x_test --work var/x prepare > log 2>&1 &` | allow |
| 27 | `tools/heavy-slot.sh -- python tools/demo_combined.py --db x_test --work var/x add-dates` | refuse H5 (no `--db`) |
| 28 | `python tools/demo_combined.py --db x_test --work var/x serve --port 8990` | allow |
| 29 | `python tools/chain_clone.py create t1probe --migrate` | refuse H5 |
| 30 | `python tools/chain_clone.py drop t1probe` | allow |
| 31 | `ASSETOPS_HEAVY_SLOT=/x/slot-1.lock npx tsc` | refuse H0 |
| 32 | `export ASSETOPS_HEAVY_SLOT_DIR=/tmp/mine` | refuse H0 |
| 33 | `pwsh -c '$env:ASSETOPS_HEAVY_SLOT = "x"'` | refuse H0 |
| 34 | `grep -rn "npx tsc --noEmit" .claude` | allow |
| 35 | `git commit -m "run npx vitest run through the pool"` | allow |
| 36 | `cat > /tmp/x.md <<'EOF'` + newline + `npx tsc --noEmit` + newline + `EOF` | allow |
| 37 | `pwsh -NoProfile -File tools/check-all.ps1` | allow |
| 38 | `find frontend/src -name '*.test.tsx' -exec npx vitest run {} +` | refuse H2 |
| 39 | `ls frontend/node_modules/.bin/tsc` | allow |
| 40 | `cat frontend/vitest.config.ts` | allow |
| 41 | `python tools/select-tests.py --base main` | allow |
| 42 | `tools/heavy-slot.sh --status` | allow |
| 43 | `DOTNET_SYSTEM_IO_DISABLEFILELOCKING=1 pwsh -NoProfile -File tools/check-all.ps1` | refuse H0 |
| 44 | `timeout 600 env PYTHONPATH=x python3 -m pytest host/tests/test_y.py` | refuse H3 |

K2, the script: spawn `node tools/heavy-slot-hook.mjs` with stdin
`{"tool_name":"Bash","tool_input":{"command":"cd frontend && npx tsc --noEmit"}}`: exit 2, stderr starts
`heavy-slot: refused (H1 type check)` and contains `Run it as: tools/heavy-slot.sh -- npx tsc --noEmit`. Case 2:
exit 0, empty stdout and stderr. `{}` and non-JSON stdin: exit 0.

K3, fail closed: a `classify` that throws (inject through an exported test seam, e.g. `main(stdin, { classify })`)
refuses a command containing `vitest` and allows `ls -la`.

K4, the wiring: `.claude/settings.json` parses; it has exactly one `PreToolUse` entry with `matcher` `Bash`
whose command names `tools/heavy-slot-hook.mjs`; that file exists.

K5, latency: 20 spawns of the script on case 2; median under 150 ms (reported in the test name's output).

K6, the document sweep over `backend/TESTING.md`, `.claude/agents/*.md`, `.claude/commands/*.md`,
`.claude/skills/**/*.md`, `.agent/lane-rules-vps-2026-11-12.md`, `.ai/RULES.md`, `.ai/START_HERE.md`,
`.ai/ROLE_CONFIG.md`, `AGENTS.md`: no refused command. Plus a planted case: a fenced block holding
`cd frontend && npx vitest run x` is reported with its line number.

K7, `tools/select-tests.py --files frontend/src/App.tsx backend/assetops_backend/estate/adapters/postgres_estate_read.py` (Python: `process.env.ASSETOPS_GUARD_PYTHON`, which check-all sets,
else `python3`, on Windows `python`): the command after `frontend (in frontend/): ` and the command after `backend: ` (the second file gives mode `selected`, so a backend line is printed) are each classified allow.

### 7.2 `tools/checks/test_heavy_slot_pool.mjs` (`node --test`; under 30 s; Linux cases skip on Windows)

Every case uses `ASSETOPS_HEAVY_SLOT_DIR` = a fresh `mkdtemp` directory, deleted after; `--wait-seconds 3`
where a wait is measured; every spawned process is stopped by PID in `after()`. A holder is
`tools/heavy-slot.sh -- sleep <n>` or a `pwsh -NoProfile -c` that opens the named lock files with
`FileShare.None`, prints `READY` and sleeps; the test waits for `READY` or for the owner file.

| Case | Setup | Expect |
| --- | --- | --- |
| P1 pass-through | `heavy-slot.sh -- sh -c 'echo "$ASSETOPS_HEAVY_SLOT"; exit 7'` | exit 7; stdout is `<dir>/slot-1.lock`; slot free afterwards |
| P2 pwsh holds, bash waits | pwsh holder on slot-1 and slot-2 | `heavy-slot.sh --wait-seconds 3 -- true` exits 75 in 3-6 s with the §3.2 message |
| P3 bash holds, pwsh waits | two `heavy-slot.sh -- sleep 20` | `heavy-slot.ps1 -SlotWaitSeconds 3 -- true` exits 75; `Test-HeavyLockHeld` is true for both |
| P4 nesting, no deadlock | holder X on slot-2; outer `heavy-slot.sh -- sh -c '<tools>/heavy-slot.sh -- true && pwsh -NoProfile -File <tools>/heavy-slot.ps1 -- true'` (`<tools>` = absolute `tools/`) | outer exits 0 in under 5 s; no third lock file is created |
| P5 stale marker | `ASSETOPS_HEAVY_SLOT=<dir>/slot-1.lock` with slot-1 free | stderr has `ignoring stale`; runs on a slot; exit 0 |
| P6 SIGKILL releases | `heavy-slot.sh -- sleep 30`, X on the other slot; `kill -9` the wrapper | `heavy-slot.sh --wait-seconds 3 -- true` exits 0 within 3 s; the orphan `sleep` (its pid from the owner file's `child=`) is then killed by the test |
| P7 SIGTERM stops the tree | `heavy-slot.sh -- sh -c 'sleep 30 & wait'`; `kill -TERM` the wrapper | wrapper exits 143 within 6 s; neither `sh` nor `sleep` is alive; slot free |
| P8 pwsh SIGTERM | as P7 with `heavy-slot.ps1` | exit 143; child gone; slot free |
| P9 one DB job at a time | `heavy-slot.sh --db -- sleep 20` running | a second `--db --wait-seconds 3` exits 75 although a slot is free; `heavy-slot.sh -- true` exits 0 |
| P10 status | one holder with label `probe` | `--status` prints `slot-1: busy pid=... label=probe` and `slot-2: free` and `db-job: free` |
| P11 locking off | `DOTNET_SYSTEM_IO_DISABLEFILELOCKING=1` | both wrappers exit 69 with the D-T1.2 text |
| P12 usage | `heavy-slot.sh npx tsc` (no `--`) | exit 64 |
| P13 check-all uses the module | static: `tools/check-all.ps1` dot-sources `_heavy_slot.ps1`, calls `Enter-HeavySlot` and `Exit-HeavySlot`, sets `ASSETOPS_HEAVY_SLOT`, and has no `[IO.File]::Open(` of its own | holds |

Postgres, vitest and tsc are not run by these tests: the pool is proved with `sleep`, `true` and `sh`.

## 8. Planted-violation proof (RULES §7: a new guard must fail on a real violation)

Record each in the packet with the real output, then restore:
- V1: comment out the H1 rule in `classify`; `node --test tools/checks/test_heavy_slot_hook.mjs` fails on case 1.
- V2: in `backend/TESTING.md` add a fenced line `cd frontend && npx vitest run x`; K6 fails naming the line.
- V3: delete `.claude/settings.json`; K4 fails.
- V4: make `heavy-slot.sh` open its lock with `>` and no `flock`; P2 or P3 fails.
- V5: drop the `{slotfd}>&-` close; P6 fails (the orphan keeps the slot).
- V6: through check-all on the branch, the "Heavy-slot hook" guard reports FAIL with V1 planted.

## 9. Acceptance (questions the work must answer yes to)

- A1 Do check-all and both wrappers use the same two lock files in `D`, and does a lock held by either shell
  block the other (P2, P3)?
- A2 Can a pooled command start a nested pooled command, or check-all, without waiting for a second slot (P4)?
- A3 Is a slot free within one poll after its wrapper is SIGKILLed, and after SIGTERM is its child tree gone (P6-P8)?
- A4 Can two heavy database jobs never run at once (P9)?
- A5 Does every fixture in §7.1 classify as listed, and does the hook script exit 2 with the exact message (K1, K2)?
- A6 Does the hook refuse when its classifier throws on a heavy-looking command, and allow otherwise (K3)?
- A7 Is the hook wired in `.claude/settings.json` (K4), and is its median latency under 150 ms (K5)?
- A8 Do the agent-read documents and select-tests' printed lines hold no unpooled command (K6, K7)?
- A9 Does each of V1-V6 fail as stated?
- A10 Fast path: is the hook guard's printed time at most 10 s (it runs in the parallel pool); when the measured change holds no pool file, does
  check-all print the pool self-test SKIP line; and is fast-mode wall time within 3 s of the same measurement on
  `main` (method: `reviewer-guide.md` R6; commit 3 is the docs commit, so `-Base <T1 head>~1` measures a change
  with no pool file)?
- A11 With a slot free, does `Enter-HeavySlot` return within 100 ms (printed `waiting for a slot` value ≤ 0.1 s)?
- A12 Is `python tools/select-tests.py --base main` on the T1 branch `mode: none` (D-T1.9)?
- A13 (post-merge, coordinator) In a Claude session started after the merge, is `cd frontend && npx tsc --noEmit`
  refused with the §5.2 message, and does `cd frontend && ../tools/heavy-slot.sh -- npx tsc --noEmit` run? Lanes 3
  and 4 open only after this.

## 10. Checks to run, and done

- `node --test tools/checks/test_heavy_slot_hook.mjs`, `node --test tools/checks/test_heavy_slot_pool.mjs`.
- `pwsh -NoProfile -File tools/check-all.ps1` once, fast mode, at the end (it runs both, since this branch changes
  pool files). `python tools/select-tests.py --base main` (expect `mode: none` and no frontend line).
- No backend or frontend suite, no Postgres, no Docker, no browser.

Done when: A1-A12 hold with real output in the packet; V1-V6 are recorded; the docs in §6 are edited; three
commits at most (pool and check-all; hook, settings and tests; docs and select-tests), staged by explicit path.

Packet: `specs/T1-heavy-tool-slot-pool/packet.md` (≤ 3k tokens, RULES §5). It records **the count of mid-build
questions** (RULES §4 item 7; above zero is a spec-template defect) and the K5 and A10 figures.

## 11. Out of scope

- Two slots for one database job (until DM05's `/usr/bin/time -v` measurement; D-T1.4); a third slot or a
  memory-aware scheduler.
- In-tool tripwires (a pytest conftest or vitest config refusing unpooled runs): conftest is ALWAYS_FULL in
  select-tests and would force a full suite; recorded as a follow-up if a bypass is seen (D-T1.6).
- Codex enforcement, the PowerShell tool on Windows, the Monitor tool, scripts and heredocs fed to a shell
  (documented gaps, D-T1.6).
- Pooling long-running servers; changing check-all's guard set, `-Slots` or timeouts; the one-at-a-time rule for
  full suites (stays a coordinator rule); PIPE-2; `.gitattributes`.
- Windows hardware verification (D-T1.10: the pwsh path is the same .NET call check-all already uses on Windows).

## 12. Sizing

2.5 units holds: the pool, the shared module and the check-all change with P1-P13 (1.0); the hook, settings and
K1-K7 (1.0); the documents, select-tests and the sweep fixes (0.5). If the bash/.NET interop (P2, P3) fails,
stop: that is a design change, not a fix.
