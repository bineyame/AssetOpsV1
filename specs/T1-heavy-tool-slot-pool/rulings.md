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

- `D-T1.5` **What is pooled.** tsc, vitest, every backend, host or gateway pytest run (not only Postgres
  files), the container and host suite runners, browser captures and heavy database jobs. Guard self-tests
  under `tools/` are not pooled. Why the pytest scope is broad: 199 test files have `postgres` in their name,
  but many Postgres modules do not (for example `test_w401_work_api.py`), and a hook that sees only a command line
  cannot tell them apart. A pooled non-database pytest run costs a few seconds of a slot (the queue model in B03
  gives a mean wait of about 3 s). This widens B03's "backend test files that use Postgres", so it is put to the
  owner below.

- `D-T1.6` **Enforcement: a Claude Code `PreToolUse` hook on Bash, plus the rule.** The hook is
  `.claude/settings.json` running `tools/heavy-slot-hook.mjs`, as B03 specifies. It fails closed when it cannot
  parse a command that looks heavy, and is otherwise open, so a hook defect cannot block unrelated work. Known
  gaps, which RULES §7 still binds: script files, a heredoc fed to a shell, `eval`, aliases, Codex sessions, the
  Monitor tool and a human terminal. In-tool tripwires (in conftest or the vitest config) are deferred, because
  touching the test harness makes select-tests choose the full suite.

- `D-T1.7` **Not pooled: check-all and long-running servers.** Check-all takes its own slot. A demo `serve`,
  the vite dev server and uvicorn would each hold a slot for hours. A capture's servers run outside the pool,
  and the capture itself runs inside it.

- `D-T1.8` **Class fix for copyable commands.** The class is an unpooled heavy command in a document that agents
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

## For the owner (defaults applied, W3)

1. **Pytest scope (D-T1.5).** Every backend pytest run goes through the pool, not only Postgres files. Default:
   yes. Example: a three-file no-database run waits about 3 s at most for a slot on average.
2. **Codex outside the hook (D-T1.6).** Codex is covered by its brief only. Default: yes while Codex only
   plans and does batched reviews. Revisit this if Codex is given build or test duties.
3. **Two slots for a large database job (D-T1.4).** Deferred until the DM05 measurement. Default: one slot plus
   the DB lock.

## Handshake answers (round 1)

(The Architect answers each question in `handshake.md` here, by its number, and folds the answer into
`spec.md`.)

## Mid-build rulings

(None yet. Each one stops only the affected part (RULES §4 item 7); the reviewer guide is updated if the done
criteria change.)
