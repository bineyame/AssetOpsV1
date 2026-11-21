# 0M review packet: Mto's demand-on-headroom replay

Branch `task/0M-mto-headroom` (the spec names `task/0M-mto-headroom-replay`; the dispatch named this one), base `main`
`6c33395ef`. **0K2 merge commit `3b4f06052`** (`git merge-base --is-ancestor 3b4f06052 HEAD`: yes). Commits: unit 1
`7fe187fdb`, unit 2 `b33b793bf`, unit 3 `465d095fc`, M4 plant fix `12b1d0427`, closeout (this packet, state). Spec rev 2,
rulings D-0M.1-22. No database, no migration, no served text, no money. `USER_REVIEW_REQUIRED: false`; the figures go
to the owner beside the design values (row 37 held, row 42 stands). Evidence: `/opt/assetecon/evidence/0M/`.
Mid-build questions: **0**.

## Pre-flight (`preflight-probe.log`, 8 days, v7)

`mto_base_run(8).execution_status` READY; at 25 kW READY. Frozen needs (both runs, value unit = canonical):
`pv-rated-power` 50.0 kW, `inverter-ac-limit` **50.0 kW / 25.0 kW** (one row each, unit kW), `battery-energy-capacity`
150.0 kWh, `battery-reserve-state-of-charge` 30.0 %, `generator-rated-power` 30.0 kW,
`generator-specific-fuel-consumption` 0.33 L/kWh. 8-day site: fuel 48.35 L, generator 146.50 kWh (the Architect's
probe said baseline 74.47 L; status and initial values match, figures are outputs).

## Files

New: `backend/assetops_backend/runs/headroom_replay.py`, `backend/tests/test_0m_headroom_replay.py`,
`host/tests/mto.py`, `host/tests/test_0m_mto_headroom.py`, `tools/mto_headroom_study.py`. Edited:
`backend/tests/test_0k1_replay_port_seam.py` (allow-list +2). `replay_study.py`, `kobo_season.py`, `host/`,
`simulator/`, `contracts/`, `config/`, guards: unchanged.

## Plant values (D-0M.21)

Edited to the manifest: PV 50, battery 150, reserve 30 (the template's own value, a traced no-op), generator 30,
SFC 0.33, inverter 50 (INV-MT-01 + INV-MT-02) or 25 (INV-MT-02 failed); ratings PV 50, battery 150, generator 30,
inverter 50/25. Kept from the template: PCS charge/discharge 30 kW, start 35 %, stop 90 %, minimum runtime 30 min,
start delay 5 min, efficiency 95 %, load ratings 25/10/40 kW, site id `KOBO-001`. Kept from the season: irradiance
windows, overcast calendar (`d % 4 == 3`), tank 20,000 L and rating, start fuel 15,000 L, start SOC 48 %. One
derivation: loads x 1/2 (6,000 / 11,580 ~ 0.52). PV 50 on a 50 kW limit never clips at full capacity (Kobo's 60 on 50
did).

## The 61-day study (`season-465d095fc/study.json`, `run.log`)

Every line and the JSON header: `input_class=SIMULATED evidence_class=MODELLED`, plant = `MTO_PLANT_NOTE`. CALIBRATED on
SIMULATED input means adapter fidelity (the replay follows the kernel run that made the series), not a match to Mto.
Calibration, 61 admissible days: generator kWh site 1,788.870 / replayed 1,788.831; starts 15 / 15; SOC MAE 0.0203;
failed (). Baseline fuel 590.314 L (= the site run). Unserved energy: 0 in every case.

| Figure (SIMULATED, MODELLED) | Study, October (window total) | design value, unchanged (held, row 37) |
|---|---|---|
| Huller: days without headroom | 6 (11 of 44) | 3 |
| Huller: kWh beyond headroom | 384 (704 of 3,300) | 225 "from battery or genset" |
| Huller: extra litres | 156.67 (287.23; Sep 130.56) | 68 |
| Huller: extra generator kWh, starts | window 870.39 kWh, 0 starts | - |
| Welder: kWh beyond headroom | 660 of 660 (1,320 of 1,320; 44 of 44 days) | every kWh diesel |
| Welder: litres per customer kWh | 116.39 L / 660 = 0.176 (window 0.159) | 0.33 |
| Reduced capacity, no customer | 7.70 L in Oct; 0.237 L a day (14.44 L, 61 days) | 5 L a day |
| Huller at 25 kW (vs reduced) | 22 days, 640 kWh beyond, 367.75 L | - |
| Welder at 25 kW (vs reduced) | 22 days, 660 kWh beyond, 124.73 L | - |

Plain reasons for the gaps. **Days and kWh:** the season's declared weather is overcast every fourth day (7-8 a
month), so more weekdays lack headroom than the design's 3; the design's 225 kWh is 3 days x 75 kWh, the study's 384 is the
step-level shortfall on its 6 days. **Huller litres:** the replay also counts the diesel spent refilling
the battery the huller drew from on days that had headroom (PV that would have charged the battery counts as headroom,
D-0M.6); the design's 68 L does not. **Welder:** the battery carries about half of the evening kWh before the
generator starts at 35 %, so 636.7 generator kWh (at 0.33 L/kWh) serve 1,320 customer kWh in the window. **Reduced:**
with loads halved, PV above 25 kW occurs only near noon on clear days and most of it would have charged the battery;
the generator makes 43.75 kWh more in 61 days. Nothing was tuned.

**Dawn (D-0K2.17, D-0M.22).** Baseline: FAIL, 15 of 61 dawns below 35 % (5 Sep and every 4th day to 31 Oct, the day
after each overcast day), worst 30.72. Cause as D-0K2.17: Mto keeps the template's start 35 / reserve 30, and the
shipped law charges only when the battery is not discharging, so after an overcast day the night dwell ends below 35.
Huller: 15 below, new () cleared (). Welder: 13 below, new (), cleared (2026-09-13, 2026-10-11). Reduced, no customer:
15, new () cleared (). Huller at 25 kW: 29 below, 14 new against the reduced replay (2026-09-02 ... 2026-10-29, in
`study.json`), cleared (). Welder at 25 kW: 13, cleared the same two dates. Each verdict is that replay's absolute
FAIL; a customer's dawn effect is its new dates only.

**Run.** Cap `max(12, ceil(2 x (2 x 117.7 + 7 x 80.3) / 60))` = 27 min (0K2's measured site 117.7 s, replay 80.3 s).
Actual: 1 site run + 6 replays of 17,568 steps (the reduced base run is frozen, not executed), wall 10 m 33 s (site
120.6 s, replays 511.1 s), peak RSS 796 MB, exit 0, rev `465d095fc`.

## Checks (rev `12b1d0427` unless stated)

- Focused + regression through the slot pool (`regression.log`): `test_0m_mto_headroom.py`, `test_0k2_kobo_season.py`,
  `test_0k1_forward_replay.py`, `test_0m_headroom_replay.py`, `test_0k2_replay_study.py`,
  `test_0k1_replay_port_seam.py`: **121 passed in 119.8 s**.
- Contracts through `tools/run-host-tests.ps1` (files listed; the wrapper refuses a directory): **190 passed in 66.8 s**.
- `check-architecture.ps1`: passed. `check-agent-workflow.ps1`: passed. Fast check-all at `5a424ce6e`: **all 40 guards passed**, 125.4 s (`check-all.log`).
- `select-tests.py --base main`: full mode (569 files) because a tool changed; the full suite was not scheduled.
- **Guard shown failing** (`guard-plant.log`): `headroom_replay.py` importing `host.forward_replay` fails
  `check-architecture` ("Banned import of the composition leaf ... headroom_replay.py:31"); reverted.

## Plants (`plants.log`, `plants-rerun.log`; throwaway worktree, removed)

P1-P12, P14-P26 each applied alone; each fails its named tests (P13 is a review item). Two found a gap, fixed:
- **P21** first passed M4 (its stub was also refused by "full not above"); M4 gained `stated-not-frozen` (frozen 25,
  stated 30), commit `12b1d0427`; rerun fails M4 and H1.
- **P6** fails M2 and **H2**, not H3: the welder runs after sunset, where headroom is 0 with or without it, so H3
  cannot see it. Recorded as a known deviation from the guide's "M2, H3".
- P24 planted as "days counted by steps, not dates" (the "all steps" variant equals the right figure, since headroom
  is never negative). P17 also as a scratch `host.forward_replay` import against the guard (above).

## Known deviations

Branch name as dispatched. P6 caught by H2 rather than H3. Nothing else.
