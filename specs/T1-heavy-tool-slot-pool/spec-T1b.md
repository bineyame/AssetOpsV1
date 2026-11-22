# T1b: a second Postgres test lane (implementer spec)

Status: spec rev 1, 2026-11-22. Architect: Claude. Rulings `D-T1.19`-`D-T1.26` (`rulings.md`, "T1b rulings").
Owner approval, verbatim: `owner/owner-second-db-lane-2026-11-22.md` ("proceed").
Branch `task/T1b-db-lanes` from `main`, own worktree. Review depth: discovery (W5), one fresh Claude reviewer.
`USER_REVIEW_REQUIRED: false`. Size: **1.0 u** (§11).

Read first: T1 `spec.md` §2 (records, lock protocol, marker, order), §3, §5.1, §5.3, §7; `backend/TESTING.md`
"The test database". This spec changes only what it names; every other T1 rule stands.

## 1. Outcome and why

Today `db-job.lock` admits one database run at a time, and the brief footer puts every focused Postgres run under
`--db`, so four build lanes queued behind one 60-minute run. The database is not the reason: since the run-owned
harness (`backend/tests/pg_harness.py`) every run already works in its own `<stem>_pt<run>_<tag>_test` databases.
What two runs still share is the **base database** (its stem names the sweep, the admin lease and every
stem-derived name) and one **fixed-name helper** (`_case_db`, §6). T1b gives each of two runs its own base, so
two focused Postgres runs proceed side by side, while a heavy database job keeps the whole database side to itself.

## 2. Structure: records and rules

### Lanes (D-T1.19)

| Lane | Lock in `D` | Owner file | Base database (container `assetopsv1-postgres-1`) |
| --- | --- | --- | --- |
| `a` | `db-job.lock` (unchanged file) | `db-job.owner` | `assetops_test` (exists) |
| `b` | `db-job-b.lock` (new) | `db-job-b.owner` | `assetops_b_test` (new, §7) |

`LANE_DATABASES = {"a": "assetops_test", "b": "assetops_b_test"}` lives once, in `tools/heavy_slot_check.py`;
`tools/run-host-tests.ps1` holds the same two names (a parity test, T-L6, compares them).

Why `assetops_b_test` and not `assetops_test_b`: the harness and every guard require the name to **end** in
`_test` (`pg_harness._stem`, `_guard`, `route`). `assetops_b_test` has stem `assetops_b`, and no lane-a pattern
(`^assetops_pt…`, `assetops_out_…`) can match a lane-b name or the reverse.

### Two entry kinds (D-T1.20; amends D-T1.4)

| Flag (bash / pwsh) | Takes | Used for |
| --- | --- | --- |
| `--db` / `-Db` (meaning unchanged: one heavy database job at a time) | lane a **and** lane b, then one slot | every §5.5 entry point (`demo_combined`, `chain_clone`, `mechanism_dataset`); every run whose tier includes slow; the container runner with `-Server shared` (§5) |
| `--db-lane` / `-DbLane` (new) | the first free lane (a, then b), then one slot | every other Postgres run: focused host files, `run-host-tests.ps1`, plain `.venv/bin/python -m pytest` with a URL |
| neither | one slot | container runs on the dedicated server (unchanged), non-DB tools |

`--db` together with `--db-lane` is a usage error, exit 64: `heavy-slot: --db and --db-lane are exclusive; give one.`

An exclusive (`--db`) holder counts as lane `a` for its own pytest runs.

### Markers (D-T1.21)

| Holder | Exports to the child | Unsets |
| --- | --- | --- |
| `--db` | `ASSETOPS_HEAVY_SLOT`, `ASSETOPS_HEAVY_DB=<D>/db-job.lock`, `ASSETOPS_HEAVY_DB_B=<D>/db-job-b.lock` | `ASSETOPS_HEAVY_DB_LANE` |
| `--db-lane` | `ASSETOPS_HEAVY_SLOT`, `ASSETOPS_HEAVY_DB_LANE=<D>/db-job.lock` or `<D>/db-job-b.lock` | `ASSETOPS_HEAVY_DB`, `ASSETOPS_HEAVY_DB_B` |
| neither | `ASSETOPS_HEAVY_SLOT` | all three |

Marker names and leaf patterns (the T1 §2 marker test, steps 1-4, unchanged otherwise):

| Name | Leaf |
| --- | --- |
| `slot` | `^slot-[12]\.lock$` |
| `db` | `^db-job\.lock$` |
| `dbb` (new) | `^db-job-b\.lock$` |
| `lane` (new) | `^db-job(-b)?\.lock$` |

- **Exclusive passes** when `ASSETOPS_HEAVY_DB` passes `db` **and** `ASSETOPS_HEAVY_DB_B` passes `dbb`.
- **Lane passes** when exclusive passes (lane `a`), or `ASSETOPS_HEAVY_DB_LANE` passes `lane` (lane = `a` for
  `db-job.lock`, `b` for `db-job-b.lock`).
- `require(..., db=True)` (every existing call site, unchanged) now means exclusive passes. A lane-only holder
  therefore cannot start a heavy database job.

### Nesting (amends D-T1.13)

After the slot marker passes:
- `--db` and exclusive fails: exit 69, the existing line `heavy-slot: refused: --db inside a held slot; put --db
  on the outermost wrapper.`
- `--db-lane` and lane fails: exit 69, `heavy-slot: refused: --db-lane inside a held slot; put --db-lane on the
  outermost wrapper.`
- otherwise take nothing (bash `exec "$@"`, pwsh runs it directly). No nested entry waits.

### Order and deadlock freedom

- `--db`: lock `db-job.lock` (poll), then `db-job-b.lock` (poll, holding a), then the lowest free slot.
- `--db-lane`: each poll tries `db-job.lock` then `db-job-b.lock`; the first it gets is its lane; then a slot.
- A process waits holding at most DB locks, never a slot. Every slot holder is running its child. Two `--db`
  entries both start with lane a, so they cannot hold one lane each. No cycle can form.
- One deadline for all waits (default 1200 s, exit 75), as today. A `--db` waiting on lane b keeps lane a, so
  it cannot be starved by lane-a runs; starvation by lane-b runs stays bounded by the deadline (D-T1.18 stands).
- Wait lines, each printed once: `heavy-slot: another database job holds db-job.lock; waiting up to <n> s.`
  (unchanged), `heavy-slot: another database job holds db-job-b.lock; waiting up to <n> s.`,
  `heavy-slot: both database lanes are busy (tools/heavy-slot.sh --status); waiting up to <n> s.`

### Owner files and status

- Owner field `db=` takes `yes` (`--db`), `lane` (`--db-lane`) or `no`. A `--db` holder writes `db-job.owner` and
  `db-job-b.owner`; a lane holder writes its lane's file only. Removal at exit is unchanged (by `pid=`).
- `--status` prints `slot-1`, `slot-2`, any other `slot-N`, then `db-job`, then **`db-job-b`**, in the existing
  line forms.

## 3. The wrappers and checkers (file by file)

All four halves keep parity (T1 §2). Messages are byte-identical between bash and pwsh.

- **`tools/heavy-slot.sh`.** Option `--db-lane` sets `hs_lane=1` and adds `-DbLane` to `hs_opts`; the 64 check
  for both flags runs right after parsing. `hs_marker` accepts the names `dbb` and `lane` per §2. Nesting per §2.
  Acquire per §2 (lane loop: `exec {fd}>>"$D/db-job.lock"`, `flock -n -x`, else close and try `db-job-b.lock`).
  All paths are computed before the first lock open (D-T1.2). The child closes every lock fd it did not need to
  keep (none) and gets the §2 marker table. Status adds `db-job-b`.
- **`tools/checks/_heavy_slot.ps1`.** `Test-HeavyMarker` accepts `dbb` and `lane`. `Enter-HeavySlot` gains
  `[switch]$DbLane`; with both switches it writes the 64 line and `exit 64`. The handle gains `DbBPath`,
  `DbBStream`, `LanePath`, `LaneStream`; `Exit-HeavySlot` disposes every stream it holds and removes its owner
  files. `Assert-HeavySlotHeld` gains `[switch]$DbLane` (lane passes, per §2) and `-Db` now means exclusive.
  `Get-HeavyContainerMarker` returns `db` only when exclusive passes, otherwise `slot`. `Get-HeavyRefusal` takes
  a mode (`''`, `db`, `lane`); `lane` prints `--db-lane ` / `-DbLane `. Status adds `db-job-b`.
- **`tools/heavy-slot.ps1`.** Parses `-DbLane`; passes `-DbLane:$dbLane` to `Enter-HeavySlot`; sets the child
  environment per §2 (removing the unset names); `SetOwners` gets every owner file of the held locks.
- **`tools/heavy_slot_check.py`.**
  - `_marker` accepts `dbb` and `lane`; a new `held_lane(env, **opts) -> str | None` returns `"a"`, `"b"` or
    `None` per §2; `check_marker(..., db=False, lane=False)`: `db` needs exclusive, `lane` needs a lane.
  - In a container (`in_container`): `lane=True` passes for `db` and for `slot` (the container runs on its own
    server, D-T1.22); `db=True` is unchanged.
  - New reason `_LANE = "a Postgres test run needs --db-lane (or --db) on the outermost wrapper"`.
  - `refusal(tool, reason, db=False, lane=False)`: `lane` prints `--db-lane ` and `-DbLane `.
  - `require(tool, *, db=False, lane=False, exit_with=None)`: after the marker passes, when `lane` is true and not
    in a container, it calls `lane_database_refusal(held_lane(...), url)` with `url =
    os.environ.get("ASSETOPS_TEST_DATABASE_BASE_URL") or os.environ.get("ASSETOPS_TEST_DATABASE_URL")`; a
    returned line is printed and exits 69 the same way.
  - New `lane_database_refusal(lane, url, environ=None) -> str | None` (§4).
  - New `lane_workers_refusal(numprocesses, env=None) -> str | None` (D-T1.25): when a lane-only holder (lane
    passes, exclusive fails) runs with `numprocesses` not in `(None, 0, 1, 2)` (any string, such as `auto`,
    counts as over), returns `heavy-slot: refused: a database-lane run uses at most -n 2 (T1b); use --db for
    more.`
- **`tools/heavy_slot_check.cjs`.** Parity of the marker test only: `markerTest` accepts `dbb`; `db: true` needs
  exclusive. No lane API (no JS tool runs Postgres).

## 4. Getting a lane and its URL (D-T1.22, D-T1.23)

- **`backend/tests/conftest.py` and `host/conftest.py`.** The first statement of `pytest_configure` stays one
  statement (D-ENV1.21 keeps the namespace line second):
  `if os.environ.get("ASSETOPS_TEST_DATABASE_URL"): _heavy_slot_check().require("pytest with Postgres", lane=True, exit_with=pytest.exit)`.
  Right after the ENV-1 namespace line, in both conftests, in the controller only (`os.environ.get(
  "PYTEST_XDIST_WORKER") is None`):
  `r = _heavy_slot_check().lane_workers_refusal(getattr(config.option, "numprocesses", None)) if os.environ.get("ASSETOPS_TEST_DATABASE_URL") else None`,
  then `if r: pytest.exit(r, returncode=69)`.
- **`lane_database_refusal(lane, url)`**, first failure wins; each returns
  `heavy-slot: refused: pytest with Postgres in database lane <lane> may not use <name>: <why>.`:
  1. `assetops_backend.database_target.database_target(url, environ)` (RC4-F1) raises: `<name>` is `that URL`,
     `<why>` is `the target is unclear (<reason>)`. An `ImportError`: `<why>` is `assetops_backend does not import`.
  2. The name does not end in `_test`: `its name does not end in _test`.
  3. The host is not `127.0.0.1`, `localhost` or `::1`: `the server is not this machine's development server
     (host <host>)`.
  4. The name is the other lane's base (`LANE_DATABASES`): `it is lane <other>'s database`.
  5. Otherwise `None`. A private `assetops_<task>_test` base stays allowed (TESTING.md); two lanes on the same
     private base is a documented gap (§10).
- **`tools/run-host-tests.ps1`.** When `ASSETOPS_TEST_DATABASE_URL` is unset, the database is `assetops_b_test` if
  the leaf of `$env:ASSETOPS_HEAVY_DB_LANE` is `db-job-b.lock`, else `assetops_test` (user, password and port as
  today). It still never prints the URL. A set URL is passed through; the conftest checks it.
- **Plain pytest** (`tools/heavy-slot.sh --db-lane -- .venv/bin/python -m pytest <files>`): the caller sets the
  URL. The idiom TESTING.md gives: `ASSETOPS_TEST_DATABASE_URL=postgresql+psycopg://assetops:<pw>@127.0.0.1:55432/$( [ "${ASSETOPS_HEAVY_DB_LANE##*/}" = db-job-b.lock ] && echo assetops_b_test || echo assetops_test )`
  evaluated inside a `bash -c` child of the wrapper. The conftest refuses a wrong pairing either way.

## 5. Shared and serialised (D-T1.24)

| Resource | Shared by | After T1b |
| --- | --- | --- |
| Run template and its migration to head | one run (`<stem>_pt<run>_tpl_test`) | not shared; no lock needed. Each run migrates its own template once, as today |
| Base database (admin lease, sweep, advisory keys) | all runs of a base | one lane per base, so one run per base at a time |
| `_case_db` databases `assetops_out_<slice>_<case>_test` (9 modules) | **every run on the server** (fixed name) | stem-derived, §6: lane-scoped; lane a's names are byte-identical |
| Setup-cache snapshots `assetops_sc_<code>_<key>_test`; mechanism templates `assetops_mechanism_<kind>_<fp8>_test` | content-keyed, shared on purpose | unchanged: built under an advisory lock or by an exclusive `--db` job, published by staging + rename, read by `CREATE DATABASE … TEMPLATE` (a share lock) |
| A heavy database job, a slow-tier run (`test_demo_combined_postgres.py`'s prepare) | the server's disk and memory | stays exclusive (`--db`) |
| The dedicated container server `postgres-test` and its setup-cache sweep | container runs | unchanged (no lane); `-Server shared` puts a container run on `assetopsv1-postgres-1`, so it needs `--db` |

Edits:
- `tools/run-backend-suite-in-container.ps1`, after line 51: `if ($Server -eq 'shared') { Assert-HeavySlotHeld
  -Tool "the container test runner on the shared server" -Db }`.
- `backend/tests/test_demo_combined_postgres.py`, first line of the `demo` fixture: load `tools/heavy_slot_check.py`
  by path exactly as `conftest._heavy_slot_check` does (`Path(__file__).resolve().parents[2] / "tools" /
  "heavy_slot_check.py"`) and call `.require("the slow-tier prepare", db=True)`. Inside the container this passes
  on the `db` marker.

## 6. The fixed-name class (W6)

The class: a database a test creates whose name ignores the base stem and the run, so two runs on one server
collide. Sweep result (every `CREATE DATABASE` site under `backend/tests` and `host`): `pg_harness.py` (stem +
run), `setup_cache.py` and `mechanism_dataset.py` (content-keyed, above), `test_md0_mechanism_postgres.py` and
`test_w504_ev_work_producer_postgres.py` (random token), `test_pg_harness.py` (stem-derived), `test_ds4_world.py`
and `test_wk_walk_world.py` (fakes, no server), `test_demo_combined_postgres.py` (run id) and
**`test_out_b4_board_postgres.py` `_case_db`, the one member**.

Fix: in `test_out_b4_board_postgres.py`, a new `_case_db_name(case, slice_="b") -> str` returns
`f"{stem}_out_{slice_}_{case}_test"` with `stem = make_url(os.environ.get(pg_harness.BASE_ENV) or URL).database[:-len("_test")]`;
`_case_db` uses it. Callers do not change. Lane a gives `assetops_out_b_<case>_test`, as today.

Class closure: test T-L5 lists the `CREATE DATABASE` files above; a new file containing `CREATE DATABASE` under
`backend/tests` or `host` fails it until it is added with its isolation reason.

## 7. Creating the second database (D-T1.26)

- One command, idempotent, run once by the builder at the DB smoke (§9 S1) and again harmlessly by anyone:
  `docker exec assetopsv1-postgres-1 sh -c "psql -U assetops -d postgres -tAc \"SELECT 1 FROM pg_database WHERE datname='assetops_b_test'\" | grep -q 1 || createdb -U assetops -O assetops assetops_b_test"`.
  It touches only `assetops_b_test` (a `*_test` name in the authorised container).
- `backend/db/init/01-test-database.sql` gains `CREATE DATABASE assetops_b_test OWNER assetops;` for a fresh volume.
- **No migration.** The base is an administrative connection only; each run migrates its own template to head.
  Under `ASSETOPS_TEST_TEMPLATE=0` a run migrates its base in place, which its lane lock already serialises.

## 8. Tests (written first)

In `tools/checks/test_heavy_slot_pool.mjs` (each in its own `makeRepo`, no database; total stays under 45 s):
- **P9 unchanged** (two `--db` entries; the second times out). Add: the first holder's status shows `db-job` and
  `db-job-b` busy.
- **P10** expects four free lines: `slot-1`, `slot-2`, `db-job`, `db-job-b`; the busy variant's `lines[4]` is
  `db-job-b: free`; a probe creates neither DB file.
- **P16** two `--db-lane` holders (one bash, one pwsh) run at once and get `db-job.lock` and `db-job-b.lock`
  (their `ASSETOPS_HEAVY_DB_LANE`, printed by the child); a third bash and a third pwsh with wait 3 exit 75 with
  the lanes-busy line.
- **P17** a `--db` entry waits (75, wait 3) while one `--db-lane` holds lane b, printing the `db-job-b.lock` line;
  a `--db-lane` entry waits (75) while a `--db` holds both.
- **P18** nesting: `--db-lane` inside a `--db` holder takes nothing (exit 0, under 3 s); `--db` inside a
  `--db-lane` holder and `--db-lane` inside a plain slot exit 69 at once with their lines; `--db --db-lane` and
  `-Db -DbLane` exit 64.
- **P-T4b** python and node: `db=True` fails under a lane-only marker and passes under `--db`; python `lane=True`
  passes under either and fails under a plain slot; container `slot` passes `lane=True`.
- **P-T8 (the planted shared-DB use)** in the temp repo with `PYTHONPATH=<worktree>/backend`, under a lane-b
  holder, `python -c "import heavy_slot_check as h; h.require('pytest with Postgres', lane=True)"` with
  `ASSETOPS_TEST_DATABASE_URL=postgresql+psycopg://u:p@127.0.0.1:1/assetops_test` exits 69 with `it is lane a's
  database`; with `…/assetops_b_test` exits 0; under lane a, `…/assetops_b_test` exits 69; `…/assetops` exits 69
  (`does not end in _test`); host `10.0.0.9` exits 69. No connection is made.

In a new `backend/tests/test_t1b_db_lanes.py` (no database, no URL needed):
- **T-L1** `lane_database_refusal` table: the five rules of §4 and a private `assetops_x_test` allowed.
- **T-L2** `lane_workers_refusal`: `None`, 1, 2 pass; 3 and `"auto"` refused under a lane-only marker
  (an injected `env` and `held_lane` stub); everything passes under exclusive.
- **T-L3** `_case_db_name("kobo", "d")` is `assetops_out_d_kobo_test` with base `assetops_test` and
  `assetops_b_out_d_kobo_test` with base `assetops_b_test` (env set by `monkeypatch`).
- **T-L4** a text check of `tools/run-host-tests.ps1` (the script never prints the URL, so a run cannot show it):
  it contains both lane names and the `db-job-b.lock` leaf test on `ASSETOPS_HEAVY_DB_LANE`.
- **T-L5** the `CREATE DATABASE` file list of §6 equals `git grep -l "CREATE DATABASE" -- backend/tests host`.
- **T-L6** `LANE_DATABASES` values equal the two names in `run-host-tests.ps1`.

## 9. Proof and acceptance

Planted violations (RULES §7; plant, run, revert): P-T8's lane-b/`assetops_test` case (the shared-DB use); revert
`_case_db_name` to the fixed name and T-L3 fails; drop the `dbb` half of the exclusive test in `heavy_slot_check.py`
and P-T4b fails.

**S1, the live smoke** (coordinator's DB turn; `--status` must show both lanes free). One bash call:
1. the §7 create command;
2. start two runs together, `tools/heavy-slot.sh --db-lane --label t1b-<x> -- pwsh -NoProfile -File
   tools/run-host-tests.ps1 -- backend/tests/test_pg_harness.py backend/tests/test_out_b4_board_postgres.py -q`
   for `x` in `a`, `b`, each `> <scratch>/t1b-<x>.log 2>&1 &`;
3. after 20 s: `tools/heavy-slot.sh --status` shows `db-job` and `db-job-b` busy, and
   `SELECT DISTINCT datname FROM pg_stat_activity WHERE datname LIKE 'assetops_b_%'` is not empty;
4. `wait` for both; both exit 0;
5. `SELECT datname FROM pg_database WHERE datname ~ '^assetops_(b_)?(pt|out_)'` returns no row.
Read-only queries via `docker exec assetopsv1-postgres-1 psql -U assetops -d postgres -tAc`. Delete the logs.

Acceptance (each must be answerable yes):
- A1 Do two focused Postgres runs hold lanes a and b at once and both pass (S1)?
- A2 Does a third lane entry wait and time out with the lanes-busy line (P16)?
- A3 Does every heavy database job and slow-tier run still exclude every other database run (P9, P17, P-T4b)?
- A4 Is a lane-b run pointed at `assetops_test` refused before any test imports (P-T8)?
- A5 Is a non-`_test`, unclear or off-machine URL refused at configure time (P-T8, T-L1)?
- A6 Does the existing heavy-slot self-test pass, with only P10's line list changed (P1-P15, P-T1-P-T7, A11)?
- A7 Is lane a byte-identical to today for names (`assetops_test`, `assetops_out_<slice>_<case>_test`) (T-L3)?
- A8 Does a new `CREATE DATABASE` site fail T-L5 until listed?

## 10. Documents and documented gaps

- `backend/TESTING.md` "The heavy-tool slot pool": the lane table, `--db-lane`, which runs are `--db`, the URL
  rule; every host example (lines 176-196) becomes `-DbLane` except the full and slow forms, which stay `-Db`.
- `.ai/RULES.md` heavy-tools line: `(--db-lane for a Postgres test run, --db for a database job)`.
- The brief footer in `.ai/ROLE_CONFIG.md` (`--db` → `--db-lane`) is the coordinator's edit at merge (decision
  queue 2); the builder does not touch `ROLE_CONFIG.md`.
- `.ai/state/tools.md` T1b entry and its `index-2.md` line at the closing commit.
- Gaps: two lanes on one private base collide on stem-derived names (rare, deliberate); a SIGKILLed wrapper frees
  its lane at once (as D-T1.2); a FIFO for `--db` is still a follow-up (D-T1.18).

## 11. Checks, sizing and units

Checks: P/T tests above; `node --test tools/checks/test_heavy_slot_inventory.mjs`; `python
tools/check-decision-index.py`; `pwsh -NoProfile -File tools/check-agent-workflow.ps1`; `statement_catalogue.py`
(exit 0 or identical to main); a pooled smoke of `backend/tests/test_pg_harness.py` under `--db-lane`; S1. Both
conftests are ALWAYS_FULL: D-T1.17's smoke rule applies, the full suites run at the next milestone.

| Unit | Work | u |
| --- | --- | --- |
| U1 | bash + pwsh wrappers and module (§2, §3) | 0.4 |
| U2 | python + cjs checkers, conftests, runner edits, `_case_db_name`, init SQL (§3-§7) | 0.3 |
| U3 | tests P9-P18, P-T4b, P-T8, T-L1-T-L6, S1, documents | 0.3 |
| | **Total** | **1.0** |

Commit plan: commit 1 tests + wrappers (U1); commit 2 checkers and Python side (U2); commit 3 documents, S1
evidence in the packet. Handshake and closing commits do not count.

## 12. Decision queue (W3; defaults applied)

1. Lane b's name: `assetops_b_test` (default; the owner's example `assetops_test_b` fails the `_test` suffix rule).
   Owner may weigh in.
2. The brief footer switches to `--db-lane` when T1b merges (default: the coordinator makes the one-line edit in
   the merge commit).
3. A third lane: not now (default). The two T1 slots are the memory bound (D-T1.25), so a third lane would only
   queue on slots.
