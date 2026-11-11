# SR-2 + SR-3 packet: pages on the shared range (PARTIAL), guard

Branch `task/SR-2-pages-on-range` (wt `AssetOpsV1-sr2`, from main `66a38d849`). Commits `61bb2060f` (step 1),
`aef240f15` (estate + Work pages, URL pins, guard). Spec: proposal 2026-11-10 "Item 12.5" SR.3/SR.4 rows SR-2, SR-3;
D-UI.2; v71 `portfolio-tabs.html` Change 0b.

## Outcome: PARTIAL. Never untrue on screen at any commit.

### Step 1 (61bb2060f): SR-1 review notes closed
- Medium: `readsSharedRange(pathname)` (`shell/sharedRange.ts`) lists the pages whose content follows the range
  (estate roots + tabs/lenses, Incidents, Maintenance, Preventive, Operational records). Only there does the bar say
  "All pages". Elsewhere (Site directory, every Site page incl. Kobo/Kisiwa day boards and Cold/EV analysed periods,
  record pages) the tag reads "Not used on this page" (kept on phones), the button is named "Date range for the other
  pages: ... This page shows its own dates, not this range", and the as-of label says "· other pages".
- Low: picker cutoff keeps seconds (`slice(0,19)`; a browser's `.000` is stripped), so Apply leaves `known_at` as is.
- Low: `rememberRange` runs only on Apply; a range arriving in an address is never remembered.

### SR-2 done (aef240f15)
- Findings (all lenses), Actions, Evidence, Financials: `EstateDateBar` removed (deleted from `estateShared.tsx`);
  each shows `EstateCutoffLine` like the Portfolio. No page shows two date controls any more.
- Incidents, Maintenance, Preventive, Operational records: `ControlBar` keeps `Reload` only (a labelled group).
- Requests: page query parsing and all clients unchanged (`git diff main -- estateClient.ts globalWorkClient.ts
  frontend/src/sites` empty). `shell/__tests__/sr2RequestUrls.test.tsx` opens story-link addresses in the whole App
  with the real clients and pins the exact fetch URLs (Portfolio `...&limit=50` + outcome-summary; Findings findings +
  scope + outcome-summary; Maintenance `...&limit=5`) and that no other estate/Work read is made.

### SR-2 NOT done (resume here)
- Site page forms, still listed in the guard's `$pending` ratchet: `EvidenceClaimLimit`, `LedgerSiteEvidence`,
  `MiniPerformance` (range + day), `MiniScenarios`, `PerformanceDispatch` (day), `SiteFindingIndex`,
  `SiteWindowOverview`, `SiteWorkActions` (2 range + 2 inputs at ~818/828, check whether data entry), `siteWorkCases`;
  plus `miniDepthClient.ts` Renewable/Service (`date=`), Cold `SelectedWindowBar`, EV `WindowBar`, Kobo/Kisiwa `date`.
- `FocusPicker` (`day`/`hour`/`event`), `date=` -> `day=` redirect, Site-local days, one default for Work (R338/S17
  rows), "Open now" line, Cold/EV latest event inside the range: not built. Site board URL pins need a Site-detail
  fixture per type in the URL test (the stubbed 503 stops Site pages at `/api/sites/{code}`).
- When a Site page moves: add it to `RANGE_PAGES`, drop its `$pending` entry, add its story link to the URL test.

## SR-3
- `tools/checks/page-range-forms.ps1` (registered "One shared date range"): fails a non-test `.tsx` with
  `type="date"` or a `datetime-local` named `from`/`to`; exempt `shell/SharedRangeBar.tsx`, `shell/FocusPicker.tsx`;
  `$pending` counts only shrink (growth, a zero entry, or a missing file fail). Built-in self-test (page form fails,
  exempt passes, named datetime-local counts, ratchet bites). Non-vacuous: main's `estateShared.tsx` and
  `globalWorkParts.tsx` each fail it ("renders its own date range form (2 date inputs)").
- Rail check: SR-1's `navigation-truthfulness.ps1` `search={railSearch}` rule + two rail fixtures (unchanged).
- Captures re-baseline: not in scope (brief: no captures).

## Checks
- vitest, one file at a time: `sharedRange` 21/21; `sr2RequestUrls` 3/3; `estateRoots` 23/23, `estateEvidence`
  17/17, `estateFinancials` 11/11, `estatePortfolio` 85/85; `globalIncidents`, `globalMaintenance`,
  `globalPreventive`, `operationalRecords` all passing (exit 0).
- Rail-href assertions in `globalIncidents`/`globalMaintenance` App tests were failing on main since SR-1 (rail carries
  the range); now compare the path part.
- `tsc --noEmit`: clean. `tools\check-architecture.ps1` (ASSETOPS_GUARD_PYTHON = plan2 .venv) on the tree of
  `aef240f15`: "Architecture check passed."
- Not run: full suites, layout evidence, captures (brief).

## Known deviations / risks
- Work pages without a range still use R338's default and the bar says "This page's own dates" (honest; SR-2 default
  change pending). Work tests asserting the old form were rewritten to assert its absence.
- Site pages still have their own forms under the bar; the bar says "Not used on this page" there.
  (Superseded by the fix round below.)

## Fix round (review Medium + Low)
- Medium: `readsSharedRange(pathname, params?)` in `sharedRange.ts` now also counts `/sites/:id...` and
  `/performance/*` as range-using when the address carries from/to (readers: SiteEvidence, coldWindowFromParams,
  miniDepthClient, EvFoundationViews, MiniOpportunity, SiteAnalyticsFrames). Without from/to those pages show their own
  day and make no claim. Record pages and the Site directory stay "Not used on this page".
- Low: with no range in the address the bar shows "This page's own dates" with no tag (was "All pages").
- Tests (`sharedRange.test.tsx`): per route class label (estate, Site story link, Site page with no range, record
  page) plus `readsSharedRange` with params for demo story link shapes.
- Checks: vitest sharedRange 22 pass, sr2RequestUrls 3 pass, tsc clean, check-architecture (see commit message).
- Known limit: a Site page type that ignores from/to still reads as range-using when its address carries one.
