# 6f rulings, part 2 (D-P6.88 to D-P6.99): the 6f1 U1 reviews' questions

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
- **`can_choose` (M4; extended by D-P6.94).** Shown only with a run, no choice and no recommendation (6a H2, H3). Amends §3.3: F6-A and a kept
  decision lose it; `NOTHING_ADMITTED` keeps `NONE_ONLY`.
- **INCOMPLETE notes.** Setting: "No option is recommended until every setting that passes the service checks has a
  value. No value yet: {unvalued}." Option twin: "No option is recommended until every option has a value. No value
  yet: {unvalued}." (a named option has no service checks).
- **Plants.** `boundsnone` (BOUNDS with none valued) fails Ruiru; `stillchoose` (`can_choose` after a choice) fails the kept
  `NO_ACTION_BEST` test (corrected by D-P6.97: F6-H has a recommendation, so it never has the note); `nearopt` (margin words
  on OPTION) fails F6-N.

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

# D-P6.94 to D-P6.98: the U1 re-review's questions

Architect (Claude), 2026-11-23. Read: `review-6f1-U1-2.md`, the view, `records.py`, `evaluate.py`, `models.py`, `run.py` at `0c7f11e40`
(`task/6f1-decisions`), the mock's `uxDecisionSlots` (`loop-ux.js:699-774`). Spec rev 5 is `spec.md` §16.

**Model coverage (checked first).** What a run reads that a person can restate after it: a one-off (every option of all ten levers:
mini-grid 4, cold 3, EV 3) and a document (the `RECORD` leaves of eight named levers; none on `generator_stop_reserve` and
`charging_schedule`). The study, the admission, the dawn readings and the effects are the run's own rows; settings never change.
The run names its one-off (`option_evaluation.one_off_id`, stored for every option, valued or not). It does not name its
documents, but `difference` stores an effect row for every changed leaf, and that row has a change only when a document was read.

## D-P6.94 The page shows the cost its figures rest on; a newer one is named as not in them (Q1, N1; the default changed)

- **Ruling.** Once a run exists, the cost shown (card, `all` row, `rec.cost`, the cost answer, the cost row) is **the one-off that
  run read**, by its id. A newer one-off never replaces it: the words say one exists and is not in the result, and its amount is
  printed once only, in the option's cost row, as what it is. No run: the latest one-off, as built. Nothing is recomputed.
- **Why not the review's default** (keep the latest cost, add a sentence). It leaves "+$1,670.00" and "costs $5,000.00" together,
  and a reader subtracts. One model-computed figure per quantity: the result is the model's, so the cost beside it must be the one the
  model took off. Why not recompute: a run is a dated act of a named person, and the ranking would move with it.
- **Newer, defined.** `newer` is true when an option that is neither the baseline nor `REJECTED` has a latest one-off whose id is not
  its evaluation's `one_off_id`, or a latest document declared after `run_at`. A `REJECTED` option's cost cannot move anything (R1);
  its own cost words still say it. A new run clears it. Clock: a document stamped between the run's clock read and its read of the
  records (milliseconds) reads as newer; the error is on the safe side.
- **Read (6a's, additive).** `DecisionBundle.run_one_offs` (by option id: the rows the run's evaluations name; both stores; their
  people join `names`). `OptionView` gains `run_one_off: OneOffView | None`, `newer_one_off: bool`, and `newer_records:
  tuple[str, ...]` (factor ids, `changes` order) in place of 6f1's own `records` (D-P6.77 Q6). `one_off` stays the latest: the
  `state_one_off` command reads it. No migration; `EVALUATOR_VERSION` unchanged.
- **Source line.** `*_STATED` when an effect row of a `RECORD` leaf of any option has a change (the run read a document), never by what
  exists now and never by date: a document restated after the run would otherwise hide the older one the run did read.
- **Words.**

  | Statement | New variant | Text |
  |---|---|---|
  | `one_off` | `STATED_BEFORE` | "costs {amount}; a newer cost is not in this result" |
  | | `NIL_BEFORE` | "no one-off cost; a newer cost is not in this result" |
  | | `MISSING_BEFORE` | "one-off cost stated, not in this result yet" |
  | `one_off_detail` | `STATED_BEFORE` | "{amount} one-off, stated by {person} on {day}: {basis}; not in these figures: {newer}, stated by {newer_person} on {newer_day}: {newer_basis}" |
  | | `MISSING_BEFORE` | "Not in these figures: {newer}, stated by {newer_person} on {newer_day}: {newer_basis}" |
  | `cost_answer` | `STATED_BEFORE` | "{amount} one-off, stated by {person}; a newer cost is not in this result" |
  | | `NIL_BEFORE` | "No one-off cost; a newer cost is not in this result" |
  | `missing` | `STATED_SINCE` | "Not available yet: what was asked for was stated after the options were worked out" (D-P6.99) |
  | `newer_inputs` (new) | `COST` | "A one-off cost was stated after these figures were worked out; they do not include it." |
  | | `DOCUMENT` | "A document was stated after these figures were worked out; they do not include it." |
  | | `COST_AND_DOCUMENT` | "A one-off cost and a document were stated after these figures were worked out; they do not include them." |
  | `at_stake` | `VALUE_BEFORE` | "{value} over {horizon}, to be worked out again" |
  | | `AGAIN` | "To be worked out again: a newer cost or document is stated" |
  | `rec_figure` | `BEFORE` | "{value} over {horizon}, against doing nothing; to be worked out again" |
  | `eyebrow` | `REC_BEFORE` | "Recommended earlier" |

  - A missing entry is "stated since" when it is `ONE_OFF` or `ONE_OFF_CURRENCY` and the option has a newer one-off, or is
    `OPTION_RECORD` or `CURRENCY_MISMATCH` and names a factor in `newer_records` (narrowed by D-P6.99). A result, an effect row and
    `first_missing` show the first entry that is **not** stated since; `STATED_SINCE` when none is left. So a page never asks for
    what a person has already given.
  - `newer_inputs` is drawn while `newer`, in every state: in `rec.notes` before `can_choose`, and in the evidence lines after
    `valued_by`.
  - `VALUE_BEFORE`, `BEFORE`, `REC_BEFORE` and `AGAIN` only while `newer` and no choice is recorded (after a choice nothing is owed).
    `AGAIN` replaces `LOSS`, `TIE`, `MIXED` and their twins; `BOUNDS*`, `NONE_ADMITTED` and the missing sentences stay true.
    The qualifier is in the figure's own text because the list row and the sticky bar draw it with no note beside it.
- **What a person may still do.** Choosing is not blocked: 6a's H rules are unchanged, the system proposes and a person chooses, and the
  choice names the run it was made on. `can_choose` is shown with a run, no choice, and **no recommendation or `newer`**, in its
  words as they are: a person is not held to a recommendation that a newer cost is not in. 6f2's dialog repeats `newer_inputs`
  (spec §11 gains it). The analyst values again to bring the cost in.
- **Sweep (W6).** Everything the page reads as latest while the figures are the run's: one-offs, documents (both here), the choice's
  run (`_STALE`, built). Nothing else. Reach: all three Site types by one path, the list and the page.
- **Tests.** Whole Pages: F6-N with its one-off restated; Kasarani K2 the same (EV, no recommendation, `BOUNDS`); a Kisiwa document stated
  after a run that read none; Thika's one-off stated after the run. Plain: F6-C with a one-off restated (grid; H1's figure,
  `VALUE_BEFORE`); F6-N with a document restated keeps `*_STATED`; only a `REJECTED` option's cost newer is not `newer`; a restatement after
  a choice; `NO_ACTION_BEST` reads `AGAIN`; a second run clears all. Postgres 7l/7m: `run_one_offs` after a restatement. Plants
  `latestcost` (the cost shown is the latest), `nonewer` (`newer` always false), `docnow` (source by `newer_records` or existence).
- **Reverse:** the review's default sentence beside the latest cost.

## D-P6.95 N3, N5, N6: words true of every option and every Site type

- **N3.** `change_answer` takes `kind`: `OPTION` "The option changes {factors}" (one option but the baseline: `storage_contract`,
  `productive_demand`, `fuel_reconciliation`), `OPTIONS` "Between them, the options change {factors}". "The options change", as the review
  proposed, is false for the three levers with one option.
- **N5 (amends D-P6.82 (c)).** `effects_option` is the first standing option in **display order**, so the caption and the cards agree
  and a valued option's rows are shown before "Not available yet" ones. The texts stand: "the list" is the cards, drawn first.
- **N6 (a), limits.** The four service checks are judged only on a replay of settings (`runs.admission`); no named option has them, at any
  Site type. The mock lists one limits line per option (`loop-ux.js` `limitsBody`, and the card's "Limits"). For a named lever:
  `limits` `columns` are OPTION and `LIMITS` "Limits", each row one cell (`check_cell` `NOT_CHECKED`), `dawn` null; `all`
  `columns` are OPTION, RESULT, COST, `LIMITS`, STANDING; a named option's `checks` (card and row) is new `LIMITS` "Limits not
  checked yet" (the baseline stays "The baseline"); `limits_answer` `NO_CHECKS` becomes "Not checked yet: limits are checked when
  bounds are set" (the old text spoke of "these options" for one, and said no check exists, which is not known). A setting grid is
  unchanged. MD-6F-6 (D1, 6b) covers it. Sweep: `limits`, `all`, the card; a dawn column was on cold and EV pages too.
- **N6 (b), why (amends D-P6.90).** Outcome `RANKING_INCOMPLETE`: `why_answer` new `INCOMPLETE` "Not every option has a value yet". "Rejected
  or deferred: 1 of 2 options" is not why. `NONE` stays for `NO_ACTION_BEST` and `NOTHING_ADMITTED`; the count stays in "All
  options". F6-B moves. MD-6F-14 (D2).
- **U3** draws a `limits` and an `all` table by the served columns; the dawn cell only when `columns` is six.
- **Reverse:** per item, the words it amends.

## D-P6.96 A figure's word is never stronger than a part of it (open point 8; N2)

- **Ruling.** (a) A stated one-off reads "Declared" (confirmed: D-SC1F.1, a value a person states with its basis; a quote is not a
  system of record). (b) No result or effect may carry a stronger evidence **class** than anything it is made of, a cost included.
  With D-P6.96 (c) it holds for every lever: a valued grid option is `MODELLED`; a valued named option has every leaf change
  known, so it is `DECLARED` or weaker; the one-off is `DECLARED`. So the one-off need not enter the fold (it would
  raise a `MODELLED` row with no value to `DECLARED`). One test holds it: over every `LEVERS` option valued with a one-off, the stored class
  ranks `DECLARED` or weaker.
- **(c) The model fault the sweep found.** A named option's change is the document's level **minus the month's own level**, and
  `stated_changes` (`decisions/models.py`) carries only the document's evidence and origin. An estimated or simulated month under an
  observed document can read as observed. Fix: `LeafChange` evidence `weakest(("DECLARED", level.evidence))`, origins
  `_origin_union((record.origin,), level.origins)` (exported, or `ORIGIN_ORDER` applied there). An option-only neutral has no class and no
  origin, so it adds nothing. No value, change or rank moves; tried on main: 6h (six files with parity) and 6c pure, 180 passed
  before and after. Tests: a fuel investigation over an `ESTIMATED` level stores `ESTIMATED`; a `demo-simulated` level under
  `observed-financial` stores `SIMULATED`. Plant `levelev` (the old line).
- **N2: fix now, in the model, same function.** When the document and the month's own level each have a currency and they differ, the
  change is missing `("CURRENCY_MISMATCH", "STRUCTURE")`, so the effect and the result say "the month's figures are in different
  currencies" and no cross-currency difference is stored. Why not a raise: a person stating a quote in another currency is
  not a code defect. No lever reaches it today (same parity run). One test: base 0.15 USD, record 23.00 KES.
- **(d) The words.** "Simulated" and "Emulated" are not stronger than "Declared": they say what the figure may not be taken for
  (D-5C.19). "Modelled" and "Estimated" are weaker. So every demo Site's page conforms (its records are simulated or emulated).
  One cell breaks the rule: a named option on a Site whose records are real reads "Recorded" over a "Declared" cost.
- **(e) D-P6.77 Q8 stands for U1 and is a Known Deviation in that one cell** (`source_class` `RECORDED`, a class that is not
  `MODELLED` or `ESTIMATED`). Which word it takes is D-P6.98, the owner's. It must be closed before a valued decision of a Site on real records is shown to anyone.
- **Reach.** Cold, EV and mini-grid named levers; values and the grid lever unchanged. **Reverse:** (c) the old line; N2 a raise.

## D-P6.97 N4, N7, `stillchoose`; the fix round; units

- **N4: fix now.** Three short cases put `TIE_OPTION`, `MIXED_OPTION` and `RANKING_INCOMPLETE_OPTION` through the view (the review's `twins.py` worlds):
  the test's name claims them. **N7: at merge**, coordinator or merge preparation (one index line; code merges cleanly).
- **`stillchoose`** (D-P6.90 corrected in place): it fails the kept `NO_ACTION_BEST` test, not F6-H.
- **Fix round 2, in order:** (1) merge main (these rulings; `index-4.md` line renumbered); (2) tests first and failing: D-P6.94's, D-P6.96's
  and N4's; (3) model: `stated_changes` (D-P6.96 (c), N2); (4) read: `run_one_offs`, `run_one_off`, `newer_one_off`, `newer_records`
  in both stores; (5) view and words of D-P6.94; (6) D-P6.95's words, columns, effects option; (7) whole Pages and
  `--write-fixtures`; (8) plants; packet: every moved literal, point 8 closed, D-P6.96 (e) as the one Known Deviation.
- **Re-review:** verification of N1 to N6, with discovery on `records.py`, the Postgres read and `stated_changes` (W5: money). This is
  U1's second fix round; a third triggers W7's readiness pass.
- **Units.** U1 2.75 -> **3.25**; U2 1.25 and U3 1.5 stand. 6f1 **6.0 u**, at the cap: nothing more
  enters U1. If it grows, D-P6.95's N6 (a) moves to U3's branch as a served-words part, and the Architect is told.

## D-P6.98 OWNER: the word on an option's expected value at a Site with real records (Q2; not decided)

- **Recommended:** "Estimated" for a named option's result and effects at a Site on real records. It is about the months to come, so
  nothing recorded it; it rests on a stated cost, so it may not read stronger than "Declared" (D-P6.96); and "Declared" on a worked-out
  $1,670.00 would say a person stated that figure. "Modelled" stays for simulated settings; "Simulated" and "Emulated" stay. The demo does not change.
- **Words for the owner:** "On a Site with its own real records, the value we expect from an option (for example '+$1,670.00 over 4 months') is marked
  'Recorded' today, because it is built from recorded figures and a document. But it is about the future, so nothing has been recorded
  yet. We suggest 'Estimated'. A cost a person stated stays 'Declared', and the demo Sites stay 'Simulated' or 'Emulated', so nothing changes in the demo.
  Is 'Estimated' right?"
- **If yes:** one branch in `_Page.evidence`, F6-N's and F6-T's literals; a fast-lane change after U1, before the first pilot Site. Until then D-P6.96 (e).

## D-P6.99 A newer document answers only the document's own entry; `STATED_SINCE` says what was asked for (amends D-P6.94)

- **Ruling.** The builder's narrowing is accepted (`T.COST_KINDS`, `T.DOCUMENT_KINDS` at `3c71cb6a9`); D-P6.94's "or names a factor in
  `newer_records`" was too wide.
- **Checked, every entry kind × every lever.** `OPTION_RECORD` with a factor: only `stated_changes`, a `RECORD` leaf with no document; a newer
  document answers it. `CURRENCY_MISMATCH` with a factor: only N2's branch; a newer document may answer it, and the next run judges it.
  `CURRENCY_MISMATCH` with no factor (the fold's): may be the month's own, so it stays. The month's own record (`NOT_CONNECTED`,
  `HELD_NOT_CALCULATED` and the providers' causes; 6h names it when a document is held over a missing level): a document never
  answers it, and on cold and EV Sites it is the usual case. `ZERO_DENOMINATOR` names a node, never a `RECORD` leaf; the base's
  `CURRENCY_MISMATCH:` causes carry a suffix, so they cannot match. `OPTION_STUDY` and `SITE_MONTH_SIMULATION` (`charging_schedule`, the grid)
  take no document. Cost kinds: all ten levers.
- **Same class, other direction (found here).** With no document, `stated_changes` names the document and stops, so a leaf whose month's
  own level is also missing hides that level in the run's row. "What it needs was stated" is then false on the same Sites: the next run asks for
  the month's record. The page knows only what the run asked for, so `STATED_SINCE` reads "Not available yet: what was asked for was stated
  after the options were worked out". No model change: which lack is named first is 6h's order, and no figure depends on it.
- **Builder:** that text in `decision_page.missing`, its case and its literals; one test: a document stated after a run over a leaf whose month's
  level is missing reads `STATED_SINCE`, and the run after it names the month's record. Nothing else. Units unchanged.
- **Reverse:** D-P6.94's wide rule and text.
