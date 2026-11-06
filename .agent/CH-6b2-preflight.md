# CH-6b2 pre-flight (Portfolio cards and the board Grow parts)

Branch `task/CH-6b2-portfolio-cards` from main `8133f5b95`. Builder: Claude (Opus). No code written yet.

## Facts (path:line, worktree `AssetOpsV1-ch6b2`)

- **Card rules to delete** (`frontend/src/estate/PortfolioOutcomes.tsx`): `protectValue` :120-136, `growShortValue` :147-153,
  `growEstimates` :156-164, `GROW_ESTIMATE_BASIS` :165, `content()` :167-245, `assureDetailText`/`verifiedText`
  :253-275, `protectDetailText` :70-75, `checkedDaysClause`/`anyWithheld`/`evidenceGapText` :87-117. `SiteDots`
  :287-309 reads `summary.sites[].rows[].state_label/tone` (`dotStateWord`, DOT_NO_OBJECTIVE kept, R7).
- **Card inputs today come from two bodies.** Grow + dots + Protect warning count + Assure verified/objective counts:
  the outcome summary (`site_outcomes/read.py:602-651`). Protect value, checked-days/withheld clause, evidence-gap
  clause, recovered value, Optimize money: the Portfolio body (`estate/portfolio.py:839-858`,
  `category_counts` :285-300 = Sites whose Finding's primary MOVES outcome is Protect).
- **Server parts already built (CH-6b1):** `portfolio_parts` `read.py:654-672` (rows{state,state_label,lead,nodes},
  earnings per Site) and `money_total` (`vocabulary.estate_income` :388-437, text + per-Site `lines`). Summary
  carries `sites[].earnings`, `sites[].rows[].nodes` and `money_total` (:635-651); `/estate/chain` the same (`chain_api.py:333-348`).
- **Node claims carry `days_line`** (`site_outcomes/board.py:303-336`), via `vocabulary.days_line` :325-342; the
  "1 day" replace at :336 applies only to a named one-day span.
- **Count claims** `chain/claims.py:93-117` (`count.open_threads`, `count.verified_results`, `count.opportunities`);
  texts `vocabulary.COUNT_TEXT` :81-88. No `count.sites_disrupted`. Thread wire carries `categories`
  (`chain/site_chain.py:82`); primary category = `outcome_roles(key, domain)` moves[0] (as `portfolio.py:295-298`).
- **Board Grow parts exist (CH-6a3 R2b):** `frontend/src/sites/OutcomeBoard.tsx:114-143` (`GrowParts`), but rendered
  **in the summary headline** (:196), while mock v70 `index.html:461-462` puts `growParts` in `ob-body` and keeps
  `ob-val` as the headline. The Grow `Opportunity` chip is :203-208 (`row.potential`).
- **CH-9 Q2 label:** `EstatePortfolio.tsx:394-403` `OPPORTUNITY_HEADROOM_UNIT` / `opportunityHeadroomUnit` (browser
  copy over `study.window_hours`); server helper `vocabulary.daylight_hours_text` :60.
- **P4:** the Portfolio priority/opportunity panel reads the Portfolio body (`EstatePortfolio.tsx:405+`,
  `portfolioOpportunity(body)`), not EstateChain rows. MD-CH4-1 stays open.
- **P5:** `G-portfolio-grow-revenue` is the only card gap (`frontend/src/ui/gapCatalogue.ts:42`, registry
  `v69-dependency-registry-pilot.json:422`); none on Protect. Retirement is BL-08 (SCOPE-1), so the entry is kept;
  the card's NOT_KNOWN Grow value keeps rendering through `<MissingClaim gapId=...>`.
- **P6:** `MA-1-mock-measurements.md:41-44,71-74` budget the four `oc-pfcard` blocks (1440: 283x413; 390: 176 wide);
  no separate `oc-pfgrow` / `ob-grow` rows. Layout evidence will measure card heights against those.
- **CH-5a2b L4:** `estateClient.ts:589` `EstateCountBasis = "COMPLETE" | "CHECKED_DAYS"` lacks `"NOT_KNOWN"`.
- **CH-6b1 review L5:** `EVENT_DATED` lead is dated whenever the event is shorter than the window, so a day card over a 65-min event reads "· 26 Oct 16:00-17:05".
- **Lane-2 overlap (DD-1a1):** `tools/demo_combined_finish.py:515-540` reads the summary Grow `headline_money`. CH-6b2
  keeps every existing summary field (additive only), so no edit there. No `host/*`, scenario or tools file planned.

## Questions (one batch; each has a default)

- **Q1. Seam: where the card claims are built and carried.** Default: one server function `portfolio_cards(...)` beside
  `portfolio_parts` (`read.py`), with texts in `vocabulary.py`, called by `_summary` and `/estate/chain`, so summary =
  EstateChain. It is carried as `cards: {GROW_REVENUE, PROTECT_ASSET, ASSURE_PERFORMANCE}`, each
  `{value: {text, small}, detail, basis, days_line, tone, parts?}`. Protect/Assure counts come from `estate_count_claims`
  through the summary service's chain reader and thread port (the call `/estate/chain` already makes). The clauses that exist only on
  the Portfolio body (evidence gaps, the checked-days/withheld clause) become one server string on the Portfolio body
  (`summary.card_notes: {PROTECT_ASSET, ASSURE_PERFORMANCE}`), rendered as its own line, never joined in the browser.
  Optimize stays on the Portfolio body (CH-5c).
- **Q2. `count.sites_disrupted`.** Default: in `chain/claims.py`, Sites with ≥1 counted thread (same restriction as
  `site_thread_states`) whose primary category is PROTECT_ASSET and state ∈ {OPEN, RECURRED, ACTION_IN_HAND}. The
  days are `sum_days`. The texts are the §B2 forms, with COMPLETE 0 = "No sites disrupted". This replaces the Findings-based
  `sites_with_primary_finding` on the card, so the value may change; it is listed old → new at L3. The withheld form "None shown yet"
  is dropped, because the basis rule covers it. Kept additive in `counts` on `/estate/chain` and the Portfolio `summary.claims`.
- **Q3. Optimize days line.** §B2 cites `rows.OPTIMIZE_COST.days_line`, but CH6a3-R2 H4 removed row-level days lines. The
  Optimize value is also the CH-5c money line, not a chain node, so a node line beside it would be untrue (ONE-SOURCE).
  Default: no days line on Optimize (MD-CH5b-4 kept for Optimize only), owner CH-5c.
- **Q4. Grow card value with `money_total`.** §B2 predates R10-replaced. Default: value = `money_total` amount
  ("{amount}" + small "estimated", prefixed "At least " on CHECKED_DAYS). If there is no total, it is the potential
  short text when a Site has one, else NOT_KNOWN through the kept gap. The Estimated-income part = `money_total.text`
  + its `lines` (`Site: …`), with the "not billed or collected" suffix once, not per line. The days line
  (`PFDAYS.grow`) = "{Site}: {earnings days_line}" per income Site, ` · `-joined on the server.
- **Q5. Portfolio Grow Target / Potential parts.** Default: Target = "{Site}: {kpi text}" for each Site whose Grow
  kpi has a record, else "No target set yet at any site" (MD-CH6-6). Potential = "{Site}: {first potential line}"
  for each Site with a potential claim, else "No potential found yet".
- **Q6. Board Grow row layout (§B3 vs mock).** Default: as the mock, `ob-val` = earnings text if its basis is not
  NOT_KNOWN, else potential, else target (server field `grow_headline` on the row), and `div.ob-grow` moves into
  `ob-body`. The Grow `Opportunity` chip is removed (Grow only; other rows keep `row.potential` if any).
- **Q7. Copy preferences handed to CH-6b2.** Default: (a) "1 of 1 days" → "1 of 1 day checked" whenever `m == 1`
  (in `days_line` and the money texts); (b) the dated lead (`EVENT_DATED`) is kept on day cards, since it is true;
  no change. (c) CH-9 Q2: the opportunity item carries a server `study.headroom_unit` text through
  `daylight_hours_text`, and the browser constant is deleted.
- **Q8. L4.** Default: add `"NOT_KNOWN"` to `EstateCountBasis`, plus one vitest that renders it.
