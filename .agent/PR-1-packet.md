# PR-1 review packet: `price_action` on unpriced items (2026-11-11)

- **Card:** "PR-1 + price-page draft", `.agent/architect-sequence-client-scope-2026-11-11.md` rev 4 (line 49).
- **Spec:** `.agent/architect-answer-price-it-2026-11-10.md` §3, §4.1, §5, §7 (BL-68). Owner item 10, `.agent/owner-price-it-and-speed-priority-2026-11-11.md`.
- **Branch:** `task/PR-1-price-action` from main `9fc353736`. Worktree `AssetOpsV1-pr1`. Main has since moved to `777e245e5` with docs/tools only; none of this slice's files are touched.
- **Commits:**
  - `d57ecc02e`: draft and notes;
  - `2175f62cd`: server;
  - `6c69d66e9`: frontend;
  - the packet commit.
- **USER_REVIEW_REQUIRED:** yes, for the draft (`frontend/mockups/v71/price-it.html`, `.agent/PR-draft-notes.md`). The code merges on review ACCEPT.

## Delivered

**Server.** Every unpriced item carries `price_action`, in one of two shapes; the words are the server's:
- `SET_PRICE {key, label, href, link_ref}`;
- `NEEDS_MODEL {need_key, text, label, href, link_ref}`.

Where it appears:
- early warnings (`Warning.wire`);
- UNPRICED estate money lines (`estate/financials._line`) and the Portfolio OPERATING_COST UNPRICED card;
- a mini Finding's UNPRICED fuel cost (`finding_api` `/financials` bridge `consequence`);
- the mill verification value (`mill_value`).

**Links.** The new Ref kind `PRICES {site, key?|need?}` goes to `/sites/{site}/financials/prices?key=|need=`, through `chain/refs.href_for` and `routeFor`, and is pinned by the shared fixture `route-refs.json`.

**Words and classification.** These live in a new module, `outcomes/price_action.py`. It is pure and builds links from the injected `chain.refs`, so `outcomes` imports nothing outside itself.

**Frontend.**
- `PriceActionLink` (`sites/PriceAction.tsx`) renders the server label from `linkFor(link_ref)`. It adds the shared range (`from`, `to`, `known_at`) and `return`, which is the current address.
- It appears under early warnings, estate money rows, the Finding "Cost exposure: Not available" tile and the mill value.
- The new route `/sites/:siteId/financials/prices` (`shell/SitePricesFrame.tsx`) is the honest target until PR-2a. It shows the existing "Not available yet" primitive, the sign-in line ("Prices are set by your AssetOps administrator until sign-in is available. Saving a price from this page comes with sign-in.") and "← Back to where you were". Only a same-app `return` is accepted.
- No form and no write path. `HUMAN_PRINCIPAL_REQUIRED` and `financial_api.py` are unchanged.

## Acceptance (card)

| Card item | Status |
|---|---|
| v7.1 price-page draft (read-only view, history, administrator sentence) | Done: `frontend/mockups/v71/price-it.html`, with notes |
| server `price_action`, two shapes, on every unpriced item | Done on warnings, money lines, Portfolio card, mini Finding fuel cost and mill value. Partial: see deviation 2 |
| words server-side | Done. The frontend renders `label` only and never classifies |
| frontend link with `return` | Done, and the shared range is kept |
| target shows an honest "not available yet" until PR-2a | Done |
| no write path; `HUMAN_PRINCIPAL_REQUIRED` unchanged | Done; `financial_api.py` is untouched |

## Checks run (revision `6c69d66e9`)

**Backend, no database.** `tests/test_pr1_price_action.py` (new, 11) plus 77 adjacent files: 1436 passed, 15 failed, 21 skipped.
- 14 of the failures are `test_k8_estate_fuel.py`, with `AttributeError ... 'known_at'` in `estate/coverage.py:68`.
  - They are order-dependent: the file passes alone (21 passed), and on plan2 main.
  - My diff does not touch `coverage.py`. I did not run the same batch on main, so "existing before this slice" is likely but not proven.
- The other failure was `test_out_c2_board` (a pinned key set). I updated it and it passes now.
- Pins updated on purpose (one key added, `price_action`):
  - `test_out_c_rules.py::test_wire_keys`;
  - `test_out_c2_board.py::test_board_and_summary_wire`, which now also asserts the href and label.
- `fixtures/k6b_mill_pins.json`: `price_action` is added to `summary_after.value` by hand. The Site code `MG-W402-001` is inferred from `test_w402_reads_postgres.CODE`, so the Postgres run must confirm it.

**Frontend.**
- `npx tsc --noEmit -p .`: exit 0.
- vitest: `priceAction.test.tsx` (new, 8), `routeRefs`, `earlyWarnings`, and 10 adjacent files (estate financials and portfolio, siteFinding\*, millVerification, linkRefOnly): 13 files, 422 tests passed.

**Guards.**
- `frontend-hardwiring.mjs`: pass, no cell raised.
- `missing-claim-scan.mjs`: pass.
- `mock-deviation-labels.mjs`: pass.
- `tools/check-architecture.ps1`: "Architecture check passed.", exit 0. It needs `ASSETOPS_GUARD_PYTHON=<plan2 .venv python>` because the worktree has no `.venv`; without it, rule 8 refuses to run.

**Not run:** full suites, production build, layout evidence. Tonight's rules exclude them, so layout is **unverified**: the link sits under a table cell or metric card at narrow widths.

## Postgres files still to run (Thu from 12:30, own `*_test` DB)

These touch changed bodies or the changed SELECT:
- `test_k6b_fuel_verification_postgres.py`: the hand-edited pin;
- `test_ch9b3_mill_verdict_postgres.py`, `test_wd1m_mill_source_postgres.py`, `test_ch9b2_midday_plan_postgres.py`: `domain_plan_context` now selects `s.site_code`;
- `test_out_c3_repeat_visits_postgres.py`, `test_fx_cold_linked_postgres.py`: the warnings wire;
- `test_w302_money_comparability_postgres.py`, `test_w302_financials_links_postgres.py`, `test_w303_portfolio_comparison_postgres.py`, `test_w303_portfolio_fixture_postgres.py`, `test_w303_portfolio_scope_snapshot_postgres.py`, `test_cov_partial_postgres.py`: money lines and cards;
- `test_lr01_money_eligibility_postgres.py`, `test_s4_finding_read_postgres.py`: the bridge `consequence`.

## Known deviations

1. **Address.** The card says `/sites/:id/prices`. I followed the spec, §4.1 `/sites/:code/financials/prices`, under the Financials tab. One constant on each side (`refs.PRICES_SUFFIX`, `SITE_PRICES_ROUTE_PATH`). This is open choice 1 in the notes.
2. **Not covered:** cold and EV Finding-page cost tiles, and Portfolio placement `UNPRICED_RISK` reasons.
   - The placement wire is policy-versioned.
   - Cold and EV Finding pages read other endpoints.
   - Their money reaches the estate Financials rows (PRODUCT gets `NEEDS_MODEL stock_record`; TARIFF gets `SET_PRICE`).
   - `RECORDED_REPAIR` uses a need key `repair_cost_record` that is not in the spec, with its own text. It needs Architect confirmation.
3. **Keys not yet stored.** Some `SET_PRICE` keys (`repair_visit_cost`, `planned_service_cost`, `charger_repair_cost`) are not stored until PR-3. The link is still offered, per spec §4.1 ("the link is never hidden").
4. **Portfolio OPERATING_COST card.** It carries `price_action`, but no current screen renders the value cards.

## Residual risk

- **AR-4 parity.** It compares money lines and Portfolio bodies byte for byte. This slice adds `price_action` to `_line` and `_card`, so whichever lands second must carry the key on both paths. Coordinate the rebase order.
- **Stored snapshot bodies.** Any board, warning or money body stored before this change lacks the key; the frontend treats it as optional.
- **AR-0 parity.** If it compares stored rows against fresh composition, it will see the added key.

## User-review focus

- The draft and choices 1-6 in `.agent/PR-draft-notes.md`. Choice 6 answers the owner's 18:10 "where do I enter the price" question.
- Whether "Set a cost per visit for GreenHarvest →" reads right on the Portfolio early warnings.
