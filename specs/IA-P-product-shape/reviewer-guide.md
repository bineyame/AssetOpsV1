# IA-P reviewer guide (rev 2, 2026-11-22: the Overview follows the range)

Read `spec.md` (§2, §3, §5, your part's §6 cards, §7, §10), `spec-period.md` (P.1, then P.2 to P.7 for IA-P1 and P.8 for
IA-P2) and `rulings.md` (D-IAP.15 on for rev 2).
- **Depth:** discovery (W5), one review per part: IA-P1 after P3b, IA-P2 after P7. Both
  parts add money figures and an endpoint (E2 in IA-P1; E0 and E1 in IA-P2).
- **Questions** go in `handshake.md` with the Implementer's pre-flight, one combined round (`.ai/RULES.md` §4). Mid-build
  questions go in `mid-build-questions.md`.
- **Mock:** vNEXT as built by IA-1, IA-2a and IA-2b1. Do not open `frontend/mockups/v69/` or `v71/`.

**IA-P1 done when:**
1. The rail equals spec §2.1 (R1).
2. `iaRouteMap.test.ts` passes, and fails on the `routemap` plant.
3. Every P1 to P3 alias lands with the range kept (R2).
4. The Portfolio has three tabs. `/portfolio` follows the range in all three modes (H3 to H6), and `deep_dive_gates.cjs`
   passes at `/portfolio?from=2026-10-01&to=2026-10-31` unchanged in its checks (H3).
5. E2's World P literals hold exactly (`spec-period.md` P.7 test 2), each month row's gap is that month's tile 2 (test 3),
   and the committed fixtures are current (test 10).
6. Decisions, Findings and Actions are `HomeList`. Every P1 to P3b plant fails its named check.
7. `view.py` and the 5c backend tests are unchanged, and the mid-build count is 0.

**IA-P2 done when:**
1. E1's World A and World P literals hold exactly (P.8 tests 1 and 7), and the sum check fails on the `sum` plant.
2. The Sites gap tile equals the Overview's tile 2 string on a one-month and a two-month range (S1).
3. Six Site tabs show on MINI, COLD and EV (T1), and object pages have three-part crumbs (T2).
4. The inbox badge equals the Decisions waiting tile (W1).
5. Ctrl K works, and only live targets are indexed.
6. Every P4 to P7 plant fails.
7. SC-1's catalogue check and the hand-built guard are green.
8. The ladder note is in the packet.

**First checks.**
- **Diff scope.** `frontend/src`, `tools/iap_gates.cjs`, `tools/deep_dive_gates.cjs`, `tools/checks/navigation-truthfulness.ps1`,
  this folder, the register and the DDR runbook's S7 line. In IA-P1 also: `backend/assetops_backend/deep_dive/period.py`
  and `read.py`, `deep_dive_api.py`, `i18n/statements/en/portfolio_period.py` and
  `backend/tests/test_iap_portfolio_period.py`. In IA-P2 also: `deep_dive/sites.py`, `estate/portfolio.py`,
  `i18n/statements/en/portfolio_sites.py`, `backend/tests/test_iap_*` and `walk-layer4-v1.json`.
- **No reviewed read rewritten.** `git diff` of `estateClient.ts` is additive only (E0 types).
- **Independence (W2).** `homeLists.test` and `iap_gates.cjs` compute expected rows from the fixture bodies with their own
  code, never by calling `homeListModel` or the defs (only `homeListModel.test`'s synthetic block calls the model).

**Probes.**
- **Q1 Nothing is lost.** Open each "Current address" in spec §2.4 with `?from=…&to=…`. It lands on the named home, and the
  range survives. Old bookmarks for `/portfolio/act-first?lens=cost`, `/operational-records` and `/portfolio/month?month=2026-10`
  all work.
- **Q2 The Overview follows the range.** Set "Last month": the month shows, and the bar says "All pages". Set a custom
  two-month range: the totals are the sum of the two months' tile 2s, and each "Month by month" row opens its month. Set
  "Last 7 days": no figure shows, the notes say why, and "Show {month}" opens the month. Set 1 October to 21 November:
  October shows, the November note is there, and the bar says the page shows part of the range. In every case the request
  is E2 for the address's range (compare two ranges' requests), and "View all" from the Overview's rows shows the same rows
  on `/decisions`.
- **Q3 One figure.** No figure on the Overview appears with a different value elsewhere for the same quantity and range:
  Contribution and Gap against `/sites` and Outcomes, and each month row against that month's own Overview. The range
  category cards appear only on Outcomes.
- **Q4 The list grammar.** Pick a facet, a sort and a search: the address changes, focus stays, Back steps through them, and
  a fresh tab restores the view. Tab gives one stop per row. At 390 there is no sideways scroll.
- **Q5 Honest gaps.** Decisions shows Due and Who decides as "Not available yet". "For you" is not available yet. Plan is
  unavailable in the rail. A NO_SNAPSHOT database shows mode `none` with the missing month named, and no invented figure.
- **Q6 Object pages.** A Finding's Recommendation lights Decisions, its Evidence lights Findings, and an Action lights
  Actions. None draws the Site tab row, and each crumb's Site link opens the Site Overview.

**Class sweeps (W6).**
- Any tab or link that drops the range.
- Any count beside a list that is not the list's length or the server's total.
- Any figure compared, sorted or summed in the browser.
- Any row with a second interactive element.
- Any route not in the route map.
- Any unlabelled departure from vNEXT.
- Any typed month or hand-built sentence.
- Any range page missing from `RANGE_PAGES`/`FILLED_PAGES` (D-IAP.19), and any date or month arithmetic in the browser
  beyond `monthDays` for the alias.

**Risks.**
- `loadAllPages` on a large estate (latency): check the 1,000-row line renders.
- E2 reads one snapshot and one standing per month (up to 24): time a 12-month range on the demo store.
- Ladder: P3a stales the world key at IA-P1's merge, not only P4 (D-IAP.22).
- The 5c test edits must touch only the decisions-panel assertions.
- `navigation-truthfulness.ps1` re-pinning can go vacuous: run its planted extra live item.
- The P5 parity test may fail for cold or EV. That is a stop and a `SPEC_AMBIGUITY`, not a builder's choice.
