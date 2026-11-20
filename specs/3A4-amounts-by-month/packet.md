# 3A4 packet: amounts by month

Implementer (Claude Opus, fresh), 2026-11-20. Branch `task/3A4-amounts-by-month`, worktree `/opt/assetecon/AssetOpsV1-3a4`,
base main `38e2b3fe1` (after 3B3). Spec rev 2, rulings D-3A4.1-11. **Mid-build questions: 0.** User review: not required
(non-screen; discovery review per W5).

## Commits
- `75ad31e87` unit 1: store reads (`known_at`, `intake_revisions`, `site_zones`), fixture, Postgres tests.
- `014e5536c` unit 2: `commercial/months.py`, `build_commercial_months`, no-database tests.
- `c7ee5e215` unit 1 fix: an edit had split `_INSERT_INTAKE` (collection error, caught by the first Postgres run).
- last commit: packet, spec status, state entry.

## Module paths (PYTHONPATH = worktree backend, backend/tests, contracts, simulator, gateway, field, host, tools)
`assetops_backend` -> `/opt/assetecon/AssetOpsV1-3a4/backend/assetops_backend/__init__.py`;
`assetops_contracts` -> `/opt/assetecon/AssetOpsV1-3a4/contracts/assetops_contracts/__init__.py`;
`fixtures.__file__` None (namespace package).

## Done (spec §7)
| # | Answer | Evidence |
|---|---|---|
| 1 exact, apart by currency/unit/origin/basis | yes | tests 1, 4, 5, 6 (31-digit sum), 3 |
| 2 move counts once, late counts in own month | yes | tests 1, 2 (CH-0004 in Nov, OM-1029 in Oct) |
| 3 no record no line; recorded 0 shown | yes | tests 7, 6 |
| 4 budget listed, duplicate has no value | yes | test 8 |
| 5 settlement in Site-local month | yes | test 3 (ST-1031 in Nov) |
| 6 stamps stale exactly; months_touched per step | yes | test 2 (stamps, A-F touched), test 9 |
| 7 `known_at` incl. `closed` | yes | test 2 (5 Nov; 31 Oct 20:00 open, empty) |
| 8 diff scope | yes | store, months, composition, adapter (3 reads + `_LATEST` clause), fixture, 2 tests, packet/state/index |

## Tests (rev `c7ee5e215`)
- `pytest backend/tests/test_3a4_commercial_months.py backend/tests/test_3a1_commercial_service.py -q`: 50 passed, 0.9 s.
- `ASSETOPS_TEST_DATABASE_URL=...assetops_test tools/heavy-slot.sh --db -- pytest test_3a4_commercial_months_postgres.py
  test_3a1_commercial_postgres.py test_pg_harness.py -q`: 39 passed, 9 warnings, 14.6 s (16 s wall).
- `tools/select-tests.py --base main`: `mode: full (527 of 527)`, because of the new fixture JSON. Full suite not run
  (coordinator schedules it).
- `pwsh tools/check-all.ps1` (fast, rev `c7ee5e215`): 38 of 40 pass (architecture seams 14/14, agent workflow, configuration-persistence included), 323 s wall (244 s slot wait). **2 FAIL, environmental:** "Missing-claim orphan scan" and its fixtures, `MODULE_NOT_FOUND` for `typescript` (fresh worktree has no `frontend/node_modules`; no frontend file changed). Not rerun with node_modules.

## Plants (each applied, run, reverted with `git checkout`)
V1 -> pg test 3 fails. V2 adapter -> `test_pg_01_known_at`, `test_pg_02_known_at_matches_memory` fail; V2 in
`MonthsMemoryStore` -> no-db test 2 (`known_at`) fails. V3 float -> tests 6 and 12. V4 -> 5. V5 -> 7. V6 -> 3. V7 -> 2.
V8 -> 8. V9 default context -> 6 (`1000000000000.000000000001000` != `...001000001`). V10 -> 1. V11 -> 3. V12 -> 2
(the 31 Oct 20:00 read).

## Not verified / notes
- V7 planted as "`months_touched` ignores the superseded revision's month"; it fails test 2 at `months_touched` for F.
  A digest variant that ignores moves out was not planted (the digest is recomputed from current placement, so no
  natural plant exists); `stale` after F is asserted in the same test.
- "At most two statements" and "one parse per placed revision" are review probes (P3), not tested.
- `_scrubbed` (D-3A2.16) not applied: 3A2 is not on `main`; 3A2 decorates the three reads at its merge.
- Commit 1's Postgres file imports the no-database file added in commit 2 (bisect between them fails to collect).
