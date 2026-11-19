# T1 reviewer guide (rev 2: option C, in-tool tripwires)

This guide is for the fresh Reviewer of T1. Read it with `spec.md` rev 2. The rulings are in `rulings.md`; the
handshake round is closed. Rev 2 replaces the hook with in-tool tripwires (owner: "C for T1"). The probes of the
rev 1 hook and classifier are gone.

**Review depth:** discovery (W5). T1 is a new mechanism, and lanes 3 and 4 open on it.

**Probe rules:**
- For any lock probe, use the self-test's temp repository harness (spec §7.1), or a private `mktemp -d` with
  `ASSETOPS_HEAVY_SLOT_DIR`. Tripwires ignore that variable, so it gives no bypass.
- On the real pool, use only `--status`, and run check-all only when `--status` shows a free slot.
- Stop every process you start, by PID only.
- No full suites and no Docker. Stay off ports 5490 and 8990.
- The Postgres smoke run needs the coordinator's DB turn.
- Do not commit into the Implementer's worktree. For R6, use detached scratch worktrees and remove them
  afterwards.

## Done

- Every question A1-A15 in spec §9 answers yes, and you have seen the output yourself.
- V1-V10 fail as stated. Reproduce V3, V4, V5, V6 and V10 yourself.
- The files touched are exactly those in spec §3-§7 plus the packet. Anything else is a finding. That includes a
  `.claude/settings.json`, which must not exist.
- The packet records the **count of mid-build questions** (RULES §4 item 7). A missing count is a finding. A
  count above zero is a spec-template defect, so report it, but not against the Implementer.
- The packet names which vitest tripwire form was used (spec §5.3).
- A16 is post-merge and the coordinator's job. Your verdict states that it is pending and that lanes 3 and 4 wait
  on it.

**Severity:**
- **High:** any undocumented way to run a pooled tool unpooled; a deadlock; a leaked lock; a refused pooled run;
  a fast-path slowdown beyond A10.
- **Medium:** a wrong message or exit code.
- **Low:** wording.

## Probes

### R1 Deadlock

- Run P4, P4b and P4c by hand. Every nested entry finishes in under 5 s, from bash to pwsh, from the main
  checkout to a worktree, and through a symlinked path.
- Nested `--db` (P9b): exit 69 **at once**. A wait, even a bounded one, is High (D-T1.13).
- Check-all inside the pool: with X holding the other slot in the same pool, run `tools/heavy-slot.sh -- pwsh
  -NoProfile -File tools/check-all.ps1`. It prints `inside a held heavy slot` and does not wait. Run this with
  `ASSETOPS_HEAVY_SLOT_DIR` set on both commands, or for real only when `--status` shows both slots free.
- Read `Enter-HeavySlot` and the bash acquisition. The order is always the DB lock, then a slot. No nested path
  waits.

### R2 A leaked lock

- Run P6, P6b, P6c, P7, P7b and P8 by hand. After a `kill -9`, `--status` shows the slot free at once.
- Check `/proc/<child>/fd` for the bash child, the pwsh child and the `Enter-HeavySlot` child: none holds a lock
  fd.
- Capture-style orphan: `tools/heavy-slot.sh -- sh -c 'sleep 60 & exit 0'` frees the slot when the wrapper
  exits.
- Owner files: none is left naming a live `pid=` after an exit. `holder unknown` shows only while the lock is
  really held.

### R3 Bypass of the tripwires

Each attempt must be refused with exit 69 and the exact message, except where marked:
- an unpooled `npx tsc --noEmit`, `npm run typecheck` or `npm run build` against the P-T5 fake install;
- an unpooled `npx vitest run <file>` (P-T6, live);
- `npx vitest@<installed version> run <file>`;
- `ASSETOPS_TEST_DATABASE_URL=<x> python -m pytest backend/tests/test_pg_harness.py`, run under the conftest
  check. To avoid needing the database, check that it exits 69 before connecting;
- `python -c "import pytest; pytest.main(['backend/tests/test_pg_harness.py'])"` with the URL set;
- `node tools/layout-evidence.mjs`;
- `node tools/evidence-checks.mjs --self-test`;
- `python tools/demo_combined.py --db x_test --work w prepare`, unpooled, and pooled without `--db`;
- `python tools/demo_combined_kobo.py build <url> <w>` run directly;
- `python tools/mechanism_dataset.py ensure`;
- a forged marker naming another holder's slot (P-T3);
- a wrapper using `ASSETOPS_HEAVY_SLOT_DIR` (P-T2);
- `GIT_DIR=/tmp/x` on the wrapper (P5b);
- an orphan that keeps a stale marker after its wrapper dies (P5c);
- the container path:
  - `ASSETOPS_HEAVY_SLOT_CONTAINER=slot` **outside** a container must not pass;
  - inside a container (inspection plus P-T4), `slot` must not pass a database job.

**Documented gaps.** Expect each to run unrefused, and record it only:
- `node frontend/node_modules/typescript/bin/tsc`;
- vitest run by its `.mjs` with `--config` pointing at another file;
- an untracked scratch script that launches Chrome;
- Windows `.cmd` shims.

Any other refusal you can get past is High, and you name the tripwire that should have caught it.

**Must not refuse:**
- `demo_combined.py serve`, `links` or `drop`;
- `chain_clone.py drop`;
- `mechanism_dataset.py status`;
- pytest without a database URL;
- `node --test tools/checks/test_evidence_checks.mjs`;
- tests that import `demo_combined` (for example `test_ar2_prepare_period_rows.py`, without the database);
- `vite` and `npm run dev`;
- check-all.

### R4 Both platforms

- On Linux, P1-P15 and P-T1 to P-T7 pass. P2c runs its 20-iteration race inside the test. Run the file twice.
- `heavy-slot.sh` with `flock` hidden: use a private `PATH` that keeps `pwsh`, `git` and `env`. The script hands
  over to `heavy-slot.ps1` and gives the same results.
- Windows, by inspection (D-T1.10):
  - the pwsh path uses the same `[IO.File]::Open(..., 'None')` as before;
  - no Linux-only API is reached outside the `PosixSignalRegistration` and ancestry guards;
  - `Get-HeavySlotDir` uses `[IO.Path]` and compares without case on Windows;
  - `.cmd` shims resolve through `Get-Command -CommandType Application`.

  Record the result as "verified by inspection".

### R5 The guards fail on a real violation

Plant V3, V4, V5, V6 and V10 yourself, then restore each.

The inventory guard (spec §7.2) must name the file and line for each of:
- a capture script with the assert removed;
- a module-level `require` in a database script;
- a conftest without the check;
- an unpooled command in `.claude/agents/assetops-reviewer.md`.

### R6 No slowdown of the fast check-all path

Make two detached scratch worktrees, one at `main` and one at the T1 head.

In each, run check-all in fast mode **three** times, with `-Base <head>~1`:
- at `main`, `-Base main~1` gives fast mode;
- at T1, `-Base <T1 head>~1` covers the docs commit, which contains no pool file.

Record for each run:
- wall time;
- the `waiting for a slot` value, which should be at most 0.1 s when a slot is free (A11);
- the inventory guard's time, which should be at most 2 s.

Pass: the T1 median is within 3 s of the `main` median, and the T1 runs print the pool self-test SKIP line.

Read the check-all diff. Only these may change: the slot block, the marker export, the three guards, the trigger
generalisation, the SKIP line and `finally`. Every other message and the summary lines stay byte-identical.

### R7 Documents and select-tests

- Inventory check 7 is clean. Also grep the §6 files by eye for unpooled commands that check 7's patterns would
  miss.
- RULES §7 matches spec §6 and stays within its cap.
- `select-tests --json` output is unchanged (diff it for the same `--files`).
- `select-tests --base main` on T1 reports `full`, for ALWAYS_FULL reasons only (A12).
- The smoke set (D-T1.17) is in the packet with real output.

## Risks to keep in view

- **The vitest config tripwire.** Vite bundles `vite.config.ts`. Check that P-T6 really ran unpooled and was
  refused, and that `npm run dev` and `vite build` still start; the check runs only under `VITEST`.
- **The tsc shim lives outside git.** A coordinator `npm ci --ignore-scripts` would drop it. The `-Full` guard
  on main must then FAIL. Check that `check` really detects a restored symlink (P-T5).
- **Tripwire cost.** Each check spawns git once and reads `/proc`. Report the time `assertHeavySlot` adds to a
  pooled vitest start; under 200 ms is fine.
- **Starvation under a long `prepare`** is accepted (D-T1.18). Do not report a wait timeout under that load as a
  defect.
- **xdist workers and children of `prepare`** must pass by ancestry. Check one pooled `-n 2` run in the smoke set
  if the DB turn allows. If not, check the ancestry walk by reading the code.
