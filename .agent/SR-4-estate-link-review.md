# SR-4 estate/Site Work link test repair review (987018db0)

Verdict: ACCEPT WITH NOTES

Checks run: the 9 named files under vitest: 9 files, 344 tests, all passed. `tsc --noEmit` exit 0. Test files only; no product code changed.

Per-assertion: the 25 changes are exact carried-href pins (ranged(...) helpers or literal triples) that match D-SR.2, D-SR.42(d) and D-SR.57. Links with their own window (COLD_LINK, first.links.evidence) stay unchanged, so the own-window-wins rule is pinned rather than loosened. The `a[href^=...]` change in estatePortfolio is broader, so it catches more.

Overrides:
- R339 mini-grid bare tabs: the new assertion pins the exact triple on every tab (stronger than the old `not.toContain("known_at")`). Correct under D-SR.2.
- R350 cold `/plan` and `/history`: only the onward `[data-action-open-verification]` link gained from/to, in the address's order, each key once. The page is still "not served", and no read is re-cut. This is a link-only carry, consistent with D-SR.64 (record reads use only known_at; the range lives in the address for onward links). Correct.
- ruling 71 cold case-row: the server path is kept and the range is appended. Correct.

Notes (none block):
1. estateFinancials: `not.toContain(FROM)` became "each of from/to/known_at appears at most once per link". Zero occurrences also passes, so it no longer proves the range is carried. The explicit `ranged(...)` pins on the site/source links cover it, but the loop is a weaker no-duplicates check, not a strengthening. Consider asserting `from` count === 1 for Site links.
2. The `ranged` helpers in siteWorkActions and estatePortfolio (overview_href) branch on `includes("from")`. This mirrors the product rule and makes the expectation data-dependent. It is acceptable because the fixtures are fixed, but literals would be more exact.
3. estateRoots `ranged` always appends WINDOW. It is correct only for hrefs without their own window, which holds for the fixtures that use it.
