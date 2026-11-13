# Review: task/SR-6-12a-pages (SR-6b Health range page + SR-12a Evidence rejections over the range)

Reviewer: fresh Claude reviewer (did not author). Diff `e8f2bdea5..bbe8cc6fa` (merge-base with main..HEAD), 24 files.
Spec: rev 10 §10.2, rev 10a (D-SR.19-23), 10b.4 (SR-12a), 10d.9 (D-SR.49); packets `.agent/SR-6-packet.md`, `.agent/SR-12a-packet.md`.

## Verdict: ACCEPT WITH NOTES

No High or Medium findings. Three Low notes, none blocking.

## What was checked

Health (SR-6b)
- Ruled words present and tested: status line from D-SR.49 Q1 ("Readings on 1 of 4 days · 3 days with no readings", the
  not-expected / not-reached-yet classes named only when non-zero); "Gateways in contact on every expected day: n of m";
  "Readings used for analysis" (day row) vs "Readings received" (source cells), never one name for both (Q3);
  READINGS_ONLY "Readings received; no status reports" (D-SR.20); AFTER_CUTOFF "Not reached yet" for gateway and source
  cells (Q4). No "In contact" wording is produced except from IN_CONTACT; READINGS_ONLY days read as partial tone, not contact.
- Summary classes: the page only renders the server's four counts. The test body sums 1+1+1+1 = 4 = days_requested;
  the sum is a server rule (SR-6a, already reviewed), not re-checked by the page.
- Battery: v69 condition panel renamed "Battery (current settings)" from the existing `/battery` read (Q5); source-health
  panel renamed "Contact now" with "Point in time: contact as of now, not over the date range." Both only under a range.
- Drill-in: `day=` requests `from=day&to=day+1` (pinned in `sr2RequestUrls`), bar declares `RangeSpan(day, day)`
  ("Showing 5 Nov of the range", pinned in `siteRangeTags`), "Back to the whole range" drops `day` and keeps from/to
  (test asserts the href), day heads stop linking in the drill-in. Range view declares nothing ("All pages"); SR-4c's
  `RangeNotUsed "shows now"` kept only when the address has no valid range.
- 503: `SITE_HEALTH_RANGE_UNAVAILABLE`/`TEMPORARILY_UNAVAILABLE` retried 2/4/8 s with "Temporarily unavailable. Retrying…",
  then "Still unavailable. Refresh to try again." (both tested); other refusals keep HTTP + code in `HealthGap`.
- R724 row added to `.agent/mock-departure-register.md` and cited in `SiteHealthRange.tsx` / `SiteHealthFrames.tsx`.

SR-12a
- Half-open `[from, to)` on batch `ingestion_batch.received_at` for rejections, conflicts (subset) and duplicates
  (`_RECEIVED_IN_WINDOW`, `postgres_evidence_ledger.py`); `site_window`'s call to `_rejection_rows` unchanged.
  Postgres test proves the `to` edge is excluded (packet also records a mutation run).
- Exactly one bound → 422 `INVALID_WINDOW` (both directions tested); reversed, empty and day-only also 422.
- Cutover order: `imported_scope(site_id)` runs before `_window_params`, so an awaiting-migration Site answers its gate
  first (commit a1ec625d9); `configuration-persistence` guard passes.
- "All dates" line removed from the rejections panel only; analytics keeps `PANEL_ALL_DATES` (tested both ways).
  Ledger page heading switches to "(received in this date range)".
- Tests are not vacuous: the no-DB route test records the window reaching the seam as instants; the file-backed test
  covers before/inside/`to`-edge/after; the Postgres test moves one batch two days later and checks each list.
- No stray files: diff holds source, tests, the register row and the two packets only.

## Findings

L1 (Low, failure path) `frontend/src/sites/SiteEvidence.tsx:208` with `:268` and the `Rejections` line.
When a range is set but the ranged rejections read fails, `rejectedCount` falls back to `evidence.rejection_count`,
which is the all-dates count (`read_model.py:272`, `len(evidence.rejections)`), and the line then says
"N records received in this date range were rejected". Wrong figure under a ranged label, only when the list read fails.
Fix: when `ranged && rejections === null`, show no count (or the plain "could not be read" line) instead of the fallback.

L2 (Low, comment) `frontend/src/sites/SiteEvidence.tsx:69` still says `/evidence/rejections` takes no date range.
Fix: name only `/analytics`.

L3 (Low, residual, not a packet defect) Layout evidence not run: the 31-column day tables rely on `DataTable`
scroll + sticky first column, unverified in a browser. The packet records it as not run with its reason, which is the
correct form. Run `tools/layout-evidence.mjs` (or capture in the walkthrough) at 31 days, desktop and phone width.

## Architect questions (view only; not blocking)
- Q7 recompute list: agree with the builder. `/evidence/rejections` has no recompute-job list (rejections, conflicts,
  duplicates only); the spec line reads as anticipating one. Nothing to filter now.
- Q8 two time bases: acceptable if each line names its basis. The list already says "received in this date range"; the
  ledger overview count ("in this period", source time) could say so too. Aligning the numbers would change S2 Q19.
- Q9 file path filtered: agree. Otherwise the generic page would list all dates with the "All dates" line removed.

## Checks run (this review, worktree /opt/assetecon/AssetOpsV1-sr6 at bbe8cc6fa)
- `pytest test_sr12a_rejections_range.py test_s2_rejection_placement.py test_sr6_health_range_route.py` (no DB): 44 passed, 3.5 s.
- `pytest test_sr12a_rejections_postgres.py` on `assetops_sr12a_test`: 1 passed, 0 skipped, 9.6 s.
- `npx tsc --noEmit`: clean.
- `npx vitest run` siteHealthRange, siteEvidenceScreen, s2LedgerEvidence, siteRangeTags, sr2RequestUrls: 5 files, 83 passed.
- Guards singly: configuration-persistence, site-links-carry-range: exit 0. check-all: for coordinator.
- Not rerun: the 88-file Site-href vitest set (packet: 2410 passed, 1 load timeout in untouched evEnergy, passes alone),
  `test_sr6_health_range_postgres.py`, production build, layout evidence.

## Residual risk
- The address range is passed raw to `/rejections` (as `/evidence` already is); a day-only `from`/`to` typed by hand
  gives 422 and "could not be read". Same as the existing overview read; the app writes instants.
- `RANGE_MATRIX` N→R for mini-grid Health is pending the SR-5 merge (second merger), as the packet names.
