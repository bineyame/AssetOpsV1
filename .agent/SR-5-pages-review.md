# SR-5 pages review (SR-5b, SR-5e, SR-5c, SR-5d, D-SR.77)

Reviewer: fresh Claude (Opus 5.5), independent of the builder. 2026-11-13.
Branch `task/SR-5-pages`, worktree `/opt/assetecon/AssetOpsV1-sr5`, head `c6143749f`, base `461ef7a60` (merge-base with main).
Spec: rev 9 §9.4, revisions 10-10e, D-SR.9-12/28-30/50/56/66/77, packet `.agent/SR-5-packet.md`.

## Verdict: ACCEPT WITH NOTES

No High or Medium findings. Five Low findings below. Each can be fixed on the branch in a small Sonnet round. None blocks merge.

## What was checked, and what it showed

- **Day states are worded honestly** (`SiteRangeOverview.tsx:60-74`).
  - FINDINGS reads "n findings", and CLEAR reads "Checked: nothing to report".
  - When a retired Finding is present, the row reads "Checked: no current findings · N finding(s) no longer supported", and a FINDINGS row takes the same suffix (D-SR.50).
  - NOT_EXPECTED shows the server's `note` in place of "Before readings began" (D-SR.56).
  - NO_READINGS, READINGS_CONFLICT, NOT_ENOUGH_READINGS and NOT_ANALYSED use the D-E5.46 `dayGapWords`.
  - STILL_PROCESSING uses the Portfolio's "Still processing".
  - The whole-range empty state gives "No readings received in this date range", with the tiles shown as "–" and the days still listed.
  - All of the above is pinned in `siteRangeOverview.test.tsx`.
- **Figures come from the server body.**
  - Tiles, status line, partial label, quantity, day money and totals are all read from the body (`coverage.days`, `money.card/partial/quantity`, `dispatch.*`, `days[]`).
  - The page adds nothing up. Money is never summed client-side, so it is never summed across currencies. Day money comes from the server's `money_state`, and CURRENCY_MIXED and OVERLAPPING get the Portfolio's "not added" words.
  - The one client-side derivation is the spec's own empty-range rule (`rangeHasNoReadings`).
- **Drill-in.**
  - "Open day" and the strip cells are `RangeLink`s to `?day=`, which carry `from`/`to`/`known_at` and drop `day`.
  - The drill-in makes no `range-overview` read.
  - "← Back to the whole range" goes to the same path with no `day`, and the range is carried. It is pinned for both the Overview and Dispatch.
  - Its place in the chip row (not above the heading) is a recorded placement reading (packet deviation 1).
- **404, 422 and 503 (D-SR.77 1).**
  - Only a 404 falls back to the one-day page, and the bar then names the day served ("Showing 9 Nov of the range"). This is pinned for the Overview and Dispatch.
  - On Financials, a 404 keeps "Assumptions in use", and the bar reads "Range not used · prices valid now".
  - A 503 (`SITE_RANGE_OVERVIEW_UNAVAILABLE` or `TEMPORARILY_UNAVAILABLE`) is retried 2/4/8 s, shows "Temporarily unavailable. Retrying…" and then "Still unavailable…", and never shows data. The client test proves 4 fetches.
  - A 422 shows "This date range can't be shown here" and never the one-day page.
- **The matrix is real.**
  - I ran a probe copy of the matrix test (deleted afterwards) to log every R row's requests. Every R row except one (L3) makes real ranged reads.
  - The only unranged reads are the two `knownUnranged` entries, and both are justified:
    - mini/EV `/evidence/rejections` → SR-12a;
    - mini `/financial-assumptions?valid_at=now` → "Prices valid now", SR-14 OUT, D-SR.39.
  - Route completeness works in both directions (`App.tsx` against the matrix).
- **Mutations the builder claims, re-run by me (each reverted with `git checkout`, worktree clean):**
  - removing `SiteOpportunityFrame`'s declaration fails `mini /opportunities/o1 (N)`;
  - dropping `rangeOverview` from the Performance route fails mini `/performance` and `/performance/dispatch` (R);
  - a wrong `to` in `useRangeOverview` fails mini `/`, `/performance`, `/performance/dispatch` and `/financials` (R).
- **Record pages from the first render (D-SR.77 2).**
  - The Opportunity, Action, mill/fuel Verification and fuel Finding frames call `useDeclareRangeNotUsed("own period")` before any read.
  - The N rows pass under the all-503 fixture, and `declaresOnLoad` is gone.
- **Money (SR-5d).**
  - The money block uses the card's `display_value` with the PARTIAL label ("… for 3 of 7 days analysed …") and the litres at stake.
  - It lists only the days that have money, each with "Open day" to the Overview drill-in with the range carried.
  - The price panel is headed "Prices valid now", the bar reads "All pages", and the frame keeps "prices valid now" for the assumptions and scenarios views.
- **Register.** R721, R722 and R723 are registered and the code labels match: `mock-deviation-labels.mjs` returned "OK 172 files". The row shape has a defect (L2).
- **Re-pins.**
  - `sr2RequestUrls`: SR-4b's `overview?date=` pins are replaced by `range-overview` pins, and Kobo/Kisiwa Dispatch pins were added.
  - `siteRangeTags`: the SR-4c Financials pin now reads "All pages".
  - `s5SiteWindowOverview` and `s502OverviewFindingList` run with no-`day` cases on a declared 404 client, so they pin the one-day fallback, and they say so.
  - All of these follow from the spec. Nothing was deleted.
- **Stray files.** None. The diff is 22 files, all on the slice. Main has moved 4 commits (`.agent` and backend tests only), with no frontend overlap.

## Findings

| # | Sev | Where | What | Why it matters | Fix |
|---|---|---|---|---|---|
| L1 | Low | `frontend/src/sites/rangeOverviewClient.ts:85-86`, `SiteRangeOverview.tsx:167` | `dispatch.days_requested` and `days_analysed` are typed `number`. The server sets them to `None` when `coverage.days` is null (`site_range.py:174-176`; `coverage.py:353` returns no days block on a day-count mismatch, for example with no grades provider). The "Days analysed" tile would then read "null of null". | It is a dishonest state on a client page. It is rare on the demo, which runs with day grades on. | Type them as `number \| null` and render with `known()` ("Not known yet"). Add one unit case. |
| L2 | Low | `.agent/mock-departure-register.md:696-698` | R721, R722 and R723 have 7 cells, but the table has 9: "Owning or resolving unit" and "Status" are missing. | The register table renders shifted, and the rows carry no "open until owner review" status, unlike R718 and R719. The guard does not check column count. | Append `\| SR-5b \| open until owner review \|` (and the same for SR-5c and SR-5d). |
| L3 | Low | `frontend/src/ui/rangeMatrix.ts:93`, `shell/__tests__/siteRangeMatrix.test.tsx:120-130` | `ev /financials/scenarios` is classified R ("computed over the range's telemetry"), but that address makes **no** request. The generic scenarios view renders "Scenarios are read for mini-grid sites only" (`SiteAnalyticsFrames.tsx` scenarios branch), and the R check passes vacuously because it never asks for at least one ranged read. | The matrix claims a range behaviour the page does not have. Any future R page that reads nothing would also pass. | In the R test, require at least one ranged data request, or a named `noReads` reason on the row. Reclassify the EV row (N "not offered here", or forward it to `/ev/financials/scenarios` as the overview does). The Architect picks the class. |
| L4 | Low | `frontend/src/sites/PerformanceDispatch.tsx:139-155`; register R722 | The "Dispatch by day" range view drops the Dispatch local-views chip row (the Analysis view switch). Analysis is reachable only from a drill-in day. R722 does not record this. | It is an undocumented mock departure on a layout the owner reviews against v69. | Add it to R722's "What is shown instead", or keep the chip row on the range view. |
| L5 | Low | `.agent/SR-5-packet.md` (Pages section) | The slice adds a day strip and a dense day table (layout-sensitive), but the packet has no `tools/layout-evidence.mjs` entry, not even "not run" with its blocking precondition. | It is a process gap: the layout at phone width and with a 31-day wrap is unverified by any record. | Record "layout-evidence: not run (needs Chrome, backend and dev server)" in the packet, or run it once the demo serve is up. |

Notes only, no change requested:
- **Finding list cutoff.** "Findings in this range" reads `finding-index` with no `known_at`, because that client has no `known_at`; this is pre-existing. On a historical address the list is at "now" while the tiles are at `known_at`.
- **Wording, preference.** The Actions tile note "Open · Awaiting verification N" is terse. "Not counted: day not analysed" also appears on a before-readings day.

## Checks run (Linux VPS, from `frontend/` with `npx vitest run <file>`)

- `siteRangeOverview` 19/19, `siteRangeMatrix` 94/94, `sr2RequestUrls` 23/23, `siteRangeTags` 11/11: 147 passed.
- `s5SiteWindowOverview` + `s502OverviewFindingList`: 106 passed.
- `performanceDispatch` + `siteFinancials`: 142 passed.
- 20 more Site-href files naming Kobo/Kisiwa Performance, Financials or a ranged address: 634 passed.
- `npx tsc --noEmit -p .`: exit 0.
- Guards run singly (lane rule, no check-all): `site-links-carry-range.ps1`, `page-range-forms.ps1` and `ui-primitives.ps1` all exit 0; `mock-deviation-labels.mjs` returned OK.

## Not verified

- **Not run on my side:**
  - check-all, which goes to the coordinator;
  - the full frontend suite and the production build (test-suite policy);
  - layout evidence (L5).
- **No live serve.** No page was opened against the demo DB, so the real-data wording of the strip and table is unseen.
- **The builder's 89-file Site-href run (2517/2518)** is cited, not re-run in full.
- **Residual risk:**
  - The WARM-1 `range-overview` warm entry is still pending (packet resume point 5). Until it lands, the first Overview, Dispatch or Financials open on an unwarmed range pays the cold read (estimated 1-4 s).
  - The real-data parity (`.agent/SR-5-parity.json`, on main) covers the body, not the page.
