# 0K4 rulings, continued (D-0K4.31 to D-0K4.44): 0K4m, the pack and mock restated once

Architect (Claude), 2026-11-21, standing in for the owner (`owner/owner-away-architect-stands-in-2026-11-21b.md`).
These rulings continue `rulings.md`, which is past the 15k cap. Unit spec: `specs/0K4m-pack-restate/spec.md`. Owner-level
calls: owner-away rows 71 to 75 and 77 (`specs/OWNER-AWAY/decisions-2026-11-21.md`). Built on 0K4d as merged (`03c665012`).

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

## D-0K4.40 Boundary proof (c): a comment in no node is outside the view (unit 1 Known Deviation 1)

- **Ruling.** Accept header comments as a class, and amend the script to the spec's wording; the rev line stays under
  the header. (c) maps each changed line to the innermost node whose `yaml.compose` span (key start mark to value end
  mark) holds it. A comment or blank line that no root entry's span holds (before the first key, or between two root
  entries) maps to `<root>`, and `<root>` comment and blank lines are allowed. Every other line keeps the spec's test:
  forbidden when its path is inside a node the view copies, comment lines included. Two new plants on scratch copies:
  **P20**, a comment line inside Kobo's `physical`, must fail (c); **P21**, a comment line above the first key, must
  pass (c). The packet prints both, beside the per-commit table.
- **Why.** The spec forbids lines "inside a node the view copies"; the script forbade every line outside every key,
  which is stricter than the rule. The view copies parsed nodes, so a header comment is never in it, and the manifest
  keeps all its rev lines in that header. Moving the line would break the file's convention to satisfy a script
  defect. P20 proves the amendment still catches a comment inside a view node, and P21 proves the class is scoped.
- **Reverse:** move the rev line into a non-view node (for example `empty_states`' comment) and keep the stricter
  script.

## D-0K4.41 The allocator: an option that changes no money node is a candidate in every decision (Known Deviation 2)

- **Ruling.** Confirmed, stated once for both models (spec §2.2, N5):
  - an option is a candidate of a decision when it is available (N1) and meets the decision's hard bounds, or, when
    no option does and the decision declares `fallback: least_violation`, every available option is a candidate;
  - whether the option changes a money node does not affect candidacy. An option that changes no money node
    (`money_changes: false`: every money node equals its basis's) adds 0 to plan value and its one-off to spend, and it
    is listed under `not_valued_in_money`. Its zero is computed, not assumed: a gap is N1's not available, never
    chosen;
  - "take none" is a choice only where the decision is `optional: true` (or has no candidate); rank is least total
    violation, then highest value, then lowest spend; a tie keeps the first combination in declared option order,
    "take none" first.
  The evaluator drops its `must` clause and implements this text, so its code no longer depends on decision kind.
  Lakeside then takes MTO-INV-CLAIM (spend 3,660.00) as each model finds from the spec.
- **Why.** M8 finds 0 extra litres a day under the inverter limit, so the inverter paths really move no money node.
  The decision still has to be made (`optional: false`): the warranty claim is the cheapest path that meets the cover
  bound, and that is a real reason to take it. Excluding computed-zero options made the plan infeasible, which is false
  of the world. In optional decisions the rule changes no result: such an option can only tie "take none" or lose to it.
- **Reverse:** candidacy in a valued decision requires `money_changes: true`, and Lakeside reads infeasible.

## D-0K4.42 Output precision: params at six places, money at cents (coordinator's fifth point; Known Deviations 3, 4)

- **Ruling.** Both models emit each output `params` value rounded half-even to 6 decimal places (N2's rule, now for
  outputs too), and null when not available. Every money output, `value`, `value_if_admissible` and each
  `sensitivities` value included, is rounded half-even to cents once, at output, from the unrounded computation (the
  monthly change is never rounded before `x months`). Node, bound and protect outputs stay at cents, as today. The
  independent model's `r2` on params (`independent_model.py:985`) becomes the six-place rounding; line 988's `r2` on
  sensitivities stays.
- **Defects 5 and 6 need no spec change.** §2.4 defines a MODEL_PENDING entry (null on the side, with words), so
  `empty_state_problems()` must accept it. H2 must read `|` as N1 does: an alternative applies on a month only when its
  records are present there, so a history month takes `generator_l`'s fallback.
- **Why.** Params are inputs: a rate below a cent (0.094815 L/kWh) cannot be compared at cents, and six places is the
  precision the manifest states them at, so the output echoes the input losslessly. Full precision would compare binary
  float representations from two arithmetics. Money is stated in cents everywhere.
- **Reverse:** emit params at full precision on both sides.

## D-0K4.43 Green is judged at the branch head; one merge, held for the owner (amends D-0K4.37, D-0K4.39; Known Deviation 7)

- **Ruling.** Commits 2 to 5 are judged green together, at the branch head. Unit 2 cannot land first: its anchors read
  the figures commit 2 produces.
  - **Commit 2 (unit 1's end):** `check_manifest.py` fails only in `anchors()`, `documents()` and K11, and only on
    files unit 2 or 3 restates. Every other check passes. H8 and H10 are re-based in commit 2; the packet lists the
    failures by file, with the H9 ledger marked provisional.
  - **Unit 2 (commit 3)** takes every document the checker reads outside the mock, as a class: the pack's documents,
    and `Docs/go-to-market/` (`website-content.md`, `commercial-plan.md` and their `.html` twins, regenerated by their
    `render_*_html.py`). At its head the only failures are on `interactive-mockup-vNEXT/` files.
  - **Unit 3 (commits 4-5)** clears those failures. A closing **commit 6** sets `H9_BASELINE` from the ledger at the
    branch head, and the head prints `0 failed`.
  - **Order (restates D-0K4.39).** Unit 1 first. Units 2 and 3 then build in parallel on commit 2's head. Units 1-2
    are reviewed together, unit 3 after them. The branch merges once, at commit 6, and that merge is held for the
    owner's look (`USER_REVIEW_REQUIRED`; D-0K4.37's unit 3 hold now covers the branch). Size unchanged: 3.5 units.
- **Why.** The mock's `index.html` carries "Design estimate" until unit 3 rewrites its labels, so main could not be
  green after a units 1-2 merge without a K11 exemption, and an exemption would weaken the check that proves the rule.
  One merge keeps main green at every merge. Nothing on main waits on units 1-2: 0K4f follows the 5c walkthrough.
- **Reverse:** merge units 1-2 on review with K11 scoped off `interactive-mockup-vNEXT/` until unit 3.

## D-0K4.44 The pending slice is 0K4f; `queued_slices` is the place (Known Deviation 8)

- **Ruling.** The mechanism is accepted: a slice outside the fortnight is declared in `empty_states.queued_slices`,
  never in `plan_model.py` SLICES. The entry is wrong, and so was spec §2.4: 0K4e is merged (`704124784`), and 4d is
  built. What is pending is the world on v8, with Kobo's October readings for dispatch-3.3 to classify: **0K4f**
  (D-0K4.13). The class fix, swept over the spec, the manifest and both models:
  - every MODEL_PENDING entry names slice `0K4f`, and `MODEL_PENDING` reads "a computed leaf whose model has not yet
    run on this world's records";
  - Kobo's `factor_sources` words, the finding's record and the bridge basis end "(0K4f)", not "(0K4e, 4d)";
  - `queued_slices` drops the `0K4e` row and declares `0K4f: {name: "The fuel law and the worlds on v8: the product's
    fuel law reads v8's curve, the Kobo template and DS2's telemetry writer adopt v8, the demo database is rebuilt,
    and Kobo's October readings are classified by dispatch-3.3", lane: STR, units: 2, deps: [0K4e, 4d]}`.
- **Why.** A missing-record entry must name the unit that would fill it. A merged slice can fill nothing, and a typed
  row for it with a made-up size is a design value in the plan.
- **Reverse:** keep the `0K4e` row and the words of D-0K4.35.

## Decision queue (W3; defaults applied)

| # | Question | Default |
|---|---|---|
| Q11 | The wear rate (0.08 per kWh of throughput) is a bare `[assumption]`. Should it get a D-0K4.27 basis and derivation? | Yes, but not in 0K4m (a price-block change sits inside the tenant's prices); queued with 0K4f |
| Q12 | The world-view design values (Kobo's 330/730, Mto's 5 L a day) | Move with 0K4f's world rebuild (D-0K4.35) |
| Q13 | Unit 3 (mock) merge while the owner is away | Held for the owner's look (D-0K4.37) |
| Q14 | Kobo's settings: absolute litres, a share, or Not available yet (R2) | Not available yet until the model runs on Kobo's October as recorded (D-0K4.38); owner asked to confirm on return |
| Q15 | MTO-WELDING's typed `break_even_tariff_usd_per_kwh: 0.42` (from the old fuel rate; not in §2.3) | A computed quantity typed by hand, so a design value (§1.1): removed from the row in commit 2; each reader (unit 2 documents, unit 3 mock) shows the evaluator's welder value instead (spec §2.3, rev 3) |
| Q16 | `demo_workflow` version 1 loses KOB-STOPSOC and its two Actions | Follows the evaluator (§2.3, do not choose or predict); units 2 and 3 tell Kobo's story as the settings admitted, litres and value Not available yet |
| Q17 | `replay-studies.json` committed in 1b, not 1a | Accepted: 1a stays labels only (R5) |
| Q18 | Whole-branch merge held for the owner (D-0K4.43) | Held; owner asked to confirm on return |
