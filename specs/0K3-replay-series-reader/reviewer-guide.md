# 0K3 reviewer guide

Architect (Claude), 2026-11-21, rev 1. Discovery review (W5): a new mechanism on the evidence seam whose series feed
a litre figure. Read `spec.md`, `rulings.md`, then the diff. Done means every question of spec §6 answers yes with
evidence and every plant below fails its named test.

## What to check, and how

1. **Independent expected values (W2).** B1 and G1 compare with literal tuples written in the test; T1 compares with
   0K2's `observed_series`, never with a `replay_series.py` helper. The S8 writer spells its addresses and quanta in
   the test. A test whose expected value comes from the reader's own code is High.
2. **Nothing invented.** Read `series_from_readings`: means are averaged only inside one step and only when they tile
   it; no value moves between steps, roles or assets; no carry-forward; no tolerance on instants (D-0K3.2, D-0K3.3).
   A fill, a spread or a substitution (`pv_power` for `pv_available_power`, requested for delivered) is High.
3. **Refusal order.** §2.2 against the code: no query before the Site; bindings before the cohort; the first failing
   reading in the stated sort order. B10's two-fault case.
4. **Exactness.** `Fraction` from the decimal text, never `float(`; the tiling weights are exact seconds.
5. **Labels.** `input_class` from source mode only (D-0K3.6); `load_role` on every read.
6. **Seam.** `git diff main...HEAD --stat` lists spec §0's files; the allow-list grows by exactly two names;
   `replay_study.py`, `forward_replay.py` and `host/forward_replay.py` are unchanged.
7. **Databases.** The Postgres file uses only `pg_harness` clones named `*_test`, each dropped in `finally`.
8. **Packet.** The refusal table, G1's totals beside R0's, and the "waits for" list are present; nothing claims a
   study ran on stored readings.

## Plants (each on a scratch copy; each must fail the named test)

| # | Plant | Fails |
|---|---|---|
| P1 | a 15-minute mean is split into three steps instead of refused | B3, G2 |
| P2 | a step with a missing minute takes the mean of the present minutes | B2 |
| P3 | an SOC instant at `t_k + 2 min` is read as step `k` | B6 |
| P4 | `PV` falls back to `pv_power` when `pv_available_power` is unbound | B7, G4 |
| P5 | bindings are checked after the cohort | B10 |
| P6 | `input_class` hard-coded `"SIMULATED"` | B8 |
| P7 | `generator_kwh = gen_kw` (no 5/60) | B1, T1 |
| P8 | loads ordered by asset id instead of code | B1 |
| P9 | the second of two SOC instants at one `t_k` silently wins | B4 |
| P10 | a non-GOOD reading's bad unit refuses | B5 |
| P11 | `start_fuel_l` taken from the first fuel reading at any step | B9 |
| P12 | `Fraction(float(value))` | B2 (1-minute values with decimals), B12 |
