# SR-4c and SR-4 fix round review (fresh Claude reviewer, 2026-11-12)

Branch `task/SR-4-site-range`, head `ebef46a3a`. Scope: branch-only commits after `59bccda4d` (77924b3ff, de0375733, 91b58baab, e885670f4, 1a665b968, b6d7124fe, 582019b0e, 286dd3237, ebef46a3a). The main commits pulled in by merges (rev 9-10d, compose, host harness, VPS tools) are out of scope. 4a/4b are reviewed separately.

Judged against: rev 8 §8.1-8.3, rev 10b.4, 10c, 10d.1-10d.3; D-SR.1-8, 39-44; owner principle (range = telemetry and its consequences, configuration facts not ranged).

## Verdict: ACCEPT WITH NOTES

No High or Medium finding. Three Lows, none blocking.

## Checks run (on ebef46a3a, by me)

- `npx tsc --noEmit`: exit 0, clean.
- vitest, every test file touched by the in-scope commits plus `siteRangeCarry` and `ui/sharedRange`, in 5 batches:
  - batch 1 (rangeLink, shell sharedRange, siteRangeTags, siteEvidenceScreen, s5SiteWindowOverview, s404SiteFindingIndex, globalIncidents, globalMaintenance): 8 files, 243/243 passed.
  - batch 2 (coldDepth, coldFindingIndex, coldHealthDepth, coldScenarios, evAssessmentRoutes, evDepth, evEnergy, evHealthDepth): 8 files, 200/200.
  - batch 3 (evScenarios, evSiteMoneyRoutes, miniBackupRoutes, miniDecisions, miniFuelRoutes, siteWorkCases, w1f4ChangesWorkStructure, evFoundation): 8 files, 184/184.
  - batch 4 (operatorSiteTabs, siteDetailRoute, siteDetailScreen, siteFoundationRoute, siteOverviewScreen, t028Screens, coldFoundation, coldRoutes): 8 files, 252/252.
  - batch 5 (coldSiteViews, miniBackupRoutes again, globalPreventive, operationalRecords, siteRangeCarry, ui sharedRange): 6 files, 141/141.
- check-all: not run (as instructed; 19/19 reported on head by the builder, coordinator runs it centrally).
- Not run: the Postgres/demo (f) checks (Cold/EV on a range with no event, EV `/ev/financials` fingerprint), still pending as the packet says; `layout-evidence.mjs` (not run, no Chrome/serve in this review).

## What I verified

**Tags are honest.**
- "Range not used" is declared only on N pages: mini-grid Health (`SiteHealthFrames.tsx:109`, server clock, until SR-6); mini-grid Financials overview + assumptions (`SiteAnalyticsFrames.tsx:1584`, gated on `mini`; Scenarios returns earlier, so it is not tagged); every Prices page (`SitePricesFrame.tsx:158`); every Foundation view, all types (`SiteFoundationFrame.tsx:75`), Foundation changes and change (`SiteAnalyticsFrames.tsx:2169/2200`); Assets list and battery page (`SiteHealthFrames.tsx:145/194`, D-SR.43); Cold financial assumptions (`SiteAnalyticsFrames.tsx:1515`) and EV `/ev/financial-assumptions` (`evSiteRoutes.tsx:109`) (D-SR.44).
- No R page declares "not used": Cold/EV Health, Cold/EV Financials overview, EV `/ev/financials`, Scenarios, Findings, Work and the Evidence ledger keep "All pages" (`siteRangeTags.test.tsx` pins EV financials as FOLLOWS).
- D pages declare a span: Renewable when it reads less than the range, Service/Backup/Fuel their hour's day (`MiniPerformance.tsx:441-459`, D-SR.42a), plus FocusPicker pages as before.
- Evidence "All dates, not only the date range" sits under Rejected records and under "How each limit is set" (only when a declaration loaded) (`SiteEvidence.tsx:295-300, 659-662`), matching D-SR.7 until SR-12a/b.
- Spoken names: "the present state / the current settings / the prices valid now" (`SharedRangeBar.tsx:66-70`, D-SR.42b).

**The 26 D-SR.40 updates** (old vs new compared, 286dd3237 plus the e885670f4 bits they build on). Count matches 10d.1 rows 1-12: s404 4, coldScenarios 1, coldFindingIndex 1, w1f4 2, siteWorkCases 2, evDepth 2, evEnergy 1, evHealthDepth 2, evScenarios 1, evAssessmentRoutes 3, evSiteMoneyRoutes 2, miniDecisions 1, miniBackup 1, miniFuel 1, globalIncidents 1, globalMaintenance 1 = 26. Each asserts the new behaviour, mostly by exact href or exact request rather than `rangeless` alone:
- R347 group: every file asserts both cases (valid address range carried exactly as the bar's day form; reversed or one-sided carries none). Purpose kept.
- Spy rows (evHealthDepth, miniDecisions): `toHaveBeenCalledWith` the exact `entryRange()` from/to.
- siteWorkCases counts: exact `action-index`/incidents/maintenance count requests with the range, plus an invalid-address case that reads nothing.
- Backup/Fuel "two hours": moved out of the `it.each` table into its own `it` (not deleted); asserts a 1-hour read at 09:00Z (12:00 EAT) and the tag "Showing 6 Oct of the range"; the refused frame stays pinned by the reversed and unprovable cases.
- No assertion was weakened to pass. The only loosenings are the ones the rulings allow: the `/^\/sites(\/|\?|$)/` link-shape regex in `evDepth.test.tsx:233` (the Sites crumb now carries a query) and R280's tab lookup by range-less pathname (`evAssessmentRoutes.test.tsx:1011`).
- `evFoundation.test.tsx` is byte-identical to 59bccda4d (row 14 "stays as written").

**D-SR.41 code.**
- (a) `sharedRange.ts:126-127` compares raw instants before rounding; unit cases for reversed, equal (invalid) and 1-hour (valid) in `shell/__tests__/sharedRange.test.tsx`.
- (b) "Open with the default date range" in `ColdDepthRefusal.tsx:71` and `EvAvailability.tsx:182`; no other copy of the old text remains in `src`. `evDepth.test.tsx:339` compares the exact href. `coldDepth` pins the valid-range href and the reversed case.
- (c) Proven, not re-pinned: `siteWorkCases` narrow_mock now compares the raw requests (`requests` not `rangeless(requests)`) to `/work/maintenance?from=<entry.from>&to=<entry.to>&limit=5`, and passes. No code change was needed; the old failure was a one-sided `rangeless`.

**Other.**
- Ratchet (D-SR.42c): `frontend-hardwiring-baseline.json` changes only `SiteAnalyticsFrames` cmp 27→26 and lit 31→30, plus the matching totals.
- EV generic Financials redirect (`SiteAnalyticsFrames.tsx:1526-1531`) keeps the query.
- `withRange` double-`known_at` fix (`sharedRange.ts:157-165`) is pinned in `rangeLink.test.tsx`.
- No stray files: the branch-only commits touch only `frontend/src`, the baseline JSON and `.agent/SR-4-packet.md`. The untracked `frontend/node_modules` is the lane symlink and is not committed.

## Findings

**L1 (Low, labelling).** `frontend/src/shell/SharedRangeBar.tsx:58` and `frontend/src/shell/SiteHealthFrames.tsx:108` cite R718/R719 but carry no `MOCK DEVIATION` label. The build sheet (line 4805) records them as "MOCK DEVIATION R718/R719" (v71 Change 0b shows only "All pages"). The same applies to the transient Evidence "All dates" line (`SiteEvidence.tsx:69`), which v69 does not show.
- Why it matters: the standing rule is that a departure from the mock is labelled MOCK DEVIATION in code.
- Fix: write "MOCK DEVIATION R718/R719" in the `FOCUS_INSIDE` docblock, and a one-line D-SR.7 deviation note at `PANEL_ALL_DATES`.

**L2 (Low, side effect not ruled; stale comment).** Mini Scenarios no longer writes the server's returned window into the address. In `frontend/src/sites/MiniScenarios.tsx:329-334` the S15 adoption runs only when the address has no from/to/known_at. After SR-4 the safety net always supplies from/to, so adoption never runs in the app. The first read's effective `known_at` cutoff is no longer in the address, and a reload reads under a later cutoff.
- What still works: cursor pages carry the body's bound. The creation-time bounds are fixed by the range, so the practical drift is small.
- What is wrong: D-SR.40 row 8 rules only the request ("the read receives the shared range's from/to"). `miniDecisions.test.tsx:309-311` now pins "no adoption" as new behaviour. The file header (`MiniScenarios.tsx:4-7`, "The first request omits both bounds … carries the returned from/to/known_at in its address … reload") is now false for in-app use.
- Fix: update the header comment. Ask the Architect to confirm, in one line, that S15's cutoff pin yields to the shared range (or that `known_at` alone should still be adopted).

**L3 (Low, ruling reading to confirm).** For D-SR.42(d), `frontend/src/ui/sharedRange.ts:160` returns a target that names `from` or `to` exactly as written, with no address `known_at` added. `rangeLink.test.tsx:67-72` pins that (`?from=A&to=B` stays bare of the address `known_at`).
- The conflict: 10d.2(d) says "own from/to/known_at win per key; the address known_at is added only when the target names none". That can be read as adding the address `known_at` to a from/to-only target.
- Impact today is small: Cold/EV frame searches pass their own `known_at`. The packet labels the reading.
- Fix: the Architect confirms the reading, or `withRange` adds the address `known_at` when the target names from/to but no `known_at`.

## Residual risks not in the packet

- On Service, Backup and Fuel the hour bar's FocusPicker and the new `WindowSpan` both declare into the single focus slot (`MiniPerformance.tsx:1037` and `:1311/1636/1983`). Today both declare the same day, so the tag is right, but two writers on one slot depend on effect order. When SR-10/SR-11 change one of them, keep only one declarer.
- The longer tags ("Range not used · prices valid now") were not checked at narrow width. The bar's short form was not captured, and layout evidence was not run (the packet says "captures: none", per rev 8 §8.3; the UQ-FI or coordinator recapture should include a narrow viewport).
- The (f) DB checks are still pending, as the packet states.
