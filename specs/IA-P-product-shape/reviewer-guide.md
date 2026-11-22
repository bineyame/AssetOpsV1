# IA-P reviewer guide (rev 3, 2026-11-22: handshake answered; three parts)

Read `spec.md` (§2, §3, §5, your part's §6 cards, §7, §10), `spec-period.md` (P.1, then P.2 to P.7 for IA-P1 and P.8 for
IA-P2) `rulings.md` (D-IAP.15 on for rev 2, D-IAP.24 on for rev 3), and `handshake.md` "Answers (Architect)" (binding).
The parts are IA-P1 (P1, P0, P2), IA-P2 (P3a, P3b, P4a) and IA-P3 (P4b, P5, P6, P7).
- **Depth:** discovery (W5), one review per part: IA-P1 after P2, IA-P2 after P4a and IA-P3 after
  P7. IA-P1 sweeps every range read; IA-P2 adds E2, E0 and E1; IA-P3 renders their figures.
- **Questions** go in `handshake.md` with the Implementer's pre-flight, one combined round (`.ai/RULES.md` §4). Mid-build
  questions go in `mid-build-questions.md`.
- **Mock:** vNEXT as built by IA-1, IA-2a and IA-2b1. Do not open `frontend/mockups/v69/` or `v71/`.

**IA-P1 done when** (P1, P0, P2):
1. The rail equals spec §2.1 (R1), and `iaRouteMap.test.ts` fails both ways: on the `routemap` plant and on the `alias`
   plant (D-IAP.27).
2. Every P1 and P2 alias lands with the range kept (R2).
3. On a 61-day range a non-whole page sends the 31-day window and the bar says so, and links keep the whole range (R7, R8).
   `noRawRangeReads` fails on the `rawread` plant.
4. Decisions, Findings and Actions are `HomeList`. `MONITOR` rows read "Being watched" and are not counted as waiting.
5. Every P1, P0 and P2 plant fails its named check, and the mid-build count is 0.

**IA-P2 done when** (P3a, P3b, P4a):
1. The Portfolio has three tabs. `/portfolio` follows the range in all three modes (H3 to H6), and `deep_dive_gates.cjs`
   passes at the October range unchanged in its checks.
2. E2's World P and World G literals hold (P.7 tests 2 and 11), each month row's gap is that month's tile 2 (test 3), and
   the fixtures are current (test 10).
3. E1's World A, World G and World P literals hold (P.8 tests 1, 2 and 7), the sum check fails on the `sum` plant, and
   World X degrades (4b).
4. `view.py` and the 5c backend tests are unchanged. SC-1's checks are green, and the ladder note is in the packet.

**IA-P3 done when** (P4b, P5, P6, P7):
1. The Sites gap tile equals the Overview's tile 2 on a one-month and a two-month range (S1), and reads "Not available yet"
   under a facet (MD-IAP-13).
2. Thika is named on the Overview, Outcomes and the Sites list (the matrix test).
3. There are six Site tabs on MINI, COLD and EV (T1), and object pages have three-part crumbs (T2).
4. The inbox badge equals the Decisions waiting tile (W1). Ctrl K works, and only live targets are indexed.
5. Every P4b to P7 plant fails, and the mid-build count is 0.

**First checks.**
- **Diff scope.** `frontend/src`, `tools/iap_gates.cjs`, `tools/deep_dive_gates.cjs`, `tools/checks/navigation-truthfulness.ps1`,
  this folder, the register and the DDR runbook's S7 line. In IA-P2 also: `backend/assetops_backend/deep_dive/period.py`
  and `read.py`, `deep_dive_api.py`, `i18n/statements/en/portfolio_period.py` and
  `backend/tests/test_iap_portfolio_period.py`, `deep_dive/sites.py`, `estate/portfolio.py`,
  `i18n/statements/en/portfolio_sites.py` and `backend/tests/test_iap_*`. In IA-P3 also: `walk-layer4-v1.json` and
  `backend/tests/test_wk_walk_world.py` (I13). In IA-P1: every range read's request builder (the P0 sweep).
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
