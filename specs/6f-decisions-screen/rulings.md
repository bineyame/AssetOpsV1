# 6f rulings (D-P6.42 to D-P6.50): the Decisions screen

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
