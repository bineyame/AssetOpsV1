# 3A4 review, round 1 (discovery, W5)

Fresh Reviewer (Claude), 2026-11-20. Branch `task/3A4-amounts-by-month`, head `1f90ba7eb`, base `38e2b3fe1`
(after 3B3; `main` has since moved only by DS1m, nothing under `commercial/`). Read only; worktree
`/opt/assetecon/AssetOpsV1-3a4`. Against `spec.md` rev 2, `rulings.md` D-3A4.1-11 and the handshake answers,
`reviewer-guide.md` rev 2, `packet.md`.

## Summary

**Verdict: ACCEPT.** No High or Medium finding. Two Low findings, neither blocking.
- The honesty rules hold in the code and in the tests:
  - currency, unit, provenance and basis are all in the line key, and nothing is converted;
  - budget lines are listed, and a duplicate gives `None` plus `DUPLICATE_DECLARATION`;
  - a heading with no record has no line, and a recorded zero shows as `0.00`;
  - "latest" is picked inside the `DISTINCT ON` subquery, after the `known_at` cutoff and before the filters;
  - `closed` is judged as `(known_at or clock()) >= hi`, with instants compared as datetimes, never text;
  - the stamp digest is the spec formula, pinned literally.
- Reruns all green: the no-database file plus 3A1 service (50), the Postgres file plus regression (39 via `--db`), my three plants (each fails one named test), the P3 probes, the architecture guard and the agent-workflow guard.
- Plant V7 has no digest form. That is acceptable: see "V7" below.

## Findings

- **L1 (Low, test gap; preference, not an acceptance gap).** `backend/tests/test_3a4_commercial_months.py:208-221`.
  - What the test shows: after step E, `stale([S10, S11]) == (S10,)`. But E both corrects `KOBO-EX-FUEL-1028` and adds `KOBO-EX-OM-1029`, so the new record alone makes October stale.
  - The gap: no behaviour test shows that a correction in place, with the same month and the same record set, makes the stamp stale. My plant P-B (digest over `record_id` only) passed every behaviour test. Only `test_02_the_digest_is_the_spec_formula` caught it, by recomputing the formula literally.
  - Why it matters: 3B7a relies on exactly this property.
  - Fix: one assertion that a stamp taken between a lone correction and its predecessor goes stale. For example, ingest a v2 of a single October record with no other change, and assert `stale([S]) == (S,)`.
- **L2 (Low, residual efficiency).** `backend/assetops_backend/commercial/months.py:246-258`.
  - For each stamp, `stale` calls `site_zones` again and reads the Site's full latest-revision set (every month), so the cost is O(stamps x Site history).
  - Correct, and fine at pilot volume.
  - 3B7a should batch its stamps per Site, or this method should group stamps by Site before reading.

Nit, not a finding: `postgres_commercial_store.py:65` has a 204-character comment line. No lint config enforces a
limit.

## Hunted honesty breaches (each checked, none found)

- **Money summed across currency, unit or provenance.**
  - The key is `(kind, dims, measure, currency, unit, provenance, basis)` (`months.py:164`).
  - AMOUNT lines have `unit = None` and QUANTITY lines `currency = None` (`months.py:142-145`). Test 1 asserts both slots on every line.
  - Tests 4 and 5 cover currency and provenance.
  - My plant P-A (currency forced into one key) fails test 4.
- **Budget lines summed.** DECLARED lines are never added (`months.py:170-172`), and test 8 covers it.
- **A heading shown as 0 with no record.**
  - Lines exist only for groups that have parts, and only parsed measures that are present make a line: a FIXED charge has no QUANTITY line, an ADJUSTMENT with only a quantity has no AMOUNT line.
  - Test 7 covers the empty month and the FUEL-only month.
  - A recorded zero is normalised with `copy_abs` (test 6).
- **Latest revision chosen wrongly.**
  - In the adapter's `_LATEST`, the cutoff is in the inner `WHERE` and the site, kind and period filters are outer. The in-memory twin follows the same order.
  - `test_pg_02` compares Postgres with memory at every step's instant and 1 µs before it, across 5 filter sets.
  - `test_pg_03` holds D-3A1.8.
- **Month assignment.**
  - `recognition_period` wins. Otherwise a SETTLEMENT is placed by `settled_at` in the Site's zone, and the portfolio uses UTC.
  - 2a requires `recognition_period` on every other money kind (`records_v1.py:160-211`), so no money record goes unplaced.
  - My plant P-C (settled_at before recognition_period) fails test 3.
  - `month_bounds` matches `month_window` across 3 zones and 12 months (test 10).
- **"Closed" judged at known_at.** `months.py:225-227`. Test 2 covers it: the 31 Oct 20:00 UTC read is open and empty.
- **Stamps 3B7a can rely on.**
  - The digest covers only the placed money revisions, plus `head`. It is computed from the same `latest_revisions` result that builds the lines, so a stamp always matches the figures it accompanies.
  - Non-money kinds do not move it (test 9).
  - A move out alone makes the month stale: after F, October changes only by losing `KOBO-CH-0004`, and `stale` says `S10e`.
  - `months_touched` includes the month that was left (F gives Oct and Nov).
  - One gap: the in-place correction behaviour test is missing (L1).

## V7 (no digest plant)

The digest is recomputed from current placement and never from an intake, so "the digest from the intake's new
revision IDs only" has no natural form here. What V7 guards is still guarded:
- after F, `stale` must flag `S10e`, and the only change to October in F is a record moving out;
- `months_touched(F)` must name October (the builder's V7 variant fails it there).

Accepted as a plant re-aimed at the same property.

## P3 probes

- **Two statements.** `intake_revisions` runs exactly two `execute` calls on one connection: the intake's revisions, then the superseded ones by ID. The second is skipped when nothing is superseded.
- **One parse.** I counted `parse_record` calls in the scratch copy. October after F: 14 parses for 14 placed records, each parsed once. November: 2. `stale`: 0. Revisions of other months are filtered by columns before any parse.

## Checks run (by me, at `1f90ba7eb`)

- Module paths: `assetops_backend.commercial.months`, `assetops_contracts` and `test_3a1_commercial_service` all resolve under `/opt/assetecon/AssetOpsV1-3a4/...`. `PYTHONPATH` was the worktree's backend, backend/tests, contracts and simulator; the interpreter was `/opt/assetecon/AssetOpsV1/.venv/bin/python`, because the worktree has no `.venv`.
- `heavy-slot.sh -- pytest test_3a4_commercial_months.py test_3a1_commercial_service.py -q`: **50 passed**, 0.86 s.
- `heavy-slot.sh --db -- pytest test_3a4_commercial_months_postgres.py test_3a1_commercial_postgres.py test_pg_harness.py -q`: **39 passed**, 9 Alembic deprecation warnings, 12.8 s. The base was `assetops_test` at 127.0.0.1:55432, routed by the harness to a run-owned `*_test` clone. No skips.
- Plants, run in a unique scratch copy (`git archive HEAD`) at `scratchpad/rev3a4r1-plants-1751547`, each reverted after its run:
  - P-A: currency left out of the key. `test_04` fails.
  - P-B: digest over `record_id` only. Only `test_02_the_digest_is_the_spec_formula` fails (hence L1).
  - P-C: `settled_at` placement put before `recognition_period`. `test_03` fails.
- `check-architecture.ps1`: passed once `ASSETOPS_GUARD_PYTHON` was set. The first run without it could not start the chain-structure guard, because the worktree has no `.venv`; that is environmental.
- `check-agent-workflow.ps1`: passed.
- Not rerun:
  - fast check-all (the coordinator is rerunning it with `node_modules` linked);
  - the builder's V1-V12 plants (I cite the packet);
  - the full suite (`select-tests` says full, because of the new fixture JSON; the coordinator schedules it).

## Scope

- The diff matches spec §7 question 8: store port, adapter (3 reads plus the `_LATEST` clause), `months.py`, composition, the fixture, 2 test files, plus packet, state, index and spec status.
- Nothing under `structure/` changed; `commercial/**` has no structure import (test 12).
- No migration.
- `_scrubbed` is correctly left off: 3A2 is not on `main`, so 3A2 decorates these reads when it merges (D-3A2.16).

## Residual risk (not named in the packet)

- `known_at` naive datetimes: the memory store raises `TypeError`, while Postgres casts the value in the session time zone. Callers must pass aware instants. Nothing guards this.
- `site_month` reads `site_zones` and `latest_revisions` on two connections. The lines and the stamp both come from the one `latest_revisions` result, so they stay consistent; only the zone could differ, and only if a Site were re-zoned mid-call (Sites are not re-zoned today).
- Commit 1 does not collect on its own, because its Postgres file imports the no-database file added in commit 2 (named in the packet). This only matters for bisect.
- 3A2's merge must keep these three reads and decorate them, then run 3A2's service test 21 (as the guide says).
