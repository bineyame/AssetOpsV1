# WK review packet (round 1)

Builder (Claude), 2026-11-21. Branch `task/WK-walk-world` off `main` `3e77a8575`; worktree `/opt/assetecon/AssetOpsV1-wk`.
Spec `spec.md` rev 2, `rulings.md` D-WK.1-14, `handshake.md` (R1-R6 and I1-I6 all answered), `reviewer-guide.md`.
`USER_REVIEW_REQUIRED`: false for the tool (non-screen, coordinator-only); the owner walks the served copy after §5.

## Outcome

`tools/walk_world.py` makes "clean and good" a command for the walkthrough copy. It copies the checked L2 at today's
key, adds the two emulated statements and one rebuild, checks W1 to W7, serves on 8991/5491, smoke-tests S1 to S4,
then stops and drops. No database was created, opened or dropped while building. No server or port was touched.

## Files

- New: `tools/walk_world.py`, `tools/walk_world_smoke.cjs`, `backend/conversions/walk-layer4-v1.json` (spec §2,
  verbatim), `backend/tests/test_wk_walk_world.py` (T1 to T12, fakes only).
- Docs: `spec.md` Status, `specs/INDEX.md` row, `.ai/state/data.md` WK entry, `.ai/state/index-3.md` line 189.
- Not edited: `tools/world.py`, `tools/checks/`, any product code, migration, route or screen.

## Acceptance (spec §6)

1. Copy is gated. It reads only `World.current_l2()` and then `World.check_state()`. Stale, unchecked and failed
   parents are refused, and a world refusal passes through (T2). Exit 2 with no DDL in every refusal.
2. One DDL. `CREATE DATABASE "<walk>" TEMPLATE "<l2>" STRATEGY FILE_COPY` through `deps.world.admin` (T3). The 13 Nov
   name, 8990 and 5490 appear only in `PROTECTED_DATABASES` and `PROTECTED_PORTS`. The 13 Nov tree path appears only in
   `refuse_walk_tree`, and `/opt/assetecon/keys` appears nowhere (T12, by AST).
3. W1 to W7 each fail on their plant (T6 parametrised: stale or failed parent, moved HEAD, a verify mismatch, an
   undeclared row, REBUILD_NEEDED, a wrong C4 value, L2 `datallowconn` true, a second walk database, an extra tenant,
   a missing step). Every check runs after W1 FAILs (T6).
4. Serve env. The API env is exactly the nine listed keys. The web env is its four, and the node env its six (T8).
   Ports 8990 and 5490 are refused in the definition (`WALK_DEFINITION_INVALID`) and on the command line
   (`WALK_PORT_PROTECTED`).
5. Smoke. S3 FAILs on any page with a status of 500 or more, a failed request, a pageerror or the cap. Each Site page
   is expanded (T11: 10 pages). S4 FAILs on a row written after the serve (T5).
6. Plants: below.

## Checks run (revision `11bf658ed`, tool commit)

- `/opt/assetecon/AssetOpsV1/.venv/bin/python -m pytest backend/tests/test_wk_walk_world.py -q`: `57 passed in 2.14s`.
- `tools/heavy-slot.sh -- .venv/bin/python -m pytest backend/tests/test_wk_walk_world.py backend/tests/test_ds4_world.py -q` at `11bf658ed`: `122 passed in 4.74s` (12 min wall, almost all waiting for a slot).
- `node tools/walk_world_smoke.cjs --help`: exit 0 (inside T11).
- Fast check-all (`pwsh -NoProfile -File tools/check-all.ps1`, at `a2ce293e9`): `All 42 guards passed (blocking; 0 advisory, 0 warned).` 219.1 s wall (74.3 s waiting for a slot), exit 0.
- Plants (each applied alone with `-k test_tN`, then `git checkout -- tools/walk_world.py`; the tree was clean after):

| Plant | Fails |
|---|---|
| PL1 accept `(None, None)` | T2 `test_t2_copy_refusals_in_order` |
| PL2 key folder in API env | T8 `serve_envs_and_argv`, `api_env_drops_every_forbidden_name` |
| PL3 census ignores other tables | T5 all three (judge, W3, S4) |
| PL4 allow `1113` | T1 `labels_and_names`, `cli_label_refusals` |
| PL5 `WITH (FORCE)` | T10 |
| PL6 accept `fresh.current` false | T7 both |
| PL7 stop at first FAIL | T6 `runs_every_check_after_w1_fails` |
| PL8 no `PROTECTED_PORTS` in reader | T8 `protected_ports` |
| PL9 prefix-only `walk_name_ok` | T1 `walk_name_ok_refuses` |
| PL10 `walk.world.census(...)` in W3 | T12 `no_world_write_or_name_check_on_the_walk` |
| PL11 smoke without S4 | T5 `smoke_s4_fails_on_a_row_written_after_the_serve` |
| PL12 node inherits env | T8 `smoke_node_env_is_exactly_six` |
| PL13 tree refusal off | T8 `tree_refusal` |

Layout evidence: not run. The tool adds no layout. The smoke PNGs come from the coordinator's §5 run.

## Fix round 2 checks (code `709611c8a`)

- `pwsh -NoProfile -File tools/check-all.ps1` (fast) at `709611c8a`: All 42 guards passed (141.6 s wall).

- `pytest -q tests/test_wk_walk_world.py tests/test_ds4_world.py tests/test_ds4_batch_days.py` (no database): 173 passed
  in 5.72 s. WK alone: 93 passed.
- Plants (WK file each time, restored after): Q1 round-1 fallback restored (session and start >= leader), 2 failed
  (`refuses_a_foreign_group_after_a_pid_wrap`, `refuses_a_recorded_pid_with_another_start_time`). Q2 RV-A session check
  removed, 1 failed (`refuses_a_recorded_member_in_another_session`). Q3 recorded start time ignored, 1 failed. Q4
  zombie leader not gone, 2 failed. Q5 no tracking during the wait, 1 failed (`failed_serve_stops_members_seen_while_waiting`).
  Q6 no tracking at success, 1 failed (`records_a_member_started_at_readiness`). Q7 zombie members counted live, 1 failed.
- Live stop check (scratch package, dev script `sleep 30 #`, 5491 probe `busy False`, npm 11.19.1, node v24.22.3).
  A, normal stop: 3 members recorded, `checked` None, `stop_child` None, group empty but the unreaped leader, `alive`
  False, 2.7 s. B, npm SIGKILLed and left a zombie: `checked` gone, `members` = the 2 live recorded members, `stop_child`
  None, group emptied, 2.8 s. The first run of A took 12.6 s: the zombie leader counted as a live member, so stop
  waited 10 s and sent SIGKILL. Zombie members are now skipped (Q7).

## Fix round 1 checks (revision `e9d5cd992`; code `7218b2835`)

- `pytest -q tests/test_wk_walk_world.py tests/test_ds4_world.py tests/test_ds4_batch_days.py` (no database): 164 passed
  in 5.52 s. WK alone: 84 passed.
- Plants (each removal restored after; the WK file run each time): P1 start-time check removed, 1 failed
  (`reused_pid_with_another_start_time`). P2 leader check removed, 2 failed (`not_leading_its_group`, L3 unverified).
  P3 recorded-group check removed, 1 failed. P4 cmdline check removed, 5 failed (vim plus the four wrappers). P5 npm
  title form removed, 2 failed (`stops_npm_retitled`, `cmdline_matches`). P6 round-0 loose tail match restored, 3
  failed (`bash -c`, `timeout` wrappers, `cmdline_matches`). P7 L4 member start-time check removed, 1 failed. P8 L4
  group fallback removed, 1 failed. P9 smoke `require` removed, 2 failed (T8 both). P10 L1 range removed, 3 failed.
  P11 L1 inequality removed, 2 failed. P12 L2 mode removed, 2 failed. P13 L2 `lstat` to `stat`, 2 failed. P14 L2
  owner removed, 1 failed. P15 L3 first child not stopped, 2 failed.
- Live stop check (this round only): the tool's exact web argv through the real `Procs.spawn` in a scratch package
  whose dev script is `sleep 30 #` (no port opened; 5491 probe `busy False`). npm 11.19.1, node v24.22.3. Recorded
  `start_time` 84479973, `pgid` = pid. `/proc` cmdline `["npm run dev --port 5491 --strictPort --host 127.0.0.1"]`;
  group of 3 (npm, sh, sleep). `checked` None, `alive` True; `stop_child` None; after it the only group entry was the
  unreaped zombie leader (`alive` False, then `exited` True). 2.9 s.
- `pwsh -NoProfile -File tools/check-all.ps1` (fast): All 42 guards passed (474.8 s wall, 286.4 s waiting for a slot).

## Known deviations

1. **Branch** `task/WK-walk-world`, as the dispatch names it (spec §0 names `task/WK-walkthrough-database`).
2. **PG* in the parent env refuses.** `walk_url` passes the full environ to `database_target` (§3.1, D-WK.11).
   `PGDATABASE` and the other target variables therefore give `WALK_TARGET_UNCLEAR ENVIRONMENT <name>` before any
   step. T4's "parent also holds `PGDATABASE`" can only be met as a refusal, and it is tested that way. T4's key-set
   assertion uses the other forbidden names. The coordinator's shell must not export `PG*` target variables.
3. **`walk_url` also refuses `ASSETOPS_PG_PORT` in `PROTECTED_PORTS`.** Without that, T1's "port 5490 is
   `WALK_TARGET_UNCLEAR`" cannot fail, because the URL's port would equal the variable.
4. **`WalkDeps` has two more seams:** `deep_dive` (url to `(read, dispose)`) and `foundation` (url to the store). They
   exist so that W4 can be tested without a database. Both default to the product compositions. In W4, the TenantRef
   comes from `resolve_tenant` (the `:172` query), and `names` from `list_sites` filtered by `import_record` (as
   `CutoverSiteRegistry.imported_sites`). The store's engine is disposed through its `_engine`.
5. **`serve --port/--web-port`** (optional overrides) exist so that T8's "on the command line" refusal has a command line.
6. **`stop`, `serving` and `status` identify a child by start time and group (fix round 1, H1/M1/L4).** Spec §3.6
   says "if `/proc/<pid>/cmdline` still equals its recorded `argv`". At spawn (`start_new_session=True`) the manifest
   records `pid`, `argv`, `start_time` (`/proc/<pid>/stat` field 22) and `pgid`. Before any signal, `Procs.checked`
   requires the recorded start time, `getpgid(pid) == pid` and the recorded group, then (secondary) a cmdline match
   exact on every token: the argv itself, `node <path>/npm ...`, or one retitled string, including npm 11's
   `npm run dev --port 5491 --strictPort --host 127.0.0.1` (no `--`). Wrappers (`bash -c`, `sh -c`, `timeout`) never
   match. Any failed check reports `WALK_PID_REUSED <pid> <check>` (`start_time`, `not_leader`, `pgid`, `cmdline`,
   `unrecorded`, `group_unverified`) and sends no signal. L4, bounded in fix round 2 (M3): during the serve wait and
   once at success, `Procs.track` records every process in the child's group and session as `members: [[pid,
   start_time], ...]`, only while the recorded leader still holds the group id. With the leader gone, or an unreaped
   zombie with the recorded start time (L5), the recorded group is signalled only when every live (non-zombie)
   member is a recorded `[pid, start_time]` pair in the recorded session (L6); any other member gives
   `group_unverified`. A member Vite starts after serve succeeds is unrecorded, so with the leader gone it refuses
   (fail-safe). A failed serve uses the same checks with SIGKILL once. Live check (scratch package, dev script
   `sleep 30 #`, no port opened): npm 11.19.1 retitled to that string, `checked` passed and `stop_child` stopped the
   group (npm, sh, sleep) in 2.9 s.
7. **Small additions.** `WALK_CAP_EXCEEDED` (exit 5). A refusal raised inside a check (a stale parent in W1) becomes
   that check's FAIL line. `drop` skips the `DROP` when the database is already gone, and removes the manifest.
   Statement and snapshot steps run through `World.run_step` with `World.env(None, ...)` plus the walk URL, so
   `rung_url` is called only in `walk_url`.
8. **`smoke` takes a heavy-tool slot (fix round 1, M2): deviation from spec §3.1, for the Architect to ratify.**
   §3.1 says `serve, smoke, stop and status do not` call `require`. `smoke` now calls
   `heavy_slot_check.require("walk-smoke")` (no `db`) before S3 launches Chromium, so outside a slot it exits 69 and
   no browser starts (T8 `test_t8_smoke_requires_a_slot_before_chromium`). The node child still gets exactly the six
   I3 names; the slot is asserted by the Python process `heavy-slot.sh` wraps. The smoke script itself still has no
   `assertHeavySlot` and is not in the inventory listing (it names no launcher word).
9. **I5 notes.** The upload key check is at `main.py:693`. Exit 69 passes through `require`. `ASSETOPS_LIVE_FIELD_*`
   stays on the deny list. The Vite child is WK's own (`demo_combined.py serve` only prints that command).
10. **Fix round 1 small codes (L1-L3).** `--port`/`--web-port` outside 1024-65535, or equal, refuse with
    `WALK_PORT_INVALID <port>` / `WALK_PORT_INVALID <port> = <web_port>` (a new code, not in §3.1's list). An existing
    `walks/` folder that is a symlink, not a folder, not the user's, or group/world accessible (`mode & 0o077`)
    refuses with `WORLD_STATE_INVALID <path>`. If the web spawn raises, the API child gets the safe stop (SIGKILL after
    the checks) and the run fails `WALK_SERVE_FAILED web spawn <error>` (exit 4).

## Residual risk

The real adapters are exercised only by the coordinator's §5 run: `Admin`'s `LIKE` lookup, `Procs`, the deep-dive
read's JSON. The npm title form and the stop of npm's group were checked live once (deviation 6). They are not tested against a database. W5 calls `world.c4_oracle` unchanged,
and a C4 FAIL on the new L2 stops at §5 step 1 (D-WK.10). The one-figure read (D-WK.12) waits for the smoke PNGs.

## Review focus

`walk_url` and `walk_name_ok` (§3.1). The census judge's expected counts. `judge_month`'s `as_of` comparison
(build `isoformat()` against the view's `iso_z`). The serve env builders. Deviations 2, 6 and 8.
