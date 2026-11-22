# 0K4 rulings, continued (D-0K4.31 to D-0K4.56): 0K4m, the pack and mock restated once

Architect (Claude), 2026-11-21, standing in for the owner (`owner/owner-away-architect-stands-in-2026-11-21b.md`).
These rulings continue `rulings.md`, which is past the 15k cap. Unit spec: `specs/0K4m-pack-restate/spec.md`. Owner-level
calls: owner-away rows 71 to 75 and 77 to 79 (`specs/OWNER-AWAY/decisions-2026-11-21.md`). Built on 0K4d as merged (`03c665012`).

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

## D-0K4.45 The product-parity seam: 0K4m leaves the structure layer as on main; it moves with 0K4f (unit 1 review H1; amends D-0K4.35, D-0K4.44; owner-away row 78)

- **What the tests assert (measured, 2026-11-22).** Host runner, DB-free (`ASSETOPS_TEST_DATABASE_URL` set to an
  unreachable sentinel, so no database is touched), one file per run, branch head `7e461e491` against main `1d4713cc8`:
  121 failures that main does not have, in eight files. The reviewer's 55 plus the two world-tool test files, which use
  fakes and need no database:

  | File | New failures | What it asserts against the pack |
  |---|---|---|
  | `backend/tests/test_3b1_structure_registry.py` | 4 | registry nodes and expressions == `structures.MINI_GRID`; leaf set == `factor_map.MINI_GRID`; `empty_states.leaf_sources`; `home_categories.nodes`; row order |
  | `backend/tests/test_2a_canonical_manifest_parity.py` | 2 | the contracts' canonical leaf catalogue == `factor_map` per structure |
  | `backend/tests/test_3b3_structure_evaluate.py` | 40 | the product's evaluated sides == `derived-values.json` `sites` and `missing-records.json` `sites` to the cent; 33 use Kobo's side values as inputs (`Decimal(None)` on the nulled split); `KeyError: 'generator_l'` |
  | `backend/tests/test_3b4_observer.py` | 7 | observer inputs built from the pack's Kobo sides (`Decimal(None)`) |
  | `backend/tests/test_5a_targets.py` | 1 | the portfolio's plan sums == `derived-values.json` `portfolio` (`KeyError: 'necessary_l'`) |
  | `simulator/tests/world/test_records.py` | 1 | T9: Kobo's plan ASSUMPTION entry in `missing-records.json` lists `necessary_l` |
  | `backend/tests/test_ds4_world.py` | 9 | `tools/world.py` C4 oracle over payloads built from `derived-values.json` `sites`; C4's contract key set == the pack's node set |
  | `backend/tests/test_wk_walk_world.py` | 57 | the walk refuses because the fake world check's C4 reads FAIL (`assert 4 == 0` in the fixture) |

  Six other readers pass on both (`test_3b2_findings_pinned`, `test_3b6_cold_ev_structures`, `test_5b_attribution`,
  `test_4b_money_leaves`, `simulator/tests/world/test_cli.py`, `host/tests/test_0m_mto_headroom.py`).
  `test_ddr_rehearsal_postgres.py` reads only the view through `world_history.py`, and the view is unchanged. Main
  itself fails two tests in this set (`test_3b1…::test_t1_leaf_sources_absence_and_words_equal_the_manifest`,
  `test_3b3…::test_t6_each_state_yields_its_leaf_value_on_its_own_record`). They are not 0K4m's, and the coordinator
  routes them separately.
- **The surface (the class).** The product, its world and its world check read these parts of the pack and nothing
  else: in the manifest, `structures`, `factor_map`, `empty_states.leaf_sources`, `home_categories.nodes`,
  `home_categories.findings`, `chain_model`, `history.rules` and the view; in `derived-values.json`, `sites` and
  `portfolio`; in `missing-records.json`, `sites`. `tools/world.py` C4 judges every live product world against
  `derived-values.json` `sites`. A restated `sites` therefore fails the next `world check`, and from then on the WK
  walk refuses its world (W1).
- **The options weighed.**
  - **(b) Bring the product in.** This needs the contracts' leaf catalogue, the MINI_GRID registry and rows
    (`backend/assetops_backend/structure/`, version 5), the evaluator, the observer, targets, the simulator's world
    records, `tools/world.py` C4_CONTRACT, product plan targets for Kobo's nulled split, the screens that render the
    dawn safeguard node, and the eight test files. About 3 units. Then a world build: `backend/assetops_backend`,
    `contracts/`, `simulator/assetops_simulator` and `tools/world.py` are the ladder's CODE_PATHS, so L1 goes stale,
    and WK runs again. It also needs a UI hold. This is 0K4f's work done early, without 0K4f's world on v8.
    Rejected.
  - **(c) Pin the tests to the pre-0K4m pack.** This needs frozen copies under `backend/tests/fixtures/` and eight
    repointed test files. The world definition's `derived_values` would also have to point at the frozen copy, or C4
    fails. The definition is hashed into L1, so that means a world build too. About 0.5 unit plus the build. It
    leaves two oracles: the product would be certified against a pack the pack has replaced. That is two figures for
    one quantity, which the owner's rule forbids. It is a workaround. Rejected.
  - **(a) Leave the structure layer unchanged.** Chosen.
- **Ruling.**
  - 0K4m changes none of the surface above. Its `derived-values.json` `sites`, `portfolio` and `history`, and its
    `missing-records.json` `sites`, are byte-equal (as parsed JSON) to main's.
  - The structure-layer restatement moves to **0K4f**, as one slice with the product and the world. It covers:
    - `generator_l`;
    - Kobo's split, read from dispatch-3.3's classification on the rebuilt world, so no override is needed;
    - the dawn safeguard node retired;
    - an admission leaf in the structure.

    0K4f rebuilds the world anyway, so one build covers it.
  - Concretely, at a new commit **2b** on the branch (spec §2.3a):
    - Restored as on main: `structures.MINI_GRID` (with `diesel_l` and `replayed_dawn_days_below_safeguard`),
      `factor_map.MINI_GRID`, `empty_states.leaf_sources.MINI_GRID` and `home_categories.nodes.MINI_GRID`. The same
      goes for the rows of the dawn node in `empty_states` and the traceability CSV, `home_categories.decisions`
      (lever `candidate_l`) and `bridge_drivers`. So do Kobo's two bridge rows (`CANDIDATE_RUNNING`,
      `EVENING_LOAD_GROWTH`) with their basis, `findings_expected.GENERATOR_SUPPORT_CANDIDATE`, and the kobo-candidate
      Finding.
    - Removed: Kobo's `factor_sources`, its MODEL_PENDING entries, `MODEL_PENDING` itself (from `CAUSES`, from the
      vocabulary and from both models) and the `0K4f` row of `empty_states.queued_slices`. Nothing else uses any of
      them. D-0K4.44's mechanism stays the rule for a future pending slice.
    - Kept: the option-layer restatement. KOB-STOPSOC's and KOB-RESERVE's `changes` read
      `candidate_l: "candidate_l - avoided_l"`, and `avoided_l` and `added_throughput_kwh` stay `unavailable(...)`
      (D-0K4.38). KIS-BATT60's reads `necessary_l: "necessary_l - shifted_fuel_l"`, and `shifted_fuel_l` stays
      `unavailable(...)`. `option_money_factors` follow: KOB-STOPSOC and KOB-RESERVE `[candidate_l,
      battery_throughput_kwh]`, KIS-BATT60 `[necessary_l]`.
    - The admission count becomes an option-only leaf in the pack's existing option frame:
      `evaluation.forward_baseline.MINI_GRID: {reduced_days: "0", admission_parts_failed: "0"}`. The `admission` bound
      and each setting's `admission_parts_failed: "admission_parts_failed_option"` change are unchanged. Doing nothing
      fails no admission part, so its count is 0.
    - The dawn bound stays removed (`evaluation` is pack-only), and `replayed_dawn_days_below_safeguard` leaves
      `protect_nodes.MINI_GRID`, so no option reports a dawn count beside its `information`. The node stays in the
      structure, reading the world's recorded `dawn_days_below_safeguard`, until 0K4f.
    - OR-MG-1 reads: "Kobo: candidate running {fig:sites.lakeside-power/Kobo.actual.nodes.candidate_l} L as the world
      records it (dispatch-3.2; dispatch-3.3 re-classifies it in 0K4f); both settings admitted on K8's replayed days;
      their litres and value Not available yet (a dispatch replay on Kobo's October as recorded, 0K4f)".
  - **Checks.**
    - **K10 is retired.**
    - **K13 (the seam)** is a section-15 check that the canonical sha256 (`json.dumps(sort_keys=True,
      separators=(",", ":"))`) of each surface part equals a literal computed from main's files (`1d4713cc8`) and
      written out in full. It covers the seven manifest subtrees above (parsed YAML), `derived-values.json` `sites`,
      `portfolio` and `history`, and `missing-records.json` `sites`.
    - **Boundary proof (d)** prints K13 per commit from 2b on.
    - **Merge gate.** At the branch head, the eight files above, run DB-free as measured here, fail exactly main's
      failures, by node id.
    - **Plants.** P23 (`generator_l` re-added to `factor_map.MINI_GRID`) and P26 (Kobo's `factor_sources` re-added)
      must each fail K13.
- **Why.**
  - The pack's derived sides are the product's oracle (W2), so the owner's rule applies across the seam: the product
    and the pack show one figure for each quantity they share, at every merge. (a) is the only option that keeps that
    true without a product slice, and it costs no world build.
  - Kobo's 330 L stays a figure of the simulated world's own record, labelled by its source. The product already shows
    the actual split blank (C4 class B, NOT_CONNECTED), so no screen pairs 330 with another figure.
  - The owner's explicit instruction is untouched: the settings' litres and value stay "Not available yet".
  - D-0K4.35's override was a stand-in default (row 73) for exactly this split. It assumed the derived sides were
    pack-only, and they are not.
- **DS4 ladder.**
  - (a) touches no CODE_PATHS, no `backend/migrations` and no definition file, so the L0, L1 and L2 keys are unchanged
    and nothing is rebuilt.
  - The L2 check does go stale, because the `derived-values.json` and manifest blobs change. After the held merge and
    before the next WK run, the coordinator reruns `world check` in a quiet DB slot. C4 must PASS, since the sides are
    main's. A FAIL is a stop, and it goes to the Architect (D-WK.10).
  - Correction to the brief: a change under `backend/tests/` or `simulator/tests/` does not stale L2. Only CODE_PATHS,
    migrations and the definition do. CHECK_CODE files stale the check only.
- **Reverse:** restore commit 2's structure-layer restatement, and take (b) or (c) with it.

## D-0K4.46 N5's "no candidate" covers every decision kind, protective included (unit 1 review L1)

- **Ruling.**
  - "Take none" is a choice in any decision, valued or protective, that has no candidate. That means every option is
    not available (N1), or no available option meets the hard bounds and the decision declares no
    `fallback: least_violation`.
  - The plan is never infeasible for that reason alone.
  - The protective decision's `protective_choices` entry then reads `{chosen: null, admissible: [], how: "no
    candidate: every option is not available"}` or `"no candidate: no option meets <hard ids, comma-separated, in
    declared order> and the decision declares no fallback"`, with no `trade_off` key.
  - Both models implement this. The evaluator's `next(...)` at `:587` takes a default of `None`, and the model's
    `return None` at `independent_model.py:1047-1049` goes. `evaluator()` compares `protective_choices`, presence
    included.
  - Plant **P24** (scratch copy): every option of one Lakeside protective decision is set `unavailable("probe")`. Both
    models take none with the first `how` and give equal plans, and nothing crashes.
- **Why.**
  - An option that cannot be evaluated says nothing about whether a plan exists. Reading the whole plan as infeasible
    would hide every other decision's result.
  - Taking none, with the reason stated in the protective entry, is the honest statement: nothing in this plan protects
    that asset, and here is why. One rule for every kind is what D-0K4.41 already says.
- **Reverse:** a protective decision with no candidate makes the plan infeasible in both models.

## D-0K4.47 N1's option words and bound rules are stated in the spec (unit 1 review L2)

- **Ruling.** The handoff's rule becomes spec text (spec §2.2 N1, rev 4), so both models are held to the spec, not to
  one builder's table:
  - an option's `not_available` words are those of the first not-available param, in declared `params` order. If no
    param is not available, they are the value's words: the monthly change's, then the one-off's. If neither is, they
    are the words of the first not-available bound, in `evaluation.bounds.<vertical>` order;
  - a not-available value's words are those of its leftmost not-available operand;
  - a not-available operand wins over a missing record, on either side of any operator except `|`, whose right side
    runs only on a missing record;
  - a bound over a not-available node has `violations.<id>: null`, and the option is not available;
  - `admissible` is null when any hard bound of the option's decision has a null violation. Otherwise it is true
    exactly when the hard violations sum to 0.

  The packet records that the checker fixes `bcf9f48c0` and `09b6a8757` came from the evaluator side.
- **Why.** Where the spec is silent, both models carry one builder's choice, and an error there would pass the
  checker. These are the rules both models already implement. Stating them makes the agreement independent.
- **Reverse:** none needed. This is a record ruling, and it changes no behaviour.

## D-0K4.48 A sensitivity follows the option's value (unit 1 review L6)

- **Ruling.** Each `sensitivities` value is null when the option's `value` is null, whether the option is not
  available or not valued in money (`money_changes: false`). Both models do this in commit 2b. MTO-INV-CLAIM's and
  MTO-INV-BUYNOW's `diesel_minus_20pct` then read null. Units 2 and 3 render no sensitivity for an option that has no
  value.
- **Why.** A sensitivity is the option's value under a changed input. A money figure under diesel −20 % for an option
  the plan lists as not valued in money would be a second figure beside a gap.
- **Reverse:** sensitivities computed regardless of `money_changes`, and hidden by units 2 and 3.

## D-0K4.49 Review fixes confirmed; 0K4m 4.0 units, eight commits, one held merge (amends D-0K4.43; unit 1 review M1, L3-L5)

- **Ruling.**
  - **M1, L3 and L4 need no ruling. The builder's fixes at `02cc14fee` are confirmed:**
    - M1: no must-take filter;
    - L3: one rounding, from unrounded sums;
    - L4: stale comments. Under D-0K4.45, the Kisiwa and Mto bridge bases keep main's driver mapping, so L4's
      re-mapping note lapses, and the bases take `{fig:}` placeholders.
  - **The M1 probe becomes plant P25,** a K9 self-test written by a model-side builder. All four MTO-INV
    `extra_l_per_day` are set `unavailable("probe")`. Both models give equal plans, and the plan is feasible.
  - **L5:** the ledger is rebuilt at commit 6, as planned.
  - **Decision-history anchors (residual risk; Q22's default).** In `design-questions-and-decisions.md` and
    `decisions-register.md`, a row dated before 21 Nov keeps its words and loses its `{fig:}` or `<!--fig:-->` anchor.
    A row from 21 Nov on is anchored to the current figure. If `documents()` then flags an untagged history figure,
    both files join `documents()`'s history exclusion by name, as they joined K11's.
  - **Order and size (amends D-0K4.43).**
    - Commit 2b (unit 1 rework, 0.5 unit) comes before units 2 and 3. It holds D-0K4.45 to .48 and plants P23 to P26.
      An evaluator-side builder does the manifest and the evaluator; a model-side builder does `independent_model.py`
      and `check_manifest.py`, sharing no code (W2).
    - Units 2 and 3 build on 2b's head.
    - Commits: 1a, 1b, 2, 2b, 3, 4, 5, 6.
    - The branch still merges once, at commit 6, held for the owner. The head must print `0 failed`, pass K13, and
      pass the DB-free product-parity set of D-0K4.45.
    - After the merge, the coordinator reruns `world check` before the next WK run (no build).
    - Unit 1 is now 2.25 units, and 0K4m is 4.0 (was 3.5).
    - 0K4f grows by the structure layer, about 1 unit: its size goes from 2 to about 3, to be specced with 0K4f.
- **Why.** Units 2 and 3 anchor figures from `derived-values.json`, so they must read 2b's figures, not commit 2's.
  One merge still keeps main green at every merge.
- **Reverse:** merge with D-0K4.43's order and accept H1 on main (red).

## D-0K4.50 The vocabulary guard stays; §4's copy says "simulation", not "replay" (unit 3 pre-flight Q1)

- **Ruling.**
  - `tools/vocab_check.cjs` keeps its `replay(?:ed|s)?` ban on loop screens. Spec §4's exact copy changes instead. These
    are the new exact strings (rev 5):
    - `SIMTEXT` = `'Simulated: from a simulation of a declared ' + <days> + '-day season, not your recorded data'`.
      `<days>` follows D-0K4.53.
    - KIS-BATT60: `'Not available yet: needs a simulation with a Kisiwa battery'`.
    - Embakasi per-bus timing: `'Not available yet: needs a simulation of the charging schedule'`.
    - Kobo's two settings (litres and value): `'Not available yet: needs a simulation of Kobo''s own October'`.
    - The popover (`loop-core.js:425`): `"Simulated figures come from a simulation of a declared season; 'Not
      available yet' names the record that would fill it"`.
    - The warranty floor is unchanged: `'Not available yet: needs Kobo''s battery sheet'`.
  - The class: every string the spec gives as exact copy for a loop screen must pass `vocab_check.cjs`. The builder
    runs the spec's strings through the guard before coding. A clash goes back to the Architect, and the guard never
    bends.
- **Why.** The ban came from the owner's review of the copy (19 Nov: "not using technical words that should not be
  user facing"). "Replay" is the pack's own word for a dispatch study. The spec put that word on screen, and the
  spec was wrong. "Simulated" is already the chip's word, so "simulation" keeps one word for one idea (UI standing
  brief: one interaction grammar; NN/g heuristic 2, match the user's language).
- **Reverse:** relax the guard for these five strings, which needs the owner's approval.

## D-0K4.51 Kobo's split is labelled in words on screen; the 0K4f code goes in the drawer's reviewer block (Q2; amends acceptance 5)

- **Ruling.**
  - On the mock, Kobo's candidate and necessary litres (330 / 730) read as a recorded figure. They get no "Simulated"
    chip. Beside them is this exact copy: `'as October''s records classify it; to be re-checked against Kobo''s own
    5-minute readings'`.
  - The evidence drawer for that figure keeps its existing collapsed block, `<details class="tech">For reviewers: demo
    data reference</details>` (`loop-core.js:299`). `render_text.cjs:36` removes that block from the vocabulary scan.
    Inside the block, add the line `source: world view, period.actual candidate_l / necessary_l (dispatch-3.2);
    re-classified in 0K4f`.
  - **Acceptance 5 (rev 5):** "labelled with their source and 0K4f in every document and on the mock" means the
    documents carry the code, and the mock carries its words on screen and the code in the reviewer block only.
- **Why.**
  - The builder's default said "as the simulated world records it". On the loop screens, the world's records are the
    operator's recorded data, and "Simulated" marks only figures from a study. Calling a record "simulated" would
    blur the one distinction the chip exists to draw (the owner's one-figure rule: labelled by its source).
  - Codes stay off screen (owner, 2026-10-04; UI guidance 2026-10-25: "no raw codes on screen"). The reviewer block
    is the place the mock already uses for such codes.
- **Reverse:** "0K4f" on screen, with a guard exception, which needs the owner's approval.

## D-0K4.52 Bridge-base words are fixed at the source, in the manifest: "against a target of" (Q3)

- **Ruling.**
  - The class is manifest prose that reaches a reader. Commit 2b introduced "{fig:} L against plan {fig:} L" in three
    bridge `basis` strings (`demo-site-scenario-manifest.yaml:115, 193, 249`), which breaks OD-6. Unit 3 rewords
    them in the manifest, in commit 4, to `"{fig:…actual.nodes.necessary_l} L against a target of {fig:…plan.nodes
    .necessary_l} L x {rec:…}"`. Placeholders, amounts and the rest of each string stay as they are.
  - **Sweep.** Unit 3 greps every manifest string (`basis`, `reason`, `words`, `how`) for OD-6's retired forms
    (`check_alignment.py`'s RETIRED pattern for "plan" as a target). Each hit is reworded the same way, and the packet
    lists the hits. Machine keys named `plan` stay (decisions-register item 9).
  - The mock's `PLAIN` map gets no entry for this wording (no instance patch).
  - Unit 2 uses the same wording wherever a document quotes a bridge base. The coordinator relays this ruling to
    unit 2's builder (`/opt/assetecon/AssetOpsV1-0k4mu2`). Unit 2 does not edit the manifest, so the two units
    cannot both edit it.
  - No new check is needed. `vocab_check.cjs` already guards the mock and A3 already guards the documents, and both
    already caught this. The manifest had no reader-side guard, and it now has one wording that both readers render.
  - The edit touches no K13 part. Bridge `basis` words are not in `structures`, `factor_map` or the derived `sites`
    (checked: `derived-values.json` has no "against plan"), so K13 and H11 are unaffected.
    `rendered-manifest-strings.json` is regenerated (§4).
- **Why.** OD-6 binds every reader. A fix in the mock alone would leave the documents and the mock on two wordings
  of one figure's basis, and the next reader would repeat the fault (W6).
- **Reverse:** a `PLAIN` entry in the mock and a separate rewording in each document.

## D-0K4.53 Unit 3's scope and evidence: the whole of §4; Simulated days per figure; no repo screenshots (Q4, Q5, Q6)

- **Ruling.**
  - **Q4.** Unit 3 covers all of §4. That includes the documents (`walkthroughs.md`, `fixture-mapping.md`), the tools
    (`gen_docs.cjs`, `audit.mjs`, `ux_interaction_check.cjs`, `vocab_check.cjs`, `hand_typed_scan.py`,
    `replay_values.py`) and the regenerated `rendered-manifest-strings.json`. It also covers the manifest strings in
    D-0K4.52 and nothing else of unit 1's.
  - **Q5.** Each Simulated chip's title reads the `days` of the study that its own figure's `source` names: K8 for
    Kobo, M8 for Mto, and so on, through `SOURCE_LABELS`. The popover has no day count.
  - **Q6.**
    - In the repo, `tools/run-audit.sh` runs without `--shots`, through `tools/heavy-slot.sh` with
      `/opt/assetecon/tools/pw/env.sh`. Its results feed `gen_docs.cjs` and `browser-audit.md`.
    - Screenshots come from a scratch copy of the mock folder run with `--shots`, then are copied to
      `/opt/assetecon/evidence/0K4m/u3/`. The scratch copy is deleted afterwards (temp-quota rule).
    - No file under the repo's `screenshots/` changes, and `audit.mjs` is not changed to move them.
- **Why.**
  - Q5: one figure, labelled by its own source. A K8 day count on an M8 figure would label one study's figure with
    another study's season.
  - Q6: §4 forbids `screenshots/`, and the audit tool's paths are not this unit's to redesign.
- **Reverse:** one page-wide day count; an `audit.mjs` output-directory option.

## D-0K4.54 The mock renders its own §4 copy, not the manifest's `reason` strings, for Kobo's settings and KIS-BATT60 (Q7)

- **Ruling.**
  - For these gaps, the mock shows the exact strings of D-0K4.50. It never renders the manifest's `reason`
    (`:135, 144, 207, 404-406`).
  - The manifest's reason strings stay as they are. They are the documents' and the reviewer's wording, codes
    included (acceptance 5).
  - This differs from D-0K4.52 because the two wordings are for two audiences:
    - a rule that binds every reader, like OD-6, is fixed at the source;
    - a reviewer reference, like a slice code or "dispatch replay", stays in the reviewer-facing manifest, and the
      screen gets its own plain copy.
  - The reviewer block (D-0K4.51) may quote the reason string.
- **Why.** Codes off screen (owner, 2026-10-04). Stripping the codes from the manifest would take the record
  documents need away from them.
- **Reverse:** plain manifest reasons and codes moved to a separate reviewer field, as a manifest-schema change.

## D-0K4.55 Every mock reader reads a field the regenerated fixtures carry; a figure with no source shows its gap, and the element stays (Q8; the five crashing pages)

- **Ruling.** This is one class with three cases. Unit 3 fixes all of them.
  1. **Removed fields, the cause of the crashes.** Unit 3 fixes every reader of a field that 0K4m's evaluator or
     manifest removed. That includes `forward_replay.*` (`avoidable_fuel_l`), `days_without_headroom`, `economics.*`
     (gross, wear, net, the Mto huller and welder rows, MTO-BILLING, Kirinyaga and Mwea where removed) and the removed
     break-even.
     - **The sweep.** List the keys present on main's `fixtures.js` and absent from the regenerated one, then grep the
       mock sources for each. The packet lists every reader with its new source.
     - **The acceptance.** `audit.mjs` reports `consoleErrorRoutes: 0` and `routesOk == routesChecked`. Confirmed:
       these readers are unit 3's to fix, and five crashing pages are a merge block.
  2. **A figure the evaluator gives.** It reads the evaluator's option figure (`value`, `monthly_or_horizon_change`,
     `params.*`, `sensitivities.*`, null as D-0K4.48 says) or the manifest record. Mto's welder break-even shows the
     evaluator's welder value, as Q15 already ruled.
  3. **A mock element with no source.** The element stays, keeping the mock's layout (START_HERE, O2; no
     `MOCK DEVIATION`). Its figure reads `'Not available yet: ' + <words naming the record or study>`. A prose
     sentence that only restated a removed figure is reworded without the figure, and never with a typed
     substitute.
     - Rows are never dropped. That changes the builder's default, which dropped them: the mock states missing data
       on screen, and content without a source shows as "not available yet".
- **Named places.**
  - **Kobo's verify line** (`loop-decisions.js:276`). The Operational entry becomes `'Generator time beyond need down
    on comparable days, and the four operating checks still pass over the trial (' + <n> + ' matched days before and
    after)'`. That removes the "35 % at 5 am every day" bound (acceptance 4: the dawn is information).
    - `<n>` is the leading integer of `verification_plan.baseline`, which `gen_fixtures.py` emits as
      `VERIFY[<decision>].matched_days`. That constant sits outside the embedded `MANIFEST` literal, which K11 parses
      back to the manifest. If `.after`'s integer differs, both numbers are shown.
    - The Economic and Causal entries read `verification_plan.economic` and `.causal`'s figures (the ±10 % bands)
      from the fixtures, in the mock's existing words.
  - **The wear row** (`loop-decisions.js:178`, the KOB-STOPSOC effect line). It shows the mechanism with no money:
    `'avoided litres × diesel price ' + <price> + ' − battery wear (assumed ' + <wear rate> + ' a kWh of added
    throughput) = value a month: Not available yet: needs a simulation of Kobo''s own October'`.
    - The price and the rate come from the tenant's prices in the fixtures.
    - The wear rate stays a labelled assumption (§7, Q11).
  - **The Mto prose** (`:305-306, 313-314`). It reads the evaluator's MTO option figures under case 2. Where none
    exists, it takes case 3.
- **Why.**
  - The crashes and the stale prose are one fault: readers bound to the old fixture shape. Fixing the named lines
    alone would leave the next removed key to crash another page (W6).
  - Keeping the element with its stated gap honours the mock as the layout spec and the owner's honest-numbers bar.
- **Reverse:** drop sourceless rows, labelled `MOCK DEVIATION` (removal), which needs the owner's look.

## D-0K4.56 P26 is carried by P26b; K10's code is retired at commit 6 (commit 2b pending point)

- **Ruling.**
  - **P26b is accepted.** Plant P26 becomes: Kobo's `factor_sources: {candidate_l: "0"}` re-added (scratch copy),
    which must fail K13 on `derived-values.json` `sites`.
    - The spec's original form, with `candidate_l` nulled, crashes both models in the history series before K13
      runs. A crash fails loudly, but it does not prove the named check.
    - Nulling a world leaf is 0K4f's state to support, not 0K4m's (D-0K4.45).
    - The original form is recorded only as "must exit non-zero". It is not a plant.
  - **K10 is retired in code.** The checker at `ba2da1c4e` still runs `k10()` (`check_manifest.py:2439`). Its row
    fails ("factor_sources sets candidate_l … (got None, None)"), although spec rev 4 retired K10 (D-0K4.45; K13
    holds the class).
    - Commit 6 removes `k10()` and its call, together with `H9_BASELINE`, since both edit `check_manifest.py`.
    - The ledger counts K10's removal by section.
    - Unit 3 does not touch `check_manifest.py`.
- **Why.** Each plant must fail its own named check. A retired check that still runs is a second oracle for the same
  class, and its standing failure would hide a real one at the head.
- **Reverse:** guard the history series against a null leaf in both models, and keep P26 as specified.

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
| Q19 | H1: restate the structure layer now (product in, or tests pinned) or keep it as on main? | Kept as on main; it moves with 0K4f together with the product and the world (D-0K4.45); owner asked to confirm on return (row 78) |
| Q20 | A protective decision with no candidate | Take none, with the reason in `protective_choices`; never infeasible for that reason alone (D-0K4.46) |
| Q21 | Sensitivities of an option with no value | Null (D-0K4.48) |
| Q22 | Decision-history rows that anchor restated figures | Rows before 21 Nov keep their words and lose the anchor; rows from 21 Nov on are anchored (D-0K4.49) |
| Q23 | Unit 3: the guard bans "replay", but §4's exact copy uses it five times | Keep the guard. The copy says "simulation", in exact strings (D-0K4.50) |
| Q24 | Kobo's 330 / 730 split: source and 0K4f on the mock, with codes kept off screen | On screen in words, as October's records classify it and to be re-checked against Kobo's readings. 0K4f goes in the drawer's reviewer block. Acceptance 5 amended (D-0K4.51) |
| Q25 | "{fig:} L against plan {fig:} L" in commit 2b's bridge bases (OD-6) | Fixed in the manifest, in unit 3's commit 4: "against a target of". Manifest strings swept; unit 2 uses the same words; no `PLAIN` patch (D-0K4.52) |
| Q26 | Unit 3 scope; SIMTEXT's day count; `--shots` writing to `screenshots/` | All of §4 plus D-0K4.52's strings. Each chip shows its own study's days. The repo audit runs without shots, and the shots come from a scratch copy into `/opt/assetecon/evidence/0K4m/u3/` (D-0K4.53) |
| Q27 | The manifest `reason` strings for Kobo's settings and KIS-BATT60 carry "0K4f" and "dispatch replay" | The mock renders its own copy. The reasons stay for the documents and reviewers (D-0K4.54) |
| Q28 | Hand-typed or stale readers outside §4's list, and five pages crashing on removed fields | One class: each reader reads a field the fixtures carry (evaluator or record). A gap shows "Not available yet", the element stays and no row is dropped. Zero console-error routes is the gate (D-0K4.55) |
| Q29 | P26, as specified, crashes both models before K13 runs | P26b (`candidate_l: "0"` override) accepted. K10's leftover code goes at commit 6 (D-0K4.56) |
