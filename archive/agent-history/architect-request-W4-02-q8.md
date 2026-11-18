# Architect request: W4-02 q8 (FAILED mini jobs on older MINIGRID Sites)

Read:
- `.agent/W4-02-build-spec.md`, q1–q7;
- `.agent/W4-02-pending-rulings.md`, q8 with its options and three readings.

Code: branch `task/W4-02-mini-grid-depth`.

The problem: `test_s4_schedule_health_postgres.py::TestHealthAndSeam::test_fence_moved_streak_terminal_s3_failure_requeue_and_recovery` fails. Older MINIGRID Sites without a `minigrid-roles-4` set keep FAILED mini jobs that never clear. A decommissioned Site is still visited, and its S4 backlog gets matched.

Rule with exact artifacts:
- the predicate that decides which Sites get mini jobs at all, whether enqueue or discovery;
- the terminal handling for FAILED mini jobs;
- the visit and decommission rule;
- the fixed test expectation.

Also confirm or replace the three readings, and name the missing "another Site" case in the q7-2 test matrix.

Append the result as "Run 8 rulings (q8)" to `.agent/W4-02-build-spec.md`. Write nothing else. Do not commit.
