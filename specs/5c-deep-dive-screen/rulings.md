# 5c rulings

Architect (Claude), 2026-11-20; rev 2 the same day (D-5C.13 to D-5C.18, D-5C.4 amended, handshake answers below).
Each ruling is indexed in `.ai/decisions/index-rulings-13.md`.

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

- **Ruling.** A money figure's word is 3A7's `money_word(word, standing)`, with the organisation's standing for
  every money figure on this screen, portfolio and by Site alike (rev 2, handshake R8: Site statements are not read
  by the deep-dive); read once with `known_at = served.as_of`. "Not available yet" carries no suffix.
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

- **Ruling.** Each `PortfolioBridge.disagreements` entry is a visible note under the bridge's title, and (rev 2,
  D-5C.14) named in L1's status line, so the executive sees it before scrolling; carried figures say "(estimate)" and
  name the missing record.
- **Why.** P5 rule 2 ("a difference is shown, never hidden"); the Kisiwa disagreement lives only on this screen.

## D-5C.11 "What is not available yet" groups the missing records by kind, with the Sites

- **Ruling.** One row per record kind (fixed order), naming what it would fill and the Sites concerned, plus one line
  for what is not built (valuing changes; Protect).
- **Why.** The executive sees what to send, once per record, not once per factor and Site.

## D-5C.12 Caps that scale to 300 Sites

- **Ruling.** Drawer Site lists and by-Site tables show 10 Sites, then "Show all {n}"; the not-available list 8 rows;
  Actions 3.
- **Why.** UI standing brief: exposure that scales from 3 to 300 Sites without changing the page's shape.

## D-5C.13 The portfolio shows only the bridge's figure

- **Ruling.** Every portfolio figure on the screen is a row of `pb.rows` or `sb[c].roots`; the uncarried composition
  (`snapshot.actual()`) never appears. The gate is literal: World A's JSON never holds "$1,693.00" (the uncarried
  composition there, 2 of 3), and World D's tiles, headline, totals and outcome cards never hold "$883.00" (its
  uncarried composition, 1 of 3; the bridge reads $633.00, 2 of 3). "$883.00" stays Kobo's honest by-Site figure.
- **Why.** Rev 1's "never 883.00" guarded nothing in World A (handshake R1): 883.00 is A's Kobo row and A's uncarried
  figure is 1,693.00. A gate must name the number the wrong path would print.

## D-5C.14 The live page honours the hub shape, checked on the live page

- **Ruling.** The page has `data-level` regions L1, L2, L3 (`display: contents`); at most 6 blocks (a visible direct
  child of a level region, outside drawers): L1 the lead and the tiles, L2 one queue block, L3 three sections. The
  headline is at most 2 lines at 1440 and 1280; L1 sits above the fold at 1440 × 900 and 1280 × 720; the hub is at
  most 2,500 px tall at 1440 with everything closed. L1's lead holds the headline and one short status line: the "as
  of", the reconciliation in a few words, and each budget disagreement by Site. The full reconciliation sentence and
  the "not checked for later changes" line move into the Assure card's drawer; "What is not available yet" closes the
  "By outcome" section. `tools/deep_dive_gates.cjs` checks all of it on the built React page, with a plant per check.
- **Why.** IA-1b's overview budget binds every hub (handshake R4); rev 1 had 11 blocks and a 230-character sentence
  in L1, and the IA gate tools read only the mock. The executive meets L1 first: the month, whether it is reconciled,
  and that one Site's budget disagrees with itself belong there in a line; the detail belongs a click away.
  MOCK DEVIATION MD8 (D2) and MD9 (D1).

## D-5C.15 The headline names a heading only when it widens the gap, and says when it is more than the gap

- **Ruling.** Of Grow and Optimize, only a heading whose sum has the gap's sign is named; the larger of those
  (ties: Optimize). Its magnitude above the gap's reads "…, more than the whole gap". None: the headline states the
  gap alone. `tile2_rest` with the opposite sign to the gap reads as offsetting it.
- **Why.** "Cost and efficiency explain $300.00 of it" for a $100.00 gap, or a heading that narrows the gap named as
  its cause, misleads (handshake R6, R14). Honest numbers.

## D-5C.16 Every driver carries its evidence word; "necessary" litres are "not shown to be avoidable"

- **Ruling.** Each drawer driver has `word` = §2.4 of its row, passed through `money_word` (its value is a money
  effect). `necessary_l` is labelled "Diesel not shown to be avoidable".
- **Why.** Modelled litres must never read as recorded (D14); the owner's brief asks every number to carry its basis
  (handshake R3). The figure includes litres dispatch could not judge (D-4D.3, D-4D.11); "needed" claimed what was not
  tested (handshake R7).

## D-5C.17 "Actions in hand" lists agreed Actions only, newest first

- **Ruling.** The port returns 3C2's agreed Actions of the tenant, newest first by `(created_at, id)`; the panel shows
  three, then "more". The S6-01a Actions (verification plans opened from findings) are never read here.
- **Why.** The deep-dive's outcome is the change just agreed (RC9); oldest first would hide it behind older ones
  (handshake R10). Finding Actions are a different record, with no person who agreed them.

## D-5C.18 The bridge's own rules are outside the snapshot's freshness this fortnight

- **Ruling.** A change to `structure/attribution/` or `deep_dive/` alters served figures without "out of date"; the
  runbook rebuilds the month after every deploy (DDR §6). 3B7b adds both to the rules digest.
- **Why.** 5c must not edit 3B7a's digest roots (its seam), and every 5c edit would mark every snapshot stale during
  the build; a rebuild after deploy is the rehearsed path (handshake R16).

## Handshake answers (round 1)

Architect (Claude), 2026-11-20, on `task/4d-5c-DDR-handshake` 8ce960a64. Every answer is folded into `spec.md`
rev 2. Each gate named here has a plant in `reviewer-guide.md` rev 2 that fails it.

### Reviewer

- **R1 (High).** Accepted: D-5C.13. Test 6: World A's JSON holds no "$1,693.00"; World D's `tiles`, `headline`,
  `bridge.totals` and `outcomes` hold no "$883.00" (D's tile reads "$633.00"); the spies stay. Done question 1, the
  gate question and P1 are restated. Gate: P1 (tiles from `snap.actual()`) prints "$1,693.00" in A and "$883.00" in D's
  tile and fails tests 3, 4(D) and 6.
- **R2 (High).** Accepted. Test 9's clock: S1 recorded 2026-11-19T10:00Z; the snapshot built at **11:00Z** (its
  `as_of`); read at 11:30Z (A's standing); S2 recorded at **12:00Z**, after `as_of`; read at 12:30Z (still A's words);
  rebuilt at 13:00Z and read at 13:30Z (B's words). One settable clock injected as 3A7's `months.clock()` and the
  builder's. Gate: P3 (standing read live) shows B's words at 12:30Z and fails test 9.
- **R3 (High).** Accepted: D-5C.16. Drivers gain `word`; World H (A with 4d's KOBO-OCT litres for Kobo, V11 for the
  others) is written in §3.5 with every driver literal, `tile2_rest` "$252.00 …", and the untracked line. Gate: P13
  (driver word omitted) fails test 4(H).
- **R4 (High).** Accepted: D-5C.14. §5.2's markup has the regions; L1 holds the lead (headline, status line, fresh
  banner) and the tiles; the 3A7 sentence moves to the Assure drawer; Kisiwa's disagreement is named in L1's status
  line ("Kisiwa's budget total differs from its own lines.") and kept in full under the bridge title. Test 15 runs
  `tools/deep_dive_gates.cjs` on the built page. Gates: plants P14 to P21.
- **R5 (Medium).** Accepted: P7 is dropped. For one currency, `portfolio_bridge._row` sums exactly the Site rows, so
  the two paths cannot differ; the currency case is test 7's `CURRENCY_MISMATCH` sentence, and the spies (test 6)
  keep `month_view` on `pb.rows`.
- **R6 (Medium).** Accepted: D-5C.15. Test 4 gains vectors L1 to L4 (§3.5).
- **R7 (Medium).** Accepted: D-5C.16, "Diesel not shown to be avoidable"; 4d R8 answered by D-4D.15.
- **R8 (Medium).** Accepted: D-5C.4 amended. `month_view` takes one `standing`; §4.1 reads only the organisation's.
- **R9 (Medium).** Accepted: `disagreement_open` sentence for `computed` None (§2.5); test 4(A2) is A with Kisiwa's
  check `computed` None (a `TargetCheck` literal, view-level).
- **R10 (Medium).** Accepted: D-5C.17; the contract binding 3C2 says newest first (§4.3). Test 4(C4): four Actions
  give three rows, newest first, and `"more": 1`.
- **R11 (Medium).** Accepted. Test 14 states G3 in full: 1280 × 720, 1440 × 900 and 390 × 844, light and dark, six
  shots for World A; `measure_screen.cjs` on each; 0 page errors; page width equals the viewport; L1 above the fold;
  no text under 12 px; plus the fuel-cost drawer open at 390. G2 is part of test 15 (static lint over
  `deepDiveMonth.css`). G4 is the separate design reviewer, as the guide says.
- **R12 (Medium).** Accepted. Done question 6 ends at "with `NotConnectedActions` the panel reads 'Not available yet'
  naming the Action, and World C's row renders from an injected port"; the connected half (test 9(d)) is 3C2's
  (3C2 spec §5).
- **R13 (Low).** Accepted: "{pct1} of cost from figures received" (the share not taken at a budget line).
- **R14 (Low).** Accepted: D-5C.15 (`tile2_rest_offset`).
- **R15 (Low).** Accepted: test 1 reads "`STEPS` are `revenue` plus the non-neutral terms of `cost_to_serve`; with
  the neutral terms they are all of `cost_to_serve`'s terms".
- **R16 (Low).** Accepted as stated: D-5C.18.
- **R17 (Low).** Accepted: zero is the currency prefix and "0.00" with no sign ("$0.00", "KES 0.00"); test 2 adds it.

### Implementer pre-flight

- **P1 (Medium).** `PortfolioTabs` (today `EstatePortfolio.tsx:827-859`) moves verbatim to `PortfolioTabs.tsx`, with
  `counts` made optional (no badge when absent) and nothing else changed. The month page passes `current="month"`, no
  `counts`, and the Portfolio's own default `window` and `lens` (the values `EstatePortfolio` uses when the URL has
  none); `portfolioHref` gives tab `month` the plain `/portfolio/month` (no `?window=`). Test 13 compares the
  Overview's outerHTML with counts before and after.
- **P2 (Low).** Expected: the fourth key is `ASSURE_PERFORMANCE`.
- **P3 (Medium).** World A's reader is 3B7a's test reader, `CommercialLeafSource(months, store, fallback())`, with no
  `LitreLeafSource`: the litre leaves read NOT_CONNECTED with no note, so A's fuel text holds. World H adds
  `LitreLeafSource`. The DDR (built through `build_structure_read`) carries the note and the setup record.
- **P4 (Low).** `build_deep_dive_read(url)` builds 3B7a's snapshot read, 3A7's `(reconciliation, dispose)` and the
  actions port, and disposes all three; test 9 injects 3A7's months clock.
- **P5 (Low).** MD7's note says the live Portfolio's six tabs against vNEXT's three predate 5c; "The month" makes seven.
