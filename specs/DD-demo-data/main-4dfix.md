# main 4d / 5c / 3b fix (2026-11-23)

Branch `fix/main-4d-litre`, from main 7c47ec357. Test-side re-pins only; no source code changed. No assertion weakened.

## Cause (one for all)
DD3b3 `b9afc1a04` (M rev 16.20, D-DD.150-152) re-pinned the commercial fixture `money_leaves_lakeside.json`: Kobo's October fuel
is 634 L, 792.50 (400 + 234 delivered), no longer 1,180 L, 1,475.00. DD3c `d24539e37` (4d fixtures build one UnitFuel) and DD3b
`138e09045` (Kisiwa 903 L / 1,173.90, M rev 16.23) re-pinned 4b/5b but not 4d, 5c, 4b1. Each file that reads the 5b world kept
the old figures. (b) throughout: the figures moved by ruling; the 4d bridge needed a litre world that adds up to the record.

## 4d (2 tests), (b)
`test_6_kobo_fuel_cost_splits_into_the_three_litre_leaves`, `test_6_the_portfolio`. The bridge's litre inputs (1,180 L) no longer
equalled the record, so the fuel node was `NOT_SPLIT RECORD_AND_FACTORS_DIFFER`. New bridge-only world `kobo_record_world()`
(634 L tank balance, necessary 400, candidate 120, unexplained 114; same 5 L/h model, same shape). Re-pinned: root gap 120.50,
fuel effect +82.50, diesel 634 L vs 700 (gap -66), leaves 400/120/114, portfolio fuel effect +2,233.60. KOBO-OCT (spec 5) for
tests 1-5, 7-10 untouched.

## 5c (7 tests), (b)
World A moved with the 5b fixtures: contribution 4,431.60 (was 1,443.00), gap +2,136.60 above target, fuel effect +2,233.60
(Kobo +82.50, Kisiwa +1,816.10, Mto +335.00), bars 4.34 / 100.00 raises. `deep_dive_lakeside_2026-10.json` regenerated from the
view (figure lines only); `make_screen_worlds.py` regenerated World H and X. World D (no Mto): 3,261.60, gap +1,881.60. Plant P1
and the "$883.00" absence check re-pinned to the new wrong figures (2,735.50; 1,565.50). `test_4_i` sign "-KES" to "+KES" (the
test pins currency, not sign). The standing's canned figures (accounts 5,100 vs records 4,995) moved to 2,100.00 vs 2,006.40
(`NOT_MATCHED`, fixture, 5c postgres test: S1 2,100.00, S2 2,010.00 inside 1%). The frontend `DeepDiveMonth.test.tsx` figure pins
moved with the fixtures.

## 4b1 (3 tests, found on the way), (b)
Kobo contribution 883.00 to 1,565.50, 925.00 to 1,607.50 (same cause).

## 3b1 t1 and 3b3 t6, (b), one-line version re-pin
Still failing on main: the registry reads `dispatch-3.3` (D-0K4.10, 0K4e); the manifest pack
(`demo-site-scenario-manifest.yaml`, owner pack, not edited) still names `dispatch-3.2`. Both tests now compare against the
manifest kind with the version replaced, citing D-0K4.10.

## Not done, needs a decision (failing on main before this fix, same cause)
`test_iap_portfolio_sites.py` (tests 1, 6, 7, 8, 9) and `test_iap_portfolio_period.py` (tests 2, 10): they pin the old World A
(Sites below target, driver headings, -852, row order). With the DD figures every Site is above target, so tests 6/8 lose their
premise (a Site below target, Kisiwa's driver heading); that is a scenario choice, not a re-pin. `IAP_WRITE_FIXTURES=1`
regenerates the `fixtures/iap` files, but then 9 frontend `sitesList.test.tsx` tests (order, "Below target", headline) need
re-pinning; I reverted that. Consequence: frontend `sitesList.test.tsx` "World A, October" now fails on its one-figure tie
(E1 fixture gap tile -$852.00 vs World A +$2,136.60); it passed on main only because the two fixtures agreed on the old figure.
Also failing in `src/shell` (not touched, not this cause): s502OverviewFindingList (2), siteRangeMatrix (3), sr2RequestUrls (1).

## Evidence
`/opt/assetecon/evidence/simfix/` (4d-before.log, after.log, 3b.log, fe2.log). Guards: architecture, agent workflow, statement
catalogue (+ self-test 78 of 78) pass.
