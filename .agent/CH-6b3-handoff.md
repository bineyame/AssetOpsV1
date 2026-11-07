# CH-6b3 handoff

- **State:** CH6b3-R3 steps 1-5, 7 done and committed; step 6 partly: drained polish clone passed (figures equal expected, 0 new, clone dropped); scoped backend 337 passed, 2 errors (TEMPLATE_STALE mechanism template, `test_ch6b_estate_postgres.py`); L3m and the Postgres Why route test not run until the states template is rebuilt (needs coordinator approval, ~1300 s).
- **Packet:** `.agent/review-packet-CH-6b3.md` section "CH6b3-R3".
- **Next:** coordinator decides the template rebuild; then run `test_ch6b_estate_postgres.py`, L3m collect/check (`--variant states`; L3m D14 recurrence may need `expected-mechanism.json` entries per the ruling); re-review.
