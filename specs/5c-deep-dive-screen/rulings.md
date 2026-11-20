# 5c rulings

Architect (Claude), 2026-11-20. Each ruling is indexed in `.ai/decisions/index-rulings-13.md`.

## D-5C.1 The one deep-dive screen is a Portfolio tab, "The month", in the hub shape

- **Ruling.** `/portfolio/month` in the live product, a tab after Overview, laid out as IA-1b's hub (L1 headline and
  four tiles, L2 panels, L3 answer-titled sections, drawers inside sections). MOCK DEVIATION MD7 (D5): the vNEXT
  Overview itself becomes this screen when IA-2 rebuilds the live Overview.
- **Why.** RC6 puts `5c` before IA-2; replacing the live Overview now would change a screen IA-2 rebuilds (reviewed
  twice, D-BW1.9). A tab keeps one interaction grammar with the Portfolio.

## D-5C.2 The server writes every figure and word; the browser only renders

- **Ruling.** `month_view` returns display strings; the page never formats, adds or compares a figure (the bar's
  width is the one exception).
- **Why.** One place for Decimal arithmetic and the words, testable to the cent; a second formatter in TypeScript
  would be a second source of truth (owner: honest numbers).

## D-5C.3 The evidence word on this screen

- **Ruling.** NOT_AVAILABLE "Not available yet", ESTIMATED "Estimated", MODELLED "Modelled"; otherwise by the
  weakest origin: emulated "Emulated", simulated "Simulated", unknown "Estimated", observed or field by evidence
  ("Recorded", "Measured", "Calculated"). Never "Verified".
- **Why.** 3A5's rule applied to this screen only (D-BW1.9); D14: emulated is never Recorded; the weakest part sets
  the label.

## D-5C.4 Every money figure carries the month's reconciliation, read at the snapshot's "as of"

- **Ruling.** A money figure's word is 3A7's `money_word(word, standing)`: the organisation's standing for portfolio
  figures, each Site's for its own; read with `known_at = served.as_of`. "Not available yet" carries no suffix.
- **Why.** 3A7: money reads "not yet reconciled" until a closed month matches; D-3A7.9: the standing labels the figure
  of its own instant, so a statement recorded after the snapshot does not relabel older figures.

## D-5C.5 The waterfall's steps are the heading rows; drivers sit in the step's drawer

- **Ruling.** Steps are the bridge rows `revenue`, `fuel_cost`, `om`, `staff`, grouped by each row's own home; the
  groups' values are their steps' sums; driver rows (kWh, litres, prices) appear in the drawer with their own "k of n".
  `by_home` is not shown on this screen. MOCK DEVIATION MD4 (D1).
- **Why.** Every Site splits to headings; drivers exist only where observed (none on a typical export). Heading rows
  add to the gap exactly once with one Site set each (D-5B.12); `by_home` moves loss lines between headings once
  revenue splits, which would show a second "Grow" figure.

## D-5C.6 n is the Sites asked; each figure has its own "k of n"; a Site left out is named with its own target

- **Ruling.** `n = len(snapshot.asked)` (3B7a ruling 15); each row's k is its own; a Site out of a row is named with
  the reason and the records that would bring it in, and its own target where it has one, never added.
- **Why.** Owner "k of n sites"; D-5B.9 and D-5B.12; 5b queue Q5's default.

## D-5C.7 On a real-data server the screen needs a signed-in person of the tenant

- **Ruling.** With the real-data switch on, `GET /api/portfolio/month` refuses without a person of the served tenant
  (401). With it off (rehearsal, demo) no person is needed.
- **Why.** RC4 keeps an operator's data in its own database under a data-processing agreement; an open route would
  serve their money to anyone who reaches the server. RC7 (the executive does not sign in) holds: this fortnight the
  owner presents on the rehearsed tenant. Owner queue Q2.

## D-5C.8 The agreed change is read through a port that 3C2 fills

- **Ruling.** `AgreedActionsPort.for_tenant` and the contract in spec §4.3 (the read and the `record_action` command)
  bind 3C2's spec. Until 3C2 merges the panel reads "Not available yet" naming the Action.
- **Why.** RC9: the first agreed change is an Action with its owner and due date, not valued; 3C2 owns Actions; one
  seam, defined once, keeps 5c buildable before 3C2.

## D-5C.9 Every stop is worded by one rule: why, then the records that would fill it

- **Ruling.** Each `NOT_SPLIT` reason and each RESIDUAL (kind first, D-5B.15) has one sentence; the records come from
  the row's unobserved leaves (a 4d note first) in a fixed order, with target leaves as budget lines.
- **Why.** D-5B.10; plan §0.4 "each naming the record that would fill it"; one rule cannot drift by row.

## D-5C.10 A budget disagreement is shown in the bridge section, never only in a drawer

- **Ruling.** Each `PortfolioBridge.disagreements` entry is a visible note under the bridge's title; carried figures
  say "(estimate)" and name the missing record.
- **Why.** P5 rule 2 ("a difference is shown, never hidden"); the Kisiwa disagreement lives only on this screen.

## D-5C.11 "What is not available yet" groups the missing records by kind, with the Sites

- **Ruling.** One row per record kind (fixed order), naming what it would fill and the Sites concerned, plus one line
  for what is not built (valuing changes; Protect).
- **Why.** The executive sees what to send, once per record, not once per factor and Site.

## D-5C.12 Caps that scale to 300 Sites

- **Ruling.** Drawer Site lists and by-Site tables show 10 Sites, then "Show all {n}"; the not-available list 8 rows;
  Actions 3.
- **Why.** UI standing brief: exposure that scales from 3 to 300 Sites without changing the page's shape.
