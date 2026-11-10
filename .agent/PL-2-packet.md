# PL-2 packet: pre-build Portfolio lens variants (D-E5.23)

Branch `task/PL-2-lens-prebuilt` (from main 862c4577f).

- `tools/demo_combined.py`: new `PORTFOLIO_LENSES = (cost, risks, opportunities)`; `prebuilt_routes` adds
  `portfolio.{week,S,month}.{lens}` (9 requests) with the same query as the `lens=all` request and `("lens", lens)`
  appended, matching `estateQueryString` order (from, to, known_at, lens). `findings.week` unchanged.
- `backend/tests/test_e4_prebuilt_routes_generator.py`: `test_the_portfolio_lens_variants_are_prebuilt_for_week_s_and_month`
  asserts the 9 ids and queries plus path/query and id uniqueness. On main the ids do not exist (KeyError), so it fails there.
- Checks (one file at a time): generator 11 passed, source 5, links 11, ch5c_env_parity 3, finish_rows 69; all pass.

Notes: the disk was full; the worktree `..\AssetOpsV1-pl2` uses a sparse checkout excluding
`.agent/post-W6-final-recapture`, `frontend/mockups`, `frontend/public`. The failing-on-main run was not executed
separately (ids absent on main).
