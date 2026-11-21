# 0K4d review

## Round 1: discovery review (W5), fresh Claude reviewer, 2026-11-21, head `7b9355ca1`

**Summary (verdict: ACCEPT WITH FIXES on the branch; no High, no Medium).**
- The figures are right. I recomputed every one by hand from `kobo-61d/study.json` and `mto-61d/study.json` (window x 30 / 61): stop 70 212.751 L, 58.997 kWh, +8.361 starts; reserve 25 59.729 L, 114.690 kWh, −2.459 starts; huller 153.880 L; welder 210.898 L. Each is labelled SIMULATED, MODELLED, with season, model and the D-0K4.27 assumptions. No design value sits beside any of them in the restated §4.2.
- **Mto reduced inverter at 0 L is honest, not a defect.** I reran the one pair (v8/v2 site run, then the full and reduced baseline replays) through the slot pool, about 5 min. The 25 kW cap binds on 3,840 of 17,568 steps, and the reduced run's SOC falls up to 30.4 points behind the full run (11 Sep, 12:15). Every one of the 38 gaps closes by 14:50 that day, with the battery back to about 100 %. Generator state differs on 0 steps, and no generator step falls inside a gap. So fuel, generator kWh and starts are identical (646.180 L, 1947.121 kWh, 18 starts). The guard is live, the cap is applied, and the units are consistent (see M-ITEM 2).
- The admission rule is D-0K4.9 exactly. All 14 Kobo admissions are correctly wired (the parts' case and baseline values equal the case and baseline fields; 0 mismatches). That every case is admitted is what the owner's rule gives on this season, not leniency in the code. A residual risk follows below.
- The §4.2 restatement holds only the four kinds. Nothing removed survives in the `F(π)`-to-vectors range. The two kind-1 calls (12-month horizon, 10 % tie) are acceptable.
- Findings: 0 H, 0 M, 4 L (L1-L4). L1 and L2 are text fixes on the branch. L3 is a missing test, which I recommend. L4 is the residual-risk list.

### Checks run (this reviewer, at `7b9355ca1`)

- Focused tests, via `tools/heavy-slot.sh -- pwsh tools/run-host-tests.ps1` (`-n 4`): `test_0k4d_admission`, `test_0k2_replay_study`, `test_0k1_replay_port_seam`, `test_0m_headroom_replay`, host `test_0k4d_v8_study` (V0-V6), `test_0k2_kobo_season`, `test_0m_mto_headroom` gave **`109 passed in 127.24s`**. The implementer's wider 153-test set at `8db4f8d41` is cited; no code changed after `6fd0d6bb6`.
- check-all (fast) via heavy-slot gave **`All 42 guards passed (blocking; 0 advisory, 0 warned).`** (7 m 33 s wall, with slot wait).
- Mto diagnostic (one v8/v2 site run, plus the full and reduced baseline replays) via heavy-slot took 306 s. Output is under item 2.
- By-hand recomputation of every packet figure from both `study.json` files; a cross-check of each case's admission parts against its fields (0 mismatches); full-charge gaps recomputed from `full_charge_dates` (all equal).
- Not rerun: `check_manifest.py` and the statement catalogue (the packet's outputs read; the docs and code are unchanged since).

### Item by item

**1. Figures and their honesty.** By hand (`Fraction(exact) x 30/61`): `stop-70-reserve-30` avoided 212.7510, throughput 58.9970, starts 8.3607 (81 − 64 = 17 x 30/61), most starts in a day 3, longest days without full charge 5, 0 breaches, 0 kWh unserved, admitted. `stop-90-reserve-25`: 59.7285, 114.6903, −2.4590, (2; 4; 0; 0), admitted. Mto huller 312.890 x 30/61 = 153.880; welder 428.826 x 30/61 = 210.898. The packet and the §4.2 cells agree, rounded to one decimal in the pack (212.8, 59.7, 153.9). The labels are on every cell and vector. "A month" is defined once in each table cell ("61-day window × 30 / 61").

**2. Mto reduced inverter = 0 L a day.** See the summary. Diagnostic: `<scratch>/rv-0k4d/mto_diag.py` (deleted after the review; its output is quoted here).
- `needs differing: {'inverter-ac-limit': (50.0, 25.0)}`: the reduced run differs from the full run only in the limit.
- `pv_clipped flags b 0 r 3840`, and steps with PV above 25 kW = 3840: the cap is applied, step for step.
- `steps with generator state differing: 0`; `steps where SOC differs and a generator runs: 0`.
- Each block of SOC differences runs from 08:05 to between 09:30 and 14:50, then closes (b 100.0 / r 99.93-100.0 at the block's last step).

The mechanism: at Mto's halved load, 25 kW of PV still refills 150 kWh before mid-afternoon on every day the cap binds. On overcast days PV does not reach 25 kW, so the cap never binds. v7's 0.237 L a day (43.75 kWh, about one partial run in 61 days) came from a different model and season. The huller moves (153.88 to 406.67 L a month) because its 15 kW, 10:00-15:00, takes exactly the afternoon surplus that refills the battery. The 0 and the 406.67 are consistent. The pack's gloss, "the reduced 25 kW run burns exactly the full run's litres", is true. L2 asks for the reason to be stated beside it.

**3. Admission.** `admission.py` against D-0K4.9: four parts in order, relative 1-2, absolute-then-`RELATIVE_BASELINE_FAILS` for 3-4, full-charge limit `every_days − 1`, `admitted` = the conjunction, and the dawn only in `DawnInformation`. `Admission.__post_init__` re-checks `admitted == all(parts)`. Not too lenient as coded: it is the owner's rule.
- The baseline's four dawn readings below 35 % are 6611/190 = 34.795 %, with the generator STARTING. That is the 5-minute step on which SOC crosses the 35 % start (night table: start at 34.56 %, SOC rising from the next step). Not counting them against a setting is right: the dawn is information (owner default 1). For stop 70 the four are the same dates as the baseline's (`new_dawn_days_below` = []), so the setting adds none (L1).
- Starts: most in a day is 2-4 across the grid against the limit of 6. Stop 70 is at 3.
- Residual risk (not a code finding): on this simulated controller, parts 1-2 cannot discriminate. The effective start is at reserve + 5 with a 40 kW set, so SOC never reaches the reserve: breaches are 0 and unserved is 0 on all 15 cases. No case comes near parts 3 and 4 either, so every setting is admitted. On this season the rule says only "no harm found". The choice among settings, and the reserve-25 setting that turns from REJECTED to admitted with 11 dawn days below 35 % (7 new), rest on `6c` and on the owner seeing the dawn information.

**4. Restatement.** I checked every numeral in lines 396-418 against packet §5. Each one is listed and of a stated kind. Scanned for 330, 120, 2,916, REJECTED, "0 of 61", dawn PASS/FAIL, 12.00, 262, 90.00, 2,286, 2,166, 15.6, 1.70, 210, 20 L, 68, 150 L, 195, `fig:`, "design value", "rule of three": no hit, apart from "−0.2 points" and "−5.2 points" matching "2 points".
- The two kind-1 calls are acceptable. The 12 is §4.1's declared horizon ("Horizon: 12 months unless a contract sets it", line 384), and the formula is `6c`'s. The 10 % tie is not strictly one of the four kinds, but D-0K4.29 keeps it by name, as `6c`'s, so it stands. A tidier tag would be "kept by D-0K4.29", not kind 1. No fix needed.
- The negative control's new words, "Kisiwa has no candidate running (OR-MG-2, a record fact)", are supported by line 207 ("Kisiwa, 0 candidate minutes (OR-MG-2)").
- Left for 0K4m, correctly: line 5 (210 L, 20 L, 68 L, 4-of-61, 0-of-61 as design values) and §4.3 (68 L, 395.00, 3,540.00). Also left, and not named in the packet: line 755's C3 row (330, 2,916.00 "(design value)") and `phase-plan-and-acceptance.md:144`'s OR-MG-1 "KOB-RESERVE rejected by dawn adequacy". The latter now contradicts the admitted reserve-25 (L4).
- `check_manifest.py`: H9 4496 against 4502, the 6 removed anchors. Spec §2.5 allows it, and the manifest is 0K4m's (D-0K4.15). Confirmed.

**5. Reproducibility.** Both headers hold commit `6fd0d6bb6b17…` (the code after it changes only docs: `git diff --stat 6fd0d6bb6 HEAD` touches no code), `mini-grid/8`, `v2`, `season_inputs_digest` `465ab6e0…f4cdb1a8` (= `V2_INPUTS_DIGEST`, `host/tests/test_0k4c_season_v2.py:39`), site trajectory digests, the four assumption strings verbatim to D-0K4.27, and on Kobo `admission_rule` (both strings verbatim). V5 and V6 pass here.

**6. Deviations.**
- V5's 14-day literals with the 3-case grid: accepted. `--days 8` on `main` is SAMPLE_TOO_SHORT (`preflight/main-kobo-8d.txt`), so the spec's literal cannot exist. V5 still asserts the 8-day refusal and the v7/v1 header. The 3 cases are the tool's own grid, narrowed, and each replay is independent of the others, so they equal `main`'s full-grid values. P7 fails V5, though by the flag-pair refusal (`2 == 0`), not the literals. That is enough for the plant.
- `MTO_ASSUMED` is a per-component dict with basis rows, like `ASSUMED_PROPERTIES`: accepted. It is the shape `mto_site_v2` needs to append rows per component, and the frozen needs (V4) are what the study reads.

**7. Plants.** The implementer's P1-P10 evidence was read: each fails its named test. Mine, on a scratch copy of `backend/` (never in the worktree):
- R1, a full-charge date needs SOC above 100 (`>=` to `>`) in `admission_measures`: `2 failed, 9 passed` (AD7 full-charge, AD7 study). Caught.
- R2, the dawn worst taken as `max` in `_dawn`: `1 failed, 10 passed` (AD4). Caught.
- Clean copy: `11 passed`.
- The tool-side swap of `admit`'s arguments is caught by no test (by inspection; L3).

### Findings

- **L1 (Low, honesty of information; §4.2 table and MG-T2, `domain-and-decision-models.md:408`, `:418`).** Stop 70 reads "worst 34.8 %, margin −0.2 points; 4 of 61 days below 35 %". This replaced "0 of 61", so a reader will take the setting to cause 4 dawn shortfalls. They are the baseline's own 4 dates (none new), each the 5-minute step on which the generator starts at 35 %. Fix: add "(the same 4 dates as no action; the step the generator starts)". Then reserve 25 shows its 7 new dates: "11 of 61 (7 more than no action)". These are dawn information already in `study.json` (`new_dawn_days_below`), not a second figure for the same quantity. Preference-adjacent, but it bears on the owner's honesty rule.
- **L2 (Low, explanation; `domain-and-decision-models.md:415`).** "0 L a day of extra fuel at half inverter capacity (… the reduced 25 kW run burns exactly the full run's litres)" is true but bare. Next to the huller's figure, an owner may take it for a broken guard, as the builder feared. Fix: add "(at Mto's load the battery refills by mid-afternoon on every day the 25 kW cap binds, so the generator never runs differently)". This review's diagnostic is the evidence.
- **L3 (Low, missing test; `host/tests/test_0k4d_v8_study.py`).** No test reads the Kobo tool's per-case admission (`tools/kobo_replay_study.py:236`, `admission_json`). Swapping `admit(result.baseline, case)` to `admit(case, result.baseline)` would pass every test, and the swap would not change this season's output, since all relative parts are 0 = 0. I verified the evidence by hand (every part's case and baseline values equal the fields). Fix: one assertion in V5's 14-day run, or a stub in AD, that `document["cases"][i]["admission"]["parts"][k]["case_value"]` is the case's measure and `baseline_value` is the baseline's. Not acceptance-blocking: the spec's tests do not ask for it.
- **L4 (Low, residual-risk list; `packet.md` §8; evidence `kobo-61d/night-table-…txt`).**
  - (a) The packet's "left for 0K4m" list omits line 755 (330, 2,916.00) and `phase-plan-and-acceptance.md:144` (OR-MG-1 "KOB-RESERVE rejected by dawn adequacy"), which now contradicts reserve 25 admitted. Add both to the 0K4m handover.
  - (b) The night table's column "battery AC kW" holds kWh per 5-minute step: 1.781 kWh/step = 21.4 kW, matching the 0.9375-point SOC fall a step on 200 kWh. "generator kWh in step" reads `generator-output-power`. The script's comment "(3 Sep)" should read 4 Sep. The SOC column, which is what guide check 4 reads, is right. Relabel the columns.

### Not verified

- I did not rerun the 61-day Kobo study. I took the figures from its `study.json` and recomputed them, not reproduced them, except the Mto full/reduced pair above.
- I did not run the guide's 8-day `stop-70` reproduction with an own loop. V2's reader covers it, and V2 passed here.
- Full backend suite: not run (`select-tests` says full; the coordinator's).
