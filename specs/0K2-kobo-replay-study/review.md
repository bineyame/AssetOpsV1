# 0K2 review

## Round 1: discovery review (W5), 2026-11-21

Reviewer: Claude (fresh, not the author). Branch `task/0K2-kobo-replay`, head `a87a80680`, diff `main...a87a80680`
(10 files). Read: spec rev 2, rulings D-0K2.1-29, reviewer guide rev 2, packet, the whole diff, logs in
`/opt/assetecon/evidence/0K2/`.

**Summary (verdict: ACCEPT).**
- The study, the fixture and the tool do what spec §2-§4 say. I reproduced the 61-day figures myself through the port.
- Every record and printed line carries SIMULATED and MODELLED. "Calibrated" is said to mean adapter fidelity in the
  docstring, the JSON note, the tool's first line and the packet. Nothing reads as validated against a real Site.
- Dawn: nothing was tuned. The 16 failing dawns come from the shipped dispatch law on the Site's settings.
- No design value or label is changed (row 37 holds). There is no money anywhere. Row 42 stands.
- Findings: 0 High, 0 Medium, 3 Low (below). None blocks the merge.
- The gap between the design and the study is explained by the season and the model's fuel law, not by a defect
  (see "Design values beside the study").

### Checks I ran (head `a87a80680`)

- `check-architecture.ps1` (with `ASSETOPS_GUARD_PYTHON`): "Architecture check passed." `check-agent-workflow.ps1`:
  "Agent workflow check passed."
- Through the slot pool, backend `test_0k2_replay_study.py` + `test_0k1_replay_port_seam.py`: 29 passed in 2.21 s.
- **Independent 61-day reproduction** (scratch script through `heavy-slot.sh`, `--label 0K2-review`, exit 0; site run
  118.4 s, study of baseline + 2 cases 257 s). I read the projections myself, by offset: fuel stock at steps 0, 8,640
  and n, dawn at step `d × 288 + 60`, and discharge by my own loop.
  - Calibration: 7,418.143 / 7,418.679 kWh; starts 46 / 46; SOC MAE 0.0214.
  - stop-70-reserve-30: avoided 85.33 L in Sep and 85.08 L in Oct; added throughput 0 / 0.
  - stop-90-reserve-25: avoided 47.59 / 48.34 L; added throughput 37.49 / 39.62 kWh.
  - Both cases: dawns below 35 % on days {0, 4, 8, …, 60} (16 of 61); least passing reading 35.263.
  - Every figure equals the packet and `study.json`.
  - The fixture's frozen inputs keep no forcing of the base scenario at any other address. Each of the four season
    series covers every 5-minute step of the 61 days exactly once.
- I did not rerun: the host kernel tests (cited: 47 passed at `79434e411`; files unchanged since), contracts (190
  passed), the plants (log read: P1-P31), or check-all (40 guards passed at `1f2f3f2be`). The production code is
  unchanged between the season run's revision `56bbefdf0` and the head (`git diff --stat`).

### Verified against the dispatch

- **Labels.** `input_class` and `evidence_class` are validated on `StudyResult`, `Calibration` and `CaseOutcome`. In
  `study.json`, every case and the calibration read SIMULATED / MODELLED, and no key or value contains "observed".
  Every printed line starts `input_class=SIMULATED evidence_class=MODELLED`. In the packet, "observed" appears only
  in code names (`observed_series`) and "agree" only in the pre-flight note. B13 covers the two source files.
- **Dawn (D-0K2.17).**
  - Bound 35 %, reserve, start charge 48 %, calendar `d % 4 == 3` and the frame are as declared. No reading is
    excluded.
  - Cause: `packs/mini_grid.py:19-23` says "It may also charge the battery, only when the battery is not
    discharging". My per-day trace fits it. After an overcast day, the 05:00 reading is 30.97 with the generator
    RUNNING; on clear days the generator first starts at 05:05 at 35.26. So the night dwell sits at the effective
    start, 5 points above the reserve.
  - 1 Sep is the declared start charge crossing 35 % at 04:55.
  - Every case has the same 16 dates. `new` and `cleared` are () for all 14 cases.
- **No modelling in `replay_study.py`.** Its arithmetic is sums, differences, tolerances, the SOC drop and local
  framing. No price, fuel law, threshold or gap fill; no `float(` or `round(`. Imports are exactly §2.1's set.
  Refusals in steps 1-4a come before the first port call, and the grid ids are fixed in step 4a.
- **T11.** The test asserts the self-shift precondition: each shift direction breaks all three bounds
  (`== (False, False, False)`). The unshifted run is within all three, and no bound was widened.
- **P24.** It fails B3 but passes T3, because neither the 8-day season nor the 61-day season has a case that adds or
  clears a dawn date. B3's stub, scripted for one date each way, is a sufficient catch, so I accept it (see L2 for the
  residual risk). **P27** was already caught by T13; the stronger B5 is extra cover.
- **Deviations.**
  - `observed_series(start=)`: a keyword with a default, needed by T13. Fine.
  - `min_litre_days < 1` raising `ValueError`: stricter than the spec and harmless; `calibrate` would still divide
    safely.
  - `select-tests` asks for the full suite because of a new file under `tools/`. Under the test-suite policy, that run
    is the coordinator's to schedule at the next milestone. It is not a finding.
  - The branch name differs from the spec's (`-study` suffix), as the packet states.

### Design values beside the study (for the owner)

Same bases, design values unchanged:

| Setting | Avoided fuel | Dawns below 35 % | Added battery throughput |
|---|---|---|---|
| stop 70 (design) | 210 L a month | 0 of 61 | 150 kWh a month |
| stop 70 (study) | 85.3 L (Sep), 85.1 L (Oct) | 16 of 61 | 0 kWh |
| reserve 25 (design) | 20 L a month | 4 of 61 | not given |
| reserve 25 (study, stop 90) | 47.6 L (Sep), 48.3 L (Oct) | 16 of 61 | 37.5 / 39.6 kWh |

The inputs explain the gaps. My per-day trace shows how:

1. **Stop 70 only saves fuel on mornings when the generator is charging the battery.**
   - On a clear day (31 of 61), PV fills the battery to 100 %. Stopping at 70 % cuts the morning run from about 12:10
     to 10:45, which saves 3.7 L (about 12 kWh at the template's 0.3 L/kWh).
   - On an overcast day (15 of 61), the battery never rises above 48 %, so the stop setting never acts and saves 0 L.
   - On the morning after an overcast day it saves 3.65 L.
   - That makes about 2.8 L a day across the season. The design needs 7 L every day, about 23 kWh, which is more than
     half of the full 90-to-70 band of 40 kWh.
2. **The fuel model is linear, with no fuel burned at idle or at start-up** (disclosed in the pack's docstring). The
   roughly 64 running hours cut over 61 days save only the energy those hours would have produced. A real generator
   would also save its idle fuel, so on real equipment these figures would tend to be higher.
3. **Added battery throughput is 0 for every reserve-30 case.** The stop setting changes only how much the generator
   charges, never how much the battery discharges. PV refills the battery each clear day, so the evening discharge is
   the same in every case.
4. **The dawn count is 16 of 61 in every case** because the no-action baseline already fails on those 16 dawns. The
   design assumed the baseline passes.
5. **Reserve 25 saves more than the design says.** The generator starts at 30 % instead of 35 %, which saves 3.2 L on
   each overcast day.

The design's 210 L came from 330 candidate litres a month taken from a different source, not from this season. The
study's season is one fixed calendar with one overcast day in four, built from the shipped Kobo day types. No figure
here is from a real Site.

### Findings

- **L1 (Low, preference): packet table layout** (`packet.md` 25-48).
  - Spec §5 asks for three columns: "site (simulated)", "season replay (SIMULATED, MODELLED)" and "design value
    (unchanged, still labelled design)". The packet gives the design values in a paragraph after the table, and labels
    the baseline *replay* row "baseline (site, simulated)". The packet does say they are equal within T11's bounds.
  - The content is complete and honest, but a reader could take the replay row for the site run.
  - Fix, if the packet is reused for the owner: rename the row "baseline replay (≈ site, simulated)" and put the
    design values in a column.
- **L2 (Low, residual risk): the new/cleared dawn dates are proven only on the stub** (B3).
  - Neither kernel season has a case that adds or clears a dawn date, so T3's comparison of these fields is
    trivially true.
  - `6c`'s admissibility default (row 42) reads exactly these fields.
  - Fix, optional and for `6c` or later: a kernel case where a setting changes a dawn date, such as a lower reserve on
    a season whose baseline passes.
- **L3 (Low, owner presentation): the packet gives no reason for the gap with the design.**
  - The spec forbids verdict words, not explanation, so this is not an acceptance gap.
  - The owner will see factors of 2.5 and more against the design values.
  - Suggest relaying the "Design values beside the study" section above with the figures.

### What I could not verify

- The plants and the host kernel tests were not rerun. I relied on the implementer's logs, whose revisions match.
- Whether the pack's 330 candidate litres hold on Kobo's real records: that is outside this slice (`0K3` / `6c`).
