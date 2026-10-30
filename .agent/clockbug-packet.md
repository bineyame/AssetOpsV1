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
