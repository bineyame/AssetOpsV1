# 4d mid-build questions

Questions raised during the build about something the spec did not fix. Count: 1 (reset at spec rev 2,
2026-11-20).

## Q1 (Implementer, 2026-11-20): the bridge's money carries five places, not two

- **What.** Spec §5's bridge literals are written `−600.00`, `−37.50`, `−412.50`, `−150.00`. The values are equal,
  but the `Decimal`s 5b returns are `−600.00000`, `−37.50000`, `−412.50000`, `−150.00000` (and `diesel_price` effect
  `0.00000`): 5b multiplies the litre gap (three places, D-4D.6) by the price (two), and 5b does not quantise a
  VOLUME or TERM effect. `fuel_cost` (−600.00) and the root (−562.00) keep two places, because they rest on records.
- **Why it is open.** 5b's own test helper compares money as `format(v, "f")` too (`check_shape`), so the literal
  fails as text and passes as a number. Fixing it needs a change to 5b (quantise effects) or to D-4D.6 (fewer
  places); both are outside 4d (§0, "5b unchanged").
- **What was built.** Nothing stopped. Test 6 compares the litre rows' scale, gap and effect as `Decimal`
  (`test_4d_litre_split.py::shape`), and `fuel_cost` and the root as text. A screen that prints the `Decimal` as
  is would show `-600.00000`; `5c` formats money, so the risk lands there.
- **Default proposed.** 5c formats every money figure to its currency's places (no 4d or 5b change). Architect to rule.
