# W3-02 commit-3 re-review (r1 fix round)

Head `cfa428ccdbcf2479f1aee3c9e8afa1f8e5c0e0ec`; fix commits `f4242856` and `8ad9d842` (plus a main merge). Read via git objects only. Tests were not rerun; verified by diff reading against the r1 rulings.

## Verdict: ACCEPT

- M1: closed. The cold branch of `windowed_lines` now sets `covered=False` when `read["withheld"]` is true (`financials.py` +2). The test extension in `test_w302_money_historical_pending_and_no_gap_rows` is non-vacuous. It asserts UNKNOWN_COVERAGE with `["NO_LINES","UNKNOWN_COVERAGE"]` for withheld with no head, and UNKNOWN_COVERAGE with a null amount and no NO_LINES for withheld with a head. It asserts the NO_LINES and INELIGIBLE results for `cold_withheld=False`. The first case is the one the r1 review's probe showed returning NO_LINES.
- M2: closed. The pending-rulings header is now "RESOLVED, both items", and item 1 cites the r1 M2 ruling. The construction was unchanged, as ruled. Nit: item 2's body still opens "Needs a ruling" (historical text, not blocking).
- L1: closed. `forced` is `withheld = guard != ERROR_PENDING; pending = guard == ERROR_PENDING`. A new vector covers HISTORICAL_CURRENT_CLAIM, STALE_BASIS and PENDING_RECOMPUTE, with line state and reasons and the group's UNKNOWN_COVERAGE and null amount asserted.
- L2: closed. The EV fingerprint uses `TARIFF_UNIT` (`currency/kWh`), and the quantity unit stays `kWh`. A new test asserts both.
- L4: closed. An eligible line in an INELIGIBLE group, with no reasons of its own, gets only PARTITION_INELIGIBLE. The line stays ELIGIBLE. The pending mate keeps PENDING, and the group keeps the union. A new test asserts this.
- L6: closed. The docstring, the stale N3 comment and the fixture summary are fixed. The fixture's operative fields are unchanged.
- L3 and L5: correctly carried to commit 4. The handoff entry records the copy requirements, the UI state check, and plain-language rendering of PARTITION_INELIGIBLE.

No new findings. Residual risk is as in r1: the implementer's 136 passed, 0 skipped is not independently rerun here.
