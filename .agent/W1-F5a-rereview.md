# W1-F5a re-review

Verdict: ACCEPT

Checked at 2692ece6. tsc --noEmit exit 0. vitest src/sites: 20 files, 740 passed (includes siteHealthBoundary and battery tests). Full suite (1992) not rerun; cited from the packet. Captures reviewed at 1440 and 390.

1. H1 fixed. Health shows 9 rows, one per gateway, each with name plus "N device(s)", a short Status ("Current · 1 min ago", "Stale · 1 min", "Never received", "Disabled"), and a Quality Badge. Attention rows come first, disabled last. The summary is one line. Device rows, queue and storage moved to a Technical details table (HealthReportedDetail) and the selected-gateway view (queue added). KOBO-001 stays tall with 9 honest rows; no redundant text remains.
2. M2 fixed. Unknown-not-normal-nor-faulty appears once on Health and once on the battery page (new test counts occurrences). The "Unknown (not configured)" and repeated sentences were removed.
3. Assertions not weakened. Status, quality, device-contact, queue and storage assertions were re-pointed to status/quality cells, data-health-reported rows, and the selected view; none deleted. New tests cover 9 rows, ordering, zero device rows in the table, selected-gateway stale limit, and the single sentence.
4. No regressions seen: one disclosure per panel, no raw IDs beyond the labelled gateway refs, no contradictions, rows are short at 390.

Low (non-blocking):
- L1. At 390 the gateway table scrolls horizontally, so Status and Quality are off-screen without a sideways scroll; only the Source column is visible. This is the existing DataTable pattern, but the key information is hidden on the first view.
- L2. The summary and Technical details say "stale" for s7-stale-cadence at 1 min in the capture, while the test fixture says 10 min; this is only a fixture-clock difference, not a defect.
