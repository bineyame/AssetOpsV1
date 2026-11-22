# 6f rulings (D-P6.42 to D-P6.58): the Decisions screen, and 6h

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
