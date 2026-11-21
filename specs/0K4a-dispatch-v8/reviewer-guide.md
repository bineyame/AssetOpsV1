# 0K4a reviewer guide

Architect (Claude), 2026-11-21, rev 1. Discovery review (W5): a new dispatch mechanism in the simulator. Read
`spec.md`, `specs/0K4-dispatch-model-review/rulings.md` (D-0K4.2 to D-0K4.6) and `review-for-owner.md` §2-§3, then the
diff. Done means every question of spec §5 answers yes with evidence and every plant below fails its named test.

## What to check, and how

1. **Is it a real controller?** Read `cycle_charge_split` against D-0K4.3 and review §2 points 1-4. Ask what an
   operator's engineer would see on N1's per-step table in the packet: the generator starts at 35 %, the battery
   charges at up to the PCS limit, nothing discharges beside the generator, and the generator stops at the stop setting
   after its minimum run. Anything else is High.
2. **Expected values are independent (W2).** S1-S7 are literals; N1-N8 read the trajectory with the test's own reader.
   A kernel test that calls `cycle_charge_split` or `generator_curve` to get its expected value is High.
3. **v1-v7 untouched.** The §2.1 extraction is behaviour-neutral: read each `_add_vN_measures` against the `main` body
   of `resolve_vN`; N9's digest equals the pre-flight value; `git diff main...HEAD` shows no change in v1-v7's
   arithmetic, strings or ordering.
4. **Only the named lines changed.** Diff `_resolve_cycle` against `resolve` (631-910): the eight changes of §2.4 and
   nothing else. An unnamed change is a mid-build question that should have been asked (count it).
5. **The kernel's balances.** The new `generator-fuel` balance and the fuel stock account at `DIESEL_ENERGY_KWH_PER_L`;
   N8 COMPLETED. No balance identity weakened or removed.
6. **No tuning.** N3 and N5 preconditions are asserted, not arranged: the fixture is 0K2's season with a declared
   overcast day; no threshold, reserve or start charge moved to make a test pass.
7. **Seams.** No edit under `config/`, `contracts/`, `runs/replay_study.py` or guards; `REPLAY_MODELS` gains one tuple;
   the backend profile adds `GENERATOR_CURVE_NEEDS` and the three foundation needs only.
8. **Labels.** The packet's dawn pair (v7 and v8) is headed as a model-change reconciliation, both SIMULATED; no design
   value appears.

## Plants (each must fail the named test; revert after)

| # | Plant | Must fail |
|---|---|---|
| P1 | `decide_v8` does not reorder (v7's battery-first request) | N2, N3 |
| P2 | `pv_to_load = u` instead of `min(u, D)` | S4, S8 |
| P3 | the battery discharge cap ignored in support | S1, N4 |
| P4 | `max(M, ...)` dropped (no minimum load) | S4, N5 |
| P5 | `D + C` cap dropped from `g` | S5 |
| P6 | the taper applied only while the generator runs | N6b |
| P7 | fuel burned as v7's `sfc x energy` | N8 |
| P8 | STARTING burns nothing | N8 |
| P9 | `_add_v3_measures` swaps the PV available and discharge capability order | N9 |
| P10 | `REPLAY_MODELS` without v8 | N11 |
| P11 | stop rule ignores the minimum runtime | N7 |

## What counts as done

All of spec §5 yes; plants P1-P11 each fail their test; check-all (fast) green; mid-build count 0 in the packet.
