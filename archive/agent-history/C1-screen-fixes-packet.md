# C1 packet: PB-5, PB-6, PB-8, RM-1, RM-2 (branch task/C1-screen-fixes, from db447d0e0)

(File name note: `.agent/C1-packet.md` already holds the older E4-C1 packet, so this one is C1-screen-fixes-packet.md.)

Commits (one per card): PB-8, PB-5, PB-6a (cold asset id), PB-6b/c (EV Financials, cohort words), RM-1 backend, RM-1 frontend, RM-2, tsc fixes.
Nothing was already done on main.

## PB-8 Fuel tab loading
`useFuelNights` (MiniFuelNights.tsx) now returns `"loading" | nights | null`; MiniPerformance shows `MINI_LOADING` while loading, hour mode only for none/failed. Test: miniFuelNights.test.tsx "PB-8" (failed before: "Fuel balance: Unknown" showed).

## PB-5 Kisiwa feeder legend
`deviceNames` (Foundation `display_name` by device id, built in SiteDetailFrame) -> SiteOverview -> SiteWindowOverview Timeline label, falling back to `idWords`. Test: s5SiteWindowOverview "PB-5" (Households / Cold store / Water pump meter). Kobo's names come from the same Foundation names; Kobo output is not otherwise changed.

## PB-6
- Cold Health asset cell: id moved behind a closed "Technical details" (was inline, and under "Full ID"). coldHealthDepth test updated.
- EV Financials: no-consequence row "Tariff not declared" -> "No analysed charging session in this window"; the status strip no longer starts with an empty " USD · selected window" / "Currency not declared" (currency lead only when an estimate exists). evSiteMoneyRoutes tests.
- AMBIGUOUS_COHORT split: `limitationWords(code, items)`; the successive-epoch reason reads "Readings for this day came from two separate recording sessions of one source; they are not joined, so the day is not analysed". Overlap case unchanged. 4 call sites pass items. Test: pb6CohortWords.test.ts.

## RM-1 changed literals (before -> after). None reads as an error; each names what is missing.
Backend (outcomes/catalogue.py, site_outcomes/cold|ev|mini.py; goldens regenerated, their diff is only these):
| row | before | after |
|---|---|---|
| MG-6 cash | no billing or payment records | billing and payment records are not connected yet |
| MG-3 earnings | needs site income, operating cost and capital records | site income, operating cost and capital records are not connected yet |
| Kobo cash/earnings contributors | Not available yet · no billing or payment records / · needs site income... | Billing and payment records are not connected yet / Site income, operating cost and capital records are not connected yet |
| EV-6 | no settlement records | billing records are not connected yet |
| EV-2 / EV Optimize row | needs odometer readings; a tariff estimate exists in Financials | odometer readings are not connected yet; a tariff estimate exists in Financials |
| EV unpriced row | Energy cost per km needs odometer readings and a published charging tariff | Odometer readings are not connected yet, and no charging tariff is published for this window |
| CC-2 / Cold Grow row | needs occupancy, storage contract, income and sales records | occupancy, storage contract, income and sales records are not connected yet |
| CC-4 | needs market and sales records | market and sales records are not connected yet |
| Cold repair cost | No repair or call-out cost recorded; No cost on work record X; "repair cost is not recorded" | Repair and call-out costs are not connected yet; Repair costs are not connected yet; work record X has no cost; "repair costs are not connected yet" |
| Cold Protect subline | Compressor and backup condition are not assessed | ... need a wear model, which is not connected yet |
| Cold storage level | Not available yet · no storage contract recorded | Storage contracts are not connected yet |
| Cold loading/door | Not available yet | Loading and door records are not connected yet |
| EV settlement | Not available yet · no settlement records (+ assure variant) | Billing records are not connected yet (+ " · reconciles the revenue shown under Grow revenue") |
| EV warranty | Not available yet · no warranty record | Warranty records are not connected yet |
| EV roster | Not available yet · no bus roster connected | Bus rosters are not connected yet |
| EV departures | which departures were affected is not known yet | which departures were affected needs bus rosters, which are not connected yet |
| Kobo Protect headline/subline | Battery and generator condition are/is not assessed | ... need(s) a wear model, which is not connected yet |

Frontend (ROADMAP_WORDS table in ui/productWords.ts; UnavailableInline/UnavailableLinkEntry take `roadmap`):
| place | before | after |
|---|---|---|
| Cold findings scope note | Cold-chain Findings are not in the global Findings list | Cold-room findings are listed here; the estate list adds them later |
| EV findings scope note | EV charging Findings are not in the global Findings list | EV charging findings are listed here; the estate list adds them later |
| Cold Work note | Global Actions does not include cold-chain Actions yet. | Cold-room actions are listed here; the estate list adds them later. |
| EV Work note | Global Actions does not include EV Actions yet. | EV charging actions are listed here; the estate list adds them later. |
| Manage in Findings (cold, EV) | Manage in Findings · Not available yet | Managing findings from this list is coming |
| Review recommendation (EV x3) | Review recommendation · Not available yet | Reviewing a recommendation needs sign-in, which is coming |
| EV Portfolio roll-up | Portfolio roll-up · Not available yet | Rolling EV money up to the estate is coming |
| EV Collections card | Not recorded / No accepted payment record | Not connected yet / Payment records are not connected yet |
| EV Evidence billing row | No payment feed | Payment records are not connected yet |

Guard: ui/__tests__/roadmapWords.test.ts (each line ends coming / later / not connected yet; no error/fail/code).

## RM-2 (revised after coordinator correction)
Derived from data, not Site codes: `siteSupportsLenses(rows)` is true when a row of the Site's own Findings read carries a non-empty `lens_flags`. The mini-grid index draws the chips (unchanged) only then; Cold and EV never draw them (`lenses={null}`, EvFindingIndex no longer renders them). Tests: Kobo-type (rows with a lens) keeps All/Cost/Risks/Opportunities, Kisiwa-type (no lens flags) none (s404SiteFindingIndex); Cold (coldFindingIndex), EV (evFindingIndex), mini fixtures (w301, miniDecisions); unit (rm2LensChips).
Caveat: no Site supplies lens destinations today, so Kobo's chips remain "Not available yet" chips; and a Kobo day whose Findings carry no lens flag would also show no row.

## Fix round (review REJECT on RM-2)
- Row-derived `siteSupportsLenses` removed. The Site summary (`sites_api.site_summary`) now carries `lenses_supported`, declared by configuration: a MINIGRID Site whose Foundation declares a LOAD with `supply-use = PRODUCTIVE` (Kobo's mill; Kisiwa declares none; Cold/EV never; a registered Site with no effective Foundation: false). Frontend: `SiteSummary.lenses_supported`, `SiteFindingIndex lensesSupported` prop; the row no longer depends on the Findings rows or read status. (Wire key avoids the substring "findings", which test_sites_api forbids.)
- Tests: s404 Kobo-type keeps chips with Findings, with zero Findings and on a refused read; Kisiwa-type hides them with real `["COST"]` flags; backend `test_c1_lenses_supported.py`. Cold/EV unchanged.
- Low fixes: stale comment reworded; EV Protect line now "Charger condition needs a wear model, which is not connected yet" (ev.py, ev_2026-10-27.json golden, test_out_b3_cold_ev).
- Caveat: the real Kobo Foundation must declare `supply-use` (demo configuration); not verified against a live DB here.

## Not done
- C17 (Due dates), E6 and shared `target.none` ("No target set yet": backlog per card), C13 (kept honest per card).
- F5b tab-row "Not available yet" entries are unchanged (outside C1).
- `test_out_c3_repeat_visits_postgres.py` and `test_out_c4_ev_warnings_postgres.py`: run against scratch DB assetops_c1_test (dropped after): 1 passed, 0 skipped each.

## Checks
Frontend vitest, one file at a time, on every touched file; `tsc --noEmit`; backend focused: test_out_*, test_polish_*, test_ch5*, test_ch6*, test_e3b*, test_idx_*, w601b. check-architecture result in the final report.
