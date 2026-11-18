# W3-03 run 0a re-review (fix 9f24f4e5)
Verdict: ACCEPT (read-only, git objects; nothing run).
- M1: financials.py adds private `_windows_covered` to the per-Site cov dict only (mini-grid = state in COVERED, cold/EV = windows_covered), exactly per r0a. applicable AND and tuple shape unchanged. Not in `_coverage_site`/token (named fields) and projected away by the underscore filter, so no wire change. Test covers covered/uncovered EV + mini-grid -> [True, False, True].
- L1: new test asserts values: `_episode_end` == stored finding_revision.episode_end, `_domain` == site.site_type, `_mechanism` None, plan (id, recorded_at) == persisted rows, `_outcome_id` == stored outcome id. Real values, not key presence.
- L2/L3/L4: ruled in r0a as deferrals/confirmations (422 INVALID_LENS kept; S1 -> run 2; call count measured in 1a); fix commit touches only 2 files, none for these, which is correct.
- No W3-01/02 wire change: diff is financials.py (1 line) + one new test file. Caveat: Postgres bytes goldens (money_comparability, financials_links) were not rerun by me; r0a requires the implementer to rerun them before release. The PARTIAL-class assertion is run 1a's.
