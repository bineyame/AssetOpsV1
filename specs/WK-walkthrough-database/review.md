# WK review

## Round 1: discovery review (fresh Claude reviewer, 2026-11-21)

**Summary.**
- Verdict: **ACCEPT WITH FIXES.** Fix H1 and M1 on the branch, then a verification re-review. M2 needs a one-line ruling or fix. The L items are optional.
- Reviewed: `task/WK-walk-world` at `0f9a1f2b2`, diffed against `git merge-base main HEAD` = `3e77a8575`. The tool commit is `11bf658ed`; the two later commits change docs only.
- The name, URL and copy guards hold under adversarial input. The copy issues one DDL, and W1 to W7 all run.
- H1: on this machine `stop` cannot stop the web child. npm 11.19.1 renames its process and drops the `--`, so the match fails.
- M1: `stop` can signal another process's whole group if a reused PID loosely matches. Record the start time and check the group leader.
- M2: no slot assertion is reachable on the smoke's browser path.
- Checks: WK+DS4 tests `122 passed in 4.27s`; fast check-all `All 42 guards passed` (exit 0). 5 spot-checked plants and 3 of my own each fail their test.
- Not verifiable here: the live serve, the smoke PNGs (the D-WK.12 one-figure read) and the real adapters. All wait on the coordinator's §5 run.

### Findings

**H1 (High, acceptance gap: spec §3.6 `stop`, D-WK.7 teardown).** `tools/walk_world.py:342-356` (`cmdline_matches`), used at `:507`, `:888-896` and `:910`; test `backend/tests/test_wk_walk_world.py:846-857`.
- **What is wrong.** On this machine, npm (11.19.1, node v24.22.3) renames its own process. I spawned the tool's exact web argv in a scratch package with `start_new_session=True`. No server and no port were opened: the script was `sleep 4 #`. `/proc/<pid>/cmdline` then read `['npm run dev --port 5491 --strictPort --host 127.0.0.1']`, with the `--` gone. `cmdline_matches(that, web_argv)` returns **False**. T9 assumes the form `"npm run dev -- --port 5491"`, which npm does not produce.
- **Why it matters.** `stop` will treat the live Vite child as a reused PID (`WALK_PID_REUSED`) and leave it running. It then sets `serve` to null, so `drop` goes ahead. Vite (npm, sh and node in one group) keeps 5491 open, and the next WK serve is refused with `WALK_PORT_BUSY`. Teardown becomes a manual kill on a server where the 13 Nov serve (5490) runs too. A manual kill there is the riskiest step in this slice. `status` also reports the web child as not alive.
- **Fix.** Make PID identity independent of the cmdline (see M1). At spawn, record the child's start time (`/proc/<pid>/stat` field 22) and that it leads its own group and session (`getpgid(pid) == getsid(pid) == pid`). In `stop`, `serving` and `status`, treat the child as ours only when both still hold. Keep at most a loose sanity check on the cmdline. Replace T9's synthetic npm form with the observed one, and add a test that the observed form is stopped.

**M1 (Medium, safety: the riskiest point named in the dispatch).** `tools/walk_world.py:352-356` and `:386-390`.
- **What is wrong.** The loose match accepts any cmdline that ends with the recorded tail and has any earlier token whose basename equals `argv[0]`'s. These all return True:
  - `bash -c "cd x && python -m uvicorn lab_app:app --host 127.0.0.1 --port 8991"`
  - `timeout 60 python -m uvicorn ...`
  - `sh -c "npm run dev -- --port 5491 ..."`

  `Procs.killpg` then signals `os.getpgid(pid)`, which is the matched process's group. If that process is not a group leader, the group is someone else's: a shell, a heavy-slot wrapper or an agent.
- **What is not wrong.** The 13 Nov serve and DDR's serve cannot match, because the tail carries the port (8991 or 5491, against 8990/5490 and 8992/5492). A wrong kill needs the exact PID to be reused by a same-port wrapper command. That is unlikely, but the guard should not depend on luck.
- **Fix.** The fix is the same as H1's. Before any signal, require `os.getpgid(pid) == pid` and that the recorded start time is unchanged. Both always hold for the real children, which run under `start_new_session=True`, so no live child is missed. Then signal `pid` as the group id. Add a T9 case: a matching cmdline whose pgid differs from its pid gets no signal.

**M2 (Medium, rule: RULES §7 / T1; packet deviation 8 asks for a ruling).** `tools/walk_world.py:828-851` and `:937`; `tools/walk_world_smoke.cjs:32-33`.
- **What is wrong.** `smoke` launches Chromium, but nothing asserts the slot. The node env is fixed at six names (I3), so the slot marker never reaches `node`. The Python side does not call `require` for `smoke`. The inventory tripwire (`tools/checks/test_heavy_slot_inventory.mjs` LAUNCH regex) misses the script, because it says `require(process.env.PW)` and never names playwright.
- **Why it matters.** The only protection is the runbook's habit, §5 step 8 (`tools/heavy-slot.sh -- python tools/walk_world.py smoke`).
- **Fix.** Before S3, call `walk.deps.world.require("walk-smoke")` (no `db`). The Python process is the one that `heavy-slot.sh` wraps, so the check is real, and I3's six names stay as they are. Assert it in T8. Then either add the word to the script's header comment so that the inventory lists it, or record that it is exempt because the parent asserts. This is a small spec deviation from §3.1 ("serve, smoke ... do not"), so the Architect should note it.

**L1 (Low).** `tools/walk_world.py:782-789`. `--port` and `--web-port` overrides are checked only against `PROTECTED_PORTS`, not against the definition reader's range check (1024 to 65535) or `port != web_port`. Reuse `_port()` and the inequality check.

**L2 (Low).** `tools/walk_world.py:435-440`. A `walks/` folder that already exists is used without checking its mode, owner or symlink. `_private_dir` checks the state root only. Run `_private_dir(d, "WORLD_STATE_INVALID")` on the folder as well.

**L3 (Low).** `tools/walk_world.py:796-797`. If the second `spawn` raises (for example, `npm` is not on `PATH`), the API child is left running and unrecorded. Wrap the second spawn, and kill the first child on failure.

**L4 (Low, residual).** `stop` signals only a live recorded leader. If npm dies but Vite lives on in the group, `stop` reports the child "already gone" and leaves the group alive. Once the start time is recorded (H1), the fallback can `killpg` the recorded pgid while any member of the group still runs.

### Judged points (dispatch 1 to 8)

1. **`walk_url`.** Probed through `walk_url` and `walk_name_ok`, with no database.
   - Refused:
     - `1113` (`WALK_PROTECTED`);
     - labels with a trailing space or newline, fullwidth or Arabic-Indic digits, a Cyrillic or fullwidth `a`, quotes, `;`, `/`, or `?dbname=...` (all `WALK_LABEL_INVALID`, ASCII `fullmatch`);
     - names in upper case, with `\n`, with fullwidth digits, or with a trailing space (`walk_name_ok` False);
     - `PGDATABASE` and `PGSERVICE` (`ENVIRONMENT ...`);
     - `ASSETOPS_PG_PORT=8990` (`port`) and a port with an injected path or query (`QUERY_KEY`, `name`);
     - an `ASSETOPS_PG_PASSWORD` carrying `?dbname=` (`QUERY_KEY dbname`) or `@host/db` (`name`).
   - A password holding `/...?host=` parses (through the same `make_url` that every engine uses) to host `127.0.0.1` and the walk name, so the target is unchanged.
   - Every guarded child gets a built env. `PGOPTIONS`, `PGSSLMODE` and `PGPASSFILE` do not change the target.
   - Symlinked trees: `refuse_walk_tree` uses `realpath` (T8 covers a symlink).
   - `World.census`, `World.exists` and `check_name` are never called on the walk name. T12 checks this by AST, and PL10 fails it.
   - `1113a` is accepted as a different name, as the spec intends; a `drop` needs a walk manifest, which only `copy` writes.
2. **Copy.** The parent comes only from `current_l2` and then `check_state`. Stale, unchecked and failed parents are refused (T2; PL1 fails T2). The L2 name is re-validated against `_L2` and the prefix. There is exactly one DDL, `CREATE DATABASE ... TEMPLATE ... STRATEGY FILE_COPY` (T3). RV2, an `ALTER` on the L2, fails T3.
3. **Serve.** 8991/5491 from the definition. 8990/5490 are refused in the definition and through `--port` and `--web-port` (T8). RV3 limits the check to the definition and fails T8. The 13 Nov tree and its subpaths are refused by realpath (PL13 fails T8 and T12). `/opt/assetecon/keys` appears nowhere, and the 13 Nov tree path only in `refuse_walk_tree` (T12). The API env has no key folder or switch. The argv and cwd match §3.5 and the `demo_combined.py` mechanism.
4. **Smoke.** S4 re-runs the W3 judge read-only through `walk_url`'s URL, and PL11 fails T5. The node env is exactly six names (T8), and the env.sh child gets only PATH, HOME and LANG. The missing slot assertion is M2.
5. **Stop.** See H1, M1 and L4. The 13 Nov serve and DDR's serve cannot be matched, because the ports differ.
6. **Prepare and check.** The argv equals §3.3, and `E` is built. Every check runs after a FAIL (`_guard`; T6 and PL7 per the packet). Only `CapExceeded` stops the run (exit 5).
7. **Text and figures.**
   - Output is JSON and codes, on stdout and stderr only. There is no new served English.
   - `source_ref` is never returned by a served read. I grepped the diff, every `*_api.py`, `deep_dive/` and `frontend/src`. The only `*_api.py` hit is `financial_api.py:167`, the assumptions' own `source_reference`.
   - The figures match DDR S5 and S8, and the text says "Emulated".
   - D-WK.12: not verifiable until the coordinator's smoke PNGs exist.
8. **Plants.**
   - Method: a scratch copy of the tool and its test file, with the rest of the tree symlinked. In that copy T4 fails on its own (its PYTHONPATH assertion names the real repo), so only failures beyond that baseline count.
   - Spot-checks: PL1 fails T2, PL9 fails T1 (`walk_name_ok_refuses`), PL10 fails T12 (and many others), PL11 fails T5 (S4), and PL13 fails T8 (`tree_refusal`) and T12.
   - My own plants:
     - RV1: `stop` ignores the cmdline. It fails T9 (`leaves_reused`).
     - RV2: `copy` issues `ALTER DATABASE <L2> ... true` first. It fails T3 and T10, among others.
     - RV3: the port refusal checks only the definition. It fails T8 (`protected_ports`).
   - The worktree was never edited.

### Checks run (by this reviewer, at `0f9a1f2b2`)

- `tools/heavy-slot.sh --wait-seconds 3000 -- .venv/bin/python -m pytest backend/tests/test_wk_walk_world.py backend/tests/test_ds4_world.py -q`: `122 passed in 4.27s`.
- `bash tools/heavy-slot.sh --wait-seconds 3000 -- pwsh -NoProfile -File tools/check-all.ps1`: `check-all: 147.2 s wall (0.2 s waiting for a slot), 4 jobs at once. All 42 guards passed (blocking; 0 advisory, 0 warned).`, exit 0.
- The `walk_url` probes and the npm process-title probe ran in scratch. Neither touched a database, a port, a server, Docker, the walk tree or the keys.

### Residual risk not in the packet

- The npm title form may differ under another npm version. H1's fix removes the dependence.
- `stop` nulls `serve` even when it leaves a child, so a later `drop` relies on the 5 s session check alone.
- D-WK.12 and S3 depend on the coordinator reading the PNGs.

## Round 2 (verification, fresh Claude reviewer, 2026-11-21)

**Summary.**
- Verdict: **ACCEPT WITH FIXES.** H1, M1, M2 and L1-L3 are closed. The L4 group fallback opens one new wrong-signal path (M3). Fix it on the branch, then a short verification of M3 only. L5 and L6 are optional.
- Reviewed: `task/WK-walk-world` at `8e71a10d0`, the fix diff `a736d9bc3..8e71a10d0` (code in `7218b2835`).
- H1: the npm 11 title (no `--`) is matched exactly, and identity rests on start time and group, not the cmdline.
- M1: a wrapper never matches, and no signal goes out unless the PID leads its own recorded group with the recorded start time.
- M3 (new, Medium): with the leader gone, `members` accepts any group whose id is the recorded pgid. After a PID wrap, a foreign process can own that id. Reproduced on real `Procs` with a recording `killpg`.
- The 13 Nov serve cannot be signalled on any path. Its processes predate the record, and its group id can never equal ours.
- Checks: WK+DS4 `149 passed in 5.50s`; fast check-all `All 42 guards passed` (exit 0). 7 of 15 plants spot-checked, all fail their tests. Of my 2 plants, 1 survives (L6).

### Findings

**M3 (Medium, safety: a new path from the L4 fix).** `tools/walk_world.py:469-481` (`members`), used at `:486-490` and `:495-501`.
- **What is wrong.** The fallback is used when `/proc/<pid>` is absent. It then signals the recorded pgid if every process in that group is in session `pgid` and started at or after the recorded start time. Our group can empty: Vite exits, or the box runs on after a crash. The kernel then frees the PID, and after a wrap (`pid_max` here is 4194304) another process can take it. If that process calls `setsid`, forks and exits, its children have pgrp = session = the recorded pgid and a later start time. This is the usual daemonise pattern, and also `Popen(start_new_session=True)` around a shell that backgrounds a job. They pass both member checks, and `stop` sends SIGTERM and then SIGKILL to that foreign group. `status` and `serving` also report it alive.
- **Reproduced** (scratch, no port, no server): a `sh -c "sleep 20 & exit 0"` started with `start_new_session=True`, reaped, then a record naming its PID with an older start time. `checked` = `gone`, `members` = `([sleep], [])`, `alive` True, `signal` returned None and called `killpg(<that pgid>, SIGTERM)` on the recording stub.
- **Why it matters.** Round 1 never signalled once the leader was gone. The fix added a path that can hit another agent's process tree, so the guard again depends on luck (the M1 class). The odds are small: an exact PID reuse after a wrap, plus that pattern. The 13 Nov serve is still safe.
- **Fix.** Bound membership by what was ours. The kernel keeps a group id reserved while any member lives, so a process recorded as a member stays ours for as long as it lives. When serve succeeds, record the group's live members as `[pid, start_time]`. In the fallback, signal only when every live member of the pgid is one of those recorded pairs; anything else is `group_unverified`. Two other ways also work: record the boot-tick time at which serve succeeded and require `start_time <= ready_ticks`, or drop the fallback (L4 was optional) and report `WALK_GROUP_LEFT <pgid> <pids>`. Add a T9 case: leader gone, and a member with a later start time that was not recorded gets no signal.

**L5 (Low, residual; fail-safe).** `tools/walk_world.py:451-467`. An unreaped zombie leader still has `/proc/<pid>/stat` (same start time, `getpgid` works) but its cmdline is empty. `checked` therefore returns `cmdline`. The result is no signal, a wrong `WALK_PID_REUSED <pid> cmdline` label, `alive` False, and live members left running (probe: zombie plus a live `sleep` in the group). In the real `stop` the leader's parent is init or a subreaper, which reaps it, so this matters only while a parent holds it. That was the case in the packet's live check, where the leader ended as a zombie. While the leader is a zombie its PID stays reserved, so the group is provably ours. Read the state field (`Z`), treat it as `gone`, and let the M3-bounded fallback run.

**L6 (Low, test gap).** `tools/walk_world.py:480`. My plant RV-A removed `st["session"] == pgid and`, and no test fails. Add a member whose session differs to `test_t9_stop_refuses_a_group_member_older_than_the_leader`, or fold this into M3's test.

### Closed (verified)

1. **H1, M1, L4.** `Procs.spawn` (`:426-437`) passes `start_new_session=True` and records pid, argv, start time (field 22, `parse_stat` `:400-411` parses after the last `)`) and pgid. `checked` (`:451-467`) requires, in this order: all three are ints; `/proc` is present; the start time is unchanged; `getpgid(pid) == pid`; the recorded pgid equals pid; an exact cmdline. Only then does `signal` call `killpg(rec["pgid"])`. `cmdline_matches` (`:346-367`) accepts the argv, `node <path>/{npm,npm-cli.js} <exact tail>`, or one title equal to the argv joined (npm: joined without `--`). `bash -c`, `sh -c`, `timeout`, a one-string wrapper, a port change and `54911` are refused (T9).
   - Attacks:
     - (a) A reused PID with a matching start time but another group: refused `not_leader`. A start-time tie needs PID reuse within one clock tick.
     - (b) A process that calls `setsid` itself: as a reused leader, refused by start time. As one of our members, it leaves the group and is not signalled (a leak, not a wrong kill).
     - (c) A zombie leader: fail-safe, see L5.
     - (d) The leader gone and its PID reused by a session leader that exited: M3.
   - The live stop evidence (packet `:75-79`) matches the code. It records start time and pgid, the npm 11 title passes `checked`, `stop_child` empties the group of 3, and the zombie that remains is the harness's own child.
   - The 13 Nov serve (8990/5490, started 13 Nov) fails the start-time check as a leader, falls into `bad` as a member, and its group id cannot be ours. It is never signalled.
2. **M2.** `cmd_smoke` `:978` calls `walk.deps.world.require("walk-smoke")` after `WALK_NOT_SERVING` and before S1-S3. `world._real_require` reaches `heavy_slot_check.require`, which calls `sys.exit(69)`. T8 `test_t8_smoke_requires_a_slot_before_chromium` asserts exit 69 and no `node`/`bash` call. Packet deviation 8 still needs the Architect's ratification.
3. **L1** `:924-928`: the range is 1024-65535 and the two ports must differ (T `test_l1_*`, 5 cases). **L2** `:569-577`: `lexists`, then `lstat` must show a directory, our uid and `mode & 0o077 == 0`; a symlink, a file, group or world access, or another owner is refused. **L3** `:940-944`: an `OSError` from the web spawn SIGKILLs the API child after the same checks and fails `WALK_SERVE_FAILED web spawn <type>`. If the checks refuse, it reports `WALK_PID_REUSED`.
4. **No regression.** `walk_url`, `walk_name_ok`, the copy path and `refuse_walk_tree` are untouched by the diff. The `WALK_PORT_PROTECTED` refusal still runs before the new range check. T1-T3, T8 port refusals and T12 (AST) pass.
5. **Plants** (scratch copy; T4's PYTHONPATH baseline failure excluded):
   - P1 → 1 failed, P2 → 2, P4 → 5, P8 → 1, P9 → 2, P12 → 2, P15 → 2. Each matches the packet.
   - Mine: RV-B (`stop_child` swallows `group_unverified`) → 1 failed (`older_than_the_leader`). RV-A (session check removed) → 0 failed (L6).

### Checks run (by this reviewer, at `8e71a10d0`)

- `tools/heavy-slot.sh --wait-seconds 3000 -- .venv/bin/python -m pytest backend/tests/test_wk_walk_world.py backend/tests/test_ds4_world.py -q`: `149 passed in 5.50s`.
- `bash tools/heavy-slot.sh --wait-seconds 3000 -- pwsh -NoProfile -File tools/check-all.ps1`: `check-all: 144.5 s wall (0.2 s waiting for a slot), 4 jobs at once. All 42 guards passed (blocking; 0 advisory, 0 warned).`, exit 0.
- The probes used real `Procs` with a recording `killpg` on `sh -c "sleep 20 & exit 0"` children in scratch. They touched no database, port, server, Docker, walk tree or keys. The probes' own `sleep` groups were killed after.

### Not verifiable here

The live serve against the walk database and the real npm/Vite group under `stop`, apart from the scratch `sleep` stand-in. Those wait for the coordinator's §5 run.

### Residual risk not in the packet

- `stop` still sets `serve` to null when a child was refused, so `drop` relies on the session check alone (as in round 1).
- A member that calls `setsid` leaves the group and outlives `stop`. Vite does not do this today.
