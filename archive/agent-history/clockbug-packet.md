# FIX clock-dependent power fixture - packet

Root cause: `publishing_submit` (test_s405_resolver_postgres.py) built the ledger without `test_decision_clock_override`, so
evidence `recorded_at` was the real wall clock while the fixture clock is a fixed 2026-10-30 ~09:00Z. Once real time passed
that, the assessment worker (`recorded_at <= knowledge_at`) saw nothing: no Finding revisions, so `PowerSite.on(POWER_DAY)` failed.
Not the PERF-02 cache (reproduced cache on and off), not test order.

Changes (test-only):
1. `publishing_submit`: ledger gets `test_decision_clock_override=Clock(decided_at)`, as `CaseRunner.submit`.
2. `test_w303_portfolio_fixture_postgres.py`: `frozen` rounded UP to whole seconds (public `known_at` is second precision;
   once db_now wins the max it carried microseconds). Rounded up, not floored, so `latest_recorded + 1us` stays visible.
   Only `fx.frozen` is compared to `known_at` (also in scope_snapshot:125, same fixture), so one change covers siblings.
3. `test_cutoff_boundaries_and_the_real_clock_skew`: `created > recorded_at` -> `created != recorded_at`. The two clocks are
   independent; their order depended on the wall clock. Chosen over a future sentinel clock because that needs fixture
   clock changes (SETUP_AT/ticks), which were ruled out, and the remaining cutoff assertions do not use the order.

Verified (host, cache off, db clockbug_test, one file at a time): resolver file 9 passed; portfolio_fixture 2 passed;
history `real_clock_skew` 1 passed. Not run: the other consumers of publishing_submit and the scope_snapshot/selectors/
estate/cc/w403 failures from rr-main.txt (awaiting go-ahead). w403 `KeyError: 'revision_id'` in rr-main is a different
symptom and is not covered here.

## Round 2 (5 more fixes, all test-only)
- estate_index `power_estate`: read pin is `max(fixture+1min, db_now)`. The cost-lens test's "earlier cutoff" is now the
  consequence's own `recorded_at` (it is recorded on the database clock, never before the fixture clock), so the intent
  (earlier cutoff -> UNKNOWN with the source revision id) holds unweakened.
- w403 replay: `alt["body"]["id"]` (route returns `id`, alternatives.py:200). The 201 branch is now asserted
  unconditionally (F02 revision time SETUP_AT 2026-10-29 is fixed and past); the 409 not-yet-visible branch is dropped,
  i.e. no longer exercised (not covered elsewhere). The fresh-vs-recorded Alternatives read comparison ignores
  `window.known_at` and `selection_token` (live read stamp), which the 201 branch newly exposed.
- w303 selectors / scope_snapshot: mechanism asserted by equality: GENERATOR_SUPPORT_CANDIDATE (selectors); each row equals the
  stored `finding.mechanism` of its revision, and the per-Site set is pinned (KOBO-001 generator candidate; COLD-LAB-001
  COLD_EXCURSION + COLD_START_FAILURE; EV Sites have no member rows).
Results (host, cache off, own DB, each file alone): cc_placement 2, s4_power_demo_case 8, w301_estate_index 20,
w301_provenance_dto 7, w301_w1_money_snapshot_helpers 6, w303_portfolio_comparison 4, w303_portfolio_fixture 2,
w303_portfolio_scope_snapshot 10, w303_selectors 3, w403_replay 2: all passed.
