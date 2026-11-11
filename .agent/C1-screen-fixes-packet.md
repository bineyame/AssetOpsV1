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

## RM-2
`LensChips` returns nothing when no lens has an href. Per-type tests: Cold (coldFindingIndex), EV (evFindingIndex), mini-grid (w301EstateShellRoutes, s404, miniDecisions), component (rm2LensChips, including that the row returns when a lens is supplied).
**Review note:** the mini-grid index is one component, so Kobo's lens chips are hidden too (no Site supplies a lens href). Kobo was not in the named list; if Kobo must keep them, a per-Site flag is needed.

## Not done
- C17 (Due dates), E6 and shared `target.none` ("No target set yet": backlog per card), C13 (kept honest per card).
- F5b tab-row "Not available yet" entries are unchanged (outside C1).
- `test_out_c3_repeat_visits_postgres.py` and `test_out_c4_ev_warnings_postgres.py` need a database and were not run (the first has its subline literal updated).

## Checks
Frontend vitest, one file at a time, on every touched file; `tsc --noEmit`; backend focused: test_out_*, test_polish_*, test_ch5*, test_ch6*, test_e3b*, test_idx_*, w601b. check-architecture result in the final report.
