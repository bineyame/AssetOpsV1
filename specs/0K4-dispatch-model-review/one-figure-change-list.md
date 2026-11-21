# One figure per quantity: the change list (D-0K4.11)

Architect (Claude), 2026-11-21. The owner's rule (`owner/owner-one-figure-loyal-to-operating-world-2026-11-21.md`):
one figure per quantity, computed by the model from simulated or real inputs and labelled by its source; no
hand-entered design value shown beside it; model faults fixed in the model; two figures together only for an operator
action or a reconciliation; Kobo's stop-70 reads "Not available yet" for litres and value, with the mechanism, until
0K4 lands.

How the list was built (W6 sweep, 2026-11-21, on `fa13f254f`): `grep` for the five pack inputs (210, 20, 68, 5 L a day,
150 L), 2,916, "0 of 61", "dawn PASS", `KOB-STOPSOC`, `KIS-BATT60`, "design value" and "design estimate" across
`backend/assetops_backend`, `frontend/src`, `config`, `contracts`, `host`, `tools` and the Layer 4 pack, plus a read of
the merged replay code. One line per place: where, what it shows or serves today, the change, and the owning unit.
"Not available yet" always names the record that would fill it.

## Merged code (served or callable on `main`)

1. **No served figure.** No merged backend, frontend, config, contract, host or tool file serves or prints any of the
   five inputs, 2,916.00, "0 of 61" or "dawn PASS" (the grep found none). Nothing to change.
2. `backend/assetops_backend/runs/replay_study.py`, `CaseOutcome.dawn_verdict` (PASS/FAIL, not served): kept, and its
   docstring says it is information only, never admission. **0K4d.**
3. `runs/replay_study.py` and `runs/headroom_replay.py` on `mini-grid` v7 and season v1: their 85 L and 68 L class of
   figures come from the battery-before-generator rule. Not served. Rerun on v8 and season v2. **0K4d.**
4. `analytics/dispatch_v3.py:298-300`, the battery-support Candidate (served through 4d's `candidate_l`, fuel-cost-1
   and candidate Findings): a moment's power read as a night's energy. Fixed in the model as `dispatch-3.3`. **0K4e.**
5. The product's fuel law (`fuel_balance/rules.py`, `financials/fuel_cost_v2.py`, `structure/litres/rules.py`:
   `SFC x kWh` plus the no-load rate over idle time only) against v8's curve: two laws for one quantity once a world runs
   on v8. No world moves to v8 until the product reads the same curve. **0K4f** (queued, D-0K4.13, owner-away row 52).
6. `config/site-templates/kobo-mini-grid-60kw.yaml`: no no-load rate, minimum load or taper; SFC 0.3. These are
   declared inputs, not shown beside a figure. The template adopts the D-0K4.4 to D-0K4.6 properties with their basis.
   **0K4f.**
7. The 5c deep-dive's `candidate_l` (4d through 5b): one model figure already. It reads "Not available yet" on the
   walkthrough world (no telemetry, D-DS4.1) and moves with 0K4e wherever there is telemetry. **0K4e.**
8. Checked, not a case: the battery's declared nameplate (`sites/battery_boundary.py`, a setup fact with no model
   figure for the same quantity); 5a targets, 3A7's month reconciliation and 5c's Kisiwa disagreement (two figures that
   set up an action or a reconciliation, which the rule allows); DS4's per-Site-day figure (already one figure,
   D-DS4.30); the 0K2 and 0M packets' "design value, unchanged" columns (records of finished work; later packets
   follow D-0K4.11).

## The pack's MG-T lines and evaluator inputs (`Docs/demo-sprint/product-direction-layer4/domain-and-decision-models.md` §4.2)

9. Lines 403-404, the setting table: stop 70 "210 of the 330 candidate L", "0 of 61", "150 kWh", "dawn PASS", "2,916.00
   (design value)"; reserve 25 "20", "4 of 61", "dawn adequacy FAIL (hard)". Becomes the v8 study's figures, SIMULATED,
   with "admitted" or "not admitted (part)"; the stop-70 value reads "Not available yet (`6c` values it)". **0K4d.**
10. Line 410, the evaluator inputs "taken from calibration spikes: design values": 210 L (stop 70) and 20 L (reserve
    25). Become the Kobo v8 study's litres, SIMULATED, with assumptions. **0K4d.**
11. Line 410: the huller's 68 L. Becomes the Mto v8 study's huller litres, SIMULATED. **0K4d.**
12. Line 410: Mto's 5 L a day at half inverter capacity. Becomes the Mto v8 study's reduced-capacity litres a day,
    SIMULATED. **0K4d.**
13. Line 410: KIS-BATT60's 150 L a month of shifted fuel (195.00 at 1.30), "a flagged assumption". Reads "Not
    available yet", naming a Kisiwa battery replay, which is not in 0K4 (queue Q7). **0K4d** (text). The manifest
    figure is **0K4m**.
14. Line 412, the sensitivities and break-even (2,286.00; 2,166.00; 15.6 L a month; 1.70/kWh). Read "Not available yet
    (`6c`)": they are money on design litres. **0K4d.**
15. Line 415, vectors MG-T1 to MG-T3. Restated with the study's figures and the admission result; MG-T4 (Kisiwa's
    negative control) is unchanged. **0K4d.**

## The pack's data and companion documents (regenerated, not hand-edited)

16. `demo-site-scenario-manifest.yaml:139`, `KOB-STOPSOC.forward_replay` `{210, 120, 0, 150}`. From 0K4d's figures.
    **0K4m.**
17. `demo-site-scenario-manifest.yaml:132`, `KOB-RESERVE.forward_replay` `{20, 4}`, and `:408`'s reason "fails dawn
    adequacy safeguard". From 0K4d, with the admission reason. **0K4m.**
18. `demo-site-scenario-manifest.yaml:264`, `MTO-HULLER.forward_replay` `{3, 225, 68}`. From 0K4d. **0K4m.**
19. `demo-site-scenario-manifest.yaml:239`, Mto's `extra_l_per_day_at_half_inverter_capacity: 5` with "design value from
    calibration spike M". From 0K4d. **0K4m.**
20. `demo-site-scenario-manifest.yaml:209`, KIS-BATT60 `monthly_fuel_saving_modelled: 195.00`. Reads "Not available
    yet". **0K4m.**
21. `demo-site-scenario-manifest.yaml:330-332`, the dawn figures `{KOB-NOACT 0, KOB-STOPSOC 0, KOB-RESERVE 4}` with
    `design_value: true`. Become information beside the admission result (D-0K4.9). **0K4m.**
22. `demo-site-scenario-manifest.yaml:393-404`, the plan's `modelled_12m_change` (KOB-STOPSOC 2,916.00; total 6,088.50)
    and the sensitivity notes. Read "Not available yet" until `6c` values the SIMULATED litres. **0K4m**, then **`6c`**.
23. `demo-site-scenario-manifest.yaml:112`, Kobo's October `CANDIDATE_RUNNING` driver built on the illustration's 330
    candidate litres, a hand-entered figure for a quantity 4d computes from records. Default: "Not available yet",
    naming Kobo's October telemetry. It changes the worked month, so **owner to weigh in**. **0K4m.**
24. `derived-values.json` (29 occurrences) and `outcome-lever-capability-traceability.csv` (32): regenerated by the
    pack's own tools (`evaluate_structure.py`, `regenerate_traceability_columns.py`) from the restated manifest; never
    hand-edited. **0K4m.**
25. Companion text that restates those figures: `derivation-register.md`, `worked-portfolios.md:166-167`,
    `economic-metric-and-effect-contracts.md:78, 227, 245`, `layer4-transformation-design.md:489` (Figure: "−210 L a
    month · +150 kWh battery throughput"), `decision-loop-specification.md:241`, `delivery-plan.md:172`,
    `phase-plan-and-acceptance.md`, `demo-build-cost-plan.md`, `repo-reuse-and-gap-matrix.md`,
    `integration-source-to-canonical-design.md`. Each restated figure follows the manifest; `check_alignment.py`
    proves it. **0K4m.** `REVIEW.md`, `REVIEW-response.md` and `regeneration/` are history and stay unchanged.

## The vNEXT mock-up (`Docs/demo-sprint/product-direction-layer4/interactive-mockup-vNEXT/`)

26. `fixtures.js` (`MANIFEST`, `DERIVED`, `REPLAY_PATTERNS`, `REPLAY_VALUES` holding 210 L, 0 of 61, 150 kWh, 2,916.0,
    68 L ...). Rebuilt by `build.mjs` from the restated manifest. **0K4m.**
27. `loop-portfolio.js:269`, `DVTEXT = 'Design estimate: not yet tested on your recorded data'`, shown on the Kobo,
    Mto and EMB option cards (`loop-site.js:36-37`, `DV_OPT`, `DV_DEC`). Replaced by the figure's source label
    (SIMULATED, with the assumptions) or by "Not available yet" naming the record. **0K4m.**
28. `loop-portfolio.js:299` and `loop-decisions.js:178`, the stop-setting text (litres a month, dawn days below 35 %,
    litres × price). Reads the restated fixtures; the dawn is shown as information. **0K4m.**
29. `loop-decisions.js:57`, KIS-BATT60's `monthly_fuel_saving_modelled`. Reads "Not available yet". **0K4m.**
30. `walkthroughs.md:48`, "+$2,916.00". Restated to the mechanism with the value "Not available yet" until `6c`.
    **0K4m.**
31. `loop-site.js:36`, EMB-DEADLINE and EMB-CHEAPEST under `DVTEXT` (spike E design values). Same class: "Not
    available yet", naming spike E, until it runs. **0K4m.** KIRI's "Assumption: recovery share 80 %" (`DV_KIRI`) is a
    labelled input assumption, not a design figure for a computed quantity, so it stays, as D-0K4.7 treats the assumed
    equipment.

## Option cards (not built yet)

32. **`6c`**, the evaluator (`delivery-plan.md` row 6c; no spec yet). Its spec must: read the option's litres only from
    the replay study on `mini-grid` v8 and season v2 (later Kobo's records); admit by `runs/admission.py` (D-0K4.9);
    carry no `design_value` field in its output; before 0K4d merges, return "Not available yet" for the litres and the
    value with the mechanism sentence of D-0K4.12. **`6c` spec** (the Architect, when written).
33. **`6f`**, the decision view (`delivery-plan.md` row 6f; no spec yet). It renders one figure per quantity with its
    source label from `6c`, and the dawn as information. There is no "Design estimate" chip. Mock element: the vNEXT
    decision view's option card, as restated by 0K4m. If 6f builds before 0K4m, its spec carries `MOCK DEVIATION` (D1,
    data or feature not available) for the chip. **`6f` spec.**

## Summary by owning unit

| Unit | Places |
|---|---|
| 0K4d | 2, 3, 9-15 |
| 0K4e | 4, 7 |
| 0K4f (queued) | 5, 6 |
| 0K4m | 13 (manifest), 16-31 |
| `6c` / `6f` specs | 22 (value), 32, 33 |
| none | 1, 8 |
