
## Fix F1 (D-DS4.27, spec section 11)

- One predicate: `Unit.has_money_dimension` (`contracts/.../canonical/units.py`); `is_money` unchanged (exactly MONEY^1). Used by the
  canonical `budget_currency` rule, `evaluate.py`, `targets/lines.py` rule 4 (the fix), `targets/read.py`, `targets/rules.py`
  `solve_main`, and 5b's `attribution/bridge.py` (it carried a second copy of the evaluator's `_money_dimension`; removed, as were
  4b1's test imports of the evaluator's). `money.py` step 4, `check.py` homes and bridge `_is_price` mean "exactly money" or
  "MONEY^1 among exponents" and are kept.
- Tests F1-1 to F1-3 in `backend/tests/test_5a_targets.py`. F1-2 uses the in-memory world (not a fake line reader) and asserts
  `necessary_l` 2300 / 700 / 300 at Kisiwa / Kobo / Mto with DECLARED price lines.
- Plants shown to fail: FP1 (rule 4 back to `.money`): F1-1, F1-2, F1-3. FP2 (`has_money_dimension` = `is_money`): F1-1, F1-2, F1-3 and
  2a `test_t5`. FP3 (no currency check): the two 2c tests, F1-1, F1-3.
- Nothing correctly refused is now accepted: a currency on `diesel_l` stays CURRENCY_ON_QUANTITY (F1-1, 2c).
- Review-fix round: restored the deleted `def test_s11a_the_registry_yields_money_and_non_money_leaves` in `test_4b1_stated_nodes.py`; added
  F1-4 (`solve_main`), F1-5/F1-6 (`read.py` LEAK_ZERO and MAIN sites, rules patched onto `tariff`) in `test_5a_targets.py` and a bridge
  currency-mismatch test on a price leaf in `test_5b_attribution.py`. Each revert of its site to `is_money` was run and fails its test.
