# DS4 review packet: units 1 and 2 (unit 3 held for row 40)

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
