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
6. **`stop` and `serving` match cmdlines loosely.** They accept an interpreter-run or retitled cmdline with the same
   tail (`cmdline_matches`): `npm` is a node script, so its `/proc` cmdline is not literally `["npm", ...]`. This is
   unverified against a live Vite. Risk: a mismatch reports `WALK_PID_REUSED` and leaves the child.
7. **Small additions.** `WALK_CAP_EXCEEDED` (exit 5). A refusal raised inside a check (a stale parent in W1) becomes
   that check's FAIL line. `drop` skips the `DROP` when the database is already gone, and removes the manifest.
   Statement and snapshot steps run through `World.run_step` with `World.env(None, ...)` plus the walk URL, so
   `rung_url` is called only in `walk_url`.
8. **The smoke script has no `assertHeavySlot`.** I3 gives `node` exactly six names, so the slot marker cannot reach
   it. The browser runs inside the slot that `tools/heavy-slot.sh -- python tools/walk_world.py smoke` holds (§5
   step 8). The inventory check (`test_heavy_slot_inventory.mjs`) does not list the file, because it loads the engine
   through `require(process.env.PW)` and names no launcher word. The reviewer should judge whether this needs a ruling.
9. **I5 notes.** The upload key check is at `main.py:693`. Exit 69 passes through `require`. `ASSETOPS_LIVE_FIELD_*`
   stays on the deny list. The Vite child is WK's own (`demo_combined.py serve` only prints that command).

## Residual risk

The real adapters are exercised only by the coordinator's §5 run: `Admin`'s `LIKE` lookup, `Procs`, the deep-dive
read's JSON, and the npm cmdline form. They are not tested against a database. W5 calls `world.c4_oracle` unchanged,
and a C4 FAIL on the new L2 stops at §5 step 1 (D-WK.10). The one-figure read (D-WK.12) waits for the smoke PNGs.

## Review focus

`walk_url` and `walk_name_ok` (§3.1). The census judge's expected counts. `judge_month`'s `as_of` comparison
(build `isoformat()` against the view's `iso_z`). The serve env builders. Deviations 2, 6 and 8.
