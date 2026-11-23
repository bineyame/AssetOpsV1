# 6f rulings (D-P6.42 to D-P6.58, D-P6.72 to D-P6.87; D-P6.88 on: `rulings-2.md`): the Decisions screen, and 6h

Architect (Claude), 2026-11-22, with `spec.md` rev 0. Code read on `main` at `591458c38` (6a and 6c merged) and IA-P1
on `task/IA-P1-frame-portfolio` (`1a19442e2`). Each ruling is a default applied now (W3); the owner answers in the
handshake table of `spec.md` §12. D-P6.43 amends an owner-visible ruling (D-P6.8): **the Architect asks the owner to
weigh in on it.**

## D-P6.42 6f is two parts; 6f1 now, 6f2 carded after the 6b and 6d specs

- **Ruling.** 6f1 (the list's source and the read-only decision page) is 4.0 units in three units, built after IA-P1
  and IA-P2 merge. 6f2 (the choice on screen) has its structure in `spec.md` §11 (about 2.0 units); its unit card is
  written after the 6b and 6d specs so their bounds rows and Action carrier fold in. 6f2 includes the inbox "For you".
- **Why.** The owner accepted "6f1 (Decisions rows, read-only page) after 6c; 6f2 (the choice) after 6b/6d"
  (`specs/6-decision-valued/rulings.md` Q3). The list needs IA-P1's component and IA-P2's E0 and Overview rows.
- **Reverse:** one 6.0-unit slice (at the cap; rejected by W4's split rule in spirit).

## D-P6.43 The Decisions list is the union of records and the placed Findings no record covers (amends D-P6.8)

**WITHDRAWN by D-P6.52 (owner, 22 Nov: "Build 6h").** It was a code workaround for a model gap (one lever, one
generator); kept below as history.

- **Ruling.** The list shows every decision record of the range (by `period`) and every placed Finding whose
  `finding_id` no record carries (D-IAP.3's rows). A covered Finding shows once, as its record(s). Order: the placed
  rows in server order, each covered row replaced in place by its records (newest `period` first), then records with
  no placed Finding in the range (or none), newest prepared first. The Findings list's "Its decision", the Overview L2
  rows, the inbox and search read the same union through one hook.
- **Why.** D-P6.8 said 6f "swaps the list's interim source for this read". Only the mini-grid generator setting has a
  lever, so a swap would leave cold-chain and EV Sites with no decision rows: against the owner's range rule ("if there
  is data in the range, then there should be corresponding output", the same way for every Site type) and "extend,
  don't drop". The placed-Finding row is a real live choice (accepting a recommendation creates an Action).
- **Reverse:** the pure swap, once every Site type has a lever (6g, 9c).

## D-P6.44 One waiting count: E0 counts the union

**AMENDED by D-P6.52:** one waiting count stands; it counts records in `NOT_VALUED` or `WAITING` only, and the
`DecisionCoverage` port is dropped.

- **Ruling.** `summary.waiting_count` and `waiting_by_site` count placed waiting members whose Finding no record
  covers, plus records in `NOT_VALUED` or `WAITING`, through a `DecisionCoverage` port injected into E0. A fault in the
  port gives `null` (the cells say "Not available yet"), never a partial count. The tile, the inbox badge and the
  Sites list read this rule.
- **Why.** Honest numbers: IA-P asserts tile = E0 = badge; three surfaces must count one set.
- **Reverse:** client-side counts (loses the Sites list and the truncated case).

## D-P6.45 The page's words are served: SC-1 statements in `decision_page.*`, figures formatted once

- **Ruling.** `decision_page/view.py` builds the list rows and the page on the server and renders every user string
  through SC-1 (`i18n/statements/en/decision_page.py`), with factor, heading and record words from the vocabulary.
  The client renders text only, plus the chrome words of `spec.md` §5.6. Display: money to cents, signed when it is a
  change against doing nothing (SC-1 `money`); litres and kWh one place; settings whole per cent; the dawn low one
  place. Rounded once from the stored figure (D-P6.6).
- **Why.** One home for factor labels and record words (5c's vocabulary), the digit and symbol guard on every
  template, and the evidence words beside every figure; the client cannot build a second figure.
- **Reverse:** client words in TS (as IA-P's list cells), with a second copy of the vocabulary.

## D-P6.46 A missing input is named by a closed map; 5c's record keys are reused (D-P6.37's text)

- **Ruling.** `SITE_MONTH_SIMULATION` → "Not available yet: needs a simulation of {site}'s own {month}" (D-0K4.50's
  wording); `ONE_OFF`, `ONE_OFF_CURRENCY`, `CURRENCY_MISMATCH`, `ZERO_DENOMINATOR` → their own sentences (`spec.md`
  §3.4); a base leaf → the records of `deep_dive.tables.RECORD_KEYS` (plus `EXTRA_RECORD_KEYS`: `wear_rate` →
  "a battery wear cost stated for the Site"), else "a record of {factor}". Any other entry raises. A card shows the
  first entry; the "All options in detail" table shows the first too, the evidence drawer the assumptions.
- **Why.** The executive must see which record is missing (D-P6.37); one record vocabulary across 5c and 6f.

## D-P6.47 Who decides: the chooser, else the current executive by name, else the role words

- **Ruling.** After a choice: the chooser's name. Before: `AccountService.executive_of` and the new
  `DecisionStore.name_of` (closing 6a review F5, D-P6.33); with no executive onboarded, "The operator's executive".
- **Why.** The mock and the owner's page brief name the person; `decision.choose` is `OPERATOR_EXECUTIVE` only and ON1
  holds one executive per operator, so the name is true, not a guess.
- **Reverse:** the role words always.

## D-P6.48 Option cards: display order and a cap of 7; the full table is never cut

- **Ruling.** Cards: doing nothing (the baseline), the recommended, `ACCEPTABLE` by rank, `DEFERRED`, `REJECTED`
  (position order within). The first 7 show, then "Show all {n} options". "All options in detail" lists every option
  in settings order. MOCK DEVIATION D2 (MD-6F-2).
- **Why.** The generator lever has 14 options; the mock's cards are sized for four. The standing brief asks for
  exposure that scales; the mock's own long-page rule caps lists at 7 and never cuts a comparison table.
- **Reverse:** every card (14), or the top three.

## D-P6.49 6f1's page is read-only and says so

- **Ruling.** No Choose control in 6f1. The act line reads "Choosing on this page: not available yet." The choice line
  shows a recorded choice, and "The options have been valued again since this choice." when the choice's run is not
  the latest. MOCK DEVIATION D5 (MD-6F-1), resolved by 6f2.
- **Why.** The owner's split; the page must not offer what it cannot do (every capability claimed must be
  demonstrable), and must not hide that a choice was made on older figures.

## D-P6.50 "How we will check it worked" states the approved method as not started

- **Ruling.** Before 6e, the section shows the method the owner approved in P6 §3 (working: generator running after a
  full battery on comparable days before and after, service checks held; money: fuel invoices, reported apart) and
  "Not started: the checks begin once the change is made." No day count is printed until 6e holds it as a record.
- **Why.** The verify link of the outcome mechanism is shown, as a plan, with no result claimed.
- **Reverse:** "Not available yet" alone.

---

# D-P6.51 to D-P6.58: levers at the source (6h), owner 22 Nov

Architect (Claude), 2026-11-22. Owner: "Build 6h (Recommended)"; 6h Q3 "Yes, +1.0 u"
(`owner/owner-6f-q1-levers-2026-11-22.md`). Assessment: `assessment-levers.md` (this folder). Spec:
`specs/6h-named-option-levers/spec.md`. Q2, Q4 and Q5 of the assessment's queue are ruled with the Architect's
defaults (D-P6.54 to D-P6.56); the owner may reverse any of them.

## D-P6.51 The lever model gains named options and option records; slice 6h, 4.0 u

- **Ruling.** A second generator `STATED_OPTIONS`: a lever lists named options (key, kind, the leaves each moves) and
  each changed leaf's source (`STUDY` or `RECORD`). The evaluator values a named option from its option records, else
  names the missing record or study. A person states an option record (a document's term) as the one-off is stated
  (6h4, owner Q3). 6h is four units: 6h1 lever model, prepare, migration 0073 (1.0); 6h2 evaluator branch (0.75); 6h3
  nine levers, their words, the class check (1.25); 6h4 option records (1.0).
- **Why.** The Sites are not different: one lever and one generator were modelled (assessment §1). A model fault is
  fixed in the model; the same functions now serve every Site type.
- **Size note.** The owner approved 3.75 u; 6h is 4.0 because the lever words move here from 6f (D-P6.58) and the
  protective rule (D-P6.57) is added; 6f1 falls to 3.75 u, so 6h + 6f1 is unchanged from the assessment's total.
- **Reverse:** the union (D-P6.43), withdrawn.

## D-P6.52 D-P6.43 is withdrawn; D-P6.8's records-only list stands (amends D-P6.44)

- **Ruling.** The Decisions list is the decision records of the range (D-P6.8). E0's waiting count is the records in
  `NOT_VALUED` or `WAITING`; no `DecisionCoverage` port. A placed Finding stays on the Findings list; its "Its decision"
  joins on `finding_id` (newest `period` when several) and otherwise reads "Not available yet". 6f1 unit 2 is 0.5 u and
  gated on 6h merged; 6f1 is 3.75 u. MD-6F-7 is withdrawn.
- **Why.** The union bridged a model gap in code; with levers for every Site type the list is the model's own reading
  and the mock's (vNEXT `DEC`: every decision a record with options).

## D-P6.53 Every pinned Finding has a decision path, or names the slice that gives it one

- **Ruling.** `check_lever_paths` at start-up: each `PINS` mechanism's row lists a lever, or the mechanism is in
  `PENDING_LEVERS` with its slice; `STRUCTURE_LEVER_PATH` otherwise. The map starts empty.
- **Why.** The class behind the gap (W6) is "a Finding with no decision path"; the rule stops it recurring silently.

## D-P6.54 Catalogue scope: nine levers (assessment Q2, default)

- **Ruling.** `backup_cover`, `chamber_efficiency`, `storage_contract`, `charging_schedule`, `charger_restore`,
  `fleet_capacity_use`, `generator_redundancy`, `productive_demand`, `fuel_reconciliation` (6h spec §5.1). Every demo
  Site has a decision and every pin a path. Rights-anchored decisions wait for 9a0/9c (MD-6H-3).
- **Why.** General over particular: the gap was all three types (Kisiwa and Mto too), not cold and EV only.
- **Reverse:** cold and EV only (six levers, 0.25 u less).

## D-P6.55 Embakasi's schedule options are valued from a charging replay of the Site's own month (Q4, default)

- **Ruling.** `charging_schedule`'s changes have source `STUDY`; until an EV replay exists the options read "Not
  available yet: needs a charging replay of Embakasi's own October under this schedule". The EV replay is queued as
  its own slice (not scheduled).
- **Why.** A schedule's kWh by window is a model result, not a document's term; typing it would be a second figure
  (one figure per quantity), the same rule that keeps Kobo's litres waiting for 0K4f (D-P6.2).
- **Reverse:** a stated record of kWh by window (weaker: a typed figure).

## D-P6.56 Who prepares a decision: the analyst, or DD's walk (Q5, default)

- **Ruling.** Unchanged from 6a: `decision.prepare` by the analyst (DD6.2's WK for the demo, 6h spec §7). No
  automatic preparation from a placed Finding until plan records (7a).
- **Why.** A person prepares and is named; automatic preparation needs the plan's ownership rules first.
- **Reverse:** a Finding on a lever's factor prepares its decision on placement.

## D-P6.57 A protective lever makes no recommendation until bounds exist; its purpose factor's change is shown

- **Ruling.** A lever with `bounds_required` (purpose home Protect) gives run outcome `BOUNDS_NOT_CHECKED`; valued
  options are `CONDITIONAL` (`BOUNDS_NOT_CHECKED`), unranked. The structure difference also covers the lever's purpose
  factor's closure and always returns `contribution`.
- **Why.** A stopgap's money value is mostly its cost; ranked on money alone, doing nothing would read best while
  stock or departures are at risk. That would be a misleading number; 6b's hard bounds decide these. The executive
  still sees the cost and the protected quantity's change (Thika: uncovered nights −26).
- **Reverse:** rank on money now (misleads until 6b).

## D-P6.58 An option record states a document's level, not a difference; lever words have one home

- **Ruling.** An option record is the leaf's monthly level under the option, from a named document, with its basis
  and declarer; the model computes the change against the no-action level (the option-only `neutral`, else the
  month's leaf) and every node. Records are allowed only on `RECORD`-sourced leaves. Every lever's words (title,
  question, doing-nothing line, option labels, record names), the generator lever's included, live in
  `i18n/statements/en/decision_lever.py`; 6f consumes them.
- **Why.** One model-computed figure per quantity; a contract's crate-days or a rota's cover is a record of the
  operating world, a computed saving is not. One home for words avoids two vocabularies.

# D-P6.72 to D-P6.79: the 6f1 pre-flight answered (Q1 to Q19)

Architect (Claude), 2026-11-22, answering `specs/6f-decisions-screen/6f1-preflight.md` on `task/6f1-decisions` at
`2cd32aec9` (implementer, against `main` at `c51ce8004`; 6a, 6c, 6h, IA-P1, IA-P2 merged). Code re-read on `main` at
`9f5552697`. Every ruling is a default applied now (W3). The pre-flight undercounted two classes, both checked by
script against the live registries and catalogue: the words a decision page can need (53 factors, not 17) and the
effect units (`KWH/DAY` too). It also missed one banned word already on `main` (D-P6.75). `spec.md` rev 2 §2b carries
these rulings. No figure moves. The owner is told of the unit card (D-P6.79) and may reword any client word below.

## D-P6.72 Factor words: the class is every factor a decision can name, and it gets its words now (Q1)

- **Ruling.** A decision page names a factor in four places: an effect row (`label`), `missing FACTOR` and `assumed`
  (`in_sentence`), and `change_answer` (`in_sentence`). The factors it can reach are the closure of `contribution`
  plus the closure of each lever's `purpose_factor`, over every registry a `LEVERS` entry names. On `main`, 53 of them
  have no vocabulary `factor` entry. U1 adds all 53 to `i18n/statements/en/vocabulary.py` `factor` (one home), as
  written below, appended to `order` in table order (the existing keys keep their relative order). The Architect
  wrote the words; the builder copies them exactly. A clash with `check_literal` or §6.4's banned words comes back.
  Style as the file: sentence-case `label`; `in_sentence` is `label` lower-cased once by hand; `article` by the
  sound of the in-sentence word; no digits, no system words.

  | Factor (structure) | label | article |
  |---|---|---|
  | `reduced_days` (MG) | Days with no standby generator | a |
  | `hours_per_day` (MG) | Committed supply hours a day | a |
  | `obligation_hours_without_redundancy` (MG) | Committed supply hours with no standby generator | a |
  | `liability` (MG, CC) | Customer credit notes | a |
  | `crate_days` (CC) | Crate-days stored | a |
  | `rate` (CC) | Storage rate | a |
  | `contract_crate_days` (CC) | Crate-days under contract | a |
  | `contract_rate` (CC) | Contract storage rate | a |
  | `base_kwh` (CC) | Chamber electricity when empty | a |
  | `k_kwh_per_crate_day` (CC) | Electricity per crate-day stored | an |
  | `model_factor` (CC) | Chamber electricity against its model | a |
  | `excess_kwh` (CC) | Electricity above what occupancy explains | an |
  | `elec_price` (CC) | Electricity price | an |
  | `maint` (CC) | Maintenance | a |
  | `handling` (CC) | Contract handling cost | a |
  | `uncovered_nights` (CC) | Nights the rota leaves uncovered | a |
  | `kwh_model` (CC) | Electricity the model expects | an |
  | `kwh` (CC) | Electricity used | an |
  | `energy` (CC) | Electricity cost | an |
  | `nights_without_backup_cover` (CC) | Nights without backup cover | a |
  | `chargers_in_service` (EV) | Chargers in service | a |
  | `charger_kw` (EV) | Charger power | a |
  | `import_limit_kw` (EV) | Grid import limit | a |
  | `window_h` (EV) | Charging window hours a night | a |
  | `buses` (EV) | Buses in the fleet | a |
  | `kwh_per_bus_night` (EV) | Energy each bus needs a night | an |
  | `nights_in_period` (EV) | Nights in the month | a |
  | `peak_kwh` (EV) | Energy charged at the peak rate | an |
  | `kwh_2200_2400` (EV) | Energy charged at the off-peak rate | an |
  | `kwh_0000_0500` (EV) | Energy charged at the night rate | an |
  | `max_kw` (EV) | Highest charging demand | a |
  | `peak_price` (EV) | Peak electricity price | a |
  | `offpeak_price` (EV) | Off-peak electricity price | an |
  | `night_price` (EV) | Night electricity price | a |
  | `demand_rate` (EV) | Demand charge rate | a |
  | `maintenance` (EV) | Maintenance | a |
  | `short_nights` (EV) | Nights short of charging capacity | a |
  | `spare_bus_nights` (EV) | Spare bus-nights | a |
  | `covered_bus_nights` (EV) | Bus-nights charged elsewhere | a |
  | `extra_missed_departures` (EV) | Extra departures missed | an |
  | `penalty_rate` (EV) | Penalty per missed departure | a |
  | `deliverable_kwh_night` (EV) | Energy the chargers can deliver a night | an |
  | `scheduled_kwh_night` (EV) | Energy scheduled a night | an |
  | `supplied_kwh_night` (EV) | Energy supplied a night | an |
  | `required_kwh_night` (EV) | Energy the fleet needs a night | an |
  | `buses_short_per_night` (EV) | Buses short of charge a night | a |
  | `departures_missed` (EV) | Departures missed | a |
  | `peak_cost` (EV) | Peak-rate charging cost | a |
  | `offpeak_cost` (EV) | Off-peak charging cost | an |
  | `night_cost` (EV) | Night-rate charging cost | a |
  | `demand_cost` (EV) | Demand charge | a |
  | `energy_cost` (EV) | Charging electricity cost | a |
  | `penalties` (EV) | Missed-departure penalties | a |

  `in_sentence` = `label` with its first letter lower-cased (every label above starts with an ordinary word, so no
  other letter changes). MG mini-grid, CC cold chain, EV EV depot.
- **The check (W6, written first in test 1).** Test 1 computes the reachable set itself from `row.children` (no
  import of `difference._closure`; W2) and asserts every factor in it has a `factor` entry with all three forms. It
  replaces "every `LEVERS` key in `LEVER_WORDS`" only in adding to it. Plant `noword` (drop `buses`' entry) fails it.
- **Why.** Words for 17 would leave the page raising on the nodes those leaves move (`charging_schedule`:
  `peak_cost`, `penalties`, `energy_cost`; `chamber_efficiency`: `kwh`, `energy`); the class is "a factor the model can put on a decision page", fixed by data and a
  computed check so a new lever or row cannot ship without words.
- **Reverse:** words for the 17 named factors only (the page raises on the nodes they move).

## D-P6.73 How an effect row shows a count or a rate (Q2)

- **Ruling.** Effects keep their stored order, with `contribution` always last (it is the sum; D-P6.74). Each row's
  figure is one stored value rounded once, signed against doing nothing, never computed. The format is chosen by
  unit for the four unambiguous units, and by factor for every other unit (`DAY`, `HOUR`, `1`, `MONEY/DAY` and
  `KWH/DAY` mean different things on different factors):

  | Stored unit | Fact | Shown as (example) |
  |---|---|---|
  | `L` | `Quantity(v, "L")`, 1 place, signed | "−250.0 L" |
  | `KWH` | `Quantity(v, "kWh")`, 1 place, signed | "+410.0 kWh" |
  | `MONEY` | `Money(v, currency)`, signed | "−$237.50" |
  | `KWH/HOUR` | `Quantity(v, "kW")`, 1 place, signed | "−12.0 kW" |
  | any other | `decision_page/tables.py` `EFFECT_FORMAT[factor_id]` | below |

  `EFFECT_FORMAT` (factor → stored unit, fact, noun or unit word, places); the view checks the stored unit equals the
  entry's and raises otherwise:

  | Factor | Unit | Fact | Word | Places | Example |
  |---|---|---|---|---|---|
  | `uncovered_nights` | DAY | Quantity | noun `night` | 0 | "−26 nights" |
  | `nights_without_backup_cover` | DAY | Quantity | noun `night` | 0 | "−26 nights" |
  | `contract_crate_days` | DAY | Quantity | noun `crate_day` | 0 | "+900 crate-days" |
  | `covered_bus_nights` | DAY | Quantity | noun `bus_night` | 0 | "+2 bus-nights" |
  | `extra_missed_departures` | DAY | Quantity | noun `departure` | 0 | "+1 departure" |
  | `departures_missed` | DAY | Quantity | noun `departure` | 0 | "−2 departures" |
  | `reduced_days` | DAY | Quantity | noun `day` | 0 | "−5 days" |
  | `obligation_hours_without_redundancy` | HOUR | Quantity | noun `hour` | 0 | "−20 hours" |
  | `buses` | 1 | Quantity | noun `bus` | 0 | "+6 buses" |
  | `buses_short_per_night` | 1 | Quantity | noun `bus` | 0 | "+1 bus" |
  | `model_factor` | 1 | Percent, signed | none | 0 | "−15%" (a ratio, not a count) |
  | `contract_rate` | MONEY/DAY | Price, signed | unit `crate-day` | as Price | "+$0.80 per crate-day" |
  | `scheduled_kwh_night` | KWH/DAY | Quantity | unit `kWh_per_night` | 1 | "−40.0 kWh a night" |
  | `supplied_kwh_night` | KWH/DAY | Quantity | unit `kWh_per_night` | 1 | "−40.0 kWh a night" |
  | `required_kwh_night` | KWH/DAY | Quantity | unit `kWh_per_night` | 1 | "+180.0 kWh a night" |

- **What the vocabulary and formats gain (U1; shared, reach in D-P6.76).**
  - `noun`: `night` (night/nights), `crate_day` (crate-day/crate-days), `bus_night` (bus-night/bus-nights),
    `departure` (departure/departures), `hour` (hour/hours), `bus` (bus/buses); `day` exists.
  - `unit`: `kW` "kW", `kWh_per_night` "kWh a night", `crate-day` "crate-day". A key may sit in `unit` or `noun`,
    never both (a vocabulary test).
  - `formats.quantity`: when the fact's unit is a `unit` key, as today; else it is a `noun` key, and the word is its
    `one` form when the displayed digits are exactly `1` (including "less than 1 night"), else `other`. A key in
    neither raises (as today).
  - `schema.OPTIONS["price"]` and `["percent"]` gain `signed: (False, True)`; `formats.price` and `formats.percent`
    pass it to `_number` in place of the hard-coded `False`. The default `False` keeps every existing statement.
  - `decision_page.py` gains one statement `effect` with four figure variants (`QUANTITY`, `PERCENT`, `PRICE`,
    `MONEY`), each a single signed slot, chosen by the table above.
- **The check.** Test 1 computes each option's effect scope from the registries (changed leaves, plus every node of
  the `contribution` and purpose closures that rests on one, plus `contribution`) and asserts each factor in it has a
  generic unit or an `EFFECT_FORMAT` entry whose unit matches the row. Plant `nounit` (drop `buses`) fails it.
- **Why.** A count is shown in its own noun, so "−26 nights" reads as the operating world says it; a ratio is not a
  count, and a money rate keeps its "per" word. The noun belongs to the factor, not to `DAY` (crate-days, bus-nights
  and departures are all `DAY`).
- **Reverse:** counts as bare numbers with the noun in the label (loses the plural and the unit beside the figure).

## D-P6.74 The contribution row's heading is "All headings" (Q3)

- **Ruling.** Vocabulary `heading` gains `ABOVE` (label "All headings", in_sentence "all headings"). An effect row
  whose factor's home category is `ABOVE` shows it. `CALENDAR` can never be in an effect scope (a calendar leaf is
  never changed, and no node in scope rests only on calendar leaves); one in a row raises (test 1's scope check
  covers it).
- **Why.** Contribution is what every heading adds up to; putting it under the decision's own heading (the default)
  would show Thika's contribution change under "Protect asset and capital" and Mwea's under "Grow revenue", which is
  not true of the figure. The four headings stay the only categories; this word says the row is their sum.
- **Reverse:** the decision's own heading (the builder's default).

## D-P6.75 The charging-schedule study words lose the banned word "replay"

- **Ruling.** `decision_lever.study` `CHARGING_SCHEDULE` becomes "a simulation of {site}'s own charging in {month}
  under this schedule" (F6-S reads "Not available yet: needs a simulation of Embakasi's own charging in October 2026
  under this schedule"). `backend/tests/statement_cases/decision_lever.py` changes its one case to match. D-P6.55's
  mechanism stands; only its quoted words change. Class sweep (W6): test 1 runs §6.4's banned-word check over every
  `decision_lever.*` variant rendered through its statement cases, not only the fixtures' pages; on `main` this one
  variant is the only hit (checked).
- **Why.** §6.4 bans "replay"; F6-S's page would fail test 1. "Simulation" is the word the page already uses for the
  generator's missing study (`missing SIMULATION`).
- **Reverse:** exempt the string (a second exception to a client-language rule).

## D-P6.76 What D-P6.72 to D-P6.75 reach, and the parity test

- **Shared changes and their reach.**
  - Vocabulary `factor`, `heading`, `noun`, `unit` (additions only): every screen rendering SC-1 statements. Pages
    that read these vocabularies today: the Site deep dive and the Portfolio period and Sites reads (5c, IA-P2:
    `deep_dive.*`, `portfolio_sites.*`, mini-grid steps only), the Optimize card scope line (1a, noun `day`), the
    agreed-change refusal (3C2, noun `character`), the energy-cover lines (0K4e, unit `kWh`), budget lines
    (`common`). None passes a new key, so none changes. All Site types; all role sets (read only).
  - `formats.quantity` (noun agreement) and the `signed` option on `price` and `percent`: every quantity, price and
    percent slot product-wide (the same pages). Existing slots pass `unit` keys and leave `signed` at its default,
    so none changes.
  - `decision_lever.study`: only the decision page (6f1); no other reader on `main`.
  - Meant to change: the decision page only.
- **Parity test (written first; golden captured from `main` at 6f1's base before any change).**
  `backend/tests/test_6f1_words_parity.py`: renders every case in `backend/tests/statement_cases/` except
  `decision_page.*` and `decision_lever.study`, and compares byte for byte with a golden JSON captured at the base
  commit. Also unchanged and run at the slice end: `test_sc1_statements.py`, the 5c deep-dive view tests, IA-P2's
  period and sites tests, 1a's card test, 0K4e's dispatch words test, and `tools/checks/statement_catalogue.py`
  (output identical to `main` except the added `decision_page.*` statements and the changed `decision_lever.study`
  line, shown as a diff in the packet). A difference elsewhere is a fault in 6f1, never a golden to refresh.
- **Why.** The 22 Nov usage rule: a ruling that changes shared behaviour names its reach and proves the rest
  unchanged.

## D-P6.77 Unit 1's other questions (Q4 to Q12)

- **Q4** Accepted: `DecisionPageRead` filters `AgreedActionService.for_tenant` by `agreed_action_id`; `actions/` is
  unchanged.
- **Q5** Accepted: `DecisionService.name_of(tenant_id, person_id)` through `_call` (a store fault is
  `StoreUnavailable`).
- **Q6** Accepted with one home: `bundle` and `for_tenant` read option records through 6h4's
  `latest_option_records(tenant_id, decision_id)` (never a second "latest" query); `OptionView.records:
  tuple[str, ...]` (factor ids, `changes` order). Additive.
- **Q7** Accepted, and the source line completed. With no study identity (every named-option run): `frame_kind`,
  `study_days`, `study_input_class` null, `months_averaged` (); `horizon_basis` reads `STATED`; `source` by the run's
  `source_class`: `RECORDED` → `RECORDED` (`RECORDED_STATED` when any shown option reads an option record);
  `EMULATED` → `EMULATED`; `SIMULATED` → new `SIMULATED_RECORDS` "Simulated: from {site}'s simulated records, not
  measured on site" (`SIMULATED_RECORDS_STATED` "Simulated: from {site}'s simulated records and the documents stated
  for each option, not measured on site" when any shown option reads an option record). The DD world's Sites are
  `demo-simulated`, so every 6h page in the demo takes this line; without it the view had no variant (simulated data
  is never shown as observed). F6-N, F6-T and F6-S assert their line.
- **Q8** Accepted: `DECLARED` → `RECORDED` through 5c's `SCREEN_EVIDENCE` (imported, not retyped); `NEUTRAL` raises
  (D-P6.61 never stores it).
- **Q9** Accepted: `decision_page.refused` has three variants (`DECISIONS_UNAVAILABLE`, `BAD_RANGE`,
  `DECISION_NOT_FOUND`); 401 renders `person.person_required` as `deep_dive_api.py` does. §3.4's row is amended.
- **Q10** Accepted: `decision_page/*.py` and `decision_page_api.py` join `ADOPTED`; each `decision_page.*` variant
  has a hand-written case in `backend/tests/statement_cases/decision_page.py`.
- **Q11** Accepted: `site` = the Site name; `month` = the decision period as `Month` (`month_year`, "October 2026").
- **Q12** Answered now from `i18n/formats.py`: minus is U+2212 "−", plus "+", USD prefix "$", any other currency
  its code and a space ("KES 1,200.00"), thousands comma, money 2 places half-even, a non-zero value that rounds to
  zero reads "less than" the smallest unit. Test 1's literals use these.

## D-P6.78 Units 2 and 3's questions (Q13 to Q19)

- **Q13** Accepted: the cache `get` takes a reader function per kind; existing callers pass the bound client method.
  Shared UI part: reach Portfolio, Findings, Actions lists (all Site types); their existing tests run unchanged.
- **Q14** Accepted: `watching` goes (a record has no such state); the W6 sweep greps "Being watched" over
  `frontend/src` and records the result.
- **Q15** Accepted: "No decisions in this range." (IA-P's words); §4.3 reads them.
- **Q16** Accepted: "Not available yet" (D-P6.52).
- **Q17** Accepted: tile = E0 now; the badge half is checked in §4.4's sweep by whichever of 6f1 U2 and IA-P3 lands
  second.
- **Q18** Accepted with one engine: `main.py` builds `build_decision_page` once; `DecisionWaiting` takes that read's
  `DecisionService` (no second `build_decisions`), disposed with it on shutdown.
- **Q19** Accepted: route `/decisions/:decisionId`; `IA_HOMES` keeps Decisions current on it.

## D-P6.79 Unit card: 6f1 is 4.25 u

- **Ruling.** U1 1.5 → 2.0 u (53 words and their check, the formats change with its parity golden, the effect table,
  the two source variants); U2 0.5, U3 1.5 unchanged. 6f1 is **4.25 u**, three units, under 6.
- **Why.** The words and the shared formats change are U1's; the parity golden is the 22 Nov rule's cost.
- **Owner.** Told of the +0.5 u. The client words of D-P6.72 to D-P6.75 are defaults the owner may reword at the
  walkthrough; none blocks. D-P6.65 (Thika's comparison) is still the owner's open question.

## D-P6.80 U1 build deviations accepted: five `effect` variants; two named `test_sc1_statements.py` lines; `frame_kind` null

- **Ruling.** (1) `decision_page.effect` has five variants: `QUANTITY` (a `unit` word, 1 place), `COUNT` (a `noun`
  word, 0 places), `PERCENT`, `PRICE`, `MONEY`. One SC-1 slot carries one `places` setting, so D-P6.73's `QUANTITY`
  splits in two. The texts are D-P6.73's examples exactly. (2) D-P6.76's parity list is amended. In
  `test_sc1_statements.py`, T8 (the statement set: `decision_page.*` added) and T12 (`signed` in the `price` and
  `percent` options) change their named lines only. Every other test there, and the words parity golden, stays byte
  for byte. (3) A run with no study identity has `RunSummary.frame_kind` None, as do `study_days` and
  `study_input_class`. D-P6.77 Q7 overrides §3.1's "`DECLARED_SEASON` when absent", which now applies only when an
  identity exists without `frame`.
- **Why.** (1) and (2) are consequences of D-P6.73 that the ruling did not foresee: no behaviour or word moves.
  (3) A named-option run has no season, so naming one would be false.
- **Reverse:** none needed.

## D-P6.81 Number-word rewordings: "one-off" stays by a narrow guard exemption; the 10 % is a figure; the rest ratified or amended

Ratifies with changes the 6f1 handoff's number-word deviation (`6f1-handoff.md` at ea2a19585). Amends §3.4's words,
D-P6.50's "Not started" line and D-SC1.32's scan. Mock: vNEXT `loop-site.js` column "One-off cost · who pays".

- **The class (W6).** The guard refuses a token that states a count, so a figure cannot hide in a template. Three
  kinds of word hit it here, and each gets its own answer. (a) An idiom that states no count: "one-off" means "not
  recurring", and there is no other plain word for that. It gets a narrow exemption. (b) A pronoun or conjunction
  ("the one", "choose one", "once the change is made"): an exact plain word exists, so it is reworded. (c) A real
  figure ("a tenth", "zero"): the figure goes in a slot from the model, or the word says the state without a number.
- **(a) The exemption, `schema.NUMBER_WORD_IDIOMS["en"] = (("one", ("off", "offs")),)`.** In `check_literal`, after
  the split into letter runs, a `one` token is skipped only when the separator between it and the next token is a
  single `-` or `_` and that next token is in the pair's tails (case-folded). Nothing else changes: `one` alone, "one
  off", "one--off", "one-of" and "twenty-one-off" (`twenty` is still refused) are all still refused. The same rule applies to variant ids, because `ONE_OFF` is the same lexeme in identifier form.
  T12b gains loads, each alone in a template: "one-off cost", "One-off", "one-offs", the variant id
  `ONE_OFF_CURRENCY`. It gains rejects, each alone in a template: "one off", "one-of", "one", "one-offer", "first-off".
  A new idiom needs an Architect ruling that shows it states no count.
- **Why an exemption and not a rewording.** "Set-up" and "upfront" are false for a fee, a contract term or a
  deposit, which are one-offs but are not set-up costs. "Non-recurring" is jargon. The mock says "One-off cost", and
  6a and 6c, the CLI (`state_one_off.py`) and the stored codes all use the same name. A rewording would split one
  concept into two names and depart from the mock.
- **Final words** (replace §3.4's and the handoff's; slots unchanged unless stated):
  - "One-off" as §3.4 wrote it: `one_off` STATED "costs {amount}" · NIL "no one-off cost" · MISSING "one-off cost not
    stated yet"; `one_off_detail` STATED "{amount} one-off, stated by {person} on {day}: {basis}"; `cost_answer`
    STATED "{amount} one-off, stated by {person}" · NIL "No one-off cost" · MISSING "One-off cost not stated yet";
    `all_columns` COST "One-off cost"; `missing` ONE_OFF "Not available yet: needs the one-off cost of this change,
    stated by the Site manager or the finance lead".
  - `missing` ONE_OFF_CURRENCY "Not available yet: the one-off cost is in a different currency from the month's
    figures" (plainer than "another currency than").
  - `missing` CURRENCY_MISMATCH "Not available yet: the month's figures are in different currencies". This is the
    existing `deep_dive` wording. "Several" was false for two currencies.
  - `missing` NIL_DENOMINATOR "Not available yet: {factor} cannot be worked out, because a figure it divides by is
    nil" (ratified: "nil" is plain business English for the stored state, and it states no count).
  - `can_choose` ANY "{who} can still choose an option, or none." · `how` "... and recommends an option. ..."
    (ratified).
  - `why_rule` SETTING "Each setting that passes the service checks is valued against doing nothing, over the same
    figures that make up the month's contribution. The setting worth the most is recommended; among the settings
    within {margin} of it, the setting closest to today's settings. The dawn readings are shown beside each setting
    and never decide." · `why_rule` OPTION "Each option is valued against doing nothing, over the same figures that
    make up the month's contribution. The option worth the most is recommended; among the options within {margin} of
    it, the option highest on the list."
  - `why_answer` NEAR "It is within {margin} of the best value and the closest to today's settings." · new twin
    NEAR_OPTION "It is within {margin} of the best value and the highest on the list." The §3.4 twin rule applies:
    NEAR names today's settings, which a named-option lever does not have.
  - `change_caption` FIRST "{option} (the setting highest on the list that passes): change a month against doing
    nothing". The rule is position order (§4), not time, so "earliest" would mislead.
  - "once" → "when": `reason` BOUNDS_NOT_CHECKED "Its limits are checked when bounds are set." · `limits_answer`
    NO_CHECKS "These options have no service checks; their limits are checked when bounds are set" ·
    `verify_answer` "Working and money are checked separately, after the change is made" · `verify_items` STATE "Not
    started: the checks begin when the change is made." (ratified, with "after" in `verify_answer` because the checks come after the change; amends D-P6.50's line).
- **`{margin}`** is a `percent` slot (D-P6.73's shared format, 0 places, unsigned). Its value is `1 - TIE` read from
  6c's evaluator constant (`TIE = Decimal("0.9")`, D-P6.16) and never retyped, so it reads "10%" today and follows
  the model if the model changes (one figure, loyal to the model). "Valued close to the best" is refused: it hides
  the rule's figure.
- **Variant ids.** `ONE_OFF` and `ONE_OFF_CURRENCY` are restored and equal 6c's codes, with no mapping. `NIL`
  (`one_off`, `cost_answer`) and `NIL_DENOMINATOR` stand ("zero" stays refused), and the view maps 6c's `ZERO` and
  `ZERO_DENOMINATOR` onto them in one table. Test 1 asserts that every 6c code reaches a variant.
- **Cost.** The exemption, its T12b lines and the restored ids are U1 work: +0.25 u, so 6f1 is **4.5 u**. The words
  parity golden is unchanged, because no existing template contains "one-off". `test_sc1_statements.py` T12b changes
  only its named load and reject lines (it joins D-P6.80's named-line list).
- **Owner.** Told: "one-off" keeps the mock's word through a narrow guard exemption; the near-best rule now prints
  its 10 %. These are defaults the owner may reword at the walkthrough.
- **Reverse:** drop `NUMBER_WORD_IDIOMS` and use "upfront cost" (a MOCK DEVIATION of the wording category).

# D-P6.82 to D-P6.87: the 6f1 U1 open points, and U2 and U3 against main after IA-P3

Architect (Claude), 2026-11-23. Read: `6f1-handoff.md` at `59087a0c5` (`task/6f1-decisions`), `main` at `558b32f32`
(IA-P3, 6h, DD3b merged), the vNEXT mock's `decisions` def (`ia-shapes.js:346-355`) and `uxDecisionSlots`
(`loop-ux.js:699-774`). Spec rev 3 is `spec.md` §14; build cards `cards/6f1-U2.md`, `cards/6f1-U3.md`.

## D-P6.82 U1's seven open points, and four words the sweep found false

- **1 Accepted, as one helper.** `first_missing()` returns the text or raises a named `ValueError`; `at_stake` and the
  rec card both call it (the card no longer skips the sentence). `result()` raises the same way for a
  `VALUE_NOT_AVAILABLE` option with no entry (same class). 6c R2 writes the entry with the code
  (`evaluate.py:216-218`), so its absence is a code defect.
- **2 Not accepted.** `decision_lever.option_label`'s four percent slots become `optional: True` (as
  `decision_page.why_answer`'s `margin`), and a named option passes none. Why: the view hands the renderer a 0% no
  record holds, and a missing value is never 0. Reach: only the decision page reads the statement; no text moves.
  If a catalogue guard refuses an optional slot there, keep the default and say so.
- **3 Not accepted.** `rec.chip_title` is the `source` line's text (§3.4 `source`, already built) when `chip` is set,
  else null. Why: §5.2 makes it the chip's accessible description; the words exist and have one home.
- **4 Accepted** (`factor_label`). **7 Accepted:** `decision_page_codes.py` stays outside `ADOPTED` (the 5c
  precedent); it holds no English.
- **5 Not accepted.** `MARGIN` carries `Evidence("DECLARED")`, as the settings do (`_SETTING`); the four cases assert
  `["Declared"]`. Why: 10% is the rule's stated constant; "Estimated" is false, whether shown or not.
- **6 Not accepted.** `horizon_basis` gains `MONTH` (exactly one month averaged): "Over {horizon}: {horizon_count}
  times the change worked out for {month_list}" ("Over 12 months: 12 times the change worked out for October 2026").
  `MONTHS` stays for two or more. Why: "the average of 1 month" is not plain, and one month is the usual case.
- **Found in the sweep (same fix round; each word is false in a state the demo has):**
  - a. `why_answer` NONE and `all_answer` count the options without the baseline (mock `optsShown`,
    `loop-ux.js:744-763`): F6-B "13 of 13 options are rejected or deferred", "13 options against doing nothing; ...".
  - b. `rec_heading` reads `NOT_VALUED` when no option but the baseline has a value (run or not), `VALUED` when every
    option but the baseline and the `REJECTED` has one, else new `PART` "Some options are valued against doing
    nothing". F6-B, F6-S: "The options, not valued yet". Today it says "Each option valued" with none valued.
  - c. `change_caption` gains `FIRST_OPTION` (a named lever) "{option} (the option highest on the list): change a month
    against doing nothing", and `NOT_VALUED` (no run) "The options have not been valued yet, so no change is shown".
    `NONE` stays for a run whose every setting is `REJECTED`.
  - d. `sticky.title` is the H1's text (`question` in `NOT_VALUED`/`WAITING`, else `title`), as the mock's `d.q`.
- **Check.** Each variant has its hand case; every literal that moves is listed in the packet. Plants: `base` (count
  the baseline) fails F6-B; `heading` (`VALUED` for F6-B) fails F6-B.
- **Reverse:** the handoff's defaults.

## D-P6.83 U1's unbuilt fixtures finish in U1's fix round

- **Ruling.** F6-J, F6-N, F6-T, F6-S and `--write-fixtures` are U1's, built in its fix round with D-P6.82, on
  `task/6f1-decisions` after main is merged in (one conflict, `.ai/state/index-3.md`). U1 merges to main on ACCEPT.
- **Worlds.** N, T, S add Sites `MWEA-001` "Mwea", `THIKA-001` "Thika" (COLDCHAIN) and `EMBAKASI-001` "Embakasi"
  (EV) to `decision_page_world.py`, and store the rows 6h's own evaluator returns for `n1`, `t1` and `s1` bases
  (`option_fixtures.py`); S at period 2026-10, horizon 12 (6h spec §7). The page literals are written by hand. N's and
  T's `source` line is `RECORDED_STATED` (6h's records are `observed-financial`). S's is by its `source_class`.
  `SIMULATED_RECORDS*` is asserted by its statement cases. F6-T's caption is `FIRST_OPTION`.
- **`decisions_list.json`** (`{"rows", "total_count"}` from `list_rows`): seven decisions prepared one minute apart,
  listed newest first. Mini-grid ones are in one Kobo world, each with the `finding_id` named (an
  `add_finding(..., "GENERATOR_SUPPORT_CANDIDATE")`), so each is its own record:
  1. F6-C, `f1f1f1f1-0000-4000-8000-000000000001`; 2. F6-A at period 2026-09, no Finding; 3. F6-G, `...0008`;
  4. F6-N, no Finding; 5. F6-S, no Finding (`charging_schedule` is on no pin); 6. F6-H, `...0002`; 7. F6-F, `...0007`.
  Waiting: 4 (1, 2, 4, 5); by Site `KOBO-001` 2, `MWEA-001` 1, `EMBAKASI-001` 1. The ids of the Findings are the
  portfolio fixture's (`iap/portfolio.json`).
- **`decision_page_*.json`:** A, B, C, D1, E, G, H, N, S, T.
- **Why.** They are the only pages of named-option levers (seven of nine demo Sites); U1's discovery review cannot
  accept the view without them, and U2 and U3 test on the files. Units: U1 2.25 -> **2.5** (D-P6.82; D-P6.83 was already
  U1's).
- **Reverse:** to U2 (a frontend unit that would own backend page literals).

## D-P6.84 One waiting set: the decisions read, for the whole range; E0 retires (amends D-P6.44, D-P6.52, D-P6.78 Q13, Q17, Q18; spec §4.1, §4.2)

- **Ruling.** Every "waiting for a choice" figure is the count of rows in `NOT_VALUED` or `WAITING` of
  `GET /api/decisions` for the **whole** shared range: the Decisions tile, the inbox badge, the Sites list column and
  the Outcomes rows. `waitingForAChoice(items)` (IA-P3's one function, taken over) and `waitingBySite(items)` are the
  two readers of that one set. The `DecisionWaiting` port is not built. E0's `waiting_count` and `waiting_by_site` are
  removed from the estate portfolio body, with `waiting_count()`, `waiting_by_site()`, `_waiting`, `WATCHED_GROUP` and
  `test_iap_waiting_counts.py`; so there is no second `DecisionService` in `main.py` and Q18 falls away.
- **Why.** Read on main: (1) `/api/estate/portfolio` is a stored route, and no decision table is one of its watermark
  inputs (the `chain_input_change` triggers, migrations 0047 and 0058), so a count inside it would stay stale after a
  choice, and tile and column would differ; (2) that read is capped at 31 days (P0) while `/api/decisions` is not, so
  a three-month range would list three months and count one; (3) an unread placed-Finding count left in the body is a
  second figure for one quantity. Records need no cap, so the range rule holds whole.
- **Client (amends D-P6.78 Q13).** `EstateClient` gains optional `decisions?(range: DayRange)` (as
  `getOutcomeSummary?`: an absent method reads as unavailable, so existing fakes stay valid). The cache keeps its form
  (no reader function per kind); `EstateReadKind` gains `"decisions"`. Cache keys (`rangeKey` in
  `createEstateReadCache` and `useEstateRead`'s `key`) add the **whole** range's days: two ranges that share their last
  31 days must not share decisions, and the two range forms must not clear each other's reads. `queryFromParams`
  gains `days: DayRange` (the valid shared range; else the request bounds' first ten characters, the server judges).
- **`known_at`.** The records read takes no cutoff. With `known_at` in the address, each surface that draws decision
  rows or counts says "Decisions are shown as they stand now, not at the earlier cutoff." (list and Overview panel
  `role="note"`; Sites column note). The Decisions page drops `EstateCutoffLine` (it states the Findings read's
  cutoff); `RangePartNote` goes from the Decisions panel, and `/decisions` joins `WHOLE_RANGE_PAGES`.
- **Reach (parity).** Pages: Decisions, Findings, Overview, Sites, Outcomes, and the shell of every operator page; all
  three Site types; every role (read only). Meant to change: the named cells. Meant to stay: the estate portfolio body
  minus two keys (`test_w303_portfolio_api.py` changes that line only), the Findings and Actions rows, Results.
- **Reverse:** D-P6.44's E0 port, plus decision tables as watermark inputs (a migration) and a capped list.

## D-P6.85 The list on main: facets, order, the join, and Finding types

- **Facets.** State (four words) and **Heading** (`Grow revenue`, `Optimize cost and efficiency`, `Protect asset and
  capital`, `Assure performance and returns`; the row's `heading.word`, "All headings"). "Finding type" (`lens`) goes: a record has no lens, and a
  decision without a Finding would vanish under it. The mock's second facet, Due, has no source (MD-6F-3); Heading is
  the mock's own Findings facet. MD-6F-10. The alias `/portfolio/act-first?lens=` becomes `heading=`: cost →
  `optimize`, risks → `protect`, opportunities → `grow` (mock `ia-routes.js:63`; `LENS_OF_CATEGORY`); gate L3 checks
  the chip "Optimize cost and efficiency · All headings".
- **Order and cap.** Sorts: "Newest first" (the read's order) and "Site". Waiting rows are kept inside the cap (mock
  `keep: iaWaiting`, missing on main).
- **At stake** shows `at_stake.text` and, when `at_stake.evidence` is not empty, its words as `<small>` (the Sites
  headline's form), so a simulated or modelled figure never stands bare.
- **The 6h gate and Finding types.** G-6h is met (6h merged; `PENDING_LEVERS` empty). A record can cover a placed
  Finding only when its mechanism is in `PINS` and the pinned row lists the lever (6a P4): `GENERATOR_SUPPORT_CANDIDATE`,
  `UNEXPLAINED_FUEL`, `COLD_START_FAILURE`, `COLD_EXCURSION`, `EV_INTERRUPTION`. The client holds **no** table of Finding
  types: the only join is `finding_id`. "Its decision" reads the newest `period`'s record (a tie: the read's order);
  with none, "Not available yet" for every type (D-P6.78 Q16; main's "No decision open" goes: the product cannot say a
  decision is not needed, only that none is recorded). A Finding covered by no record leaves the Decisions list for
  the Findings list; its recommendation view stays one link away there.
- **Merge and the demo.** Until WK-SC prepares the ten decisions (D-DD.173), the Decisions list, inbox and waiting
  column are empty, said as "No decisions in this range." U2 merges on ACCEPT; the coordinator does not rebuild a demo
  app from main between U2 and WK-SC without saying so.
- **Reverse:** keep `lens` by a client join on the placed row (drops decisions with no Finding).

## D-P6.86 The decision page against main: five amendments to spec §5

- **Who pays.** The mock's cards and cost section say who pays; a one-off record has no payer (6a: amount, currency,
  crew visits, basis, who stated it). The cost section's body adds the chrome line "Who pays for each change: not
  available yet." MD-6F-11, D1. Spec §9 had no row: an unlabelled departure.
- **The Finding line** (§5.5) reads the shell's cached portfolio read, which is capped at 31 days. Its words: found →
  "The Finding behind it: {title}" linked by `findingLinkLive` and `linkFor(link_refs.finding)`, plain text when not
  live; loaded and not found → "The Finding behind it is outside the days shown."; loading → "Loading the Finding…";
  refused → "The Finding behind it cannot be read right now."; `finding_id` null → "Opened with no Finding behind
  it." ("from the setting itself" is false for a named-option lever).
- **Show all.** The button reads "Show {n} more options" with n the hidden cards, never the baseline (it is first);
  "Show all 14 options" beside "13 options against doing nothing" would be two counts of one quantity. Amends D-P6.48.
- **Shared parts.** `ui/Drawer` and `useDrawers` (IA-P3 P6), `ui/Breadcrumbs` (three parts, D-IAP.38), `ui/Disclosure`
  inside `.panel.dp-sec`, `StatusPill`, the range-carrying `RangeLink`; the month link is `monthDays(period)`. The scope
  chip (`EverySiteChip`) is not drawn: the page is one object (as Site and record pages, D-IAP.50).
- **Kept as it is** marks no card `is_chosen` (as U1 serves it): the choice line and the pill say it.
- **Reverse:** per item, spec §5 as written.

## D-P6.87 Units, branches and merge order

- **Ruling.** U1 2.5, U2 0.5 -> **1.25** (one cache key, six consumers, E0's removal, the shell test migration), U3
  1.5: 6f1 is **5.25 u** (cap 6). U1 merges first. U2 (`task/6f1-u2-list`) and U3 (`task/6f1-u3-page`) then build from
  main in parallel, one discovery review each; **U3 merges before U2**, because U2's rows link to U3's route. They share
  four files, one block each: `estateClient.ts` (one optional method each), `App.tsx`, `shell/iaRoutes.ts`,
  `.agent/mock-departure-register.md`. Each has its own client module (`estate/decisionsListClient.ts` U2,
  `estate/decisionPageClient.ts` U3).
- **Why.** IA-P3 landed second surfaces (inbox, search, Sites and Outcomes columns, whole-range pages) that rev 2's U2
  did not hold. Stacking would hold U3 behind a list it does not read.
- **Owner.** Told, no decision asked: the Decisions filter "Finding type" becomes "Heading"; the list and inbox are
  empty until WK-SC; who pays is not recorded.
- **Reverse:** one branch, U1 to U3 in order.
