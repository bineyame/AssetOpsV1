# 5a F1 review (fresh Claude, head 746b4c265)

Verdict: ACCEPT WITH FIXES (no High or Medium; two Lows, non-blocking).

Checks run (own scratch copy of the head, PYTHONPATH on that tree):
- Focused run via heavy-slot --db: test_5a_targets + test_4b1_stated_nodes, 153 passed.
- Scratch copy of 5a, 4b1, 3b3 evaluate, 5b attribution tests: 282 passed, 1 skipped.
- Plants: FP1 (rule 4 back to .money) fails F1-1; FP2 (has_money_dimension = is_money) fails F1-2, F1-3 and others
  (4 failed); FP3 (no currency check) fails F1-1 and F1-3. Own plant: records_v1 `budget_currency` back to is_money
  fails F1-2; evaluate.py STRUCTURE_CURRENCY back to is_money fails 3b3 t5 (tariff case).
- necessary_l reads 2300 / 700 / 300 at Kisiwa / Kobo / Mto (F1-2 asserts it, blocked == {}, tariff and diesel_price
  DECLARED USD, necessary_l ESTIMATED from assumption:main-factor:fuel_cost); diesel_l with a currency is still
  CURRENCY_ON_QUANTITY (F1-1).

Predicate: Unit.has_money_dimension is the single check in records_v1, evaluate.py (private copy removed), lines.py
rule 4, read.py (3 sites), rules.py solve_main and 5b bridge.py (private copy removed). grep finds no remaining
inline MONEY-exponent test outside units.py.

Exact-money kept (judged):
- money.py step 4 (one currency over AMOUNT lines): correct. It sums commercial AMOUNT lines of money kinds; no rate
  leaf is a commercial sum. Different question, not the defect.
- check.py homes (_money_home) and _stated (is_money or KWH): correct; sums/stated nodes are exact-money by design.
- bridge._is_price (MONEY^1 among exponents and not exact money): correct and deliberate (it means "money per unit").

Findings
- Low (test hygiene) backend/tests/test_4b1_stated_nodes.py ~line 235: the edit deleted the `def
  test_s11a_the_registry_yields_money_and_non_money_leaves():` line. Its body (and a redundant `_check_leaf` import)
  now trails test_s11a_every_valued_part_with_empty_origins_is_refused, so that sanity test no longer exists by name
  and its assertions run once per parameter. Nothing is weakened in what is asserted, but restore the def line.
- Low (coverage) The bridge.py call site and the three latent read.py / rules.py sites are not caught by any test:
  reverting each to is_money leaves 5a, 5b, 3b3 and 4b1 green. Spec calls read.py/rules.py latent and the spec's plants
  do not require it; a rate leaf with LEAK_ZERO/MAIN, or a 5b currency-mismatch on a price, would cover them. Backlog.

Could not verify: full suites, frontend, check-architecture (not run; focused scope only). Residual risk: none beyond
the Lows; blanks at all three Sites now read budget figures only if the live budget export carries the currency, as
D-DS4.27 states.
