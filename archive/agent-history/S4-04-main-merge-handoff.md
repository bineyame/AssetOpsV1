# S4-04 main-merge handoff

Merged main (7edbe396) cleanly into task/S4-04-site-finding-index. Index now honours deferred_window_starts (postgres_finding_store.index_snapshot -> finding_index._day). New tests: tests/test_s4_finding_index_reach.py; deferred-match scenario A index assertion. Full suite 2388 passed, 0 skipped (12m25s); check-all 9/9. Temporaries removed. Not merged to main; ready for owner walkthrough/merge.
