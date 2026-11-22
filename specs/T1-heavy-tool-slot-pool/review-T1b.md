# T1b review: a second Postgres test lane

## Round 1 (discovery, W5), 2026-11-22, branch `task/T1b-db-lanes` at `6f179dcaa`

Summary:
- Verdict: **accept, with M1 addressed before or at merge** (a merge-procedure or small code fix; no High).
- The design holds: lock order is cycle-free, `--db` still excludes every new-tools database run, markers and
  nesting match the spec in all four halves, `_case_db` is stem-derived with lane a byte-identical, and the lane
  database refusal runs at configure time before any test module imports.
- M1: until every worktree runs this branch's tools, a pre-T1b `--db` job holds only lane a, so a new `--db-lane`
  run takes lane b beside a heavy database job. The packet's "merge when db-job is free" does not cover it.
- Low: L1 stale `ASSETOPS_TEST_DATABASE_BASE_URL` can make the conftest check a different base than the harness
  uses; L2 the setup-cache advisory lock is per database, so it does not serialise across lanes (spec §5 and T-L5
  say it does); L3 `backend/README-db.md:85` still exports a fixed `assetops_test` URL, which lane b refuses.
- Checks rerun (non-DB only, per dispatch): T-L 27/27, inventory 8/8, self-test 40/40, architecture, workflow,
  catalogue, decision index all pass. S1 not rerun (live lanes in use); cited from the packet.

### Scope read

`spec-T1b.md`, rulings D-T1.19-26, `packet-T1b.md`, T1 `spec.md` (sections named by spec-T1b), and
`git diff main...HEAD` (21 files). Also read for the sweep: `backend/tests/pg_harness.py` (`route`, `_admin`,
`_owned_pattern`, `cleanup_run`), `backend/tests/setup_cache.py` (`_save`, `_save_database`), the tools that run
`CREATE DATABASE` and the tests that drive them.

### Findings

**M1 (Medium, merge caution; packet `packet-T1b.md:75-77`).** Mixed old and new tools break A3 for longer than
"at merge". The lock directory is the git common dir, shared by every worktree (`git worktree list`: about 330).
A worktree whose branch predates T1b keeps its own old `tools/heavy-slot.sh`, whose `--db` takes only
`db-job.lock`. After merge, any new-tools `--db-lane` entry finds `db-job-b.lock` free and runs beside that old
`--db` job, which may be a `demo_combined` prepare, a slow-tier run or a mechanism build: exactly the "exclusive
today becomes concurrent by accident" that D-T1.20 rules out. This lasts until every worktree that may run `--db`
has merged main, not only until the current `db-job` holder exits. Names stay isolated (lane b's databases are
stem-distinct), so the risk is memory and disk load and a template being dropped or renamed while a lane-b run
clones it, not a wrong database. (The reverse direction is fail-safe: an old wrapper given `--db-lane` exits 64.)
Fix, either: (a) code, small: when `--db-lane` gets `db-job-b.lock`, read `db-job.owner`; if it says `db=yes`
with a live `pid` and `db-job-b.owner` is not that pid's, release lane b and keep waiting (both halves, one P
case); or (b) procedure: the coordinator switches the brief footer to `--db-lane` only after the active DB-using
worktrees (today `dd3c`, `dd4` and any lane that may run `--db`) have merged main, says so in the merge commit,
and the packet's residual-risk paragraph is corrected to that.

**L1 (Low, `tools/heavy_slot_check.py:243` against `backend/tests/pg_harness.py:99`).** `require` checks
`ASSETOPS_TEST_DATABASE_BASE_URL or ASSETOPS_TEST_DATABASE_URL`, but a serial run with no
`ASSETOPS_TEST_RUN` set routes from `ASSETOPS_TEST_DATABASE_URL` and then overwrites the base variable. With a
stale base variable in the caller's environment (for example `BASE=…/assetops_b_test`, `URL=…/assetops_test`
in lane b), the check passes on the stale value while the run works on lane a's base, so A4 is bypassed. It needs
a hand-set variable, and the harness's lease-aware sweep limits the harm. Fix: pick the URL the way `route` does
(the base variable only when the run variable is also set), and add a T-L1 row for that pair.

**L2 (Low, `spec-T1b.md:168`, `backend/tests/test_t1b_db_lanes.py:129`, `backend/tests/setup_cache.py:776,290`).**
Postgres advisory locks are scoped to the current database. `setup_cache._save` takes its lock on the run's
admin connection, which is on the base, so lane a (`assetops_test`) and lane b (`assetops_b_test`) do not
exclude each other. Its staging database name `<snapshot>_wip_test` is fixed per key, so two lanes saving the same
key at once can drop each other's staging database or fail the rename. Exposure today is small: the cache is
on only when `ASSETOPS_SETUP_CACHE_DIR` is set, which only the container runner does, and a shared-server
container run is now `--db`; `_save` failures are caught and the live result stands. Fix: correct the spec §5
row and the T-L5 reason ("serialised by advisory lock within one base; host lanes do not enable it"), or take the
lock on the `postgres` maintenance database. A preference, not an acceptance gap.

**L3 (Low, `backend/README-db.md:85`).** README-db still tells agents to
`export ASSETOPS_TEST_DATABASE_URL=…/assetops_test`. With that exported, `run-host-tests.ps1` passes the URL
through, and every run that lands on lane b is refused with "it is lane a's database". This is fail-safe but
means about half of lane runs fail for anyone who follows README-db. Fix: point README-db at the lane rule in
TESTING.md (or the `bash -c` idiom), and do not export a fixed URL.

Nothing else found. Specifically checked and found correct:
- bash fd bookkeeping: `hs_fds` holds every lock fd plus the sleep pipe; the child and the `rm` subshell close all
  of them; a failed lane probe closes its fd at once (`tools/heavy-slot.sh:244-257, 283-290, 340-347`).
- Order: `--db` polls lane a, then lane b while holding a, then a slot; `--db-lane` takes the first free lane, then
  a slot; no process waits while holding a slot. Same in `_heavy_slot.ps1` (`Enter-HeavySlot`).
- Markers: `--db` exports both exclusive markers and unsets the lane marker; `--db-lane` the reverse; neither unsets
  all three (bash child block, `heavy-slot.ps1` env block). `db=True` needs both markers in py, cjs and pwsh.
- Nesting: `--db-lane` inside `--db` takes nothing; `--db` inside a lane and `--db-lane` inside a plain slot exit
  69 with the spec's lines; `--db --db-lane` exits 64 in both halves; messages identical.
- Conftests: the first statement stays one `require(..., lane=True)` line; the workers check runs in the
  controller only, after the ENV-1 line, before workers start; in a container the lane passes on `slot`.
- Fixed-name sweep: the only `CREATE DATABASE` literals under `backend/tests` and `host` are the nine T-L5 lists.
  Tests that drive database-creating tools (`w502`, `w504`, `w601_seed`, `world`) build through `_case_db`, a random
  token or not at all; the slow-tier tools they spawn (`demo_combined` tick) refuse under a lane (`db=True`), which
  is the right failure. Sweep patterns are anchored (`^<stem>_pt…`), so lane a's sweep cannot match lane b's names.
- `test_demo_combined_postgres.py` `demo` fixture requires `db=True` before any prepare.

### Checks run (from the worktree root, this head)

| Check | Result |
| --- | --- |
| `tools/heavy-slot.sh -- <main venv>/python -m pytest backend/tests/test_t1b_db_lanes.py -q` | 27 passed in 0.65 s |
| `tools/heavy-slot.sh -- node --test tools/checks/test_heavy_slot_inventory.mjs` | 8 tests, 8 pass |
| `tools/heavy-slot.sh -- node --test tools/checks/test_heavy_slot_pool.mjs` (temp repos, env scrubbed, no DB) | 40 tests, 40 pass, 40.7 s |
| `pwsh -NoProfile -File tools/check-architecture.ps1` (guard python set) | Architecture check passed. |
| `pwsh -NoProfile -File tools/check-agent-workflow.ps1` | Agent workflow check passed. |
| `tools/checks/statement_catalogue.py` | exit 0, `OK statement catalogue` |
| `tools/check-decision-index.py` | OK |

All jobs used a plain slot; no `--db` or `--db-lane` job was run from this branch's tools.

### Not verified

- S1 (two live lanes, 26 passed / 1 xfailed each) and the configure-time smoke: not rerun, because the live lanes
  were in use (at review time `db-job` was held by `AssetOpsV1-dd3c`). Cited from the packet at `91047a8d7`;
  later commits change only the P17 test and documents.
- The four plants: cited, not replanted.
- Full suites: not run (D-T1.17; next milestone).

### Residual risk not named in the packet

- A `--db` waiting on lane b holds lane a for up to the full deadline (1200 s) while new lane entries keep taking
  lane b, so in a busy period it can time out after blocking half the database capacity for 20 minutes
  (D-T1.18 accepts starvation; this cost of it is new with two lanes).
- T-L5 matches the exact upper-case literal only; a lower-case `create database` or a `createdb` call in a test
  would not be caught (none exists today).
- Leftover `<stem>_pt<run>_tpl_test` templates on both bases (pre-existing harness behaviour, packet deviation 1)
  now accumulate on two bases; each is removed only by the next run on that base.
