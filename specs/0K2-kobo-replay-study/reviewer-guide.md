# 0K2 reviewer guide

Architect (Claude), 2026-11-21, rev 1. Discovery review (W5): a new mechanism whose litres feed a money figure. Read
`spec.md`, `rulings.md`, then the diff. Done means every question of spec §6 answers yes with evidence and every plant
below fails its named test.

## What to check, and how

1. **Independent expected values (W2).** T1 to T6 compare the study with values the host test reads itself from the
   site trajectory and the projections (dawn by fixed offset, months by offset, its own start and throughput loops).
   A test that computes its expected values by calling a `replay_study.py` helper is High.
2. **Nothing modelled in the study.** Read `runs/replay_study.py`: its only arithmetic is sums, differences, the
   tolerance comparisons, the SOC-drop throughput and local-time framing. A price, SFC, start threshold, reserve rule,
   inverter law or gap fill in it is High (D-0K2.10, D-0K2.12).
3. **Whole-window replays only.** T7 and B12: `1 + len(grid)` calls when calibrated, one when not, none on a short
   sample; every request of `n` steps (D-0K2.4).
4. **Order of checks.** §2.2 steps 1 to 8 against the code; B7's two-fault case; refusals raised before any later
   port call.
5. **The fixture.** `kobo_season.py` against spec §3: every value from the named shipped file or `NIGHT_WINDOWS`;
   the calendar `d % 4 == 3`; the publication quanta; loads in reverse sorted order; no import of
   `host/forward_replay.py`.
6. **Seam.** `git diff main...HEAD --stat` lists spec §0's five new files and the one edited test; the seam test's
   allow-list grows by exactly two names; the packet shows the guard failing on the scratch copy.
7. **Exactness.** No `float(` and no `round(` on a value in `replay_study.py`; the fixture's rounding is on
   `Fraction`s (half-even).
8. **Labels.** `input_class` and `evidence_class` on every result; nothing served; no design value or label edited
   anywhere in the diff (D-0K2.13).
9. **Packet.** The 61-day table beside the design values, the calibration figures, run count and wall time.

## Planted violations (each must fail the named test; the builder shows each failing once, in a scratch copy)

| # | Plant | Fails |
|---|---|---|
| P1 | tolerance taken relative to the replayed side | B1 (obs 100, rep 95 must pass) |
| P2 | calibration over all days, not admissible ones | B2 |
| P3 | the dawn step taken at 05:00 UTC | B3, T3 |
| P4 | months by UTC date | B4 (the 31 Aug 21:00Z hours) |
| P5 | throughput counting charge as well as discharge | B5, T3 |
| P6 | starts counted as RUNNING steps | B6, T1 |
| P7 | one replay per day | T7, B12 |
| P8 | the fixture's quantization dropped | T1 precondition |
| P9 | avoided litres as case minus baseline | B4 (`Σ == avoided_l` sign), T3 |
| P10 | the grid replayed without its settings (`ReplaySettings()` for every case) | T2 (`stop_source`), T3 (`stop-70` avoided ≠ 0) |
| P11 | the sample checked after the baseline replay | B7 and T5 (zero port calls) |
| P12 | the grid replayed after a failed calibration | T4, B12 (one call) |
| P13 | a dawn verdict under 61 days | T6 |
| P14 | the tank bound not checked | B9, T9 |
| P15 | `MIN_DAWN_DAYS = 60` | T8 |
| P16 | `replay_study.py` imports `host.forward_replay` | B12, dependency-direction guard |
| P17 | a `None` PV value replaced by the previous value before the port | T10 |
| P18 | a clipped day excluded from the admissible days | T1 (every day admissible) |
| P19 | `ForwardReplayRefused` caught and re-raised as `StudyRefused` | B8 |
| P20 | the (90, 30) case named `baseline` or skipped | T2 |

## Not findings

No money, no price, no option choice, no CANDIDATE share computed (spec §7, D-0K2.12). No reader from accepted
readings (D-0K2.1, `0K3`). No gap fill (D-0K2.6). No zone with a clock change (D-0K2.7). The dawn bound failing under
no action is a result, not a defect (D-0K2.8). Throughput excludes PCS losses (D-0K2.11). Design values unchanged
(D-0K2.13).
