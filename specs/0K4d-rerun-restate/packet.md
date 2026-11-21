# 0K4d review packet: admission rule, rerun on v8 and season v2, MG-T restated

Implementer (Claude), 2026-11-21. Branch `task/0K4d-rerun-restate`, worktree `/opt/assetecon/AssetOpsV1-0k4d`. Spec rev 2,
rulings D-0K4.26 to D-0K4.30. Commits: 1 `6390f3404` (admission rule; packet facts in `handoff.md`), 2 `6fd0d6bb6`
(tools, fixtures, V0-V6; the two 61-day runs are at this commit), 3 `8db4f8d41` (§4.2 restated), then this packet.
`USER_REVIEW_REQUIRED: true`: these are the figures the owner will see. Evidence: `/opt/assetecon/evidence/0K4d/`.

## 0. Pre-flight (opens commit 2, after merging `main` at `ff87ecac9`, before either tool was edited)

1. `main`'s `tools/kobo_replay_study.py --days 8`, no flag: `status=SAMPLE_TOO_SHORT`, no case (14 admissible days
   are needed for any litre figure), so 8 days gives no `avoided_l`. Also run `--days 14`, no flag: CALIBRATED;
   `avoided_l` exact per case, recorded as V5's literals (`MAIN_AVOIDED_L_14`, 14 cases; e.g. `stop-70-reserve-30`
   1637/40, `stop-90-reserve-25` 362043/16000). Evidence `preflight/main-kobo-{8d,14d}*.txt|json`. Known Deviation 1.
2. `--time-one --days 61 --model-version 8 --season v2`: Kobo site 127.3 s, replay 88.7 s; Mto site 124.5 s,
   replay 94.5 s (`preflight/time-one.txt`).
3. Caps: Kobo `max(25, ceil(2 x (127.3 + 15 x 88.7) / 60))` = 49 min; Mto `max(25, ceil(2 x (124.5 + 6 x 94.5) / 60))` = 25 min.

## 1. Identity headers (`study.json`)

| | Kobo (`kobo-61d/`) | Mto (`mto-61d/`) |
|---|---|---|
| commit | `6fd0d6bb6b17b851a0e27d3098a592a656f56fc1` | same |
| model, season | `mini-grid/8`, `v2` | `mini-grid/8`, `v2` |
| `season_inputs_digest` (S9's form, v7 base) | `465ab6e0818f3fbd...07f4cdb1a8` (= S9's literal) | same |
| site `trajectory_digest` | `7be8f02e64fa91a8...3fba1d` | `afd2a3e376b8f75b...defa757` |
| status; calibration | CALIBRATED; gen kWh 9369.149 site / 9369.396 replayed, starts 64/64, SOC MAE 0.024 | CALIBRATED; 1947.123 / 1947.121, 18/18, 0.025 |
| run | 16 kernel runs, 26 m 39 s wall (cap 49) | 1 site + 6 replays, 11 m 49 s (cap 25) |

Assumptions (both headers, D-0K4.27 verbatim; V4 asserts them): Kobo no-load 3.3 L/h, minimum load 30 %, taper 95 %
(GENERIC_DEFAULT), SFC 0.3 L/kWh (TEMPLATE); Mto no-load 2.4 L/h (GENERIC_DEFAULT: 0.08 L/h per kW x 30 kW), minimum
load 30 %, taper 95 %, SFC 0.33 L/kWh (declared, MANIFEST). Kobo `admission_rule`: max-starts-per-day 6, full-charge
-every-days 7 (assumed, GENERIC_DEFAULT), words in the tool.

## 2. Kobo figures: season v2 on mini-grid v8 (SIMULATED, MODELLED; assumptions as above)

A month is the 61-day window x 30 / 61. Dawn is information beside the admission, never a gate.

| Case | Avoided L a month (Sep / Oct window) | Added throughput a month | Added starts a month | Admission (most starts a day; longest days w/o full charge; reserve breaches; unserved) | Dawn (information) | Lowest charge |
|---|---:|---:|---:|---|---|---:|
| no action (`baseline`) | 0 | 0 | 0 | (2; 4; 0; 0 kWh) | worst 34.795 %, margin −0.205, 4 of 61 below 35 % | 33.226 % |
| stop 70, reserve 30 | **212.75** (190.150 / 242.444) | 59.00 kWh | 8.36 | **admitted** (3, limit 6; 5, limit 6; 0; 0 kWh) | worst 34.795 %, margin −0.205, 4 of 61 | 33.141 % |
| stop 90, reserve 25 | **59.73** (32.595 / 88.853) | 114.69 kWh | −2.46 | **admitted** (2; 4; 0; 0 kWh) | worst 29.816 %, margin −5.184, 11 of 61 | 28.243 % |

All 14 grid cases are admitted (`kobo-61d/run.txt`, one line each). Per-dawn tables (date, SOC, state, class) are in
`study.json` `dawn_below`; every reading below 35 % is class `other` (none after an overcast day): the baseline's four
(6 Sep, 2, 15, 28 Oct) are 34.795 % with the generator STARTING (the step it crosses the 35 % start). Night table
after the 3-4 Sep overcast spell: `kobo-61d/night-table-2026-09-04-after-overcast.txt` (starts at 34.56 % at 19:55,
SOC rises every RUNNING step, battery charging at −2.1 to −2.5 kWh per 5-minute step, 0 RUNNING steps with battery discharge).

## 3. Mto figures: season v2 on mini-grid v8 (SIMULATED, MODELLED)

| Case | Extra fuel (window; a month = x 30 / 61) | Days without headroom | Extra starts | Dawn below 35 % (information) |
|---|---:|---:|---:|---|
| `mto-huller` (SIGNED) | 312.890 L; **153.88 L a month** | 16 | 5 | 0 (worst 35.253 %) |
| `mto-welder` (VERBAL) | 428.826 L; 210.90 L a month | 44 | 14 | 0 |
| `reduced` (25 kW inverter) | **0 L a day** (exactly 0/1 L, 0 kWh) | n/a | n/a | 0 |

Mto has no admission rule (0M's outcomes unchanged in shape). Baseline fuel 646.180 L over 61 days.

## 4. What moved from the v7 study and why (both columns model figures)

Cause for every row: **model v7 to v8 and season v1 to v2 together (not separated)**. v7: `/opt/assetecon/evidence/0K2/season-61/study.json`, `/opt/assetecon/evidence/0M/season-465d095fc/study.json`.

| Quantity | v7 study | v8 study |
|---|---:|---:|
| stop 70: avoided L a month | 83.80 | 212.75 |
| stop 70: dawn days below 35 % / worst | 16 of 61 / 30.968 % | 4 of 61 / 34.795 % |
| stop 70: added throughput; added starts a month | 0.00 kWh; 0.00 | 59.00 kWh; 8.36 |
| reserve 25: avoided L a month | 47.18 | 59.73 |
| reserve 25: dawn days below / worst | 16 of 61 / 25.530 % | 11 of 61 / 29.816 % |
| most starts in a day; longest days w/o full charge; admission | not computed on v7 | as §2 |
| baseline starts (61 days) | 46 | 64 |
| huller extra L a month | 141.26 | 153.88 |
| welder extra L a month | 103.33 | 210.90 |
| reduced inverter extra L a day | 0.237 | 0 |

## 5. §4.2 restated: every numeral and its kind (D-0K4.29)

Kinds: (1) declared setting or record fact, (2) v8 study figure SIMULATED, (3) Not available yet, (4) `runs/admission.py` rule or information beside it. Identifiers (`dispatch-3.2`, `dispatch-3.3`, `v8`, `D-0K4.27`, `MG-T1`-`MG-T4`, `OR-MG-2`, `Q7`, `0K4e`, `4d`, `6c`, code line citations `:36-37`, `:43-45`) are names, not quantities.

| Place | Numerals | Kind |
|---|---|---|
| code block | `05:00`, `35` in `dawn(π)` | 4 (dawn reading time and limit, `admit`'s `dawn_limit_pct`; information) |
| code block | `12` in `value(π)` | 1 (§4.1's 12-month horizon; the formula is `6c`'s) |
| reserve paragraph | r − 5; 30, 25; min(35, 35) = 35; min(35, 30) = 30 | 1 (today's rule and declared settings) |
| table, settings | 30 → 25; 90 → 70, reserve 30; 100 kWh battery (28,000) | 1 (declared settings; KOB-BATT100 size and manifest capex) |
| table, litres | 59.7, 212.8 L a month; "61-day window × 30 / 61" | 2 (and its definition) |
| table, dawn | worst 29.8 %, 34.8 %; 11 of 61, 4 of 61; margin −5.2, −0.2; "below 35 %" | 2 (readings, counts); margin and 35 are 4 |
| table, dawn, comparison | "same 4 dates as no action"; "7 more than no action, which has 4" (11 against 4) | 2 (the baseline's own 4 and the case's 11 are v8 study counts, SIMULATED); 7 is their difference, 4 (information beside the rule) |
| table, throughput, starts | 114.7, 59.0 kWh a month; −2.5, 8.4 a month; most starts in a day 2, 3 | 2 |
| table, lowest charge | 33.1 % | 2 |
| table, value, warranty | Value cells; warranty floor; candidate running litres | 3 |
| candidate grid | {90, 85, 80, 75, 70, 65, 60} × {30, 25}; 10 % tie | 1 (proposed grid; `6c`'s tie rule, kept by D-0K4.29) |
| evaluator inputs | 212.8, 59.7, 153.9 L a month; "× 30 / 61"; 0 L a day | 2 |
| evaluator inputs | "mid-afternoon" (the Mto reduced-inverter reason, review L2) | 2 (read from the review's diagnostic on the SIMULATED v8 run, no new figure) |
| evaluator inputs | half inverter capacity, 25 kW | 1 |
| evaluator inputs | KIS-BATT60 | 3 |
| calibration | ±5 %, ±10 %, 5 points, 5 minutes; G = 1000 ×; 60 kW PV on 50 kW AC; ≥ 14 days | 1 (declared thresholds, `replay_study.py` CALIBRATION_*, MIN_LITRE_DAYS) |
| error modes | > 20 min, < 14 days | 1 |
| minimum sample | the study's 61 days; ≥ 14 days | 1 |
| sensitivity | Not available yet (`6c`) | 3 |
| vectors | MG-T1 59.7, MG-T2 212.8 L a month, worst, margin, counts as table; MG-T2 value, MG-T3 | 2 / 4 / 3 |

Gone: `dawn_ok ... → bound`, "Design values:", REJECTED, "0 of 61", "dawn PASS", "dawn adequacy FAIL (hard)", 330, 120 L,
"warranty floor 10%", wear 12.00, `(262.50 − 12.00) × 12 − 90.00 = 2,916.00`, the 2-point rule, 210/20/68/5 L, 150 L and 195.00,
the rule-of-three sentence, 2,286.00, 2,166.00, 15.6 L/month, 1.70/kWh, "Kisiwa replays to 0", MG-T1 "20 L, 4/61",
MG-T2 "210 L, 0/61, 2,916.00", and the 6 `<!--fig:-->` anchors on them.

## 6. Checks run (real output, evidence by path)

- V0-V6 `host/tests/test_0k4d_v8_study.py`: `11 passed in 94.49s` (`commit2/v-tests.txt`).
- Plants (`commit2/plants.txt`): P6 V4 `1 failed` (`assert () == (...)`); P7 V5 `1 failed` (`assert 2 == 0`);
  P9 V4 `1 failed` (`KeyError` at `mto_headroom_study.py:96`); P10 V6 `1 failed, 3 passed` (`assert 0 == 2`, Kobo 8/v1 only).
  P1-P5, P8 are commit 1's (`commit1/plants.txt`). Each reverted; tree clean.
- Regression at `8db4f8d41` (`commit3/regression.txt`): `test_0k2_replay_study`, `test_0k1_replay_port_seam`,
  `test_0k4d_admission`, `test_0k4b_properties`, `test_0m_headroom_replay`, host `test_0k2_kobo_season`,
  `test_0m_mto_headroom`, `test_0k4b_kobo_assumed`, `test_0k4c_season_v2`, `test_0k4a_dispatch_v8`,
  `test_0k4d_v8_study`: `153 passed in 132.66s` (`-n 4`, 8 m 60 s with slot wait).
- `tools/select-tests.py --base main`: `mode: full (595 of 595 backend test files)` because both tools changed; full suite not run (coordinator's).
- check-all (fast) at `8db4f8d41`: `All 42 guards passed (blocking; 0 advisory, 0 warned)`, 195.2 s (`commit3/check-all.txt`).
- `check_manifest.py` (`commit3/check_manifest.txt`): `7565 checks passed (2868 history checks), 1 failed`;
  `FAIL H9 baseline: 4496 checks passed before the history checks == 4502`: the 6 removed anchors. The manifest is 0K4m's (D-0K4.15); not edited.
- Statement catalogue: `OK statement catalogue: load, coverage, legacy, scan (6 adopted), keys, imports`; no `HAND_BUILT_NEW`; no baseline file changed.
- R5 regex `\b(210|2,?916|68)\b` and `\b(20|150) ?L\b` over both tools, `admission.py` and the `replay_study.py` diff: no hit.
- V0 applied (0K4c's packet: 0K4a was not on main, so S7's frozen half and S8 are here), with the overcast override.

## 7. Known deviations

1. V5: `--days 8` with no flag is SAMPLE_TOO_SHORT and has no `avoided_l`, so V5 asserts that (status, no case, header)
   and the `--days 14` literals; it narrows the tool's `KOBO_GRID` to the 3-case grid (monkeypatch) to keep the test near 1 min.
2. `MTO_ASSUMED` is a per-component dict like `ASSUMED_PROPERTIES` (with basis rows), not the flat tuple sketched in §2.3.
3. JSON headers add `trajectory_digests.site` only (the reduced Mto run is a replay base, never executed as a site).
4. The Kobo header's `admission` key states the source or `admission not available (<status>)`.

## 8. Residual risk and review focus

- The reduced-inverter figure is exactly 0 on v8/v2 (v7: 0.237 L a day): the 25 kW run's replay burns the full run's litres. Huller and welder do move with the limit (406.67 vs 153.88 L a month), so the limit is applied; review whether a battery full by midday explains it.
- Every Kobo case is admitted, and the reserve-25 row turns from "REJECTED" to "admitted" with 11 dawn readings below 35 %: the owner's rule, but the owner should see it.
- The dawn readings below 35 % are the start-threshold crossing step (34.795 %), so the baseline itself shows a −0.205 margin.
- The digest covers forcings and initial values only, not the rest of `FrozenWorldInputs`.
- Line 5 of the pack still names 210 L, 20 L, 68 L as design values, and §4.3 still holds 68 L: outside §4.2's Kobo text (0K4m).
- 0K4m hand-over (review L4): `domain-and-decision-models.md` line 755 still shows 330 and 2,916.00;
  `phase-plan-and-acceptance.md:144` says "KOB-RESERVE rejected by dawn adequacy", which now contradicts reserve 25 admitted.
- Round after review (L1-L4): L1, L2 in the doc; L3 the V5 test records `admit`'s arguments (baseline first); L4(b) the night table's column is relabelled kWh per 5-minute step in the evidence copy and `night.py`.
- Mid-build questions: 0.
