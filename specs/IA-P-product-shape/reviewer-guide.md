# IA-P reviewer guide (rev 1, 2026-11-22)

Read `spec.md` (§2, §5, your part's §6 cards, §7, §10) and `rulings.md`.
- **Depth:** discovery (W5), one review per part: IA-P1 after P3, IA-P2 after P7.
- **Questions** go in `handshake.md` with the Implementer's pre-flight, one combined round (`.ai/RULES.md` §4). Mid-build
  questions go in `mid-build-questions.md`.
- **Mock:** vNEXT as built by IA-1, IA-2a and IA-2b1. Do not open `frontend/mockups/v69/` or `v71/`.

**IA-P1 done when:**
1. The rail equals spec §2.1 (R1).
2. `iaRouteMap.test.ts` passes, and fails on the `routemap` plant.
3. Every P1 to P3 alias lands with the range kept (R2).
4. The Portfolio has three tabs. `/portfolio` is the month, and `deep_dive_gates.cjs` passes at `/portfolio?month=2026-10`
   unchanged in its checks (H3).
5. Decisions, Findings and Actions are `HomeList`. Every P1 to P3 plant fails its named check.
6. The mid-build count is 0.

**IA-P2 done when:**
1. E1's World A literals hold exactly (test 1), and the sum check fails on the `sum` plant.
2. The Sites gap tile equals the Overview's tile 2 string (S1).
3. Six Site tabs show on MINI, COLD and EV (T1), and object pages have three-part crumbs (T2).
4. The inbox badge equals the Decisions waiting tile (W1).
5. Ctrl K works, and only live targets are indexed.
6. Every P4 to P7 plant fails.
7. SC-1's catalogue check and the hand-built guard are green.
8. The ladder note is in the packet.

**First checks.**
- **Diff scope.** `frontend/src`, `tools/iap_gates.cjs`, `tools/checks/navigation-truthfulness.ps1`, this folder and the
  register. In IA-P2 also: `backend/assetops_backend/deep_dive/`, `deep_dive_api.py`, `estate/portfolio.py`,
  `i18n/statements/en/portfolio_sites.py`, `backend/tests/test_iap_*`, `walk-layer4-v1.json`.
- **No reviewed read rewritten.** `git diff` of `estateClient.ts` is additive only (E0 types).
- **Independence (W2).** `homeLists.test` and `iap_gates.cjs` compute expected rows from the fixture bodies with their own
  code, never by calling `homeListModel` or the defs (only `homeListModel.test`'s synthetic block calls the model).

**Probes.**
- **Q1 Nothing is lost.** Open each "Current address" in spec §2.4 with `?from=…&to=…`. It lands on the named home, and the
  range survives. Old bookmarks for `/portfolio/act-first?lens=cost`, `/operational-records` and `/portfolio/month?month=2026-10`
  all work.
- **Q2 One period per page.** On `/portfolio` the top bar names the month (SR-4c), and changing the range does not change
  the month figures. Go to `/decisions` and the range is still the one you set. "View all" from the Overview's rows shows
  the same rows.
- **Q3 One figure.** No figure on the Overview appears with a different value elsewhere for the same quantity: Contribution
  and Gap against `/sites` and Outcomes. The range category cards appear only on Outcomes.
- **Q4 The list grammar.** Pick a facet, a sort and a search: the address changes, focus stays, Back steps through them, and
  a fresh tab restores the view. Tab gives one stop per row. At 390 there is no sideways scroll.
- **Q5 Honest gaps.** Decisions shows Due and Who decides as "Not available yet". "For you" is not available yet. Plan is
  unavailable in the rail. A NO_SNAPSHOT database shows the month's state text, with no invented figure.
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

**Risks.**
- `loadAllPages` on a large estate (latency): check the 1,000-row line renders.
- The 5c test edits must touch only the decisions-panel assertions.
- `navigation-truthfulness.ps1` re-pinning can go vacuous: run its planted extra live item.
- The P5 parity test may fail for cold or EV. That is a stop and a `SPEC_AMBIGUITY`, not a builder's choice.
