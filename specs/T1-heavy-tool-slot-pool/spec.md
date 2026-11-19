# T1: the heavy-tool slot pool, enforced (implementer spec)

Status: in_review. Architect spec **rev 2**, 2026-11-19; built on `task/T1-heavy-tool-slot-pool`; review packet `specs/T1-heavy-tool-slot-pool/packet.md`.

Rev 2 does two things:
- It switches enforcement to **option C, in-tool tripwires**. The owner chose this: "yes install playwright, and
  C for T1" (`owner/owner-playwright-and-t1-c-2026-11-19.md`). There is **no Claude Code hook and no
  `.claude/settings.json`**.
- It folds in the answers from handshake round 1: R1-R21 and I1-I15 (`rulings.md`).

Branch `task/T1-heavy-tool-slot-pool` (worktree `/opt/assetecon/AssetOpsV1-t1`). Review depth: discovery (W5).
Reviewer guide: `reviewer-guide.md`. Rulings: `rulings.md` (D-T1.1-D-T1.18; D-T1.6 and D-T1.8 are
superseded).

Sources:
- the delivery plan row `T1` (pack branch, `delivery-plan.md:59`);
- the go-to-market plan §2.4 "B03" (2-3 units);
- PIPE-1 A3;
- owner TW23 (`owner/owner-sitting1-answers-2026-11-18.md` item 7): lanes 3 and 4 open once B03 is merged and
  enforced;
- `.agent/owner-start-t1-2026-11-19.md`.

`USER_REVIEW_REQUIRED: false`.

## 0. Before you start

1. The handshake round is closed (`handshake.md` Status). Code may start.
2. Stay off ports 5490 and 8990. Run no full suites and no Docker. The Postgres smoke run in §10 needs the
   coordinator's DB turn.
3. Every self-test that takes locks uses its own temp repository (§7.1). The exception is the few check-all runs
   (I11c): start one only when `tools/heavy-slot.sh --status` shows both slots free.
4. Commit plan (I11):
   - commit 1: the pool and its tests;
   - commit 2: the tripwires and their tests;
   - commit 3: the documents and `select-tests`.

   The handshake commits and the closing commit (packet, spec status, `.ai/state` entry) do not count toward the
   three.

## 1. Outcome and why

With four build lanes, agents running `tsc`, vitest, Postgres test files, browser captures and the heavy
database job side by side exhaust the server's memory, and it has no swap. Today only check-all takes a slot
(`tools/check-all.ps1:202-221`).

T1 puts every heavy tool through **the same two slots**. Each heavy tool then **refuses to start by itself
outside a held slot**, whoever starts it: a Claude agent, Codex or a human terminal.

Lanes 3 and 4 open after the merge and the post-merge check A16.

## 2. Structure: records and rules

### The pool directory `D` (D-T1.12)

One function per language computes `D`. Every wrapper, check-all and every tripwire calls it.

1. Run `git -C <the directory of the calling module or script> rev-parse --path-format=absolute
   --git-common-dir`. Remove **every** environment variable whose name starts with `GIT_` from that git call's
   environment. This stops `GIT_DIR` and the like from redirecting the pool (R3).
2. Make the path canonical with `realpath` semantics:
   - bash: `realpath -e`;
   - node: `fs.realpathSync`;
   - python: `os.path.realpath`;
   - pwsh on Linux: `& realpath -e -- <p>`;
   - pwsh on Windows: `[IO.Path]::GetFullPath`, compared without case.
3. Append `/check-all-slots`.
4. If git fails:
   - a tripwire retries step 1 from the current directory;
   - a wrapper falls back to `<canonical system temp>/assetops-check-all-slots`.

All 61 checkouts on this server resolve to `/opt/assetecon/AssetOpsV1/.git/check-all-slots`.

`ASSETOPS_HEAVY_SLOT_DIR` replaces `D` **in the wrappers and in `Enter-HeavySlot` only**, so that self-tests can
use a private directory. **Tripwires never read it.** A slot held in a private directory therefore never
satisfies a tripwire.

### Files in `D`

| File | Meaning |
| --- | --- |
| `slot-1.lock`, `slot-2.lock` | the two heavy slots. A slot is held when a process has an exclusive `flock` on an open fd of the file. The shared pool has exactly 2 (R8c) |
| `db-job.lock` | one heavy database job at a time (D-T1.4) |
| `slot-N.owner`, `db-job.owner` | one field per line: `pid=`, `child=`, `label=`, `since=` (UTC ISO 8601), `cwd=`, `db=yes|no`. The ancestry check uses `pid=` (D-T1.14). The lock stays the authority on "held" |

### Lock protocol (D-T1.2)

The lock is an exclusive, non-blocking `flock(2)`, polled every 2 s. The pre-flight proved it on this server:
cases (A)-(G) in `handshake.md`, and `/proc/locks` shows `FLOCK ADVISORY WRITE`.

- **Acquire.** pwsh: `[IO.File]::Open($p, 'OpenOrCreate', 'ReadWrite', 'None')`. bash: `exec {fd}>>"$p"`, then
  `flock -n -x "$fd"`.
- **Probe.** Open in pwsh with mode `Open`, and in bash with `<`. A probe never creates the file. A missing file
  is free. In pwsh, catch `FileNotFoundException` and `DirectoryNotFoundException` before `IOException`
  (I12d, R8b).
- **Locking disabled.** If `DOTNET_SYSTEM_IO_DISABLEFILELOCKING` is non-empty, both wrappers and check-all
  refuse with exit 69: `heavy-slot: refused: DOTNET_SYSTEM_IO_DISABLEFILELOCKING is set; the slot locks would
  not hold.`

### The wrapper holds the lock, the child does not (D-T1.2)

- **pwsh.** .NET opens files close-on-exec, so the child inherits nothing.
- **bash.** Compute every value before the first lock open. After it, use builtins only: no `git`, `date` or
  `realpath`. For timestamps use `printf '%(%Y-%m-%dT%H:%M:%SZ)T' -1` under `TZ=UTC`.
- **Starting the child (bash, I4).** Use `( exec {slotfd}>&-; <only if db> exec {dbfd}>&-; exec "$@" ) <&0 &`.
  The explicit `<&0` keeps stdin; bash would otherwise give a background job `/dev/null`.
- **Process group (D-T1.15).** The child stays in the wrapper's process group: there is no `set -m`. A group
  kill stops both.
- **TERM, HUP or INT to the wrapper.** Collect the child's descendants by walking `/proc/<pid>/task/*/children`
  recursively. Send TERM to all of them, wait up to 5 s, then send KILL. Exit 128+signal (TERM 143, HUP 129,
  INT 130).
- **SIGKILL of the wrapper alone.** The slot frees at once and the child runs on unpooled. This is accepted. A
  tripwired tool that is already running does not check again.

### Nesting marker (D-T1.3, D-T1.14)

A holder exports `ASSETOPS_HEAVY_SLOT=<D>/slot-N.lock`. A `--db` holder also exports
`ASSETOPS_HEAVY_DB=<D>/db-job.lock`. Both paths are canonical and absolute.

The **marker test** passes when all four hold, checked in this order:
1. The variable is non-empty.
2. Its canonical directory equals `D`, and its name matches `^slot-[12]\.lock$`.
3. On Linux: the `pid=` in `slot-N.owner` is alive and is the caller itself or an ancestor of the caller. Walk
   the 4th field of `/proc/<pid>/stat`, parsed after the last `)`, for at most 64 steps. On Windows, skip this
   check.
4. A probe finds the lock held.

For `db`, apply the same test to `ASSETOPS_HEAVY_DB`, with the name `db-job.lock`.

A wrapper, check-all or `Enter-HeavySlot` that finds a marker:
- **Marker passes.** The caller is **nested** and takes nothing:
  - bash runs `exec "$@"`;
  - pwsh runs the command directly;
  - check-all prints `check-all: inside a held heavy slot (<path>); not taking another.`
- **Marker fails.** Print `heavy-slot: ignoring stale ASSETOPS_HEAVY_SLOT=<value> (<reason>)` to stderr, then
  acquire normally.
- **Nested `--db`.** If `ASSETOPS_HEAVY_DB` does not pass, refuse at once with exit 69: `heavy-slot: refused:
  --db inside a held slot; put --db on the outermost wrapper.` (D-T1.13, R4). No nested entry ever waits for any
  lock.

### Order and deadlock freedom

- An outer entry takes `db-job.lock` first, then the lowest free slot.
- It holds at most one slot plus the DB lock.
- A nested entry takes nothing.
- The only process that waits while holding a lock is an outer `--db` entry. It holds the DB lock only, and
  every slot holder is a non-DB job (or that same entry). So no cycle can form.
- Waits are bounded: default 1200 s, then exit 75.

## 3. The pool

### 3.1 `tools/checks/_heavy_slot.ps1` (new)

Also change the exclusion in `tools/check-architecture.ps1:58-72` from `_common.ps1` to `_*.ps1` (one line, I1).

| Function | Contract |
| --- | --- |
| `Get-HeavySlotDir([string]$RepoRoot)` | returns `D` per §2 and creates it; the override env applies |
| `Get-HeavyCanonicalPath([string]$Path)` | the §2 canonicalisation |
| `Test-HeavyLockHeld([string]$Path)` | a §2 probe; `$true` only when someone holds the lock |
| `Test-HeavyMarker([string]$Value, [string]$SlotDir, [string]$Name)` | the §2 marker test, `Name` `slot` or `db`; returns `@{ Ok; Reason }` |
| `Enter-HeavySlot -SlotDir <s> [-Slots 2] -WaitSeconds <n> [-Db] [-Label <s>] [-Announce <s>]` | applies the marker rules, then acquires. Prints `-Announce` once, at the first wait. Returns `@{ Nested; SlotPath; SlotStream; DbPath; DbStream; WaitedSeconds }`, or `$null` on timeout (after releasing everything). `-Slots` above 2: exit 64, `the shared pool has 2 slots (T1)`. Writes the owner files |
| `Exit-HeavySlot $Handle` | disposes the streams; deletes an owner file only if its `pid=` is `$PID`; `$null`-safe |
| `Assert-HeavySlotLocking` | the D-T1.2 refusal |
| `Assert-HeavySlotHeld -Tool <s> [-Db]` | the pwsh tripwire (§5); resolves `D` with **no** override |

### 3.2 `tools/heavy-slot.ps1` (new)

```
pwsh -NoProfile -File tools/heavy-slot.ps1 [-Db] [-SlotWaitSeconds <n>] [-Label <text>] -- <command> [args...]
pwsh -NoProfile -File tools/heavy-slot.ps1 -Status
```

- **Supported form (I3).** Only the `pwsh -NoProfile -File` form is supported, and the usage line says so. A
  missing `--` gives exit 64. A `-name:value` argument is split by pwsh into two arguments: this is a documented
  limitation, so use `--name=value` forms.
- **Parsing.** A plain script that parses `$args`, like `tools/run-host-tests.ps1`. Options are read only before
  the first `--`.
- **Defaults.** Wait 1200 s. The label defaults to the first two words of the command, made into one line with
  newlines and `=` replaced by spaces (I12e).
- **Running the child.** Use `System.Diagnostics.Process` with `UseShellExecute = $false` and `ArgumentList`.
  - A first word that ends in `.ps1` and names a file runs as `(Get-Process -Id $PID).Path -NoProfile -File
    <script> <args>` (I2).
  - Any other first word is resolved with `Get-Command -CommandType Application`, taking the first hit.
  - The marker variables are set in the child's environment only.
  - A first word of `setsid` is refused with exit 64: `put setsid/nohup before the wrapper` (I5b).
- **Signals.** SIGTERM and SIGHUP use `PosixSignalRegistration`, as `check-all.ps1:140-175` does. The handler
  kills the child tree with `Kill($true)` and exits 143 or 129. Ctrl-C kills the tree and exits 130 (I12b).
- **Exit codes.**

  | Code | Meaning |
  | --- | --- |
  | the child's | the command ran |
  | 64 | usage error |
  | 69 | refused |
  | 75 | no slot came free |

  A child that itself exits 64, 69 or 75 can be told from the wrapper only by the wrapper's stderr line (R20,
  accepted; stated in TESTING.md).
- **Messages (I12a).** Each goes to stderr, printed once:
  - `heavy-slot: both heavy slots are busy (tools/heavy-slot.sh --status); waiting up to <n> s.`
  - `heavy-slot: another database job holds db-job.lock; waiting up to <n> s.`
  - on timeout: `heavy-slot: no slot came free in <n> s (-SlotWaitSeconds).`
- **`-Status` (I12c).** Always prints `slot-1`, `slot-2` and `db-job`, plus any other `slot-N.lock` that
  exists. Exit 0. Each line is one of:
  - `free` (a missing file is free);
  - `busy pid=<p> child=<c> label=<l> since=<t> cwd=<d>`;
  - `busy, holder unknown (owner file stale); find it with: fuser -v <path>`.

### 3.3 `tools/heavy-slot.sh` (new, LF, `git update-index --chmod=+x`)

```
tools/heavy-slot.sh [--db] [--wait-seconds <n>] [--label <text>] -- <command> [args...]
tools/heavy-slot.sh --status
```

- `#!/usr/bin/env bash`, `set -u`. Same options, defaults, messages, exit codes and status format as §3.2, with
  the bash option names.
- No `flock` on `PATH`: `exec pwsh -NoProfile -File "<dir>/heavy-slot.ps1"` with the options translated. No pwsh
  either: exit 69.
- Child start and tree kill: as in §2. Wait in a loop on `wait "$child"` until the child has really exited.
- `trap EXIT` removes the owner file if its `pid=` is `$$`.
- Nested: `exec "$@"`.

### 3.4 `tools/check-all.ps1` (edit)

- **Module.** Dot-source `_heavy_slot.ps1` and call `Assert-HeavySlotLocking`.
- **Acquire.** Replace `:202-221` with `Enter-HeavySlot -Slots $Slots -WaitSeconds ($SlotWaitMinutes * 60)
  -Label "check-all" -Announce "check-all: all $Slots slots are in use by other runs; waiting for one."`.
  - On timeout, keep the existing failure line and exit 1.
  - When it takes a slot, set `$env:ASSETOPS_HEAVY_SLOT` before any guard starts, so a tripwired tool started by
    a guard passes.
  - When nested, print the §2 line.
- **Release.** `finally` calls `Exit-HeavySlot`; remove `$slotStream`.
- **Messages.** Every other message and the summary lines stay byte-identical.
- **New guards**, all run in the pool:

  | Guard | Command | When it runs |
  | --- | --- | --- |
  | `Heavy-slot tripwire inventory (T1)` | `$Node --test tools/checks/test_heavy_slot_inventory.mjs` | every run (static, under 2 s) |
  | `Heavy-slot pool and tripwire self-test (T1)` | `$Node --test tools/checks/test_heavy_slot_pool.mjs` | only when the trigger rule selects it |
  | `tsc shim installed (T1)` | `$Node tools/heavy-slot-shims.mjs check frontend/node_modules` | only with `-Full` and on main, so the coordinator's after-merge run catches a missing shim (§5.2) |

- **Trigger rule (I15).** Generalise `Get-SelfTestDecision` with a file-list parameter, and use it for both the
  estate rule and the pool rule.
  - The pool rule's list: `$heavySlotFiles = tools/heavy-slot.sh, tools/heavy-slot.ps1,
    tools/checks/_heavy_slot.ps1, tools/heavy_slot_check.cjs, tools/heavy_slot_check.py,
    tools/heavy-slot-shims.mjs, tools/checks/test_heavy_slot_pool.mjs, tools/check-all.ps1`.
  - Add four `-SelfTestSelection` cases: a pool file changed, none changed, `-Full`, a diff error.
  - When skipped, print `[SKIP] Heavy-slot pool self-test: no pool file changed. It runs with -Full and on
    main.`

## 4. What is pooled, and what refuses it (D-T1.5 as revised by D-T1.16)

Pooled forms are given from the worktree root. From `frontend/`, use `../tools/heavy-slot.sh`. A database job
adds `--db` (pwsh `-Db`).

| Class | Pooled form | Tripwire (§5) |
| --- | --- | --- |
| type check | `cd frontend && ../tools/heavy-slot.sh -- npx tsc --noEmit` (also `npm run typecheck`, `npm run build`) | the `tsc` shim in `node_modules/.bin` |
| vitest | `cd frontend && ../tools/heavy-slot.sh -- npx vitest run <files>` | `frontend/vite.config.ts` when `process.env.VITEST` is set |
| pytest with Postgres (`ASSETOPS_TEST_DATABASE_URL` non-empty) | `tools/heavy-slot.sh -- .venv/bin/python -m pytest <files> -q`, or `tools/heavy-slot.sh -- pwsh -NoProfile -File tools/run-backend-suite-in-container.ps1 ...`. A run whose tier includes slow needs `--db`, because `test_demo_combined_postgres.py` runs a prepare | `backend/tests/conftest.py` and `host/conftest.py` `pytest_configure`; the container runners |
| browser capture | `tools/heavy-slot.sh -- node tools/layout-evidence.mjs <base-url>` | each of the 30 launching scripts, and any future Playwright config or script (§5.4) |
| heavy database job | `setsid nohup tools/heavy-slot.sh --db -- .venv/bin/python tools/demo_combined.py --db <db> --work <w> prepare > <log> 2>&1 &` | the dispatch of each entry point (§5.5) |

Not pooled (D-T1.7):
- check-all, which takes its own slot;
- servers: `serve`, `links`, `drop`, `live-field`, `npm run dev`, vite, uvicorn, `lab_app`;
- pytest without a database URL (D-T1.16);
- guard tests under `tools/`, including a hand-run `test_estate_guard.py -n 4` (R15b: accepted, since check-all
  runs it inside its slot);
- `npx vite build` alone;
- `select-tests.py`.

## 5. The tripwires (D-T1.11)

### 5.1 Check modules

- **`tools/heavy_slot_check.cjs`** (CommonJS, Node standard library only; exports written as `exports.x = x`
  lines so ESM named imports work):
  - `slotDir({ from })`: `D` per §2, with no override;
  - `checkMarker(env, { slotDir, pid, procRoot, platform, inContainer })`: pure apart from reading files and
    `/proc`; returns `{ ok, reason }`;
  - `assertHeavySlot(tool, { db = false } = {})`: on failure, writes the message to stderr and calls
    `process.exit(69)`.
- **`tools/heavy_slot_check.py`**, the same contract:
  - `slot_dir(start)`;
  - `check_marker(env, *, slot_dir, pid, proc_root, platform, in_container)`;
  - `require(tool, *, db=False, exit_with=None)`: on failure, prints the message and calls `exit_with` if given
    (pytest passes `pytest.exit`, which is called with `returncode=69`); otherwise calls `sys.exit(69)`.
- **pwsh:** `Assert-HeavySlotHeld` (§3.1).

**Container rule.** Inside a container (`/.dockerenv` exists), the marker test is replaced by one check:
`ASSETOPS_HEAVY_SLOT_CONTAINER` is `slot` or `db`. A `db` caller needs `db`. Outside a container, the variable is
ignored.

**Refusal message (exact):**
```
heavy-slot: refused: <tool> runs only inside the heavy-tool slot pool (<reason>).
Run it as: tools/heavy-slot.sh <--db >-- <your command>   (from frontend/: ../tools/heavy-slot.sh; pwsh: pwsh -NoProfile -File tools/heavy-slot.ps1 <-Db >-- ...)
RULES §7 (T1).
```

`<reason>` is one of:
- `ASSETOPS_HEAVY_SLOT is not set`
- `the marker is not a slot of this machine's pool`
- `the slot's holder is not this process or an ancestor`
- `the slot is not held`
- `a database job needs --db on the outermost wrapper`
- `in a container without ASSETOPS_HEAVY_SLOT_CONTAINER`

The `--db` and `-Db` text appears only when `db` is true.

### 5.2 tsc: the shim (`tools/heavy-slot-shims.mjs`, new)

- **`install <node_modules>`** first makes `<nm>` canonical, so a worktree's symlink resolves to main's install.
  Then it:
  1. writes `<nm>/.heavy-slot/tsc.cjs` with mode 755:
     ```
     #!/usr/bin/env node
     // T1 heavy-slot shim (tools/heavy-slot-shims.mjs); the real tsc is ../typescript/bin/tsc
     require(<JSON string of canonical <nm>/../../tools/heavy_slot_check.cjs>).assertHeavySlot("tsc");
     require("../typescript/bin/tsc");
     ```
  2. replaces `<nm>/.bin/tsc` with a symlink to `../.heavy-slot/tsc.cjs`. The `.cjs` extension fixes the module
     format whatever `frontend/package.json`'s `"type"` is.

  It is idempotent.
- **`check <nm>`** exits 0 only when the symlink resolves to that shim and the shim names an existing check
  module. Otherwise it exits 1 with one line.
- **`frontend/package.json`** gets `"postinstall": "node ../tools/heavy-slot-shims.mjs install node_modules"`, so
  that `npm ci` keeps the shim.
- **When it is installed.** The coordinator installs the shim on main's `node_modules` **after the merge**
  (A16). The shim requires main's `tools/heavy_slot_check.cjs`, which does not exist on main before the merge.
  Before the merge, prove the shim only against a fake `node_modules` in a temp repository (P-T5).
- **Documented gaps.** Running `node node_modules/typescript/bin/tsc` directly, and the Windows `.cmd` shims.

### 5.3 vitest and pytest

- **`frontend/vite.config.ts`.** Add, after the imports:
  ```
  import { createRequire } from "node:module";
  if (process.env.VITEST) createRequire(import.meta.url)("../tools/heavy_slot_check.cjs").assertHeavySlot("vitest");
  ```
  - Proof (P-T6): an unpooled `npx vitest run src/<one small test>` exits 69 with the message, and the pooled
    form passes.
  - **Fallback**, only if Vite's bundled config resolves `import.meta.url` elsewhere: set `test.globalSetup:
    ["../tools/heavy-slot-vitest-setup.mjs"]`, where that file's `export function setup()` calls the same
    assert. Record in the packet which form you used. This is the specified fallback, not a design choice.
- **`backend/tests/conftest.py` and `host/conftest.py`.** The first statement of `pytest_configure` is
  `if os.environ.get("ASSETOPS_TEST_DATABASE_URL"): _heavy_slot_check().require("pytest with Postgres",
  exit_with=pytest.exit)`.
  - `_heavy_slot_check()` loads `<repo>/tools/heavy_slot_check.py` with
    `importlib.util.spec_from_file_location`, found from `Path(__file__).resolve()`.
  - xdist workers check too, and pass by ancestry.
- **Container runners.** `tools/run-backend-suite-in-container.ps1` and `tools/profile-tests-in-container.ps1`
  call `Assert-HeavySlotHeld -Tool "the container test runner"` before `docker compose`. They set
  `$env:ASSETOPS_HEAVY_SLOT_CONTAINER` to `db` when `ASSETOPS_HEAVY_DB` passes the marker test, otherwise to
  `slot`.
  - In `docker-compose.test.yml`, the `environment:` of `backend-test-runner` gets
    `ASSETOPS_HEAVY_SLOT_CONTAINER: ${ASSETOPS_HEAVY_SLOT_CONTAINER:-}`.
  - The `.sh` halves are unchanged.

### 5.4 Browser captures

**Which files.** Every tracked file outside `archive/`, `frontend/mockups/v69/` and `frontend/mockups/v71/` that
contains `remote-debugging-port`, `playwright` or `puppeteer`. Today that is 30 files: `git grep -l -E
"remote-debugging-port|playwright|puppeteer"` with those exclusions. Excluded: the check module itself and the
inventory test.

**What each one does.** It calls `assertHeavySlot("browser capture")` before it launches anything, importing it
with `import { assertHeavySlot } from "<relative>/heavy_slot_check.cjs";`.

**Where the call goes.**
- By default, at the top level.
- If a test imports the file (check with `git grep -n "<basename>" -- tools/checks frontend/src`; today only
  `tools/evidence-checks.mjs`), the call goes inside the launching branch instead. In `evidence-checks.mjs`
  that is the `--self-test` path.

**Playwright.** The owner is having it installed separately. Its config or scripts fall under this rule as soon
as they are tracked.

### 5.5 Heavy database jobs

Each entry point calls `heavy_slot_check.require("database job", db=True)`. The `import heavy_slot_check` goes
inside the dispatch, never at import time, because tests import these modules (for example
`backend/tests/test_ar2_prepare_period_rows.py`).

| Entry point | Where the call goes |
| --- | --- |
| `tools/demo_combined.py` | `main()`, after argument parsing, for `prepare`, `add-day`, `add-dates`, `tick`, `after-children` |
| `tools/chain_clone.py` | `main()`, for `create`, `settle` |
| `tools/mechanism_dataset.py` | `main()`, for `build`, `derive`, `ensure` (I7) |
| `demo_combined_{kobo,cold,ev,kisiwa,mill,finish,ex1,after}.py` | the `if __name__ == "__main__":` block; as children of a pooled `prepare` they pass by ancestry |

`demo_combined_drain.py` and `demo_combined_rows.py` are helpers and stay out.

## 6. Documents

| File | Change |
| --- | --- |
| `.claude/agents/assetops-reviewer.md:35-38` | `tools/heavy-slot.sh -- .venv/bin/python -m pytest <focused backend files> -q` and `cd frontend && ../tools/heavy-slot.sh -- sh -c 'npx vitest run <focused files> && npx tsc --noEmit'` |
| `.claude/agents/assetops-implementer.md:54` | `tools/heavy-slot.sh -- node tools/layout-evidence.mjs <base-url>` |
| `.agent/lane-rules-vps-2026-11-12.md` | line 7: "allows 2 runs at once machine-wide (a third waits for a slot by itself)" becomes "takes one of 2 heavy slots machine-wide and waits for a free one" (I9). The vitest line in pooled form. The Database line: Postgres test files and DB jobs through the pool (`--db` for a job), with the turn rule unchanged. A new bullet **Heavy tools**: see RULES §7; a tool refuses to run outside the pool |
| `backend/TESTING.md` | a new section `## The heavy-tool slot pool (T1)` after "When to run what", at most 25 lines. It covers: what is pooled and the tripwires; both forms; `--db`, including for slow-tier and full runs; `--status`; exit 75; nesting; R20; the tsc shim reinstalls on `npm ci`. Also rewrite in pooled form (I8a): line 19; the five `tools\run-host-tests.ps1` lines 147-159; lines 162-168; the fenced block at 210-213 (`pwsh -NoProfile -File tools/heavy-slot.ps1 -- tools\run-backend-suite-in-container.ps1 ...`); line 347 |
| `.ai/RULES.md` §7, Guards bullet | replace "it allows 2 runs at once machine-wide and waits for a free slot" with "it takes one of 2 heavy slots machine-wide and waits for a free one". Add one bullet: "Heavy tools (tsc, vitest, pytest with a database, browser captures) and heavy database jobs run only through the slot pool, `tools/heavy-slot.sh -- <command>` (`--db` for a database job; pwsh `tools/heavy-slot.ps1`); each refuses to start outside it (T1, `backend/TESTING.md`)." |
| `.ai/START_HERE.md:72` | `- Tests: \`backend/TESTING.md\`; heavy tools through \`tools/heavy-slot.sh\`. Guards: \`tools/check-all.ps1\`.` |
| `tools/select-tests.py` | the printed lines only, in pooled form. Add `tools/heavy-slot.sh`, `tools/heavy-slot.ps1`, `tools/select-tests.py` and `tools/heavy_slot_check.py` to `TOOLS_EXEMPT` (D-T1.9). `--json` output is unchanged |

## 7. Tests (written first)

Every spawn removes `ASSETOPS_HEAVY_SLOT`, `ASSETOPS_HEAVY_DB`, `ASSETOPS_HEAVY_SLOT_CONTAINER` and
`DOTNET_SYSTEM_IO_DISABLEFILELOCKING` from its environment, unless the case sets them (I10).

### 7.1 `tools/checks/test_heavy_slot_pool.mjs` (concurrent cases, each in its own `mkdtemp`; under 30 s in total)

**Harness (R2).** Create a temp git repository `M` with one commit and a worktree `W`. Copy `heavy-slot.sh`,
`heavy-slot.ps1`, `checks/_heavy_slot.ps1`, `heavy_slot_check.cjs` and `heavy_slot_check.py` into both
`M/tools` and `W/tools`. `D` is then `M/.git/check-all-slots`, the real pool of **that** repository. No case
needs the override unless it says so.

**Pool cases**

| Case | What it does | Expect |
| --- | --- | --- |
| P1 | `-- sh -c 'echo "$ASSETOPS_HEAVY_SLOT"; exit 7'` | exit 7; prints the canonical `D/slot-1.lock`; the slot is free afterwards |
| P2 | a pwsh holder on both slots; bash with `--wait-seconds 3` | exit 75 within 3-6 s, with the timeout line |
| P2c | race (R1b): one bash entry and one pwsh entry started together, one slot free and the other held; 20 iterations | exactly one wins each time |
| P3 | two bash holders; `heavy-slot.ps1 -SlotWaitSeconds 3` | exit 75; `Test-HeavyLockHeld` is true for both slots |
| P4 | X holds slot 2; an outer bash entry runs a nested bash entry, then a nested pwsh entry | both finish in under 5 s |
| P4b | the outer entry is pwsh `heavy-slot.ps1`, then a pwsh script calling `Enter-HeavySlot` (the check-all path); the nested entry is bash (R1a) | under 5 s |
| P4c | the outer entry runs from `M/tools`, the inner from `W/tools`; then the reverse; then the outer through a symlinked path to `M` (R2) | nested every time |
| P5 | stale markers: (a) one naming a free slot; (b) one in another directory; (c) on Linux, a held slot whose holder is not an ancestor (R5) | each acquires normally and prints `ignoring stale` with its reason |
| P5b | `GIT_DIR=/tmp/x` and `GIT_COMMON_DIR=/tmp/x` set on the wrapper (R3) | it still uses `M/.git/check-all-slots` |
| P6, P6b | `kill -9` of the bash wrapper, then of the pwsh wrapper (R7b) | the slot is free within 3 s; the test then kills the orphan by its `child=` pid |
| P6c | a pwsh process calls `Enter-HeavySlot`, then `Start-Process sleep`; `kill -9` the pwsh process (the check-all mechanism) | the slot is free, and `/proc/<sleep>/fd` holds no fd on the lock |
| P7, P8 | TERM to the bash wrapper, then to the pwsh wrapper, each running `sh -c 'sleep 30 & wait'` | exit 143 within 6 s; the whole tree is gone; the slot is free |
| P7b | TERM to the bash wrapper's process group (D-T1.15) | the wrapper and its child stop together |
| P9 | one `--db` holder; then a second `--db` entry and a plain entry | the second `--db` exits 75 although a slot is free; the plain entry exits 0 |
| P9b | a nested `--db` inside a non-DB slot (R4) | exit 69 at once, with the D-T1.13 line |
| P10 | `--status` | the specified format; a missing `db-job.lock` shows as `free` |
| P11 | locking disabled | exit 69 from both wrappers |
| P12 | `heavy-slot.sh npx tsc` (no `--`), and `heavy-slot.sh -- setsid x` | exit 64 for both |
| P13 | stdin (R6): `heavy-slot.sh -- sh -c 'read x; echo $x' <<<y` | prints `y` |
| P14 | `heavy-slot.ps1 -- <tmp>/x.ps1 a b`, where the script exits 5 (I2) | both arguments arrive; exit code 5 passes through |
| P15 | `-Slots 3` through `Enter-HeavySlot` (R8c) | refused |

**Tripwire cases.** Same harness; the check modules run from `M/tools`.

| Case | What it does | Expect |
| --- | --- | --- |
| P-T1 | node and python `require`, under `M/tools/heavy-slot.sh --` and unpooled | pooled: both pass. Unpooled: both exit 69 with the exact message and reason `ASSETOPS_HEAVY_SLOT is not set` |
| P-T2 | a wrapper run with `ASSETOPS_HEAVY_SLOT_DIR=<private>` holds a slot | both tripwires refuse with `not a slot of this machine's pool`, so this bypass is closed |
| P-T3 | a forged marker: `ASSETOPS_HEAVY_SLOT=<D>/slot-1.lock` while another process holds slot 1 | refused with `not this process or an ancestor` |
| P-T4 | db: `require(db=True)` under a non-`--db` wrapper, then under `--db`. Container (a fake `/.dockerenv`, injected through the `in_container`/`inContainer` parameter): `slot` and `db`, with a non-db and a db caller | non-`--db`: refused, database-job reason; `--db`: passes. `slot` passes a non-db caller and refuses a db caller; `db` passes both |
| P-T5 | shim: a fake `<M>/frontend/node_modules/typescript/bin/tsc` that prints `REAL TSC`, then `install` | unpooled `.bin/tsc` exits 69; pooled prints `REAL TSC`; `check` is 0 after install and 1 after `.bin/tsc` is restored to the original symlink; a second `install` changes nothing |
| P-T6 | **live, in this worktree: run once by hand and record it in the packet; not part of check-all.** `cd frontend && npx vitest run <one small test file>`, then its pooled form | refused unpooled; passes pooled. This is the only live vitest run in T1 |
| P-T7 | the pwsh `Assert-HeavySlotHeld` | behaves as in P-T1 to P-T3 |

### 7.2 `tools/checks/test_heavy_slot_inventory.mjs` (static, under 2 s, every check-all run)

1. Every browser-launching file (per §5.4) contains `assertHeavySlot(`. A planted string fixture without it is
   reported.
2. Each §5.5 entry point calls `require("database job", db=True)` inside `main()` or the `__main__` block, never
   at module level. A planted module-level call is reported.
3. `vite.config.ts` has the VITEST tripwire, or its `globalSetup` names the fallback file.
4. Both conftests call `require(` in `pytest_configure`.
5. `package.json` has the postinstall line.
6. Both container `.ps1` runners call `Assert-HeavySlotHeld`, and `docker-compose.test.yml` passes
   `ASSETOPS_HEAVY_SLOT_CONTAINER`.
7. The §6 documents contain no command span for `npx tsc`, `npx vitest`, `-m pytest`, `run-host-tests.ps1 --`,
   `run-backend-suite-in-container.ps1 -` or `-evidence.mjs ` unless `heavy-slot.` comes before it on the same
   line. Two kinds of line are skipped: a line that contains the word `unpooled` or `refused`, which is how a
   document shows a refused example (R17a), and a line under a `##` heading whose name contains "history". A
   planted line is reported with its line number.

## 8. Planted-violation proof (RULES §7)

For each planted violation, record the real output, then restore the code.

| Violation | Planted change | Expect |
| --- | --- | --- |
| V1 | remove `assertHeavySlot(` from `tools/layout-evidence.mjs` | inventory check 1 fails |
| V2 | move the conftest `require` to module level, or delete it | inventory check 4 fails |
| V3 | `checkMarker` skips the directory comparison | P-T2 fails |
| V4 | `checkMarker` skips ancestry | P-T3 and P5c fail |
| V5 | the bash wrapper uses `>` and no `flock` | P2 and P3 **both** fail (R18a) |
| V6 | drop the child's fd close | P6 fails: the orphan keeps the lock |
| V7 | treat the marker as nested whenever it is set | P5 fails |
| V8 | skip `db-job.lock` | P9 fails |
| V9 | no TERM trap | P7 fails |
| V10 | V1 planted and uncommitted, then run check-all | the inventory guard shows FAIL |

## 9. Acceptance (questions the build must answer yes)

- **A1** Do check-all and both wrappers take the same two locks, and does each shell see the other's (P2, P2c,
  P3)?
- **A2** Is nesting free of deadlock across shells and checkouts (P4, P4b, P4c, P9b)?
- **A3** Is `D` the same for every caller, and immune to `GIT_*` and to the override (P4c, P5b, P-T2)?
- **A4** Are slots free after a SIGKILL of either wrapper or of the check-all path, and are trees gone after a
  TERM (P6-P8)?
- **A5** Does only one heavy database job run at a time (P9)?
- **A6** Does every tripwire refuse an unpooled run with the exact message, and pass a pooled one (P-T1 to
  P-T7)?
- **A7** Does the inventory hold, and does it catch each planted defect (§7.2)?
- **A8** Does each of V1-V10 fail as stated?
- **A9** Do the documents carry only pooled commands (§7.2 check 7)?
- **A10** Fast path: is the inventory guard at most 2 s; does the pool self-test print its SKIP line when no
  pool file changed; and is fast-mode wall time within 3 s of `main`'s (reviewer guide R6: 3 runs each,
  medians)?
- **A11** Does `Enter-HeavySlot` return within 0.1 s when a slot is free?
- **A12** Does `select-tests --base main` report `full`, for ALWAYS_FULL reasons only (conftest, compose,
  container runner, `vite.config.ts`, `package.json`)? Under D-T1.17 the §10 smoke set replaces the full suites.
- **A13** Is the pooled smoke set green (§10)?
- **A14** Is the `--json` output of `select-tests` unchanged?
- **A15** Does the packet record the mid-build question count?
- **A16** (post-merge, coordinator):
  - On main, `npm ci` or `node tools/heavy-slot-shims.mjs install frontend/node_modules` has been run, and
    `check-all -Full` shows `tsc shim installed` PASS.
  - In a lane worktree that has merged main, `cd frontend && npx tsc --noEmit` and `npx vitest run <file>` are
    refused, and the pooled forms run.
  - Each lane merges main before its next heavy command. Lanes 3 and 4 open only after that.

## 10. Checks and done

Checks:
- `node --test tools/checks/test_heavy_slot_pool.mjs tools/checks/test_heavy_slot_inventory.mjs`.
- P-T6, by hand.
- One fast check-all run at the end.
- The smoke set (D-T1.17), pooled:
  - `npx tsc --noEmit`;
  - one focused vitest file;
  - on the coordinator's DB turn, `tests/test_pg_harness.py` and one host Postgres file
    (`host/tests/test_up1_reading_upload_flow_postgres.py`), each run once unpooled (refused) and once pooled
    (passes).
- No full suites. They wait for the next milestone run, which uses `--db`.

**Done** when:
- A1-A15 hold, with real output in the packet;
- V1-V10 are recorded;
- the build used at most three commits, staged by explicit path.

The packet is `specs/T1-heavy-tool-slot-pool/packet.md`, at most 3k tokens. It records the mid-build question
count, the A10 figures and which vitest tripwire form was used.

## 11. Out of scope

- Two slots for one database job, until DM05 is measured (D-T1.4).
- A FIFO queue against starvation (D-T1.18; a follow-up if starvation is seen).
- The Claude Code hook, `classify` and `sweepDoc` (D-T1.6 and D-T1.8 are superseded).
- Windows hardware verification, and the Windows `.cmd` tsc shim.
- `frontend/mockups/v69` and `frontend/mockups/v71`.
- Pooling servers, and changing check-all's guard set, its timeouts or its `-Slots` default.

## 12. Sizing

About 2.75 units, still inside B03's 2-3:

| Part | Units |
| --- | --- |
| pool, module, check-all, P1-P15 | 1.0 |
| check modules, shim, P-T1 to P-T7 | 0.75 |
| 30 capture files, 11 database entry points, conftests, runners and the inventory guard (mechanical) | 0.75 |
| documents and `select-tests` | 0.25 |

No split. If P2 or P3 is flaky, or P-T6 fails in both vitest forms, stop and raise it.
