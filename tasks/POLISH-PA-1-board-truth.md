# POLISH PA-1 - Board truth (Lane A, 5 units)

Status: in_review

USER_REVIEW_REQUIRED: no (merges on review ACCEPT; walkthroughs deferred to the owner walkthrough after this round).

Contract: `.agent/build-sheet-POLISH.md` §1.1 (backend), §1.3 (connector wording), §1.6, §1.7, §5 Lane A PA-1,
§6 D-2, §7 (R635, R636) and Addendum 2 (pre-flight rulings). Branch `task/POLISH-PA-1-board-truth`.

## Acceptance

1. P-06: a PRICED Cost amount of zero gives headline "No fuel cost estimated: the generator was on but delivered no
   measured power" with no headline money; `COST_MONEY`/`COST_NO_MONEY` read "possible extra fuel cost on this day" /
   "No fuel cost estimated for this day". No idle-fuel model (owner Q1).
2. P-11: EV Optimize row names a tariff estimate only when Grow holds a priced tariff; otherwise
   `ROW_NOT_MEASURED_EV_COST_UNPRICED`. EV-2 `missing_records` unchanged (Addendum 2 Q-C).
3. P-12: MG-7 settles when the overview day reading is COMPLETE with zero dispatch intervals and readiness is exactly
   UNKNOWN; the Readings line states there was nothing to check. Shared `reduce_day` unchanged. Grow not changed (R636).
4. `ev.py` option reads "Investigate Connector c1" via `connector_name`.
5. D-2 / OUT-E L4: `cost_line` credits a MODELLED_IMPROVEMENT only to a VERIFIED trial; otherwise `COST_NOT_CREDITED`.
6. OUT-E L3: trial comparison `history()` orders by `recorded_at, revision_no, id`, pinned by a two-outcome test.
7. Captures `kobo-board-S`, `kobo-board-S1`, `ev-board-fault` at 1440/390 under the Addendum 2 capture-slot rule.
8. Register rows R635, R636; R626 backend part closed. Guards: check-all.
