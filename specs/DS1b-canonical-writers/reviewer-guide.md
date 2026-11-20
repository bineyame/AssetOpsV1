# DS1b reviewer guide (rev 2: handshake round 1 folded in)

For the fresh Reviewer: first at the handshake (read `spec.md`, `rulings.md` and this guide; put questions in
`handshake.md`), then at the review of the built unit. Depth: discovery (W5), because the unit writes money records.

## What to check first

1. **Base.** The branch starts after `2a` merged, and imports `assetops_contracts.canonical`; nothing is copied from
   it.
2. **Scope.** `git diff --stat main...HEAD` shows only the following, plus the finish bookkeeping:
   - `simulator/assetops_simulator/world/records.py`;
   - `simulator/assetops_simulator/world/leaves.py` (docstring only);
   - `simulator/assetops_simulator/world/__init__.py` (docstring);
   - `tools/world_history.py`;
   - `simulator/tests/world/test_records.py`;
   - `simulator/tests/world/golden/records_v1.json`;
   - `simulator/tests/world/conftest.py` (docstring and help text only);
   - the packet.
3. **History untouched.** `history.json` and `golden/history_v1.json` are unchanged.

## Done means

- Spec §6's five questions are each answered yes, with output.
- `PASS_THROUGH` and `ACTUAL_WRITERS` equal spec §2's tables.
- The unwritten counts are in the packet.

## Probes

- **P1 Inputs only.** Grep `records.py` for `oracle`, `checks`, `expect` and `derived`: nothing. It reads the view
  and the generated history only.
- **P2 To the cent.** Pick Kobo October and Thika September. Recompute each EXPENSE, ADJUSTMENT and BUDGET_LINE by
  hand from the view and `history.json`.
- **P3 Own lines only.** No BUDGET_LINE `kwh_2200_2400` at Embakasi or Kasarani, and no `delivered_kwh` or
  `necessary_l` at the mini-grid Sites; their plan fields are listed `NOT_OWN_LINE`. T9 checks this against
  `missing-records.json`, independently of the rule.
- **P3b Estimates.** Kisiwa October `om`, Thika October `maint` and Kasarani October `maintenance` are not written,
  and are listed `ESTIMATED_NOT_RECEIVED`.
- **P4 No totals.** No BUDGET_LINE names `contribution`, `revenue`, `energy_cost`, `total` or any other node.
- **P5 Zero handling.** An actual `liability` of 0 gives no row (`ZERO_NO_ROW`). Thika's plan `liability` of 0 gives a
  `0.00` BUDGET_LINE. An `om` of 0, if one occurs, gives a 0.00 row.
- **P6 Determinism.** Run the CLI twice yourself and compare the bytes with `cmp`.
- **P7 Labels.** Every batch's provenance is `source-emulated`, and no output holds `RECORDED` or a stronger
  provenance (T1).
- **P8 Merge gate.** `T2` is on `main` before DS1b merges.

## Class sweeps (W6)

- If one mapping row is wrong, recheck all of spec §2.1 and §2.2 against the manifest. T3 is the check for this, so
  confirm that it derives the tables rather than copying them.
- If one honesty case slips (an estimate, a fallback or a label), sweep all three over every Site and month.

## Risks to keep in view

- `3A3` and `DS2` will add customer-level records for the same months. Their totals must reconcile with these month
  lines, or one of them must replace the other. Note this in the review; it is not a DS1b defect.
