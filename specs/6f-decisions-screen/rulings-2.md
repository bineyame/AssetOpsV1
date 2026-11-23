# 6f rulings, part 2 (D-P6.88 to D-P6.93): the 6f1 U1 review's questions

Architect (Claude), 2026-11-23. Continues `rulings.md` (15k cap). Read: `review-6f1-U1.md` at `ef2a81039`
(`task/6f1-decisions`), `decisions/evaluate.py` and `structure/difference.py` on main `93ed567d7`, the mock's `uxDecisionSlots`
(`loop-ux.js:699-774`). Spec rev 4 is `spec.md` §15. D-P6.82 to D-P6.87 stand except where D-P6.93 says so.

## D-P6.88 A price effect stores its record's currency at the run (Q1; the default changed)

- **Ruling.** The fault is fixed where the row is made, not in the view. In `decisions/evaluate.py`,
  `_effect_currency(delta, option_currency, change)` takes the factor's own `LeafChange` (`changes.get(d.factor_id)`).
  D-P6.34's branch is first and unchanged. Then: the unit has a money dimension but is not `MONEY`, the change is
  known and the factor is itself a changed leaf → `change.currency`. Else `delta.currency`, as today. So Mwea's `contract_rate` row
  stores USD, and N1k's KES. `structure/difference.py`, `OptionView.records`, the schema (0072 allows it) and
  `EVALUATOR_VERSION` do not change: no figure moves.
- **View.** PRICE reads `row.currency`; null raises a named `ValueError` (a code defect: no run of a `storage_contract`
  is stored anywhere yet, WK-SC prepares the first).
- **Why not the option record read by the view.** The read holds the **latest** record; a run used the record of its
  own day. A document restated in another currency after the run would put the new currency on the old figure. The row
  is the run's own memory, so it names its own currency. Why not `Delta.currency` for every price row: it moves
  6h's parity golden on planted price nodes no decision can show.
- **Reach and parity.** Every `LEVERS` entry, three structures: only `contract_rate` changes (the only non-`MONEY` price
  leaf in an effect scope, D-P6.73). Tried on main: 6a, 6c, 6h (pure) and `test_6h_parity` pass unchanged; one line moves,
  `test_6h_evaluate.py:59` `"contract_rate": "USD"`. 6h spec §10.1 N1 reads so. Add: N1k's row is KES. Plant `pricecur`
  (drop the new branch) fails N1 and F6-N's page. Page text: "+$0.18 per crate-day".
- **Reverse:** the record's currency on `OptionView`, read as of `run_at`.

## D-P6.89 A zero money change with no currency reads "No change" (Q2; accepted, capital N)

- **Ruling.** `effect` gains variant `NONE` "No change", used when a `MONEY` row's change is exactly 0 and its currency is null
  (D-P6.34 leaves it null when the option has none). A non-zero change with a null currency raises a named `ValueError`.
  A zero that has a currency keeps its figure ("$0.00"). `NONE` prints no figure, so its evidence is `[]`.
- **Why.** The structure says no money moves and read no money value, so there is no currency to show and none is
  invented. Zero is stated as zero. A cell starts with a capital, as every other cell does.
- **Tests.** The page of `generator_redundancy` with no records and of `backup_cover` with no one-off; plant `nocur`.

## D-P6.90 The words follow the model's rule and its state (Q3)

- **Valued (M2): "Valued" never shows when no option has a value.** "Options" here are those but the baseline and the
  `REJECTED`. For outcome `BOUNDS_NOT_CHECKED`:

  | Options with a value | `at_stake` | `outcome_note` |
  |---|---|---|
  | all | `BOUNDS` (as built) | `BOUNDS` (as built) |
  | some (Thika T1) | new `BOUNDS_PART` "Some options valued; no option recommended until the limits are checked" | new `BOUNDS_PART` "No option is recommended until the limits for this decision are checked. No value yet: {unvalued}." |
  | none (Ruiru, Kisiwa) | `INCOMPLETE` (the missing sentence) | new `BOUNDS_NONE` "No option is recommended until the options have values and the limits for this decision are checked. No value yet: {unvalued}." then the missing sentence |

  Sweep of the class: `rec_heading` is D-P6.82 (b)'s. `valued_by` gains `NO_VALUE` "Worked out on {day} by {person}; no option
  has a value yet", when no option but the baseline has a value (F6-B, F6-S). `choice` `*_STALE` reads "... worked out again since
  this choice." (true with or without values). `disposition` `CONDITIONAL` is set only on a value: kept.
- **Tie rule (M3).** 6c is not changed: a named option's distance is 0, so the highest value wins, which is the right
  rule when there is no setting to stay close to. Position order would let a worse option win by 10%.
  - `why_rule` SETTING: "... The setting worth the most is recommended; among the settings within {margin} of it, the
    setting closest to today's settings, and of settings equally close, the setting worth more. The dawn readings ..."
  - `why_rule` OPTION: "Each option is valued against doing nothing, over the same figures that make up the month's
    contribution. The option worth the most is recommended; of options worth exactly the same, the order is fixed
    beforehand." (6c's last key is `option_key`.) No `{margin}`: the slot becomes optional.
  - new `why_rule` BOUNDS (a `bounds_required` lever, any state): "Each option is valued against doing nothing, over the same
    figures that make up the month's contribution. No option is recommended until the limits for this decision are
    checked."
  - `why_answer` NEAR_OPTION is withdrawn (variant, `OPTION_TWIN` entry, case); a named recommendation whose value is
    not the best raises a named `ValueError`. New `why_answer` BOUNDS "The limits for this decision are not checked yet"
    (outcome `BOUNDS_NOT_CHECKED`). NONE becomes "Rejected or deferred: {rejected}" (the mock's fact, singular-safe;
    the baseline not counted, D-P6.82 (a): F6-B "Rejected or deferred: 13 of 13 options").
- **`can_choose` (M4).** Shown only with a run, no choice and no recommendation (6a H2, H3). Amends §3.3: F6-A and a kept
  decision lose it; `NOTHING_ADMITTED` keeps `NONE_ONLY`.
- **INCOMPLETE notes.** Setting: "No option is recommended until every setting that passes the service checks has a
  value. No value yet: {unvalued}." Option twin: "No option is recommended until every option has a value. No value
  yet: {unvalued}." (a named option has no service checks).
- **Plants.** `boundsnone` (BOUNDS with none valued) fails Ruiru; `stillchoose` (`can_choose` after a choice) fails
  F6-H; `nearopt` (margin words on OPTION) fails F6-N.

## D-P6.91 Every figure on the page carries its evidence words (Q4; accepted, as one form)

- **Ruling.** The form §3.3 already has for `rec.figure` and `at_stake`, `{text, evidence: [words]}`, becomes the form of
  every field that can state a figure of the Site: Card and `all` row `result`, `cost`, `dawn` (`dawn` null as
  today); `limits` row `dawn`; `change` row `change`; `cost` row `cost`; `rec.cost`. `evidence` is what `served` returns: `[]` for
  a missing sentence, "The baseline", "No change", "one-off cost not stated yet". An effect row carries its option's
  evidence (the only class stored; it is the weakest, so never stronger than the row's own).
- **Not in it:** settings in an option's label (the option's name), counts, the near-best margin (the rule's constant,
  D-P6.82) and section `answer`s (text; the cost answer's figure is repeated with its word in its own row).
- **Why one form.** `_text` dropped the words of eight kinds of figure, not two; a parallel key beside some of them would leave
  the class open. The mock marks each result too (`uxMark`, card and recommendation). The view's `_text` may then be
  called only for statements of the "not in it" list; a test walks every fixture page: each
  field named above is `{text, evidence}`, and one whose text holds a digit and does not begin "Not available yet" has at
  least one evidence word. Plant `noev` (`change` served without words).
- **U3 (card amended).** Draws `evidence` as `<small>` under the figure (as `at_stake` on U2's list), in cards, the
  three tables, the effect rows and the rec card's cost; a word equal to the chip drawn beside it is not drawn twice; `[]` draws nothing.
  Plant `noev` (words dropped) fails. MD-6F-12 (D2, U3): the mock drops the mark from cards when all valued options
  share it; here each figure keeps its word (RULES §1). U2 is unchanged (its row already has the form).

## D-P6.92 `buses_full_by_charger` is "Buses the chargers can fully charge a night" (Q5; the default changed)

- **Ruling.** Vocabulary `factor` entry, appended last: label "Buses the chargers can fully charge a night", in_sentence
  "buses the chargers can fully charge a night", article "a". It joins D-P6.72's table. It needs no `EFFECT_FORMAT` (no lever changes a
  leaf it rests on; the scope check proves it).
- **Why.** "Fill a bus" reads as passengers; "fully charge" matches its neighbour "Buses short of charge a night".

## D-P6.93 The review's contrary defaults and Lows; the fix round; units

- **Reopened, the review is right: point 4.** `missing` NIL_DENOMINATOR takes `{factor}` (in-sentence, as D-P6.81 wrote); slot
  `factor_label` goes. The handoff's "same text" is false: "Not available yet: Tariff cannot ..." capitalises mid-sentence, unlike
  every sibling. **Not reopened:** 1 (agrees), 2 (slots optional), 3 (agrees), 5 (`DECLARED`), 6 (`MONTH`; its words below), 7 (agrees).
  L7 is D-P6.86's (no card marked). M7 is D-P6.82 (c)'s; no `NONE_OPTION` (a named option is never `REJECTED`).
- **`assumed`** takes in-sentence words (D-P6.72), registry order (H3).
- **Accepted as the review proposes:** H3, H4, M5, M6 (`checks` BASE "The baseline"; `banned_in` over every served
  string of every fixture; the exemption case-blind), L5 (`limits` columns are six, DAWN last), L6 (`cards_note` `EMULATED` "Each
  result over {horizon}; emulated figures are marked Emulated").
- **M5 is a class (W6).** `AgreedActionService`'s `StoreUnavailable` joins the `unavailable` tuple of **both** routers in
  `main.py` (6f1's and 5c's), one test each; no follow-up is left.
- **L4, singular-safe words.** `horizon_basis`: MONTH "Over {horizon}: the change worked out for {month_list}, times
  {horizon_count}"; MONTHS "Over {horizon}: the average of {months} ({month_list}), times {horizon_count}"; STATED "Over {horizon}: the
  month's change, times {horizon_count}". `limits_answer`: REC_SOME "The recommendation keeps every service check; a service
  check fails for {failing}"; SOME "A service check fails for {failing}".
- **Fix round, in order:** (1) merge main (`index-3.md` conflict), Q5 word; (2) D-P6.82's list; (3) D-P6.83's F6-J, N, T, S, plus one world per
  remaining named lever on real evaluator rows, **first and failing**; (4) D-P6.88 to D-P6.92; (5) the accepted items here; (6)
  whole-Page literals, `--write-fixtures`; (7) one test for the review's residual
  risk: a record whose page raises makes the list route raise (500), never a partial list; (8) packet: every moved literal, seven open points. Re-review is
  verification of named findings, except `evaluate.py` and the never-run named-option half: discovery (W5).
- **Units.** U1 2.5 → **2.75** (one evaluator branch, the served form, new variants); U2 1.25, U3 1.5 stand. 6f1 **5.5 u** (cap 6).
- **Owner.** Told, no decision asked: every figure on the decision page shows its evidence word, also when all agree.
- **Reverse:** per item, the text it amends.
