# Owner: approve load-aware timing tests (2026-11-21)

Verbatim, in session, after the coordinator asked for approval to make two timing-sensitive tests allow for machine load (T1 heavy-slot self-test P4b, "pwsh outer took 5154/5387 ms", failing check-all on main twice at load ~9 and passing alone; contracts `test_3a6_profiles` n3_r5_b1 wall bound 7.5 s vs 3.0 s under load):

> approval granted for timeing-sensitive tests

Scope: a guard/test change that scales or retries those wall-time bounds under load, with tests; no other guard rule changes.
