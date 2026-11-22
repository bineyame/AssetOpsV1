# IA-P2 review packet (P3a, P3b, P4a and D-IAP.34)

Branch `task/IA-P2-portfolio-figures`, worktree `/opt/assetecon/AssetOpsV1-iap2b`. Head: see `git log -1` (stated in the hand-back).
Spec: `spec.md` rev 3 §6 P3a/P3b/P4a, `spec-period.md` P.2 to P.9, `rulings.md` D-IAP.34 (merged from main).
`USER_REVIEW_REQUIRED`: no (a build slice; the owner walkthrough is after the IA shape is built, `owner-review-at-product-shape`).

## 1. What was built

- **P3a** `deep_dive/period.py`, `read.py`, `deep_dive_api.py` (`GET /api/portfolio/period`), `tables.py`, statements `portfolio_period.*`, `portfolio_sites.*`.
- **P4a** E0 `waiting_count` and `waiting_by_site` (`estate/portfolio.py`), E1 `deep_dive/sites.py` (`GET /api/portfolio/sites`).
- **P3b** `PortfolioOverview`, `PortfolioPeriod`, `PortfolioTabs` (three tabs), `portfolioPeriodClient`, `DeepDiveMonth` props (`month`, `nav`, `notes`),
  `Results` (live at `/results`), the scope section in Evidence & records, `entryRange(pathname, now)`, aliases, `iap_gates.cjs` H1 to H6,
  `deep_dive_gates.cjs` URL, the DDR runbook S7 line (`specs/DDR-rehearsal/spec.md` line 49).
- **D-IAP.34** (ruled on deviation 12; merged from main at `Merge main (D-IAP.34)`): `period.py` serves `body.out` after `notices` and the one k/n set
  (`n` = Sites asked in any served month, `k = n - len(out)`); statement `portfolio_period.out_only`; `PortfolioPeriod` Lead renders `body.out` in
  `[data-dd-out]` with `<Lines className="dd-lines dd-lines--note">`; the client refuses a period body without `out`. Register R789 (MD-IAP-16).

## 2. Test migration: the 140 existing frontend tests that failed (per file)

Baseline: vitest `src/estate src/shell src/ui` on main (`fed238c25`, a scratch worktree): 1981 tests, 4 failed (pre-existing, below).
At `a2b806502` the same set: 144 failed (the handoff's 146 counted two flakes); head-only (not failing on main): **140**.
Rule: (a) the slice broke real behaviour, fix the code; (b) the test pins the old shape the spec replaced, migrate it and cite the section.
**(a) = 0. (b) = 140** (about 8 of them are retirements of a test whose subject left the page; each is named). No assertion was loosened to pass.

| File | Failing | Decision | What changed, and the spec section |
|---|---:|---|---|
| `estate/__tests__/DeepDiveMonth.test.tsx` | 24 | (b) | 20: the mount. The page takes `month`, `nav`, `notes` as props and reads no `?month=` (§6 P3b, I1); `renderMonth` mounts `DeepDiveMonthFrame` with them and an estate client; every assertion kept. 2 (World A strings, World A money): the month JSON's `decisions` panel is replaced by the Decisions list (§6 P3b), so `decisions` leaves the expected strings and the list's own figures leave the served-money check (`[data-home-list]` skipped). 2 month-link tests rewritten to E2's `nav` (days, no `?month=`, no next control when null; plus the next link, the month prop and the notes as new tests). The 2 tab-row tests (counts, "The month" tab) are retired: §2.2 replaced that row with three tabs, no counts; replacement `portfolioHub` "three tabs". |
| `estate/__tests__/estatePortfolio.test.tsx` | 68 | (b) | Entry moved to `/portfolio/outcomes` (§3, D-IAP.2: `/portfolio` is E2's Overview). Header is "Portfolio" alone (§5.3). Pulse and top-three assertions removed (D-IAP.12); tests retired with no replacement: `namesOnePrioritySiteInTheSingular`, `ch4_strip_counts_opportunities…`, the PF-T "known counts" test (merged into "no tab shows a count badge"), "Overview shows the four cards…" (replaced by "Outcomes shows the four cards, no pulse"). Tab names are Overview, Outcomes, Demand & capacity (§2.2). "What changed" assertions run on `ResultsPage` (§2.4: `/portfolio/changes` is `/results`); the scope, coverage-line, refused-window and partial-Site tests run on `PortfolioScopeSection` (§2.4: scope is Evidence & records'); the coverage line's placement check is now "leads the scope section". Two helpers left unused are deleted. |
| `estate/__tests__/estatePortfolioRoutes.test.tsx` | 3 | (b) | Title "Portfolio" (§5.3); Results live (3 unavailable roots); the Overview reads E2, not the estate portfolio, so its estate read count is 0 (D-IAP.2); the one-mounted-route and unknown-tab tests use the Outcomes and Demand tabs (§2.2). |
| `estate/__tests__/estateEvidence.test.tsx` | 2 | (b) | The v69 `globalevidence` panel structure is checked with the scope section set aside (`withoutScopeSection`), which is asserted by its own two tests (§2.4, §6 P3b "the `estateEvidence` scope section"); the "no mock values" scan skips that section's Site names. |
| `shell/__tests__/operatorRailInventory.test.tsx` | 22 | (b) | Results is a live link (§2.1, P3b): ten links, `Results` not among the unavailable roots, focus order of ten. 15 of the 22 are the same list in `railAt` helpers. |
| `shell/__tests__/operatorRouteFrames.test.tsx` | 2 | (b) | Same (rail list, ASSURANCE group "Results | live"). |
| `shell/__tests__/operatorSiteTabs.test.tsx`, `simulatorLabWorkspaceEntryPoint.test.tsx`, `w301EstateShellRoutes.test.tsx`, `siteDetailRoute.test.tsx` (3), `siteFoundationRoute.test.tsx` (3), `sitesIndexRoute.test.tsx` (2), `ui/__tests__/sharedVisualVocabulary.test.tsx` (2) | 13 | (b) | The rail's label, href and icon lists gain `Results` (`/results`, icon `book`) before Evidence & records (§2.1). |
| `shell/__tests__/sharedRange.test.tsx` | 2 | (b) | `/portfolio` with no range opens on last month (§6 P3b, D-IAP.21); the 7-day default is pinned on `/portfolio/outcomes`, last month by a new test. The Portfolio range test reads the Outcomes tab (the estate request) and the tab row has Demand & capacity. |
| `shell/__tests__/sr2RequestUrls.test.tsx` | 1 | (b) | The pinned estate requests (`/api/estate/portfolio` and `outcome-summary`, same strings) belong to `/portfolio/outcomes`; the Overview reads E2. |
| `shell/__tests__/s502OverviewFindingList.test.tsx` | 3 | not caused by the slice | The failure is `expected 'loading' to be …` and moves between tests from run to run (3 at `a2b806502`, 1 on main's baseline, 1 in this head run, 0 in an isolated run). Each green in isolation; recorded as an existing timing flake under load, not edited. |

Failing on main as well (not edited, not this slice): `siteRangeMatrix` "mini /health (R)" and "each Site route in App.tsx has a matrix row" (the
uploads route, a main fault), `sr2RequestUrls` SR-6b, `s502OverviewFindingList` (flake). `simulatorLabGate` "offers no way to create a site" failed once in the full run
under load and passes in isolation.

**Questions for the Architect or coordinator.** None blocks. (1) The deleted tab-row HTML fixture `portfolioTabsOverview.before.html` is now referenced only by a
comment; delete it when convenient. (2) See Risks 1: the demo's prebuilt-response generator.

## 3. New tests and failing-first

- Backend: `test_iap_portfolio_period.py` gains test 11's `out` assertion, tests 13 and 14; run failing-first earlier for tests 1 to 12 (collection error: module absent, P3a).
  Test 13 and the plants: `countonly` (`out` always `[]`): test 10, 11, 13 fail; `twosets` (`k`, `n` of the latest month): test 13 fails. `test_sc1_statements.py` T8 key list has `out_only`.
- Frontend (new, `portfolioHub.test.tsx` 16 with the D-IAP.34 additions, `Results.test.tsx` 2, `estateEvidence.test.tsx` scope section 2): run at `1979bbef1` (before the P3b code) in a
  scratch worktree with the three files and fixtures copied in: `Results.test.tsx` fails to collect ("Failed to resolve import ../Results"), `portfolioHub` 13 of its 14 then-present tests failed
  (the 14th passes without P3b code; the D-IAP.34 tests were written after), `estateEvidence` scope section 2 of 2 failed.
- P3b plants (one-line source edits, each reverted):

| Plant | Edit | Result |
|---|---|---|
| `fourtab` | a fourth entry in `PORTFOLIO_TABS` | `portfolioHub` "three tabs in order" fails; gate H1 fails (`tabs are [Overview, Outcomes, Demand & capacity, Extra]`, all three modes) |
| `window` | `SectionTabs` `to={tab.to}` (no `withRange`) | `portfolioHub` "three tabs … keeping the range" fails (`['absent', …]`) |
| `twofig` | `data-portfolio-card-value` on the period headline | gate H2 fails (`H2: period: 1 [data-portfolio-card-value]`) |
| `browsermonth` | month read for the address range's `to` month | `portfolioHub` "mode month reads the month read for E2's served month" fails (`['2026-11']`) |
| `span` | `useDeclareRangeSpan(null, null)` | `portfolioHub` "declares E2's shown span" fails; gate H6 fails (`the bar's tag is null`) |
| `nameless` (D-IAP.34) | Lead ignores `body.out` | `portfolioHub` "two months (World G)" fails |
| P3a/P4a plants | `dayscut`, `onefig`, `handbuilt`, `sum`, `order` | as the handoff (test 1; tests 2 and 3; `HAND_BUILT period.py:126` and `sites.py:36`; test 4; tests 1, 7, 9) |

## 4. Gates and checks

- `tools/iap_gates.cjs` after a fresh `vite build` (preview on `:5573`): 50 results, all pass: R1 to R8, L1 to L3, aliases (including the three P3b aliases), H1 and H2 (month, period, none),
  H4 (hub regions L1 L2 L3, 390 width, the bar says "All pages", both month rows land on their month), H5 (notes visible, "Show October 2026" lands on `2026-10-01..2026-10-31` and renders L1),
  H6 (tag `inside`). `tools/deep_dive_gates.cjs <url> <World A fixture>` at `/portfolio?from=2026-10-01&to=2026-10-31` (H3): 9 of 9; `--world X`: 7 of 7.
- Shots: `/opt/assetecon/evidence/IA-P/IA-P2/iap/` and `dd/` (the gate's own captures; the three widths, light and dark).
- `tools/check-architecture.ps1` (with `ASSETOPS_GUARD_PYTHON`): passed. `tools/check-agent-workflow.ps1`: passed. `tsc --noEmit` over `src` including tests: clean.
- Register: R784 to R789 (MD-IAP-3, -7 P3b part, -10, -11, -12 P4a part, -16). State entry 205 in `shell.md`.

## 5. Counts (head against main)

COUNTS_PLACEHOLDER

## 6. Known deviations (all 16 of the handoff plus the session's)

1. Worktree path `/opt/assetecon/AssetOpsV1-iap2b`. 2. P.7 test 2 lists tile 1's lines as target plus "3 of 3 Sites" (5c's `W.sites` line kept, P.5/R2). 3. World P's recipe also moves each Site snapshot's `month`
(5b's compose check; test support). 4. P.8 test 8: targets emptied by `value=None`. 5. `header(..., *, now)`. 6. Statements beyond P.6 (`portfolio_sites.driver`, `portfolio_period.assure_entry`, `.month`, `.text`).
7. A missing month row's `sites` is null. 8. E1 mode `none`: `without_target` `{count: 0, text: null}`. 9. E1 money only in the months' currency. 10. E1 fixtures over five Sites. 11. Build order P3a, P4a, P3b.
12. **Resolved by D-IAP.34** (the period body names the Sites it leaves out; built). 13. `PortfolioTabs` has no counts (SectionTabs has none). 14. `ProgressPanel`, `ScopeDisclosure`, `ContextFooter` exported from `EstatePortfolio.tsx`, rendered verbatim by `Results` and the scope section.
15. The month alias deletes `month` from the search it is given. 16. New words: "Loading Results…", the period header has no operator, "Decisions" as the L2 title outside mode `month`.
17. (session 3) Test 14 is in-process: it pins `body: null` for modes month and none, and `out` only in the period bodies; the `view.py` diff and the byte-identity of the month, none and sites fixtures are the `git diff` below, not a test.
18. (session 3) The gates' E2 stub answers by range (`2026-09-01..2026-10-31` period, `2026-11-15..2026-11-21` none, anything else the one-month body), and the month read is World A's.
19. (session 3) `deep_dive_gates.cjs` takes `--path` (default the October Overview address); the base URL argument is unchanged.

**Parity (D-IAP.34 reach).** `git diff 7e8770cb0 -- backend/assetops_backend/deep_dive/view.py` is empty; across the D-IAP.34 commits the fixtures `period-month-*.json`, `period-none-*.json`,
`month-*.json` and `sites-*.json` are unchanged and only `period-period-2026-09-10.json` and `period-period-g-2026-09-10.json` gain `out` (`git diff --stat` of the fixture directory).

## 7. Risks

1. **Demo prebuilt responses.** `tools/demo_combined.py` (`prebuilt_routes`, `LINK_FORMS`) derives, from the story links `/portfolio?…`, the estate reads `/api/estate/portfolio` and `outcome-summary`.
   The Overview now reads `/api/portfolio/period` and `/api/portfolio/month` instead, which no prebuilt route answers. Not in the spec; not changed here. Needs a ruling before the next demo build.
2. The summary of `/api/estate/portfolio` grew two keys: stored `chain_response` bodies grow (spec §8, D-WK.16).
3. IA-P2's merge stales the world ladder's L2 `code` part (`tools/world.py` keys on `backend/assetops_backend`): the coordinator rebuilds the current rung once after the merge (spec §8). No migration.
4. Flaky under load: `s502OverviewFindingList`, `simulatorLabGate` (green in isolation).
