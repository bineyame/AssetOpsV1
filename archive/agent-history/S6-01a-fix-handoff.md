# S6-01a fix round handoff

- L1: `actions/composition.py` S1_FAILURES maps FOUNDATION_CLOCK_BEHIND -> (409, ACTION_FOUNDATION_STALE). The Site lock is taken inside the S1 publish, so the server time cannot be re-read after it; the clock-behind refusal is the window guard. Test: `test_s6_action_apply_postgres.py::TestClockBehindIsStale`.
- L2: `service.py _application_basis` relabelled, adds `covers_instant` (= read_at). Contract fixture regenerated (ASSETOPS_WRITE_S6_CONTRACT=1; raw IDs churn, comparison is normalised) and `NOTES["application_basis"]` added in `tests/s6_action_records.py` for S6-01b.
- L3/L4 recorded as accepted deviations 7/8 in the review packet.
- Proof: 4 S6 test files, 80 passed (122 s) on private DB (dropped afterwards). No full suite.
