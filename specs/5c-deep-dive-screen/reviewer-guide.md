# 5c reviewer guide

Architect (Claude), 2026-11-20, rev 2 (handshake round 1 answered). Discovery review (W5): money figures on the screen the executive sees. Read
`spec.md`, `rulings.md`, 5b `rulings.md` D-5B.10 to D-5B.15, then the diff. Done means every question in spec §8
answers yes with evidence, every plant below fails its named test, and the G2 to G4 gates of
`Docs/design-system/uiux-guide.md` pass on the captures.

## What to check, and how

1. **The fixture is hand-written (W2).** `backend/tests/fixtures/5c/deep_dive_lakeside_2026-10.json` must match spec
   §3.5 string for string; a fixture produced by running `month_view` is High. Compare it to §3.5 yourself.
2. **One contribution (D-5B.12, D-5C.13).** `grep -n "actual()\|targets()" backend/assetops_backend/deep_dive/` is
   empty; test 6's spies pass; World A's JSON has no "$1,693.00" and D's tiles, headline, totals and cards no
   "$883.00".
3. **Words.** §2.4 by row; every money figure's word, each driver's included, passes through `money_word` with the
   organisation's standing, read once at `served.as_of` (`grep -n "known_at" deep_dive/read.py`); the headline names
   only a heading with the gap's sign (D-5C.15).
4. **Stops.** Every reason of 5b's `SPLITS`/reasons has a sentence (test 7); RESIDUAL by kind first; the records'
   order is `RECORDS`.
5. **No browser arithmetic (D-5C.2).** Read `DeepDiveMonth.tsx`: no `Number(`, `parseFloat`, `toFixed`,
   `toLocaleString` or `Intl.NumberFormat` on a figure; only the bar's ratio.
6. **Mock fidelity.** Open vNEXT `#/portfolio` (Lakeside) beside the 1440 capture: headline, four tiles, the queue
   panel, the bridge with groups and "Show as table, by Site", "By outcome"; each difference is one of MD1 to MD9 and
   has a register row; an unlabelled one is High.
7. **Hub gates and G3 (D-5C.14).** Run `tools/deep_dive_gates.cjs` yourself on the built page; open all six G3 shots
   and the 390 drawer shot; read the `measure_screen.cjs` lines. Count the blocks yourself at 1440 (6 at most), the
   headline's lines at 1280, and check L1 above the fold. Check that each of the eight plants made the script fail.
8. **Accessibility.** Drawer: dialog, labelled, focus to Close, Escape and scrim close, focus returns (test 11);
   words are text; the status line is a status.
9. **Seams.** `git diff main...HEAD --stat` lists only spec §0's files, the fixture, the tests and the packet;
   `structure/attribution/`, `structure_snapshot/` and `commercial/` untouched.
10. **Real data (D-5C.7).** Test 8's 401 case exists and uses `person_from_request`.

## Planted violations (each must fail the named test; the builder shows each failing once, in a scratch copy)

| # | Plant | Fails |
|---|---|---|
| P1 | the tiles read `snap.actual()` | tests 3, 4(D) and 6 ("$1,693.00" in A; "$883.00" in D's tile) |
| P2 | `n` taken from the Sites with a structure, not `asked` | test 4(G) ("3 of 4 Sites") |
| P3 | the standing read live (`known_at` None) | test 9(b) (B's words at 12:30Z) |
| P4 | the suffix added to a "Not available yet" money figure | test 5 |
| P5 | the disagreement only inside a drawer | test 10 |
| P6 | a carried O&M shown without "(estimate)" | tests 3, 10 |
| P7 | (dropped in rev 2: the two paths cannot differ for one currency; handshake R5) | — |
| P8 | the browser formats a figure (`toFixed`) | grep in check 5 and test 10 (strings differ) |
| P9 | "Recorded" for an emulated figure | test 5 |
| P10 | the real-data guard skipped | test 8 |
| P11 | a stop sentence without its records | test 7 |
| P12 | drawer focus not returned | test 11 |
| P13 | a driver's word omitted | test 4(H) |
| P14 | the headline names the larger heading whatever its sign | test 4 (lead vectors L1, L2) |
| P15 | `money` zero as "$0.00" for every currency | test 2 ("KES 0.00") |
| P16 | Actions shown oldest first or uncapped | test 4(C4) |
| P17 | the disagreement sentence with `computed` None prints "None" | test 4(A2) |
| P18 | the status line without the disagreement clause | tests 3 and 10; gates `status` |
| P19 | a seventh block in a level region | test 15 (gates `block`) |
| P20 | a headline over 2 lines, L1 below the fold, or the hub over 2,500 px | test 15 (gates `headline`, `fold`, `height`) |
| P21 | a level region missing, horizontal scroll at 390, or a font size off the scale | test 15 (gates `levels`, `scroll`, `lint`) |

## Not findings

Plan tiles, Decisions and Protect reading "Not available yet" (MD1, MD2, MD6). "Actions in hand" reading "Not
available yet" before 3C2 connects it; the connected case is 3C2's review. No trend lines (MD5). The status line in
L1 and the reconciliation sentence in the Assure drawer (MD8, flagged to the owner). A 5b or 5c rule change not
marking figures out of date (D-5C.18).
