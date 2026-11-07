# Build sheet CH-5d: the Portfolio evidence cell and the Optimize card from the chain

- Architect: Claude (Architect 6), 2026-11-04. This is split out of the earlier CH-5c (unit u3) by OWN-CH5c (owner: "go with option A"), which turned CH-5c into a lane-1 performance slice ahead of CH-6. These two labelled keeps need CH-6b's EstateChain, so they cannot ride in a slice that comes before CH-6.
- Lane 2, **last**: branch `task/CH-5d-portfolio-cells`, cut from main after **DD-1b and CH-6b** have merged. **1 unit.**
- Inputs: CH5a-R R5; CH-6 §S.2, R4, §B2 and §B4; I-16 (Optimize part). Paths: `B/` = `backend/assetops_backend/`.

## 1. Rulings (carried unchanged from CH5c-R)

| # | Gap (code reality) | Ruling |
|---|---|---|
| R4 | The Portfolio evidence cell (`B/estate/portfolio.py:472-481` `evidence_cell_state`, used `:507`) is a labelled keep → CH-5c. | **Fixed.** The cell is `readiness_of(days)` (`B/chain/read.py`, CH-5a1) over the Site-local days of `[from, to)` for each Site, from the EstateChain day rows (CH-6b `request.days_rows`, one query for all Sites). It honours `known_at` through snapshots, so the old "historical → UNKNOWN" (`:475`) becomes the snapshot grade at `k` (allowed change P-E2). `evidence_cell_state` is deleted, with its tests rewritten. `evidence_unit` (coverage units) is kept for the status: labelled keep → CH-7. |
| R5 | The Optimize card. CH-6b leaves it "unchanged (CH-5c)" on the money lines, which withhold money from a partly checked period (`B/estate/coverage.py:240-256`, `withhold`; I-16). The board shows the same Finding's money through `money_head` (settled day, CH5a-R R4). The two can disagree. | **Fixed.** The Optimize card reads each Site's `rows.OPTIMIZE_COST` cost claim from EstateChain: the `avoided_cost@1` claim over `money_head` (CH-6 R4), `basis` from `count_basis` over the window's days (CH-6 §S.2). Texts are CH-6 §A4 `money.days` / `money.days_partial` / `money.not_known`, unchanged. Never summed across Sites (design A6, D-AW-5). COH-17 extends to the Optimize money claim. The Portfolio money **lines** (`/estate/financials`, cost cell, token) keep `withhold`: labelled keep → CH-7. |

## 2. Pre-flight
- **P5.** Every caller of `select_dispatch_days_on`, `evidence_cell_state` and the Optimize card's current inputs (`F/estate/PortfolioOutcomes.tsx` after CH-6b), with `path:line`.
- **P6.** The EstateChain field CH-6b emits for the Site's cost claim (`rows.OPTIMIZE_COST.nodes` or a separate claim), so the card reads one field. If CH-6b emits no cost claim on the Portfolio, stop. The Architect decides whether §3.5 builds it here (+0.25) or drops it.
- **P7.** CH-5c's stored responses: confirm that the Portfolio body change invalidates stored copies through `CODE_VERSION`, and add the CH-5c parity test, stored copy against a fresh compute, for the changed Portfolio.

## 3. Work
### 3.4 Portfolio evidence cell (R4)

As ruled in R4. `objective()` (`B/estate/portfolio.py:498-509`) takes the cell value from the EstateChain day rows passed in. It calls no selection for the cell.

### 3.5 Optimize card (R5)

- Backend: `B/chain/vocabulary.py` already holds the texts (CH-6a). The Portfolio body (CH-6b) gains or reuses the Site's cost claim (P6).
- Frontend: the Optimize card renders the claim text only. The browser card rule for Optimize, if CH-6b left one in `PortfolioOutcomes.tsx`, is deleted (design §8b item 4). The CH-5b hard-wiring ratchet only shrinks.


## 4. Acceptance
- The allowed changes are **P-E1** (the evidence cell equals `readiness_of` over the Site's window days, and equals the board chip for one day), **P-E2** (a historical cell shows the snapshot grade at `k`) and **P-O1** (the Optimize card shows each Site's cost claim by basis). Everything else is byte-equal against main. COH-17 extends to the Optimize money claim.
- Tests: L0/L1 card and claim fixtures; L2 on `pg_harness`; L3 on the DD-1 clone; L3m. Scoped `test_w303_portfolio_*`, `test_ch6b_*`, `estatePortfolio.test.tsx` and the `PortfolioOutcomes` tests. Guards A, W, N, V, M, and the CH-5b and CH-6 ratchets.

## 5. DS-R1 and OL-1
- Portfolio evidence cell via `evidence_cell_state`: **fixed**.
- Optimize card withholding money in a partly checked period: **fixed** for the card; the money lines' `withhold` is a **labelled keep → CH-7**.
- OL-1: no outcome id is added.

## Build units (split 2026-11-05)

- Architect: Claude (Architect 13), 2026-11-05. Plan row **SPLIT-1**. **One unit, CH-5d1 (1), not split.** It is already one builder's worth.
- **Depends on:** CH-6b3 and DD-1b2 merged (lane 2, last). Own review; a Sonnet re-review for named findings.
- **Reading budget:** this whole sheet (37 lines); `.agent/build-sheet-CH-6.md` §S.2, R4 row, §A4 rows `money.*`, §B1 and the Optimize row of §B2 only. Code: `B/estate/portfolio.py:465-515`, `B/estate/coverage.py:235-260`, `readiness_of` in `B/chain/read.py` (grep), the EstateChain `rows.OPTIMIZE_COST` field (P6), `F/estate/PortfolioOutcomes.tsx` Optimize card (grep), the CH-5c `CODE_VERSION` and parity test (grep `code_version`).
- **Acceptance:** §4 as written (P-E1, P-E2, P-O1; everything else byte-equal against main; COH-17 over the Optimize money claim; the CH-5c stored-copy parity test for the changed Portfolio); guards A, W, N, V, M and the CH-5b and CH-6 ratchets.

## Scope cut (SCOPE-1)

- Architect: Claude (Architect 16), 2026-11-05. Plan row **SCOPE-1**. Owner, verbatim (`.agent/owner-scope-backlog-2026-11-05.md`): "put implemnatation that are not demo critical to a backlog, don't keep on pilling commitments", then "let architect divide the remaing work accordingly and only focus on what we should be presenting defensibily to the frist clients". Test and backlog: `.agent/backlog-post-demo.md`. This section overrides the "Build units" section and every earlier ruling where they differ; backlogged text above is history, not scope.
- **CH-5d1 (1): unchanged.** Both fixes stop the Portfolio contradicting the board (evidence cell vs board chip; Optimize money withheld on the card but shown on the board), and the stored-copy parity test guards against stale pages. Depends on CH-6b3 and DD-1b2 (lane 2, last). The "CH-6 ratchets" in its acceptance means the CH-5b frontend ratchet only (the outcome-id ratchet is BL-04).

## CH5d1-R: pre-flight ruling on today's main (2026-11-07)

- Architect: Claude (fresh Architect, CH-5d1). Binding checked: `.ai/ROLE_CONFIG.md` Architect = Claude (2026-10-27). Main at `1c2e5ed28` (DD-1b2b merged, check-all 17/17). **This section overrides every earlier section of this sheet where they differ.** Paths: `B/` = `backend/assetops_backend/`, `F/` = `frontend/src/`.

### 1. Code reality and the cut (SCOPE-1)

| Item | Code on main | Ruling |
|---|---|---|
| R4 evidence cell | `objectives[].cells[EVIDENCE]` (`B/estate/portfolio.py:526-534`, `:561`) is on the Portfolio wire but **not rendered**: `F/estate/EstatePortfolio.tsx:345-347` (OUT-B B6, "The portfolio body's `objectives` wire stays but is not rendered"). The matrix and dots come from `/api/estate/outcome-summary`. `site_readiness` / `site_readiness_many` (`B/estate/evidence_money.py:488-552`) have test callers only. The one reader is finish row CO-9 (`tools/demo_combined_finish.py:375-381`), which only asserts "not UNKNOWN". | **Cut → BL-51.** No client sees the cell, so it cannot contradict the board on screen. Nothing in R4 is built. CO-9 is unchanged. |
| R5 Optimize card | The card still reads the CH-5c money line: `F/estate/PortfolioOutcomes.tsx:121-128` (`value_cards` `OPERATING_COST` via `cardValue`, `:29-49`), with `withhold` in `B/estate/coverage.py:243-256`. Its words are system vocabulary (`B/estate/portfolio.py:384-389`: "Site-owned selected consequence", "No selected operating-cost consequence", "No value line"). Its "Why?" (`B/chain_api.py:363-399`) explains each Site's **board** Optimize row (chain nodes, CH-6a3 price line) and borrows Protect's days line. So the value and its "Why?" come from two different sources. `portfolio_cards` (`B/site_outcomes/read.py:745-781`) builds Grow, Protect and Assure only (CH6b2-R Q3). | **Kept, demo-critical.** DS-1 ST-1 opens the Portfolio on "the four card values" and a "Why?". Today the Optimize value is not traceable through its own "Why?" and uses system words. That fails the SCOPE-1 test. |
| P6 | The chain already carries the cost claim: each summary Site row's `nodes.earnings` (`B/site_outcomes/read.py:614-617`; window re-evaluation `:486-511`). The only Optimize money record is MG-2 `possible_extra_fuel_cost`, `avoided_cost@1` over `money_head` (`B/outcomes/outcome_map.py:161-164`, `B/chain/strategies/avoided_cost.py`). The stored consequence has no days, so its claim's basis is NOT_KNOWN and its text is the amount alone (CH6a2-R Q2, `B/chain/vocabulary.py:381-400`). | Satisfied; nothing is built. R5's "basis from `count_basis` over the window's days" is **superseded** by CH6a2-R Q2. |
| P7 | `code_version` hashes every backend source file (`B/chain/adapters/file_code_version.py:1-6`), so a changed `read.py` invalidates the stored copies by construction. | Satisfied. Only the parity run below is owed. |

**Scope of CH-5d1 after the cut:** the Portfolio Optimize card from the chain's per-Site cost claims, built by the one card builder. Nothing else.

### 2. Build

**2.1 Backend: `B/site_outcomes/read.py`**
- Add `COST = "OPTIMIZE_COST"` beside `GROW, PROTECT, ASSURE` (`:689`).
- Add `_optimize_card(sites)`. `portfolio_cards` returns it under `COST`, first in the dict, so the order is Grow, Optimize, Protect, Assure. No signature change.
- Inputs, per Site in Site order: `row` = the Site's `rows[]` entry with `category == OPTIMIZE_COST`; `claim` = `(row.get("nodes") or {}).get("earnings")`. A Site is **priced** when `claim` is not None and `claim["value"] is not None`. A Site whose board failed (`_unknown_row`, nodes None) is never priced. Nothing else is read; there is no reach into `value_cards`, `/estate/financials` or the coverage money lines.
- Output, the same shape as the other cards (`{value:{text,small}, missing, detail, basis_text, days_line, tone, claim}`), with `missing` always False:

| Case | `value.text` | `value.small` | `detail` | `basis_text` | `tone` | `claim` |
|---|---|---|---|---|---|---|
| 0 priced Sites | `NOT_KNOWN_TEXT` ("Not known yet") | None | `cost.detail.none` | `cost.basis.none` | `neutral` | None |
| 1 priced Site | `claim["text"]`, **byte-equal** (ONE-SOURCE; for a stored consequence it is the amount) | `COST_SMALL[label]`, label = `claim["key"].removeprefix("money.")` | `cost.detail.one` (site = site name) | `cost.basis.money` | `amber` | that claim, unchanged |
| ≥2 priced Sites | `cost.sites` (sites = `sites_text(n)`) | None | `" · ".join(cost.site per priced Site)` | `cost.basis.money` | `amber` | None |

- Never summed (design A6, D-AW-5). No Decimal arithmetic in `_optimize_card`.
- `days_line` = `_site_days(priced sites, days of that Site's claim)`, which is None for a stored consequence (days None). Do not change `_estate_why`: with no Optimize days line it keeps Protect's line (CH6b3-R3 M2).
- An unknown label in `COST_SMALL` is a KeyError. Fail loud, never blank.

**2.2 Backend: `B/chain/vocabulary.py` `CARD_TEXT`** (new keys, verbatim):
- `"cost.detail.none": "No cost worked out yet at any site"`
- `"cost.detail.one": "At {site} · not added across sites"`
- `"cost.site": "{site}: {text} {small}"` (≥2 case: text = claim text, small = `COST_SMALL[label]`)
- `"cost.sites": "Costs at {sites}"`
- `"cost.basis.money": "Modelled from the stored record and the declared price · not a saving"`
- `"cost.basis.none": "A cost needs a priced record"`
- A new dict `COST_SMALL = {"possible_extra_fuel_cost": "possible extra fuel cost"}`, next to `INCOME_LABELS`.
- **MOCK DEVIATION MD-CH5d-1** (v70 `outcomes.js:190`, `pfCard` `cost`): the mock shows one bare amount (`money()`), detail "Kobo generator time, 1 trial in hand · …", basis "Modelled + scenario · one-hour window · reliability checked as a safeguard", and a days line "Kobo: 6 Oct partly checked · GreenHarvest: from 3 work records". We show the claim's amount with the small words "possible extra fuel cost" (AG-24: money is labelled modelled), our own detail and basis words (no scenario or one-hour window exists behind this claim), and no days line (a stored consequence has no counted days, CH6a2-R Q2). Tone amber and the `/financials` link match the mock. Put the label as a code comment on the new keys and as a row in the packet.

**2.3 Frontend: `F/estate/PortfolioOutcomes.tsx`**
- `content()`: delete the `OPTIMIZE_COST` branch (`:122-128`). Optimize then takes the generic summary-card path (`:129-144`) with one exception: `note` stays `null` for Optimize, as today (byte-equal; `card_notes` has no Optimize clause on screen).
- Delete `OPTIMIZE_COST_MISSING` (`:75-82`) and `cardValue` (`:28-49`); Optimize was their only caller. Keep `amountOf`, which `F/estate/EstatePortfolio.tsx:718` uses.
- The card destination stays `CARD_DESTINATION.OPTIMIZE_COST` = `/financials`.
- No new CSS and no layout change. The card already renders `value.small`, `detail`, `basis_text`, `days_line` and tone for the other cards.
- `F/estate/estateClient.ts`: allow `OPTIMIZE_COST` in the summary `cards` type if it is narrower today. No other type change.

**2.4 Coherence: `tools/checks/chain_coherence.py` `_coh17_full`** (COH-17 extends to the Optimize money claim). New row **O1** per estate window:
- the priced Sites, read from summary `sites[].rows[OPTIMIZE_COST].nodes.earnings` by the 2.1 rule, give the expected card;
- 0 priced: `value.text == NOT_KNOWN_TEXT` and `claim is None`;
- 1 priced: `claim ==` that node claim and `value.text == claim["text"]`;
- ≥2 priced: every priced Site's name prefixes one of the detail's `" · "`-separated lines, and `claim is None`.
- C3 (chain cards == summary cards) and V4 (summary nodes == board nodes, S, mini) already tie the card to the board. Add an O1 self-test case (pass and fail) to the coherence check's existing self-test file (grep `_coh17_full` under `tools/checks/`).

**2.5 Untouched (labelled keeps):** the Portfolio body's `value_cards` `OPERATING_COST` stays on the wire, unrendered → BL-51. The `/estate/financials` money lines keep `withhold` → CH-7, as already ruled in R5. The evidence cell and `site_readiness*` are unchanged → BL-51. Migrations: none. Schema version: no bump (an additive card key, as CH-6b2 did).

### 3. Tests

- **L0, new `backend/tests/test_ch5d1_optimize_card.py`:**
  - 0 / 1 / 2 priced Sites, each against the table literals;
  - one priced Site plus one Site with a NOT_KNOWN earnings claim (not priced);
  - a failed Site (`_unknown_row`) ignored;
  - the 1-Site `value.text` is byte-equal to `claim["text"]`;
  - a claim with days produces a days line through `_site_days`; days None gives None;
  - an unknown label raises KeyError;
  - the ≥2 case contains no summed amount (assert that no Decimal sum of the two amounts appears in any field).
- **L0, `backend/tests/test_ch6b2_portfolio_cards.py`:** update only the assertions on the `portfolio_cards` key set or order. Grow, Protect and Assure expectations stay byte-equal.
- **L2m, `backend/tests/test_ch6b_estate_postgres.py`:** one new test on `mechanism_db()`. For the week window, the summary's Optimize card equals `_optimize_card` over that body's own Site rows, `cards` on `/api/estate/chain` equal the summary's, and the Kobo Optimize row's `nodes` equal the S board's.
- **Stored copy (P7):** `backend/tests/test_ch5c_response_store_postgres.py::test_stored_bytes_are_served_and_equal_a_fresh_compose`; then `tools/chain_response_probe.py` on the L3m DB for the summary and `/api/estate/chain` routes on week, S and month: stored == fresh, 0 differences.
- **Frontend** (vitest by listing files):
  - `F/estate/__tests__/estatePortfolio.test.tsx`: replace the two `OPERATING_COST` card tests (`:575-600` area) with summary-card tests: one priced Site (value, small, detail, basis, amber), none ("Not known yet", neutral), and no `/api` text anywhere;
  - `F/estate/__tests__/portfolioFixtures.ts`: add an `OPTIMIZE_COST` summary card;
  - the `PortfolioOutcomes` / `evidenceTrace` tests that select the Optimize card;
  - `estateFinancials.test.tsx` only if it imports a deleted export.
- **Guards:** A, W, N, V, M; `node tools/checks/frontend-hardwiring.mjs` (the CH-5b ratchet). The count must not rise. If it falls, run `--shrink` and commit the lowered numbers. The missing-claim guards need no change, because no new `MissingClaim` is added.
- **Not run:** the full suite, prepare, baseline build, `test_demo_combined_postgres`, check-all (coordinator, after merge).

### 4. Measurements owed (packet table)

- **M1, before any code**, on the L3m DB: for week, S and month, record each of the following:
  - the Kobo Optimize row `lead_outcome`;
  - `nodes.earnings` (key, value, basis, days, text) from the summary;
  - the old card from `/api/estate/portfolio` `value_cards` `OPERATING_COST` (state, display_value, detail, basis_text);
  - Cold's and EV's Optimize `nodes.earnings`.
- **M2, after the build**, on the same DB and windows:
  - the new Optimize card (all fields);
  - the COH-17 O1 result;
  - the probe's stored == fresh result;
  - each Site's Optimize "Why?" `comes_from` lines (unchanged by this unit; recorded so the packet shows the value and its "Why?" now share a source).
- **Owed at E3, not by the builder:** the Optimize card on the full demo data, in the E3 captures. Expected (DS-1 carry lines): "Not known yet", because the generator problem carries no fuel figure. A money value there is an E3 finding against DS-1, not a reason to edit this unit.

### 5. Stops (report to the Architect; do not design around them)

- **S1.** The Kobo summary row for `OPTIMIZE_COST` carries no `nodes.earnings`, or the key is not `money.possible_extra_fuel_cost` (M1). The card would always read "Not known yet" for a structural reason.
- **S2.** Any byte change on the summary, chain, Portfolio or Why bodies other than `cards.OPTIMIZE_COST` (and the hash and ETag that follow from it), or any change to the Grow, Protect or Assure card rendering.
- **S3.** The hard-wiring ratchet count rises.
- **S4.** M2 shows the Optimize card with money while the Kobo board's Optimize `nodes.earnings` on the same window is NOT_KNOWN, or the other way round.
- **S5.** The work needs more than 1.0 unit, or it needs any edit to `B/estate/coverage.py`, `B/estate/financials.py`, `B/estate/portfolio.py` or the evidence cell.

### 6. Branch, worktree, DB, size

- Branch `task/CH-5d1-optimize-card`, cut from main at or after `1c2e5ed28`. Worktree `C:\Users\assef\Bineyame\AssetOpsV1-ch5d1`. The builder creates both.
- **DB.** Two databases:
  - pg_harness base `ASSETOPS_TEST_DATABASE_URL` → `assetops_ch5d1_test` on 127.0.0.1:55432 (run-owned clones `assetops_ch5d1_pt*_test`). Read the credentials from the repo config; never guess them.
  - L3m and the M1/M2 reads on `assetops_mechanism_test`, rebuilt once with `tools/mechanism_dataset.py full` (the states template is stale on merged main, about 1300 s). Lane 1 is idle, so no other builder shares it.
  - Never `assetops_demo3_full_test`, never a polish DB, no prepare, no baseline build, no full suite. Drop `assetops_ch5d1_*` after the merge.
- **Size: 0.75 unit** (1.0 → 0.75; R4 cut, −0.25 → BL-51). Own Opus review; a Sonnet re-review for named findings. The plan's CH-5d row and G5/G6 need −0.25 (coordinator).
- **Owner:** nothing to decide. Inform only: on the demo data, the Optimize card will most likely read "Not known yet" (no fuel figure), and its "Why?" now matches it.
