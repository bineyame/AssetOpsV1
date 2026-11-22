# 6h rulings (D-P6.59 to D-P6.67): the handshake answered

Architect (Claude), 2026-11-22, answering `handshake-review.md` (reviewer, on `main` at `c39006bf6`). Code re-read on
`task/6h-handshake` at `c1a9c65b6`. D-P6.51 to D-P6.58 (in `specs/6f-decisions-screen/rulings.md`) stand except where a
ruling below amends one. Spec `spec.md` rev 1 carries every ruling. **The owner is asked to weigh in on D-P6.65** (the
figure Thika's page shows) and is told of the unit card (D-P6.67).

## D-P6.59 `backup_cover` moves one leaf: `uncovered_nights` (B1, proposal accepted)

- **Ruling.** `backup_cover.changes = ("uncovered_nights",)`, source `RECORD`; `stopgap-and-claim` and `self-repair`
  both change `uncovered_nights`. The record word `BACKUP_COVER__BACKUP_UNPROVEN_DAYS` is dropped. T1's literals stand;
  `self-repair` without its record names `[OPTION_RECORD, DECISION, uncovered_nights]` then `[ONE_OFF, DECISION, null]`.
- **Why.** The manifest's three Thika options state `uncovered_nights` only; `backup_unproven_days` reaches neither
  `contribution` nor the purpose factor, so a second leaf would only add a record nobody holds. A proven backup is the
  supplier's remedy record (9c), which can add the leaf to the lever as data.
- **Reverse:** `self-repair` changes both leaves (T1 unchanged; one more record word).

## D-P6.60 An option's own unrecorded leaves are always named, and its value is then null (B2, accepted)

- **Ruling.** In `_value_option`, after the outcome's missing inputs and before `ONE_OFF`: for each leaf of `changes`
  in the catalogue option's `changes` order whose `LeafChange.delta` is None, add `_leaf_input(leaf, changes, base)`
  unless an equal `MissingInput` is already listed. Any missing input makes the value null (as today).
- **Why.** Missing is never 0: a changed leaf outside `contribution`'s closure (Thika, Kisiwa) would otherwise read a
  value of minus the one-off. Generic: no generator or structure is named.
- **Reverse:** none sound (a missing record read as 0).

## D-P6.61 A row's evidence and source class include its changed leaves (B3, accepted with one precision)

- **Ruling.** `evidence = weakest((out.evidence, *[c.evidence for c in changes.values() if c.delta is not None]))`; if
  that is `NEUTRAL`, `weakest([c.evidence for c in changes.values()])`. `source_class = _source_class(_origin_union(
  out.origins, *[c.origins for c in changes.values() if c.delta is not None]))`.
- **Why.** A no-money-path option (Thika) has no used factor, so `NEUTRAL` reached a column 0072 refuses and an emulated
  record read `RECORDED`. Known deltas only, because 6c's convention is that a missing value is not a used value
  (`test_1_f1a...`); on the generator path every known changed leaf is already in `contribution.used`, so nothing moves.
- **Reverse:** all changed leaves, known or not (moves 6c's season-declared rows to `SIMULATED`; rejected).

## D-P6.62 A record's currency enters the difference; `OPTION_RECORD_CURRENCY` is withdrawn (B4, accepted)

- **Ruling.** `LeafChange` gains `currency: str | None = None` (last field, keyword default). `stated_changes` sets it
  from the record; `_Difference.delta` collects a `LeafChange` part's currency as it does a value's. The existing
  `CURRENCY_MISMATCH` and `ONE_OFF_CURRENCY` cover a record in another currency; `OPTION_RECORD_CURRENCY` (6h §4.2/§4.3,
  6f §2a `missing`) is dropped.
- **Why.** One rule, one sentence: N1's `revenue` and `handling` effects read USD; a KES record against a USD base is
  caught with or without a one-off. Every existing `LeafChange` carries None, so 6c's results are unchanged
  (D-P6.67's parity test).
- **Reverse:** keep the extra code as a distinct sentence (two rules for one fault).

## D-P6.63 The axis, template and grid lever checks run for `SETTING_GRID` only (B5, accepted)

- **Ruling.** In `_lever_fault`, branches 2 to 5 and 14 run for every lever; 6 to 13 only when `generator ==
  "SETTING_GRID"`. Branch 17 refuses `SETTING_GRID` with options; `STATED_OPTIONS` with axes, with no options, or with a
  non-empty `key_template`.
- **Why.** A lever with no axes has one empty grid point whose key `""` fails branch 13, so every real named-option
  lever would stop start-up. 6a's planted cases are all the generator lever and refuse exactly as today.
- **Reverse:** give named-option levers a dummy template (a workaround).

## D-P6.64 Gate G4 and Kasarani on the DD world (H1 with N6)

- **Ruling.** G4 (a done condition, not a stop): 6h is done on K2 (unit, 630.00). On the DD world Kasarani is valued
  only when DD's EV inputs for 2026-11 read (Q11); until then its page names the missing November record. When they
  read, with the manifest's `KAS-OEM-STOPGAP` cover `nights: 2` and penalty 120.00, the value is 2 x 120.00 - 90.00 =
  **150.00**, the manifest's `modelled_12m_change`; DD6.2's acceptance asserts it (provided DD's November leaves give
  at least two missed departures before cover; else the floor `max(..., 0)` applies and DD6.2 reports the figure).
- **Why.** The mechanism is proven at unit level; the demo figure is pinned so it is checked, not discovered.
- **Reverse:** hold 6h until Q11 reads (blocks the slice on DD).

## D-P6.65 The no-action level is the decision month's own leaf; Thika shows uncovered nights -26 (H2 with N7)

- **Ruling.** For every named-option lever the no-action level of a recorded leaf is the decision month's base value
  (D-P6.58, one rule; no Thika case). Thika (October, horizon 1) reads base 26 against the rota's 0: "uncovered nights
  -26". The manifest's `THIKA-EPC-WAIT` (nights to the supplier's restore) is a forward level; it enters when 9c's
  remedy records (restore date) exist, through the same rule. The packet states it; the coordinator names this figure
  to the owner before the walkthrough. **Owner to weigh in:** is "a month like October" the comparison the executive
  should see for a stopgap, or should Thika's page wait for the restore date (9c)?
- **Why.** Every 6h value is "a month like the decision month" (Mwea's contract too); a special forward level for one
  Site would be a vertical branch and a second figure.
- **Reverse:** Thika waits for 9c (its value reads "Not available yet: needs the supplier's restore date").

## D-P6.66 The non-blocking points N1 to N12

- **N1** Accepted: `NO_ACTION_WORDS = ("KEEP_SETTINGS", "KEEP", "WAIT_FOR_REMEDY")`; the generator lever takes
  `KEEP_SETTINGS`.
- **N2** Accepted: "the route offer: buses in the fleet"; "the repair quote and the electricity above the model after
  the repair". Same class (W6): `BACKUP_COVER__UNCOVERED_NIGHTS` becomes "the rota: the nights it leaves uncovered"
  (both options state it now, and the leaf is the uncovered level); the other record words were checked and state
  levels.
- **N3** Accepted, and a third test found: `test_6a_decisions.py::test_1_the_registry_row_lists_the_lever_and_no_other_does`
  becomes the §5.2 listing as a literal (`MINI_GRID` version 4 stays). All three change as written in spec §10.2;
  none is loosened.
- **N4** Accepted, widened: mini-grid `_node` gains `levers=()`; cold-chain and EV `_leaf` and `_node` each gain it.
- **N5** Accepted with defaults so 6c's calls stay unchanged: `option_inputs(options, lever, study: StudyInput | None,
  by_key, admissions, one_offs, *, base=None, records=MappingProxyType({}), grid_changes=SETTING_GRID_CHANGES)`; a
  `STATED_OPTIONS` option with `base is None` raises `RuntimeError` (a caller fault). E3's study block is skipped and
  `study_sha256`, `study_identity` are None.
- **N6** See D-P6.64. **N7** See D-P6.65.
- **N8** Accepted: R7's money test is `unit.has_money_dimension`; `declared_by_script` true from the CLI;
  `_covering_role(roles, site_id, command)` reads `roles_of(command)` (one-off passes `COMMANDS["one_off"]`).
- **N9** Accepted: `BOUNDS_NOT_CHECKED` is the outcome of a `bounds_required` lever even when no option is valued.
- **N10** Accepted: one rule, delta = record value - base value; a missing base is named. The plant that could never
  fail is replaced by "records looked up by factor alone, not (option, factor)", failing new fixture T1b.
- **N11** Accepted: the EV replay slice amends E2 (spec §13).
- **N12** Accepted: a `PENDING_LEVERS` key that is not a `PINS` key refuses `STRUCTURE_LEVER_PATH` with structure key `""`.

## D-P6.67 What the shared changes reach, the parity test, and the unit card

- **Ruling.** The shared changes and their reach:
  - `difference` (`also`, `OUTCOME_FACTOR` always in scope, `LeafChange.currency`): every registry (MINI_GRID,
    COLD_CHAIN, EV_DEPOT_CAPTIVE and the test registries OPS, PRODUCT, NEUTRAL, DIVISION); its only production caller is
    `evaluate_options`, run by `decision.evaluate` (ANALYST).
  - `evaluate_options` / `option_evaluation` rows (D-P6.60, .61, `BOUNDS_NOT_CHECKED`): all three Site types; ANALYST
    writes; every role that reads a decision page reads them.
  - `check_levers` (D-P6.63, branches 15 to 22) and `check_lever_paths`: start-up, all three registries and the five
    `PINS`; no role.
  - `option_inputs`, `prepare` P5/P7, `_covering_role`: ANALYST (prepare, evaluate), SITE_MANAGER and
    FINANCE_AND_COMMERCIAL_LEAD (one-off, option record).
  Meant to stay unchanged: 6c's fixtures (F1, F1a, F1b, K1, C1, C1b, E1 and the OPS/PRODUCT/NEUTRAL/DIVISION plants)
  and Kobo's `generator_stop_reserve` path (prepare, option inputs, evaluation, 6a's planted lever cases). New test
  `test_6h_parity.py` compares them byte for byte with a golden captured from the slice's base commit before any 6h
  change (spec §10.2 test 8). A difference is a fault in 6h, never a golden to refresh.
- **Unit card.** 6h1 1.0, 6h2 1.0 (+0.25 for D-P6.60 to .62 and the parity golden), 6h3 1.25, 6h4 1.0: **4.25 u**, one
  slice, under 6. The owner approved 3.75 u; the slice is now 0.5 u above it (0.25 lever words and protective rule,
  D-P6.51; 0.25 the handshake's fixes). 6f1 stays 3.75 u.
- **Why.** The 22 Nov usage rule: a ruling that changes shared behaviour names its reach and proves the rest unchanged.
- **Reverse:** none (the rule is standing).
