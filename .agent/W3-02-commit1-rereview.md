# W3-02 commit-1 fix r1 re-review (33b9711e)

Verdict: ACCEPT (two Lows, non-blocking). Read through git objects only; nothing was run, so the new tests passing is not verified by me.

Closed as ruled: M1 (_window_state maps a live pin HISTORICAL to CURRENT, a missing pin stays UNKNOWN, PENDING/STALE precedence kept), M2 (the five codes map to an unavailable day with HISTORICAL_SELECTION_UNAVAILABLE plus the original code, 200, other Sites intact; the test goes through the real adapter mapping), R1, R2, L1 (_token_cited = cited + read evidence_ids, claimless row cites nothing), L2, L3, L4 (complete keyed on snap.basis_historical).

Test deviation: sound. Page two is read at the cursor's frozen k, so its token must equal page one's (k is in the token). Comparing page two to page one therefore proves the fence is stable under a later watermark. The test also compares row states, IDs, gaps and counts against a whole-window read, and it asserts watermark > cursor_k, so it fails on the old UNKNOWN flip. The separate 409 control with a backdated disposition covers the "changed selected ID" half. Splitting them does not weaken M1.

Lows:
- L5 EV test: `row_ids < token_ids` only shows extra IDs are present. It does not show they are the session revision IDs, and it does not assert the session-only 409 in that test (it is covered only by a pure test).
- `test_w302_evidence_composition_mount_no_db_503` accepts 401 or 503 and asserts nothing on 401. Pin the status, or send auth.
