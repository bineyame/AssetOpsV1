# FIX-MAIN-2 review packet
Test-only fixes; no product code changed. Run via tools\run-host-tests.ps1 (127.0.0.1, *_test DB), localised.

| Failure | Cause commit | Fix | Result |
|---|---|---|---|
| test_ch9_daylight: test_0048_replaces..., test_downgrade_restores_the_0029_bodies; test_ch9_service_v2: test_0049_enqueues... (3 head pins) | CH-5c2 `0050_chain_response_expiry` moved head | literal `0049_mini_service_v2` -> `pg_harness.alembic_head()` (import added) | pass |
| test_ch2_thread_store: test_0042_catalogue_and_head | CH-5c 0047 `_cic_` change-log triggers on thread tables | exclude `_cic_` triggers from the 0042 trigger set (`tgname !~ '_cic_'`); `_immutable` and `_thread_target` still asserted exactly | pass |
| test_s6_action_records: test_d_action_records_walkthrough_and_contract | CH-5a2b a8c748b7c/0a7f369c2 added `source_class` (null in S6 demo) to the recommendation/action contract; downstream hashes/keys change with it | regenerated fixture via ASSETOPS_WRITE_S6_CONTRACT=1; diff (uuids masked) = `source_class: null` added + hash values; test re-run clean on a second (new-uuid) run | pass |
| test_w403_migration (3 tests, not in the original list) | CH-5c 0047 `_cic_` triggers on mini tables | exclude `_cic_` triggers from the observed catalogue | pass |
| test_w402_migration | already excludes `_cic_` | none | pass on main |

Not touched: product bugs - none found.
Runs: ch9 x2 + s6 + ch2 + ch5c_store_off: 30 passed; w402+w403: 25 passed.
Caveat: the S6 fixture hash changes are accepted from the regenerated run; reviewer may confirm they trace to source_class.
