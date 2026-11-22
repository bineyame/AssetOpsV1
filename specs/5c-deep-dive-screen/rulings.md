# 5c rulings

Architect (Claude), 2026-11-20; rev 2 the same day (D-5C.13 to D-5C.18, D-5C.4 amended, handshake answers below);
rev 3 on 2026-11-21 (D-5C.19 to D-5C.25, review round 1 answers); rev 4 the same day (D-5C.26 to D-5C.28,
unit 3 review round 1 answers, at the end); rev 5 the same day (D-5C.29, the cash sentence; indexed in `index-rulings-23.md`).
Each ruling is indexed in `.ai/decisions/index-rulings-13.md` (D-5C.19 on: `index-rulings-22.md`).

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

## Amendment (SC-1, 2026-11-21): words as statements (D-SC1.14)

If `SC-1a` (`specs/SC-1-statement-composer/spec.md`) has merged when unit 1 starts, §2.5 is written as structured
statements in `i18n/statements/en/deep_dive.py` (the headline exactly as SC-1 §5.2; every other row by the same rules:
`{below|above}` and similar as picks, "appended when k < n" and optional fragments as parts, one / two or three / more
Sites as variants, `{a|an}` as the factor vocabulary's declared article); §2.1's formats are SC-1's formats (identical
by D-SC1.10); §2.2 to §2.4 are read from SC-1's shared vocabulary; `deep_dive/words.py` keeps only the functions that
build facts (which heading is named, `needs` keys), and it and `deep_dive/view.py` join the guard's `ADOPTED`; every
variant gets a case. Otherwise §2 ships as written, its keys join the legacy baseline, and SC-1b converts them.

**Amended (SC-1 handshake, 2026-11-21; D-SC1.26 replaces the "otherwise" above).** Unit 1 starts when SC-1a has
merged (its other gates stand); the coordinator checks at dispatch and says so in the brief. There is no flat
fallback. The headline is SC-1 §5.2 rev 2: a `served` statement whose `requires` checks the named heading's sign
(D-SC1.20); the payload's `headline` becomes `{"text", "evidence"}` and the screen shows `evidence` beside it as the
tiles show `word` (D-SC1.18). If the governing mock shows no evidence word beside the headline, that is a **MOCK
DEVIATION** (category: honesty rule, every figure carries its evidence class). The share column and the disagreement
notice are SC-1 §5.4's shapes; prices use SC-1's `price` format. Every template or vocabulary word holding a number
word is reworded to drop it (D-SC1.21): `SITE_SETUP` reads "a generator and a fuel tank declared in the Site's setup
(litres are worked out for each)". This unit's expected strings change by these rules only; the packet lists each.

**Amended (owner away, 2026-11-21; D-SC1.28 replaces D-SC1.26's start rule above).** Code starts on its gates (3B7a and 3A7 merged; 3A7 now merges only after SC-1a, so unit 1 still starts after SC-1a); only the
text waits: no 5c code writes served text outside SC-1 statements (D-SC1.28). The unit merges only after SC-1a.

**Amended (4a spec, 2026-11-21; D-4A.12).** `RECORDS`, `RECORD_KEYS` and `NOTE_KEYS` of spec §2.3 change as D-4A.12
states (`specs/4a-energy-to-cash/rulings.md`): `METER_READS` and `LOSS_BAND` added after `METER_REGISTER`,
`TARIFF_SHEET` removed, the energy leaves' keys and 4a's notes mapped. If 5c has not merged when 4a starts, the 5c
builder takes it; if it has, 4a's last commit does. Words as SC-1 statements (D-SC1.28). 4a's handshake adds:
`adjustments_kwh` (BILLING) and `BILLING_ADJUSTMENTS` removed from `RECORDS` (D-4A.20); `NOTE_KEYS` gains
`METER_REF_CONFLICT` (METER_READS, METER_REGISTER) (D-4A.24).

## Review round 1 answers (units 1-2; 2026-11-21)

Architect (Claude), standing in for the owner (`owner/owner-away-architect-stands-in-2026-11-21b.md`), on the review at
`task/5c-deep-dive-screen` 519c8a305 (`review.md`, round 1). Folded into `spec.md` rev 3. Owner-level calls are
OWNER-AWAY rows 59 to 62 (`specs/OWNER-AWAY/decisions-2026-11-21.md`). H1, M1 and L1 are in the running fix round as
the review states; L1's words are D-5C.23's. L4 and L6 need no action.

## D-5C.19 (H2) Spec §2.4 governs this screen's evidence words, after SC-1f too

- **Ruling (the coordinator's, recorded here).** On the deep-dive every figure's word follows §2.4's order:
  NOT_AVAILABLE, ESTIMATED, MODELLED first; otherwise the weakest origin when it is not observed (`source-emulated`
  "Emulated", `demo-simulated` "Simulated", `unknown` or none "Estimated"); otherwise by evidence, with `DECLARED`
  read as "Recorded". So an emulated figure reads "Emulated" after SC-1f. `word()` applies this order before it
  calls the shared vocabulary (the review's H2 fix): for an observed origin it hands `DECLARED` over as `RECORDED`.
  §2.4's table gains the rows `DECLARED` with `source-emulated` "Emulated" and with `demo-simulated` "Simulated".
  Text another unit renders and 5c passes through unchanged (3A7's `standing.text` and `details`, where SC-1f's
  "(Declared)" words the tolerance itself) keeps that unit's words.
- **Why.** D-SC1F.1 words a declared *setting* shown as such (a tolerance). A step's figure is an actual set against
  a declared target; its weakest part is its origin, and D14 says an emulated figure is never shown as if it were
  real. "Declared" on revenue −$97.00 would hide that the records are emulated.
- **Reverse.** Drop the mapping in `word()`: the step words become "Declared, not yet reconciled" (the scratch
  merge's output); §3.5's literals follow.

## D-5C.20 (M2) One figure, one evidence statement: the headline's words carry the standing

- **Ruling.** PF8 is confirmed: `headline` is `{"text", "evidence"}` and the screen shows `evidence` beside it as
  the tiles show `word` (MD10). Every evidence word 5c serves for a money figure goes through the one 5c function
  that words the tiles (`word()` then `money_word(word, standing)`), the headline's `evidence` included: World A
  `["Estimated, not yet reconciled"]`, World B `["Estimated"]`, `headline_na` `[]`. The headline's facts carry the
  same evidence the payload's own figures carry: the gap R's, the named heading's the weakest of its steps'.
  Test 3 (class form): for A, B, D and vectors L1 to L4, `set(headline.evidence)` equals the set of `tiles[1].word`
  and, when a heading is named, that outcome card's `word`. A plant serving `served()`'s words unmapped fails it.
- **Why.** The owner's rule: one figure carries one evidence statement wherever it appears. The status line states
  the standing for the page, but the tile beside the headline words the same −$852.00 with it, so the headline's
  chip without it is a second statement of one figure.
- **Class beyond 5c (queue Q10).** SC-1 words a figure's evidence on three paths: `with` (honours `money` and
  `Evidence.reconciled`), inline and `served` (both ignore `reconciled`). No producer sets `reconciled` on an inline
  or served figure today (only `reconciliation.py`'s `with` slot), so nothing reads wrong now; Q10 makes
  `figure_word` the one path in SC-1's next unit.
- **Reverse.** Serve `served()`'s words unmapped and record in §3.5 that the status line states the headline's
  standing.

## D-5C.21 (L2) Drivers are nested: each driver holds its own parts

- **Ruling.** A step drawer's `drivers` lists the step's direct parts only. Each driver is `{"key", "label",
  "value", "sites", "detail", "word", "children"}`; `children` has the same shape, recursively, and is `[]` for a
  leaf. A driver's parent is its nearest registry ancestor that is the step or has a driver row; `residual:<x>` is
  the last child of `x` (of the step when `x` is the step). Order within a level is `pb.rows` order. World H's fuel-cost drivers: Diesel used
  (children: Diesel not shown to be avoidable, Diesel run while solar and battery could carry the load, Unexplained
  fuel; each `children` []) and Diesel price (`children` []). Screen: one `<ul>` per level, a driver's children in a
  nested `<ul>` inside its `<li>`, indented by one spacing token; no control (the drawer shows every level; World H
  has two). The page adds nothing (D-5C.2).
- **Why.** Siblings at one level add to their parent's effect (5b's attribution, D-5B.12). A flat list puts −$600.00
  beside its three parts, which invites adding them to −$1,200.00. Nesting makes the grouping the sum's grouping;
  a `depth` field would leave the grouping to the page to rebuild.
- **Tests.** Test 4(H) asserts the nested literal (spec §3.5); a plant that flattens it fails. Unit 3: a frontend
  test renders H's fuel-cost drawer and finds the three part rows inside Diesel used's list item.
- **Reverse.** A flat list with `depth` and `parent` keys; the screen indents by `depth`.

## D-5C.22 (L3) The JSON holds every Site row; the screen applies the caps

- **Ruling.** Lists bounded by the Sites asked ship whole: drawer `sites`, `by_site.rows` and `not_available.rows`
  have no `more` key. The screen shows the first 10 (8 for not-available rows) and a button "Show all {n}", `n` the
  array's length, which shows the rest in place. `actions` keeps its server cap (3 rows and `more`): the Actions
  port is not bounded by the Sites and grows with time.
- **Why.** At most 300 Sites keeps each list small enough to send whole, and a server cap would need a second fetch
  for "Show all". Counting rows is not figure arithmetic, so D-5C.2 holds. §3.4 already said "the JSON holds all".
- **Tests.** Unit 3: A's fixture with `by_site.rows` and the revenue drawer's `sites` repeated in memory to 12 shows
  10 and "Show all 12", then 12 after the click; `not_available.rows` at 9 shows 8 and "Show all 9".
- **Reverse.** Cap at the server with `more`, and fetch the full list on "Show all".

## D-5C.23 (flag (a), L1) A carried step's cell names its source: "(at budget)"

- **Ruling.** The suffix on a carried Site's step value is " (at budget)", in the by-Site cell and in that step
  drawer's per-Site row (one form, `CELL_FORM[carried]`, L1). World A: Kisiwa's O&M cell and its O&M drawer row read
  "$0.00 (at budget)". The `carried` sentence, the not-available row's "(taken at its budget line meanwhile)" and the
  step's word ("Estimated, not yet reconciled") are unchanged. 5b's carry rule (`CARRY_AT_TARGET`) is unchanged.
- **Why.** The owner's rule: one figure per quantity, labelled by its source. $0.00 is one figure, the effect of an
  actual taken at its budget line by 5b's explicit rule, and a part of the $1,443.00 total and of Kisiwa's −$185.00
  row; "Not available yet" there would break the row's sum and contradict the total. "(estimate)" said how strong
  it is (the chip already does) but not where it came from.
- **Reverse.** Restore " (estimate)"; or carry nothing in 5b (then the total reads k = 2 for O&M), which changes
  5b's served totals and needs its own review.

## D-5C.24 (KD1) World H's diesel price: no detail, "Modelled"

- **Ruling.** §3.5 H's Diesel price driver is {"Diesel price", "$0.00", "1 of 3 Sites", detail null, "Modelled, not
  yet reconciled"}. A price composes NONE, so its portfolio row has no actual or target and §3.2's rule gives no
  detail; its effect is the Modelled litres times the price difference.
- **Why.** A price does not add across Sites; printing one Site's price as the portfolio's would be a second figure.
- **Reverse.** A Site-level price detail when k = 1 (a later refinement, not needed).

## D-5C.25 (L5) Record words name what is missing in a record already received, and hold no comma

- **Ruling (fix now, in 5c).** In the shared `record` vocabulary: `BILLING` reads "the billing export with each
  line's kWh and tariff"; `LOSS_BAND` reads "each feeder's expected technical loss as declared in the Site's setup".
  Class rule, with a statement case over every `record` entry: a record's words hold no comma outside brackets,
  because `needs` joins records with commas. World A's revenue stop becomes "Not split further until the billing
  export with each line's kWh and tariff, a feeder meter export, a meter register with change dates, the customer
  meter reads for the month, each feeder's expected technical loss as declared in the Site's setup, the
  productive-use tariff and budget lines for energy delivered, tariff and productive-use price."; its not-available
  rows' `needs` follow. 5c takes it because it carries D-4A.12's record change (PF2) and has not merged.
- **Why.** Revenue is read from the billing export; what is missing is the kWh and tariff on its lines, so asking
  for "the billing export" asks for a record already sent. The comma inside LOSS_BAND's words made the list
  unparseable. The revenue drawer is on the walkthrough's path, and the change is a vocabulary edit and literals
  (about 0.25 unit).
- **Reverse.** Restore the two entries; drop the case.

### Flag (c): 0K4e's sweep names test 4(H)

`specs/0K4e-candidate-energy/spec.md` §0 now names `backend/tests/test_5c_deep_dive_view.py::test_4_h_kobo_litres`.
Its litres (330 L, −$412.50, 730 L, −$37.50) come from 4d's KOBO-OCT test inputs. If those inputs are literals that
0K4e does not change, the test is left and the packet says so. If 0K4e moves them, the literals are updated by hand
(W2). Whichever of 5c and 0K4e merges second runs the test.

### Flag (b)

"Target 0 L" is kept as it is (5a's `LEAK_ZERO` rule, plan against actual, which the owner's rule allows).

## Unit 3 review round 1 answers (2026-11-21, rev 4)

Architect (Claude), standing in for the owner (`owner/owner-away-architect-stands-in-2026-11-21b.md`), on the review at
`task/5c-unit3-screen` bc2df265f (`review.md`, "Unit 3 round 1"). Folded into `spec.md` rev 4. Owner-level calls are
OWNER-AWAY rows 68 and 69. Scopes: §11 of `spec.md` (backend fix, off `main`; screen fix, on `task/5c-unit3-screen`
after the backend fix merges).

## D-5C.26 (item 6, L3) A figure slot with no figure states "Not available yet" once, as its value, with no word

- **Ruling.** A *figure slot* is a served object that prints one figure in `value` and its evidence in `word`: tiles
  `contribution` and `gap`, bridge steps, drawer drivers (every level), outcome cards `grow` and `optimize`, and `cash`
  (its figure is the collected root's actual, printed in `text`). The plan tiles and the Protect card are figure slots
  that never have a figure. Server: a slot's `word` is null **exactly when its figure is absent** (the figure's value
  or its currency is None); otherwise it is the §2.4 word through `money_word`. One view method,
  `figure_word(value, currency, ev, origins)`, builds every slot's word and the headline's `evidence` (D-5C.20), and
  returns None for an absent figure. This **revises L9's fix**: a card over mixed currencies serves `word` null, not
  "Not available yet". `W.word` takes `currency: str`; `NO_CURRENCY` ("XXX") is deleted (no caller reaches it).
  The Assure card is not a figure slot: its `value` is the standing's statement and it opens a drawer; its `word`
  stays null and it is never muted. Page: a figure slot's value is muted (one modifier class, `dd-na`) when its
  `word` is null; for an outcome card, when `word` is null and `drawer` is null. No key or text test (`startsWith`
  goes; L3 closed).
- **Why.** The owner's rule: one figure, one statement. "Not available yet" twice (as the value and as its chip) is
  one fact stated twice, and a chip is an evidence class, which an absent figure does not have. The headline already
  follows this (D-5C.20: `evidence` [] when it states no figure); the plan tiles did too. A word built only when the
  figure is present makes the null the server's statement, so the page reads the shape (D-5C.2), and it retires the
  "XXX" carrier L9 left.
- **Tests.** Class case over A, B, D, G, H, World X and every 4 i currency world: in every figure slot `word is None`
  if and only if the slot's figure is absent (`value` "Not available yet"; cash: its root's actual is None); no
  served `word` anywhere equals "Not available yet". Plants that fail it: L9's card word restored; World X's
  contribution tile served `word` "Not available yet". Test 3's class form compares the non-null words. Unit 3: World
  X renders no word chip reading "Not available yet"; its contribution and gap tiles, revenue step, Optimize card are
  muted; the Assure card is not.
- **Reverse.** Serve "Not available yet" as the word again (L9); the page mutes by the same shape rule.

## D-5C.27 (item 7, MD11, MBQ5) The bridge draws each step as a bar on the gap's scale, positioned by the server

- **Ruling.** As the mock (`uxBridge`, `.ux-wf-bar` on the gap's scale, `.ux-wf-scale` marks): each step gains
  `bar`, null or `{"left", "width", "tone"}`; `bridge` gains `scale`, null or `{"target_at", "actual_at"}`. Every
  position is a percentage of the step track, a plain decimal string with two places, computed by one pure function
  `bridge_bars(effects, gap)` in `view.py` (spec §3.2). `tone` is "lowers" (effect below 0) or "raises". A step's
  `bar` is null when its row is absent, its effect is None or 0, or its row's currency is not R's; every `bar` and
  `scale` are null when R's effect is None or 0. The page sets `left` and `width` from the strings
  (`` `${bar.left}%` ``) and maps `tone` to a class: no arithmetic, so **D-5C.2 stands as written** (the tile bar
  stays its one exception); the reviewer's one-line extension is not needed. The scale's marks are labelled with the
  served `totals` strings (`{target_label} {target}`, `{actual_label} {actual}`). Bars and marks are `aria-hidden`:
  the row's text states the value and share. MD11 is closed (R767 resolved).
- **Why.** The mock is the layout spec and this waterfall is the overview's one chart (guide §9) and the visual of
  walkthrough step 2; rows without bars drop it with no honesty or scale reason. Serving positions keeps one place for
  Decimal arithmetic. About 0.25 unit across the view and the page, inside the walkthrough's window.
- **Tests.** Pure vectors (spec §3.5 "Bars") and World A's literal; H equals A; World X all null. Unit 3: A's revenue
  bar at left 0.00 % width 11.38 %, fuel cost at 11.38 % and 88.62 %, O&M and staff with an empty track; X has no bar
  and no scale.
- **Reverse.** Drop `bar` and `scale`; MD11 open again (rows without bars).

## D-5C.28 (M1) No gap, no share: a step's share is null when R's effect is None or 0

- **Ruling (confirmed; fix on `main`).** `shares()` returns no share when `R.effect` is None or 0, so every step's
  `share` is null and the page omits it; `gap = self.R.effect or Decimal(0)` goes. With a non-zero gap the rule is
  §3.2's, unchanged (A: 11 %, 89 %, "No effect" twice).
- **Why.** A share is a part of the gap; with no gap known, "Offsets it" states a direction against a figure that is
  not there (World X: a KES 600 overspend read as offsetting). Zero is the same class: nothing widens a gap of 0.
- **Tests.** 4 i on World X: every step `share` null and "Offsets it" nowhere in the payload; a vector with R's
  effect 0 and steps +5.00 and −5.00: both shares null. A plant restoring `or Decimal(0)` fails both.
- **Reverse.** None sensible; a "not compared" share word would be a second statement of the absent gap.

## D-5C.29 (DDR review, cash) The cash sentence states October's bills and the three parts they split into

Rev 5, 2026-11-21, Architect standing in for the owner (owner-away row 70). Fix scope: `spec.md` §12.

- **Finding.** World A read "In October, $8,870.00 was collected against $9,785.00 expected; $668.00 is still
  outstanding and $150.00 is paid but in transit." A reader adds 8,870 + 668 + 150 = 9,688 and finds 97 short of
  9,785. The figures are each correct; the sentence pairs them on two bases.
- **Where each figure comes from** (5b's cash tree, `rows_mini_grid.py:112`: `collected = revenue - in_transit -
  outstanding`; `targets/rules.py` LEAK_ZERO sets the targets of `in_transit` and `outstanding` to 0).
  `$8,870.00` is `pb.rows["collected"]["collected"].actual`, the bills less what is in transit and outstanding
  (Kobo 3,180, Kisiwa 3,800, Mto 1,890). `$668.00` is `pb.rows["collected"]["outstanding"].actual`, the RECEIPT
  leaf (278 + 270 + 120). `$150.00` is `pb.rows["collected"]["in_transit"].actual`, the SETTLEMENT leaf (Mto's
  150). `$9,785.00` ("expected") is `pb.rows["collected"]["collected"].target`, which by LEAK_ZERO is the revenue
  *target*. It is not the billed figure: `pb.rows["collected"]["revenue"].actual` is $9,688.00. The 97 between
  them is Grow's revenue step, already in the contribution gap. The identity that holds is billed = collected + in
  transit + outstanding (9,688 = 8,870 + 150 + 668), per Site and in total. That is the mock's own form:
  `loop-core.js:151` "Collected … + in transit … + outstanding … = billed …; cash does not change contribution",
  and `walkthroughs.md` §2 "Kobo collected 3,180.00 of 3,458.00 billed, with 278.00 outstanding".
- **Same class, second instance.** The table's Billed cells read the *contribution* tree's revenue
  (`self.rows["revenue"]`, `_find(roots["root"], "revenue")`), not the cash tree's. Where the two trees cover
  different Sites, the total does not add. In the one-currency subset world (4 i) the total reads "Not available
  yet" for Billed beside KES 6,980.00 collected, KES 0.00 in transit and KES 548.00 outstanding for the same 2
  Sites, whose bills are KES 7,528.00.
- **Ruling.**
  1. The sentence states the bills, then the three parts they split into, in the table's column order, so the
     sum a reader does holds. Exact text (variant `cash`):
     "Of {billed} billed for {month}, {collected} has been collected, {in_transit} is paid but in transit and
     {outstanding} is still outstanding."
     World A: "Of $9,688.00 billed for October, $8,870.00 has been collected, $150.00 is paid but in transit and
     $668.00 is still outstanding."
  2. "Expected" (the revenue target) leaves the cash sentence. One figure per quantity: the revenue target is
     already stated, with its basis, in the Revenue step's drawer ("Target $9,785.00"); the section is "outside
     the contribution gap", and collection against target is not a quantity this screen defines. `billed` is
     the same quantity as the Revenue drawer's "Actual $9,688.00" and prints the same figure.
  3. Every figure in the section comes from the cash tree (`pb.rows["collected"]`, and per Site
     `sb[c].roots["collected"]`). Billed is the cash tree's `revenue` row, in the sentence, the total and each
     Site's row.
  4. The parts are stated together or not at all. A pure function `cash_parts(rows)` returns the `revenue`,
     `in_transit` and `outstanding` rows only when all of these hold:
     - the collected root's actual and currency are present;
     - each part row exists, with its actual present and its currency equal to the root's;
     - each part covers the root's Sites (its `out` codes equal the root's `out` codes);
     - `collected.actual == revenue.actual - in_transit.actual - outstanding.actual` (Decimal, exact).

     Otherwise it returns None, and then:
     - the sentence reads variant `collected_only`: "{collected} has been collected on the bills for {month}; the
       amounts billed, in transit and still outstanding are not available for the same Sites yet.";
     - the total row's Billed, In transit and Outstanding cells read "Not available yet".

     Variant `not_available` ("Cash collected in {month} is not available yet.") is unchanged. No sentence and
     no total row ever pairs figures that do not add up.
- **Why.** Honest numbers and one figure per quantity (owner). Each figure names its basis ("billed for October",
  "collected", "paid but in transit", "still outstanding"), and the reader's own arithmetic holds. The fix
  restores the mock's form (it is not a MOCK DEVIATION). The 5c text was the departure: it carried the cash root's
  target into a sentence whose other figures sit on the bills' side. The identity check makes the class hold by
  construction, not by fixture. The real bridge drops a Site's whole cash tree when its collected is not compared
  (worlds D, G and the subset world all match), so the `collected_only` variant is a defence that only a plant
  reaches. It reads honestly where a page error would not.
- **Reverse.** Restoring "expected" is a second, target-side quantity. It could only come back as its own
  statement ("against a revenue target of …"), never as the base the parts are subtracted from.
