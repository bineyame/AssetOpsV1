# 0K4 rulings, continued (D-0K4.31 to D-0K4.39): 0K4m, the pack and mock restated once

Architect (Claude), 2026-11-21, standing in for the owner (`owner/owner-away-architect-stands-in-2026-11-21b.md`).
These rulings continue `rulings.md`, which is past the 15k cap. Unit spec: `specs/0K4m-pack-restate/spec.md`. Owner-level
calls: owner-away rows 71 to 75 (`specs/OWNER-AWAY/decisions-2026-11-21.md`). Built on 0K4d as merged (`03c665012`).

## D-0K4.31 The pack's numbers are of four kinds; the replay inputs come from a committed extract

- **Ruling.** Every design value in the pack and the mock, and every figure computed from one, becomes one of four kinds:
  - a declared fact;
  - a v8 study figure (SIMULATED, MODELLED, with the study's assumptions);
  - "Not available yet", naming its record or unit;
  - an admission-rule line, or information beside it.
- **How the inputs are held.**
  - The study figures enter through `replay-studies.json`, which `extract_replay_studies.py` writes from 0K4d's two
    `study.json` files. Each param names its study, case and field (`source:`). The manifest's `replay_studies:`
    block, which replaces `calibration_spikes:`, carries each study's identity, checked against the extract (K2, K3).
  - `design_value` is removed as a key, and "design value" and "design estimate" as words (K1, K11).
  - The evaluator gains one form for a gap, `unavailable("<record words>")`. It never collapses a side. Every node
    that does not read the gap still evaluates (N1).
- **Why.** D-0K4.29 applied the owner's rule to §4.2. This is the same rule as a class over the pack, with the
  numeral-by-numeral check made executable. The extract is committed because evidence is purged after two weeks, and a
  figure must stay reproducible from its recorded source.

## D-0K4.32 Money on SIMULATED litres is the evaluator's figure (amends D-0K4.29's Value cells; owner-away row 71)

- **Ruling.** Where an option's litres or kWh come from a v8 study, the pack's evaluator values it from those figures
  and the declared prices, quotes and wear rate. That covers KOB-STOPSOC, KOB-RESERVE, MTO-HULLER, MTO-WELDING and
  the MTO-INV paths.
  - The value is a figure, labelled MODELLED on SIMULATED v8 inputs.
  - The plan chooses among admitted options by value, as before.
  - §4.2's Value cells, MG-T2's value and MG-T3 change from "Not available yet (`6c` values it)" to the evaluator's
    anchored figure.
  - `6c` still computes the product's figure, by the same arithmetic.
  - The `feasible_fuel_160l` sensitivity goes: it was a design litre.
- **Why.** The owner's words: "Until 0K4's corrected model lands, Kobo's stop-70 option reads 'Not available yet' for
  litres and value". The model has landed, so the value is the model's figure from simulated inputs, with its source.
  D-0K4.29 was written before 0K4d ran and before this pass regenerated the evaluator. Keeping a gap where
  the inputs and the arithmetic exist would hide what the owner most wants visible: economic usefulness.
- **Reverse:** replace the four option values with `unavailable("6c values it")` (N1). The plan then leaves them out.

## D-0K4.33 The admission rule replaces the dawn bound in the pack

- **Ruling.**
  - The MINI_GRID bound `dawn_adequacy` and the node `replayed_dawn_days_below_safeguard` are removed.
  - A bound `admission` on the option-only leaf `admission_parts_failed` (max 0) takes their place. Its value is the
    study's count of failed parts.
  - The dawn readings (worst 05:00 SOC, days below 35 %, new days against no action), the lowest charge, the most
    starts in a day and the longest run without a full charge travel as the option's `information`, copied from the
    extract and never bounded.
  - Kobo's October record leaf `dawn_days_below` stays as it is.
- **Why.** Owner default 1 (D-0K4.9): the dawn is information, never a gate. A bound over a leaf of option-only replay
  information mixed a 61-day replay count with an October record (no action read 0 against stop 70's 4, which are the
  baseline's own 4 days). Option information keeps the two apart.

## D-0K4.34 Mto's litres are litres per customer kWh times the declared load (amends D-0K4.28 I6 for the pack; owner-away row 72)

- **Ruling.**
  - The huller's and the welder's extra litres are the M8 study's `litres_per_customer_kwh` times the option's
    declared kWh a month (load x hours x days). That puts revenue and fuel on one basis.
  - The inverter paths read M8's `extra_fuel_l_per_day`, which is 0, with its reason as information.
  - §4.2's huller line is restated to this definition. The "window x 30 / 61" month stays for Kobo's settings, which
    have no declared day count.
- **Why.** The study's customer has 44 days in 61 (21.6 a month), while the pack declares 22 days. Mixing the study's
  litres a month with the pack's revenue a month puts the two figures on different bases. For the welder that mismatch
  alone turns the margin's sign. One basis per option is the honest form.

## D-0K4.35 The world view is not edited; Kobo's candidate split reads "Not available yet" (owner-away row 73)

- **Ruling.**
  - 0K4m edits no byte of the manifest view that the world generator reads (`view.py` TOP/SITE/PERIOD keys) and does not
    touch `history.json`. Proof: H11, K8 and the view hash.
  - Kobo's October `necessary_l: 730, candidate_l: 330` and Mto's `physical.extra_l_per_day_at_half_inverter_capacity: 5`
    stay in the file for 0K4f, which rebuilds the world (D-0K4.13), and nothing reads them.
  - The evaluator reads Kobo's split as `unavailable(...)` through `factor_sources`, outside the view. The structure's
    `diesel_l` becomes `generator_l + unexplained_l + extra_l`, with `generator_l` = recorded litres less the unexplained
    residual. Fuel, contribution, the variance and the portfolio bridge are therefore unchanged.
  - Kobo's two 3.2 bridge rows become one `GENERATOR_RUNNING` row with the split "Not available yet".
  - Class rule (K10): every site whose actual record holds a non-zero `candidate_l` gets the same override.
- **Why.**
  - 330 L is a dispatch-3.2 classification typed into the world, not produced by any model. §4.2 already reads Kobo's
    candidate litres "Not available yet". Change-list row 23 asked the owner, and this is the stand-in answer: its default.
  - Editing the world view would change the DS1b records, the 3A3 exports and the walkthrough world, which D-0K4.13
    keeps as built until 0K4f.
  - Zero candidate litres (Kisiwa, Mto) stay. dispatch-3.3 only turns Candidate points Indeterminate, so a 3.2 zero is
    a 3.3 zero.
- **Reverse:** remove Kobo's `factor_sources`, and the 330 returns.

## D-0K4.36 Embakasi without spike E; KIS-BATT60 not available (owner-away row 74)

- **Ruling.**
  - EMB-DEADLINE's missed departures come from the structure's own energy check (`buses_short_per_night`), the
    mechanism EMB-CHEAPEST already uses. `feasible_nights 31` (design value E) and the "21-bus night … 406 kW" clause
    go, and per-bus departure timing reads "Not available yet (the Embakasi schedule replay, not run)".
  - Embakasi's money does not move: no money node read `feasible_nights`.
  - KIS-BATT60's shifted litres are `unavailable("a Kisiwa battery replay (queue Q7)")`. Its value is null and it is
    never chosen.
- **Why.** Spike E never ran. The figure it stood for, nightly energy feasibility, is computable from records the
  structure already holds, so it becomes the model's figure. Per-bus timing is not computable from records, so it is
  a gap. Q7 stands for Kisiwa.

## D-0K4.37 0K4m's size, units and order (amends D-0K4.1's 0.75)

- **Ruling.** 2.75 units in three units of work:
  - unit 1: extract, checker, manifest, evaluator, regeneration and re-base (1.5);
  - unit 2: companion documents and the sweep (0.5);
  - unit 3: the mock (0.75).
  It builds now (0K4d merged at `03c665012`), in any free lane, and does not gate the 5c walkthrough. Units 1-2 merge
  on review. Unit 3's merge is held for the owner's look (owner-away terms: UI-facing changes wait).
- **Why.** D-0K4.1's 0.75 assumed a value-for-value swap. The handshake read of the pack found three things that cost
  more: the evaluator needs a gap form, the dawn bound becomes an admission bound, and the world-view boundary needs
  its own proof. H9's re-base also needs a ledger. The sum, 2.75, is the honest size.
- **Total 0K4:** 13.25 units (11.25 + 2.0).

## D-0K4.38 The world-month rule: Kobo's settings read "Not available yet" (amends D-0K4.32 for Kobo; owner-away row 75)

- **Ruling (0K4m handshake R2).**
  - A study figure reaches the world's month only as a rate on a quantity the option itself declares: litres per
    customer kWh times the option's kWh (MTO-HULLER, MTO-WELDING), or extra litres per day times the option's days at
    reduced capacity (MTO-INV paths).
  - An amount of a site's existing running from a replayed season is never applied to the world's record of another
    month, either as litres or as a share. KOB-STOPSOC's and KOB-RESERVE's litres, added throughput and value read
    "Not available yet (a dispatch replay on Kobo's October as recorded; 0K4f)". Neither is chosen.
  - Both settings keep their admission result and dawn information, stated in the replay's frame ("of 61 replayed
    days"); no amount a month travels as information. §4.2's Kobo Value cells keep "Not available yet" with the new
    words; D-0K4.32's valuation stands for the Mto options. Check K12 enforces the rule (spec §1.3).
- **Why, in plain terms.**
  - K8's 212.751 L is what stop 70 saves a month in a simulated season whose generator burns about 1,442 L a month.
    Kobo's October, the world the screens show, burns 1,060 generator litres. Taking 212.751 off 1,060 claims a 20 %
    cut; the model found about 15 % on the season it ran. The figure is true of the season, not of Kobo's October, so
    on Kobo's October it is out of touch with the operating world.
  - The share form (15 % of 1,060) assumes the saving scales with total running. No model ran that assumption: it is
    a workaround that looks like a model figure. The owner's rule says a model mismatch is fixed in the model, not
    bridged with arithmetic.
  - The `avoided_l <= generator_l` check would only catch the absurd case; it does not make the figure loyal.
  - "Not available yet" is the owner's own answer for stop 70 until the model lands on this world ("loyal to the
    operating world"), and it is what the rehearsed screens already say (row 66), so the pack, the mock and the
    product agree. The mechanism stays visible: both settings pass the operating checks in the replay.
  - Mto is different on both counts: its options declare their own quantity (the huller's kWh, the days until the
    inverter is back), and its season burns about what Mto's October records (packet basis print). Its valued figures
    stand.
- **Reverse:** give KOB-STOPSOC's and KOB-RESERVE's `avoided_l` and `added_throughput_kwh` their K8 `source:` again
  and drop K12's `scaled_to_30_days` clause; the 212.751 L and its money return. When 0K4f runs the model on Kobo's
  October as recorded, the params take that study's source and K12 passes unchanged.

## D-0K4.39 0K4m handshake answers and size (amends D-0K4.37's 2.75)

- **Ruling.** R1, R3 to R6 and I1 to I6 take their handshake defaults, folded into spec rev 2, with these settings:
  - R1: the boundary proof is (a) the view hash, (b) `world_history.py check`, (c) a changed-line to YAML-path map,
    at every commit. I1: `VIEW_HELD` is acceptable for the four view paths that keep a design value for 0K4f. It is
    proven by four checks: the list equals what K1 finds, every entry lies inside the view, K7 covers the mock's
    sources, and K11's skip of the embedded `MANIFEST` literal is guarded by an equality check.
  - R4: not available is its own value; `|` never falls through it; `evaluator()` compares key presence (P16, P17).
  - R5: commit 1 splits into 1a (labels only, count unchanged) and 1b; the H9 ledger is the labels' per-section
    multiset diff.
  - I2: `generator_l` falls back to `record.necessary_l + record.candidate_l` on history months; Kobo's override is
    side-free (plan split null too).
- **Size.** 3.5 units: unit 1 1.75 (commits 1a, 1b, 2; adds K12, `VIEW_HELD`, the labels and the boundary script),
  unit 2 0.75 (I4's added files and the motivation figures), unit 3 1.0 (`replay_values.py` rewritten, chip and day
  count from fixtures). Unit 1 builds first; units 2 and 3 may then build in parallel. Total 0K4: 14.0 units.
- **Why.** The handshake found real gaps in the proof (semantic hash, null against absent, unlabelled H9) and in the
  place lists. Each default closes its gap with a check, not a note, and the size follows the added work.

## Decision queue (W3; defaults applied)

| # | Question | Default |
|---|---|---|
| Q11 | The wear rate (0.08 per kWh of throughput) is a bare `[assumption]`. Should it get a D-0K4.27 basis and derivation? | Yes, but not in 0K4m (a price-block change sits inside the tenant's prices); queued with 0K4f |
| Q12 | The world-view design values (Kobo's 330/730, Mto's 5 L a day) | Move with 0K4f's world rebuild (D-0K4.35) |
| Q13 | Unit 3 (mock) merge while the owner is away | Held for the owner's look (D-0K4.37) |
| Q14 | Kobo's settings: absolute litres, a share, or Not available yet (R2) | Not available yet until the model runs on Kobo's October as recorded (D-0K4.38); owner asked to confirm on return |
