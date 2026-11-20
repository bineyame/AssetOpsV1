# DDR rulings

Architect (Claude), 2026-11-20. Each ruling is indexed in `.ai/decisions/index-rulings-13.md`.

## D-DDR.1 The rehearsal is the runbook run as written, with a checker of what each step leaves

- **Ruling.** DDR is twelve runbook steps (spec §1) and `rehearsal_check`, which reads the records each step leaves
  and fails at the first missing one. The automated test runs the same steps; the coordinator then runs them on
  `assetops_rehearsal_ddr1` with an agent that has only the runbook.
- **Why.** "Proven end to end" means a person can do it from the runbook, not that a test harness can; the checker
  makes a skipped or bypassed step visible after the fact.

## D-DDR.2 The unseen shape is the operator's board budget, and it replaces the emulated budget

- **Ruling.** The budget arrives as an XLSX board pack (title rows, header on row 3, month as "October 2026",
  thousands separators, negatives in parentheses), read by a profile admitted by command; the emulated
  `budget.csv` is removed from the folder before loading.
- **Why.** One source system per source type per Site (D-3A6.5) forbids two budgets for a Site; the board budget
  carries Kisiwa's −60.00 contribution line, so the disagreement the screen must show (D-5B.10) arrives through the
  real path; a profile is data, so the run proves "no code change".

## D-DDR.3 Each gate reads its own step's records, never another gate's output

- **Ruling.** G1 to G10 each query the store their step writes (tenant and grants, profiles, uploads, records and
  targets, statements, snapshots, Actions) and the screen read; the order of gates follows the steps.
- **Why.** A check that trusts an earlier check's result cannot see that the earlier step was bypassed (test 4: records
  written without an upload fail G3).

## D-DDR.4 The rehearsal shows "not yet reconciled" before it shows "reconciled"

- **Ruling.** The finance lead's first figures differ by 105.00 of fuel (beyond the 51.00 allowed); the month is
  prepared and shown; the corrected figures follow and the month is prepared again.
- **Why.** Risk 2 of the plan: most operators' first comparison fails; the screen must say so plainly, and the owner
  should rehearse that conversation (3A7).

## D-DDR.5 DDR waits for 3C2

- **Ruling.** S11 and G10 need 3C2's `record_action` and `build_agreed_actions` (5c spec §4.3); DDR builds after 3C2
  merges.
- **Why.** RC9 makes the agreed change part of the deep-dive; a rehearsal that skips it would not prove the path.

## D-DDR.6 One read is added to the snapshot store: the month's portfolio rows by "as of"

- **Ruling.** `portfolio_history(tenant_id, period)` in the port, the memory store and the Postgres adapter; nothing
  else in 3B7a changes.
- **Why.** G6 must see that a snapshot was prepared between the two statements; `latest_portfolio` cannot show an
  earlier one.
