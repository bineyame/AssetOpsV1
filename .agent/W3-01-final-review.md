# W3-01 final review (whole slice, head `60e0bf55`)

Reviewer: fresh Claude reviewer, independent of the builder. Read through git only. I did not run tests in
`AssetOpsV1-review2` because the full backend suite is running there.

## Verdict: REVISE (one High; one CSS line to fix, then a recapture of the affected PNGs)

## Findings

### H1 (High, user-visible mock mismatch): the first table-header cell loses the header band on all five roots
- `frontend/src/estate/estate.css:96-101`:
  `.estate-page .data-table th:first-child, .estate-page .data-table td:first-child { position: sticky; ... background: var(--surface-raised); }`.
  - Its specificity is (0,2,2). The shared header rule `.data-table thead th { background: var(--surface-sunken) }`
    at `frontend/src/ui/primitives.css:560` is (0,1,2), so the estate rule wins.
  - Result: the `FINDING` and `ACTION` header cells render white while the rest of the header row is grey.
- Where it shows: on every Findings lens and on Actions, at 1440 and at 390, in every state. See
  `findings-positive-1440-app.png`, `actions-positive-1440-app.png` and `findings-positive-390-app.png`.
- The v69 mocks (`mock/mock-findings-1440.png`, `mock/mock-actions-1440.png`) show one uniform grey header band.
- Fix: add
  `.estate-page .data-table thead th:first-child { background: var(--surface-sunken); z-index: 2; }`.
  Recapture or re-check the header row on one Findings and one Actions capture at each width. No measured height
  changes.
- Why the earlier checks missed it: the panel-structure test and `measure-summary.json` measure heights and
  rectangles, not colour.

### L1 (Low, carry): `FindingsIndex` is orphaned
- `frontend/src/sites/FindingsIndexes.tsx:63` (`FindingsIndex`) has no production consumer now that `FindingsFrame`
  was removed. Either delete it or record it as a carry.

### L2 (Low, pre-existing, not W3-01): tall dark band under the mobile shell header on short pages
- The packet's observation is confirmed: `findings-refused-partial-390-app.png` shows a header about 290 px tall.
- It appears only when the page content is shorter than the viewport. Long 390 pages look normal.
- W3-01 changed only the rail entry in `OperatorShellLayout.tsx`, so this is existing shell behaviour. Log it for the
  W1 UI/UX pass. It does not block.

## Focus items

1. **Commit 4 captures, heights, public reads and packet.**
   - Captures: all 64 PNGs are committed (5 roots x 5 states x 2 widths, plus page two and the refusal). I viewed them
     against the v69 mocks.
   - Panel order and copy: these match the mocks, apart from the ruled rewrites (q9/q13 copy, `Not assessed`,
     `Finding {8 chars}`, the Actions lifecycle line, and the Site cell `site_name` link with the code below it).
   - Fixture artefact: the Finding labels are identical in the captures (`Finding 00000005`) because the fixture UUIDs
     share a prefix. Random UUIDs differ. This is not a finding.
   - Heights: I re-read `measure-summary.json`. It has 52 rows, the only cap breach is the Findings 1440 card row
     (150/146), and overflowX and clipped are 0 everywhere.
   - Public reads: `reads-{positive,pending,partial}.json` back every claim in the packet:
     - scope;
     - FOREIGN-001 404;
     - page one `PENDING_RECOMPUTE` and page two `HISTORICAL`, with the same token `sha256:75e8e609...`;
     - historical page one and page two, with the same token and `as_of` 11:07:15Z;
     - `INVALID_WINDOW` and `INVALID_CURSOR`.
   - Minor packet note: the page-two UI capture shows 2 rows, but the API proof used `limit=1`. The UI capture
     evidently used a different limit. No row is lost.
   - Otherwise the packet is complete and its accepted limitations are stated honestly.
2. **CSS fix `89c53b0e`.**
   - The new selector `.estate-page .estate-state-chips` matches only `findingIndex.tsx:186`. The class
     `estate-state-chips` has no other consumer.
   - The other `.v69-chips` consumers keep the shared wrap rule. These are `SiteFindingIndex`, `SitesIndex`,
     `PerformanceDispatch`, `SiteWindowOverview`, `SiteWorkActions`, `siteWorkCases` and `LedgerSiteEvidence`.
   - The test regex at `estateRoots.test.tsx:539` still matches.
   - No regression.
3. **q14-1 (cards 150 px against a cap of 146).** Recommend option (a): accept it and record a cap waiver.
   - The overrun is 4 px, about 3% above a cap that already allows 30%. Nothing is clipped, and it occurs only on
     complete reads.
   - The cause is the ruled honest zero copy. Option (b) would reopen a ruling, and option (c) would hide the
     explanation. Option (a) needs the Architect's sign-off.
4. **Net diff against main.**
   - `main` (`a4dafe30`) is an ancestor of the head, so the merge cannot drop HEAD's side.
   - Money helpers are present at the head: `select_consequence_on` 1, `for_finding_on` 1, and
     `test_w301_w1_money_snapshot_helpers_postgres.py` present. Main has 0 of each.
   - `git diff 75f4e4c8 60e0bf55` over the financials, analytics and evidence adapters is empty.
   - No W4 file is touched. The deletions are limited to reviewed W3-01 files.
   - No debug code was found: no console.log, print, breakpoint or TODO. `pin_read_at` and `/__capture` live only in
     `.agent/W3-01-evidence/serve.py` and tests.
   - All material files were covered by an earlier unit review.
5. **Classification of the packet readings.**
   - Covered:
     - q8, q9-2, q10 and q11-1 (Runs 9-12 and c2r1);
     - c2r1 reading 1 (Run 12);
     - c2r1 readings 2-7 (classed as mechanical in `W3-01-commit2-review.md`, with the EV catch-all as a Low carry);
     - q13 readings 1-12 (Run 13);
     - the commit-3 mini-grid predicate (re-review ACCEPT);
     - q14-2 (withheld pending rows follow Run 12; the limitation sentence carries the pending basis);
     - q14-3 (an Action's coverage does not depend on a selection; matches golden `actions-none-complete`; the partial
       Actions copy is proved by frontend tests only);
     - q14-4 (the same TEST-SCOPED pin as golden `mixed`, within the accepted clock-drift limitation).
   - Needs the Architect: q14-1 only.
   - Not a reading: the shell band observation (L2 above).

## Checks
- Ran: git reads and greps, the `measure-summary.json` and `reads-*.json` analysis, and a visual review of the
  captures against the mocks.
- Not run by me:
  - backend focused or full suites, because the worktree is busy;
  - vitest, build and tsc;
  - `check-all.ps1`.
- The packet's numbers for those checks (75 focused tests, 2373 frontend tests, 11 guards) are unverified by me.
  The full backend suite result is still pending.
