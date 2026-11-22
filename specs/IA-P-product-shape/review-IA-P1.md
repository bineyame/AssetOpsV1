# Review: IA-P1 (P1 the frame, P0 the long range, P2 the lists)

Discovery review (W5), round 1, 2026-11-22. Branch `task/IA-P1-frame-portfolio`, head `78b947376`, against `main...HEAD`
(merge base `902b908be`). Reviewer: fresh Claude, not the author.

## Summary (round 1)

- **Verdict: ACCEPT with findings fixed on the branch** (M1, M2 and M3; the Lows are optional).
- Frame (P1): the rail matches spec §2.1 in groups, order, labels and states. The aliases keep the range, and
  `/evidence` with `/evidence/records` draws the tab row. Verified in the browser.
- Long range (P0): `readWindow`/`capWindow` hold. The sweep covers the estate, mini depth, cold, EV and health families.
  R7 and R8 pass in the browser.
- Lists (P2): the model and component match §5.2. On a mixed fixture (mini-grid, cold, EV, MONITOR, under way, no ref)
  each row has 0 or 1 control, and the cold row with no window is text with "Detail not available yet". The EV windowed
  row links, mini-grid rows open `recommendation`, and 390 does not scroll sideways.
- M1: the State tiles (parts) are counted from the unfiltered store, so under a facet a part can exceed tile 1.
- M2: the Findings list states "No decision open" and a 0 tile while its Decisions read is in flight or refused.
- M3: `/evidence/records` refuses a valid 31-day range written in the day form. It shows in the gate's own screenshot,
  and gate R3 still passes.
- (a) Scan exemptions: justified. (b) Hard-wiring shrink: real removal, not a loosened check.

## Checks run (this review, same head)

| Check | Result |
|---|---|
| `tools/check-architecture.ps1` | passed (needs `ASSETOPS_GUARD_PYTHON` set to main's `.venv`; the worktree has none) |
| `tools/check-agent-workflow.ps1` | passed |
| `node tools/checks/missing-claim-scan.mjs` | passed: 44 tagged, 10 baselined, seed ceiling 16 |
| `node tools/checks/frontend-hardwiring.mjs` | passed: totals api 12, href 20, lit 69, cmp 50, code 3 |
| `navigation-truthfulness.ps1`, `navigation-rail-fixtures.ps1` | exit 0, exit 0 |
| vitest, 13 files (homeListModel, homeLists, iaRoutes, iaRouteMap, noRawRangeReads, rangePartNote, readWindow, sharedRange, estatePortfolio, estatePortfolioRoutes, operatorRailInventory, operationalRecords, sr2RequestUrls) | 266 passed, 1 failed: `sr2RequestUrls` SR-6b (an extra `/reading-uploads` request). This is UP-1 (`490c92fa0`) on main, not this branch: the diff has no `reading-uploads`. It matches the packet. |
| `tsc --noEmit` | clean |
| `vite build`, then `iap_gates.cjs` on preview :5573 | 29 of 29 pass, exit 0 (R1 to R8, L1 to L3, at 1440 and 390, light and dark, plus the menu) |
| Own browser probe: Decisions on a mixed-type fixture (scratch copy of `portfolio.json`) | see the summary; also confirmed M1 (below) |

I did not rerun the full suite or the plants; I relied on the packet's same-head runs (vitest 3 pre-existing failures,
check-all fast, 42 of 42).

## Findings

### M1 (Medium, acceptance gap): State tiles count the unfiltered store, not n
`frontend/src/ui/HomeList.tsx:126` passes `items` (unscoped, unfiltered) to `def.tiles`. Two tile definitions count
from it:
- `frontend/src/estate/homeLists.tsx:127`, the Decisions "Waiting for a choice" tile;
- `frontend/src/estate/homeLists.tsx:244-249`, the Actions per-`application_state` parts. Their sum is the whole store,
  not n.

Tile 1 is `model.n`, which counts after the filters. Probe: `/decisions?…&state=watching` shows **"Decisions 1" beside
"Waiting for a choice 6"**, a part larger than its whole.

Spec §5.2 says the Actions parts "sum to n", and n is the filtered count (IA-2b §3.1). This also falls in the W6 class
sweep "Any count beside a list that is not the list's length or the server's total", and it is not an honest number.

Fix: compute the parts from `model.rows`, the filtered rows, or pass that array to `tiles`. For the E0 `waitingTotal`
branch, use the server figure only when nothing is filtered or scoped, as tile 1 already does. Add a `homeLists.test`
case: a set facet makes the parts sum to tile 1.

### M2 (Medium): Findings "Its decision" claims "No decision open" while the Decisions read is pending or refused
`frontend/src/estate/homeLists.tsx:340-342`: `decided` is `[]` until the portfolio read has loaded, and also when it is
refused. The Findings list renders as soon as the findings read loads.

Every row then reads "No decision open", and the "Decision waiting for a choice" tile reads 0. That is a false statement
on a 503, and it flickers on every cold load because the two reads race.

Fix: while `decisions` is null, show the column and tile as loading, or hold the list. On a refusal, show "Not available
yet" in the column and tile, never "No decision open" or 0. Add a test in which the portfolio read is refused.

### M3 (Medium): the Records tab refuses a valid range in the day form, and gate R3 does not see it
The gate's own shot of `/evidence/records?from=2026-10-01&to=2026-10-31` (1 to 31 October) shows "Choose a valid date
range of at most 31 days.":
- `frontend/src/work/globalWorkClient.ts:807` accepts only the midnight-instant form (`validMidnight`). The bar and the
  estate pages accept the day form too (SR-1).
- The bug is old on main. This slice brings it into the IA frame: the alias keeps the query, so an old
  `/operational-records?from=YYYY-MM-DD…` bookmark now lands on a refusal.
- The same function adds its own day arithmetic at `:812`, which P.9 says belongs only in `readWindow`. It also reads
  `getAll("from")`, which `noRawRangeReads` does not match.

R3 checks only the regions, so it passed over a refusal screen.

Fix:
1. Have `globalWorkPageQuery` take its window from `readWindow` and `rangeWindow`. That accepts both forms and removes
   the second piece of arithmetic.
2. Have R3 fail on any `[data-page-refusal]` on a page whose fixtures are served.
3. Widen the `noRawRangeReads` pattern to `getAll`.

### L1 (Low): the focus outline misses the title cell, and the first column has a white fill
`frontend/src/ui/homeList.css`: on the Decisions shot at 1440, `tr:focus-within` draws its outline around the `td`s
only. The `th` keeps the table's white row-header fill against transparent cells, so the focused row's outline is cut
at the title.

The packet names the fill as cosmetic, but the cut focus ring is an accessibility defect. Fix: give
`.hl-table th[scope=row]` the row background and draw the outline on the `tr` with `outline-offset`, or as an inset
`box-shadow` on every cell.

### L2 (Low): Loading copy differs from §5.3
`homeLists.tsx:321,350,375` read "Loading the decisions across the estate.", not "Loading {plural}…". The tiles'
labels are also not shown while loading. Fix: use the spec words and draw the tile labels.

### L3 (Low): "First page" is a dead control after the I9 restart fails
`homeLists.tsx:322`, together with `estateReadCache.tsx:154`. The refusal link goes to the current address, so
`useEstateRead`'s key does not change and nothing is read again. Fix: add a nonce to the key, or let a click on the
refusal link force a re-read.

### L4 (Low): wording and crumb
- The Portfolio's "See all 8 findings" now opens `/decisions`; it should say "decisions". P3b rebuilds this panel, so it
  can wait.
- The Records tab's breadcrumb reads "Operational records" above the H1 "Evidence & records"
  (`OperationalRecords.tsx:630`).

### L5 (Low): one exemption const carries two meanings
`NOT_AVAILABLE_YET` (`homeLists.tsx:29`) serves the Decisions Due and Who decides columns (MD-IAP-2, resolving unit 6f)
and also the Findings "Heading" fallback, a Finding with no categories. Optional fix: a second const for the heading, so
the 6f resolution can retire the first without touching the second.

## (a) The two missing-claim-scan exemptions: justified
- Both words are spec literals: §5.2 for "Detail not available yet" and the Heading fallback; §7 MD-IAP-2 for Due and
  Who decides.
- Each exemption is one `const`, and the scan enforces that every reference is in its own file. I confirmed no
  reference outside those files.
- They follow the existing precedents (`NAV_RAIL_UNAVAILABLE_STATUS`, `IN_PAGE_UNAVAILABLE_STATUS`): a destination or
  record the build has not made.
- They do not hide a Site-evidence gap. The "not a missing claim about a site" wording in the reason stretches for
  Due/Who decides, but MD-IAP-2 governs those words, with a resolving unit.
- The scan still passes with the seed ceiling unchanged. See L5 for a tidier split.

## (b) The hard-wiring baseline shrink: real removal
- The four `href` hits in `findingIndex.tsx` were `to={item.links.opportunity}`, `to={item.links.evidence}`, a second
  `to={item.links.opportunity}` and `to={item.links.site}`. All four were in the retired Findings opportunity table, and
  the diff deletes them.
- The ratchet's regex (`frontend-hardwiring.mjs:32`) is unchanged.
- The new list targets are built from typed Refs through `linkFor` (`homeLists.tsx:70-73,152,232`). They are not raw
  server hrefs that escape the pattern.
- The check passes at href 20. The capability is moved to the Portfolio Opportunity tab, which is packet deviation 3,
  not hidden.

## Not verified
- Light against dark: the live app has no dark token block (`frontend/src` has no `prefers-color-scheme: dark`), so
  every "dark" gate and shot renders light. "Clean in light and dark" is true but proves nothing. This was already so
  before this slice; note it for the owner walkthrough.
- The 768 × 1024 shots (spec §6) and `layout-evidence.mjs` were not run, by me or the builder.
- The plants were not rerun; I relied on the packet.
- Live data: I had no backend outside the forbidden ports, so Site-type coverage is from fixtures only.

## Residual risk the packet does not name
- The read cache holds a loaded read until the range changes. An Action recorded in the session does not move a
  Decision to "Under way" until reload. This is by spec §4.1, but the owner should know.
- The rail lights "Findings" on a Finding's `recommendation` view, which is where a Decisions row lands. Spec §2.3
  "Decisions" home for that view arrives with P5's object pages.
- `navigation-truthfulness.ps1` now pins only `export function railHomeOf`, not its patterns. `iaRoutes.test.ts` carries
  that coverage.

## Questions for the Architect
None blocking. Optional: should the `iap_gates.cjs` fixtures include a cold, EV, MONITOR and no-ref row, so that L2
exercises the text-row and windowed-link paths in the browser? Today they are covered only by vitest and this review's
probe.

## Verification (fix round 1)

Head be1d55363, diff 232c5b4e0..HEAD. **Verdict: ACCEPT.** No remaining Medium or High finding.

- M1 fixed: `HomeList` hands `model.rows` (filtered) and a `whole` flag to `tiles`; Decisions uses the server `waiting_count` only when whole. New tests in `homeLists.test.tsx` cover parts under a State facet on Decisions and Actions.
- M2 fixed: Findings column and tile read `Loading…` in flight and `Not available yet` when refused; "No decision open" and 0 only when the read is ready. Two tests.
- M3 fixed: `globalWorkPageQuery` calls `readSharedRange`/`capWindow`/`rangeWindow`; its own day arithmetic and `validMidnight` are gone; `known_at` is checked first. Test covers 1-31 Oct, a 40-day range (last 31 days, `link` keeps the whole) and a reversed range. Gate R3 now fails on any `[data-page-refusal]` on a list page or any `INVALID_*` on any page. `noRawRangeReads` also matches `getAll`.
- Deviation (01:00Z accepted, rounded to its day; "not a UTC midnight" case became "not a date"): consistent, not a loosening. `readSharedRange` already accepts instant forms by their day, rejects a reversed raw instant pair (line 131) and caps at 31 days; the Incidents client must read the same address the date bar writes, and a single reader is what M3 asked for. Invalid input ("yesterday") still refuses. Residual: no test pins a 01:00Z `from` against Incidents; low risk.
- Gate fixtures: portfolio/findings carry cold windowed, cold no-window, EV, watched, under-way and no-link rows; actions a no-link row. Decisions shot shows Decision 4 and 7 as text rows ("Detail not available yet"), Being watched and Under way states, three Site types. L2 now requires at least one text row per list, so it cannot pass vacuously. Real coverage.
- Deferred Lows (L2 tile labels while loading, L3 nonce, L5 second exemption const, L4 wording) are reasonable: cosmetic or cross-cutting, none affects an acceptance criterion.
- Noted, not a finding: on `/evidence/records` the gate serves no records API, so the shot shows the inline "Work records could not be read. Reload." alert; a read failure, not an `INVALID_*` refusal, and the bar reads "1-31 Oct 2026". I did not exercise a real records fetch.

Checks run: `tsc --noEmit` clean. Vitest `src/estate src/ui` plus globalIncidents and operationalRecords: 33 files, 429 passed. `src/work`: 10 files, 207 passed. `src/shell` full: 22 failures in untouched files (overviewDispatchAssessment, s502, s5SiteWindowOverview, siteDetailScreen, ...), none in the diff; not compared against main (the packet names only SR-6b). Fresh vite build, `iap_gates.cjs`: 29 of 29 pass, exit 0. Architecture and agent-workflow scripts not rerun (packet figures cited). Preview server stopped, scratch deleted.
