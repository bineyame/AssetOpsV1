# Review packet CH-5d1: the Portfolio Optimize card from the chain

- Spec: `.agent/build-sheet-CH-5d.md` ruling **CH5d1-R** (commit 1428e3a8c). Branch `task/CH-5d1-optimize-card`, cut
  from main 1428e3a8c. Build commit `151580feb`. Main has since gained MV-1 (e31ccbbb8); no file overlaps this branch.
- USER_REVIEW_REQUIRED: no (ruling §6 "Owner: nothing to decide"). Own review next.

## Outcome

The Portfolio Optimize card is now built by the one card builder (`portfolio_cards`) from each Site's chain cost claim
(`sites[].rows[OPTIMIZE_COST].nodes.earnings`), the same claim the board and its "Why?" show, never summed across Sites.
The browser renders the server card only. COH-17 gains row O1.

## Files

| File | Change |
|---|---|
| `backend/assetops_backend/site_outcomes/read.py` | `COST`, `_cost_claim`, `_optimize_card`; `portfolio_cards` returns Grow, Optimize, Protect, Assure. No signature change. |
| `backend/assetops_backend/chain/vocabulary.py` | `COST_SMALL`; `CARD_TEXT` keys `cost.detail.none/one`, `cost.site`, `cost.sites`, `cost.basis.money/none` (verbatim from the ruling), with the MD-CH5d-1 label comment. |
| `frontend/src/estate/PortfolioOutcomes.tsx` | The `OPTIMIZE_COST` branch, `cardValue` and `OPTIMIZE_COST_MISSING` were deleted. Optimize now takes the generic summary-card path, with `note` held `null` as before. `amountOf` is kept. |
| `frontend/src/estate/portfolioWords.ts` | `CARD_VALUE` deleted (dead: `cardValue` was its only caller). See KD-3. |
| `frontend/src/estate/estateClient.ts` | Summary `cards` type allows `OPTIMIZE_COST`. |
| `tools/checks/chain_coherence.py` | `coh17_optimize` (row O1), called from `_coh17_full` after C3. |
| `tools/checks/test_chain_coherence.py` + bundles `clean_full`, `coh18_day_grades` (summary/chain week+S) | The O1 self-tests: 9 direct cases (pass and fail) and 2 planted bundle breaks. Both stamped fixture bundles gain the none-priced Optimize card. |
| `backend/tests/test_ch5d1_optimize_card.py` (new) | L0, 7 tests. |
| `backend/tests/test_ch6b2_portfolio_cards.py` | Only the key-set assertion changed (now asserts the order). |
| `backend/tests/test_ch6b_estate_postgres.py` | New L2m test (not run, see KD-1). |
| `backend/tests/test_out_b2_vocabulary.py` | Sample gains `small`, so `cost.site` formats; `COST_SMALL` values are scanned. See KD-2. |
| `frontend/src/estate/__tests__/estatePortfolio.test.tsx`, `portfolioFixtures.ts` | Two `OPERATING_COST` card tests became summary-card tests (one priced Site; none; no `/api` text). Five other Optimize assertions were restated. The Optimize detail is no longer excluded from the w1 vocabulary scans. The fixture gains `OPTIMIZE_ONE_SITE` / `OPTIMIZE_NONE`, plus an `OPTIMIZE_COST` entry in `serverCards`. |

## Mock deviation

**MOCK DEVIATION MD-CH5d-1** (v70 `outcomes.js:190`, `pfCard` `cost`). The mock has a bare amount, the detail "Kobo generator time, 1 trial in hand · …", the basis "Modelled + scenario · one-hour window · reliability checked as a safeguard", and a days line. We show the claim amount with the small words "possible extra fuel cost" (AG-24), our own detail and basis words (there is no scenario or one-hour window behind this claim), and no days line (CH6a2-R Q2). Tone amber and the `/financials` link match the mock. The label is a code comment on `COST_SMALL` and on the new `CARD_TEXT` keys.

## Measurements

L3m DB `assetops_mechanism_test`, rebuilt with `tools/mechanism_dataset.py build --variant full`. The first run stopped at its budget (exit 3, D1–D14 in about 1100 s). The `--resume` run then did drain_mini (457 s), studies (42 s) and derive (71 s), for about 1670 s in total. Story S = 2026-10-31. Windows: week = 10-25..11-01, S = 10-31..11-01, month = 10-03..11-03. The DB is Kobo only (MD0-S2), so there are no Cold or EV Optimize rows to record.

**M1 (before any code, main 1428e3a8c)**

| | week | S | month |
|---|---|---|---|
| Kobo Optimize `lead_outcome` | MG-2 "Supply cost per kWh" | same | same |
| Kobo `nodes.earnings` | key `money.possible_extra_fuel_cost`, value null, basis NOT_KNOWN, days null, text "Not known yet" | same | same |
| Same claim on the Kobo board | equal | equal | equal |
| Old card (`value_cards` `OPERATING_COST`) | NO_LINE · "No supported value" · "No selected operating-cost consequence" · "No value line" · neutral | same as week | WITHHELD · "Can't be compared across these sites yet" · "Inspect Site records and exclusions" · "No combined operating-cost amount" · neutral |
| Cold / EV `nodes.earnings` | not on this DB | — | — |
| Summary `cards` keys | Grow, Protect, Assure | same | same |

No S1: the claim is present and its key is `money.possible_extra_fuel_cost`. It carries no value on this DB.

**M2 (after the build, `151580feb`)**

| | week | S | month |
|---|---|---|---|
| New Optimize card | `{value:{text:"Not known yet",small:null}, missing:false, detail:"No cost worked out yet at any site", basis_text:"A cost needs a priced record", days_line:null, tone:"neutral", claim:null}` | same | same |
| Card == `_optimize_card(summary.sites)`; key order | true; Grow, Optimize, Protect, Assure | same | same |
| `/api/estate/chain` `cards` == summary `cards` | true | true | true |
| COH-17 O1 | 0 findings, compared 1 | 0, 1 | 0, 1 |
| S4 (card money iff Kobo board claim has a value) | no money / NOT_KNOWN: consistent | consistent | consistent |
| Optimize "Why?" `comes_from` (unchanged from M1) | ["Kobo mini-grid: Unknown"]; Kobo: "Unused daytime solar on 1 checked day", "Generator time beyond need on 1 checked day" | same | ["Kobo mini-grid: Unknown"]; Kobo: "Nothing has been recorded for this yet" |
| "Why?" `days_used` (Protect's line, as ruled) | "Kobo mini-grid: 6 of 7 days checked" | "1 of 1 day checked" | "13 of 31 days checked" |

The card's value and its "Why?" now both come from the board's Optimize row. The card reads "Not known yet", and the row's claim is NOT_KNOWN.

**Stored == fresh (P7).** `tools/chain_response_probe.py fresh` on the L3m DB ran in 397 s and reported 28/43:

- Summary week, S and month are equal (stored).
- `/api/estate/chain` week and its four "Why?" bodies are equal (hit).
- All 15 DIFF rows are Cold and EV board, chain and "Why?" paths. They return `404 SITE_NOT_FOUND` on this Kobo-only DB (both sides 404, checked directly), so they are outside this unit.

The probe's own path set has `/api/estate/chain` for week only. The same method (store, then hit, then a store-less compose; scratch `chain_sm_fresh.py`) gives chain S and month: 2/2 equal, 0 masked. The `test_ch5c_response_store_postgres.py::test_stored_bytes_are_served_and_equal_a_fresh_compose` test passed.

**S2 byte check.** Same DB, branch against main (1428e3a8c), store off: the summary, chain, every Portfolio page and the four estate "Why?" bodies, on week, S and month (21 bodies). With `cards.OPTIMIZE_COST` removed from the six branch summary and chain bodies, and `known_at`/`selection_token` masked, there are **0 differences**.

## Acceptance (CH5d1-R)

- 2.1 builder (cases 0/1/≥2, failed Site, never summed, days line, KeyError): met (L0 7/7).
- 2.2 texts and `COST_SMALL` verbatim: met.
- 2.3 frontend: met. No CSS or layout change; destination `/financials`.
- 2.4 O1: met. Non-vacuity was proven by forcing `coh17_optimize` to return `[]`: 8 self-tests fail. Reverted with `git checkout`.
- 2.5 untouched: `coverage.py`, `financials.py`, `portfolio.py` and the evidence cell are unedited. No migration and no schema bump.
- §3 L2m: written, **not run** (KD-1). Its assertions are covered on the full L3m DB by M2 and the S2 check.
- Stops: S1 none. S2 none (0 differences). S3 none (ratchet totals unchanged: api 12, href 24, lit 70, cmp 51, code 3). S4 none. S5 none (no edit to the named files; within 0.75 unit).

## Checks run

- Backend L0 (no DB): `test_ch5d1_optimize_card`, `test_ch6b2_portfolio_cards`, `test_out_b2_vocabulary`, `test_ch6b_estate_chain`, `test_w303_portfolio_api`, `test_w303_portfolio_reduction`, `test_w303_portfolio_workflow_labels`. Result: 138 passed, 1 skipped. The skip is the one `test_w303_portfolio_api` DB test, which then passed in the Postgres run.
- Backend Postgres on `assetops_ch5d1_test` (pg_harness): the stored-bytes test plus `test_w303_portfolio_api`, `_comparison_postgres`, `_fixture_postgres`, `_scope_snapshot_postgres`. Result: 24 passed, 0 failed.
  - It took three runs. The combined run hit my 590 s and then 1200 s caps at `[c2_mixed]`, because another builder's pytest was loading the machine.
  - That case then ran alone: 135 s on the branch and 126 s on main, both passed.
  - The remaining 3 cases passed in 129 s.
- `test_ch6b_estate_postgres.py`: not run (KD-1).
- Coherence self-tests `tools/checks/test_chain_coherence.py`: 150 passed.
- Frontend: `npx tsc --noEmit` clean. Vitest on `estatePortfolio.test.tsx`, `evidenceTrace.test.tsx`, `estateFinancials.test.tsx` and `estateRoots.test.tsx`: 108/108.
- Guards:
  - A, W and N (`check-architecture`, `check-agent-workflow`, `check-navigation-truthfulness`): all pass.
  - V (`test_out_b2_vocabulary.py` passed; `test_mock_deviation_labels.mjs` 14/14).
  - M (`missing-claim-scan.mjs` passed; `test_missing_claim_scan.mjs` 26/26).
  - CH-5b ratchet `frontend-hardwiring.mjs` passed with the count unchanged, so no `--shrink` was needed.
- Not run, as ruled: the full suite, prepare, the baseline build, `test_demo_combined_postgres`, and check-all.

## Known deviations

- **KD-1 (precondition).** The L2m test uses the `mech` fixture, which clones the `states` template. That template is stale on this checkout: `TEMPLATE_STALE: template inputs abc647639e60 != this checkout 6780e1498733`. Rebuilding it (`build --variant states`) was not authorized in this dispatch. The test is committed but unrun. Its three assertions were measured on the full L3m DB instead (M2 rows 2–3, the board equality in M1/M2, and S2). It is owed when a states template exists.
- **KD-2.** `test_out_b2_vocabulary.py` (guard V) needed a `small` sample field, because `cost.site` would otherwise raise a KeyError in the guard. I also added the `COST_SMALL` values to the scanned copy. This is a test-only edit that the ruling does not name.
- **KD-3.** `CARD_VALUE` (`portfolioWords.ts`) was deleted as dead code. The ruling names only `cardValue` and `OPTIMIZE_COST_MISSING`, but `cardValue` was `CARD_VALUE`'s only reader.
- **KD-4.** The `nodes.earnings` claim on the wire also carries a `days_line` field. The card's `claim` is that dict unchanged (ONE-SOURCE).
- **KD-5.** The Optimize priced paths (1 and ≥2 Sites) are proved at L0 and in the O1 self-tests only. On the L3m DB, Kobo's claim has no value, so M2 exercises the none case. E3 owes the demo-data check (ruling §4).

## Residual risk and review focus

- `_optimize_card` treats any claim with a non-null `value` as priced, including the `{low, high}` form. Its text is used byte-equal.
- The O1 ≥2 rule checks name prefixes and `claim is None`, as ruled. It does not re-check the amounts, which V3/V4 tie to the board.
- Clean up after the merge: the `assetops_ch5d1_test` base and its `assetops_ch5d1_pt7a6092bd_{tpl,main}_test` clones remain. Per ruling §6 they are dropped after the merge.
