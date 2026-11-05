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
