# 0K4 rulings, continued (D-0K4.31 to D-0K4.37): 0K4m, the pack and mock restated once

Architect (Claude), 2026-11-21, standing in for the owner (`owner/owner-away-architect-stands-in-2026-11-21b.md`).
These rulings continue `rulings.md`, which is past the 15k cap. Unit spec: `specs/0K4m-pack-restate/spec.md`. Owner-level
calls: owner-away rows 71 to 74 (`specs/OWNER-AWAY/decisions-2026-11-21.md`). Built on 0K4d as merged (`03c665012`).

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

## Decision queue (W3; defaults applied)

| # | Question | Default |
|---|---|---|
| Q11 | The wear rate (0.08 per kWh of throughput) is a bare `[assumption]`. Should it get a D-0K4.27 basis and derivation? | Yes, but not in 0K4m (a price-block change sits inside the tenant's prices); queued with 0K4f |
| Q12 | The world-view design values (Kobo's 330/730, Mto's 5 L a day) | Move with 0K4f's world rebuild (D-0K4.35) |
| Q13 | Unit 3 (mock) merge while the owner is away | Held for the owner's look (D-0K4.37) |
