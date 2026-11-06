# CH-6b2 handoff (PARTIAL: backend done, frontend code committed, frontend tests not yet rewritten)

- State: main (CH6b2-R) merged; backend `6b4e682f2`; **frontend code committed (see git log), tsc clean**.
- Frontend landed: `estateClient.ts` (`EstatePortfolioCard`, `cards`, `card_notes`, `headroom_unit`, `EstateCountBasis` NOT_KNOWN);
  `PortfolioOutcomes.tsx` card rules deleted, `content()` renders `summary.cards` (+ `card_notes` line, `oc-pfdays`, `PortfolioGrowParts`
  `dl.oc-pfgrow`), Optimize via `cardValue`; `OutcomeBoard.tsx` Grow ob-val = `grow_headline`, `GrowParts` in `ob-body`, Grow chip
  dropped, its `title` on the Potential part (the chip had no link_ref, only a title: note in packet); `EstatePortfolio.tsx` unit = `study.headroom_unit`.
- **RESUME HERE:** `npx vitest run src/estate/__tests__/estatePortfolio.test.tsx` has 24 failures, all tests of the deleted browser rules
  (OUT-A A6 protect/assure, OUT-C U5 protect text, WALK1-1 block, grow short value/missing claim, ch4 panel unit). Rewrite them to feed
  `summary.cards` / `body.summary.card_notes` / `study.headroom_unit` fixtures (`portfolioFixtures.ts`) and assert the server text renders;
  add: NOT_KNOWN basis vitest (Q8), Grow parts on card, board Grow parts in ob-body + no Grow chip (`outcomeBoard.test.tsx`), body without
  `nodes` renders none texts. `vitest related` fails to parse a .py import: run the test files directly. outcomeBoard + evidenceTrace pass.
- Backend landed:
  - `chain/claims.py`: `counted_threads`, `primary_category`, `disrupting`, `SITES_DISRUPTED` in `CLAIM_KEYS`, `EstateCounts.disrupted`.
  - `chain/vocabulary.py`: `count.sites_disrupted` + `COUNT_ZERO`; `node_text` "1 of 1 day checked" (Q7a); `CARD_TEXT`, `card_text`,
    `evidence_gap_text`, `checked_days_clause`, `count_card_value`, `sites_text`; `headroom_unit`; why `why.from.disrupted*`.
  - `site_outcomes/read.py`: `portfolio_cards` / `_grow_card` (summary `cards`), `estate_counts`; `chain_api.py` carries `cards` and the
    Protect why `comes_from` (`why.disrupted_lines`). `estate/portfolio.py` `card_notes` -> `summary.card_notes`.
  - `site_outcomes/board.py` `grow_headline` -> Grow row `grow_headline`. `chain/opportunities.py` `study.headroom_unit`.
  - L0 `backend/tests/test_ch6b2_portfolio_cards.py` (15 pass). Goldens ch5a1/ch5a2 regenerated (one-day wording, grow_headline, cards).
  - Pre-existing failures on main, not this slice: test_ch6_claims::test_templates_are_the_a4_table, test_out_b1_board
    ::test_board_imports_only_outcomes_and_stdlib, 5 x test_walk1_productive_sales (same 7 fail with the slice stashed).
- Card shape (`summary.cards` and `/estate/chain` `cards`): `{GROW_REVENUE|PROTECT_ASSET|ASSURE_PERFORMANCE: {value:{text,small}, missing,
  detail, basis_text, days_line, tone, claim, parts?:{target, potential, income, income_note}}}`; `summary.card_notes:{PROTECT_ASSET,
  ASSURE_PERFORMANCE}` on the Portfolio body.
- Original frontend plan (1-4 done):
  1. `F/estate/estateClient.ts`: types for `cards`, `card_notes`, `study.headroom_unit`; `EstateCountBasis` += `"NOT_KNOWN"` (Q8) + 1 vitest.
  2. `F/estate/PortfolioOutcomes.tsx` CategoryCards renders `summary.cards` + `body.summary.card_notes` (own line); delete protectValue,
     growShortValue, growEstimates, content() card rules, assureDetailText/verifiedText, checkedDaysClause/anyWithheld/evidenceGapText,
     GROW_ESTIMATE_BASIS; Grow `dl.oc-pfgrow` (Target/Potential/Estimated income + `dd.oc-pfnote`); `small.ob-days.oc-pfdays` (remove
     MD-CH5b-4 comment except Optimize); `missing` -> `<MissingClaim gapId="G-portfolio-grow-revenue">`. Optimize keeps `cardValue`.
  3. `F/sites/OutcomeBoard.tsx`: Grow ob-val = `row.grow_headline`; `GrowParts` into `ob-body`; drop the Grow Opportunity chip, its link
     onto the Potential part (Q6).
  4. `F/estate/EstatePortfolio.tsx`: delete `OPPORTUNITY_HEADROOM_UNIT`/`opportunityHeadroomUnit`, render `study.headroom_unit`.
  5. vitest related (estatePortfolio, outcomeBoard), tsc, CH-5b ratchet; non-vacuous proofs; polish clone L3 old->new; guards; packet.
