# 5c handshake

Reviewer questions and builder pre-flight, one combined round (`.ai/RULES.md` §4). Empty: no round yet.

## Reviewer questions

Fresh Claude reviewer, 2026-11-20, on `main` 93b9e23e1 (spec rev 1, `rulings.md`, `reviewer-guide.md`; owner RC1-RC9,
UI standing brief, k-of-n; 3B7a read on `task/3B7a-snapshot` c574de8a7; 3A7 by its spec). Severity: **High** blocks
coding; Medium needs a ruling; Low is the Architect's call. **(done)** = the answer changes what counts as done.

### High

- **R1 (done) §1, §6 test 6, §8 Q1, reviewer guide P1: the uncarried figure in World A is not 883.00.** 3B7a §5's
  `actual()` reads 883.00, 1 of 3, only because Mto has no records there (Mto `contribution` None). World A adds 5b's
  step, so Mto's actual contribution is 810.00 and `snap.actual()` composes to **1,693.00, 2 of 3** (Kisiwa's O&M not
  carried). "Never $883.00" therefore guards nothing: the plant renders "$1,693.00", and 883.00 is also Kobo's honest
  by-Site figure, so a page-wide check for it cannot be written. Test 3 still catches the plant by whole-JSON compare,
  but done question 1 and the gate question name the wrong number. Expected: test 6 asserts "$1,693.00" appears
  nowhere in World A's JSON or rendered page (and "$883.00" appears nowhere in D's tiles, headline and totals, where
  `actual()` is 883.00 and the honest figure 633.00); done question 1 and P1 updated.
- **R2 (done) §6 test 9, reviewer guide P3: the instants cannot catch a live standing.** World A's `as_of` is
  2026-11-20T08:00Z; S1 is recorded 2026-11-19T10:00Z and S2 2026-11-19T12:00Z, both *before* that `as_of`. A read at
  `known_at = as_of` and a live read (`known_at` None) then give the same standing, so P3 passes test 9. Expected:
  test 9 names the snapshot's `as_of` (e.g. build at 2026-11-19T11:00Z), records S2 at 12:00Z, reads (still A's
  words), rebuilds after 12:00Z (B's words); 3A7's `months.clock()` injected for `recorded_at` (3A7 §2.5).
- **R3 (done) §3.2 `drivers`: Modelled litres appear with no word.** A driver is `{label, value, sites, detail}`; once
  4d fills the litres, the fuel-cost drawer (whose step chip reads "Emulated"/"Recorded") lists "Diesel needed to
  serve the load · Actual 730 L · Target 700 L" with nothing saying it is Modelled. The UI brief asks every number to
  carry its basis, and RC/D14 forbid a modelled figure reading as recorded. No fixture exercises a split fuel cost, so
  nothing tests it. Expected: each driver carries `word` (§2.4 on its row: "Modelled"), a World H = A with 4d's
  KOBO-OCT litres for Kobo (fuel cost split −37.50, −412.50, −150.00; drivers "Modelled"; tile2_rest drops by 600.00),
  and a plant (driver word omitted) failing it.
- **R4 (done) §5.2, §5.3, §6 test 14: the hub-shape gates are not applied.** 5c says "the hub shape (IA-1b §3.1)", but
  (a) the markup sketch has no `data-level="L1|L2|L3"` regions or `[data-ia-drawers]` (IA-1 §3.1); (b) IA-1b's
  overview budget is at most 6 blocks per hub and a headline of at most 2 lines at 1440 and 1280; 5c's L1 alone holds
  headline, standing, as-of, fresh banner, untracked line and tiles, plus 2 L2 panels and 4 L3 sections (11-12 blocks),
  and the reconciliation sentence (~230 characters) sits in L1; (c) the IA gate tools (`ia_gates.cjs`,
  `ux_interaction_check.cjs`, `ia_shots.cjs` headline rule) run on vNEXT only, so none can run on the React page.
  Expected: a ruling naming which hub gates bind 5c and how they are checked on the live page (a block count and
  headline-lines check in the capture script, with a plant), the standing moved out of L1 or into the tile's word, and
  `data-level` regions in the markup.

### Medium

- **R5 Reviewer guide P7 cannot fail.** `portfolio_bridge._row` includes every Site whose row has an effect and sums
  them (`structure/attribution/portfolio.py:91-133`), so "summed from Site rows" equals the portfolio row unless the
  currencies differ. In D, Mto has no revenue row at all, so both give −17.00; −97.00 is unreachable. Expected: replace
  P7 with a currency-mismatch case (portfolio effect None, step "Not available yet") or drop it.
- **R6 (done) §2.5 headline and bridge_title: "explain {abs big} of it" can mislead.** `big` is the larger heading by
  magnitude whatever its sign. Gap −100 with Grow +200 and Optimize −300 reads "cost and efficiency explain $300.00 of
  it" for a $100.00 gap; Grow −120 with Optimize +20 reads "Grow revenue explains $120.00 of it", more than the gap.
  Expected: name only a heading with the gap's sign, and say "more than all of it"
  when its magnitude exceeds the gap; a vector each.
- **R7 (done) §2.2 `necessary_l` label overclaims.** "Diesel needed to serve the load" includes litres dispatch could
  not judge (D-4D.3); the claim was only that they are not shown avoidable. Expected: "Diesel not shown to be
  avoidable" (or the label kept with "of which {x} L could not be judged", which needs 4d R8).
- **R8 D-5C.4 "each Site's [standing] for its own": no Site figure carries a word.** `by_site`, drawer `sites` and the
  cash table hold no word, so `standings(site_id)` is read (and memoised, §4.1) but never used. Expected: either Site
  rows get words from their own standing, or §4.1 reads only the organisation's and D-5C.4 says so.
- **R9 §2.5 `disagreement` when `TargetCheck.computed` is None** (`structure/targets/read.py:41-46`: `computed` may be
  None with `agrees` False). The sentence would print "add to None". Expected: a sentence for it.
- **R10 (done) §3.1 `actions`: oldest first, at most 3, hides the change just agreed.** The deep-dive's outcome (RC9)
  is the newest Action; with three older Actions it falls behind "more". Also, which Actions count: the product already
  has Actions (`backend/assetops_backend/actions/`, verification plans from findings); "every Action of the tenant
  created by a person" may include those. Expected: newest first (or agreed-in-the-deep-dive first) and a definition
  binding 3C2.
- **R11 (done) §6 test 14 vs uiux-guide G3.** G3 needs 1280, 1440 and 390 in light and dark (six shots per screen,
  per operator), `measure_screen.cjs` metrics, 0 page errors, L1 above the fold; test 14 lists three widths, no dark.
  Expected: test 14 states G3 in full.
- **R12 (done) §6 test 9(c), done question 6: half of done belongs to 3C2.** "Shown as an Action once 3C2 is connected"
  cannot be answered at 5c's review (3C2 has no spec; see DDR R1). Expected: done question 6 ends at "reads Not
  available yet naming the Action, and renders World C's row from an injected port"; the connected half moves to 3C2.

### Low

- **R13 §2.5 tile1_cost "{pct1} of cost rests on records"** on emulated data: D14 keeps emulated figures from reading as
  records. Consider "rests on received figures", or the word beside it.
- **R14 §2.5 `tile2_rest` and the headline use `abs`:** a remainder whose sign opposes the gap reads as part of it.
- **R15 §6 test 1 `STEPS`:** `cost_to_serve` is a term of `contribution` but neither a step nor neutral; word the test
  as "the terms of `cost_to_serve` plus `revenue`".
- **R16 Freshness of the bridge itself.** 5c recomputes `site_bridge` at read time; 3B7a's `rules_digest` closure
  starts at `structure_snapshot.composition` (branch `code_digest.py` `RULE_ROOTS`) and does not reach
  `structure/attribution/` or `deep_dive/`, so a 5b or 5c rule change alters served figures without "out of date".
  State it as accepted, or add the two to the closure.
- **R17 §2.1 `money` zero:** "$0.00" is USD only; a zero in KES should read "KES 0.00".

## Implementer pre-flight

Pre-flight of spec §0 to §6 against `main` 93b9e23e1 (read-only), 3B7a on `task/3B7a-snapshot` (c574de8a7), 3A7
by its spec (not merged). Verified: 5b's `site_bridge`, `portfolio_bridge(sites, asked, sites_excluded,
portfolio_lines, month, key, version)`, `PortfolioRow` (`k`, `n`, `out`, `carried`, `evidence`, `origins`),
`PortfolioBridge.disagreements` as `(code, TargetCheck)`, `lowest`, `BRIDGE_ROOTS["MINI_GRID"] == ("contribution",
"collected")`, `CARRY_AT_TARGET`; 3B7a's `Served`, `PortfolioMonthSnapshot` (`asked`, `sites_excluded`, `sites`,
`portfolio_lines`), `SiteMonthSnapshot.inputs/targets`, `Freshness` fields, `SnapshotRead.portfolio`, D-3B7A.15 on the
branch; 3A7's `MoneyStanding.reconciled/reason/text`, `money_word(base, standing)`, `standing(…, *, known_at)`;
`app.state.site_registry.tenant()` (`sites/cutover.py:71`), `imported_sites()` → `StoredSite.name`;
`person_from_request` (`accounts/principal.py:18`); `commercial_upload_settings(url).real_data`;
`message("person.person_required")`; `fetchRetrying` (`sites/temporarilyUnavailable.ts:29`); the `/portfolio/:tab?`
route (`App.tsx:540`). World A's arithmetic checks (1,443.00, 2,295.00, −852.00; 91.5 %; 63 %; shares 11 % and 89 %;
cash rows; D's 633.00, 1,380.00, 46 %, 89.8 %). World A's 3A7 sentence matches 3A7's template and rounding.

- **P1 (Medium) §0, §5.1: `PortfolioTabs` already exists** as a function in `estate/EstatePortfolio.tsx:827-859` with a
  required `counts` prop (badges) and `useCurrentTabInView`; §5.1's `<PortfolioTabs current window lens />` drops
  `counts`, and the month page has no `window` or `lens` of its own (its state is `?month=`), while `portfolioHref`
  would give the month tab a `?window=` address. Expected: the moved component keeps `counts` optional (month page
  passes none), and the spec says which `window`/`lens` the month page passes and that the month tab's link ignores
  them. Test 13's outerHTML check is then meaningful.
- **P2 (Low) §2.2 `HEADINGS`:** `CATEGORIES` is `("GROW_REVENUE", "OPTIMIZE_COST", "PROTECT_ASSET",
  "ASSURE_PERFORMANCE")` (`outcomes/catalogue.py:9`), so the fourth key is renamed as §2.2 allows; noted so the
  reviewer expects it.
- **P3 (Medium) World A and 4d's merge order.** 5c is built on day 8, the day 4d merges. The fuel stop text in §3.5
  holds only if World A's reader stays 3B7a's test reader (`CommercialLeafSource(months, store, fallback())`): with 4d
  merged its litre leaves read NOT_CONNECTED with no note (still EMS, fuel curve, dips, deliveries). Built through
  `build_structure_read` instead, they would carry `GENERATOR_OR_TANK_NOT_DECLARED` and add "the Site's generator and
  fuel tank" (as DDR §3.4 expects). Expected: the spec states World A's reader.
- **P4 (Low) 3A7 not merged:** `build_commercial_reconciliation` returns `(reconciliation, dispose)`; test 9 needs
  3A7's months clock injected for `recorded_at` (3A7 §2.5: `months.clock()`); the 5c composition disposes it with
  3B7a's service.
- **P5 (Low) §5.1 tab order:** the live Portfolio has six tabs (`portfolioWords.ts:29-36`), the vNEXT hub three; "The
  month" second makes seven. The six-versus-three difference is older than 5c; MD7 should mention it so the review
  does not count it as a new departure.
