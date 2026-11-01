# POLISH-PB-3 Estate, cold/EV and work copy; P-07, P-09, P-10

Status: in_review
USER_REVIEW_REQUIRED: false
Lane: B (frontend and tools). Units: 6. Branch `task/POLISH-PB-3-estate-work-copy`.

The spec is `.agent/build-sheet-POLISH.md`. The sections that apply:
- §1.2 (P-07), §1.4 (P-09, frontend half), §1.5 (P-10).
- The Estate, Cold, EV, Maintenance and WR rows of §3.1.
- §5 Lane B "PB-3", and §7 (R660+; close R630).
- Addenda 4, 5, 6 Q4, 7 (Q1 out-of-capture UTC list, Q6), 8 (Q3-Q6) and 12 (PB-3 pre-flight rulings).

This file states scope only. The sheet is the contract.

## Scope

- **Estate.** Portfolio, Findings and Financials copy. "What-if" replaces "Scenario" (Addendum 8 Q4). Finding and Action ids move into Technical details.
- **Cold and EV.** Their copy. "Possible cost" headings. Charger report and Finding references, with the ids in Technical details. The P-10 incident line through the `OutcomeBoard` `onRead` prop, with no new fetch.
- **Work.**
  - P-07: the `RepeatVisitNotice` states and `data-repeat-check`.
  - P-09: the Preventive cards, strip badge and row chips from the PA-2b `summary` and `due_state`, and due dates in the Site zone (Addendum 12 Q2) with the two-part time note.
  - Asset labels from the wire `asset_label`, replacing the two parsers (Addendum 6 Q4, Addendum 12 Q3).
  - Work copy, and "Not yet approved" for draft plans (Addendum 12 Q4).
- **Time.** The out-of-capture UTC list from the PB-1 packet (Addendum 7 Q1).

## Not in scope

- Server text (lane A).
- The PA-3 wire fields: board item `kind`/`occurred_at`, preventive `site_time_zone`, and `work_asset.asset_label`. The frontend treats them as optional.

## Checks

- Scoped vitest (`estate`, `work`, `sites/cold*`, `sites/Ev*`), `tsc --noEmit`, and `tools\check-all.ps1` 12/12.
- Strict captures: `portfolio-week`, `findings-*`, `cold-board-*`, `ev-board-fault`, `maintenance-preventive` and `wr-overview`.
- One full `npx vitest run` at the end.
