# DS4 review packet: units 1, 2 and 3

Implementer (Claude), 2026-11-21. Branch `task/DS4-template-ladder`; main `9f591dd5a` merged (`e7113c9f5`).
Commits: `11e8abb5b` (unit 1 part), `5f86021d0` (unit 1 rest: T12-T14), `9eff83776` (unit 2). Spec rev 3
(D-DS4.16 to D-DS4.27). Evidence: `/opt/assetecon/evidence/DS4/unit2-2026-11-21/` (T12-T14 log, plant outputs),
spike `/opt/assetecon/evidence/DS4/spike-2026-11-21/spike.log`. Mid-build count: 1 (MBQ-1, answered D-DS4.26/27).
`USER_REVIEW_REQUIRED: false` (a tool and a load rule; no screen; the demo impact of D-DS4.27 is the Architect's).

## Files

- `tools/world.py`: §3.1-§3.5 (unit 1); unit 2 adds `C4_CONTRACT` (§2.1 as a literal), `C4_SITE_CLASSES` (D-DS4.26),
  `C4_KNOWN_FINDINGS` (the 12 `plan.<f> D-DS4.27` lines), `site_class`, `judge_side`, `c4_oracle`, `harness_run`,
  `_c1`..`_c7`, `cmd_check`; `current_l2` keeps the ladder's inputs for C1.
- `backend/assetops_backend/evidence/bulk_load.py`: `BatchTimeUnreadable`, `envelope_span`, `cover_gap` (days from
  `chain.events.local_days`/`S3_BRACKET`, imported), step 7a, two codes in `BULK_LOAD_REFUSALS`.
- `.../evidence/adapters/postgres_evidence_ledger.py`: `site_timezone` beside `gateway_principal`.
- Tests: `test_ds4_world.py` (T1-T7, T9, T9b, T11; T6 staleness), `test_ds4_world_postgres.py` (T12-T14),
  `test_ds4_batch_days.py` (T8), `test_ds4_batch_days_postgres.py` (T15-T17), `test_s2_evidence_ledger_postgres.py`
  (`Kit.envelope` gains `interval_start`, default unchanged).

## Spec §7, one by one

1. Reuse at an unchanged key, partial rebuilt, stale/absent L2 refused naming the part: T2, T5, T6 pass.
2. Writes only through product commands with §3.5's env; names pass `permitted_database`; no `FORCE`: T4, T5, T11.
3. Frozen before the manifest, dropped only without descendants/sessions, keys erased first: T5, T12 (`datallowconn`
   false on all three rungs), T13 (`key_state` ERASED, `keys_left` 0), T14 (`WORLD_DATABASE_IN_USE`).
4. `check` fails on each named break (T9); C5 runs under `assetops_wc5_pt<hex>_base_test`, never `assetops_test`
   (T9 C5 case); staleness (T6). Real world (T12): C1 5 files, C2 136 tables, C3 1 snapshot matches, C5 (injected 0),
   C6 `0 batches (telemetry none)`, C7 7 steps: PASS. **C4 FAIL with 12 `known D-DS4.27` lines, 0 `new`.** Counts:
   Kisiwa actual 15 E / 32 B, Kobo and Mto actual 18 E / 29 B, every plan side 36 E / 11 B (§2.1 as amended). Blank
   list 135 = §2.1's B cells (123) + the 12 known cells. Exit 4, `passed: false` until 5a F1 merges.
5. Cover rule: T8 (a)-(g) and the unreadable cases, T15 (refused, ledger counts unchanged), T16/T16b (loaded),
   T16c (real-path COMPLETED gap batch: already loaded), T17 (exit 2, `BULK_BATCH_GAP_DAYS <b>`, `a` stored).
   DS3 regression unchanged (below).
6. Bench: unit 3, not built.
7. Plants P1-P34 except unit 3's: each failed its named test once (below).

## Checks run (real output)

| Command (worktree, PYTHONPATH = backend, contracts, simulator, tools) | Result |
|---|---|
| `pytest test_ds4_world.py test_ds4_batch_days.py test_ds3_bulk_load.py` at `9eff83776` | 95 passed in 5.5 s |
| `heavy-slot.sh --db -- pwsh run-host-tests.ps1 -- test_ds4_world_postgres.py -s` | 3 passed in 33.5 s (285 s wall, slot wait included; an earlier try gave up after 1200 s waiting: exit 75) |
| same, `test_ds4_batch_days_postgres.py` | 5 passed in 8.7 s |
| same, DS3 bulk-load and parity, `test_pg_harness`, 3A3, 3B4, 3B7a, ON1 postgres | 69 passed, 0 failed in 104.5 s |
| `test_ds3_bulk_load.py`; ON1, 3B4, 3A3, 3B7a no-DB tests | 29 passed; 188 passed (1 warning) |
| `check-architecture.ps1` (`ASSETOPS_GUARD_PYTHON` set) / `check-agent-workflow.ps1` | passed / passed |
| `select-tests.py --base main` | full mode (571 files: `tools/world.py`, the definition JSON); full suite not run (not scheduled) |
| fast `check-all.ps1` | see the closing line of this packet |

Databases: prefix `assetops_ds4t<hex>` and `assetops_wc5_pt<hex>_base_test`, all dropped by the module `finally`
(T13 asserts none left); harness `ds4g*` clones dropped. Keys and state: pytest temp dirs (0700). Nothing created
under `/opt/assetecon/keys` or `/opt/assetecon/worlds` (row 40 held).

## Plants (each alone, throwaway worktree, removed after)

P1 T2; P2 T6 (`WORLD_TEMPLATE_STALE`); P3 T6 (+T11 scan); P4 T6; P5 T5; P6 T4 (`walk1`); P9 T9 (C2); P10, P11, P19,
P21 T9 oracle; P12 T5; P13 T5; P14 T5 partial; P15 T3; P16 T1; P17 T9 (clone dropped on a raise); P18 T9 and T9b;
P20 T9b; P22, P23 T9 C5; P24, P25 T6 staleness; P26 T5 (`.key` in a manifest); P27 T5 (0755 accepted); P34 T9b;
P33 T9b, and T12 on Postgres (see the closing line). Cover rule: P7 T8 (a)(f)(g) and T15; P8 T15 (ledger counts
change); P28 T8 (d)(e) and T16b; P29 T8 (f); P30 T8 (g); P31 T8 (5 of 7 unreadable cases raise `ValueError`/
`AttributeError`; the naive-time cases still pass because the naive check stays); P32 T16c. Outputs:
`plants-world.out`, `plants-cover.md` in the evidence folder.

## Known deviations

- T8 lives in `test_ds4_batch_days.py` (pure), not `test_ds4_world.py`; same cases.
- §3.6 names the check block `derived_values_sha256`; §3.3 (D-DS4.21) names `check_inputs`. Built per §3.3.
- T6 "a new id for `tools/world.py` only gives `check_stale: code.tools/world.py` on `clone`": `tools/world.py` is
  also a key `code` part (§3.2), so `clone` refuses first with `WORLD_TEMPLATE_STALE code.tools/world.py`. The test
  shows the clone path with `backend/tests/pg_harness.py` (check code only) and `code.tools/world.py` through `list`.
- C4's detail is an object (`sites` counts, `fails` with `mark` new/known, `blanks`); the other checks' details are
  strings. The blank list holds every blank cell with its record, whatever its class (so the known cells appear).
- C6 reads the Site zone on the check clone with `SELECT timezone FROM site WHERE id = '<uuid>'` (added to T11's
  shapes); C6 is PASS `0 batches` today, so its parse path is exercised only by T8/T15-T17's functions.
- A check that raises becomes that check's FAIL (`raised <type>: <text>`); a refusal, step failure or cap still
  propagates, and the check clone is dropped in `finally` either way.
- `site_timezone` is not added to the `EvidenceLedger` Protocol (neither are `gateway_principal`, `bulk_admit`).
- Unit 1 carry-over: `reset` clones directly when no clone manifest exists; `list` recomputes `check_passed` live.

## Residual risk and review focus

- C4 is FAIL on the real world until 5a F1 merges; then remove the 12 lines and T12 expects PASS, exit 0.
- C5 in T12 is injected; the real parity file ran in the regression set. C5's real `pwsh` path runs in unit 3.
- Focus: `C4_CONTRACT` cell for cell against §2.1; `judge_side`'s union and `None` rule; `harness_run`'s env and
  drops; step 7a's place and the grain functions.

**Closing results.** Fast `check-all.ps1` at `9eff83776`: "All 40 guards passed (blocking; 0 advisory, 0 warned)",
121 s (580 s wall with slot wait). P33 on Postgres: T12 FAILED with three `new` C4 lines at KISIWA-001
(`actual.om`, `actual.cost_to_serve`, `actual.contribution`, `class=E product=None`); `plant-p33-t12.log`.

## Fix round r1 (review round 1: ACCEPT WITH FIXES)

Branch head after the round is in the commit log (`DS4 fix r1`); main merged first at `a8a30426a` (5a F1).

- **M1 fixed.** `site_set_fails` (tools/world.py) compares the Sites judged with the definition's Sites per
  snapshot of the tenant: FAIL lines `site_missing <slug>/<code>`, `site_duplicate <slug>/<code>`,
  `site_undeclared <slug>/<code>` (new FAIL line forms in §3.6; Architect to note). `_c4` passes the snapshot counts.
  Tests: `test_t9_c4_judges_exactly_the_declared_sites` (missing, duplicate, both, undeclared, two snapshots) and
  `test_t9_c4_site_set_through_the_command`.
- **M2 fixed.** `harness_run` builds from `world.env(None)` plus `HARNESS_ENV_ALLOW`; T9's C5 test plants
  `DATABASE_URL`, `ASSETOPS_TEST_DATABASE_BASE_URL`, `ASSETOPS_TENANT_SLUG`, `ASSETOPS_PSEUDONYM_KEY_DIR`, `LANG`,
  an unrelated variable and asserts the child's keys are exactly the allow-list.
- **F1 follow-up.** `C4_KNOWN_FINDINGS` is `()`; a test pins it empty. T12 on the merged branch: C4 PASS, `fails: []`,
  `ALL` PASS, exit 0 (see Checks).
- **L1** closing `{"check": "ALL", "state"}` line, asserted in T9. **L2** tests: `_equal` no tolerance, manifest
  staleness through `clone`. (c) (C6 gap report) stays covered by T8/T15-T17 only. **L3** `known` only when
  `product=None` (test). **L4** current-key manifest without its database is `WORLD_NO_TEMPLATE ... (database
  missing)`. **L5** a clone that stays in use after the wait is a coded `WORLD_DATABASE_IN_USE` (lines emitted, clone
  left for `drop`), not a traceback. **L6** not changed (spec asks no erase): unit 3 runbook line needed: a partial L1
  that failed after `onboard apply` leaves its tenant key file live until the coordinator removes the key directory.
- **Plants (throwaway worktree, removed):** M2 inherit-parent (`env = dict(world.environ)`) fails 1; M1 site check
  dropped fails 2; `_equal` 0.01 tolerance fails 1; `ALL` line dropped fails 2. Each reverted.
- **Checks (r1):** DS4 no-DB + DS3 bulk-load unit: 99 passed. T12-T17 via `heavy-slot.sh --db`: 8 passed in 42.2 s; T12 C1-C3, C5-C7 PASS, C4 PASS (`fails: []`), `ALL` PASS, exit 0. DS3 bulk_load/parity/pg_harness Postgres: 40 passed in 47.0 s. Fast check-all: "All 40 guards passed" (150 s).

## Unit 3: the re-benchmark and the real runs (after owner row 40)

Implementer (Claude), 2026-11-21. Main `c76111132` merged first (SC-1a guard; row 40 approval). Code commit
`58bb50809`: `tools/world.py` `bench` (`cmd_bench`, `assemble_bench`, `pipeline_line`, `bench_evidence_dir`,
`_bench_sweep`, `_late_record`, `_late_csv`; `cmd_build` split into `_build`), the new
`backend/tests/test_ds4_bench_pipeline_postgres.py` (B5), and T10 in `test_ds4_world.py`. The report uses codes
only (`PROJECTION_NOT_MEASUREMENT`, `WALL_ONE_RUN_THIS_VPS`, ...). It holds no hand-built English. `tools/world.py` is
outside the SC-1 ratchet. Evidence: `/opt/assetecon/evidence/DS4/unit3-2026-11-21/` (`bench.json`, `bench.out/err`,
`build.out/err`, `check.out/err`). Directories `/opt/assetecon/keys`, `/keys/world`, `/worlds`: 700, `deploy`,
made by the coordinator. The tool only passed their paths.

**Preconditions as found.** The machine was not idle. Both heavy slots and the DB slot were busy with other lanes,
so each run queued on `--db`. Load average at bench start was 6.98 / 6.04 / 4.97, recorded in `bench.json` `start`.
`tools/keep-awake-during-tests.ps1` was started and failed at once on Linux (`SetThreadExecutionState`
`MethodInvocationException`; it is a Windows sleep guard), so `keep-awake: not run (Windows-only)`. Caps were
`--cap-seconds 3600` for the bench (expected about 30 min; the 13 Nov 62 s per Site-day figure), and 600 for build
and for check. None was reached.

### The runs (in §6's order, each `tools/heavy-slot.sh --db --label ds4 --wait-seconds 3000`)

| Run | Exit | Wall (slot wait included) | Stdout |
|---|---|---|---|
| `world.py bench --key-root /opt/assetecon/keys/world --evidence /opt/assetecon/evidence/DS4/unit3-2026-11-21 --cap-seconds 3600` | 0 | 2,688 s (the run itself about 6 min, 15:45 to 15:51Z) | report path and `ds7` |
| `world.py build --key-root /opt/assetecon/keys/world --cap-seconds 600` | 0 | 36 s | three rungs, `reused: false` |
| `world.py check --cap-seconds 600` | 0 | 620 s | C1-C7 and `ALL` PASS |

### Bench figures (`bench.json`, `assetops.world-bench/1`), with §4's meaning

Every figure here is the wall clock of one run on this VPS, with subprocess start-up and Python imports included and
`synchronous_commit` at the server default. Each is one sample, not a distribution, so differences under 10 in 100
are noise. The figures describe this world: one tenant, three Sites, one month, no telemetry. L1 and L2 here are not
the strategy's full world. The machine was loaded, as stated above.

| # | Figure | Meaning |
|---|---|---|
| B1 L0 | 4.37 s total (`L0.migrate` 3.92 s); 18,264,547 bytes | create + `alembic upgrade head` + census + freeze |
| B1 L1 | 7.38 s total; steps: digest 0.29, check 1.29, apply 2.44, `load_world_inputs` 2.63 s; 19,395,043 bytes | onboarding one tenant and its October commercial inputs (no telemetry) |
| B1 L2 | 8.89 s total; snapshot build 4.51 s, observe 3.73 s; 19,747,299 bytes | one tenant × one month of the product's L2 steps on a telemetry-free world |
| B2 | clones `b1` 0.272 s, `b2` 0.242 s, `b3` 0.280 s; each 19,747,299 bytes; dropped | `CREATE DATABASE ... TEMPLATE ... STRATEGY FILE_COPY` wall seconds, the 5 s idle wait included |
| B3 | 9.75 s in total: load 1.87 s (`ACCEPTED`, `revised: 1`), snapshot 4.35 s, observe 3.53 s; `revenue_delta` **10.00** (expected 10.00, `AS_EXPECTED`); clone `bl` dropped | a one-row late billing revision (`KOBO-001`, `Revision` 2, `Amount` 86.80 to 96.80) end to end on a clone |
| B4 | `option_change` `NOT_BUILT` (6a); `contract_term_edit` `NOT_BUILT` (9a0) | these change kinds do not exist yet |
| B5 | exit 0 ("1 passed ... in 284.49s"); 14 Site-days, 70 batches, 6,720 envelopes; load 33.99 s; 13 ticks, 240.19 s of tick wall time; drain verdict **`fail`**, "past 2N: 13 ticks with N=6"; stage ms summed: chain_snapshots 61,146, mini 19,904, s3 19,896, fuel_night 14,660, s4 13,752, chain_threads 13,449, opportunity 13,403, ev_assess 12,729, cold_assess 12,633, ev_consequence 12,227, cold_consequence 11,070, consequence 10,856 | the flat fixture Kobo (hand rows, not the world's physics). The stage split shows where time goes; the total gives the per-Site-day figure |
| B6 | `per_site_day_seconds` 19.585 = (33.992 + 240.192) / 14; `projected_l2_seconds` 10,760.821 = 8.891 + 19.585 × 9 × 61 | **a projection, arithmetic on a measurement, not a measurement** (`kind: PROJECTION_NOT_MEASUREMENT`) |

Strategy §4 targets in the report: inputs "under 1 min" against L1 7.38 s; L2 "under 45 min" against 8.89 s
measured and 10,760.8 s projected; a run's database "under 10 s" against B2's worst, 0.28 s; a one-option change
"about 2 min" `NOT_BUILT` (6a); advance one day "under 1 min" `NOT_BUILT` (DS6). Every bench database was dropped
(`dropped.after`: the three bench rungs; clones `b1`-`b3` and `bl` were dropped in their own `finally`;
`dropped.before`: none).

**The `ds7` block (D-DS4.12; owner row 35):**

```json
{"threshold_seconds": 2700, "measured_l2_seconds": 8.891, "projected_l2_seconds": 10760.821, "triggered": true,
 "basis": "manifest time_scales.sparse_operational_context span 2026-09-01..2026-10-31; nine Sites"}
```

Read on the projection, DS7 is triggered: about 3.0 h projected against 45 min. Read literally on B1's L2 (8.9 s),
it is not. This is the owner's call (row 35).

### The kept ladder (`assetops_world`, built at `58bb50809`; manifests in `/opt/assetecon/worlds/manifests/`)

| Rung | Database | Key | `size_bytes` |
|---|---|---|---|
| L0 | `assetops_world_audit_l0_35467c68d361` | `35467c68d361e0d4a04560f7829ffe4fd3f5109f41f5f7502f6fed061caa39ab` | 18,264,547 |
| L1 | `assetops_world_audit_l1_5d26f14268f5` | `5d26f14268f5c9fa07bb6abb493326fc7052ae6ee14d2cda85374f209e84b28a` | 19,395,043 |
| L2 | `assetops_world_audit_l2_ca818e745fd9` | `ca818e745fd9084265e50185d53c14d9f6fa49da1fa6e30aa598eca3fbcbab8f` | 19,747,299 |

The keys equal the bench's keys (same commit, same inputs). `key_dir` is
`/opt/assetecon/keys/world/assetops_world_audit_l1_5d26f14268f5` (path only). `world list` reports L2
`check_passed: true`, `check_stale: null`.

### The check's lines (`world check`, exit 0)

```
C1 PASS "5 files"
C2 PASS "136 tables"
C3 PASS "1 snapshots match"
C4 PASS fails [] ; 123 blanks listed; E/B per side: KISIWA-001 actual 15/32, plan 36/11; KOBO-001 actual 18/29, plan 36/11; MTO-001 actual 18/29, plan 36/11
C5 PASS "exit 0 ... 3 passed, 2 warnings in 39.21s"   (the real pwsh path, under its own assetops_wc5_pt<hex>_base_test)
C6 PASS "0 batches (telemetry none)"
C7 PASS "7 steps"
ALL PASS
```

### Clones made and dropped

- Bench: the ladder `assetops_worldbench_audit_l0_35467c68d361`, `_l1_5d26f14268f5`, `_l2_ca818e745fd9`, and the
  clones `assetops_worldbench_audit_c_b1`, `_c_b2`, `_c_b3` and `_c_bl`. All were dropped. The bench L1's tenant key
  was erased by `drop`. Its key directory `/opt/assetecon/keys/world/assetops_worldbench_audit_l1_5d26f14268f5`
  stays for the coordinator (D-DS4.19).
- B5: the base `assetops_wb5_pt<hex>_base_test` and the harness clones under it (`ds4pseed`, `ds4ppipe` and the run
  template). All were dropped by the harness and `harness_run`.
- Check: `assetops_world_audit_c_check`, plus C5's `assetops_wc5_pt<hex>_base_test` and its harness clones. All
  were dropped.
- After the runs, `pg_database` holds only the three kept `assetops_world_audit_*` rungs among `assetops_world%`,
  `assetops_wb5%`, `assetops_wc5%` and `%ds4p%`. No walk, serve or `assetops_op*` database was touched, and nothing
  was served or copied (row 36 held).

### Checks (unit 3)

- `test_ds4_world.py` + `test_ds4_batch_days.py` (no DB): 75 passed. T10 has four tests: the projection and `ds7`
  above and below 2700 s; no pipeline line, no projection; evidence in the repository refused (exit 2,
  `WORLD_EVIDENCE_IN_REPO`); the late-record file.
- Plants (each alone, reverted with `git checkout`): the projection without `/ site_days` failed T10 twice. Dropping
  the `contract_term_edit` `NOT_BUILT` row failed T10 twice.
- Fast check-all at `088e93f9d`: "All 42 guards passed (blocking; 0 advisory, 0 warned)", 123.5 s (1,052 s wall with slot wait); `check-all-fast.log`.

### Mid-build count, deviations, residual risk

- Mid-build count for unit 3: **0**. The total for DS4 stays 1 (MBQ-1).
- Known deviations:
  - The bench command did not exist when unit 3 was dispatched. It was built here as §6 unit 3 lists it.
  - The bench default prefix: `world bench` uses `assetops_worldbench` when `--prefix` is left at its default.
  - `start.slot` records the first line of `heavy-slot.sh --status` (slot-1, ours), not the DB lock line.
  - The bench's drop lines are not copied into the report, so the bench L1's `keys_left` is not recorded; `drop` erased each tenant key as in T13.
- Residual risk:
  - **B5's drain did not settle.** The verdict was `fail` (past 2N, 13 ticks, N=6) on the fixture slice. It is
    reported, not hidden, and it goes to the Architect. The per-Site-day figure therefore covers 13 ticks of a pipeline
    that had not drained, so it is a lower bound on the real drain cost.
  - The machine was loaded (load 5-7, other lanes in the slots), so every figure includes that contention.
  - The projection assumes the per-Site-day cost is linear in Sites × days and the same for every Site type. It is
    arithmetic only, to be replaced by `world bench` at the first world telemetry (D-DS4.11 reverse).
  - The kept ladder is keyed to `58bb50809`. Any later change to the code paths makes it stale, and `clone` then
    refuses with `WORLD_TEMPLATE_STALE`. WK rebuilds with `world build` (about 20 s).
- `USER_REVIEW_REQUIRED: false` for the tool. DS7's trigger (row 35) and serving (row 36) are the owner's, as before.
