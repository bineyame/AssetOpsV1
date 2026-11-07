# Review: TEST-drift (task/TEST-drift-main) vs DRIFT-R1

Verdict: ACCEPT. No findings.

Checks run (no DB): test_ch5c2_clock_guard, test_ch5a1_scope, test_out_d2_objectives, test_ch5a2_contract with the prescribed PYTHONPATH: 73 passed. grep for `outcome-status/3` in backend/tests: none.

1. Drift fixes: scope fake adds `prefetched=None` (matches _window_read call); `outcome-status/4` expectation matches status.py:16; stale `declare.work` entry replaced. Each minimal, no assertion weakened.
2. Product change: only the status.py module docstring line (/3 -> /4).
3. Golden: only estate_week_2026-10-25.json changed (+23 lines), only `cards.OPTIMIZE_COST` added, placed in key order. Values match CH5d1-R 2.1 one-priced-Site row: text "3.31 to 3.97 USD" byte-equal to claim text, small "possible extra fuel cost", detail "At Kobo · not added across sites", tone amber, claim unchanged, days_line null, missing false. read.py:767 uses cost.detail.one / cost.basis.money.
4. Clock guard: stronger, not weaker.
   - String defaults of function/lambda args (args.defaults and non-None kw_defaults) matching CLOCK_SQL are now flagged without a keyword.
   - `_insert_statement` allowlist entry re-added with reason, keyed by (module, qualname).
   - PY_CLOCK_ALLOWLIST keyed (module, function) with the single financials.recompute._utc_now entry and reason; violations() skips only that exact key.
   - Stale check now covers both allowlists.
   - Planted tests are non-vacuous: `def f(c, at="now()")` and lambda default fail; a non-default prose literal stays quiet; datetime.now() in `_utc_now` of a non-allowlisted module fails; another function in the allowlisted module fails.

Residual (Low, not a finding): the default scan only sees string-constant defaults, not computed ones; acceptable per ruling.
