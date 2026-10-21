# W3-03 pending rulings

## P-0b-1 — B3 clean fixture: cold `normal` makes no POTENTIAL_PRODUCT_EXPOSURE line (run 0b, stopped variant)

Spec: closure 4 B3 names cold `normal` (via `mixed_replay` mechanics) and requires "cold `POTENTIAL_PRODUCT_EXPOSURE`
UNPRICED" in the clean four-Site fixture, plus F/E/M COMPLETE.

Producer step: `test_w303_portfolio_fixture_postgres.py::build_portfolio_fixture` — `opened("normal", cold_chain)`,
`run(cold)` (W2-03 assessment worker), then EV x2, tariffs, money, P01 PowerSite v1-v3, `rig.run()`; frozen read
`2026-10-30T09:03:00Z` (= PowerSite `runner.now + 1 min`); request `[2026-10-06,2026-10-07)`, no `known_at`.

Actual public read (cold `normal`):
- `/findings`, `/evidence`, `/financials`: `CURRENT`, `coverage.state=COMPLETE`, all four Sites `CURRENT`.
- `/findings` rows: only KOBO-001 (W1 PRICED). **No COLD-LAB-001 Finding.**
- `/financials` rows: KOBO-001 `CANDIDATE_OPERATING_COST_EXPOSURE ELIGIBLE`; EV-LAB-001/002 `GROSS_TARIFF_SCENARIO
  ELIGIBLE` (group `COMPARABLE`, 2 lines). **No cold line**; group `POTENTIAL_PRODUCT_EXPOSURE` state
  `UNKNOWN_COVERAGE`, 0 lines, while root `coverage.state` is `COMPLETE` (under closure 5 S4 this cold unit is `U`,
  so Portfolio M would be PARTIAL, not COMPLETE).
- `/evidence`: COLD-LAB-001 rows backup/cooling/temperature FULL, exposure NONE (window 19:00-20:05Z).
- Cold coverage item: selection `…017c`, watermark real DB time, job SETTLED, freshness RECENT.

Mismatched assertion: "cold POTENTIAL_PRODUCT_EXPOSURE UNPRICED" (and M COMPLETE once Portfolio reduces it).

Probes (not committed; evidence only, same DB, same composition):
- cold `excursion` without drain: two cold Findings (`UNPRICED` in `/findings`), still no cold line,
  `POTENTIAL_PRODUCT_EXPOSURE` still `UNKNOWN_COVERAGE`.
- cold `excursion` **plus the W2-04 cold consequence worker** (`test_w204_cold_consequence.drain(cold)`, the pattern of
  `test_w301_provenance_dto_postgres.py::_cold`): one cold line `POTENTIAL_PRODUCT_EXPOSURE UNPRICED`, amount null,
  `finding_revision_id` = a selected cold Finding revision; group `INELIGIBLE` (1 line); all three roots
  `CURRENT/COMPLETE`; every other assertion in the test still passes (1 passed, 83 s).

Question: should the clean fixture use cold `excursion` + W2-04 drain (builder already takes
`cold_case="excursion", cold_drain=True`), or another cold producer? Once ruled, the held assertions to add are:

```python
(cold_line,) = lines[fx.site_ids["COLD-LAB-001"]]
cold_revisions = {r["finding_revision_id"] for r in rows[fx.site_ids["COLD-LAB-001"]]}
assert (cold_line["category"], cold_line["eligibility"]) == ("POTENTIAL_PRODUCT_EXPOSURE", "UNPRICED")
assert cold_line["amount"] is None and cold_line["finding_revision_id"] in cold_revisions
assert len({line["category"] for line in financials["rows"]}) == 3
```
