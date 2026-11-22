# IA-P2 handoff (PARTIAL: P3a and P4a built; P3b code built, its test migration, gates and slice end not done)

Branch `task/IA-P2-portfolio-figures`, worktree `/opt/assetecon/AssetOpsV1-iap2b` (the brief's
`/opt/assetecon/AssetOpsV1-iap2` already held another clean worktree, `task/IA-P-spec-rev2`; left untouched).
Head after this file: see `git log -3`. No DB used, no process left running, no preview server.

## Done
- **P3a** (`c558fd4e2`): `deep_dive/period.py` (`Period`, `MonthServed`, `month_days`, `closed`, `resolve`, `header`,
  `Sums`, `period_view`, `driver`, `contribution`, `span`, `refused_text`, `RangeRefused`), `deep_dive/read.py`
  (`period`, `_period_reads`, `_suggest`, `BadRange = P.RangeRefused`), `deep_dive_api.py` (shared `answer()` refusal
  order; `GET /api/portfolio/period`), `deep_dive/tables.py` (code constants: modes, routes, `DAY_PATTERN`, ...),
  statements `i18n/statements/en/portfolio_period.py` and `portfolio_sites.py`, cases
  `backend/tests/statement_cases/portfolio_period.py|portfolio_sites.py`, T8 key list in `test_sc1_statements.py`,
  `period.py` and `sites.py` added to `ADOPTED` in `tools/checks/statement_catalogue.py`.
  Tests `backend/tests/test_iap_portfolio_period.py` (P.7 tests 1 to 12 plus every statement case rendered).
  Fixtures `frontend/src/estate/__tests__/fixtures/iap/period-{period-2026-09-10,month-2026-10,none-2026-11}.json`
  (test 10; rewrite with `IAP_WRITE_FIXTURES=1`).
- **P4a** (`dc03a546c`): E0 `waiting_count` / `waiting_by_site` in `estate/portfolio.py` (summary, after
  `category_counts`; `MONITOR` and matched Actions not waiting); E1 `deep_dive/sites.py` (`SiteRef`, `sites_view`,
  sum check `AssertionError("SITES_SUM")`, logged 503 in the route), `DeepDiveRead.sites`, `GET /api/portfolio/sites`.
  Tests `test_iap_waiting_counts.py` (4), `test_iap_portfolio_sites.py` (P.8 tests 1 to 9 with 4b).
  Fixtures `sites-2026-10.json`, `sites-2026-09-10.json`, `sites-none-2026-11.json`; `portfolio.json` gains
  `waiting_count` 6 and `waiting_by_site` {KOBO-001: 3, COLD-001: 2, EV-001: 1} (indent 1 kept).
- Each new test file was run failing first (collection error: module absent), then green.
- Run at `dc03a546c`: `test_iap_portfolio_period.py`, `test_iap_portfolio_sites.py`, `test_iap_waiting_counts.py`,
  `test_sc1_statements.py`: 472 passed; with `test_5c_deep_dive_api.py` and `test_5c_deep_dive_view.py`: green
  (673 at P3a). `statement_catalogue.py`: only `HAND_BUILT_NEW decisions/adapters/structure_read.py:24`, which is
  pre-existing (seen with this slice's ADOPTED edit stashed). `git diff main -- backend/assetops_backend/deep_dive/view.py`
  is empty.

## Plants (one-line edits, each reverted; output in the packet to be written)
- `dayscut` (`resolve` counts a PARTIAL month: `if closed(...)`): test 1 fails (1 failed).
- `onefig` (row gap re-formatted from `R.effect.quantize(Decimal("1E1"))`): tests 2 and 3 fail. Note: a whole-dollar
  quantize is invisible on World P (all whole dollars); the tens rounding is the one shown.
- `handbuilt` (an f-string in `period.py`): `HAND_BUILT period.py:126`. E1's (f-string in `sites.py`):
  `HAND_BUILT sites.py:36`.
- `sum` (sum check returns): test 4 fails. `order` (reverse sort): tests 1, 7, 9 fail.

## Defaults and deviations to carry into the packet
1. Worktree path (above).
2. P.7 test 2 lists tiles[0] lines as only the target line; P.5 and R2 (D-IAP.25, later) keep 5c's `W.sites` line, so
   the test asserts `["Target $4,590.00 · 63% of target", "3 of 3 Sites"]`.
3. World P's recipe (`replace(served, snapshot=replace(snapshot, month=...))`) trips 5b's compose check, so
   `copy_to` also moves each Site snapshot's `month`, `inputs.month` and `targets.structure.month` (test support only).
4. P.8 test 8 "targets emptied": an empty values mapping breaks 5b's bridge (KeyError), so every target value is
   withdrawn (`value=None`); September `R.k` is then 2 (asserted).
5. `header(..., *, now)`: P.2's signature has no clock, but 5c's `_nav` rule needs one; added keyword-only.
6. Two statements not named in P.6 carry P.5/P.8's f-string forms without new English: `portfolio_sites.driver`
   ("{factor} {effect}") and `portfolio_period.assure_entry` ("{month}: {standing}"); plus `portfolio_period.month`
   (the year rule), `portfolio_period.text` and `portfolio_sites.text` (column words). BAD_RANGE's "two" and "the
   first not after the last" are example slots (SC-1 bans number words in literals).
7. A missing month row's `sites` is null, like its four figure keys.
8. E1 mode `none`: `without_target` is `{"count": 0, "text": null}` (no figure exists to be left out of).
9. E1 Site money is shown only in the months' own currency (`Sums.cur`); otherwise "Not available yet" (needed for
   test 4b: World X's Kobo would else read "−KES 562.00"). Compared rows with no effect sort after those with one.
10. E1 fixtures are built over the IA-P fixture estate's five Sites (World A's three plus `COLD-001` and `EV-001`
    from `portfolio.json`), so E0's keys are E1's codes (R8) and the frontend sees MD-IAP-12 rows.
11. Order P3a, P4a, then P3b (both backend units together; P3b reads E1 only from P4b on).

## Next (P3b, spec section 6 "P3b"; then the slice end)
- Build P3b exactly as its card: `portfolioWords.ts`, `PortfolioTabs.tsx`, new `portfolioPeriodClient.ts`,
  `PortfolioOverview.tsx`, `PortfolioPeriod.tsx`, `DeepDiveMonth.tsx` props (`month`, `nav`, `notes`; I1 deletes
  `MONTHS`, `monthWords`, `monthAfter`), `sharedRange.ts` (`entryRange(pathname?, now)` per I3, `monthDays`, `/results`
  in RANGE_PAGES and FILLED_PAGES), `EstatePortfolio.tsx`, new `Results.tsx` (I14), `EstateEvidence.tsx`, `App.tsx`
  aliases (§2.4 P3b rows), `tools/deep_dive_gates.cjs` (URL argument, period and IA-P portfolio fixtures),
  `tools/iap_gates.cjs` gates H1 to H6, the DDR runbook S7 line. Tests first: `portfolioHub.test.tsx` (the card's nine
  cases plus I3's `/` lands on last month), `DeepDiveMonth.test.tsx` updates (name them), `Results.test.tsx`, the
  `estateEvidence` scope section, and R2's vitest matrix (Overview names Thika on one- and two-month fixtures; the
  Outcomes/Sites part lands with P4b). Plants `fourtab`, `window`, `twofig`, `browsermonth`, `span`. Register
  MD-IAP-3, MD-IAP-7 (P3b part), MD-IAP-10, MD-IAP-11, MD-IAP-12 (P4a) in `.agent/mock-departure-register.md` from
  R784. Shots per the card to `/opt/assetecon/evidence/IA-P/IA-P2/` on `vite preview --port 5573`.
- Slice end: `IA_LANDED` gains `IA-P2`; test scope (every backend file importing a touched module, notably the
  `estate/portfolio.py` users `test_w303_portfolio_api.py`, `test_cov_partial_portfolio.py`,
  `test_cc_placement_postgres.py` via `--db`; whole `src/estate`, `src/shell`, `src/ui`) at head and on main; tsc;
  fast check-all; IA-P gates after a fresh build; packet `packet-IA-P2.md`, state entry (next number in
  `.ai/state/index-3.md`), spec status. The spec says IA-P2's merge stales the world ladder's L2 `code` part: the
  coordinator rebuilds the current rung once after the merge (spec section 8), to be stated in the packet.

## Risks
- `estate/portfolio.py` summary grew two keys: stored `chain_response` bodies grow (spec section 8, D-WK.16).
- Not yet run: the Postgres tests over `estate/portfolio.py`, and check-all.

## Session 2 (2026-11-22): P3b code (PARTIAL; stopped at the context budget)

`git merge main` (`1979bbef1`, brings the statement-catalogue allow entry for `structure_read.py:24`). Then
`a2b806502` (P3b code and its new tests) and the commit carrying this section (RESULTS_PATH moved for `iaRouteMap`).
`frontend/node_modules` is a symlink to the main checkout's (the convention of the other worktrees; gitignored).

### Built (P3b card)
- `portfolioWords.ts` three tabs (`overview`, `outcomes`, `demand` = `demand-and-capacity`), `PORTFOLIO_HUB_TITLE`.
- `PortfolioTabs.tsx` draws `SectionTabs` (range carried by `withRange`); `portfolioHref(window, tab)`, `decisionsHref`.
- `portfolioPeriodClient.ts` (`fetchPeriod`, `createPortfolioPeriodClient`, schema check `portfolio-period-1`).
- `PortfolioOverview.tsx`: E2 for the address range in days (`readSharedRange`; the entry fill writes instants),
  modes month / period / none, `useDeclareRangeSpan(shown)`, "Preparing the figures…", 401/422/503 handling, an old
  `?lens=` goes to `/decisions`.
- `PortfolioPeriod.tsx`: header with `period_words` and notes, L1 lead + `DdTiles`, L2 `DdQueue`, L3 "Month by month"
  (`DataTable`, one `<Link>` per row in `<th scope=row>`, gap word as chip, `sites` as `<small>`) + `DdOutcomes`.
- `DeepDiveMonth.tsx`: props `month`, `nav` (E2's), `notes`; `MONTHS`, `monthWords`, `monthAfter`, `monthHref` deleted
  (I1); no next control when `next` null; exports `DdTiles`, `DdOutcomes` (takes `cards`, `na | null`), `DdActions`,
  plus `DdQueue`, `DdHead`, `DdNotes`, `monthRangeHref`, `useDrawers`, `DrawerApi`; `DeepDiveMonthFrame` kept for tests
  only (not routed). `.dd-period` style in `deepDiveMonth.css`.
- `homeLists.tsx` `DecisionsRows` (HomeList decisions, `{tools:false, tiles:false, cap:6}`, `RangePartNote`).
- `sharedRange.ts`: `entryRange(pathname?, now)` (Last month on `/portfolio`), `monthDays`, `/results` in
  `RANGE_PAGES` and `FILLED_PAGES`; `SharedRangeBar.tsx` passes `location.pathname`.
- `EstatePortfolio.tsx`: Overview branch, pulse, `TopThree`, `PulseCount`, `episodeText` removed; Outcomes =
  `ObjectivesPanel` + `CategoryCards`; Demand = `OpportunityPanel`; header "Portfolio" (§5.3); coverage line moved out;
  `ProgressPanel`, `ScopeDisclosure`, `ContextFooter` exported; new `PortfolioScopeSection` (coverage line, disclosure,
  footer) rendered as the last section of `EstateEvidence.tsx` (estate client passed via `EstateEvidenceFrame`).
- `Results.tsx` (`ResultsPage`, `ResultsFrame`); `RESULTS_PATH` in `shell/operatorSiteRoutes.ts`.
- `App.tsx`: `/portfolio` → `PortfolioOverview`, `/portfolio/:tab`, `/results`; `/portfolio/month` route removed.
- `iaRoutes.ts`: four `IA-P2` aliases (month via `monthDays`, dropping `month`), `/results` home, `IA_LANDED` has
  `IA-P2` already (needed by the alias tests). Rail: Results live (`OperatorShellLayout.tsx`, guard
  `navigation-truthfulness.ps1`, `iap_gates.cjs` R1 table).
- Tests (new, green): `portfolioHub.test.tsx` 14 (the card's nine, the `/` landing, R2 matrix one- and two-month),
  `Results.test.tsx` 2, `estateEvidence.test.tsx` scope section 2. Backend test 10 now also writes the World G
  fixtures `month-g-2026-10.json`, `period-month-g-2026-10.json`, `period-period-g-2026-09-10.json`.
- `settled.ts` regex learns "Preparing the figures…" and "Loading Results…".

### Next (in order)
1. Failing-first proof of the new tests: a scratch worktree at `1979bbef1` with the three test files and fixtures
   copied in (collection failure, module absent), as P3a/P4a did.
2. Migrate the existing tests (vitest `src/estate src/shell src/ui` at `a2b806502`: 146 failed / 1850 passed, 19 files):
   `DeepDiveMonth.test.tsx` 24 (mount `DeepDiveMonthFrame` with `month`, `nav`, `notes`, an estate client; rewrite
   the month-links test to E2 nav and the tab-row tests 13; name each in the packet), `estatePortfolio.test.tsx` 68
   (Overview card tests → `/portfolio/outcomes`; pulse and top-three tests retired with D-IAP.12; scope tests →
   Evidence; the progress test already moved to `Results.test.tsx`; PF-T tab tests → three tabs),
   `estatePortfolioRoutes` 3, `estateEvidence` 2 (v69 `globalevidence` panel structure: check the v69 part with the
   scope section removed and assert the section separately), `operatorRailInventory` 22 (Results live: ten links),
   `operatorRouteFrames` 2, `sharedRange` 2, `s502OverviewFindingList` 5, `siteDetailRoute` 3,
   `siteFoundationRoute` 3, `siteRangeMatrix` 2, `sitesIndexRoute` 2, `sr2RequestUrls` 2, `operatorSiteTabs` 1,
   `simulatorLabGate` 1, `simulatorLabWorkspaceEntryPoint` 1, `w301EstateShellRoutes` 1,
   `sharedVisualVocabulary` 2. Compare each with main (some may be pre-existing). Log:
   scratchpad `vt1.log` (not kept).
3. Plants `fourtab`, `window`, `twofig`, `browsermonth`, `span`; gates H1 to H6 in `iap_gates.cjs`;
   `deep_dive_gates.cjs` URL argument and the period/estate fixtures; DDR runbook S7 line; register MD-IAP-3,
   MD-IAP-7 (P3b), MD-IAP-10, MD-IAP-11, MD-IAP-12 from R784; shots.
4. Slice end as the brief.

### Deviations added (carry into the packet)
12. R2's two-month matrix: P.5 (binding, built in P3a) serves counts, not names, in mode `period`; the Overview states
    "Compared for 3 of 4 Sites" (headline, tile 1, each row) but names Thika only inside a month's step drawer (one
    click via the month row). The one-month test opens a step drawer to find "Thika: not a mini-grid Site, not
    included." Question for the Architect: is the count enough on the two-month Overview?
13. PortfolioTabs lost its counts (SectionTabs has none; the Opportunity and What changed counts had no tab left).
14. `ProgressPanel`, `ScopeDisclosure`, `ContextFooter` are exported from `EstatePortfolio.tsx` and rendered verbatim
    by `Results.tsx` and `PortfolioScopeSection`, not moved file to file.
15. The month alias's `to` function deletes `month` from the search it is given (the redirect then merges the rest).
16. New words beyond the spec: "Loading Results…" (§5.3's list pattern), the period header without operator (E2 serves
    none), "Decisions" as the L2 title outside mode `month` (menu label).
