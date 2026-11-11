# SR-2b packet: Site pages onto the shared range (PARTIAL), FocusPicker, day=

Branch `task/SR-2b-site-pages` (wt `AssetOpsV1-sr2b`, from main `bfb2376f5`). Commits `282116e9b` (step 1),
`0218982ce` (step 2), step 3 (pin test), this packet. Spec: proposal 2026-11-10 "Item 12.5" SR.3/SR.4 rows SR-2;
D-UI.2; v71 `portfolio-tabs.html` Change 0b. Every commit leaves the screen honest.

## Outcome: PARTIAL (context budget). Never untrue on screen at any commit.

### Done
- `shell/FocusPicker.tsx` (guard-exempt): the one day picker. `min`/`max` = the shared range; line
  "Day shown: 24 Oct (inside 20 Oct – 26 Oct)" or "24 Oct is outside the date range (...), so this page does not use
  the range." with a "Show 24 Oct" button that widens the range (`widenToDay`, capped at 31 days).
- `shell/rangeFocus.tsx`: the page declares the day it shows (`useDeclareRangeFocus`, via FocusPicker); provider in
  `OperatorShellLayout`. `SharedRangeBar` then tags "Day shown: 24 Oct" or "Showing 24 Oct · range not used", the
  button reads "Date range for the other pages: ... This page shows one day of it / ... outside this range; the range
  is not used here". **Closes the residual:** a Kobo/Kisiwa day board with from/to in the address no longer claims
  "All pages".
- `sharedRange.ts`: `focusDayOf` (`day`, else legacy `date`), `withFocusDay`, `dayInRange`, `widenToDay`.
- Kobo/Kisiwa board (`SiteOverview`, `SiteWindowOverview`): the address names `day=`; an old `date=` link reads the
  same day and is rewritten to `day=` (replace). The overview read still sends `date=` (byte-identical). Previous/Next
  day links keep the shared range and `known_at`.
- FocusPicker replaces the day inputs of: claim limit (`EvidenceClaimLimit`), Dispatch (`PerformanceDispatch`),
  Service/hour pages' day (`MiniHourBar`), Renewable first day (`MiniPeriodBar`; declares its day only for a one-day
  period; several days are the address range, which the bar names truthfully).
- Guard `$pending`: removed SiteWindowOverview, EvidenceClaimLimit, PerformanceDispatch, MiniPerformance.
- `sr2RequestUrls.test.tsx`: Site requests pinned for Kobo `date=` board, Kisiwa `date=` board, Cold whole day, Cold
  analysed period, EV whole day, Kisiwa Findings (story nights), Kisiwa Service hour. Expected strings recorded by
  running the test against main's page sources (`git checkout bfb2376f5 -- <sources>`, restored after); the branch
  matches exactly. Limit: the stub answers 503, so each board stops at its first read; the outcome-board request
  itself is not reached (it is built from the served day / the same window, unchanged code).

### NOT done (resume here)
1. Range forms still in `$pending`: `LedgerSiteEvidence` (2), `MiniScenarios` (2), `SiteFindingIndex` (2),
   `SiteWorkActions` (WindowForm 2 + DomainWorkWindow 2 at ~812/828), `siteWorkCases` (2). Each already writes
   from/to instants into the address, so removing the form and reading the address keeps requests identical. A
   no-range state must point to the top bar ("Choose the days in the date range at the top"), not to a removed form.
   Tests asserting the forms (`data-site-work-window`, `data-cold-work-window-*`, `data-scenarios-window-*`,
   `site-findings-window`) need rewriting to drive the address.
2. Renewable/Service `date=` in `miniDepthClient.ts` (334, 358): read `focusDayOf` and rewrite `date=` -> `day=`.
3. One default (R338/S17), Work "Last 7 days, including today" preset, "Open now" line, register rows R338/S17.
4. Cold/EV: "No event in 2-8 Nov" wording via `analysed_periods`/`shown_period` (PB-1a merged; PB-1b in review) -
   not read yet; backend untouched.
5. Then empty `$pending` (and drop the ratchet branch or keep it empty).

## Known deviations (MOCK DEVIATION, in `FocusPicker.tsx`)
- SR-2-1: a `day` outside the range is still the day shown (said in words, "Show 24 Oct" offered), not the range's
  last day: keeps every old `date=` story link reading the same day and request.
- SR-2-2: a range with no `day` shows the read's default day, not the range's last day (request unchanged).
- Site-local days: the bar writes UTC-midnight instants; Site pages read them as given (requests identical). The
  Renewable/Service day compared with the range is the Site-local day.

## Checks
- vitest, one file at a time: `s5SiteWindowOverview` 64/64 (4 address asserts moved `date=` -> `day=` per spec, one
  new SR-2 case: inside/outside tag, widen, request unchanged); `sharedRange` 22/22; `sr2RequestUrls` 10/10;
  `evidenceClaimLimit` 50/50; `performanceDispatch` 44/44; `miniRenewableRoutes` 18/18; `miniServiceRoutes` 16/16;
  `miniFuelNights` 8/8.
- `tsc --noEmit`: clean.
- `tools\check-architecture.ps1` (ASSETOPS_GUARD_PYTHON = plan2 .venv): see the final report / commit.
- Not run (brief): full suites, captures, layout evidence.

## Review focus
- Bar wording on a one-day board ("Day shown" / "range not used"); the `date=` -> `day=` rewrite on the board.
- The range modules live in `frontend/src/ui/` (`sharedRange.ts`, `FocusPicker.tsx`, `rangeFocus.tsx`): the Site
  substrate may not import `shell/` (`site-substrate.ps1` failed the first architecture run). `shell/sharedRange.ts`
  re-exports; the guard's FocusPicker exemption moved to `ui/FocusPicker.tsx` (still one file). Where this packet
  says `shell/FocusPicker.tsx` / `shell/rangeFocus.tsx`, read `ui/`.
- Architecture check after the move: "Architecture check passed." Post-move reruns: tsc clean, sharedRange 22/22,
  sr2RequestUrls 10/10, performanceDispatch 44/44.
