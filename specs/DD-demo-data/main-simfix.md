# main-simfix: seven simulator tests red on main

Branch `fix/main-simulator-tests`. Bisected with detached worktrees: at 8acfaab77 the physical-reads and seasons tests are green; at 5ddf77777 (DD4.6, D-DD.144, merged in 601bdb489) the cold ones are red. Lakeside and Metro digests are unchanged (asserted in the re-pin).

| Test | Broke at | Why | Class | Fix |
| --- | --- | --- | --- | --- |
| test_core `test_t6_greps[\b31\b]` | 312b95bfa / 200ad01f4 (DD4.4 `exports_measured`, `telemetry_ev`) | the sentinel `"9999-12-31"` contains the literal 31 (R25a guard) | (a) code | `date.max.isoformat()` (same value); guard untouched |
| test_dd2b_cold c11 | 83e83cbff (DD4.6: plan kwh whole kWh, D-DD.49/D-DD.144) | pinned Mwea July plan kwh `3410`; the ruling's restated cold model gives `1716` | (b) re-pin | `3410` -> `1716` |
| test_scope_physical_reads `test_cold_fixture_scopes_equal_main`, `test_cold_history_json_blocks_equal_main` | 5ddf77777 (D-DD.144) | cold scope blocks hold the restated cold energy and plan kwh, so the 9 cold digests and block hashes moved | (b) re-pin | `golden/physical_reads_cold_main.json` regenerated from the fixture view (history.json equals it) |
| test_scope_seasons_parity (3 tests) | 5ddf77777 (D-DD.144) | same cause; D-DD.90's own claim (a season adds no digest move) still holds, only cold digests differ | (b) re-pin | `golden/scope_seasons_main.json` cold digests and `tenants_sha256` regenerated; script asserted every non-cold digest equals the old golden |

Counts: `simulator/tests/world` 7 failed / 379 passed before, 386 passed after. check_manifest 6 FAIL before and after (main's 6). No assertion was weakened.
