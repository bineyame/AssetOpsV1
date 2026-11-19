# T1 reviewer guide

For the fresh Reviewer of T1, the heavy-tool slot pool. Use it with `spec.md`; the rulings are in `rulings.md`.

**Review depth:** discovery (W5). T1 is a new mechanism that every lane depends on, and lanes 3 and 4 open on
it. Read `spec.md` §2-§5 closely; the rest can be checked against the code.

**Before coding:** read this guide and `spec.md`, then put your questions in `handshake.md` "Reviewer
questions", in the same round as the Implementer's pre-flight. If a question would change what counts as done
here, say so; the Architect updates this guide when it answers.

**Rules for your probes:**
- Every probe that takes locks sets `ASSETOPS_HEAVY_SLOT_DIR` to a private `mktemp -d` directory. On the real
  directory, use only `--status`.
- Stop every process you start, by PID only.
- No suites, no Postgres, no Docker, and no browser beyond what the spec's tests start. Stay off ports 5490 and
  8990.
- Do not commit into the Implementer's worktree. For R6, use detached scratch worktrees and remove them when
  you are done.

## What counts as done

- A1-A12 in `spec.md` §9 each answer yes, and you have seen the real output yourself, not only in the packet.
- V1-V6 (§8) each fail as stated. You reproduce at least V1, V4 and V5 yourself.
- The files touched are exactly those in `spec.md` §3-§6 and §7, plus the packet. Anything else is a finding.
- The packet (`specs/T1-heavy-tool-slot-pool/packet.md`, at most 3k tokens) records the **count of mid-build
  questions** (RULES §4 item 7). A missing count is a finding. A count above zero is reported as a defect in the
  spec template, not in the Implementer's work.
- A13 is post-merge and the coordinator's. Your verdict says it is pending, and that lanes 3 and 4 wait for it.

Severity: a bypass of a form listed in §4 (anything other than the documented gaps in D-T1.6), a deadlock, a
leaked lock, or a slower fast path beyond A10 is **High**. A wrong message or exit code is Medium. Wording is Low.

## Probes

### R1 Deadlock

- Run P4 by hand. With holder X on one slot, run a pooled `sh -c` that starts a pooled pwsh, which starts a
  pooled bash. The command must finish in under 5 s.
- Check-all inside the pool: with X on the other slot, run `tools/heavy-slot.sh -- pwsh -NoProfile -File
  tools/check-all.ps1`. It must print `inside a held heavy slot` and not wait. This is the one real-directory
  check-all run you make. Run it only when `--status` shows both slots free, and use a private directory for X.
  If you cannot do both, run it with `ASSETOPS_HEAVY_SLOT_DIR` set for both.
- A nested DB job: a pooled non-DB command that runs `--db` while a DB job holds `db-job.lock`. It must time out
  with exit 75 within the wait. It must not hang.
- Read `Enter-HeavySlot` and the bash acquisition. Confirm the order is always the DB lock first, then a slot,
  and that no code path waits for a second slot while holding one.

### R2 A leaked lock

- P6 and P7 by hand. After `kill -9` of the wrapper, `--status` shows the slot free at once.
- The orphan child: confirm with `ls -l /proc/<child>/fd` that the child holds no fd on `slot-N.lock`. This is the
  V5 property.
- A capture-style orphan: run `tools/heavy-slot.sh -- sh -c 'sleep 60 & exit 0'`. The wrapper exits, the slot is
  free, and `sleep` lives on without the lock. Kill it by PID.
- pwsh: check that `heavy-slot.ps1`'s child does not inherit the stream. .NET opens with `O_CLOEXEC`; check the
  child's `/proc/<pid>/fd` the same way.
- Owner files: after any exit, an owner file is gone or no longer names a live `pid=`, and `--status` reports
  `holder unknown` only when the lock is really held.

### R3 Bypass

Feed each of these to `node tools/heavy-slot-hook.mjs` as hook JSON on stdin. Expect exit 2, except where a
case is marked as a documented gap:
- `cd frontend&&npx tsc --noEmit` (no spaces around `&&`)
- `(cd frontend; npx vitest run x)`
- `npx  --yes  vitest run x`
- `NODE_OPTIONS=--max-old-space-size=4096 npx tsc`
- `npm exec -- tsc`
- `pnpm vitest`, which should refuse through the `vitest` word
- `/opt/assetecon/AssetOpsV1/.venv/bin/python -m pytest backend/tests/test_x.py`
- `python -m pytest ./backend/tests`
- `python -m pytest tools/checks/test_a.py backend/tests/test_b.py` (one non-tools target)
- `bash -lc 'python tools/demo_combined.py --db x_test --work w prepare'`
- `xargs -a files.txt npx vitest run`
- `tools/heavy-slot.sh -- true; ASSETOPS_HEAVY_SLOT=$HOME/x npx tsc`
- `timeout 900 node tools/layout-evidence.mjs`
- a fake wrapper: `./heavy-slot.sh -- npx tsc` in an arbitrary directory. This is allowed by design. Record it
  as a residual risk; it is not a finding.
- documented gaps (expect allow, record only): `sh run.sh` where the script runs tsc; `bash <<EOF` with tsc in
  the body; `eval "$CMD"`.

Report any other allowed heavy form as High, with the rule it should have matched.

Check the false positives too, which must allow: a `git commit -m` naming vitest, `grep tsc`, heredoc docs, and
`demo_combined.py serve`. Also read `.claude/settings.json`: it must have only the hook key, and there must be no
change to user or local settings.

### R4 Both platforms

- On Linux, both shells: P1-P13 pass. Run P2 and P3 twice each, because the interop between bash and .NET is the
  core claim.
- Run `heavy-slot.sh` with `flock` hidden from it: `PATH` set without `/usr/bin` while keeping `pwsh`, through a
  private bin directory with symlinks to `pwsh`, `git` and `env`. It must hand over to `heavy-slot.ps1` with the
  options translated, and the result must be the same.
- Windows: there is no hardware here, so review by inspection (D-T1.10). Check that the pwsh path uses the same
  `[IO.File]::Open(..., 'None')` call as before. Check that it uses no Linux-only API outside the
  `PosixSignalRegistration` guard. Check that `Get-HeavySlotDir` joins paths with `[IO.Path]` and not with `/`.
  Check that the Windows `.cmd` shims (`npx.cmd`) resolve through `Get-Command -CommandType Application`.
  Record this as "verified by inspection", not as tested.

### R5 The guards fail on a real violation

- Plant V1, V4 and V5 yourself and see each fail, then restore them. Check that V6's check-all output names the
  hook guard as FAIL.
- K6: plant an unpooled fenced command in `.claude/agents/assetops-reviewer.md`. The sweep must name the file and
  line.

### R6 No slowdown of the fast check-all path

- Make two detached scratch worktrees, at `main` and at the T1 head. Use the `.venv` and the frontend install the
  way the lane rules say.
- In each, run check-all twice in fast mode, `-Base <head>~1`. At `main`, `-Base main~1` makes it fast. At T1,
  `<T1 head>~1` puts only the docs commit in the change. Run on a quiet machine with `--status` free.
- Record the wall time, the `waiting for a slot` value (at most 0.1 s when free, A11) and the hook guard's time
  (at most 10 s).
- Pass: the T1 median is within 3 s of the `main` median, and the T1 run prints the pool self-test SKIP line.
  Remove the scratch worktrees afterwards.
- Hook latency (K5): 20 timed calls, median under 150 ms. Report the figure.
- Read the check-all diff. Apart from the slot block, the marker export, the two guards, the skip line and
  `finally`, nothing changes. Messages and exit codes match the old ones exactly, because coordinator scripts match
  the summary lines.

### R7 Documents and commands

- Run `git grep -nE 'npx (tsc|vitest)|-m pytest|run-host-tests|evidence\.mjs|demo_combined\.py [a-z-]*'` over the
  §6 documents. Every hit is either pooled or prose that the sweep rightly skips.
- Check that the RULES §7 text matches spec §6 and that RULES stays within its cap.
- Check that `select-tests.py`'s `--json` output is unchanged (diff the output before and after for the same
  `--files`), and that the T1 branch selects `mode: none` (A12).
- Check that the W6 sweep is recorded in the packet: the class, the documents swept and the result.

## Risks to keep in view

- **.NET may not use `flock`.** If P2 or P3 is flaky, the slice stops (D-T1.2). Do not accept a retry loop as a
  fix.
- **Over-refusal.** Read every refusal in the K1 table and ask whether an agent's normal command would be refused.
  Common forms are `cd x && ...`, `setsid nohup ... &` and `2>&1 | tail`. Blocking normal work is Medium.
- **Hook fail-closed scope.** Confirm the prefilter is as in the spec, so that a broken classifier cannot block
  `git` or `ls`.
- **A slot held for hours.** Check that no pooled form in the docs wraps a server (`serve`, `npm run dev`).
- **The coordinator's after-merge `-Full` run.** It takes one slot, as before. Check that nothing makes it take
  two.
