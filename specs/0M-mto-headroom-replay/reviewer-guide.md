# 0M reviewer guide

Architect (Claude), 2026-11-21, rev 1. Discovery review (W5): a new mechanism whose litres and kWh feed a money
figure. Read `spec.md`, `rulings.md`, 0K2's `spec.md` §2.5, then the diff. Done means every question of spec §6
answers yes with evidence and every plant below fails its named test.

## What to check, and how

1. **Independent expected values (W2).** H1 to H5 compare the study with the host test's own reader (customer steps by
   fixed offset, headroom by its own loop, litres from `fuel_start_l` by its own loop). Expected values built by
   calling a `headroom_replay.py` or `replay_study.py` helper are High.
2. **One rule of each.** `headroom_replay.py` calls 0K2's helpers for window, sample, start, calibration, starts,
   burns, months and dawn; a second copy of any of them is High (D-0M.1).
3. **Nothing modelled.** Only sums, differences, the headroom `max`, the reduced `min` and the ratio. A tariff, price,
   SFC, inverter law or dispatch rule is High (D-0M.8, D-0M.11).
4. **Whole-window pairs.** M6 and H1: `1 + k` or `2 + 2k` calls of `n` steps; each customer compared with its own
   capacity's no-customer run (D-0M.7).
5. **The request.** M1 and H5: only `host_load_id` changes, at the customer's local steps; other loads by id.
6. **Fixtures.** `mto.py` against spec §3 and the manifest's Mto block; Kobo-template facts kept are listed in the
   packet.
7. **Seam.** The diff lists spec §0's five new files and the one edited test; `runs/replay_study.py` and
   `host/tests/kobo_season.py` are unchanged; the guard shown failing.
8. **Labels.** `input_class` and MODELLED on every result; nothing served; no design value edited (D-0M.11).

## Planted violations (each must fail the named test; the builder shows each failing once, in a scratch copy)

| # | Plant | Fails |
|---|---|---|
| P1 | customer steps by UTC time | M1, H5 |
| P2 | customer steps on every day, weekends included | M1, H6 (22 weekdays) |
| P3 | the customer added to every load, or to the first load by position | M1 (reverse-ordered loads), H5 |
| P4 | headroom not clamped at 0 | M2 (day 3) |
| P5 | a day without headroom judged on the day total, not per step | M2 |
| P6 | headroom read with the customer inside the load | M2, H3 |
| P7 | a reduced customer compared with the full baseline | M4 |
| P8 | the reduced run fed the unclipped PV | M4 (the port refuses 51 > 25 in H1 too) |
| P9 | extra litres as baseline minus customer | M3, H2, H3 (`> 0`) |
| P10 | one replay per customer day | M6 |
| P11 | the sample checked after the baseline replay | M5, H7 (zero calls) |
| P12 | customers replayed after a failed calibration | M5 (one call) |
| P13 | a second calibration rule in `headroom_replay.py` | review item 2 (High) |
| P14 | `litres_per_customer_kwh` divides by zero or reads 0 | M3 |
| P15 | `MIN_DEMAND_DAYS = 14` | H6, H7 |
| P16 | the welder refused for verbal evidence | H3 |
| P17 | `headroom_replay.py` imports `host.forward_replay` | M7, dependency-direction guard |

## Not findings

No money, no `NO_CUSTOMER_EVIDENCE`, no PRODUCTIVE_LOAD record (spec §7, D-0M.9, D-0M.11). One inverter component
stands for Mto's two (D-0M.2). Kobo-template values kept where Mto states none (D-0M.2). Mto shares Kobo's declared
weather (D-0M.3). PV that would have charged the battery counts as headroom (D-0M.6). Reduced runs are not
calibrated (D-0M.10). The run keeps the fixture's `KOBO-001` site id (spec §3).
