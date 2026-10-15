# S5-01 fix round handoff
- L1: read.py - an unreadable overlapping Finding sets discovery_complete False (money UPSTREAM_PENDING, no amount); test asserts it.
- L2: .agent/S5-01-owner-walkthrough.md - exact tick command inline; tick before steps 1, 4 (5); never between attest and steps 6-7; tick at 8; step-5 stale reference removed.
- L3: no dispatch result carries an objective, so the dead `objective` key was removed (backend + client type). Panel now states "The assessment does not state an operating objective for this day" and shows the day's claim level, operating-period count and covered-role count from existing fields (SiteWindowOverview.tsx; test added). "dispatch interval" is banned vocabulary, so copy says "operating periods".
- Proof: test_s5_overview_read.py 34 passed; tsc clean; npm test 63 files / 1513 passed; check-all 9 guards passed (run with -ExecutionPolicy Bypass).
- Not run: test_s5_overview_postgres.py, s5-overview-evidence.mjs re-run at 1440/390 (panel copy changed; layout unverified for the added two lines), no DBs created.
