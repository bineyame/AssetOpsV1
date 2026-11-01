# POLISH-PC Final gate of the client-demo polish round

Status: in_review
USER_REVIEW_REQUIRED: true
Lane: after both lanes merge. Units: 3. Branch `task/POLISH-PC-final-gate`.

The spec is `.agent/build-sheet-POLISH.md`. The sections that apply:
- §5 "PC · Final gate", §6 (rulings logged for the walkthrough), §7 (register rows).
- Every addendum (1-13). Addendum 13 item 3: PC rebuilds `assetops_polish_full_test` from merged main before the strict
  28-capture run.
- Review Lows folded into PC: PB-3 review N1 and N2, and the EV tariff copy residual.

This file states scope only. The sheet is the contract.

## Scope

- **Copy pass.** N1 (`REGISTERED_SIMULATION` reads "Example data"), N2 (EV Energy "Charging tariff"), the EV
  "No charging income estimate yet" fallback matching the server, and the EV Analysis/Financials/Assumptions/Energy
  "Scenario" leftovers. Pins updated; no guard loosened.
- **Rebuild.** `tools/demo_combined.py --db assetops_polish_full_test --work var/polish_full prepare` from this branch;
  finish check 17/17.
- **Strict capture.** 14 keys x 2 widths, `DEMOB_STRICT=1`: 0 counted hits, 28/28 settled, no overflow. One
  review-mode set; `-open` looks at the cold and EV disclosures where the tool supports it.
- **Full suites.** Slow demo build test, full vitest, backend `-Tier all`, check-all 12/12.
- **Register reconcile.** R625-R662, close R626, R630, R111 (demo) and P-B3-3.
- **Runbook.** `.agent/POLISH-runbook.md`: start steps, timings, links, the demo3 fallback, the owner-confirm list.

## Not in scope

- New behaviour, new server text beyond the named copy rows, the §8 Lows.
- `assetops_demo3_full_test` (walkthrough fallback; never touched).

## Checks

- Targeted vitest for the copy pins, the vocabulary guard, then the heavy jobs one at a time in the order: rebuild,
  capture, slow test, full vitest, `-Tier all`.
