# W2-04 re-review (r2) after Run 9 fix round, head c2da7779

## Verdict: ACCEPT (no High or Medium findings)

| Finding | Status | Evidence |
| --- | --- | --- |
| M1 unbound Affects | CLOSED | coldSiteViews.tsx:859 uses `CLOSED_SOURCE[row.label].affects`; undeclared inverter row keeps `Claim effect not assessed`. Test coldSiteViews.test.tsx:575-580 asserts Cooling / Backup / Temperature · cooling. Capture shows Transfer `Backup`, Loading `Temperature · cooling`. |
| M2 line-height | CLOSED | w2-cold-site.css unchanged for that rule (ruled as-is). |
| M3 stray `x` | CLOSED | file absent at head; removed in diff. |
| M4 null link | CLOSED | coldSiteViews.tsx ~1253 `No linked page for this item`, non-interactive; test asserts text, no anchor, old string absent. |
| M5 chip tones | CLOSED | COLD_TONE map (coldSiteViews.tsx:663-676) matches the ruled table; applied only to Contact, Quality, capability and evidence-strip chips. Unknown, No fact, None, Evidence unknown, Coverage, claim-level, provenance/lifecycle/origin/configuration badges get no class. CSS selectors and hex values at w2-cold-site.css:143-146 match the ruling exactly. `w2-cold-assessment.css` untouched. Captures: Full green, Limited and Evidence limited amber, Not declared amber, Good green, Unknown neutral, as in the mock. |
| L1 quantity copy | CLOSED | `quantityPhrase` strings exact; used in Exposure cell, card note (UNPRICED only) and Basis details; `boundText` removed. Test covers all three cases and asserts no `degC_min` / `Unknown bound`. Capture shows `at least 19 °C-minutes (upper bound unknown)`. |
| L2 non-primary role | CLOSED | `roleName` for exactly one accepted non-primary role; test asserts `Generator state`. |

## New decisions not covered by the ruling
- `Badge` gained an optional `className` prop (Badge.tsx). It is the minimal mechanism for the ruled classes; neutral output is unchanged. Low, no action.
- The multi-role `Other recorded roles` path is unreachable with current row roles and its Source-details enumeration is untested. Low, no action.

## Checks run
- `vitest run coldSiteViews.test.tsx`: 46/46 passed.
- `tools/check-all.ps1`: all 10 guards passed.
- Not run (as instructed): backend, host and full frontend suites; live DOM remeasurement.
