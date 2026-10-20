# Architect request: W2-07 run-7 readings (q6)

You are the AssetOps Architect. Read:
- `.ai/ROLE_CONFIG.md`;
- `.agent/W2-07-build-spec.md` through q5;
- the "Run 7" note in `.agent/W2-07-phase-handoff.md`, plus the code at `50c31605` on branch `task/W2-07-ev-site-evidence-money` (use `git show`).

The builder made three readings while applying q5. Readings are defects. Confirm or replace each one with literal keys, values and copy, and name the test.

1. **Declared schedule flag.** It added `objective.service_schedule_declared` (bool), so that a declared schedule with no overlap in the window is not shown as "not declared". `configured_service_windows` is always a list.
2. **Contact fields.** It added `age_seconds`, `diagnostic_id`, `diagnostic_received_at` and `cadence_seconds` to `contact`. A connector slot with three bound sources in differing states shows `MIXED`. In the replay, `checked_at` equals `known_at` (09:00), which is before `to` (09:05).
3. **Coverage.**
   - Coverage gained a `unit` key: `WINDOW_SECONDS`, `SESSION_SECONDS` or null.
   - Session claims get null coverage if any session lacks a proved span.
   - `SUPPORTED` drops to `LIMITED` unless the ratio is exactly "1".
   - The null-coverage sentence is appended to the claim limitation.

Also state the UI copy that each confirmed field drives on the five EV routes, if q5 did not already give it.

Append to `.agent/W2-07-build-spec.md` as "Run 7 rulings (q6)". Write nothing else. Do not commit.
