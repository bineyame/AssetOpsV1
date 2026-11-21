# WK: the walkthrough database, copied from the checked world (implementer spec and coordinator runbook)

Status: rev 2, Architect (Claude), 2026-11-21: handshake round 1 answered (`rulings.md`, "Handshake answers (round 1)",
D-WK.10 to D-WK.14); rev 1 the same day, on the owner's delegation
(`owner/owner-away-architect-stands-in-2026-11-21b.md`; owner-away rows 36 (owner: option b), 53, 54, 66 and 67).
`delivery-plan.md` §2 row `WK`: "Prepare the clean day-14 walkthrough database at main" (1 unit; structure page
DAY13; non-screen). `two-week-build-plan.md` §0.2 day 13, §0.3 ("`DS3`, `DS4` and the walkthrough database `WK`").
**1.4 units, one commit plus the coordinator's run** (D-WK.8; rev 2 adds 0.15: the walk name guard D-WK.11, the
after-serve census D-WK.13, the smoke's browser env and `WalkDeps`). Day-14 order (D-WK.14): 3C2 unit 2, then the world
build and check (§5 step 1), then WK's run, then DDR. Standard review (W5): it reuses DS4's reviewed meaning of clean
and good, adds only product-command writes, and serves the way the 13 Nov walkthrough is served.
**Decisions:** `rulings.md` (D-WK.1 to D-WK.14). **Reviewer guide:** `reviewer-guide.md`.

- **What it is.** One coordinator-only tool, `tools/walk_world.py`. It copies the current checked L2 world template
  into `assetops_polish_walk<label>_test` with `CREATE DATABASE ... TEMPLATE` (owner row 36, option b). On top of the
  world it adds what the walkthrough needs and nothing else: the finance lead's two management-accounts statements and
  one snapshot rebuild after them. Then it checks the copy, serves it, smoke-tests the served pages, and tears it
  down. A browser script, `tools/walk_world_smoke.cjs`, walks the pages.
- **Builds on (on `main` before WK builds):** `DS4` with its unit 3 fix round (`tools/world.py`: `World`,
  `World.prepare`, `World.current_l2`, `World.check_state`, `World.wait_idle`, `Admin`, `rung_url`, `rung_query`,
  `CENSUS_TABLES`, `TENANTS`, `read_definition`, `c4_oracle`, `canonical`, `Deps`); `3A7` (`reconcile_month`); `3B7a`
  (`build_structure_snapshot build|verify`, `structure_snapshot.composition.build_structure_snapshot`, `codec`); 5c
  units 1 and 2 (`deep_dive.composition.build_deep_dive_read`, `GET /api/portfolio/month`); `ON1` (served tenant,
  `ASSETOPS_TENANT_SLUG`); `RC4-F1` (`database_target`, `is_operator_name`, `OPERATOR_PREFIX`); `T1`
  (`tools/heavy_slot_check.py` `require`); the 13 Nov serve (`tools/demo_combined.py` `serve`, `_serve_api`,
  `_kill_tree`: the shape WK copies, D-WK.5).

## 0. Before you start (gates; each is a hard stop)

- **Build:** DS4 merged, including D-DS4.33, and 5c units 1 and 2 merged (both hold now). Branch
  `task/WK-walkthrough-database` off `main`; worktree `/opt/assetecon/AssetOpsV1-wk`; symlink `frontend/node_modules`
  from the main checkout. The build does not wait for 3C2 unit 2; the coordinator's run does (§5 step 0).
- **Read:** `rulings.md`; DS4 `spec.md` §3.2 to §3.6 and `tools/world.py` (the names above, whole functions);
  `tools/demo_combined.py:1-70`, `:830-875`, `:1791-1880`; `host/lab_app.py:1-140`; `backend/assetops_backend/main.py:680-700`
  (the commercial upload router: off without a key folder); `build_structure_snapshot.py`; `reconcile_month.py:40-70`;
  5c `spec.md` §3.1, §4.1, §4.2; DDR `spec.md` §1 (rows S5, S8); `frontend/vite.config.ts:30-50`
  (`ASSETOPS_API_PORT`); `/opt/assetecon/tools/pw/shot.cjs`.
- **Databases while building:** none. Every test is pure and uses injected fakes (`deps`, as `tools/world.py` does).
  Never create, clone or drop a database, never connect to `assetops_polish_walk1113_test`, ports 5490 or 8990,
  `/opt/assetecon/AssetOpsV1-walk`, any `assetops_world_audit_*` database, Docker, or `/opt/assetecon/keys`.
- **Files.** New: `tools/walk_world.py`, `tools/walk_world_smoke.cjs`, `backend/conversions/walk-layer4-v1.json`,
  `backend/tests/test_wk_walk_world.py`. Edited: none. **No migration**, no route, no screen, no product code, no guard
  edit, nothing under `tools/checks/`.

## 1. Outcome and why

The owner's rule is that a walkthrough runs only on a clean, good database (`owner/owner-clean-walkthrough-over-time-2026-11-13.md`,
`owner/owner-rules-clarification-2026-11-19.md`; a verified clone counts, OD-4). DS4 makes "good" a command: an L2 world whose `world check` passed. Row 36 makes the
walkthrough a copy of that L2 under a walk name. WK adds the copy, the two facts the deep-dive needs that the world
does not hold, proof that the copy is still clean and good afterwards, and the serve.

Gate questions (each can fail): Is the copy made only from the L2 at today's key whose check passed on today's check
inputs? Does the copy differ from its L2 in exactly the declared rows? Does the month read SERVED, current and
reconciled, with Lakeside October at 1,443.00 against 2,295.00? Do the served pages answer with no server error at every
Site? Is the walkthrough database of 13 Nov never named, opened or stopped? Does the serve hold no key and no real-data
switch?

## 2. What WK adds to the DS4 world (D-WK.3)

The world (DS4 §3.1) is Lakeside Power (Kobo, Kisiwa, Mto), October 2026, from emulated exports, with no telemetry.
L2 already holds one snapshot per tenant and month (`build_structure_snapshot build`, by `service:world-build`) and
the observer's Findings (`observe_structure run`). Steps that only re-run what L2 did are not repeated.

| Added | Why | How |
|---|---|---|
| The finance lead's draft statement: revenue 9,700.00, fuel cost 5,100.00 | 5c reads "not yet reconciled" until a closed month matches (3A7); the draft shows the mismatch the owner expects first (fuel 2.1% apart) | `reconcile_month record`, as DDR S5, source labelled emulated |
| The final statement: fuel cost 5,000.00 | It matches within 1% (revenue 9,688.00 recorded, fuel 4,995.00), so the screen shows the gate lifted, with both statements in the record | as DDR S8 |
| One snapshot rebuild after the statements | 5c reads the standing at the snapshot's as of; the L2 snapshot predates the statements. The 3B4 merge note: "Served snapshots need build_structure_snapshot build per tenant-month" | `build_structure_snapshot build --by service:world-build` |
| Not added: an agreed Action | The change is agreed by people at the walkthrough (RC9); the owner may have it recorded live (§5 step 10) | none |
| Not added: an admitted profile, an observer rerun | DDR proves the profile path; statements change no observation | none |

`backend/conversions/walk-layer4-v1.json` holds these as data, exactly:

```json
{
  "format": "assetops.walk-definition/1",
  "world": "layer4",
  "statements": [
    {"tenant": "lakeside-power", "as": "joseph@lakeside-power.example", "period": "2026-10", "currency": "USD",
     "revenue": "9700.00", "fuel_cost": "5100.00",
     "source_ref": "Emulated management accounts, October 2026, draft"},
    {"tenant": "lakeside-power", "as": "joseph@lakeside-power.example", "period": "2026-10", "currency": "USD",
     "revenue": "9700.00", "fuel_cost": "5000.00",
     "source_ref": "Emulated management accounts, October 2026, final"}
  ],
  "rebuild_by": "service:world-build",
  "serve": {"tenant": "lakeside-power", "port": 8991, "web_port": 5491},
  "expect": {"tenant": "lakeside-power", "month": "2026-10", "contribution_actual": "1443.00",
             "contribution_target": "2295.00", "reconciled": true},
  "pages": ["/portfolio", "/portfolio/month?month=2026-10", "/sites", "/sites/{code}", "/findings", "/actions",
            "/evidence", "/financials"]
}
```

`read_walk_definition(path)` is strict: exactly these keys; `world` equal to the world definition's; every
statement's `tenant` a world tenant and `period` one of the world's `months`; amounts match `^[0-9]+\.[0-9]{2}$`;
`rebuild_by` matches `structure_snapshot.model.BUILT_BY`; ports are integers 1024 to 65535 and not in
`PROTECTED_PORTS = (8990, 5490)`; `{code}` appears in exactly one page. Any breach: `WALK_DEFINITION_INVALID <json path>`.
No key in this file is `site_id` or `site_code` (SC-1's `KEY_INSTANCE` scans `backend/conversions/*.json`).

## 3. The tool (`python tools/walk_world.py <command> --label L`)

### 3.1 Names, state and refusals

- `--label` fullmatches `[0-9]{4}[a-z]?` (the month and day, plus an optional letter for a second copy on the same
  day). The database is `assetops_polish_walk<label>_test`. `PROTECTED_DATABASES = ("assetops_polish_walk1113_test",)`;
  a label giving a protected name: `WALK_PROTECTED`. Else `WALK_LABEL_INVALID`. The name must pass RC4-F1's
  `database_target` and not `is_operator_name`.
- **The walk URL (D-WK.11; I2).** Every connection to the walk database goes through one function,
  `walk_url(label, environ) -> str`, and nothing else in the tool builds a URL or opens a connection naming the walk
  database. `World.census`, `World.exists` and `check_name` are never called on the walk name (`check_name` refuses any
  name holding `walk` or `serve`, `evidence/bulk_load.py:47`, which is right for the world tool and stays). In order:
  (1) `label` fullmatches `[0-9]{4}[a-z]?`, else `WALK_LABEL_INVALID`; (2) `name =
  f"assetops_polish_walk{label}_test"`; `name in PROTECTED_DATABASES` gives `WALK_PROTECTED`; (3) `walk_name_ok(name)`
  is true, else `WALK_NAME_REFUSED <name>`: it fullmatches `assetops_polish_walk[0-9]{4}[a-z]?_test`, is not in
  `PROTECTED_DATABASES`, `is_operator_name(name)` is false (any case of `assetops_op`, `database_target.py:22,68`), and
  it does not start `assetops_world` (a rung is never a walk); (4) `url = world.rung_url(name, environ)`;
  `database_target(url, environ)` raises nothing (`DatabaseTargetUnclear` gives `WALK_TARGET_UNCLEAR <reason>`), its
  `name` equals `name`, its host is `127.0.0.1` or `localhost`, and its port equals `ASSETOPS_PG_PORT` (default
  `55432`), else `WALK_TARGET_UNCLEAR <field>`. Counts and lookups on the walk database run through `world.rung_query`
  on that URL; `pg_database` lookups are plain `Admin` `SELECT`s with a bound name. `wait_idle(l2_name)` and
  `check_state` stay on `World` (they name the L2, not the walk).
- Common options: `--definition` (default `backend/conversions/world-layer4-v1.json`), `--walk-definition` (default
  `backend/conversions/walk-layer4-v1.json`), `--state` (default `/opt/assetecon/worlds`), `--prefix` (default
  `assetops_world`), `--cap-seconds` (default 900). `main(argv, *, deps=None) -> int`; `deps` (tests only) replaces
  the world object, the admin connection, the subprocess runner, the git reader, the clock, `require`, the HTTP getter
  and the process table, as `WalkDeps(world: world.Deps, http, procs, world_factory)` (I4): `world_factory(namespace,
  deps.world)` builds the `World` (tests inject a fake), and the copy's one DDL goes through `deps.world.admin`.
- **Walk manifests:** `<state>/walks/<database>.json`, created 0700 by the tool under the existing state folder,
  written atomically, canonical JSON (`world.canonical`). They hold names, keys, ids, counts, PIDs and paths, never key
  content and never a file name under `key_dir` (D-DS4.19). The tool reads the world's manifests only through `World`.
- `copy`, `prepare`, `check` and `drop` first call `heavy_slot_check.require("walk", db=True)`; `serve`, `smoke`,
  `stop` and `status` do not (a serve is not a heavy job; the smoke's browser runs through the slot pool, §5).
- **Exits:** 0 done; 2 refused before any change (`<CODE> <detail>` on stderr); 3 a product step failed
  (`STEP_FAILED <database> <step> <exit>`); 4 a check or smoke FAIL; 5 the cap was reached; 69 passes through from
  `heavy_slot_check.require` (`tools/heavy_slot_check.py:161-171`, as `tools/world.py:13` documents). A world refusal passes
  through with its own code (`WORLD_NO_TEMPLATE`, `WORLD_TEMPLATE_STALE`, `WORLD_TREE_DIRTY`, ...). WK codes:
  `WALK_LABEL_INVALID`, `WALK_PROTECTED`, `WALK_NAME_REFUSED`, `WALK_TARGET_UNCLEAR`, `WALK_DEFINITION_INVALID`, `WALK_NOT_CHECKED`, `WALK_CHECK_FAILED`,
  `WALK_CHECK_STALE`, `WALK_EXISTS`, `WALK_UNKNOWN`, `WALK_COMMIT_MOVED`, `WALK_PREPARED`, `WALK_NOT_PREPARED`,
  `WALK_NOT_PASSED`, `WALK_TREE_MISMATCH`, `WALK_PORT_PROTECTED`, `WALK_PORT_BUSY`, `WALK_SERVING`, `WALK_NOT_SERVING`,
  `WALK_PID_REUSED`, `WALK_DATABASE_IN_USE`, `WALK_SERVE_FAILED`. Diagnostics for the coordinator only; nothing is
  served.

### 3.2 `copy`

1. Build `world = World(<namespace with prefix, state, definition, cap_seconds>, deps)`, `world.prepare()` (clean
   tree, state, definition), `l2_name, l2 = world.current_l2()` (today's key; refuses stale or missing),
   `passed, stale = world.check_state(l2)`. `stale` not None: `WALK_CHECK_STALE <part>`. `passed is None`:
   `WALK_NOT_CHECKED`. `passed is False`: `WALK_CHECK_FAILED`. This is the same test `world list` prints as
   `check_passed` (D-WK.2).
2. The walk name (from `walk_url`'s checks) exists in `pg_database` (an `Admin` `SELECT` with the bound name) or has a
   walk manifest: `WALK_EXISTS`. The same `SELECT` lists every `assetops_polish_walk%` name, kept as `walks_before`.
3. `world.wait_idle(l2_name)` false: `WALK_DATABASE_IN_USE <l2_name>`. Then exactly one admin statement:
   `CREATE DATABASE "<walk>" TEMPLATE "<l2_name>" STRATEGY FILE_COPY`. No other DDL, and no `ALTER` on the L2.
4. Write the walk manifest: `{"format": "assetops.walk-build/1", "database", "label", "parent": l2_name,
   "parent_key": l2["key"], "commit": git HEAD, "copied_at": UTC ISO seconds, "seconds", "tenants": l2["tenants"],
   "key_dir": l2["key_dir"], "parent_census": l2["census"], "parent_snapshots": l2["snapshots"], "steps": [],
   "walks_before", "snapshots": null, "check": null, "serve": null}`.
5. Stdout: `{"database", "parent", "parent_key12", "seconds"}`.

### 3.3 `prepare`

Refused without a walk manifest (`WALK_UNKNOWN`), when `git rev-parse HEAD` differs from the manifest's `commit`
(`WALK_COMMIT_MOVED`), or when `steps` is non-empty (`WALK_PREPARED`; a failed prepare is dropped and copied again,
which takes seconds). The steps run as `tools/world.py` runs its steps (DS4 §3.5): `subprocess.run([sys.executable,
*argv], cwd=<repo>, env=E, capture_output=True, text=True, timeout=<cap left>)`. `E` is built, never inherited: `PATH`,
`HOME`, `LANG` when set; `PYTHONPATH=<repo>/backend:<repo>/contracts:<repo>/simulator`; `DATABASE_URL` the walk URL
(`world.rung_url`'s form with the walk name); `ASSETOPS_TENANT_SLUG` the step's tenant; `ASSETOPS_PSEUDONYM_KEY_DIR`
the manifest's `key_dir` (D-DS4.22); `ASSETOPS_PG_PORT`, `ASSETOPS_PG_PASSWORD` when set. In order:

1. Per statement `s`, in file order: `-m assetops_backend.reconcile_month record --tenant <s.tenant> --as <s.as>
   --period <s.period> --currency <s.currency> --revenue <s.revenue> --fuel-cost <s.fuel_cost> --source-ref
   <s.source_ref>` (step `prepare.statement:<n>`).
2. Per world tenant and month: `-m assetops_backend.build_structure_snapshot build --tenant <slug> --month <M> --by
   <rebuild_by>` (step `prepare.snapshot:<slug>:<M>`). Its stdout line gives `as_of`, `portfolio_snapshot_id`,
   `sites` and `rules_digest`, kept under `snapshots["<slug>:<M>"]`.

Every step's record (`step`, `argv`, `seconds`, `exit`, `out`) is appended to `steps` and the manifest is rewritten
after each step. A non-zero exit: exit 3, `snapshots` stays null.

### 3.4 `check` (D-WK.4: clean and good)

Refused without a prepared manifest (`WALK_NOT_PREPARED`). Runs every check (no stop at the first FAIL), writes
`check: {"at", "commit", "passed", "lines"}`, prints one line per check `{"check", "state": "PASS"|"FAIL", "detail"}`,
then `{"check": "ALL", "state"}`, and exits 0 or 4. The checks run in this order, so a write by W2 would show in W3.

| Check | Passes when |
|---|---|
| W1 lineage | `world.current_l2()` returns the manifest's `parent` with the same `key`; `world.check_state` of it is `(True, None)`; HEAD equals the manifest's `commit` |
| W2 rebuild | per `snapshots` entry, `build_structure_snapshot verify --tenant <slug> --snapshot <portfolio_snapshot_id>` on the walk database exits 0 with `"matches": true` |
| W3 census | the walk census (`world.CENSUS_TABLES`, then a count per table through `world.rung_query` on `walk_url`'s URL; never `World.census`, I2) equals `parent_census` table by table, except: `commercial_accounts_statement` is exactly `+ len(statements)`, and `structure_snapshot` is exactly `+ Σ (1 + len(sites))` over `snapshots`. Every other difference FAILs, naming the table and both counts |
| W4 served | `read, dispose = build_deep_dive_read(url)` (disposed in `finally`; I1); `read.month(TenantRef(id, slug, name), expect.month, names)`, the `TenantRef` from `SELECT id, slug, name FROM tenant WHERE slug = :s` on the walk URL (as `sites/adapters/postgres_foundation_store.py:172`) and `names` from the Foundation's imported Sites as the route does (`deep_dive_api.py:58`), never from the world definition: `state` SERVED, `as_of` equals the walk's newest snapshot `as_of`, `fresh.current` true, `fresh.untracked_text` null, `standing.reconciled` equal to `expect.reconciled`, and the `contribution` tile's `bar` `{"actual", "target"}` equal to `expect` as `Decimal`s. Read with `ASSETOPS_TENANT_SLUG` unset in-process; the tenant comes from `TENANTS` on the walk database |
| W5 oracle | `world.c4_oracle(rows, definition, derived_values, counts)` over the walk snapshots' Site rows (read through `structure_snapshot.composition.build_structure_snapshot(url).store.get` and `codec.payload_of`, as DS4's `_c4`) is PASS, with no line marked `new` and no line marked `known`. The oracle is used unchanged; WK never edits `C4_CONTRACT` or `C4_KNOWN_FINDINGS` (D-WK.10) |
| W6 isolation | the walk name passes `walk_url`'s checks (§3.1); the parent L2's `datallowconn` is still false; the walk database's tenants (`TENANTS`) are exactly the manifest's `tenants`; no `pg_database` name starting `assetops_polish_walk` other than this one was created by this run (compare the list before `copy`, kept in the manifest as `walks_before`, with today's, less this name) |
| W7 steps | every recorded step has exit 0, and the statement and snapshot step counts equal the definitions' |

### 3.5 `serve`

`--tree DIR` is required; `DIR` resolving (`os.path.realpath`) to `/opt/assetecon/AssetOpsV1-walk` or below it is
`WALK_TREE_MISMATCH` before anything else (R6). Refused unless the manifest's `check.passed` is true and `check.commit` equals the
manifest's `commit` (`WALK_NOT_PASSED`); `git -C DIR rev-parse HEAD` equals the manifest's `commit`
(`WALK_TREE_MISMATCH`); `serve` is null or its PIDs are gone (`WALK_SERVING`); either port is in `PROTECTED_PORTS`
(`WALK_PORT_PROTECTED`) or accepts a TCP connection on 127.0.0.1 (`WALK_PORT_BUSY`). Then, as `demo_combined.py serve`
does (D-WK.5), each child with `start_new_session=True`, stdout and stderr to `DIR/var/polish_walk<label>/logs/`:

- **API:** `[sys.executable, "-m", "uvicorn", "lab_app:app", "--host", "127.0.0.1", "--port", <port>]`, `cwd=DIR/host`,
  env built, never inherited: `PATH`, `HOME`, `LANG` when set; `PYTHONPATH` = `DIR/backend`, `DIR/contracts`,
  `DIR/gateway`, `DIR/simulator`, `DIR/host` joined by `os.pathsep`; `DATABASE_URL` the walk URL;
  `ASSETOPS_TENANT_SLUG` the definition's `serve.tenant`; `ASSETOPS_PG_PORT`, `ASSETOPS_PG_PASSWORD` when set;
  `PYTHONUNBUFFERED=1`. Never set, whatever the parent holds: `ASSETOPS_PSEUDONYM_KEY_DIR` (commercial uploads stay
  off, `main.py:693`), `ASSETOPS_REAL_OPERATOR_DATA`, `ASSETOPS_OPERATIONAL_ENTRY`, any `ASSETOPS_READING_UPLOAD_*`,
  `ASSETOPS_GATEWAY_*` or `ASSETOPS_LIVE_FIELD_*` name, `ASSETOPS_PERIOD_READ_KINDS`, or a `PG_TARGET_ENV` name
  (`PGDATABASE` and the rest).
- **Web:** `["npm", "run", "dev", "--", "--port", <web_port>, "--strictPort", "--host", "127.0.0.1"]`,
  `cwd=DIR/frontend`, env `PATH`, `HOME`, `LANG` when set and `ASSETOPS_API_PORT=<port>`.
- Wait up to 120 s for `GET /api/health` to answer 200 and the web port to accept a connection. If either child exits
  first, or time runs out, kill both by PID (as `_kill_tree`) and exit 4 with `WALK_SERVE_FAILED <which> <log path>`.
- Record `serve: {"tree", "port", "web_port", "api": {"pid", "argv"}, "web": {"pid", "argv"}, "started_at"}` and
  print `{"api": "http://127.0.0.1:<port>", "web": "http://127.0.0.1:<web_port>", "api_pid", "web_pid"}`. The tool
  then exits; the children run on until `stop`.

### 3.6 `smoke`, `stop`, `status`, `drop`

- **`smoke`** (refused when not serving: `WALK_NOT_SERVING`): S1 `GET /api/health` is 200. S2 `GET
  /api/portfolio/month?month=<expect.month>` is 200 and its body meets W4's conditions (served through the real app
  this time). S3 runs `node tools/walk_world_smoke.cjs --base http://127.0.0.1:<web_port> --pages <JSON list>
  --out /opt/assetecon/evidence/WK/<label>/`. Its env (I3): `env.sh` is sourced in a `bash -c` child that prints the
  values, and `node` gets exactly `PATH`, `HOME`, `PW`, `CHROME`, `FONTCONFIG_FILE` and
  `LD_LIBRARY_PATH=<AUDIT_LD_LIBRARY_PATH>` (`/opt/assetecon/tools/pw/env.sh:4-5`), nothing else. The
  list is `smoke_pages(walk_definition, world_definition)`: each page in order, `{code}` expanded to each world
  Site code in definition order. The script opens each page at 1440 × 900, waits for network idle (cap 30 s), and
  records every response whose path starts `/api/`. A page FAILs on a status of 500 or more, a failed request, a
  `pageerror`, or the cap. It saves one full-page PNG per page and `report.json` (`[{"page", "api", "fail": [{"url",
  "status"}], "errors"}]`). Exit 0 when every page passes, else 1. S4 (D-WK.13; R3), after S3: W3's census judge
  re-run read-only on `walk_url`'s URL against the manifest's `parent_census` plus the declared deltas; any other
  difference FAILs naming the table and both counts (a read that wrote a row). `smoke` prints S1 to S4 and `ALL` and
  exits 0 or 4.
- **`stop`:** for each recorded child, if `/proc/<pid>/cmdline` still equals its recorded `argv`, send SIGTERM to its
  process group, wait 10 s, then SIGKILL. Otherwise report `WALK_PID_REUSED <pid>` and leave it. Set `serve` to null.
- **`status`:** prints the manifest's `database`, `parent`, `check.passed`, `serve` and whether each PID is alive.
- **`drop`:** refused while serving (`WALK_SERVING`), without a manifest (`WALK_UNKNOWN`), or with sessions after a
  5 s wait (`WALK_DATABASE_IN_USE`). Then `DROP DATABASE "<walk>"` (never `WITH (FORCE)`), then the manifest is
  removed. It never touches L0 to L2, a world manifest, a key folder or a worktree.

## 4. Tests (written first; `backend/tests/test_wk_walk_world.py`, no database)

| # | Test |
|---|---|
| T1 | Names: `1123` gives `assetops_polish_walk1123_test`; `1123b` is accepted; `1113` is `WALK_PROTECTED`; `abc`, `11234`, `1123B` are `WALK_LABEL_INVALID`; every accepted name is at most 63 bytes and not an operator name. `walk_name_ok` refuses `assetops_polish_walk1113_test`, `assetops_op_lakeside`, `ASSETOPS_OP_X`, `assetops_opx_test`, `assetops_world_audit_l2_1906a5d074a0` and `assetops_polish_walk1123`; `walk_url` with `ASSETOPS_PG_PORT=5490` or a host other than 127.0.0.1 is `WALK_TARGET_UNCLEAR` (D-WK.11) |
| T2 | `copy` refusals in order, on a fake world: `current_l2` raising `WORLD_TEMPLATE_STALE` passes through (exit 2); `check_state` `(None, "manifest")` gives `WALK_CHECK_STALE manifest`; `(None, None)` gives `WALK_NOT_CHECKED`; `(False, None)` gives `WALK_CHECK_FAILED`; an existing name gives `WALK_EXISTS`; a busy L2 gives `WALK_DATABASE_IN_USE`. No admin DDL is issued in any of them |
| T3 | `copy` success: the fake admin's statements are exactly one `CREATE DATABASE "assetops_polish_walk1123_test" TEMPLATE "<l2>" STRATEGY FILE_COPY` plus `SELECT`s; the manifest has every §3.2 field |
| T4 | `prepare`: the argv of all three steps equals §3.3 exactly (from the committed walk definition); `E` has exactly the listed keys when the parent environment also holds `PGDATABASE`, `ASSETOPS_REAL_OPERATOR_DATA` and `ASSETOPS_OPERATIONAL_ENTRY`; `WALK_COMMIT_MOVED`, `WALK_PREPARED`, `WALK_UNKNOWN`; a failed second step gives exit 3, two step records, `snapshots` null |
| T5 | Census judge: equal plus the two declared deltas is PASS; `+1` in any other table FAILs naming it with both counts; a statement delta of 1 FAILs; the snapshot delta is computed from the build lines' `sites`; the same judge as smoke S4 FAILs on a row added after the serve (D-WK.13) |
| T6 | `check` runs W1 to W7 even after W1 FAILs; exit 4; the manifest's `check.passed` is false; all PASS gives exit 0 |
| T7 | W4 and S2 judge: SERVED, current, reconciled, 1443.00 and 2295.00 is PASS; each of `REBUILD_NEEDED`, `fresh.current` false, `reconciled` false, actual `1443.01` FAILs with its reason |
| T8 | `serve` env: the API env has exactly the listed keys when the parent holds every forbidden name; the web env has exactly its four; the smoke's `node` env has exactly its six (I3); `--tree /opt/assetecon/AssetOpsV1-walk` (and a symlink to it) is `WALK_TREE_MISMATCH`; port 8990 or 5490 in the walk definition is `WALK_DEFINITION_INVALID` and on the command line `WALK_PORT_PROTECTED`; serve is refused for an unchecked manifest, a mismatched tree HEAD, a busy port |
| T9 | `stop`: a PID whose cmdline matches is signalled (fake process table); a reused PID is left and reported |
| T10 | `drop`: refused while serving and with sessions; issues `DROP DATABASE "<walk>"`, never `FORCE`; removes only the walk manifest; issues nothing naming the L2 |
| T11 | `smoke_pages`: the committed definitions expand to 10 pages, the three Site pages in definition order (Kisiwa, Kobo, Mto as the world definition lists them) |
| T12 | Static: `tools/walk_world.py`'s source names `assetops_polish_walk1113_test`, `8990` and `5490` only inside `PROTECTED_DATABASES` and `PROTECTED_PORTS`, names `/opt/assetecon/AssetOpsV1-walk` only in the tree refusal and `/opt/assetecon/keys` nowhere (R6); it never calls `World.create`, `World.drop_db`, `World.freeze`, `World.census`, `World.exists` or `check_name`, and `rung_url` is called only inside `walk_url` (D-WK.11) |

Run: `tools/heavy-slot.sh -- <host tests> backend/tests/test_wk_walk_world.py` (no `--db`). Fast check-all green.
`node tools/walk_world_smoke.cjs --help` exits 0 (the reviewer runs the real smoke only through the coordinator).

## 5. The coordinator's run (after WK merges; each step alone; stop at the first failure)

Run in `/opt/assetecon/AssetOpsV1` after `git -C /opt/assetecon/AssetOpsV1 branch --show-current` prints `main`.
`<L>` is the label (for example `1203`); `<C>` is the commit the walk manifest records. Machine quiet: no other
heavy database job (`tools/heavy-slot.sh --status`), keep-awake started (RULES §7).

0. **Start condition (D-WK.14).** 3C2 unit 2 is merged (`git -C /opt/assetecon/AssetOpsV1 grep -n StoreAgreedActions
   main -- backend/assetops_backend/deep_dive/composition.py` shows a line) and WK is merged. From step 1 to step 5 no
   merge into `backend/assetops_backend`, `contracts/assetops_contracts`, `simulator/assetops_simulator`,
   `tools/world.py` or `tools/world_history.py` (it stales the L2, D-WK.6); from step 3 to step 5 no merge to `main` at
   all (`prepare` and W1 require HEAD to equal the copy's commit). DDR merges after step 5.
1. `tools/heavy-slot.sh --db --label wk -- python tools/world.py build --key-root /opt/assetecon/keys/world --cap-seconds 900`.
   Three lines. The kept L2 is stale (R1): expect `"reused": false` for L1 and L2 (L0 reused); then run
   `tools/heavy-slot.sh --db --label wk -- python tools/world.py check --cap-seconds 900` (it must exit 0). The kept
   `assetops_world_audit_l2_1906a5d074a0` is never copied. **If C4 FAILs** (D-WK.10): stop. Do not copy, do not edit the
   contract or the known findings, and send the C4 lines to the Architect as a DS4 finding. The one expected change,
   the honesty list naming `dispatch-3.3` where it named `dispatch-3.2`, is not judged by C4 and cannot fail it.
2. `python tools/world.py list`. The L2 line at the key that step 1 printed must show `"exists": true` and
   `"check_passed": true`. Note its database name.
3. `tools/heavy-slot.sh --db --label wk -- python tools/walk_world.py copy --label <L>`. Its `parent` must equal step 2's
   name.
4. `tools/heavy-slot.sh --db --label wk -- python tools/walk_world.py prepare --label <L>`.
5. `tools/heavy-slot.sh --db --label wk -- python tools/walk_world.py check --label <L>`. `ALL` PASS (exit 0). A FAIL
   stops the run: send the lines to the Architect, then run step 11's `drop`.
6. `git -C /opt/assetecon/AssetOpsV1 worktree add --detach /opt/assetecon/AssetOpsV1-wk<L> <C>`, then
   `ln -s /opt/assetecon/AssetOpsV1/frontend/node_modules /opt/assetecon/AssetOpsV1-wk<L>/frontend/node_modules`.
7. `python tools/walk_world.py serve --label <L> --tree /opt/assetecon/AssetOpsV1-wk<L>`.
8. `tools/heavy-slot.sh -- python tools/walk_world.py smoke --label <L>`. `ALL` PASS. The PNGs and `report.json` are in
   `/opt/assetecon/evidence/WK/<L>/`.
9. Owner access as on 13 Nov (Tailscale; SSH tunnel), on port 5491:
   `ssh -L 5491:127.0.0.1:5491 <server>`, then `http://127.0.0.1:5491/portfolio/month?month=2026-10`.
10. If the owner asks during the walkthrough to record the agreed change (RC9): DDR S11's `record_action` command,
    with `DATABASE_URL` the walk URL, `ASSETOPS_TENANT_SLUG=lakeside-power` and the owner's own title, owner and due date.
    Record that it was run in the walkthrough notes.
11. **Teardown**, on the owner's word after the walkthrough, or when a newer WK replaces this one:
    `python tools/walk_world.py stop --label <L>`;
    `tools/heavy-slot.sh --db --label wk -- python tools/walk_world.py drop --label <L>`;
    `git -C /opt/assetecon/AssetOpsV1 worktree remove /opt/assetecon/AssetOpsV1-wk<L>`. The L2, its manifests, the
    key folder and `assetops_polish_walk1113_test` stay as they are.

If `main` moves after step 3 and the walkthrough should show the newer code, make a new WK with the next label
(`<L>b`) from step 1, then tear down the old one. Never re-point a running serve at a newer tree (D-WK.6).

## 6. Done (questions; each can fail)

1. Is the copy refused unless the L2 is at today's key with its check passed on today's check inputs?
2. Is the copy's only DDL one `CREATE DATABASE ... TEMPLATE`, and is the protected walkthrough database never named
   outside its refusal?
3. Do W1 to W7 fail on a stale parent, a snapshot that no longer verifies, an undeclared row, a month not served
   current and reconciled, a figure off the independent model, a second walk database, or a failed step?
4. Does the serve hold no key folder, real-data switch or operational-entry switch, and refuse ports 8990 and 5490?
5. Does `smoke` fail on any server error on any page at any Site?
6. Does each plant in the reviewer guide fail its named test?

## 7. Units

| Part | Units |
|---|---|
| §2 definition and reader; §3.1 to §3.3 copy and prepare; T1 to T5 | 0.5 |
| §3.4 check W1 to W7; T6, T7 | 0.35 |
| §3.5, §3.6 serve, smoke script, stop, status, drop; T8 to T12; packet | 0.4 |
| Rev 2 (R1 to R6, I1 to I5): `walk_url` and its guard, `WalkDeps`, smoke env and S4, tree refusal; T1, T5, T8, T12 additions | 0.15 |
| **Total** | **1.4** |

One commit. Then the coordinator's run (§5): about 26 minutes this time (step 1 builds and checks a new L2, R1), about
15 when L2 is current.

## 8. Out of scope

The world itself (DS4); telemetry (DS2); an operator's real data (RC4); the 13 Nov walkthrough database and its serve;
DDR's rehearsal; any product change; a second tenant (the world has one).

## 9. Decision queue (W3; defaults applied)

| # | Question | Default |
|---|---|---|
| Q1 (owner) | What the walkthrough database adds to the world | Two emulated finance-lead statements and one snapshot rebuild; no agreed Action (D-WK.3, row 53) |
| Q2 (owner) | Ports | 8991 and 5491; 8990 and 5490 stay with the 13 Nov serve (D-WK.5, row 54) |
| Q3 | Prepare's builder identity | `service:world-build`, as the world's own snapshots |
| Q4 | Whether the serve gets the pseudonym key folder | No: nothing on the walkthrough uploads (least privilege) |
| Q5 | Whether 5c's screen must be in the served tree | No. S2 needs only 5c's route (units 1 and 2). If the screen is not merged, `/portfolio/month` shows the live product's fallback page, and the owner walks the screen as 5c's spec says (D-WK.9) |
| Q6 | The new L2's C4 after 0K4a, 0K4b and 0K4e | A stop if it FAILs; never absorbed by the oracle (D-WK.10) |
| Q7 (owner) | Two figures for one quantity on the served pages | Only plan against actual, Kisiwa's budget notice, and statement against records while unmatched (D-WK.12; owner-away row 66) |
| Q8 (owner) | Day-14 order | 3C2 unit 2, world build and check, WK, then DDR (D-WK.14; owner-away row 67) |
