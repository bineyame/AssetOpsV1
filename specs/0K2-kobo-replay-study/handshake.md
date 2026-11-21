# 0K2 handshake (one combined round, RULES §4 items 6-7)

**Answered (round 1), 2026-11-21:** every question below is answered once in `rulings.md` "Handshake answers (round 1)" and folded into `spec.md` rev 2 and `reviewer-guide.md` rev 2. No question is open.

The Reviewer, after reading `spec.md`, `reviewer-guide.md` and `rulings.md`, and the Implementer, after a
pre-flight of `spec.md` against `main`, write their questions here in one batch. Number them R1, R2 ... and
I1, I2 .... Each question cites the spec section, says what is unclear and what answer the writer expects, and is
marked **(done)** when its answer changes what counts as done. The Architect answers every question once, in
`rulings.md` under "Handshake answers (round 1)", and folds the answers into `spec.md`. The handshake ends when
neither section has an open question; coding starts only then.

## Reviewer questions

Checked on `main` (head `5a3987dcd`): spec, rulings and guide read whole; 0K1's contract, port and adapter read whole;
the Kobo files and the kernel's generator law read where the questions cite them. One kernel probe was run through the
slot pool (scratch, deleted): the §3 recipe written independently, 8 and 61 days, v7. It confirms the recipe runs
(COMPLETED); a first attempt without `valid_from` 2026-08-01 was BLOCKED with 16 reasons, so §3's `season_site` line is
load-bearing.

**R1 (done). The dawn failure under no action: cause, and what the packet must say (§2.4, D-0K2.8, §5 packet).**
D-0K2.8 says the baseline is "below 35% at dawn on days after overcast ones" and treats it as a result. The probe
(61 days) gives 16 failing dawns of 61 under no setting: 15 are the days after each overcast day (SOC 30.97, generator
`RUNNING` at 05:00), and one is day 0 (34.84, `STARTING`). The two have different causes and neither is a model defect:
(a) after an overcast day the battery sits on the reserve (30%) all night with the generator RUNNING, because Kobo's
priority is PV, battery, generator and `mini_grid.py` charges from the generator only "when the battery is not
discharging"; the stop (90%) is therefore not reached until PV returns, so the generator runs for hours without raising
the charge, and the design's 35% dawn limit lies above the reserve of 30%, so the bound fails whenever the battery
rides to the reserve; (b) day 0 is a fixture artefact: the start charge 48% is a declared fixture choice, the start
threshold equals the dawn limit (35), and the crossing falls at 04:55. Also, 45 of the 46 other dawns read 35.26, 0.26
above the limit: the verdict is a knife-edge on one step, not a margin. The spec does not say any of this, and a
reader of `dawn_verdict == FAIL` on every case would take it for the setting's effect. Expected answer: the packet
prints, per case, each failing dawn's date, SOC and generator state, classifies the baseline's 16 as above, and says
every case, the baseline included, fails the bound, so the study does not separate settings on it (admissibility
relative to no action is `6c`'s); D-0K2.8's "after overcast ones" is replaced by the cause; no change to `replay_study.py`.
Is the generator law (no charging while the battery can discharge) to be stated in the packet as the model's
documented simplification, since it drives the dawn and, with it, how little a lower stop threshold can change at night?

**R2 (done). Plants that depend on position, not only on totals (§4 T1, T3; guide plants).**
0K1's lesson was that totals hide position errors. The tolerances (5% energy, 5 points SOC MAE) are wide, and T1/T3 compare
`CaseOutcome` figures with a reader of the replay's own projections, so a fixture that publishes PV, a load, the
SOC or the generator state one step late (`B[i]` for `B[i+1]` or the reverse), or a start state read from step 1,
still calibrates and still equals the reader (both sides are shifted alike). P1 to P20 plant none of these. Expected
answer: a test T11 on the 8-day kernel season compares the baseline replay with the site trajectory step by step
(generator state equal on every step; SOC within a stated bound, from the 0.02 MAE probe, say 0.5 point; generator kWh
within the quantum plus drift), and plants P21 (PV or loads from `B[i]`), P22 (SOC or state from `B[i+1]`), P23 (start
state from step 1), each named against T11 or T1; and the dawn reader reads the site's own trajectory, not only the
replay.

**R3 (done). A kernel-backed month boundary (§2.4 `by_month`, T3, P4).**
The 8-day kernel season lies wholly in September, so T3's month split has one month and cannot fail on a local-versus-UTC
or off-by-one boundary; only the stub test B4 can, and the 61-day run has only the sum identity. Expected answer: T3
(or one more kernel case) runs a window that crosses 1 Oct local (the fixture takes a start date; the overcast
calendar is by day index so it is unchanged) and the reader splits by offset, with both months non-zero.

**R4 (done). Labels on the figures a reader will actually see (§2.1, D-0K2.12, D-0K2.13, §4 tool, §5 packet).**
Row 37 is held, so no output may read as a design value confirmed or replaced. Four places lean that way:
(1) `input_class` and `evidence_class` sit on `StudyResult` only; the tool's one-line-per-case print and `study.json`
may show a `CaseOutcome` without them. (2) The series is called `observed` in the types, `Calibration` fields and
the packet ("observed generator energy"), though it is simulated. (3) `status == "CALIBRATED"` on a series that
this kernel produced means the adapter added no distortion, not that the model matches a site; `6c` will read the word.
(4) D-0K2.12 says "the manifest carries the spike's figures as option parameters (`design_value: K`)", which reads as
if 0K2's figures reach the manifest. Expected answer: every printed line and the JSON header carry `input_class=SIMULATED`
and `evidence_class=MODELLED`; the packet columns read "site (simulated)" and, beside the design values, "design value
(unchanged, still labelled design)" and "season replay (SIMULATED, MODELLED)" with no verdict word (reproduces, confirms,
agrees, replaces) and no pass/fail between them; the packet says CALIBRATED is the adapter-fidelity check; D-0K2.12's manifest
sentence is reworded as `6c`'s future use, held by row 37, and nothing in 0K2 writes a manifest, config or label.

**R5 (done). The design values' basis for the comparison table (§5 packet, D-0K2.11).**
The design values are "avoided 210 L a month, 150 kWh added throughput, 0 of 61 dawn days". The study gives litres by
month (Sep 30 days, Oct 31) but `added_throughput_kwh` for the whole window, and D-0K2.11 calls "the design's 150 kWh"
the wear basis while the frame uses the template's 200 kWh battery. A table of 61-day totals beside a per-month design
figure would mislead. Expected answer: the packet states the basis of each design figure (per month or in all; which
capacity), and shows each season figure on that basis (per month and per 30 days, computed in the packet's arithmetic,
not in `replay_study.py`).

**R6. The shipped overcast day's reserve change is left out (§3 day types).**
`kobo-daytime-overcast` has an `evening-reserve-override` (reserve 15% from 16:00) that the season does not take
("not a series"). The reserve lever (30 to 25) and the after-overcast nights are exactly where that override acts, so the
season's overcast days differ from the shipped day type in the one respect the reserve grid is about. Expected answer: a
declared simplification stated in the packet beside the reserve figures (and not a finding), unless the Architect wants the
override added as a frozen forcing.

**R7. Starts counted twice (§2.3, §2.4).** `CaseOutcome.starts` is the §2.3 rule over the steps; the projection carries its
own `starts` (STOPPED to STARTING transitions). They can differ at the window edges (a STARTING first step after a STOPPED
start state, or a transition at the last boundary). Expected answer: T3's independent reader counts transitions on the
trajectory, asserts study `starts` equals it and equals `projection.starts` on the season, and says which one `6c` is
to read when they differ.

## Implementer questions

Pre-flight of `spec.md` against `main` (head `5a3987dcd`), with the §3 recipe built independently in a scratch probe
(8 and 61 days, v7; output below). Signatures checked and matching: `ForwardReplayRequest(case_id, pv_available_kw,
loads, start, settings)`, `LoadSeries(load_id, kw)`, `ReplayStartState(soc_pct, fuel_l, generator_state)`,
`ReplaySettings`, `ForwardReplayProjection` fields used by §2.2 to §2.4, `ForwardReplayRefused`, `ForwardReplayPort`,
`HostForwardReplay`, `kobo_draft` (its keywords), `set_property`, `frozen_world_inputs`, `model_for`, `execute`; the four
series' state keys and `timing.duration_minutes`; the prolonged scenario has no other forcing and no cause, so nothing else
is replaced or kept; the template's battery capacity 200, start 35, stop 90, reserve 30, delay 5, minimum runtime 30;
`CASE_ID` accepts `stop-90-reserve-30`; `zoneinfo` resolves Africa/Addis_Ababa.

**I1 (done). The pre-flight's expected figures and the 61-day shape (§0, §4 tool).**
§0 gives 959.56 kWh, 7 starts, min SOC 30.0, fuel 287.87 L for 8 days; I did not re-derive them and an unequal figure is
not a question. On 61 days the probe's own reader gave: COMPLETED; generator 7,418.68 kWh; 46 starts (§2.3 rule); min SOC
30.0; fuel burned 2,225.6 L (so the tank bound is far away); 16 dawns below 35% (see R1). The one run took under two
minutes; the spec's 44 s per replay is extrapolated from 8 and 14 days, and the forcing count grows from about 700 to
about 3,500 on 61 days. Expected answer: the tool's first step times one 61-day replay and prints it; if it exceeds 90 s
the 25-minute cap is re-set before the 15-replay run, and the packet records the wall time per replay.

**I2 (done). The tank-bound check names a field a step does not have (§2.2 step 5, D-0K2.10, B9).**
Step 5 says "any step's `fuel_start_l == 0` or `fuel_end_l == 0`"; `ReplayStep` has `fuel_start_l` only, and
`fuel_end_l` is the projection's. Expected answer: any step's `fuel_start_l == 0` or the projection's `fuel_end_l == 0`
(a tank that empties in the last step), and B9 has a case for each.

**I3 (done). `LATE_WINDOWS` against `NIGHT_WINDOWS["late"]` (§3, T8).**
The two have different shapes: `NIGHT_WINDOWS["late"]` is `(("20:00","22:00",0,120,9,<basis>,4,<basis>), ("22:00","24:00",120,120,5,...,2,...))`.
T8 says "equals" without a mapping. Expected answer: the test maps each row to `(local start minute from "HH:MM", minutes,
{"load-res": res, "load-clinic": clinic})` and asserts equality with `LATE_WINDOWS` row by row, plus that the file's start
minute plus its offset gives 1200 and 1320.

**I4. The seam test's text scan (§4 edit, D-0K2.14).**
`test_nothing_else_in_the_backend_names_the_replay` flags any backend file containing the text `forward_replay`. Both new
files contain it, so both go into `allowed`, as stated. Expected answer: yes; a docstring in any other new backend file
must not name `forward_replay` (none is planned), and the packet shows the scan count (above 100).

**I5. The kernel test file's run time (§4).** `test_0k2_kobo_season.py` runs about 16 kernel runs of 8 days (T1 three
settings plus baseline, T3, T4's 14 days twice, T6, T9). Expected answer: cache the 8-day site run and its baseline
replay per module (`functools.cache`, as 0K1), so the file stays near one minute; T4's 14-day site run is built once.
