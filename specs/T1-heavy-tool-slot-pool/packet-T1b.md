# T1b review packet: a second Postgres test lane

Branch `task/T1b-db-lanes`, worktree `/opt/assetecon/AssetOpsV1-t1b`. Spec `spec-T1b.md` rev 1, rulings D-T1.19-26.
`USER_REVIEW_REQUIRED: false`. Review depth: discovery (W5), one fresh Claude reviewer. Mid-build questions: none.
Evidence: `/opt/assetecon/evidence/T1-heavy-tool-slot-pool/T1b-build-2026-11-22/` (red/green logs, plants, S1).

## Outcome

Two focused Postgres runs now proceed side by side: `--db-lane` / `-DbLane` takes lane a (`db-job.lock`,
`assetops_test`) or lane b (`db-job-b.lock`, `assetops_b_test`). `--db` / `-Db` keeps its meaning and takes both.

## Commits

- `ce9afb59f` U1: both wrappers and `_heavy_slot.ps1` (flags, markers, nesting, acquire order, owners `db=lane`,
  status `db-job-b`); P9 addition, P10 four lines, P16-P18 (red first: 5/5 failed, `red1.log`).
- `807d7a6dc` U2: `heavy_slot_check.py` (`exclusive`, `held_lane`, `check_marker(lane=)`, `refusal(lane=)`,
  `require(lane=)`, `lane_database_refusal`, `lane_workers_refusal`, `LANE_DATABASES`); cjs `db` needs `dbb`;
  conftests; `run-host-tests.ps1` lane URL; container runner `-Server shared` needs `-Db`; demo fixture
  `require(db=True)`; `_case_db_name`; init SQL; `test_t1b_db_lanes.py` T-L1..T-L6; P-T4b, P-T8 (red first:
  python 26 failed / 1 passed (T-L5 by design), `red3.log`; P-T4b and P-T8 failed, `red2.log`).
- `0197e767d` P-T4b forged lane-a exclusive case (the dbb plant was not caught without it); T-L5 file had the
  literal in its own docstring (only visible once tracked).
- `7a7dc7ba4` documents: `backend/TESTING.md` (lane table, `--db-lane`, URL rule, host examples `-DbLane`),
  `.ai/RULES.md` heavy-tools line.
- `91047a8d7` P17: the two `--db` timeouts run one at a time (run together they queue on lane a, which is correct).
- closing commit: this packet, spec status, `specs/INDEX.md`, `.ai/state/tools.md` + `index-3.md` line 207.

## Acceptance

- **A1 yes (S1).** Revision `91047a8d7`, 18:52:53-18:54:45 UTC. Both lanes free at start; `createdb` exit 0. At
  20 s `--status`: slot-1 + `db-job` held by `t1b-a`, slot-2 + `db-job-b` held by `t1b-b`;
  `pg_stat_activity` had `assetops_b_test` sessions. Both exit 0: `26 passed, 1 xfailed` each (109.9 s and
  110.1 s), 112 s wall for both (about 220 s one after another).
- **A2 yes.** P16: bash and pwsh holders print `.../db-job.lock` and `.../db-job-b.lock`; a third bash and a
  third pwsh exit 75 with the lanes-busy line.
- **A3 yes.** P9 (`--db` holds both, shown in status), P17 (`--db` waits on lane b with the `db-job-b.lock` line;
  `--db-lane` waits while `--db` holds both), P-T4b (`db=True` refused under a lane, including a forged
  `ASSETOPS_HEAVY_DB=<lane a lock>`).
- **A4 yes.** P-T8: lane b + `assetops_test` exits 69 `it is lane a's database`. A live check at configure time
  (both conftests) refuses before any import (`conf-smoke`, see below).
- **A5 yes.** P-T8 (`assetops` not `_test`; host `10.0.0.9`); T-L1 (unclear driver, `None`, `PGHOST` env,
  ImportError; `::1`, `localhost` and a private `assetops_x_test` allowed).
- **A6 yes.** `node --test tools/checks/test_heavy_slot_pool.mjs`: 40 tests, 40 pass, 0 fail, 40.5 s (under 45 s).
  Only P10's line list changed among old cases (plus the P9 addition the spec names).
- **A7 yes.** T-L3: `assetops_out_d_kobo_test` (base `assetops_test`), `assetops_b_out_d_kobo_test` (lane b).
- **A8 yes.** T-L5 fails on a planted tracked file with the literal (`pl4.log`).

## Checks (real output)

- Planted (each committed first, reverted by `git checkout`): drop the other-lane rule -> P-T8 fails
  (`PASSED` where 69 expected); `_case_db_name` back to the fixed name -> T-L3 fails; drop the `dbb` half of
  `exclusive` -> P-T4b fails (`database job: code 0; PASSED`); new create-database site -> T-L5 fails.
- Configure-time smoke (no DB contact): plain slot + URL -> 69 lane reason; lane b + `assetops_test` -> 69;
  lane + `-n 3` -> 69 workers line; host conftest lane b + `assetops_test` -> 69.
- `pytest backend/tests/test_t1b_db_lanes.py`: 27 passed. `node --test tools/checks/test_heavy_slot_inventory.mjs`:
  8/8. `tools/check-architecture.ps1` (guard python set): `Architecture check passed.` (108.8 s).
  `statement_catalogue.py`: exit 0, `OK statement catalogue`. `check-decision-index.py`: OK.
  `check-agent-workflow.ps1`: `Agent workflow check passed.` (on the closing commit).
- Not run: full suites (not scheduled; both conftests are ALWAYS_FULL, D-T1.17: full suites at the next milestone).
  Layout evidence: not applicable (no UI).

## Known deviations

1. S1 step 5 was not clean: each lane left its run's `<stem>_pt<run>_tpl_test` template. This happens on lane a
   too (another agent's lane-a run on main's code swept mine and left its own, `assetops_pt30af01d26e_tpl_test`).
   So it comes from the existing harness, not from T1b. The next run's sweep on that base removes it. I dropped
   my lane-b leftover by hand. `out_` databases: none left.
2. `lane_database_refusal(lane, None)` refuses (`URL_UNREADABLE`); `require(lane=True)` with no URL is therefore
   refused. The conftests only call it when the URL is set.
3. P-T8 needs a Python with SQLAlchemy: it uses `ASSETOPS_GUARD_PYTHON`, else `<repo>/.venv/bin/python`, else
   main's venv; it fails with a clear message when none exists.

## Residual risk

- Transition at merge: a `--db` holder started from the old wrapper holds only `db-job.lock`. A new `--db-lane`
  entry would take lane b beside it. Merge when `--status` shows `db-job` free (or accept one overlap: lane b's
  databases are isolated by name).
- Two lanes on one private base collide (documented gap). No FIFO for `--db` (D-T1.18).

## Review focus

- `tools/heavy-slot.sh` fd bookkeeping (`hs_fds` closed in the child and before `rm`), and bash/pwsh message parity.
- `heavy_slot_check.require`: the lane database check runs only after the marker passes and never in a container.
- Conftest second block: controller only, before workers start.

## Coordinator at merge

- Switch the brief footer in `.ai/ROLE_CONFIG.md` from `--db` to `--db-lane` (decision queue 2).
- `assetops_b_test` already exists in `assetopsv1-postgres-1` (created by S1; the init SQL covers fresh volumes).
