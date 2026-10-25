# post-W6 W2-EV independent review

Reviewer: fresh Claude reviewer (not the author). Branch `task/post-W6-W2-EV`, head `d28e6e73`, last product commit
`dab4d15e`. Diff `git diff main...HEAD -- ':!.agent'` (28 files). Main `2835e69e` is ahead of the merge base `ba971d96`
only by docs (`ui-ux-decision-guide.md`, demo-sprint planning), so there is no unmerged code drift.

## Verdict

**ACCEPT with findings fixed on the branch.** Two Medium findings: M1 (Q31) and M2 (Q23). Neither changes the
architecture. The Low items are guide-alignment notes and do not block.

## Findings

### M1 (Medium, acceptance gap: Q31 and the register header): the R420/R421 D4 labels are code comments, not visible labels
- `frontend/src/sites/EvAssessmentViews.tsx:466` and `frontend/src/sites/EvSiteViews.tsx:1246` carry
  `MOCK DEVIATION (D4) R420/R421` only as JSDoc comments. Nothing near the Sessions line `[data-ev-outside-outcomes]` or the
  billing chip renders a `MOCK DEVIATION D4 (R420)` / `(R421)` label.
- Ruling Q31 says "Keep visible D2/D4 labels adjacent to touched departures, including Q4/Q13". The register header
  (`mock-departure-register.md:211`) says "Each open D1/D2/D4/D5/D6 row must show `MOCK DEVIATION Dn` beside the affected
  element". The builder's own pre-flight default for Q31 says "visible". Other cards render the label with
  `<p className="mock-deviation-line" data-mock-deviation="R383">MOCK DEVIATION D2 (R383)</p>` (`SiteAnalyticsFrames.tsx:959`).
- What goes wrong: in the owner walkthrough, the Q4 line and the Q13 chip read as mock-conformant. The owner cannot see
  that they are registered departures.
- Fix: render the same `mock-deviation-line` element with `data-mock-deviation="R420"` next to the outside-outcomes line,
  and one with `"R421"` next to the billing chip on ev-financials and ev-assumptions. Use the guide §5 format
  `MOCK DEVIATION D4 (Rnnn)`. Add one assertion per label. Then recapture the affected pairs: sessions missing-meter (the
  case where the line shows) and ev-financials/ev-assumptions (billing).

### M2 (Medium, Q23): the EV Findings index row links use the address window, not the read's selected window and cutoff
- `frontend/src/shell/SiteAnalyticsFrames.tsx:503-504` builds `findingHref` and `sessionsHref` from
  `coldWindowFromParams(params)`. The tabs on the same page use the loaded read's `selectedWindowSearch(read.value)`
  (`EvFindingIndex.tsx:50`).
- Ruling Q23: "New Sessions/Finding/Energy links and tabs use their own selected window and cutoff." The test pins the
  gap. In `evFindingIndex.test.tsx:65`, the read's window has `known_at: TO`, but the row href is asserted with `from`/`to`
  only and no `known_at`.
- What goes wrong: on a no-window address (indexed case `inventory-check`), the rows open the Finding and Sessions pages
  with no window, although the index listed the read's selected window. On an address without `known_at`, the row omits
  the cutoff the list was read at. The Finding then opens at the latest revision rather than the revision shown (the row
  key uses `revision_id`).
- Fix: build the two hrefs inside `EvFindingIndex` from `body.window`, using `selectedWindowSearch(body)` or the item's
  `links.self` through the existing UI-href mapper. Update the test to expect `known_at`, and add a no-window-address case.

### L1 (Low, UI guide §3): refusal sentences have no `role="alert"`
`RefusedGap` (`EvAssessmentViews.tsx:~142`) renders through `Gap`, a plain `<p className="not-available-yet">` with no
live role. The guide asks for one `role="alert"` per refused read. The guide landed on main after this branch's
pre-flight, so this is alignment, not a ruling miss. Fix: give the one in-panel sentence `role="alert"`. Keep the other
panels' `Not assessed` gaps without a role.

### L2 (Low, UI guide §4): missing-zone fallback on EV Analysis shows only "UTC"
With no usable Site zone, the headers read `Measured (UTC)` / `Sent (UTC)` / `Received (UTC)` (`EvSiteViews.tsx:1146`).
They do not say the Site zone is unavailable, and `siteTime(...).siteZone === false` is ignored. A genuinely UTC Site
looks identical. The shell's Ledger evidence table behaves the same way, so the two are consistent. Optional fix: add the
guide's explicit suffix when `siteZone` is false.

### L3 (Low, UI guide §1): EV Findings index has no paging although the API takes a cursor
`EvFindingIndex.tsx` states "Showing the first N Findings; paging is not available on this page." when `next_cursor` is
set. The backend `ev/findings` accepts `cursor`, but `evAssessmentClient.listFindings` does not take one, so the rows
after the first page (default 50) cannot be reached. This is honest rather than silent, and a 50-Finding EV Site is
unlikely for the demo. A "Load more" like EV Analysis would close it. The same branch renders
"Showing the first 0 Findings…" under "No Findings…" when the items list is empty and a cursor is present (test
`states empty and cursor`). That is an implausible state with odd copy.

## Rulings checked (all others implemented as ruled)
- **Ruling 5 refusal copy, verbatim:** `EV_WINDOW_INVALID` gives "The selected window needs both a start and an end, with
  the start before the end."; `EV_WINDOW_TOO_LONG` gives "The selected window is longer than 31 days."; any other 422
  gives "The selected window is invalid."; the title is "Window cannot be read"; 403/404/503 keep their own wording and
  the requested-window line. Strip and tile labels stay with `Not assessed`, one in-panel sentence plus a technical
  disclosure, no banner. Applied on the Overview, Evidence, Analysis, Financials, Assumptions, Sessions, Finding and EV
  Findings pages (`EvAssessmentViews.tsx:88-160`).
- **`FINDING_SECTION_UNAVAILABLE`:** changed once to "This Finding section is not available for this kind of
  Finding." (`SiteAnalyticsFrames.tsx:646`).
- **Tab override and EV home:** `OperatorSiteTabs` has `hrefs` and `search` (`operatorSiteTabs.tsx`). `EV_SITE_TAB_HREFS`
  is in `evSiteRoutes.tsx`. EV mounts are wired in `SiteAnalyticsFrames`, `SiteFoundationFrame` (only the two readiness
  hrefs and the tab override) and `evSiteRoutes`. Bare `/sites/:id` redirects to `/sites/:id/ev` with the query kept
  (`SiteDetailFrame.tsx:138-151`). Mini and cold are unchanged. Tabs carry the loaded read's selected window and carry
  nothing on refused or loading reads.
- **Site time:** `siteTime.ts` adds Asmara, Djibouti and Mogadishu to the canonical EAT table. `EXTRA_EAT_ZONES` is
  deleted (no occurrence left in `frontend/src`). `eatTime` delegates to `siteTime`. EV Analysis uses
  `siteTime`/`siteZoneLabel` with exact UTC in `title`. No second algorithm.
- **Merge integrity:** in `SiteAnalyticsFrames.tsx`, `LedgerSiteEvidence.tsx` and `SiteFindingIndex.tsx`, the main...HEAD
  diff removes only W2-EV-intended lines: the two tab lines, the old section copy, `EXTRA_EAT_ZONES`, and nothing else.
  Shell, W1-a and W1-b hunks are intact.
- **Q1–Q13, Q15:** spot-checked in code. Readiness links, unique labels, lineage and claim-evidence links (hidden on
  refusal), the denominator line (no fabricated category; nulls only co-occur with the guarded UNKNOWN state), the Outcome
  column CSS, the strip phrase, plurals, the chronology (no padding; all events rendered because no Event details target
  is mounted), the Energy source link (none when unestimated), billing chips, cards with "View detail →", live Health,
  "Portfolio evidence", "Review energy →", unpadded next-evidence rows, quiet-case Cause and local-day-aware times.
- **Guards:** no guard was loosened. `missing-claim-scan.mjs` changes only the exemption decision/reason text. There is
  no baseline entry for EV readiness, which I confirmed in `missing-claim-baseline.json`.
- **Register:** R420/R421 are the only new rows, inside the W2-EV/W2-cold block (W4 ruling 22: R420–R449; dispatch:
  W2-EV R420–R434). `git log --all -S"| R420 "` shows only this branch, so there is no collision.
- **Stray files:** the diff has none (no `.venv`, `node_modules`, `__pycache__`, `var/` or `dist/`). The recapture is
  447 files and 81 MB under `r2/`.

## Caps: classification check (UI guide §1)
- **EV Findings index:** the classification is correct. Only the title is free text. Domain (`Sessions`), Priority and
  Lens (`Not assessed`), Confidence (claim word), State (lifecycle word) and Main consequence (`Not in this list`) are
  fixed words. Measured 429/699 against the 550/850 cap, and 462/781 with a 320-character gap. **Pass.**
- **EV Accepted records:** the classification is correct. `value_display` comes from `ev_site_reads._row_words`: a ruled
  closed word set for events and connector states (`KIND_TEXT`/`STATE_TEXT`), otherwise the stored numeric reading plus
  its unit. That is a fixed typed value. Source is free text (asset name plus a fixed suffix). Times are formatted
  instants and Record is a UUID. Measured 562/577 against 700/1000. **Pass.** The packet's "Source+Value 1344" row is
  informational, not a cap miss, so no Architect cap revision is needed on this point.
- **Sessions table:** even with every cell at 160 characters, 765/1258 against 900/1400 (798/1340 with the gap). **Pass.**
- **Finding Bounded conclusion:** 279/625 against 600/850 (331/793 with the gap). **Pass.** At 1440 each 160-character
  line fits on one line, so the height equals the real height.
- In `inspect.json` every synthetic variant is `verified: true` with `fieldsChanged == intendedFields`. Clipping is empty
  and `docOverflowX` is 0. At 390 the tables scroll inside `.data-table__scroll`.
- No genuinely free-text cell was exempted.

## Recapture coverage
- The audit index has 96 entries for the nine W2-EV screens (sessions 24, ev-finding 12, five EV Site screens 10 each,
  ev-readiness 6, ev-findings 4). The branch has exactly 96 app/mock pairs (batch-08 46, batch-09 50), split equally
  between 1440 and 390.
- Q29 extras: 8 pairs (one-sided and 32-day, on Overview and Sessions). I viewed the 390 one-sided Sessions capture. It
  shows the "Window cannot be read" strip, four `Not assessed` tiles, the exact sentence once, and no banner.
- Q28 shared reach: `reps` has 18 pairs and `batch-16` has 12.
- I viewed the ev-findings-window 1440 capture. It shows the EV branch with the strip separators.

## Checks I ran (worktree `AssetOpsV1-review5`, head `d28e6e73`)
- `npx.cmd tsc --noEmit`: exit 0.
- Targeted vitest (9 files: operatorSiteTabsOverride, evFindingIndex, siteTime, evAssessmentRoutes, evSiteMoneyRoutes,
  evFoundation, miniDecisions, siteFinding, v01bEvidenceVisual): **248/248 pass**. Vitest ran in this session, unlike
  the documented sandbox failure.
- `tools/check-all.ps1 -Python <main venv>`: **All 11 guards passed.** The missing-claim scan reported 42 tagged and 10
  baselined occurrences against merge-base `ba971d969a`.
- Revert proofs, each restored afterwards (`git status` clean):
  - `siteTime.ts` set to main: 9 failures (all three zones in siteTime, v01bEvidenceVisual and siteFinding).
  - Old `FINDING_SECTION_UNAVAILABLE`, old `EV_WINDOW_INVALID` sentence and the EV redirect disabled, together: 8
    failures across evAssessmentRoutes, evSiteMoneyRoutes (including bare home) and miniDecisions.
  - EV Findings branch disabled: 4 of 5 evFindingIndex tests fail. The mini-site case correctly still passes.
- Not run, per the dispatch: the full vitest suite, `npm run build` and captures. The packet's full vitest run (133 files,
  3179 tests) and build pass at `dab4d15e` are cited but not reverified by me. No backend change, so no backend suite.

## Residual risk not named in the packet
- `SiteDetailFrame` reads the Site type only when `coldSite` is passed. App always passes a default, but a test or embed
  without `coldSite` silently loses the EV redirect.
- At 390 the Site tab row is still a clipped horizontal scroller ("Findings  W…"). This is the shell/W4 R453 domain,
  not this card, but it is visible on every EV capture.
