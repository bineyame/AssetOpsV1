# FX-KOBO-V3 review

Verdict: ACCEPT with one Medium finding (fail-open on missing schema), recommended fix before the v4 build is relied on.

Tests run (one file at a time, worktree PYTHONPATH): test_demo_combined_finish_rows 69 passed; test_demo_story_days 92 passed; test_demo_combined_mill 15 passed. Not run: guards A/W/V/N, build.

1. Medium, tools/demo_combined_finish.py load() + demo_combined_rows.gap_gated: `days.json["schema"]` missing/unreadable gives `{}`, so `gap_gated` is False and WK-GAP returns `gated: false` and passes, even on a v4 build. Fail-open. In practice demo_combined.py:873 always writes `schema` from the days doc (KeyError otherwise), so the default v4 build cannot reach this path. Still, the test pins the fail-open behaviour (`gap_gated({})` is False). Fix: in wkgap, raise or gate when `days_schema` has no readable version (only an explicit version < 4 should be ungated).
2. Settled, label: `days_label` reads `days.json` `source` (the str(days_path) written at build), correct for v3 and v4. `tmp.parent` is `work` (mkdtemp dir=work). Low: only the basename is used, so it assumes the file lives in backend/conversions.
3. Settled, tests: the v3 case calls wkgap with a stubbed `_week_grades`; the two v4 bad-pattern cases raise; `_wkgap_assert` called directly raises on v3. Fails without the gate. The v4 S-10 test is coverage only, as stated.
4. Settled, module: `tools/demo_rows.py` does not exist; `demo_combined_rows` is aliased `demo_rows` in finish and already holds week_gap_pattern, so it is the right module.
5. Low, cosmetic: two stray blank lines in `_wkgap_assert` after the import. On v3 an AssertionError is caught only around `_wkgap_assert`; an assertion in `week_day_classes` would still escape (acceptable).
