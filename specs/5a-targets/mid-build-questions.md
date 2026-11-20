# 5a mid-build questions (RULES §4 item 7)

A question about something the spec did not fix stops only the affected part. Write it here (Q1, Q2 ...): the
unit, the section, what is stopped, what is built, and what you ask. The Architect rules in `rulings.md`. Record
the count in the packet; a count above zero is a spec-template defect to fix.

Count: **3** (reset at spec rev 2, after handshake round 1; Q2 and Q3 raised in units 2-3).

## Q1 (unit 1, spec §6 test 10): DS1b parity cannot live in `backend/tests`: ANSWERED

**Answered** 2026-11-20 in `rulings.md` "Mid-build answers (round 1)": builder's default confirmed
(simulator-side test reading the fixture by path; guard unchanged), with its assertions and plants.

- **Stopped:** test 10 only. **Built:** tests 1 and 2, `lines.py`, the fixture (its step 1 was produced from DS1b's
  `build_records` output for the October `plan` records and matches §5's values).
- **Why:** test 10 calls `build_records(view, generate_history(view))`. From `backend/tests/test_5a_targets.py` that
  is `from assetops_simulator...`, which `tools/checks/dependency-direction.ps1` (product-to-simulator) refuses for
  every file under `backend/`, tests included, with no allowlist. check-all failed on it at the first run. DS1b's
  golden (`simulator/tests/world/golden/records_v1.json`) holds digests only, so no file read can stand in.
- **Ask:** where the parity test lives. Builder's suggested default, not applied: a new
  `simulator/tests/world/test_5a_fixture_parity.py` that reads `backend/tests/fixtures/targets_lakeside.json` by path
  (a file read, no import across the seam) and compares step 1's parsed records with `build_records` for those IDs.
  This adds a file outside spec §7 question 8's list, so it needs the ruling.

## Q2 (units 2-3, spec §5 step 1 and §6 "Postgres" test 1): `loader:ds3` cannot be stored in Postgres: ANSWERED

**Answered** 2026-11-20 in `rulings.md` "Mid-build answers (round 2)": the literal becomes `service:ds3-loader` in
the fixture, both test files and spec §5; the Postgres workaround (`PG_LOADER`) is removed.

- **Stopped:** nothing in the in-memory file (it keeps the literal). **Built, as a workaround:** the Postgres file
  enters step 1 as `service:ds3-loader` (`PG_LOADER`, `test_5a_targets_postgres.py`) and passes that name to test
  1(a)'s check; tests 1, 3 and 6 and the composition test then pass on Postgres (4 passed).
- **Why:** migration `0063_commercial_records.py:51` checks `entered_by ~ '^(service:[a-z][a-z0-9-]{0,62}|person:[0-9a-f-]{36})$'`
  (`StoreRefused: commercial_intake_entered_by_check`); the in-memory store accepts `loader:ds3`, so the spec's fixture
  names a declarer production cannot hold.
- **Ask:** change the fixture's step-1 `entered_by` (and §5's `declared_by` literal) to a `service:` name, e.g.
  `service:ds3-loader`, so one literal serves both stores and the workaround goes; or keep it with the workaround.
  Touches unit 1's fixture, its parity test (which reads only records, so stays green) and test 1's literals.

## Q3 (units 2-3, spec §3.2 steps 3 and 5; D-4B.18): which origins an assumed target carries: ANSWERED

**Answered** 2026-11-20 in `rulings.md` "Mid-build answers (round 2)" (D-5A.16): the builder's default is
confirmed, `currency=` keyword included; spec §3.1 and §3.2 rev 3 name it.

- **Stopped:** nothing; the evaluator refuses a valued, non-NEUTRAL, non-CALENDAR leaf with `()` origins
  (`STRUCTURE_ORIGIN`), and spec §3.2 (written before D-4B.18) names origins only for a line's target, so no
  assumption could be built without a choice. The coordinator's brief says: assumptions carry origins, unknown weakest.
- **Builder's default (applied, pinned by `test_3a_origins_of_assumptions`):** `LEAK_ZERO` carries `("unknown",)` (it
  rests on no record); `AT_ACTUAL` carries the actual's origins (`("unknown",)` if ever empty); a solved `MAIN` leaf
  carries its heading line's origins united with the other targets under that heading (Kobo `necessary_l`:
  `("source-emulated", "unknown")`); `solve_main`'s probe carries `("unknown",)` (it never reaches the result) and
  gains a keyword-only `currency=` (spec: "the heading currency if the leaf is money", which the positional
  signature cannot reach). Stated headings keep their line's origin, so Kobo `contribution` stays
  `("source-emulated",)` as §5 expects.
- **Ask:** confirm, or name another rule (the alternative for `MAIN` is `("unknown",)`, the more conservative label).
