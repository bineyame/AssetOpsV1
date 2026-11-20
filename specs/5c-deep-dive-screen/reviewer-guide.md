# 5c reviewer guide

Architect (Claude), 2026-11-20, rev 1. Discovery review (W5): money figures on the screen the executive sees. Read
`spec.md`, `rulings.md`, 5b `rulings.md` D-5B.10 to D-5B.15, then the diff. Done means every question in spec §8
answers yes with evidence, every plant below fails its named test, and the G2 to G4 gates of
`Docs/design-system/uiux-guide.md` pass on the captures.

## What to check, and how

1. **The fixture is hand-written (W2).** `backend/tests/fixtures/5c/deep_dive_lakeside_2026-10.json` must match spec
   §3.5 string for string; a fixture produced by running `month_view` is High. Compare it to §3.5 yourself.
2. **One contribution (D-5B.12).** `grep -n "actual()\|targets()" backend/assetops_backend/deep_dive/` is empty;
   test 6's spies pass; the tiles, headline and totals read the bridge's root row.
3. **Words.** §2.4 by row; every money figure's word passes through `money_word`; the standing is read at
   `served.as_of` (`grep -n "known_at" deep_dive/read.py`).
4. **Stops.** Every reason of 5b's `SPLITS`/reasons has a sentence (test 7); RESIDUAL by kind first; the records'
   order is `RECORDS`.
5. **No browser arithmetic (D-5C.2).** Read `DeepDiveMonth.tsx`: no `Number(`, `parseFloat`, `toFixed`,
   `toLocaleString` or `Intl.NumberFormat` on a figure; only the bar's ratio.
6. **Mock fidelity.** Open vNEXT `#/portfolio` (Lakeside) beside the 1440 capture: headline, four tiles, the queue
   panel, the bridge with groups and "Show as table, by Site", "By outcome"; each difference is one of MD1 to MD7 and
   has a register row; an unlabelled one is High.
7. **Scale and phone.** 390 capture: one column, no page scroll, tables scroll in their own box, drawer full width.
   Height at 1440 ≤ 2,500 px with everything closed.
8. **Accessibility.** Drawer: dialog, labelled, focus to Close, Escape and scrim close, focus returns (test 11);
   words are text; the standing is a status.
9. **Seams.** `git diff main...HEAD --stat` lists only spec §0's files, the fixture, the tests and the packet;
   `structure/attribution/`, `structure_snapshot/` and `commercial/` untouched.
10. **Real data (D-5C.7).** Test 8's 401 case exists and uses `person_from_request`.

## Planted violations (each must fail the named test; the builder shows each failing once, in a scratch copy)

| # | Plant | Fails |
|---|---|---|
| P1 | the tiles read `snap.actual()` (883.00) | tests 3, 6 |
| P2 | `n` taken from the Sites with a structure, not `asked` | test 4(G) ("3 of 4 Sites") |
| P3 | the standing read live (`known_at` None) | test 9 (a statement after `as_of` changes the body) |
| P4 | the suffix added to a "Not available yet" money figure | test 5 |
| P5 | the disagreement only inside a drawer | test 10 |
| P6 | a carried O&M shown without "(estimate)" | tests 3, 10 |
| P7 | a step's value summed from Site rows instead of the portfolio row | test 4(D) (Mto out: −17.00 must hold, not −97.00) |
| P8 | the browser formats a figure (`toFixed`) | grep in check 5 and test 10 (strings differ) |
| P9 | "Recorded" for an emulated figure | test 5 |
| P10 | the real-data guard skipped | test 8 |
| P11 | a stop sentence without its records | test 7 |
| P12 | drawer focus not returned | test 11 |

## Not findings

Plan tiles, Decisions and Protect reading "Not available yet" (MD1, MD2, MD6). "Actions in hand" reading "Not
available yet" before 3C2 connects it. No trend lines (MD5).
